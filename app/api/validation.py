"""
Validation utilities for subscriber management.

This module is shared between:
- CLI scripts (manual management)
- API endpoints (website subscriptions)
- Admin interface (future)
"""

import re
import secrets
import logging
from typing import Tuple, Optional
from app.models import Subscriber, SubscriberStatus, DigestFrequency, db

logger = logging.getLogger(__name__)


class SubscriberValidator:
    """
    Validates and manages subscriber operations.
    
    Used by both CLI and API to ensure consistent validation.
    """
    
    # Email regex pattern 
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Blocked domains 
    BLOCKED_DOMAINS = [
        'tempmail.com',
        'guerrillamail.com',
        '10minutemail.com',
        'throwaway.email',
        'mailinator.com',
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address.
        
        Args:
            email: Email address to validate
        
        Returns:
            tuple: (is_valid, error_message)
                - (True, None) if valid
                - (False, "error message") if invalid
        
        Example:
            valid, error = SubscriberValidator.validate_email("test@gmail.com")
            if not valid:
                print(f"Invalid: {error}")
        """
        # Check if empty
        if not email:
            return False, "Email address is required"
        
        # Strip whitespace
        email = email.strip().lower()
        
        # Check length
        if len(email) > 255:
            return False, "Email address is too long (max 255 characters)"
        
        # Check format
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Check blocked domains
        domain = email.split('@')[1]
        if domain in cls.BLOCKED_DOMAINS:
            return False, f"Temporary/disposable email addresses are not allowed"
        
        return True, None
    
    @classmethod
    def check_exists(cls, email: str) -> Optional[Subscriber]:
        """
        Check if email already exists in database.
        
        Args:
            email: Email to check
        
        Returns:
            Subscriber object if exists, None otherwise
        """
        email = email.strip().lower()
        return Subscriber.query.filter_by(email=email).first()
    
    @classmethod
    def add_subscriber(
        cls,
        email: str,
        skip_validation: bool = False
    ) -> Tuple[bool, str, Optional[Subscriber]]:
        """
        Add a new subscriber.
        
        Args:
            email: Email address
            skip_validation: Skip email validation (for testing)
        
        Returns:
            tuple: (success, message, subscriber)
        
        Example:
            success, msg, subscriber = SubscriberValidator.add_subscriber("test@gmail.com")
            if success:
                print(f"Added: {subscriber.email}")
            else:
                print(f"Error: {msg}")
        """
        email = email.strip().lower()
        
        # Validate email format
        if not skip_validation:
            valid, error = cls.validate_email(email)
            if not valid:
                return False, error, None
        
        # Check if already exists
        existing = cls.check_exists(email)
        if existing:
            if existing.status == SubscriberStatus.ACTIVE:
                return False, f"Email already subscribed: {email}", existing
            else:
                # Reactivate
                existing.status = SubscriberStatus.ACTIVE
                db.session.commit()
                return True, f"Reactivated subscription for: {email}", existing
        
        # Create new subscriber
        try:
            subscriber = Subscriber(
                email=email,
                status=SubscriberStatus.ACTIVE,
                frequency=DigestFrequency.DAILY,
                unsubscribe_token=secrets.token_urlsafe(32)  # Generate unique unsubscribe token
            )
            
            db.session.add(subscriber)
            db.session.commit()
            
            logger.info(f"New subscriber added: {email}")
            return True, f"Successfully subscribed: {email}", subscriber
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding subscriber {email}: {e}")
            return False, f"Database error: {str(e)}", None
    
    @classmethod
    def remove_subscriber(cls, email: str) -> Tuple[bool, str]:
        """
        Remove/deactivate a subscriber.
        
        Args:
            email: Email to remove
        
        Returns:
            tuple: (success, message)
        """
        email = email.strip().lower()
        
        subscriber = cls.check_exists(email)
        
        if not subscriber:
            return False, f"Email not found: {email}"
        
        try:
            subscriber.status = SubscriberStatus.UNSUBSCRIBED
            db.session.commit()
            
            logger.info(f"Subscriber unsubscribed: {email}")
            return True, f"Unsubscribed: {email}"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error unsubscribing {email}: {e}")
            return False, f"Database error: {str(e)}"
    
    @classmethod
    def get_all_active(cls):
        """Get all active subscribers."""
        return Subscriber.query.filter_by(status=SubscriberStatus.ACTIVE).all()
    
    @classmethod
    def get_all(cls):
        """Get all subscribers (including inactive)."""
        return Subscriber.query.all()
    
    @classmethod
    def get_stats(cls) -> dict:
        """
        Get subscriber statistics.
        
        Returns:
            dict: Statistics
        """
        total = Subscriber.query.count()
        active = Subscriber.query.filter_by(status=SubscriberStatus.ACTIVE).count()
        unsubscribed = Subscriber.query.filter_by(status=SubscriberStatus.UNSUBSCRIBED).count()
        bounced = Subscriber.query.filter_by(status=SubscriberStatus.BOUNCED).count()
        
        return {
            'total': total,
            'active': active,
            'unsubscribed': unsubscribed,
            'bounced': bounced
        }