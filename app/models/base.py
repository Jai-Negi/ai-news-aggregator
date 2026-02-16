"""
Database Base Configuration

This module sets up the database connection and provides base functionality
for all models. It includes:
- SQLAlchemy initialization
- Base model class with common fields
- Database session management
- Helper methods for all models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import inspect

# Initialize SQLAlchemy
# This creates a database object that manages connections and sessions
db = SQLAlchemy()


class BaseModel(db.Model):
    """
    Abstract base model with common fields and methods.
    
    All other models inherit from this class to get:
    - id (primary key)
    - created_at (timestamp)
    - updated_at (timestamp)
    - Common CRUD methods
    
    This is an abstract class, meaning it won't create its own table.
    It just provides functionality to child classes.
    """
    
    # Tell SQLAlchemy this is abstract 
    __abstract__ = True
    
    # Common Fields 
    
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    # Primary key - unique identifier for each row
    # autoincrement=True means database automatically assigns 1, 2, 3, etc.
    
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    # Timestamp when record was created
    # default=datetime.utcnow means automatically set to current time
    # nullable=False means this field is required
    
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    # Timestamp when record was last updated
    # onupdate=datetime.utcnow means automatically update when row changes
    
    # Helper Methods 
    
    def save(self):
        """
        Save the current instance to the database.
        
        Usage:
            user = User(email="test@example.com")
            user.save()  # Saves to database
        """
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """
        Delete the current instance from the database.
        
        Usage:
            user = User.query.first()
            user.delete()  # Removes from database
        """
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """
        Update multiple fields at once.
        
        Usage:
            user = User.query.first()
            user.update(email="new@example.com", active=True)
        
        Args:
            **kwargs: Dictionary of field names and values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        
        Useful for:
        - Returning as JSON in API responses
        - Serialization
        - Debugging
        
        Usage:
            user = User.query.first()
            data = user.to_dict()
            # Returns: {'id': 1, 'email': 'test@example.com', ...}
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        """
        String representation of the model.
        
        Makes debugging easier by showing useful info when you print the object.
        
        Usage:
            user = User.query.first()
            print(user)
            # Shows: <User id=1>
        
        Returns:
            str: String representation
        """
        return f"<{self.__class__.__name__} id={self.id}>"


def init_db(app):
    """
    Initialize database with Flask app.
    
    This function:
    1. Configures SQLAlchemy with Flask
    2. Sets up database connection
    3. Creates all tables if they don't exist
    
    Usage (in main.py):
        from app.models.base import init_db
        
        app = create_app()
        init_db(app)
    
    Args:
        app: Flask application instance
    """
    # Configure SQLAlchemy with Flask app
    db.init_app(app)
    
    # Create all tables within application context
    with app.app_context():
        # Import all models so SQLAlchemy knows about them
        from app.models import source, article, subscriber
        
        # Create tables if they don't exist
        db.create_all()
        
        app.logger.info("Database initialized successfully")