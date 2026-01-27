"""
App Package Initialization

Sets up Flask app and database connection.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (without app yet)
db = SQLAlchemy()