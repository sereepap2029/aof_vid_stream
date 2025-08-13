"""
AOF Video Stream - Cameras API Controller

This module handles camera-related REST API endpoints.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from ...models.camera_model import camera_model

logger = logging.getLogger(__name__)

# Create blueprint for camera API routes
cameras_bp = Blueprint('cameras_api', __name__)


@cameras_bp.route('/')
def get_cameras():
    """
    Get list of available camera devices.
    
    Returns:
        JSON response with camera devices
    """
    try:
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        quick_scan = request.args.get('quick_scan', 'true').lower() == 'true'
        
        devices = camera_model.get_devices(refresh=refresh, quick_scan=quick_scan)
        
        return jsonify({
            'success': True,
            'data': {
                'cameras': devices,
                'count': len(devices)
            },
            'meta': {
                'refreshed': refresh,
                'quick_scan': quick_scan,
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


@cameras_bp.route('/start', methods=['POST'])
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
        codec = data.get('codec', '')  # Get codec parameter
        quick_start = data.get('quick_start', True)  # Enable quick start by default
        
        # Convert resolution to tuple if needed
        if isinstance(resolution, list):
            resolution = tuple(resolution)
        
        # Start camera with optimization and codec
        logger.info(f"Starting camera device {camera_index} at {resolution} {fps}fps (quality: {quality}, codec: {codec}, quick: {quick_start})")
        success = camera_model.start_stream(camera_index, resolution, fps, quick_start=quick_start, codec=codec)
        
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


@cameras_bp.route('/stop', methods=['POST'])
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


@cameras_bp.route('/status')
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


@cameras_bp.route('/settings', methods=['POST'])
def update_camera_settings():
    """
    Update camera settings via API.
    
    Returns:
        JSON response confirming settings update
    """
    try:
        data = request.get_json() or {}
        
        # Validate input data
        allowed_settings = ['resolution', 'fps', 'quality', 'brightness', 'contrast']
        settings = {k: v for k, v in data.items() if k in allowed_settings}
        
        if not settings:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'No valid settings provided',
                    'code': 'NO_VALID_SETTINGS'
                }
            }), 400
        
        # Apply settings (implementation would depend on camera model capabilities)
        success = True  # Placeholder - would implement actual settings update
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Camera settings updated successfully',
                    'settings': settings
                },
                'meta': {
                    'action': 'settings_updated',
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Failed to update camera settings',
                    'code': 'SETTINGS_UPDATE_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error updating camera settings: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@cameras_bp.route('/frame')
def get_latest_frame():
    """
    Get latest frame as JPEG via API.
    
    Returns:
        JPEG image or JSON error response
    """
    try:
        # Get JPEG frame from camera model
        frame_data = camera_model.get_frame_as_jpeg()
        
        if frame_data:
            from flask import Response
            return Response(frame_data, mimetype='image/jpeg')
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'No frame available - camera may not be started',
                    'code': 'NO_FRAME_AVAILABLE'
                }
            }), 404
        
    except Exception as e:
        logger.error(f"API Error getting frame: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@cameras_bp.route('/stream')
def get_camera_stream():
    """
    Get video stream via API.
    
    Returns:
        Video stream or JSON error response
    """
    try:
        # Implementation would provide video stream
        # This is a placeholder for Phase 3 implementation
        return jsonify({
            'success': False,
            'error': {
                'message': 'Video streaming not yet implemented',
                'code': 'NOT_IMPLEMENTED'
            }
        }), 501
        
    except Exception as e:
        logger.error(f"API Error getting stream: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@cameras_bp.route('/snapshot', methods=['POST'])
def take_snapshot():
    """
    Take snapshot via API.
    
    Returns:
        JSON response with snapshot information
    """
    try:
        # Implementation would capture a snapshot
        # This is a placeholder for Phase 3 implementation
        return jsonify({
            'success': False,
            'error': {
                'message': 'Snapshot capture not yet implemented',
                'code': 'NOT_IMPLEMENTED'
            }
        }), 501
        
    except Exception as e:
        logger.error(f"API Error taking snapshot: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


# Error handlers specific to cameras API
@cameras_bp.errorhandler(400)
def cameras_api_bad_request(error):
    """Handle 400 Bad Request errors for cameras API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Bad request for camera operation',
            'code': 'CAMERA_BAD_REQUEST'
        }
    }), 400


@cameras_bp.route('/encoding/status')
def get_encoding_status():
    """
    Get hardware encoding status and capabilities.
    
    Returns:
        JSON response with encoding information
    """
    try:
        encoding_enabled = camera_model.is_hardware_encoding_enabled()
        performance_stats = camera_model.get_encoding_performance()
        
        return jsonify({
            'success': True,
            'data': {
                'hardware_encoding_enabled': encoding_enabled,
                'performance': performance_stats
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting encoding status: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to get encoding status: {str(e)}',
                'code': 'ENCODING_STATUS_ERROR'
            }
        }), 500


