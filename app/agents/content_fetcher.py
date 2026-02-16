"""
ContentFetcher Agent

Fetches new content from all active sources (RSS and YouTube).

Responsibilities:
- Get list of active sources from database
- Fetch content using appropriate service (RSS or YouTube)
- Save new content to ContentItem table
- Avoid duplicates
- Track statistics

Example:
    fetcher = ContentFetcherAgent()
    results = fetcher.fetch_all(hours_back=24)
    print(f"Saved {results['total_saved']} new items")
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional


from app.services import RSSService, YouTubeService

from app.models import Source, ContentItem, SourceType

from app.models import db

logger = logging.getLogger(__name__)


class ContentFetcherAgent:
    """
    Agent responsible for fetching new content from all sources.
    
    This agent:
    1. Gets all active sources from database
    2. Fetches content based on source type (RSS or YouTube)
    3. Saves new content to ContentItem table
    4. Handles duplicates automatically
    
    Example:
        fetcher = ContentFetcherAgent()
        results = fetcher.fetch_all()
        # Returns: {"fetched": 25, "saved": 20, "duplicates": 5}
    """
    
    def __init__(self):
        """Initialize the agent with required services."""
        self.rss_service = RSSService()
        self.youtube_service = YouTubeService()
        logger.info("ContentFetcherAgent initialized")
    
    def fetch_all(self, hours_back: int = 24) -> Dict:
        """
        Fetch content from all active sources.
        
        Args:
            hours_back: Only fetch content from last N hours (default: 24)
        
        Returns:
            dict: Statistics about fetching
                {
                    "total_fetched": 25,
                    "total_saved": 20,
                    "duplicates": 5,
                    "by_source": {
                        "MIT Tech Review": {"fetched": 5, "saved": 4},
                        ...
                    }
                }
        
        Example:
            fetcher = ContentFetcherAgent()
            results = fetcher.fetch_all(hours_back=24)
            print(f"Saved {results['total_saved']} new items")
        """
        logger.info(f"Starting content fetch (last {hours_back} hours)")
        
        # Initialize statistics
        stats = {
            "total_fetched": 0,
            "total_saved": 0,
            "duplicates": 0,
            "by_source": {}
        }
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        logger.info(f"Fetching content published after {cutoff_time}")
        
        # Get all active sources from database
        sources = Source.query.filter_by(active=True).all()
        
        if not sources:
            logger.warning("No active sources found in database")
            return stats
        
        logger.info(f"Found {len(sources)} active sources")
        
        # Fetch from each source
        for source in sources:
            try:
                logger.info(f"Processing source: {source.name}")
                source_stats = self._fetch_from_source(source, cutoff_time)
                stats["by_source"][source.name] = source_stats
                stats["total_fetched"] += source_stats["fetched"]
                stats["total_saved"] += source_stats["saved"]
                stats["duplicates"] += source_stats["duplicates"]
                
            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}")
                stats["by_source"][source.name] = {
                    "fetched": 0,
                    "saved": 0,
                    "duplicates": 0,
                    "error": str(e)
                }
        
        logger.info(
            f"Fetch complete: {stats['total_saved']} saved, "
            f"{stats['duplicates']} duplicates, "
            f"{stats['total_fetched']} total fetched"
        )
        
        return stats
    
    def _fetch_from_source(
        self,
        source: Source,
        cutoff_time: datetime
    ) -> Dict:
        """
        Fetch content from a single source.
        
        Routes to appropriate method based on source type.
        
        Args:
            source: Source object to fetch from
            cutoff_time: Only fetch items after this time
        
        Returns:
            dict: {"fetched": 10, "saved": 8, "duplicates": 2}
        """
        logger.info(f"Fetching from {source.name} ({source.source_type.value})")
        
        # Route to appropriate handler
        if source.source_type == SourceType.RSS:
            return self._fetch_from_rss(source, cutoff_time)
        
        elif source.source_type == SourceType.YOUTUBE:
            return self._fetch_from_youtube(source, cutoff_time)
        
        else:
            logger.error(f"Unknown source type: {source.source_type}")
            return {"fetched": 0, "saved": 0, "duplicates": 0}
    
    def _fetch_from_rss(
    self,
    source: Source,
    cutoff_time: datetime
    ) -> Dict:
        """
        Fetch content from an RSS source.
        
        Args:
            source: Source object with RSS feed URL
            cutoff_time: Only fetch items after this time
        
        Returns:
            dict: {"fetched": 10, "saved": 8, "duplicates": 2}
        """
        from datetime import timezone
        
        stats = {"fetched": 0, "saved": 0, "duplicates": 0}
        
        try:
            # Fetch from RSS feed
            logger.info(f"Fetching RSS feed: {source.identifier}")
            articles = self.rss_service.fetch_feed(
                feed_url=source.identifier,
                max_items=20  # Fetch up to 20 items
            )
            
            stats["fetched"] = len(articles)
            logger.info(f"Fetched {len(articles)} articles from {source.name}")
            
            # Make cutoff timezone-aware if it isn't
            if cutoff_time.tzinfo is None:
                cutoff_time = cutoff_time.replace(tzinfo=timezone.utc)
            
            # Process each article
            for article in articles:
                # Make published_at timezone-aware if it isn't
                published_at = article['published_at']
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
                
                # Check if published after cutoff
                if published_at < cutoff_time:
                    logger.debug(f"Skipping old article: {article['title'][:50]}")
                    continue
                
                # Try to save
                saved = self._save_content_item(source, article)
                
                if saved:
                    stats["saved"] += 1
                else:
                    stats["duplicates"] += 1
            
            logger.info(
                f"{source.name}: {stats['saved']} saved, "
                f"{stats['duplicates']} duplicates"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching RSS from {source.name}: {e}")
            return stats
    
    def _fetch_from_youtube(
        self,
        source: Source,
        cutoff_time: datetime
    ) -> Dict:
        """
        Fetch content from a YouTube channel.
        
        Args:
            source: Source object with YouTube channel ID
            cutoff_time: Only fetch videos after this time
        
        Returns:
            dict: {"fetched": 5, "saved": 3, "duplicates": 2}
        """
        stats = {"fetched": 0, "saved": 0, "duplicates": 0}
        
        try:
            # Fetch from YouTube channel
            logger.info(f"Fetching YouTube channel: {source.identifier}")
            videos = self.youtube_service.get_channel_videos(
                channel_id=source.identifier,
                max_results=10,
                published_after=cutoff_time  # YouTube service handles filtering
            )
            
            stats["fetched"] = len(videos)
            logger.info(f"Fetched {len(videos)} videos from {source.name}")
            
            # Process each video
            for video in videos:
                # Try to save 
                saved = self._save_content_item(source, video)
                
                if saved:
                    stats["saved"] += 1
                else:
                    stats["duplicates"] += 1
            
            logger.info(
                f"{source.name}: {stats['saved']} saved, "
                f"{stats['duplicates']} duplicates"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching YouTube from {source.name}: {e}")
            return stats
    
    def _save_content_item(
        self,
        source: Source,
        data: Dict
    ) -> bool:
        """
        Save content item to database.
        
        Handles duplicate detection automatically using:
        1. external_id (URL or unique ID from source)
        2. content_hash (SHA-256 of content)
        
        Also updates existing items if transcript becomes available.
        
        Args:
            source: Source object this content came from
            data: Content data from RSS or YouTube service
                Expected keys:
                - 'id' or 'link': unique identifier
                - 'title': article/video title
                - 'content' or 'transcript': main content
                - 'published_at': publication date
                - 'author': author name (optional)
        
        Returns:
            bool: True if saved/updated, False if duplicate
        """
        try:
            # Get unique identifier
            external_id = data.get('id') or data.get('link')
            
            if not external_id:
                logger.warning(f"No external_id found for: {data.get('title', 'Unknown')[:50]}")
                return False
            
            # Check if already exists by external_id
            existing = ContentItem.query.filter_by(
                external_id=external_id
            ).first()
            
            if existing:
                # Check if we need to update transcript/content
                new_content = data.get('content') or data.get('transcript', '')
                existing_content = existing.content or ''
                
                # If existing has no/minimal content but new has transcript, update it
                if (not existing_content or len(existing_content) < 50) and new_content and len(new_content) >= 50:
                    logger.info(f"Updating transcript for existing video: {data.get('title', 'Unknown')[:50]}")
                    existing.content = new_content
                    existing.calculate_word_count()
                    
                    # Regenerate hash 
                    try:
                        existing.content_hash = existing.generate_content_hash()
                        db.session.commit()
                        logger.info(f"✅ Updated transcript: {existing.title[:60]}")
                        return True
                    except Exception as hash_error:
                        # If hash conflicts, rollback and skip update
                        db.session.rollback()
                        logger.warning(f"Hash conflict when updating {external_id}: {hash_error}")
                        return False
                
                logger.debug(f"Duplicate found (external_id): {data.get('title', 'Unknown')[:50]}")
                return False
            
            # Get content (RSS uses 'content', YouTube uses 'transcript')
            content = data.get('content') or data.get('transcript', '')
            
            # For YouTube videos, allow saving with description even if transcript is missing
            is_youtube = source.source_type == SourceType.YOUTUBE
            
            if not content:
                content = data.get('description', '')
                
                # For YouTube: allow saving with description
                # For RSS: require minimum content length
                min_length = 50 if not is_youtube else 10
                
                if not content or len(content) < min_length:
                    logger.warning(f"No content or description for: {data.get('title', 'Unknown')[:50]}")
                    return False
            
            # Create new ContentItem
            content_item = ContentItem(
                source_id=source.id,
                external_id=external_id,
                title=data.get('title', ''),
                content=content,
                url=data.get('link') or data.get('url', ''),
                author=data.get('author', ''),
                published_at=data.get('published_at'),
                metadata={
                    'feed_title': data.get('feed_title'),
                    'channel_title': data.get('channel_title'),
                    'view_count': data.get('view_count'),
                    'like_count': data.get('like_count'),
                    'duration': data.get('duration'),
                    'thumbnail': data.get('thumbnail'),
                }
            )
            
            # Calculate word count
            content_item.calculate_word_count()
            
            # Calculate content hash for additional duplicate detection
            content_item.content_hash = content_item.generate_content_hash()
            
            # Check if content hash already exists 
            existing_hash = ContentItem.query.filter_by(
                content_hash=content_item.content_hash
            ).first()
            
            if existing_hash:
                logger.debug(f"Duplicate found (content_hash): {data.get('title', 'Unknown')[:50]}")
                return False
            
            # Save to database
            db.session.add(content_item)
            db.session.commit()
            
            logger.info(f"✅ Saved: {content_item.title[:60]}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving content item: {e}")
            db.session.rollback()
            return False
    
    def get_stats(self) -> Dict:
        """
        Get statistics about content items in database.
        
        Returns:
            dict: Statistics
                {
                    "total_items": 150,
                    "unprocessed": 25,
                    "by_source": {
                        "MIT Tech Review": 50,
                        ...
                    }
                }
        """
        try:
            total_items = ContentItem.query.count()
            unprocessed = ContentItem.query.filter_by(processed=False).count()
            
            # Get count by source
            sources = Source.query.all()
            by_source = {}
            
            for source in sources:
                count = ContentItem.query.filter_by(source_id=source.id).count()
                by_source[source.name] = count
            
            return {
                "total_items": total_items,
                "unprocessed": unprocessed,
                "by_source": by_source
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}