"""
Article Models

Contains two models:
1. ContentItem - Raw fetched content from sources
2. Article - Processed and summarized content for digests

Flow: Source → ContentItem → Article → Email Digest
"""

from app.models.base import db, BaseModel
from datetime import datetime
import hashlib


class ContentItem(BaseModel):
    """
    Raw content fetched from sources.
    
    This stores the original, unprocessed content from:
    - YouTube video transcripts
    - RSS feed articles
    - Scraped blog posts
    
    One ContentItem can become one Article (after processing).
    
    Relationships:
    - Belongs to one Source
    - Has one Article (after processing)
    
    Example:
        item = ContentItem(
            source_id=1,
            external_id="dQw4w9WgXcQ",
            title="New AI Breakthrough Explained",
            content="[Full transcript here...]",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ"
        )
        item.save()
    """
    
    # Table name
    __tablename__ = 'content_items'
    
   
    # Foreign Keys
    
    source_id = db.Column(
        db.Integer,
        db.ForeignKey('sources.id'),
        nullable=False
    )
    # Links to the source this content came from
    
    # Content Identification
    
    external_id = db.Column(
        db.String(500),
        nullable=False,
        unique=True,
        index=True
    )
    # Unique identifier from external source
    # YouTube: video ID (dQw4w9WgXcQ)
    # RSS: GUID or link
    # Blog: URL
    # index=True for fast lookups (deduplication)
    
    content_hash = db.Column(
        db.String(64),
        nullable=True,
        unique=True,
        index=True
    )
    # SHA-256 hash of content (backup deduplication)
    # Catches duplicates even with different IDs
    
    # Content Data
    
    title = db.Column(
        db.String(500),
        nullable=False
    )
    # Original title from source
    
    content = db.Column(
        db.Text,
        nullable=False
    )
    # Full content/transcript
    # YouTube: transcript text
    # RSS: article content
    # Blog: scraped text
    
    url = db.Column(
        db.String(1000),
        nullable=False
    )
    # Direct link to original content
    # This goes in the email!
    
    author = db.Column(
        db.String(255),
        nullable=True
    )
    # Author name (if available)
    
    published_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    # When the content was originally published
    # index=True for date-based queries
    
    # Processing Status
    
    processed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )
    # Has this been processed into an Article?
    # False = needs processing
    # True = already processed
    # index=True for querying unprocessed items
    
    processed_at = db.Column(
        db.DateTime,
        nullable=True
    )
    # When it was processed
    
    # Metadata
    
    word_count = db.Column(
        db.Integer,
        nullable=True
    )
    # Length of content 
    
    language = db.Column(
        db.String(10),
        nullable=True,
        default='en'
    )
    # Content language 
    
    # Relationships
    
    # Many content items belong to one source
    source = db.relationship(
        'Source',
        backref='content_items',
        lazy=True
    )
    # Usage: item.source.name
    # Usage: source.content_items (get all items from source)
    
    # One content item has one article (after processing)
    # We'll add this relationship from the Article model
    
    # Methods
    
    def __repr__(self):
        """String representation"""
        return f"<ContentItem {self.title[:30]}... from {self.source.name if self.source else 'Unknown'}>"
    
    def generate_content_hash(self):
        """
        Generate SHA-256 hash from title and content.
        
        Used for duplicate detection when external_id is not reliable.
        
        Returns:
            str: 64-character hex hash
        """
        # Normalize text
        text = f"{self.title}|{self.content}".lower().strip()
        text = ' '.join(text.split())  # Remove extra whitespace
        
        # Generate hash
        hash_object = hashlib.sha256(text.encode('utf-8'))
        return hash_object.hexdigest()
    
    def calculate_word_count(self):
        """Calculate and store word count of content"""
        if self.content:
            self.word_count = len(self.content.split())
    
    def mark_processed(self):
        """Mark this content item as processed"""
        self.processed = True
        self.processed_at = datetime.utcnow()
        self.save()
    
    @classmethod
    def get_unprocessed(cls, limit=50):
        """
        Get unprocessed content items.
        
        Args:
            limit (int): Maximum number to return
            
        Returns:
            list: Unprocessed ContentItem objects
        """
        return cls.query.filter_by(
            processed=False
        ).order_by(
            cls.published_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def check_exists(cls, external_id=None, content_hash=None):
        """
        Check if content already exists (deduplication).
        
        Args:
            external_id (str): External identifier
            content_hash (str): Content hash
            
        Returns:
            ContentItem or None: Existing item or None if new
        """
        if external_id:
            existing = cls.query.filter_by(external_id=external_id).first()
            if existing:
                return existing
        
        if content_hash:
            existing = cls.query.filter_by(content_hash=content_hash).first()
            if existing:
                return existing
        
        return None


class Article(BaseModel):
    """
    Processed and summarized content ready for digest.
    
    Created from ContentItems after:
    - AI summarization (Gemini)
    - Quality scoring
    - Topic extraction
    
    These are what actually go into email digests.
    
    Relationships:
    - Created from one ContentItem
    - Can be grouped with other Articles (topic clustering)
    
    Example:
        article = Article(
            content_item_id=1,
            summary="OpenAI announced GPT-5 with breakthrough capabilities...",
            quality_score=9,
            topic_cluster="gpt-5-release"
        )
        article.save()
    """
    
    # Table name
    __tablename__ = 'articles'
    
    # Foreign Keys
    
    content_item_id = db.Column(
        db.Integer,
        db.ForeignKey('content_items.id'),
        nullable=False,
        unique=True
    )
    # Links to the original content item
    # unique=True: one content item = one article
    
    # Processed Content
    
    title = db.Column(
        db.String(500),
        nullable=False
    )
    # Cleaned/processed title (might differ from original)
    
    summary = db.Column(
        db.Text,
        nullable=False
    )
    # AI-generated summary from Gemini
    # Length controlled by MAX_SUMMARY_LENGTH config
    
    # Quality & Relevance
    
    quality_score = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )
    # Quality/relevance score from 0-10
    # Used to filter: only include if score >= MIN_QUALITY_SCORE
    # index=True for filtering queries
    
    relevance_tags = db.Column(
        db.JSON,
        nullable=True
    )
    # AI-extracted tags: ["machine-learning", "gpt", "natural-language"]
    # JSON field stores array
    
    # Topic Clustering
    
    topic_cluster = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )
    # Topic identifier for grouping related articles
    # Example: "gpt-5-release", "ai-safety-research"
    # index=True for grouping queries
    
    cluster_summary = db.Column(
        db.Text,
        nullable=True
    )
    # Combined summary when multiple articles on same topic
    # Only primary article in cluster has this
    
    is_primary = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    # Is this the main article for its topic cluster?
    # Primary article shows cluster_summary in digest
    
    # Digest Status
    
    included_in_digest = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )
    # Has this been included in a digest email?
    # False = available for next digest
    # True = already sent
    # index=True for querying available articles
    
    digest_date = db.Column(
        db.Date,
        nullable=True,
        index=True
    )
    # Which digest date this was included in
    # Used to prevent duplicates in same digest
    
    # Metadata
    
    published_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    # Original publication date (copied from ContentItem)
    # index=True for date-based sorting
    
    # Relationships
    
    # One article belongs to one content item
    content_item = db.relationship(
        'ContentItem',
        backref=db.backref('article', uselist=False, lazy=True),
        lazy=True
    )
    # Usage: article.content_item.url
    # Usage: content_item.article.summary
    # backref with uselist=False creates one-to-one relationship
    
    # Methods
    
    def __repr__(self):
        """String representation"""
        score = self.quality_score or '?'
        return f"<Article [{score}/10] {self.title[:30]}...>"
    
    def to_dict(self):
        """
        Convert to dictionary with additional fields.
        
        Includes source information from content_item.
        """
        data = super().to_dict()
        
        # Add source info
        if self.content_item and self.content_item.source:
            data['source_name'] = self.content_item.source.name
            data['source_type'] = self.content_item.source.source_type.value
            data['url'] = self.content_item.url
        
        # Add author
        if self.content_item and self.content_item.author:
            data['author'] = self.content_item.author
        
        return data
    
    def get_source_link(self):
        """
        Get the original source URL.
        
        Returns:
            str: URL to original content
        """
        if self.content_item:
            return self.content_item.url
        return None
    
    def mark_included_in_digest(self, digest_date):
        """
        Mark this article as included in a digest.
        
        Args:
            digest_date (date): Date of the digest
        """
        self.included_in_digest = True
        self.digest_date = digest_date
        self.save()
    
    @classmethod
    def get_for_digest(cls, max_items=10, min_quality=6):
        """
        Get articles ready for digest.
        
        Filters:
        - Not yet included in digest
        - Quality score >= min_quality
        - Ordered by quality score (best first)
        
        Args:
            max_items (int): Maximum number of articles
            min_quality (int): Minimum quality score
            
        Returns:
            list: Article objects ready for digest
        """
        return cls.query.filter(
            cls.included_in_digest == False,
            cls.quality_score >= min_quality
        ).order_by(
            cls.quality_score.desc(),
            cls.published_at.desc()
        ).limit(max_items).all()
    
    @classmethod
    def get_by_topic_cluster(cls, topic_cluster):
        """
        Get all articles in a topic cluster.
        
        Args:
            topic_cluster (str): Cluster identifier
            
        Returns:
            list: Articles in this cluster
        """
        return cls.query.filter_by(
            topic_cluster=topic_cluster
        ).order_by(
            cls.is_primary.desc(),  # Primary first
            cls.quality_score.desc()
        ).all()
    
    @classmethod
    def get_recent(cls, days=7, min_quality=6):
        """
        Get recent high-quality articles.
        
        Args:
            days (int): Number of days to look back
            min_quality (int): Minimum quality score
            
        Returns:
            list: Recent articles
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.published_at >= cutoff_date,
            cls.quality_score >= min_quality
        ).order_by(
            cls.published_at.desc()
        ).all()