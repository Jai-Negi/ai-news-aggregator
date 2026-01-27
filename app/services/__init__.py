"""
Services Package

External API integrations and service connectors.

Available services:
- GeminiService: AI summarization and analysis
- YouTubeService: YouTube video and transcript fetching
- RSSService: RSS feed parsing
"""

from app.services.gemini_service import GeminiService
from app.services.youtube_service import YouTubeService
from app.services.rss_service import RSSService

__all__ = [
    'GeminiService',
    'YouTubeService',
    'RSSService',
]