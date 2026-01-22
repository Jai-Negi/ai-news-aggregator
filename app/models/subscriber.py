"""
Subscriber Models

Contains two models:
1. Subscriber - Email subscribers for the digest
2. DigestLog - Tracks sent digest emails

Flow: Subscriber → DigestLog (when digest is sent)
"""

from app.models.base import db, BaseModel
from datetime import datetime, date
from sqlalchemy import Enum
import enum


class SubscriberStatus(enum.Enum):
    """
    Status of a subscriber.
    
    Using enum ensures only valid statuses.
    """
    ACTIVE = "active"           # Receiving digests
    PAUSED = "paused"           # Temporarily paused
    UNSUBSCRIBED = "unsubscribed"  # Opted out
    BOUNCED = "bounced"         # Email bounced (invalid)


class DigestFrequency(enum.Enum):
    """
    How often subscriber receives digests.
    
    For future expansion (currently only daily).
    """
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Subscriber(BaseModel):
    """
    Email subscribers for AI news digest.
    
    Stores subscriber information and preferences.
    
    Relationships:
    - Has many DigestLogs (history of sent emails)
    
    Example:
        subscriber = Subscriber(
            email="user@example.com",
            name="John Doe",
            frequency=DigestFrequency.DAILY
        )
        subscriber.save()
    """
    
    # Table name
    __tablename__ = 'subscribers'
    
    # ================================
    # Subscriber Information
    # ================================
    
    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True
    )
    # Email address (unique per subscriber)
    # index=True for fast lookups and deduplication
    
    name = db.Column(
        db.String(255),
        nullable=True
    )
    # Subscriber's name (optional)
    # Used for personalization: "Hi John!"
    
    # ================================
    # Subscription Settings
    # ================================
    
    status = db.Column(
        Enum(SubscriberStatus),
        nullable=False,
        default=SubscriberStatus.ACTIVE,
        index=True
    )
    # Subscription status
    # index=True for filtering active subscribers
    
    frequency = db.Column(
        Enum(DigestFrequency),
        nullable=False,
        default=DigestFrequency.DAILY
    )
    # How often to receive digests
    # Currently only DAILY is implemented
    
    # ================================
    # Preferences
    # ================================
    
    topics_of_interest = db.Column(
        db.JSON,
        nullable=True
    )
    # Array of topics subscriber is interested in
    # Example: ["machine-learning", "gpt", "ai-safety"]
    # Future: Filter digest to only these topics
    
    min_quality_score = db.Column(
        db.Integer,
        nullable=False,
        default=6
    )
    # Minimum quality score for articles (0-10)
    # Only send articles with score >= this value
    
    max_articles_per_digest = db.Column(
        db.Integer,
        nullable=False,
        default=10
    )
    # Maximum number of articles in each digest
    # Prevents overwhelming the subscriber
    
    # ================================
    # Subscription Management
    # ================================
    
    subscribed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    # When they subscribed
    
    unsubscribed_at = db.Column(
        db.DateTime,
        nullable=True
    )
    # When they unsubscribed (if applicable)
    
    last_digest_sent_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    # When we last sent them a digest
    # Used to prevent duplicate sends
    # index=True for scheduling queries
    
    # ================================
    # Tokens & Security
    # ================================
    
    unsubscribe_token = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        index=True
    )
    # Unique token for unsubscribe link
    # Example: /unsubscribe?token=abc123...
    # index=True for fast token lookups
    
    # ================================
    # Metadata
    # ================================
    
    source = db.Column(
        db.String(100),
        nullable=True
    )
    # How they subscribed
    # Examples: "website", "referral", "api"
    
    ip_address = db.Column(
        db.String(45),
        nullable=True
    )
    # IP address when subscribed (for spam prevention)
    # IPv6 can be up to 45 characters
    
    user_agent = db.Column(
        db.String(500),
        nullable=True
    )
    # Browser/device info when subscribed
    
    total_digests_sent = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Counter for statistics
    
    total_digests_opened = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Tracks email opens (requires tracking pixel)
    # Future feature
    
    # ================================
    # Relationships
    # ================================
    
    # One subscriber has many digest logs
    digest_logs = db.relationship(
        'DigestLog',
        backref='subscriber',
        lazy=True,
        cascade='all, delete-orphan'
    )
    # Usage: subscriber.digest_logs (get all sent emails)
    # cascade='all, delete-orphan' = delete logs when subscriber deleted
    
    # ================================
    # Methods
    # ================================
    
    def __repr__(self):
        """String representation"""
        return f"<Subscriber {self.email} ({self.status.value})>"
    
    def generate_unsubscribe_token(self):
        """
        Generate unique unsubscribe token.
        
        Returns:
            str: 64-character hex token
        """
        import secrets
        return secrets.token_urlsafe(48)[:64]
    
    def get_unsubscribe_url(self, base_url="https://your-domain.com"):
        """
        Get unsubscribe URL for this subscriber.
        
        Args:
            base_url (str): Base URL of your application
            
        Returns:
            str: Full unsubscribe URL
        """
        return f"{base_url}/unsubscribe?token={self.unsubscribe_token}"
    
    def mark_digest_sent(self):
        """Mark that a digest was sent to this subscriber"""
        self.last_digest_sent_at = datetime.utcnow()
        self.total_digests_sent += 1
        self.save()
    
    def unsubscribe(self):
        """Unsubscribe this subscriber"""
        self.status = SubscriberStatus.UNSUBSCRIBED
        self.unsubscribed_at = datetime.utcnow()
        self.save()
    
    def pause(self):
        """Temporarily pause subscription"""
        self.status = SubscriberStatus.PAUSED
        self.save()
    
    def reactivate(self):
        """Reactivate subscription"""
        self.status = SubscriberStatus.ACTIVE
        self.unsubscribed_at = None
        self.save()
    
    def should_receive_digest_today(self):
        """
        Check if subscriber should receive digest today.
        
        Checks:
        - Status is ACTIVE
        - Frequency matches (currently only DAILY)
        - Haven't already sent today
        
        Returns:
            bool: True if should send, False otherwise
        """
        # Must be active
        if self.status != SubscriberStatus.ACTIVE:
            return False
        
        # Check frequency (currently only DAILY)
        if self.frequency != DigestFrequency.DAILY:
            return False
        
        # Check if already sent today
        if self.last_digest_sent_at:
            today = date.today()
            last_sent_date = self.last_digest_sent_at.date()
            
            if last_sent_date == today:
                # Already sent today
                return False
        
        return True
    
    @classmethod
    def get_active_subscribers(cls):
        """
        Get all active subscribers.
        
        Returns:
            list: Active Subscriber objects
        """
        return cls.query.filter_by(
            status=SubscriberStatus.ACTIVE
        ).all()
    
    @classmethod
    def get_for_daily_digest(cls):
        """
        Get subscribers who should receive today's digest.
        
        Filters:
        - Status = ACTIVE
        - Frequency = DAILY
        - Not sent today yet
        
        Returns:
            list: Subscriber objects ready for digest
        """
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        return cls.query.filter(
            cls.status == SubscriberStatus.ACTIVE,
            cls.frequency == DigestFrequency.DAILY,
            db.or_(
                cls.last_digest_sent_at == None,
                cls.last_digest_sent_at < today_start
            )
        ).all()
    
    @classmethod
    def find_by_email(cls, email):
        """
        Find subscriber by email.
        
        Args:
            email (str): Email address
            
        Returns:
            Subscriber or None
        """
        return cls.query.filter_by(email=email.lower().strip()).first()
    
    @classmethod
    def find_by_token(cls, token):
        """
        Find subscriber by unsubscribe token.
        
        Args:
            token (str): Unsubscribe token
            
        Returns:
            Subscriber or None
        """
        return cls.query.filter_by(unsubscribe_token=token).first()


