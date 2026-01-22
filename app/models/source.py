"""
Source Model

Represents content sources (YouTube channels, RSS feeds, blogs).
Sources are where we fetch AI news content from.

Examples:
- YouTube channel: Two Minute Papers
- RSS feed: OpenAI Blog
- Blog: Anthropic News
"""

from app.models.base import db, BaseModel
from sqlalchemy import Enum
import enum


class SourceType(enum.Enum):
    """
    Enumeration of source types.
    
    Using Python Enum ensures we only use valid source types
    and prevents typos in the database.
    """
    YOUTUBE = "youtube"
    RSS = "rss"
    BLOG = "blog"


class Source(BaseModel):
    """
    Source model for content providers.
    
    Stores information about where we get content from.
    Each source can be a YouTube channel, RSS feed, or blog.
    
    Relationships:
    - One source has many content items
    
    Example:
        # Create YouTube source
        source = Source(
            name="Two Minute Papers",
            source_type=SourceType.YOUTUBE,
            identifier="UCbfYPyITQ-7l4upoX8nvctg",
            url="https://youtube.com/channel/UCbfYPyITQ-7l4upoX8nvctg"
        )
        source.save()
    """
    
    # Table name in database
    __tablename__ = 'sources'
    
    # ================================
    # Columns
    # ================================
    
    name = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )
    # Human-readable name
    # Example: "Two Minute Papers", "OpenAI Blog"
    # unique=True means no two sources can have same name
    
    source_type = db.Column(
        Enum(SourceType),
        nullable=False
    )
    # Type of source: YOUTUBE, RSS, or BLOG
    # Using Enum ensures only valid types
    
    identifier = db.Column(
        db.String(500),
        nullable=False,
        unique=True
    )
    # Unique identifier for this source
    # YouTube: channel ID (UCbfYPyITQ...)
    # RSS: feed URL (https://openai.com/blog/rss)
    # Blog: base URL (https://anthropic.com/news)
    
    url = db.Column(
        db.String(1000),
        nullable=True
    )
    # Full URL to the source
    # nullable=True because not always needed
    
    description = db.Column(
        db.Text,
        nullable=True
    )
    # Optional description of the source
    # db.Text = unlimited length (unlike String)
    
    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    # Whether this source is currently active
    # False = temporarily disabled (don't fetch from it)
    
    fetch_frequency = db.Column(
        db.Integer,
        nullable=False,
        default=6
    )
    # How often to fetch from this source (in hours)
    # Default: 6 hours
    
    last_fetched_at = db.Column(
        db.DateTime,
        nullable=True
    )
    # When we last fetched content from this source
    # None = never fetched yet
    
    total_items_fetched = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Total number of items we've fetched from this source
    # Useful for statistics
    
    # ================================
    # Relationships
    # ================================
    
    # One source has many content items
    # This creates a "virtual" field: source.content_items
    # content_items = relationship to ContentItem model (we'll create this next)
    # We'll add this relationship when we create article.py
    
    # ================================
    # Methods
    # ================================
    
    def __repr__(self):
        """String representation for debugging"""
        return f"<Source {self.name} ({self.source_type.value})>"
    
    def to_dict(self):
        """
        Convert to dictionary, with enum converted to string.
        
        Overrides BaseModel.to_dict() to handle the Enum properly.
        """
        data = super().to_dict()
        # Convert enum to string for JSON serialization
        if self.source_type:
            data['source_type'] = self.source_type.value
        return data
    
    def mark_fetched(self, items_count=0):
        """
        Mark this source as fetched.
        
        Updates last_fetched_at and increments total_items_fetched.
        
        Args:
            items_count (int): Number of items fetched in this batch
            
        Example:
            source = Source.query.first()
            source.mark_fetched(items_count=10)
            # Updates timestamps and counters
        """
        from datetime import datetime
        self.last_fetched_at = datetime.utcnow()
        self.total_items_fetched += items_count
        self.save()
    
    def should_fetch_now(self):
        """
        Check if it's time to fetch from this source.
        
        Returns True if:
        - Source is active
        - Never fetched before OR
        - Enough time has passed since last fetch
        
        Returns:
            bool: True if should fetch, False otherwise
            
        Example:
            source = Source.query.first()
            if source.should_fetch_now():
                # Fetch content from this source
                fetch_content(source)
        """
        # If not active, don't fetch
        if not self.active:
            return False
        
        # If never fetched, fetch now
        if not self.last_fetched_at:
            return True
        
        # Check if enough time has passed
        from datetime import datetime, timedelta
        time_since_last_fetch = datetime.utcnow() - self.last_fetched_at
        hours_passed = time_since_last_fetch.total_seconds() / 3600
        
        return hours_passed >= self.fetch_frequency
    
    @classmethod
    def get_active_sources(cls):
        """
        Get all active sources.
        
        Class method (uses cls instead of self).
        Can be called without an instance.
        
        Returns:
            list: List of active Source objects
            
        Example:
            sources = Source.get_active_sources()
            for source in sources:
                print(source.name)
        """
        return cls.query.filter_by(active=True).all()
    
    @classmethod
    def get_sources_by_type(cls, source_type):
        """
        Get all sources of a specific type.
        
        Args:
            source_type (SourceType): Type to filter by
            
        Returns:
            list: List of Source objects of that type
            
        Example:
            youtube_sources = Source.get_sources_by_type(SourceType.YOUTUBE)
            rss_sources = Source.get_sources_by_type(SourceType.RSS)
        """
        return cls.query.filter_by(
            source_type=source_type,
            active=True
        ).all()