"""
Services Package

External API integrations and service connectors.

Available services:
- GeminiService: AI summarization and analysis
"""

from app.services.gemini_service import GeminiService

__all__ = [
    'GeminiService',
]