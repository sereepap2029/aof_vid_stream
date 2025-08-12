"""
AOF Video Stream - API Package

This package contains separate API controllers for different system components.
"""

from flask import Blueprint
from .cameras_api import cameras_bp
from .streams_api import streams_bp
from .system_api import system_bp

# Create main API blueprint
api_bp = Blueprint('api', __name__)

def register_api_blueprints(app):
    """
    Register all API blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register individual API blueprints
    app.register_blueprint(cameras_bp, url_prefix='/api/cameras')
    app.register_blueprint(streams_bp, url_prefix='/api/streams')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    
    # Register main API blueprint for documentation
    app.register_blueprint(api_bp, url_prefix='/api')

@api_bp.route('/')
def api_info():
    """
    Get API information and available endpoints.
    
    Returns:
        JSON response with API information
    """
    from flask import jsonify
    
    api_info = {
        'name': 'AOF Video Stream API',
        'version': '1.0.0',
        'description': 'REST API for camera streaming and management',
        'endpoints': {
            'cameras': {
                'GET /api/cameras': 'Get list of available cameras',
                'POST /api/cameras/start': 'Start camera streaming',
                'POST /api/cameras/stop': 'Stop camera streaming',
                'GET /api/cameras/status': 'Get camera status',
                'POST /api/cameras/settings': 'Update camera settings',
                'GET /api/cameras/frame': 'Get latest frame as JPEG',
                'GET /api/cameras/stream': 'Get video stream',
                'POST /api/cameras/snapshot': 'Take snapshot'
            },
            'streams': {
                'GET /api/streams': 'Get streaming sessions',
                'GET /api/streams/status': 'Get streaming status',
                'GET /api/streams/<session_id>': 'Get specific session info'
            },
            'system': {
                'GET /api/system/status': 'Get system status',
                'GET /api/system/config': 'Get system configuration',
                'GET /api/system/health': 'Get system health check'
            }
        }
    }
    
    return jsonify(api_info)

# Common error handlers for all API endpoints
@api_bp.errorhandler(400)
def api_bad_request(error):
    """Handle 400 Bad Request errors for API."""
    from flask import jsonify
    return jsonify({
        'success': False,
        'error': {
            'message': 'Bad request',
            'code': 'BAD_REQUEST'
        }
    }), 400


@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 Not Found errors for API."""
    from flask import jsonify
    return jsonify({
        'success': False,
        'error': {
            'message': 'Endpoint not found',
            'code': 'NOT_FOUND'
        }
    }), 404


@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle 500 Internal Server errors for API."""
    from flask import jsonify
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }
    }), 500
