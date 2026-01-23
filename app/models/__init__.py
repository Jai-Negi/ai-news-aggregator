"""
Models Package

Exports all database models for easy importing.

Usage:
    from app.models import Source, Article, Subscriber
    from app.models.base import db, init_db
"""

# Import base components
from app.models.base import db, BaseModel, init_db

# Import enums
from app.models.source import SourceType
from app.models.subscriber import SubscriberStatus, DigestFrequency

# Import models
from app.models.source import Source
from app.models.article import ContentItem, Article
from app.models.subscriber import Subscriber, DigestLog

# Export all models and utilities
__all__ = [
    # Base components
    'db',
    'BaseModel',
    'init_db',
    
    # Enums
    'SourceType',
    'SubscriberStatus',
    'DigestFrequency',
    
    # Models
    'Source',
    'ContentItem',
    'Article',
    'Subscriber',
    'DigestLog',
]