"""
AOF Video Stream - System API Controller

This module handles system-related REST API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
import logging

from ...models.camera_model import camera_model
from ...models.stream_model import stream_model

logger = logging.getLogger(__name__)

# Create blueprint for system API routes
system_bp = Blueprint('system_api', __name__)


@system_bp.route('/status')
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


@system_bp.route('/config')
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
            },
            'server_info': {
                'host': current_app.config.get('HOST', 'localhost'),
                'port': current_app.config.get('PORT', 5000),
                'environment': current_app.config.get('ENV', 'development')
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


@system_bp.route('/health')
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
        stream_status = stream_model.get_stream_status()
        
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
                'streaming_system': {
                    'status': 'pass',
                    'details': f"Streaming: {'active' if stream_status['is_streaming'] else 'idle'}"
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


@system_bp.route('/info')
def get_system_info():
    """
    Get general system information.
    
    Returns:
        JSON response with system information
    """
    try:
        import platform
        import sys
        
        system_info = {
            'application': {
                'name': 'AOF Video Stream',
                'version': '2.0.0',
                'phase': 'Phase 2 Complete',
                'api_version': '1.0.0'
            },
            'system': {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'python_version': sys.version.split()[0],
                'python_implementation': platform.python_implementation()
            },
            'capabilities': {
                'camera_detection': True,
                'video_capture': True,
                'web_interface': True,
                'rest_api': True,
                'streaming': False,  # Phase 3 feature
                'recording': False   # Phase 4 feature
            }
        }
        
        return jsonify({
            'success': True,
            'data': system_info,
            'meta': {
                'timestamp': camera_model.get_status().get('last_frame_time'),
                'api_version': '1.0.0'
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting system info: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'SYSTEM_INFO_ERROR'
            }
        }), 500


@system_bp.route('/logs')
def get_system_logs():
    """
    Get recent system logs.
    
    Returns:
        JSON response with recent log entries
    """
    try:
        # Get query parameters
        level = request.args.get('level', 'INFO')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 entries
        
        # This is a placeholder implementation
        # In a real system, you would read from actual log files
        logs = [
            {
                'timestamp': camera_model.get_status().get('last_frame_time'),
                'level': 'INFO',
                'module': 'system_api',
                'message': 'System logs endpoint accessed'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'total_entries': len(logs),
                'level_filter': level,
                'limit': limit
            },
            'meta': {
                'timestamp': camera_model.get_status().get('last_frame_time'),
                'api_version': '1.0.0'
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting system logs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'LOGS_ERROR'
            }
        }), 500


@system_bp.route('/restart', methods=['POST'])
def restart_system():
    """
    Restart system components.
    
    Returns:
        JSON response confirming restart
    """
    try:
        data = request.get_json() or {}
        component = data.get('component', 'all')
        
        success = False
        message = ''
        
        if component == 'camera' or component == 'all':
            # Restart camera system
            camera_model.stop_stream()
            # In a real implementation, you might reinitialize the camera system
            success = True
            message += 'Camera system restarted. '
        
        if component == 'stream' or component == 'all':
            # Restart streaming system
            stream_model.stop_all_sessions()
            success = True
            message += 'Streaming system restarted. '
        
        if not success:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Unknown component: {component}',
                    'code': 'UNKNOWN_COMPONENT'
                }
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'message': message.strip(),
                'component': component
            },
            'meta': {
                'action': 'system_restart',
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error restarting system: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'RESTART_ERROR'
            }
        }), 500


# Error handlers specific to system API
@system_bp.errorhandler(400)
def system_api_bad_request(error):
    """Handle 400 Bad Request errors for system API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Bad request for system operation',
            'code': 'SYSTEM_BAD_REQUEST'
        }
    }), 400


@system_bp.errorhandler(404)
def system_api_not_found(error):
    """Handle 404 Not Found errors for system API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'System endpoint not found',
            'code': 'SYSTEM_NOT_FOUND'
        }
    }), 404


@system_bp.errorhandler(500)
def system_api_internal_error(error):
    """Handle 500 Internal Server errors for system API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error in system operation',
            'code': 'SYSTEM_INTERNAL_ERROR'
        }
    }), 500
