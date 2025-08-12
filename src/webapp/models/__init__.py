"""
AOF Video Stream - Models Package

This package contains data models and business logic for the application.
"""

from flask import Flask
from .camera_model import CameraModel
from .stream_model import StreamModel

def init_models(app: Flask) -> None:
    """
    Initialize all models with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Initialize models if needed
    # This could include database connections, cache setup, etc.
    pass
