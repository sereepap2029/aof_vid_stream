"""
AOF Video Stream - Views Package

This package contains view-related utilities and template helpers.
In Flask applications, views are primarily handled by templates,
but this module provides additional view logic and template filters.
"""

from flask import current_app
from typing import Any, Dict

def format_resolution(resolution: tuple) -> str:
    """
    Format resolution tuple as string.
    
    Args:
        resolution: Resolution as (width, height) tuple
        
    Returns:
        Formatted resolution string
    """
    if not resolution or len(resolution) != 2:
        return "Unknown"
    return f"{resolution[0]} x {resolution[1]}"


def format_fps(fps: int) -> str:
    """
    Format FPS value as string.
    
    Args:
        fps: Frames per second value
        
    Returns:
        Formatted FPS string
    """
    if fps is None:
        return "N/A"
    return f"{fps} FPS"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_duration(seconds: int) -> str:
    """
    Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"


def get_status_badge_class(status: str) -> str:
    """
    Get CSS class for status badge.
    
    Args:
        status: Status string
        
    Returns:
        CSS class name
    """
    status_lower = status.lower()
    
    if status_lower in ['active', 'online', 'connected', 'streaming']:
        return 'status-success'
    elif status_lower in ['starting', 'stopping', 'connecting']:
        return 'status-warning'
    elif status_lower in ['stopped', 'offline', 'disconnected', 'idle']:
        return 'status-secondary'
    elif status_lower in ['error', 'failed', 'unavailable']:
        return 'status-danger'
    else:
        return 'status-info'


def get_quality_settings(quality: str) -> Dict[str, Any]:
    """
    Get quality settings based on quality level.
    
    Args:
        quality: Quality level string
        
    Returns:
        Dictionary with quality settings
    """
    quality_map = {
        'low': {
            'resolution': (320, 240),
            'fps': 15,
            'compression': 60,
            'description': 'Low quality for slow connections'
        },
        'medium': {
            'resolution': (640, 480),
            'fps': 30,
            'compression': 75,
            'description': 'Balanced quality and performance'
        },
        'high': {
            'resolution': (1280, 720),
            'fps': 30,
            'compression': 85,
            'description': 'High quality for fast connections'
        },
        'ultra': {
            'resolution': (1920, 1080),
            'fps': 60,
            'compression': 95,
            'description': 'Ultra high quality'
        }
    }
    
    return quality_map.get(quality.lower(), quality_map['medium'])


def register_template_filters(app):
    """
    Register custom template filters with the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.template_filter('format_resolution')
    def template_format_resolution(resolution):
        return format_resolution(resolution)
    
    @app.template_filter('format_fps')
    def template_format_fps(fps):
        return format_fps(fps)
    
    @app.template_filter('format_file_size')
    def template_format_file_size(size_bytes):
        return format_file_size(size_bytes)
    
    @app.template_filter('format_duration')
    def template_format_duration(seconds):
        return format_duration(seconds)
    
    @app.template_filter('status_badge_class')
    def template_status_badge_class(status):
        return get_status_badge_class(status)


def register_template_globals(app):
    """
    Register global template variables and functions.
    
    Args:
        app: Flask application instance
    """
    
    @app.template_global()
    def get_app_config(key, default=None):
        """Get application configuration value in templates."""
        return current_app.config.get(key, default)
    
    @app.template_global()
    def get_quality_options():
        """Get available quality options for templates."""
        return [
            {'value': 'low', 'label': 'Low (320x240)', 'description': 'For slow connections'},
            {'value': 'medium', 'label': 'Medium (640x480)', 'description': 'Balanced performance'},
            {'value': 'high', 'label': 'High (1280x720)', 'description': 'High quality'},
            {'value': 'ultra', 'label': 'Ultra (1920x1080)', 'description': 'Maximum quality'}
        ]
    
    @app.template_global()
    def get_resolution_options():
        """Get available resolution options for templates."""
        return [
            {'value': '320x240', 'label': '320 x 240 (QVGA)'},
            {'value': '640x480', 'label': '640 x 480 (VGA)'},
            {'value': '800x600', 'label': '800 x 600 (SVGA)'},
            {'value': '1024x768', 'label': '1024 x 768 (XGA)'},
            {'value': '1280x720', 'label': '1280 x 720 (HD)'},
            {'value': '1920x1080', 'label': '1920 x 1080 (Full HD)'}
        ]
    
    @app.template_global()
    def get_fps_options():
        """Get available FPS options for templates."""
        return [
            {'value': 15, 'label': '15 FPS'},
            {'value': 24, 'label': '24 FPS'},
            {'value': 30, 'label': '30 FPS'},
            {'value': 60, 'label': '60 FPS'}
        ]
