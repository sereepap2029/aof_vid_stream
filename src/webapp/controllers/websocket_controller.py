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

from flask import request
from flask_socketio import SocketIO, emit, disconnect
from ..models.camera_model import camera_model

logger = logging.getLogger(__name__)

class WebSocketVideoStreamer:
    """
    WebSocket-based video streaming controller.
    Handles real-time video transmission with configurable quality and framerate.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.streaming_threads: Dict[str, threading.Thread] = {}
        self.setup_handlers()
    
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
                'connection_time': time.time()
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
            
            # Stop streaming for this client
            self.stop_stream_for_client(client_id)
            
            # Clean up connection data
            if client_id in self.active_connections:
                del self.active_connections[client_id]
        
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
            
            self.stop_stream_for_client(client_id)
            
            emit('stream_stopped', {
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
                
                emit('fps_updated', {
                    'fps': fps,
                    'timestamp': time.time()
                })
        
        @self.socketio.on('get_stats', namespace='/video')
        def handle_get_stats():
            """Handle statistics request."""
            client_id = request.sid
            
            if client_id in self.active_connections:
                conn_data = self.active_connections[client_id]
                camera_status = camera_model.get_status()
                
                stats = {
                    'client_id': client_id,
                    'streaming': conn_data['streaming'],
                    'frame_count': conn_data['frame_count'],
                    'connection_time': time.time() - conn_data['connection_time'],
                    'camera_status': camera_status,
                    'timestamp': time.time()
                }
                
                emit('stream_stats', stats)
    
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
    
    def stop_stream_for_client(self, client_id: str):
        """Stop streaming for a specific client."""
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
        
        logger.info(f"Stopped streaming for client {client_id}")
    
    def _stream_worker(self, client_id: str):
        """Worker thread for streaming video frames to a specific client."""
        logger.info(f"Video streaming worker started for client {client_id}")
        
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
                if current_time - conn_data['last_frame_time'] < frame_interval:
                    time.sleep(0.001)  # Short sleep to prevent busy waiting
                    continue
                
                # Get frame from camera
                frame_data = camera_model.get_frame_as_jpeg(quality=conn_data['quality'])
                
                if frame_data:
                    # Encode frame as base64 for WebSocket transmission
                    frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                    
                    # Send frame to client
                    self.socketio.emit('video_frame', {
                        'frame': frame_b64,
                        'timestamp': current_time,
                        'frame_count': conn_data['frame_count'],
                        'quality': conn_data['quality']
                    }, namespace='/video', room=client_id)
                    
                    # Update connection data
                    conn_data['last_frame_time'] = current_time
                    conn_data['frame_count'] += 1
                else:
                    # No frame available, short sleep
                    time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error in streaming worker for client {client_id}: {e}")
            # Notify client of error
            self.socketio.emit('stream_error', {
                'error': str(e),
                'code': 'STREAMING_ERROR'
            }, namespace='/video', room=client_id)
        
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
            stats['connections'][client_id] = {
                'streaming': conn_data['streaming'],
                'frame_count': conn_data['frame_count'],
                'connection_time': time.time() - conn_data['connection_time'],
                'camera_index': conn_data.get('camera_index'),
                'quality': conn_data.get('quality'),
                'target_fps': conn_data.get('target_fps')
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
