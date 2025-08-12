"""
AOF Video Stream - Legacy API Controller (Compatibility Layer)

This module provides backward compatibility for existing API routes.
All functionality has been moved to modular API controllers:
- Cameras API: src/webapp/controllers/api/cameras_api.py
- Streams API: src/webapp/controllers/api/streams_api.py  
- System API: src/webapp/controllers/api/system_api.py

For new development, use the modular API endpoints directly.
"""

from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)

# Create blueprint for legacy API compatibility
api_bp = Blueprint('api_legacy', __name__)

@api_bp.route('/')
def api_info():
    """
    API documentation endpoint showing the new modular structure.
    
    Returns:
        JSON response with API information and migration guide
    """
    api_info = {
        'name': 'AOF Video Stream API',
        'version': '2.0.0',
        'description': 'Modular REST API for camera streaming and management',
        'migration_notice': 'API has been restructured into modular endpoints for better organization',
        'new_endpoints': {
            'cameras': {
                'base_url': '/api/cameras',
                'endpoints': {
                    'GET /api/cameras/': 'Get list of available cameras',
                    'POST /api/cameras/start': 'Start camera streaming',
                    'POST /api/cameras/stop': 'Stop camera streaming',
                    'GET /api/cameras/status': 'Get camera status',
                    'POST /api/cameras/settings': 'Update camera settings',
                    'GET /api/cameras/frame': 'Get latest frame as JPEG',
                    'GET /api/cameras/stream': 'Get video stream',
                    'POST /api/cameras/snapshot': 'Take snapshot'
                }
            },
            'streams': {
                'base_url': '/api/streams',
                'endpoints': {
                    'GET /api/streams/': 'Get streaming sessions',
                    'GET /api/streams/status': 'Get streaming status',
                    'GET /api/streams/<session_id>': 'Get specific session info',
                    'POST /api/streams/create': 'Create new streaming session',
                    'POST /api/streams/<session_id>/start': 'Start specific session',
                    'POST /api/streams/<session_id>/stop': 'Stop specific session',
                    'DELETE /api/streams/<session_id>/delete': 'Delete session',
                    'GET /api/streams/metrics': 'Get streaming metrics'
                }
            },
            'system': {
                'base_url': '/api/system',
                'endpoints': {
                    'GET /api/system/status': 'Get system status',
                    'GET /api/system/config': 'Get system configuration',
                    'GET /api/system/health': 'Get system health check',
                    'GET /api/system/info': 'Get system information',
                    'GET /api/system/logs': 'Get recent system logs',
                    'POST /api/system/restart': 'Restart system components'
                }
            }
        },
        'legacy_support': {
            'status': 'deprecated',
            'message': 'Legacy endpoints under /api/ will redirect to new modular structure',
            'recommendation': 'Update your client code to use the new modular endpoints'
        }
    }
    
    return jsonify(api_info)

# Error handlers for legacy API
@api_bp.errorhandler(400)
def api_bad_request(error):
    """Handle 400 Bad Request errors for legacy API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Bad request',
            'code': 'BAD_REQUEST',
            'note': 'Consider using the new modular API endpoints under /api/cameras/, /api/streams/, /api/system/'
        }
    }), 400


@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 Not Found errors for legacy API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Endpoint not found',
            'code': 'NOT_FOUND',
            'note': 'This endpoint may have moved to the new modular API structure. Check /api/ for documentation.'
        }
    }), 404


@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle 500 Internal Server errors for legacy API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }
    }), 500