class DigestLog(BaseModel):
    """
    Log of sent digest emails.
    
    Tracks when and what was sent to each subscriber.
    Useful for:
    - Preventing duplicate sends
    - Analytics and statistics
    - Debugging delivery issues
    
    Relationships:
    - Belongs to one Subscriber
    
    Example:
        log = DigestLog(
            subscriber_id=1,
            digest_date=date.today(),
            articles_included=10,
            status="sent"
        )
        log.save()
    """
    
    # Table name
    __tablename__ = 'digest_logs'
    
    # ================================
    # Foreign Keys
    # ================================
    
    subscriber_id = db.Column(
        db.Integer,
        db.ForeignKey('subscribers.id'),
        nullable=False,
        index=True
    )
    # Links to subscriber who received this digest
    # index=True for fast queries by subscriber
    
    # ================================
    # Digest Information
    # ================================
    
    digest_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )
    # Date of the digest content
    # Example: January 22, 2026
    # index=True for date-based queries
    
    sent_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    # When the email was actually sent
    
    # ================================
    # Content Details
    # ================================
    
    articles_included = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Number of articles in this digest
    
    article_ids = db.Column(
        db.JSON,
        nullable=True
    )
    # Array of article IDs that were included
    # Example: [1, 5, 8, 12, 15]
    # Useful for tracking which articles were sent
    
    topic_clusters = db.Column(
        db.JSON,
        nullable=True
    )
    # Array of topic clusters included
    # Example: ["gpt-5-release", "ai-safety-research"]
    
    # ================================
    # Delivery Status
    # ================================
    
    status = db.Column(
        db.String(50),
        nullable=False,
        default='pending',
        index=True
    )
    # Delivery status:
    # - "pending" = queued for sending
    # - "sent" = successfully sent
    # - "failed" = delivery failed
    # - "bounced" = email bounced
    # index=True for filtering by status
    
    error_message = db.Column(
        db.Text,
        nullable=True
    )
    # Error details if delivery failed
    
    # ================================
    # Email Service Response
    # ================================
    
    email_service_id = db.Column(
        db.String(255),
        nullable=True
    )
    # ID from email service (Resend, SendGrid, etc.)
    # Used to track delivery status
    
    # ================================
    # Engagement Tracking
    # ================================
    
    opened_at = db.Column(
        db.DateTime,
        nullable=True
    )
    # When email was opened (requires tracking pixel)
    # Future feature
    
    clicked_at = db.Column(
        db.DateTime,
        nullable=True
    )
    # When a link was clicked
    # Future feature
    
    clicks_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    # Number of link clicks
    # Future feature
    
    # ================================
    # Methods
    # ================================
    
    def __repr__(self):
        """String representation"""
        return f"<DigestLog {self.digest_date} → {self.subscriber.email if self.subscriber else 'Unknown'} ({self.status})>"
    
    def mark_sent(self, email_service_id=None):
        """
        Mark digest as successfully sent.
        
        Args:
            email_service_id (str): ID from email service
        """
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        if email_service_id:
            self.email_service_id = email_service_id
        self.save()
    
    def mark_failed(self, error_message):
        """
        Mark digest as failed.
        
        Args:
            error_message (str): Error details
        """
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def mark_opened(self):
        """Mark that email was opened"""
        if not self.opened_at:
            self.opened_at = datetime.utcnow()
            self.save()
            
            # Update subscriber stats
            if self.subscriber:
                self.subscriber.total_digests_opened += 1
                self.subscriber.save()
    
    def record_click(self):
        """Record a link click"""
        if not self.clicked_at:
            self.clicked_at = datetime.utcnow()
        
        self.clicks_count += 1
        self.save()
    
    @classmethod
    def get_by_date(cls, digest_date):
        """
        Get all digest logs for a specific date.
        
        Args:
            digest_date (date): Date to query
            
        Returns:
            list: DigestLog objects
        """
        return cls.query.filter_by(digest_date=digest_date).all()
    
    @classmethod
    def get_recent_logs(cls, days=7):
        """
        Get digest logs from recent days.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            list: DigestLog objects
        """
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=days)
        
        return cls.query.filter(
            cls.digest_date >= cutoff_date
        ).order_by(
            cls.digest_date.desc()
        ).all()
    
    @classmethod
    def get_statistics(cls, start_date=None, end_date=None):
        """
        Get digest statistics.
        
        Args:
            start_date (date): Start of period
            end_date (date): End of period
            
        Returns:
            dict: Statistics
        """
        query = cls.query
        
        if start_date:
            query = query.filter(cls.digest_date >= start_date)
        if end_date:
            query = query.filter(cls.digest_date <= end_date)
        
        logs = query.all()
        
        total = len(logs)
        sent = len([l for l in logs if l.status == 'sent'])
        failed = len([l for l in logs if l.status == 'failed'])
        opened = len([l for l in logs if l.opened_at is not None])
        
        return {
            'total': total,
            'sent': sent,
            'failed': failed,
            'pending': total - sent - failed,
            'opened': opened,
            'open_rate': (opened / sent * 100) if sent > 0 else 0
        }