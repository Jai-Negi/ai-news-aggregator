"""
Configuration Settings for AI News Aggregator

This module manages all application configuration including:
- Environment variables loading
- API credentials
- Database settings  
- Application behavior settings
- Development vs Production configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads the .env file and makes variables available via os.getenv()
load_dotenv()


class Config:
    """
    Base configuration class
    
    Contains all common settings shared between development and production.
    Uses environment variables with sensible defaults as fallback.
    """
    
    # Flask Application Settings

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Used by Flask for session encryption and CSRF protection
    # In production, this MUST be a random, secret value
    
    

    # Database Configuration

    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://ai_news_user:ai_news_password@localhost:5432/ai_news_db'
    )
    # PostgreSQL connection string
    # Format: postgresql://username:password@host:port/database_name
    # Default uses our docker-compose database
    
    
    
    # Google Gemini AI
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    # Free tier: 60 requests per minute
    # Get from: https://makersuite.google.com/app/apikey
    
    
  
    # Resend Email Service
 
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    # Free tier: 3,000 emails per month
    # Get from: https://resend.com/api-keys
    
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'onboarding@resend.dev')
    # Email address to send from
    # Free tier can use: onboarding@resend.dev
    # Or verify your own domain
    
    
    
    # Content Sources

    YOUTUBE_CHANNELS = os.getenv('YOUTUBE_CHANNELS', '').split(',')
    # Comma-separated YouTube channel IDs
    # Example: "UCbfYPyITQ-7l4upoX8nvctg,UCYO_jab_esuFRV4b17AJtAw"
    # Gets split into a Python list: ['id1', 'id2']
    
    RSS_FEEDS = os.getenv('RSS_FEEDS', '').split(',')
    # Comma-separated RSS feed URLs
    # Example: "https://openai.com/blog/rss,https://anthropic.com/news/rss"
    # Gets split into a Python list
    
    
    # ================================
    # Scheduling Configuration
    # ================================
    DIGEST_SEND_HOUR = int(os.getenv('DIGEST_SEND_HOUR', 8))
    # Hour of day to send digest (0-23, 24-hour format)
    # Default: 8 = 8:00 AM
    
    DIGEST_SEND_MINUTE = int(os.getenv('DIGEST_SEND_MINUTE', 0))
    # Minute of hour to send digest (0-59)
    # Default: 0 = on the hour
    
    CONTENT_FETCH_INTERVAL = int(os.getenv('CONTENT_FETCH_INTERVAL', 6))
    # How often to fetch new content (in hours)
    # Default: 6 = fetch every 6 hours
    
    
    # ================================
    # Content Processing Settings
    # ================================
    MAX_SUMMARY_LENGTH = int(os.getenv('MAX_SUMMARY_LENGTH', 300))
    # Maximum words in AI-generated summary
    # Shorter = less tokens used = lower cost
    
    MIN_QUALITY_SCORE = int(os.getenv('MIN_QUALITY_SCORE', 6))
    # Minimum quality score (0-10) to include in digest
    # Higher = more selective, fewer items
    
    MAX_ITEMS_PER_DIGEST = int(os.getenv('MAX_ITEMS_PER_DIGEST', 10))
    # Maximum number of items in each email digest
    # Prevents overwhelming subscribers
    
    
    # ================================
    # Logging Configuration
    # ================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    # DEBUG: Most verbose (use in development)
    # INFO: Standard (use in production)
    # ERROR: Only errors


class DevelopmentConfig(Config):
    """
    Development-specific configuration
    
    Used when running locally on your laptop.
    Enables debug mode and detailed error messages.
    """
    DEBUG = True
    # Shows detailed error pages with stack traces
    # NEVER enable in production (security risk)
    
    TESTING = False
    # Not in test mode


class ProductionConfig(Config):
    """
    Production-specific configuration
    
    Used when deployed to Render.
    Disables debug mode for security.
    """
    DEBUG = False
    # Hides detailed errors from users
    # Shows generic error pages instead
    
    TESTING = False


class TestingConfig(Config):
    """
    Testing-specific configuration
    
    Used when running tests with pytest.
    Uses in-memory database for speed.
    """
    TESTING = True
    DEBUG = True
    
    # Use SQLite in-memory database for tests
    DATABASE_URL = 'sqlite:///:memory:'
    # Fast and isolated (doesn't affect real database)


# ================================
# Configuration Dictionary
# ================================
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get the appropriate configuration based on environment
    
    Reads FLASK_ENV environment variable to determine which config to use.
    Falls back to development config if not set.
    
    Returns:
        Config class: DevelopmentConfig, ProductionConfig, or TestingConfig
        
    Example:
        >>> from config import get_config
        >>> cfg = get_config()
        >>> print(cfg.DEBUG)
        True
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])