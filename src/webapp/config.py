"""
AOF Video Stream - Application Configuration

Configuration classes for different environments.
"""

import os
from typing import Optional

class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'aof-video-stream-secret-key-2025')
    DEBUG = False
    TESTING = False
    
    # Server Settings
    HOST = os.getenv('HOST', 'localhost')
    PORT = int(os.getenv('PORT', 5000))
    
    # Camera Settings
    DEFAULT_RESOLUTION = (640, 480)
    DEFAULT_FPS = 30
    MAX_CAMERAS = 10
    
    # Streaming Settings
    STREAM_QUALITY = 'medium'
    FRAME_BUFFER_SIZE = 10
    WEBSOCKET_TIMEOUT = 30
    
    # Static Files
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'
    
    # API Settings
    API_PREFIX = '/api'
    API_VERSION = 'v1'


class DevelopmentConfig(BaseConfig):
    """Development configuration with debug enabled."""
    
    DEBUG = True
    
    # Development specific settings
    CAMERA_MOCK_MODE = False  # Set to True to use mock camera data
    LOG_LEVEL = 'DEBUG'
    
    # Performance settings for development
    STREAM_QUALITY = 'medium'
    DEFAULT_FPS = 30


class ProductionConfig(BaseConfig):
    """Production configuration with optimizations."""
    
    DEBUG = False
    
    # Production specific settings
    CAMERA_MOCK_MODE = False
    LOG_LEVEL = 'INFO'
    
    # Performance settings for production
    STREAM_QUALITY = 'high'
    DEFAULT_FPS = 30
    
    # Security settings - will be validated when app starts
    SECRET_KEY = os.getenv('SECRET_KEY', 'production-secret-key-change-me')


class TestingConfig(BaseConfig):
    """Testing configuration for unit tests."""
    
    TESTING = True
    DEBUG = True
    
    # Testing specific settings
    CAMERA_MOCK_MODE = True  # Always use mock data in tests
    LOG_LEVEL = 'ERROR'
    
    # Test database or storage settings
    WTF_CSRF_ENABLED = False


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> BaseConfig:
    """
    Get configuration class based on environment name.
    
    Args:
        config_name: Name of the configuration ('development', 'production', 'testing')
        
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config_map.get(config_name.lower(), DevelopmentConfig)
