"""
Configuration Package

This package manages all application configuration.

Usage:
    from config import get_config, Config
    
    cfg = get_config()
    print(cfg.GEMINI_API_KEY)
"""

from config.settings import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    get_config
)

# This allows: from config import Config
# Instead of: from config.settings import Config

__all__ = [
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'get_config'
]