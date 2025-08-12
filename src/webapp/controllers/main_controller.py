"""
AOF Video Stream - Main Controller

This module handles the main web routes and page rendering.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from typing import Dict, Any
import logging

from ..models.camera_model import camera_model
from ..models.stream_model import stream_model

logger = logging.getLogger(__name__)

# Create blueprint for main routes
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Render the main homepage.
    
    Returns:
        Rendered index template
    """
    try:
        # Get camera devices for status display
        devices = camera_model.get_devices()
        camera_status = camera_model.get_status()
        stream_status = stream_model.get_stream_status()
        
        return render_template(
            'index.html',
            devices=devices,
            camera_status=camera_status,
            stream_status=stream_status
        )
        
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html', error=str(e))


@main_bp.route('/camera')
def camera():
    """
    Render the camera interface page.
    
    Returns:
        Rendered camera template
    """
    try:
        # Get camera devices and status
        devices = camera_model.get_devices(refresh=True)
        camera_status = camera_model.get_status()
        stream_status = stream_model.get_stream_status()
        
        # Get current settings
        active_session = stream_model.get_active_session()
        current_settings = None
        if active_session:
            current_settings = active_session.settings.to_dict()
        
        return render_template(
            'camera.html',
            devices=devices,
            camera_status=camera_status,
            stream_status=stream_status,
            current_settings=current_settings
        )
        
    except Exception as e:
        logger.error(f"Error rendering camera page: {e}")
        return render_template('camera.html', error=str(e))


@main_bp.route('/about')
def about():
    """
    Render the about page.
    
    Returns:
        Rendered about template
    """
    return render_template('about.html')


@main_bp.route('/help')
def help():
    """
    Render the help page.
    
    Returns:
        Rendered help template
    """
    return render_template('help.html')


@main_bp.route('/status')
def status():
    """
    Get system status information.
    
    Returns:
        JSON response with system status
    """
    try:
        camera_status = camera_model.get_status()
        stream_status = stream_model.get_stream_status()
        devices = camera_model.get_devices()
        
        system_status = {
            'timestamp': camera_status.get('last_frame_time'),
            'system': {
                'camera_system': 'online' if devices else 'offline',
                'available_devices': len(devices),
                'streaming_active': stream_status['is_streaming']
            },
            'camera': camera_status,
            'stream': stream_status,
            'devices': devices
        }
        
        return jsonify(system_status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'error': str(e),
            'system': {
                'camera_system': 'error',
                'available_devices': 0,
                'streaming_active': False
            }
        }), 500


@main_bp.route('/config')
def config():
    """
    Get current application configuration.
    
    Returns:
        JSON response with configuration information
    """
    try:
        config_info = {
            'debug_mode': current_app.config.get('DEBUG', False),
            'camera_settings': {
                'default_resolution': current_app.config.get('DEFAULT_RESOLUTION', (640, 480)),
                'default_fps': current_app.config.get('DEFAULT_FPS', 30),
                'max_cameras': current_app.config.get('MAX_CAMERAS', 10),
                'mock_mode': current_app.config.get('CAMERA_MOCK_MODE', False)
            },
            'stream_settings': {
                'quality': current_app.config.get('STREAM_QUALITY', 'medium'),
                'buffer_size': current_app.config.get('FRAME_BUFFER_SIZE', 10),
                'websocket_timeout': current_app.config.get('WEBSOCKET_TIMEOUT', 30)
            },
            'server_info': {
                'host': current_app.config.get('HOST', 'localhost'),
                'port': current_app.config.get('PORT', 5000)
            }
        }
        
        return jsonify(config_info)
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for main blueprint."""
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors for main blueprint."""
    return render_template('errors/500.html'), 500
