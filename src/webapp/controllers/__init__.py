"""
AOF Video Stream - Controllers Package

This package contains request handlers and routing logic for the application.
"""

from flask import Flask
from .main_controller import main_bp
from .camera_controller import camera_bp
from .api_controller import api_bp

def register_blueprints(app: Flask) -> None:
    """
    Register all blueprint controllers with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    # Register main routes
    app.register_blueprint(main_bp)
    
    # Register camera routes
    app.register_blueprint(camera_bp, url_prefix='/camera')
    
    # Register API routes
    app.register_blueprint(api_bp, url_prefix='/api')
