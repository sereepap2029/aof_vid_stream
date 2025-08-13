"""
AOF Video Stream - Camera Controller

This module handles camera-specific web routes and operations.
"""

from flask import Blueprint, request, jsonify, Response, render_template
from typing import Dict, Any, Optional, Tuple
import logging
import uuid
import json

from ..models.camera_model import camera_model
from ..models.stream_model import stream_model, StreamSettings, StreamQuality

logger = logging.getLogger(__name__)

# Create blueprint for camera routes
camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/devices')
def get_devices():
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
            'devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error getting camera devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'devices': [],
            'count': 0
        }), 500


@camera_bp.route('/status')
def get_camera_status():
    """
    Get current camera status.
    
    Returns:
        JSON response with camera status
    """
    try:
        status = camera_model.get_status()
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/start', methods=['POST'])
def start_camera():
    """
    Start camera streaming.
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        data = request.get_json() or {}
        
        # Extract parameters
        camera_index = data.get('camera_index')
        resolution = data.get('resolution', (640, 480))
        fps = data.get('fps', 30)
        quality = data.get('quality', 'medium')
        
        # Validate camera index
        if camera_index is None:
            return jsonify({
                'success': False,
                'error': 'Camera index is required'
            }), 400
        
        # Parse resolution if it's a string
        if isinstance(resolution, str):
            try:
                width, height = map(int, resolution.split('x'))
                resolution = (width, height)
            except ValueError:
                resolution = (640, 480)
        
        # Create stream settings
        stream_settings = StreamSettings(
            quality=StreamQuality(quality),
            fps=fps,
            resolution=resolution
        )
        
        # Create session
        session_id = str(uuid.uuid4())
        session = stream_model.create_session(session_id, camera_index, stream_settings)
        
        # Start camera
        success = camera_model.start_stream(camera_index, resolution, fps)
        if not success:
            camera_status = camera_model.get_status()
            error_msg = camera_status.get('error_message', 'Failed to start camera')
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Start stream session
        stream_success = stream_model.start_session(session_id)
        if not stream_success:
            camera_model.stop_stream()
            return jsonify({
                'success': False,
                'error': 'Failed to start stream session'
            }), 500
        
        # Mark session as active
        session.activate()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'camera_index': camera_index,
            'resolution': resolution,
            'fps': fps,
            'quality': quality
        })
        
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/stop', methods=['POST'])
def stop_camera():
    """
    Stop camera streaming.
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        # Get active session
        active_session = stream_model.get_active_session()
        if not active_session:
            return jsonify({
                'success': False,
                'error': 'No active streaming session'
            }), 400
        
        # Stop stream session
        stream_model.stop_session(active_session.session_id)
        
        # Stop camera
        camera_model.stop_stream()
        
        return jsonify({
            'success': True,
            'message': 'Camera stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/settings', methods=['POST'])
def update_settings():
    """
    Update camera settings.
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        data = request.get_json() or {}
        
        resolution = data.get('resolution')
        fps = data.get('fps')
        
        # Parse resolution if it's a string
        if isinstance(resolution, str):
            try:
                width, height = map(int, resolution.split('x'))
                resolution = (width, height)
            except ValueError:
                resolution = None
        
        # Update camera settings
        success = camera_model.update_settings(resolution=resolution, fps=fps)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update settings'
            }), 500
        
    except Exception as e:
        logger.error(f"Error updating camera settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/snapshot', methods=['POST'])
def take_snapshot():
    """
    Take a snapshot from the current camera stream.
    
    Returns:
        JSON response with snapshot information
    """
    try:
        # Take snapshot
        frame = camera_model.take_snapshot()
        
        if frame is None:
            return jsonify({
                'success': False,
                'error': 'No frame available for snapshot'
            }), 400
        
        # Get JPEG encoded frame
        jpeg_data = camera_model.get_frame_as_jpeg(quality=95)
        
        if jpeg_data is None:
            return jsonify({
                'success': False,
                'error': 'Failed to encode snapshot'
            }), 500
        
        # Return snapshot info (in a real implementation, you might save the image)
        return jsonify({
            'success': True,
            'message': 'Snapshot taken successfully',
            'size_bytes': len(jpeg_data),
            'timestamp': camera_model.get_status().get('last_frame_time')
        })
        
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/frame')
def get_frame():
    """
    Get the latest frame from the camera as JPEG.
    
    Returns:
        JPEG image response or error
    """
    try:
        # Get JPEG frame
        jpeg_data = camera_model.get_frame_as_jpeg()
        
        if jpeg_data is None:
            return jsonify({
                'error': 'No frame available'
            }), 404
        
        # Update stream metrics if active session exists
        active_session = stream_model.get_active_session()
        if active_session:
            stream_model.update_frame_metrics(active_session.session_id, len(jpeg_data))
        
        return Response(
            jpeg_data,
            mimetype='image/jpeg',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting frame: {e}")
        return jsonify({'error': str(e)}), 500


@camera_bp.route('/stream')
def stream_video():
    """
    Stream video frames as multipart response.
    
    Returns:
        Multipart response with JPEG frames
    """
    def generate_frames():
        """Generator function for streaming frames."""
        try:
            while True:
                # Get JPEG frame
                jpeg_data = camera_model.get_frame_as_jpeg()
                
                if jpeg_data is None:
                    break
                
                # Update stream metrics
                active_session = stream_model.get_active_session()
                if active_session:
                    stream_model.update_frame_metrics(active_session.session_id, len(jpeg_data))
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
                
        except Exception as e:
            logger.error(f"Error in frame generator: {e}")
    
    try:
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting video stream: {e}")
        return jsonify({'error': str(e)}), 500


@camera_bp.route('/stream/stats')
def get_stream_stats():
    """
    Get current streaming statistics including bitrate.
    
    Returns:
        JSON response with streaming statistics
    """
    try:
        import time
        
        # Get WebSocket streaming stats
        from .websocket_controller import get_websocket_streamer
        ws_streamer = get_websocket_streamer()
        
        stats = {
            'camera_status': camera_model.get_status(),
            'websocket_stats': None,
            'timestamp': time.time()
        }
        
        if ws_streamer:
            ws_stats = ws_streamer.get_connection_stats()
            stats['websocket_stats'] = ws_stats
            
            # Calculate aggregate statistics
            if ws_stats['connections']:
                total_bitrate = sum(conn.get('current_bitrate_mbps', 0) 
                                  for conn in ws_stats['connections'].values())
                total_bytes = sum(conn.get('total_bytes_sent', 0) 
                                for conn in ws_stats['connections'].values())
                avg_frame_size = sum(conn.get('avg_frame_size', 0) 
                                   for conn in ws_stats['connections'].values())
                if ws_stats['active_streams'] > 0:
                    avg_frame_size /= ws_stats['active_streams']
                
                stats['aggregate_stats'] = {
                    'total_bitrate_mbps': total_bitrate,
                    'total_bytes_sent': total_bytes,
                    'average_frame_size_kb': avg_frame_size / 1024 if avg_frame_size > 0 else 0,
                    'active_streams': ws_stats['active_streams']
                }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stream stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/test')
def test_camera():
    """
    Test camera functionality.
    
    Returns:
        JSON response with test results
    """
    try:
        # Test camera detection
        devices = camera_model.get_devices(refresh=True)
        
        test_results = {
            'camera_detection': {
                'success': len(devices) > 0,
                'device_count': len(devices),
                'devices': devices
            }
        }
        
        # Test camera initialization if devices found
        if devices:
            camera_index = devices[0]['index']
            test_results['camera_initialization'] = {
                'camera_index': camera_index,
                'success': False,
                'error': None
            }
            
            try:
                success = camera_model.start_stream(camera_index)
                test_results['camera_initialization']['success'] = success
                
                if success:
                    # Test frame capture
                    frame = camera_model.get_frame()
                    test_results['frame_capture'] = {
                        'success': frame is not None,
                        'frame_shape': frame.shape if frame is not None else None
                    }
                    
                    # Stop the test stream
                    camera_model.stop_stream()
                
            except Exception as e:
                test_results['camera_initialization']['error'] = str(e)
        
        return jsonify(test_results)
        
    except Exception as e:
        logger.error(f"Error testing camera: {e}")
        return jsonify({
            'error': str(e),
            'camera_detection': {
                'success': False,
                'device_count': 0,
                'devices': []
            }
        }), 500
