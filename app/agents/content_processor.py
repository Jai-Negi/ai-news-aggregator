"""
ContentProcessor Agent

Processes raw content items using AI.

Responsibilities:
- Get unprocessed ContentItems from database
- Summarize content using Gemini
- Rate content quality
- Extract topics and tags
- Create Article records
- Mark ContentItems as processed

Example:
    processor = ContentProcessorAgent()
    results = processor.process_all()
    print(f"Processed {results['processed']} articles")
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.services import GeminiService

from app.models import ContentItem, Article, db

logger = logging.getLogger(__name__)


class ContentProcessorAgent:
    """
    Agent responsible for processing raw content with AI.
    
    This agent:
    1. Gets unprocessed ContentItems from database
    2. Summarizes each with Gemini AI
    3. Rates quality (0-10)
    4. Extracts topic and tags
    5. Creates Article records
    6. Marks ContentItems as processed
    
    Example:
        processor = ContentProcessorAgent()
        results = processor.process_all(limit=10)
        # Returns: {"processed": 8, "failed": 2}
    """
    
    def __init__(self):
        """Initialize the agent with Gemini service."""
        self.gemini = GeminiService()
        logger.info("ContentProcessorAgent initialized")
    
    def process_all(self, limit: int = 50) -> Dict:
        """
        Process all unprocessed content items.
        
        Args:
            limit: Maximum number of items to process (default: 50)
        
        Returns:
            dict: Statistics about processing
                {
                    "processed": 8,
                    "failed": 2,
                    "skipped": 0,
                    "total_attempted": 10
                }
        
        Example:
            processor = ContentProcessorAgent()
            results = processor.process_all(limit=20)
            print(f"Processed {results['processed']} articles")
        """
        logger.info(f"Starting content processing (limit: {limit})")
        
        # Initialize statistics
        stats = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "total_attempted": 0
        }
        
        # Get unprocessed items from database
        items = ContentItem.query.filter_by(processed=False).limit(limit).all()
        
        if not items:
            logger.info("No unprocessed items found")
            return stats
        
        logger.info(f"Found {len(items)} unprocessed items")
        
        # Process each item
        for item in items:
            stats["total_attempted"] += 1
            
            try:
                success = self._process_item(item)
                
                if success:
                    stats["processed"] += 1
                else:
                    stats["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}")
                stats["failed"] += 1
        
        logger.info(
            f"Processing complete: {stats['processed']} processed, "
            f"{stats['failed']} failed, {stats['skipped']} skipped"
        )
        
        return stats
    
    def _process_item(self, item: ContentItem) -> bool:
        """
        Process a single content item.
        
        Args:
            item: ContentItem to process
        
        Returns:
            bool: True if processed successfully, False if skipped
        """
        logger.info(f"Processing: {item.title[:60]}")
        
        # Check if already has an article
        existing_article = Article.query.filter_by(content_item_id=item.id).first()
        if existing_article:
            logger.debug(f"Article already exists for item {item.id}, marking as processed")
            item.processed = True
            db.session.commit()
            return False
        
        # Check if content is too short
        if not item.content or len(item.content) < 100:
            logger.warning(f"Content too short for item {item.id}, skipping")
            item.processed = True
            db.session.commit()
            return False
        
        # Summarize
        logger.debug("Summarizing content...")
        summary = self.gemini.summarize(
            item.content,
            max_words=200,
            style="concise"
        )
        
        if not summary:
            logger.warning(f"Failed to generate summary for item {item.id}")
            return False
        
        # Rate quality
        logger.debug("Rating quality...")
        quality_score = self.gemini.rate_quality(item.content)
        
        # Extract topic
        logger.debug("Extracting topic...")
        topic = self.gemini.extract_topic(item.title, summary)
        
        # Extract tags
        logger.debug("Extracting tags...")
        tags_list = self.gemini.extract_tags(item.content, max_tags=5)
        
        # Create Article record
        article = Article(
            content_item_id=item.id,
            title=item.title,
            summary=summary,
            quality_score=quality_score,
            relevance_tags=tags_list,
            topic_cluster=topic,
            published_at=item.published_at
        )
        
        # Mark item as processed
        item.processed = True
        
        # Save to database
        try:
            db.session.add(article)
            db.session.commit()
            logger.info(f"✅ Processed: {item.title[:60]} (Quality: {quality_score}/10)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save article for item {item.id}: {e}")
            db.session.rollback()
            return False
    
    def process_single(self, content_item_id: int) -> Optional[Article]:
        """
        Process a specific content item by ID.
        
        Args:
            content_item_id: ID of ContentItem to process
        
        Returns:
            Article: Created article, or None if failed
        
        Example:
            processor = ContentProcessorAgent()
            article = processor.process_single(123)
            if article:
                print(f"Created article: {article.summary}")
        """
        item = ContentItem.query.get(content_item_id)
        
        if not item:
            logger.error(f"ContentItem {content_item_id} not found")
            return None
        
        success = self._process_item(item)
        
        if success:
            return Article.query.filter_by(content_item_id=item.id).first()
        
        return None
    
    def reprocess_failed(self, limit: int = 10) -> Dict:
        """
        Reprocess items that were marked as processed but have no article.
        
        Useful for recovering from errors.
        
        Args:
            limit: Maximum number to reprocess
        
        Returns:
            dict: Statistics
        """
        logger.info("Looking for processed items without articles...")
        
        # Find processed items without articles
        items = db.session.query(ContentItem).outerjoin(Article).filter(
            ContentItem.processed == True,
            Article.id == None
        ).limit(limit).all()
        
        if not items:
            logger.info("No failed items found")
            return {"processed": 0, "failed": 0}
        
        logger.info(f"Found {len(items)} items to reprocess")
        
        # Mark as unprocessed
        for item in items:
            item.processed = False
        
        db.session.commit()
        
        # Process them
        return self.process_all(limit=limit)
    
    def get_stats(self) -> Dict:
        """
        Get statistics about content processing.
        
        Returns:
            dict: Statistics
                {
                    "total_items": 150,
                    "processed": 100,
                    "unprocessed": 50,
                    "articles": 95,
                    "avg_quality": 7.5
                }
        """
        try:
            total_items = ContentItem.query.count()
            processed = ContentItem.query.filter_by(processed=True).count()
            unprocessed = ContentItem.query.filter_by(processed=False).count()
            articles = Article.query.count()
            
            # Calculate average quality
            avg_quality = db.session.query(
                db.func.avg(Article.quality_score)
            ).scalar() or 0
            
            return {
                "total_items": total_items,
                "processed": processed,
                "unprocessed": unprocessed,
                "articles": articles,
                "avg_quality": round(avg_quality, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}