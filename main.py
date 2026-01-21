"""
AI News Aggregator - Main Application Entry Point

This is the main entry point for the AI News Aggregator application.
It initializes Flask, connects configuration, and starts the web server.
"""

from flask import Flask
from config import get_config
import logging
import os


def create_app():
    """
    Application Factory Pattern
    
    Creates and configures the Flask application instance.
    This pattern allows for:
    - Easy testing (can create multiple app instances)
    - Different configurations (dev, prod, test)
    - Better organization
    
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    cfg = get_config()
    app.config.from_object(cfg)
    
    # Set up logging
    setup_logging(app)
    
    # Log startup information
    app.logger.info("=" * 50)
    app.logger.info("AI News Aggregator Starting...")
    app.logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    app.logger.info(f"Debug Mode: {app.debug}")
    app.logger.info(f"Testing Mode: {app.testing}")
    app.logger.info("=" * 50)
    
    # Register routes
    register_routes(app)
    
    # Initialize extensions (database, scheduler, etc.) will go here later
    # initialize_extensions(app)
    
    return app


def setup_logging(app):
    """
    Configure application logging
    
    Sets up logging based on LOG_LEVEL from config.
    Logs will help us debug issues and monitor the application.
    
    Args:
        app: Flask application instance
    """
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging format
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set Flask's logger to same level
    app.logger.setLevel(numeric_level)
    
    app.logger.info(f"Logging configured at {log_level} level")


def register_routes(app):
    """
    Register all application routes
    
    For now, we'll add a simple test route.
    Later, we'll import and register blueprints from app/api/
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Root endpoint - Welcome message"""
        return {
            'message': 'Welcome to AI News Aggregator API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'api_docs': 'Coming soon...'
            }
        }
    
    @app.route('/health')
    def health():
        """Health check endpoint - Used to verify app is running"""
        return {
            'status': 'healthy',
            'message': 'AI News Aggregator is running!',
            'debug': app.debug,
            'testing': app.testing
        }
    
    app.logger.info("Routes registered successfully")


# Entry point when running directly
if __name__ == '__main__':
    # Create the application
    app = create_app()
    
    # Get port from environment or use 5000
    port = int(os.getenv('PORT', 8000))
    
    # Run the application
    app.logger.info(f"Starting Flask server on port {port}")
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=port,
        debug=app.debug
    )