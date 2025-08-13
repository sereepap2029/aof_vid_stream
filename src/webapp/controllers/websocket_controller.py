"""
AOF Video Stream - WebSocket Controller

This module handles WebSocket-based real-time video streaming.
Provides low-latency, high-performance video transmission.
"""

import base64
import time
import threading
from typing import Optional, Dict, Any
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
import zlib
from datetime import datetime

from flask import request
from flask_socketio import SocketIO, emit, disconnect
from ..models.camera_model import camera_model

logger = logging.getLogger(__name__)

def serialize_for_json(obj):
    """Convert datetime and other non-serializable objects to JSON-compatible format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

class WebSocketVideoStreamer:
    """
    WebSocket-based video streaming controller.
    Handles real-time video transmission with configurable quality and framerate.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.streaming_threads: Dict[str, threading.Thread] = {}
        # Thread pool for encoding operations to avoid blocking
        self.encoder_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="FrameEncoder")
        # Frame queues for async processing
        self.frame_queues: Dict[str, queue.Queue] = {}
        self.setup_handlers()
    
    def safe_emit(self, event, data, **kwargs):
        """Safely emit data with error handling for disconnected clients."""
        try:
            emit(event, data, **kwargs)
            return True
        except Exception as e:
            # Log the error but don't raise it - client might have disconnected
            logger.warning(f"Failed to emit {event}: {e}")
            return False
    
    def setup_handlers(self):
        """Setup WebSocket event handlers."""
        
        @self.socketio.on('connect', namespace='/video')
        def handle_connect():
            """Handle client connection."""
            client_id = request.sid
            logger.info(f"Video client connected: {client_id}")
            
            # Initialize client connection data
            self.active_connections[client_id] = {
                'connected': True,
                'streaming': False,
                'camera_index': None,
                'quality': 85,
                'target_fps': 30,
                'last_frame_time': 0,
                'frame_count': 0,
                'connection_time': time.time(),
                'performance_stats': {
                    'avg_encode_time': 0,
                    'avg_frame_size': 0,
                    'frames_skipped': 0,
                    'total_bytes_sent': 0,
                    'bitrate_window_start': time.time(),
                    'bitrate_window_bytes': 0,
                    'current_bitrate_mbps': 0
                },
                'encoding_method': 'binary',  # binary, base64, compressed
                'max_bitrate_kbps': 0,  # 0 = unlimited, otherwise limit in kbps
                'bitrate_control': {
                    'enabled': False,
                    'target_kbps': 0,
                    'quality_adjustment': 0,  # -50 to +50 quality adjustment
                    'last_adjustment_time': 0
                }
            }
            
            emit('connection_status', {
                'status': 'connected',
                'client_id': client_id,
                'server_time': time.time()
            })
        
        @self.socketio.on('disconnect', namespace='/video')
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid
            logger.info(f"Video client disconnected: {client_id}")
            
            # Stop streaming for this client and clean up completely
            self.stop_stream_for_client(client_id, disconnect_client=True)
        
        @self.socketio.on('start_stream', namespace='/video')
        def handle_start_stream(data):
            """Handle stream start request."""
            client_id = request.sid
            
            try:
                camera_index = data.get('camera_index', 1)
                resolution = data.get('resolution', [640, 480])
                fps = data.get('fps', 30)
                quality = data.get('quality', 85)
                
                logger.info(f"Starting WebSocket stream for client {client_id}: "
                           f"camera={camera_index}, resolution={resolution}, fps={fps}, quality={quality}")
                
                # Start camera if not already active
                camera_status = camera_model.get_status()
                if not camera_status['is_active']:
                    success = camera_model.start_stream(camera_index, tuple(resolution), fps)
                    if not success:
                        emit('stream_error', {
                            'error': 'Failed to start camera',
                            'code': 'CAMERA_START_FAILED'
                        })
                        return
                
                # Update connection data
                if client_id in self.active_connections:
                    self.active_connections[client_id].update({
                        'streaming': True,
                        'camera_index': camera_index,
                        'quality': quality,
                        'target_fps': fps,
                        'resolution': resolution
                    })
                
                # Start streaming thread for this client
                self.start_stream_for_client(client_id)
                
                emit('stream_started', {
                    'camera_index': camera_index,
                    'resolution': resolution,
                    'fps': fps,
                    'quality': quality,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                logger.error(f"Error starting WebSocket stream: {e}")
                emit('stream_error', {
                    'error': str(e),
                    'code': 'STREAM_START_ERROR'
                })
        
        @self.socketio.on('stop_stream', namespace='/video')
        def handle_stop_stream():
            """Handle stream stop request."""
            client_id = request.sid
            logger.info(f"Stopping WebSocket stream for client {client_id}")
            
            # Stop streaming but keep client connected for potential restart
            self.stop_stream_for_client(client_id, disconnect_client=False)
            
            # Send stopped confirmation
            try:
                emit('stream_stopped', {
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.warning(f"Error emitting stream_stopped to client {client_id}: {e}")

        @self.socketio.on('update_resolution', namespace='/video')
        def handle_update_resolution(data):
            """Handle resolution update request."""
            client_id = request.sid
            resolution = data.get('resolution', [640, 480])
            
            if client_id in self.active_connections:
                self.active_connections[client_id]['resolution'] = resolution
                logger.info(f"Updated resolution for client {client_id}: {resolution}")
                
                # Update camera settings in real-time
                try:
                    camera_status = camera_model.get_status()
                    if camera_status['is_active']:
                        success = camera_model.update_settings(resolution=tuple(resolution))
                        if success:
                            logger.info(f"Camera resolution updated to {resolution}")
                        else:
                            logger.warning(f"Failed to update camera resolution to {resolution}")
                except Exception as e:
                    logger.error(f"Error updating camera resolution: {e}")
                
                emit('resolution_updated', {
                    'resolution': resolution,
                    'timestamp': time.time()
                })

        @self.socketio.on('update_quality', namespace='/video')
        def handle_update_quality(data):
            """Handle quality update request."""
            client_id = request.sid
            quality = data.get('quality', 85)
            
            if client_id in self.active_connections:
                self.active_connections[client_id]['quality'] = quality
                logger.info(f"Updated quality for client {client_id}: {quality}")
                
                emit('quality_updated', {
                    'quality': quality,
                    'timestamp': time.time()
                })
        
        @self.socketio.on('update_fps', namespace='/video')
        def handle_update_fps(data):
            """Handle FPS update request."""
            client_id = request.sid
            fps = data.get('fps', 30)
            
            if client_id in self.active_connections:
                self.active_connections[client_id]['target_fps'] = fps
                logger.info(f"Updated FPS for client {client_id}: {fps}")
                
                # Update camera settings in real-time
                try:
                    camera_status = camera_model.get_status()
                    if camera_status['is_active']:
                        success = camera_model.update_settings(fps=fps)
                        if success:
                            logger.info(f"Camera FPS updated to {fps}")
                        else:
                            logger.warning(f"Failed to update camera FPS to {fps}")
                except Exception as e:
                    logger.error(f"Error updating camera FPS: {e}")
                
                emit('fps_updated', {
                    'fps': fps,
                    'timestamp': time.time()
                })
        
        @self.socketio.on('set_encoding_method', namespace='/video')
        def handle_set_encoding_method(data):
            """Handle encoding method change request."""
            client_id = request.sid
            method = data.get('method', 'binary')  # binary, base64, compressed
            
            if client_id in self.active_connections:
                self.active_connections[client_id]['encoding_method'] = method
                logger.info(f"Updated encoding method for client {client_id}: {method}")
                
                emit('encoding_method_updated', {
                    'method': method,
                    'timestamp': time.time()
                })
        
        @self.socketio.on('set_max_bitrate', namespace='/video')
        def handle_set_max_bitrate(data):
            """Handle maximum bitrate setting."""
            client_id = request.sid
            max_bitrate_kbps = data.get('max_bitrate_kbps', 0)  # 0 = unlimited
            
            if client_id in self.active_connections:
                conn_data = self.active_connections[client_id]
                conn_data['max_bitrate_kbps'] = max_bitrate_kbps
                
                # Configure bitrate control
                if max_bitrate_kbps > 0:
                    conn_data['bitrate_control']['enabled'] = True
                    conn_data['bitrate_control']['target_kbps'] = max_bitrate_kbps
                    conn_data['bitrate_control']['quality_adjustment'] = 0
                    conn_data['bitrate_control']['last_adjustment_time'] = time.time()
                else:
                    conn_data['bitrate_control']['enabled'] = False
                    conn_data['bitrate_control']['quality_adjustment'] = 0
                
                logger.info(f"Updated max bitrate for client {client_id}: {max_bitrate_kbps} kbps")
                
                emit('max_bitrate_updated', {
                    'max_bitrate_kbps': max_bitrate_kbps,
                    'enabled': conn_data['bitrate_control']['enabled'],
                    'timestamp': time.time()
                })
        
        @self.socketio.on('get_stats', namespace='/video')
        def handle_get_stats():
            """Handle statistics request."""
            client_id = request.sid
            
            # Check if client is still connected and has active connection data
            if client_id not in self.active_connections:
                logger.warning(f"Stats requested for disconnected client: {client_id}")
                return
                
            try:
                conn_data = self.active_connections[client_id]
                camera_status = camera_model.get_status()
                
                stats = {
                    'client_id': client_id,
                    'streaming': conn_data['streaming'],
                    'frame_count': conn_data['frame_count'],
                    'connection_time': time.time() - conn_data['connection_time'],
                    'camera_status': serialize_for_json(camera_status),
                    'performance_stats': conn_data.get('performance_stats', {}),
                    'timestamp': time.time()
                }
                
                emit('stream_stats', stats)
            except Exception as e:
                logger.error(f"Error handling stats request for client {client_id}: {e}")
                # Clean up potentially corrupted connection data
                if client_id in self.active_connections:
                    del self.active_connections[client_id]
        
        @self.socketio.on('get_performance_stats', namespace='/video')
        def handle_get_performance_stats():
            """Handle performance statistics request."""
            client_id = request.sid
            
            # Check if client is still connected and has active connection data
            if client_id not in self.active_connections:
                logger.warning(f"Performance stats requested for disconnected client: {client_id}")
                return
                
            try:
                conn_data = self.active_connections[client_id]
                perf_stats = conn_data.get('performance_stats', {})
                
                emit('performance_stats', {
                    'client_id': client_id,
                    'avg_encode_time': perf_stats.get('avg_encode_time', 0),
                    'avg_frame_size': perf_stats.get('avg_frame_size', 0),
                    'frames_skipped': perf_stats.get('frames_skipped', 0),
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error handling performance stats request for client {client_id}: {e}")
                # Clean up potentially corrupted connection data
                if client_id in self.active_connections:
                    del self.active_connections[client_id]
    
    def start_stream_for_client(self, client_id: str):
        """Start streaming thread for a specific client."""
        if client_id in self.streaming_threads:
            # Stop existing thread
            self.stop_stream_for_client(client_id)
        
        # Create and start new streaming thread
        thread = threading.Thread(
            target=self._stream_worker,
            args=(client_id,),
            daemon=True,
            name=f"VideoStream-{client_id[:8]}"
        )
        self.streaming_threads[client_id] = thread
        thread.start()
        
        logger.info(f"Started streaming thread for client {client_id}")
    
    def stop_stream_for_client(self, client_id: str, disconnect_client: bool = False):
        """Stop streaming for a specific client and optionally disconnect them."""
        # Mark as not streaming
        if client_id in self.active_connections:
            self.active_connections[client_id]['streaming'] = False
        
        # Wait for thread to finish
        if client_id in self.streaming_threads:
            thread = self.streaming_threads[client_id]
            if thread.is_alive():
                # Thread will stop when streaming flag is False
                thread.join(timeout=1.0)
            del self.streaming_threads[client_id]
        
        # Release camera and deinitialize if no other clients are streaming
        try:
            # Check if any other clients are still streaming
            other_clients_streaming = any(
                conn['streaming'] for cid, conn in self.active_connections.items() 
                if cid != client_id
            )
            
            if not other_clients_streaming:
                # No other clients streaming, safe to release camera
                camera_status = camera_model.get_status()
                if camera_status['is_active']:
                    logger.info("Stopping camera stream - no active clients")
                    camera_model.stop_stream()
                    camera_model.cleanup()
                    logger.info("Camera stopped and cleaned up")
                else:
                    logger.info("Camera already inactive")
            else:
                logger.info(f"Camera remains active - {sum(1 for conn in self.active_connections.values() if conn.get('streaming', False))} other clients streaming")
                
        except Exception as e:
            logger.error(f"Error releasing camera for client {client_id}: {e}")
        
        # Only disconnect client if explicitly requested (e.g., for cleanup scenarios)
        if disconnect_client:
            # Notify client that stream is being stopped
            try:
                self.socketio.emit('stream_force_stop', {
                    'reason': 'Stream stopped by server',
                    'timestamp': time.time()
                }, namespace='/video', room=client_id)
                logger.info(f"Notified client {client_id} of stream stop")
            except Exception as e:
                logger.warning(f"Error notifying client {client_id}: {e}")
            
            # Clean up connection data for disconnected clients
            if client_id in self.active_connections:
                del self.active_connections[client_id]
        
        logger.info(f"Stopped streaming for client {client_id} (disconnect: {disconnect_client})")
    
    def _encode_frame_fast(self, frame_data: bytes, method: str) -> tuple:
        """Fast encoding methods for frame data."""
        encode_start = time.time()
        
        if method == 'binary':
            # Fastest: Direct binary transmission (no encoding needed)
            encoded_data = frame_data
            encode_time = time.time() - encode_start
            return encoded_data, encode_time, 'binary'
            
        elif method == 'compressed':
            # Compress then base64 encode
            compressed = zlib.compress(frame_data, level=1)  # Fast compression
            encoded_data = base64.b64encode(compressed).decode('utf-8')
            encode_time = time.time() - encode_start
            return encoded_data, encode_time, 'compressed'
            
        else:  # base64 (fallback)
            # Traditional base64 encoding
            encoded_data = base64.b64encode(frame_data).decode('utf-8')
            encode_time = time.time() - encode_start
            return encoded_data, encode_time, 'base64'
    
    def _adjust_quality_for_bitrate(self, client_id: str, current_bitrate_kbps: float, target_kbps: int) -> int:
        """Adjust quality based on current vs target bitrate."""
        if client_id not in self.active_connections:
            return 85  # Default quality
        
        conn_data = self.active_connections[client_id]
        bitrate_control = conn_data['bitrate_control']
        current_time = time.time()
        
        # Only adjust every 2 seconds to avoid oscillation
        if current_time - bitrate_control['last_adjustment_time'] < 2.0:
            return conn_data['quality']
        
        base_quality = 85  # Base quality without adjustments
        current_adjustment = bitrate_control['quality_adjustment']
        
        # Calculate bitrate difference
        bitrate_diff_percent = ((current_bitrate_kbps - target_kbps) / target_kbps) * 100
        
        # Adjust quality based on bitrate difference
        if bitrate_diff_percent > 20:  # 20% over target
            # Reduce quality more aggressively
            adjustment_change = -10
        elif bitrate_diff_percent > 10:  # 10% over target
            # Reduce quality moderately
            adjustment_change = -5
        elif bitrate_diff_percent < -20:  # 20% under target
            # Increase quality more aggressively
            adjustment_change = 10
        elif bitrate_diff_percent < -10:  # 10% under target
            # Increase quality moderately
            adjustment_change = 5
        else:
            # Within acceptable range, small adjustment towards optimal
            if bitrate_diff_percent > 5:
                adjustment_change = -2
            elif bitrate_diff_percent < -5:
                adjustment_change = 2
            else:
                adjustment_change = 0
        
        # Apply adjustment with limits
        new_adjustment = max(-50, min(50, current_adjustment + adjustment_change))
        adjusted_quality = max(20, min(95, base_quality + new_adjustment))
        
        # Update adjustment tracking
        bitrate_control['quality_adjustment'] = new_adjustment
        bitrate_control['last_adjustment_time'] = current_time
        
        if adjustment_change != 0:
            logger.info(f"Bitrate control for client {client_id}: {current_bitrate_kbps:.1f}kbps -> target {target_kbps}kbps, "
                       f"quality {conn_data['quality']} -> {adjusted_quality} (adj: {new_adjustment})")
        
        return adjusted_quality
    
    def _stream_worker(self, client_id: str):
        """Worker thread for streaming video frames to a specific client."""
        logger.info(f"Video streaming worker started for client {client_id}")
        
        # Performance optimization variables
        last_encode_time = 0
        last_frame_size = 0
        
        try:
            while True:
                # Check if client is still connected and streaming
                if client_id not in self.active_connections:
                    break
                
                conn_data = self.active_connections[client_id]
                if not conn_data['streaming']:
                    break
                
                # Calculate frame timing
                target_fps = conn_data['target_fps']
                frame_interval = 1.0 / target_fps if target_fps > 0 else 1.0 / 30
                
                # Check if it's time for next frame
                current_time = time.time()
                time_since_last = current_time - conn_data['last_frame_time']
                
                # Frame timing: if we're behind, skip frames
                if time_since_last < frame_interval * 0.8:  # 80% threshold
                    time.sleep(0.001)  # Short sleep to prevent busy waiting
                    continue
                
                # Use user-specified quality with bitrate control
                encode_start = time.time()
                base_quality = conn_data['quality']
                encoding_method = conn_data.get('encoding_method', 'binary')
                
                # Apply bitrate control if enabled
                effective_quality = base_quality
                if conn_data['bitrate_control']['enabled'] and conn_data['performance_stats']['current_bitrate_mbps'] > 0:
                    current_bitrate_kbps = conn_data['performance_stats']['current_bitrate_mbps'] * 1000
                    target_kbps = conn_data['bitrate_control']['target_kbps']
                    effective_quality = self._adjust_quality_for_bitrate(client_id, current_bitrate_kbps, target_kbps)

                self.active_connections[client_id]['quality'] = effective_quality
                # Get frame from camera with calculated quality
                frame_data = camera_model.get_frame_as_jpeg(quality=effective_quality)
                
                if frame_data:
                    # Get frame size
                    current_frame_size = len(frame_data)
                    
                    # Skip frame if it's too large and we have recent frame data
                    if (current_frame_size > 150000 and  # >150KB (increased threshold)
                        last_frame_size > 0 and 
                        current_time - conn_data['last_frame_time'] < frame_interval * 2):
                        time.sleep(0.005)
                        conn_data['performance_stats']['frames_skipped'] += 1
                        continue
                    
                    # Fast encoding based on method
                    encoded_data, encode_time, actual_method = self._encode_frame_fast(frame_data, encoding_method)
                    
                    # Send frame to client with appropriate format
                    try:
                        if actual_method == 'binary':
                            # Send binary data directly (much faster)
                            self.socketio.emit('video_frame_binary', {
                                'timestamp': current_time,
                                'frame_count': conn_data['frame_count'],
                                'quality': effective_quality,
                                'base_quality': base_quality,
                                'frame_size': current_frame_size,
                                'encode_time': encode_time,
                                'encoding': actual_method,
                                'bitrate_control': conn_data['bitrate_control']['enabled']
                            }, namespace='/video', room=client_id)
                            # Send binary data separately
                            self.socketio.emit('frame_data', encoded_data, namespace='/video', room=client_id)
                        else:
                            # Send text-based data (base64 or compressed)
                            self.socketio.emit('video_frame', {
                                'frame': encoded_data,
                                'timestamp': current_time,
                                'frame_count': conn_data['frame_count'],
                                'quality': effective_quality,
                                'base_quality': base_quality,
                                'frame_size': current_frame_size,
                                'encode_time': encode_time,
                                'encoding': actual_method,
                                'bitrate_control': conn_data['bitrate_control']['enabled']
                            }, namespace='/video', room=client_id)
                        
                        # Update connection data
                        conn_data['last_frame_time'] = current_time
                        conn_data['frame_count'] += 1
                        last_encode_time = encode_time
                        last_frame_size = current_frame_size
                        
                        # Update performance statistics
                        perf_stats = conn_data['performance_stats']
                        
                        # Update total bytes sent
                        perf_stats['total_bytes_sent'] += current_frame_size
                        perf_stats['bitrate_window_bytes'] += current_frame_size
                        
                        # Calculate bitrate every second
                        bitrate_window_duration = current_time - perf_stats['bitrate_window_start']
                        if bitrate_window_duration >= 1.0:  # Calculate bitrate every second
                            # Calculate bitrate in Mbps
                            bits_per_second = (perf_stats['bitrate_window_bytes'] * 8) / bitrate_window_duration
                            perf_stats['current_bitrate_mbps'] = bits_per_second / 1_000_000  # Convert to Mbps
                            
                            # Reset bitrate window
                            perf_stats['bitrate_window_start'] = current_time
                            perf_stats['bitrate_window_bytes'] = 0
                        
                        # Running average of encode time
                        if perf_stats['avg_encode_time'] == 0:
                            perf_stats['avg_encode_time'] = encode_time
                        else:
                            perf_stats['avg_encode_time'] = (perf_stats['avg_encode_time'] * 0.9) + (encode_time * 0.1)
                        
                        # Running average of frame size
                        if perf_stats['avg_frame_size'] == 0:
                            perf_stats['avg_frame_size'] = current_frame_size
                        else:
                            perf_stats['avg_frame_size'] = (perf_stats['avg_frame_size'] * 0.9) + (current_frame_size * 0.1)
                        
                        # Log performance warnings
                        if encode_time > frame_interval:
                            logger.warning(f"Slow encoding for client {client_id}: {encode_time:.3f}s > {frame_interval:.3f}s")
                        
                    except Exception as emit_error:
                        logger.error(f"Error emitting frame to client {client_id}: {emit_error}")
                        # Don't break the loop, just skip this frame
                        time.sleep(0.01)
                        continue
                        
                else:
                    # No frame available, adaptive sleep based on how long we've been waiting
                    if time_since_last > frame_interval * 3:  # If we haven't had a frame for 3x the interval
                        time.sleep(0.05)  # Longer sleep
                    else:
                        time.sleep(0.01)  # Short sleep
                
        except Exception as e:
            logger.error(f"Error in streaming worker for client {client_id}: {e}")
            # Notify client of error
            try:
                self.socketio.emit('stream_error', {
                    'error': str(e),
                    'code': 'STREAMING_ERROR'
                }, namespace='/video', room=client_id)
            except:
                pass  # Don't let error notification errors crash the worker
        
        finally:
            logger.info(f"Video streaming worker finished for client {client_id}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics for all active connections."""
        stats = {
            'total_connections': len(self.active_connections),
            'active_streams': sum(1 for conn in self.active_connections.values() if conn['streaming']),
            'connections': {}
        }
        
        for client_id, conn_data in self.active_connections.items():
            perf_stats = conn_data.get('performance_stats', {})
            bitrate_control = conn_data.get('bitrate_control', {})
            stats['connections'][client_id] = {
                'streaming': conn_data['streaming'],
                'frame_count': conn_data['frame_count'],
                'connection_time': time.time() - conn_data['connection_time'],
                'camera_index': conn_data.get('camera_index'),
                'quality': conn_data.get('quality'),
                'target_fps': conn_data.get('target_fps'),
                'current_bitrate_mbps': perf_stats.get('current_bitrate_mbps', 0),
                'total_bytes_sent': perf_stats.get('total_bytes_sent', 0),
                'avg_frame_size': perf_stats.get('avg_frame_size', 0),
                'encoding_method': conn_data.get('encoding_method', 'binary'),
                'max_bitrate_kbps': conn_data.get('max_bitrate_kbps', 0),
                'bitrate_control_enabled': bitrate_control.get('enabled', False),
                'quality_adjustment': bitrate_control.get('quality_adjustment', 0)
            }
        
        return stats


# Global WebSocket streamer instance
websocket_streamer: Optional[WebSocketVideoStreamer] = None

def init_websocket_streaming(socketio: SocketIO):
    """Initialize WebSocket streaming with the given SocketIO instance."""
    global websocket_streamer
    websocket_streamer = WebSocketVideoStreamer(socketio)
    logger.info("WebSocket video streaming initialized")
    return websocket_streamer

def get_websocket_streamer() -> Optional[WebSocketVideoStreamer]:
    """Get the global WebSocket streamer instance."""
    return websocket_streamer