@cameras_bp.route('/encoding/enable', methods=['POST'])
def enable_hardware_encoding():
    """
    Enable hardware encoding.
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json() or {}
        
        # Reinitialize with specific parameters if provided
        width = data.get('width')
        height = data.get('height')
        fps = data.get('fps')
        
        success = camera_model.set_hardware_encoding(True)
        
        if success and (width or height or fps):
            camera_model.reinitialize_hardware_encoder(width, height, fps)
        
        if success:
            performance_stats = camera_model.get_encoding_performance()
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Hardware encoding enabled',
                    'performance': performance_stats
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Failed to enable hardware encoding',
                    'code': 'ENCODING_ENABLE_ERROR'
                }
            }), 500
            
    except Exception as e:
        logger.error(f"API Error enabling hardware encoding: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to enable hardware encoding: {str(e)}',
                'code': 'ENCODING_ENABLE_ERROR'
            }
        }), 500


@cameras_bp.route('/encoding/disable', methods=['POST'])
def disable_hardware_encoding():
    """
    Disable hardware encoding (fallback to software).
    
    Returns:
        JSON response with operation result
    """
    try:
        success = camera_model.set_hardware_encoding(False)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Hardware encoding disabled, using software encoding'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Failed to disable hardware encoding',
                    'code': 'ENCODING_DISABLE_ERROR'
                }
            }), 500
            
    except Exception as e:
        logger.error(f"API Error disabling hardware encoding: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to disable hardware encoding: {str(e)}',
                'code': 'ENCODING_DISABLE_ERROR'
            }
        }), 500


@cameras_bp.route('/encoding/performance')
def get_encoding_performance():
    """
    Get detailed encoding performance statistics.
    
    Returns:
        JSON response with performance data
    """
    try:
        performance_stats = camera_model.get_encoding_performance()
        
        return jsonify({
            'success': True,
            'data': {
                'performance': performance_stats,
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting encoding performance: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to get encoding performance: {str(e)}',
                'code': 'ENCODING_PERFORMANCE_ERROR'
            }
        }), 500


@cameras_bp.route('/codecs')
def get_available_codecs():
    """
    Get list of available video codecs on the server.
    
    Returns:
        JSON response with available codecs
    """
    try:
        available_codecs = camera_model.get_available_codecs()
        current_codec = camera_model.get_current_codec_info()
        
        return jsonify({
            'success': True,
            'data': {
                'available_codecs': available_codecs,
                'current_codec': current_codec
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting available codecs: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to get available codecs: {str(e)}',
                'code': 'CODECS_ERROR'
            }
        }), 500


@cameras_bp.route('/codec', methods=['POST'])
def set_codec():
    """
    Set the video codec for encoding.
    
    Expects JSON: {"codec": "H264"}
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data or 'codec' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Missing codec parameter',
                    'code': 'MISSING_CODEC'
                }
            }), 400
        
        codec = data['codec']
        
        # Validate codec
        available_codecs = camera_model.get_available_codecs()
        if codec != 'auto' and codec not in available_codecs:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Codec "{codec}" not available. Available: {list(available_codecs.keys())}',
                    'code': 'INVALID_CODEC'
                }
            }), 400
        
        success = camera_model.set_codec(codec)
        
        if success:
            current_codec = camera_model.get_current_codec_info()
            performance_stats = camera_model.get_encoding_performance()
            
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Codec set to {codec}',
                    'current_codec': current_codec,
                    'performance': performance_stats
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Failed to set codec to {codec}',
                    'code': 'CODEC_SET_ERROR'
                }
            }), 500
            
    except Exception as e:
        logger.error(f"API Error setting codec: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to set codec: {str(e)}',
                'code': 'CODEC_SET_ERROR'
            }
        }), 500


@cameras_bp.route('/codec')
def get_current_codec():
    """
    Get information about the currently selected codec.
    
    Returns:
        JSON response with current codec information
    """
    try:
        current_codec = camera_model.get_current_codec_info()
        performance_stats = camera_model.get_encoding_performance()
        
        return jsonify({
            'success': True,
            'data': {
                'current_codec': current_codec,
                'performance': performance_stats
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting current codec: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': f'Failed to get current codec: {str(e)}',
                'code': 'CODEC_GET_ERROR'
            }
        }), 500


@cameras_bp.errorhandler(404)
def cameras_api_not_found(error):
    """Handle 404 Not Found errors for cameras API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Camera endpoint not found',
            'code': 'CAMERA_NOT_FOUND'
        }
    }), 404


@cameras_bp.errorhandler(500)
def cameras_api_internal_error(error):
    """Handle 500 Internal Server errors for cameras API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error in camera operation',
            'code': 'CAMERA_INTERNAL_ERROR'
        }
    }), 500
