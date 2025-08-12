"""
AOF Video Stream - Streams API Controller

This module handles streaming-related REST API endpoints.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from ...models.stream_model import stream_model
from ...models.camera_model import camera_model

logger = logging.getLogger(__name__)

# Create blueprint for streams API routes
streams_bp = Blueprint('streams_api', __name__)


@streams_bp.route('/')
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


@streams_bp.route('/status')
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


@streams_bp.route('/<session_id>')
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


@streams_bp.route('/create', methods=['POST'])
def create_stream_session():
    """
    Create a new streaming session.
    
    Returns:
        JSON response with new session information
    """
    try:
        data = request.get_json() or {}
        
        # Extract session configuration
        session_config = {
            'quality': data.get('quality', 'medium'),
            'resolution': data.get('resolution', [640, 480]),
            'fps': data.get('fps', 30),
            'duration': data.get('duration'),  # Optional duration limit
            'description': data.get('description', 'API Created Session')
        }
        
        # Create session using stream model
        session = stream_model.create_session(**session_config)
        
        if session:
            return jsonify({
                'success': True,
                'data': {
                    'session': session.to_dict(),
                    'message': 'Stream session created successfully'
                },
                'meta': {
                    'action': 'session_created',
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': 'Failed to create stream session',
                    'code': 'SESSION_CREATE_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error creating stream session: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@streams_bp.route('/<session_id>/start', methods=['POST'])
def start_stream_session(session_id: str):
    """
    Start a specific streaming session.
    
    Args:
        session_id: ID of the streaming session
        
    Returns:
        JSON response confirming session start
    """
    try:
        success = stream_model.start_session(session_id)
        
        if success:
            session = stream_model.get_session(session_id)
            return jsonify({
                'success': True,
                'data': {
                    'session': session.to_dict() if session else None,
                    'message': f'Stream session {session_id} started successfully'
                },
                'meta': {
                    'action': 'session_started',
                    'session_id': session_id,
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Failed to start stream session {session_id}',
                    'code': 'SESSION_START_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error starting stream session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@streams_bp.route('/<session_id>/stop', methods=['POST'])
def stop_stream_session(session_id: str):
    """
    Stop a specific streaming session.
    
    Args:
        session_id: ID of the streaming session
        
    Returns:
        JSON response confirming session stop
    """
    try:
        success = stream_model.stop_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Stream session {session_id} stopped successfully'
                },
                'meta': {
                    'action': 'session_stopped',
                    'session_id': session_id,
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Failed to stop stream session {session_id}',
                    'code': 'SESSION_STOP_FAILED'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"API Error stopping stream session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@streams_bp.route('/<session_id>/delete', methods=['DELETE'])
def delete_stream_session(session_id: str):
    """
    Delete a specific streaming session.
    
    Args:
        session_id: ID of the streaming session
        
    Returns:
        JSON response confirming session deletion
    """
    try:
        success = stream_model.delete_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Stream session {session_id} deleted successfully'
                },
                'meta': {
                    'action': 'session_deleted',
                    'session_id': session_id,
                    'timestamp': camera_model.get_status().get('last_frame_time')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'message': f'Failed to delete stream session {session_id}',
                    'code': 'SESSION_DELETE_FAILED'
                }
            }), 404
        
    except Exception as e:
        logger.error(f"API Error deleting stream session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'INTERNAL_ERROR'
            }
        }), 500


@streams_bp.route('/metrics')
def get_stream_metrics():
    """
    Get streaming performance metrics.
    
    Returns:
        JSON response with streaming metrics
    """
    try:
        # Get metrics from stream model
        metrics = stream_model.get_metrics()
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': metrics
            },
            'meta': {
                'timestamp': camera_model.get_status().get('last_frame_time')
            }
        })
        
    except Exception as e:
        logger.error(f"API Error getting stream metrics: {e}")
        return jsonify({
            'success': False,
            'error': {
                'message': str(e),
                'code': 'METRICS_ERROR'
            }
        }), 500


# Error handlers specific to streams API
@streams_bp.errorhandler(400)
def streams_api_bad_request(error):
    """Handle 400 Bad Request errors for streams API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Bad request for stream operation',
            'code': 'STREAM_BAD_REQUEST'
        }
    }), 400


@streams_bp.errorhandler(404)
def streams_api_not_found(error):
    """Handle 404 Not Found errors for streams API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Stream endpoint not found',
            'code': 'STREAM_NOT_FOUND'
        }
    }), 404


@streams_bp.errorhandler(500)
def streams_api_internal_error(error):
    """Handle 500 Internal Server errors for streams API."""
    return jsonify({
        'success': False,
        'error': {
            'message': 'Internal server error in stream operation',
            'code': 'STREAM_INTERNAL_ERROR'
        }
    }), 500
