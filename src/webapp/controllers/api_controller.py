"""
AOF Video Stream - API Controller

This module handles REST API endpoints for the application.
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List
import logging
import json

from ..models.camera_model import camera_model
from ..models.stream_model import stream_model

logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)


@api_bp.route('/')
def api_info():
    """
    Get API information and available endpoints.
    
    Returns:
        JSON response with API information
    """
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


# Camera API endpoints
@api_bp.route('/cameras')
def get_cameras():
    """
    Get list of available camera devices.
    
    Returns:
        JSON response with camera devices
    """
    try:
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        devices = camera_model.get_devices(refresh=refresh)
        
        return jsonify({
            'success': True,
            'data': {
                'cameras': devices,
                'count': len(devices)
            },
            'meta': {
                'refreshed': refresh,
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting cameras: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'CAMERA_LIST_ERROR'
            }
        }), 500


@api_bp.route('/cameras/start', methods=['POST'])
def start_camera_stream():
    """
    Start camera streaming via API.
    
    Returns:
        JSON response with stream information
    """
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if 'camera_index' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'camera_index is required',
                    'code': 'MISSING_PARAMETER'
                }
            }), 400
        
        camera_index = data['camera_index']
        resolution = data.get('resolution', [640, 480])
        fps = data.get('fps', 30)
        quality = data.get('quality', 'medium')
        
        # Convert resolution to tuple if needed
        if isinstance(resolution, list):
            resolution = tuple(resolution)
        
        # Start camera
        success = camera_model.start_stream(camera_index, resolution, fps)
        
        if success:
            # Get current status
            status = camera_model.get_status()
            
            return jsonify({
                'success': True,
                'data': {
                    'camera_index': camera_index,
                    'resolution': resolution,
                    'fps': fps,
                    'quality': quality,
                    'status': status
                },
                'meta': {
                    'action': 'camera_started',
                    'timestamp': status.get('last_frame_time')
                }
            })
        else:
            error_msg = camera_model.get_status().get('error_message', 'Unknown error')
            return jsonify({
                'success': False,
                'error': {
                    'message': error_msg,
                    'code': 'CAMERA_START_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error starting camera: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@api_bp.route('/cameras/stop', methods=['POST'])
def stop_camera_stream():
    """
    Stop camera streaming via API.
    
    Returns:
        JSON response confirming stop
    """
    try:
        success = camera_model.stop_stream()
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Camera stream stopped successfully'
                },
                'meta': {
                    'action': 'camera_stopped',
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Failed to stop camera stream',
                    'code': 'CAMERA_STOP_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error stopping camera: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@api_bp.route('/cameras/status')
def get_camera_status_api():
    """
    Get camera status via API.
    
    Returns:
        JSON response with camera status
    """
    try:
        status = camera_model.get_status()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status
            },
            'meta': {
                'timestamp': status.get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting camera status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'STATUS_ERROR'
            }
        }), 500


# Stream API endpoints
@api_bp.route('/streams')
def get_streams():
    """
    Get all streaming sessions.
    
    Returns:
        JSON response with streaming sessions
    """
    try:
        sessions = stream_model.get_all_sessions()
        stream_status = stream_model.get_stream_status()
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': [session.to_dict() for session in sessions],
                'active_session': stream_status.get('active_session'),
                'is_streaming': stream_status.get('is_streaming', False)
            },
            'meta': {
                'total_sessions': len(sessions),
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting streams: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'STREAM_LIST_ERROR'
            }
        }), 500


@api_bp.route('/streams/status')
def get_stream_status_api():
    """
    Get streaming status via API.
    
    Returns:
        JSON response with streaming status
    """
    try:
        status = stream_model.get_stream_status()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status
            },
            'meta': {
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting stream status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'STREAM_STATUS_ERROR'
            }
        }), 500


@api_bp.route('/streams/<session_id>')
def get_stream_session(session_id: str):
    """
    Get specific streaming session information.
    
    Args:
        session_id: ID of the streaming session
        
    Returns:
        JSON response with session information
    """
    try:
        session = stream_model.get_session(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Session {session_id} not found',
                    'code': 'SESSION_NOT_FOUND'
                }
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'session': session.to_dict()
            },
            'meta': {
                'session_id': session_id,
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting stream session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'SESSION_ERROR'
            }
        }), 500


# System API endpoints
@api_bp.route('/system/status')
def get_system_status():
    """
    Get system status via API.
    
    Returns:
        JSON response with system status
    """
    try:
        camera_status = camera_model.get_status()
        stream_status = stream_model.get_stream_status()
        devices = camera_model.get_devices()
        
        system_status = {
            'camera_system': 'online' if devices else 'offline',
            'streaming_system': 'active' if stream_status['is_streaming'] else 'idle',
            'available_devices': len(devices),
            'active_streams': 1 if stream_status['is_streaming'] else 0,
            'uptime': camera_status.get('last_frame_time'),
            'memory_usage': 'N/A',  # Could be implemented with psutil
            'cpu_usage': 'N/A'      # Could be implemented with psutil
        }
        
        return jsonify({
            'success': True,
            'data': {
                'system': system_status,
                'camera': camera_status,
                'stream': stream_status,
                'devices': devices
            },
            'meta': {
                'timestamp': camera_status.get('last_frame_time'),
                'api_version': '1.0.0'
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'SYSTEM_STATUS_ERROR'
            }
        }), 500


@api_bp.route('/system/config')
def get_system_config():
    """
    Get system configuration via API.
    
    Returns:
        JSON response with system configuration
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
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'config': config_info
            },
            'meta': {
                'timestamp': camera_model.get_status().get('last_frame_time'),
                'api_version': '1.0.0'
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting system config: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'CONFIG_ERROR'
            }
        }), 500


@api_bp.route('/system/health')
def health_check():
    """
    System health check endpoint.
    
    Returns:
        JSON response with health status
    """
    try:
        # Basic health checks
        devices = camera_model.get_devices()
        camera_status = camera_model.get_status()
        
        health_status = {
            'status': 'healthy',
            'checks': {
                'camera_detection': {
                    'status': 'pass' if devices else 'warn',
                    'details': f'{len(devices)} devices available'
                },
                'camera_system': {
                    'status': 'pass' if not camera_status.get('error_message') else 'fail',
                    'details': camera_status.get('error_message', 'OK')
                },
                'api_response': {
                    'status': 'pass',
                    'details': 'API responding normally'
                }
            }
        }
        
        # Determine overall health
        check_statuses = [check['status'] for check in health_status['checks'].values()]
        if 'fail' in check_statuses:
            health_status['status'] = 'unhealthy'
        elif 'warn' in check_statuses:
            health_status['status'] = 'degraded'
        
        return jsonify({
            'success': True,
            'data': health_status,
            'meta': {
                'timestamp': camera_status.get('last_frame_time'),
                'api_version': '1.0.0'
            }
        })
        
    except Exception as e:
        logger.error(f"API Error in health check: {e}")
        return jsonify({
            'success': False,
            'data': {
                'status': 'unhealthy',
                'checks': {
                    'api_response': {
                        'status': 'fail',
                        'details': str(e)
                    }
                }
            },
            'error': {
                'message': str(e),
                'code': 'HEALTH_CHECK_ERROR'
            }
        }), 500


# Error handlers for API blueprint
@api_bp.errorhandler(400)
def api_bad_request(error):
    """Handle 400 Bad Request errors for API."""
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
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }
    }), 500
