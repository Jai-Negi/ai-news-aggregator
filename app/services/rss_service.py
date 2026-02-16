"""
RSS Service

Handles all interactions with RSS/Atom feeds.

Features:
- Fetch articles from RSS feeds
- Parse feed metadata
- Extract article content
- Handle different feed formats (RSS 2.0, Atom, RSS 1.0)

Uses:
- feedparser library for parsing
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import feedparser
from dateutil import parser as date_parser


import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

logger = logging.getLogger(__name__)


class RSSService:
    """
    Service for fetching and parsing RSS feeds.
    
    Supports RSS 2.0, Atom, and RSS 1.0 formats.
    
    Example:
        rss = RSSService()
        articles = rss.fetch_feed('https://openai.com/blog/rss')
    """
    
    def __init__(self):
        """Initialize RSS service."""
        logger.info("RSSService initialized successfully")
    
    def fetch_feed(
        self,
        feed_url: str,
        max_items: int = 10
    ) -> List[Dict]:
        """
        Fetch and parse an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to return (default: 10)
        
        Returns:
            list: List of article dictionaries
        
        Example:
            articles = rss.fetch_feed('https://openai.com/blog/rss', max_items=5)
        """
        try:
            # Parse the feed
            logger.info(f"Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            # Check if feed was parsed successfully
            if feed.bozo:
                # bozo = True means there was an error parsing
                logger.warning(f"Feed parse warning for {feed_url}: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return []
            
            # Get feed metadata
            feed_title = feed.feed.get('title', 'Unknown Feed')
            feed_link = feed.feed.get('link', feed_url)
            
            # Process entries
            articles = []
            for entry in feed.entries[:max_items]:
                article_data = self._process_entry(entry, feed_title, feed_link)
                if article_data:
                    articles.append(article_data)
            
            logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch feed {feed_url}: {e}")
            return []
    
    def _process_entry(
        self,
        entry: Dict,
        feed_title: str,
        feed_link: str
    ) -> Optional[Dict]:
        """
        Process a single feed entry.
        
        Extracts and normalizes data from different feed formats.
        """
        try:
            # Get title
            title = entry.get('title', '').strip()
            if not title:
                logger.warning("Entry has no title, skipping")
                return None
            
            # Get link (try multiple fields)
            link = entry.get('link') or entry.get('id') or ''
            if not link:
                logger.warning(f"Entry '{title}' has no link, skipping")
                return None
            
            # Get unique ID (guid or link)
            external_id = entry.get('id') or entry.get('guid') or link
            
            # Get published date
            published_at = self._parse_date(entry)
            
            # Get content/summary
            content = self._extract_content(entry)
            
            # Get author
            author = self._extract_author(entry)
            
            # Build article data
            article_data = {
                'id': external_id,
                'title': title,
                'link': link,
                'content': content,
                'author': author,
                'published_at': published_at,
                'feed_title': feed_title,
                'feed_link': feed_link
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            return None
    
    def _parse_date(self, entry: Dict) -> Optional[datetime]:
        """
        Parse date from entry.
        
        Tries multiple date fields and formats.
        """
        # Try different date fields
        date_fields = [
            'published',
            'updated',
            'created',
            'published_parsed',
            'updated_parsed'
        ]
        
        for field in date_fields:
            date_value = entry.get(field)
            
            if not date_value:
                continue
            
            try:
                # If it's a time struct (from parsed fields)
                if hasattr(date_value, 'tm_year'):
                    return datetime(
                        date_value.tm_year,
                        date_value.tm_mon,
                        date_value.tm_mday,
                        date_value.tm_hour,
                        date_value.tm_min,
                        date_value.tm_sec
                    )
                
                # If it's a string
                if isinstance(date_value, str):
                    return date_parser.parse(date_value)
                    
            except Exception as e:
                logger.debug(f"Could not parse date from {field}: {e}")
                continue
        
        # If no date found, use current time
        logger.debug("No date found in entry, using current time")
        return datetime.now()
    
    def _extract_content(self, entry: Dict) -> str:
        """
        Extract content from entry.
        
        Tries multiple content fields and cleans HTML.
        """
        # Try different content fields (in order of preference)
        content_fields = [
            ('content', 0, 'value'),  # Atom format
            ('summary',),              # RSS 2.0
            ('description',),          # RSS 2.0 alternative
            ('summary_detail', 'value'),
        ]
        
        for field_path in content_fields:
            try:
                value = entry
                for key in field_path:
                    if isinstance(key, int):
                        value = value[key]
                    else:
                        value = value.get(key)
                    if value is None:
                        break
                
                if value and isinstance(value, str):
                    # Clean HTML tags
                    cleaned = self._clean_html(value)
                    if cleaned.strip():
                        return cleaned
                        
            except (KeyError, IndexError, TypeError):
                continue
        
        # Fallback
        return entry.get('title', '')
    
    def _clean_html(self, html_text: str) -> str:
        """
        Remove HTML tags from text.
        
        Simple implementation - for production, consider using BeautifulSoup.
        """
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_text)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_author(self, entry: Dict) -> str:
        """
        Extract author from entry.
        
        Tries multiple author fields.
        """
        # Try different author fields
        if 'author' in entry:
            return entry['author']
        
        if 'author_detail' in entry:
            author_detail = entry['author_detail']
            return author_detail.get('name', '')
        
        if 'authors' in entry and entry['authors']:
            return entry['authors'][0].get('name', '')
        
        if 'dc_creator' in entry:
            return entry['dc_creator']
        
        return ''
    
    def get_feed_info(self, feed_url: str) -> Optional[Dict]:
        """
        Get metadata about a feed without fetching articles.
        
        Args:
            feed_url: URL of the RSS feed
        
        Returns:
            dict: Feed metadata (title, description, link)
        
        Example:
            info = rss.get_feed_info('https://openai.com/blog/rss')
        """
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                logger.error(f"Failed to parse feed: {feed.bozo_exception}")
                return None
            
            info = {
                'title': feed.feed.get('title', 'Unknown'),
                'link': feed.feed.get('link', feed_url),
                'description': feed.feed.get('description', ''),
                'language': feed.feed.get('language', ''),
                'updated': feed.feed.get('updated', ''),
                'entry_count': len(feed.entries)
            }
            
            logger.info(f"Got feed info for {feed_url}: {info['title']}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get feed info for {feed_url}: {e}")
            return None
    
    def test_connection(self, feed_url: str = 'http://feeds.bbci.co.uk/news/rss.xml') -> bool:
        """
        Test if RSS fetching works.
        
        Args:
            feed_url: Feed URL to test (default: TechCrunch)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            feed = feedparser.parse(feed_url)
            
            result = len(feed.entries) > 0
            
            if result:
                logger.info(f"RSS connection test: SUCCESS ({len(feed.entries)} entries)")
            else:
                logger.warning("RSS connection test: No entries found")
            
            return result
            
        except Exception as e:
            logger.error(f"RSS connection test FAILED: {e}")
            return False