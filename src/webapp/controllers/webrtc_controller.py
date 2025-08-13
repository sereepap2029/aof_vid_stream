"""
AOF Video Stream - WebRTC Controller

This module handles WebRTC-based real-time video streaming with frame chunking.
Provides ultra-low latency, high-performance video transmission for high-resolution streams.
"""

import asyncio
import json
import time
import threading
import struct
import uuid
from typing import Optional, Dict, Any, List
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib

from flask import request
from flask_socketio import SocketIO, emit, disconnect
from ..models.camera_model import camera_model

logger = logging.getLogger(__name__)

class FrameChunker:
    """
    Handles frame chunking for large video frames.
    Splits large frames into smaller chunks for better network handling.
    """
    
    def __init__(self, chunk_size: int = 32768):  # 32KB chunks
        self.chunk_size = chunk_size
        self.frame_cache: Dict[str, Dict] = {}  # Cache for reassembling chunks
        
    def chunk_frame(self, frame_data: bytes, frame_id: str) -> List[Dict]:
        """Split frame into smaller chunks."""
        chunks = []
        total_size = len(frame_data)
        total_chunks = (total_size + self.chunk_size - 1) // self.chunk_size
        
        # Create frame metadata
        frame_hash = hashlib.md5(frame_data).hexdigest()[:16]
        
        for i in range(total_chunks):
            start_idx = i * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, total_size)
            chunk_data = frame_data[start_idx:end_idx]
            
            chunk = {
                'frame_id': frame_id,
                'chunk_index': i,
                'total_chunks': total_chunks,
                'chunk_size': len(chunk_data),
                'total_size': total_size,
                'frame_hash': frame_hash,
                'data': chunk_data
            }
            chunks.append(chunk)
            
        return chunks
    
    def reassemble_frame(self, chunk: Dict) -> Optional[bytes]:
        """Reassemble frame from chunks."""
        frame_id = chunk['frame_id']
        
        # Initialize frame cache entry
        if frame_id not in self.frame_cache:
            self.frame_cache[frame_id] = {
                'chunks': {},
                'total_chunks': chunk['total_chunks'],
                'total_size': chunk['total_size'],
                'frame_hash': chunk['frame_hash'],
                'received_at': time.time()
            }
        
        frame_entry = self.frame_cache[frame_id]
        frame_entry['chunks'][chunk['chunk_index']] = chunk['data']
        
        # Check if all chunks received
        if len(frame_entry['chunks']) == frame_entry['total_chunks']:
            # Reassemble frame
            frame_data = b''
            for i in range(frame_entry['total_chunks']):
                if i in frame_entry['chunks']:
                    frame_data += frame_entry['chunks'][i]
                else:
                    # Missing chunk
                    logger.warning(f"Missing chunk {i} for frame {frame_id}")
                    return None
            
            # Verify frame integrity
            frame_hash = hashlib.md5(frame_data).hexdigest()[:16]
            if frame_hash != frame_entry['frame_hash']:
                logger.error(f"Frame hash mismatch for {frame_id}")
                return None
            
            # Clean up cache
            del self.frame_cache[frame_id]
            return frame_data
        
        return None
    
    def cleanup_old_frames(self, max_age: float = 5.0):
        """Clean up old incomplete frames from cache."""
        current_time = time.time()
        expired_frames = []
        
        for frame_id, frame_entry in self.frame_cache.items():
            if current_time - frame_entry['received_at'] > max_age:
                expired_frames.append(frame_id)
        
        for frame_id in expired_frames:
            logger.warning(f"Cleaning up expired frame {frame_id}")
            del self.frame_cache[frame_id]


class WebRTCVideoStreamer:
    """
    WebRTC-based video streaming controller with frame chunking.
    Optimized for high-resolution, high-framerate streaming.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.streaming_threads: Dict[str, threading.Thread] = {}
        self.chunkers: Dict[str, FrameChunker] = {}  # Per-client chunkers
        
        # High-performance thread pool for frame processing
        self.frame_pool = ThreadPoolExecutor(
            max_workers=8, 
            thread_name_prefix="WebRTCFrame"
        )
        
        # Cleanup thread for old frames
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="WebRTCCleanup"
        )
        self.cleanup_thread.start()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup WebRTC WebSocket event handlers."""
        
        @self.socketio.on('connect', namespace='/webrtc')
        def handle_connect():
            """Handle WebRTC client connection."""
            client_id = request.sid
            logger.info(f"WebRTC client connected: {client_id}")
            
            # Initialize client connection data
            self.active_connections[client_id] = {
                'connected': True,
                'streaming': False,
                'stream_mode': 'webrtc',
                'camera_index': None,
                'quality': 85,
                'target_fps': 60,  # Default to 60fps for WebRTC
                'resolution': [1920, 1080],  # Default to 1080p
                'last_frame_time': 0,
                'frame_count': 0,
                'connection_time': time.time(),
                'performance_stats': {
                    'avg_encode_time': 0,
                    'avg_frame_size': 0,
                    'frames_skipped': 0,
                    'total_bytes_sent': 0,
                    'chunks_sent': 0,
                    'frames_chunked': 0,
                    'current_bitrate_mbps': 0,
                    'chunk_success_rate': 100.0
                },
                'encoding_method': 'binary',
                'chunk_size': 32768,  # 32KB default chunk size
                'enable_chunking': True,
                'max_frame_size': 500000,  # 500KB max before forced chunking
            }
            
            # Initialize frame chunker for this client
            self.chunkers[client_id] = FrameChunker(
                chunk_size=self.active_connections[client_id]['chunk_size']
            )
            
            emit('webrtc_connected', {
                'status': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'capabilities': {
                    'max_resolution': [1920, 1080],
                    'max_fps': 60,
                    'chunk_support': True,
                    'binary_support': True
                }
            })
        
        @self.socketio.on('disconnect', namespace='/webrtc')
        def handle_disconnect():
            """Handle WebRTC client disconnection."""
            client_id = request.sid
            logger.info(f"WebRTC client disconnected: {client_id}")
            
            # Stop streaming for this client
            self.stop_stream_for_client(client_id)
            
            # Clean up connection data
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            if client_id in self.chunkers:
                del self.chunkers[client_id]
        
        @self.socketio.on('start_webrtc_stream', namespace='/webrtc')
        def handle_start_stream(data):
            """Handle WebRTC stream start request."""
            client_id = request.sid
            
            try:
                camera_index = data.get('camera_index', 1)
                resolution = data.get('resolution', [1920, 1080])
                fps = data.get('fps', 60)
                quality = data.get('quality', 85)
                chunk_size = data.get('chunk_size', 32768)
                enable_chunking = data.get('enable_chunking', True)
                
                logger.info(f"Starting WebRTC stream for client {client_id}: "
                           f"camera={camera_index}, resolution={resolution}, fps={fps}, "
                           f"quality={quality}, chunking={enable_chunking}")
                
                # Start camera if not already active
                camera_status = camera_model.get_status()
                if not camera_status['is_active']:
                    success = camera_model.start_stream(camera_index, tuple(resolution), fps)
                    if not success:
                        emit('webrtc_error', {
                            'error': 'Failed to start camera',
                            'code': 'CAMERA_START_FAILED'
                        })
                        return
                
                # Update connection data
                if client_id in self.active_connections:
                    conn_data = self.active_connections[client_id]
                    conn_data.update({
                        'streaming': True,
                        'camera_index': camera_index,
                        'quality': quality,
                        'target_fps': fps,
                        'resolution': resolution,
                        'chunk_size': chunk_size,
                        'enable_chunking': enable_chunking
                    })
                    
                    # Update chunker settings
                    if client_id in self.chunkers:
                        self.chunkers[client_id].chunk_size = chunk_size
                
                # Start streaming thread for this client
                self.start_stream_for_client(client_id)
                
                emit('webrtc_stream_started', {
                    'camera_index': camera_index,
                    'resolution': resolution,
                    'fps': fps,
                    'quality': quality,
                    'chunk_size': chunk_size,
                    'chunking_enabled': enable_chunking,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                logger.error(f"Error starting WebRTC stream: {e}")
                emit('webrtc_error', {
                    'error': str(e),
                    'code': 'STREAM_START_ERROR'
                })
        
        @self.socketio.on('stop_webrtc_stream', namespace='/webrtc')
        def handle_stop_stream():
            """Handle WebRTC stream stop request."""
            client_id = request.sid
            logger.info(f"Stopping WebRTC stream for client {client_id}")
            
            self.stop_stream_for_client(client_id)
            
            emit('webrtc_stream_stopped', {
                'timestamp': time.time()
            })
        
        @self.socketio.on('chunk_received', namespace='/webrtc')
        def handle_chunk_received(data):
            """Handle chunk reception acknowledgment from client."""
            client_id = request.sid
            frame_id = data.get('frame_id')
            chunk_index = data.get('chunk_index')
            
            # Update performance stats
            if client_id in self.active_connections:
                conn_data = self.active_connections[client_id]
                # Could implement chunk success rate tracking here
        
        @self.socketio.on('request_chunk_resend', namespace='/webrtc')
        def handle_chunk_resend(data):
            """Handle request for chunk retransmission."""
            client_id = request.sid
            frame_id = data.get('frame_id')
            chunk_index = data.get('chunk_index')
            
            logger.warning(f"Chunk resend requested for client {client_id}: "
                         f"frame {frame_id}, chunk {chunk_index}")
            
            # Could implement chunk caching and resending here
    
    def start_stream_for_client(self, client_id: str):
        """Start WebRTC streaming thread for a specific client."""
        if client_id in self.streaming_threads:
            # Stop existing thread
            self.stop_stream_for_client(client_id)
        
        # Create and start new streaming thread
        thread = threading.Thread(
            target=self._webrtc_stream_worker,
            args=(client_id,),
            daemon=True,
            name=f"WebRTCStream-{client_id[:8]}"
        )
        self.streaming_threads[client_id] = thread
        thread.start()
        
        logger.info(f"Started WebRTC streaming thread for client {client_id}")
    
    def stop_stream_for_client(self, client_id: str):
        """Stop WebRTC streaming for a specific client."""
        # Mark as not streaming
        if client_id in self.active_connections:
            self.active_connections[client_id]['streaming'] = False
        
        # Wait for thread to finish
        if client_id in self.streaming_threads:
            thread = self.streaming_threads[client_id]
            if thread.is_alive():
                thread.join(timeout=1.0)
            del self.streaming_threads[client_id]
        
        logger.info(f"Stopped WebRTC streaming for client {client_id}")
    
    def _webrtc_stream_worker(self, client_id: str):
        """Worker thread for WebRTC video streaming with frame chunking."""
        logger.info(f"WebRTC streaming worker started for client {client_id}")
        
        try:
            while True:
                # Check if client is still connected and streaming
                if client_id not in self.active_connections:
                    break
                
                conn_data = self.active_connections[client_id]
                if not conn_data['streaming']:
                    break
                
                # Calculate frame timing for high FPS
                target_fps = conn_data['target_fps']
                frame_interval = 1.0 / target_fps if target_fps > 0 else 1.0 / 60
                
                # Check if it's time for next frame
                current_time = time.time()
                time_since_last = current_time - conn_data['last_frame_time']
                
                # High-precision frame timing
                if time_since_last < frame_interval * 0.95:  # 95% threshold for precision
                    time.sleep(0.0001)  # Very short sleep for high FPS
                    continue
                
                # Get frame from camera
                quality = conn_data['quality']
                frame_data = camera_model.get_frame_as_jpeg(quality=quality)
                
                if frame_data:
                    frame_size = len(frame_data)
                    frame_id = f"{client_id}_{conn_data['frame_count']}_{int(current_time*1000)}"
                    
                    # Update frame count and timing
                    conn_data['frame_count'] += 1
                    conn_data['last_frame_time'] = current_time
                    
                    # Decide whether to chunk the frame
                    should_chunk = (
                        conn_data['enable_chunking'] and 
                        frame_size > conn_data['max_frame_size']
                    )
                    
                    if should_chunk and client_id in self.chunkers:
                        # Send frame in chunks
                        self._send_chunked_frame(client_id, frame_data, frame_id, current_time)
                    else:
                        # Send frame as single packet
                        self._send_single_frame(client_id, frame_data, frame_id, current_time)
                    
                    # Update performance statistics
                    self._update_performance_stats(client_id, frame_size, should_chunk)
                
                else:
                    # No frame available, adaptive sleep
                    if time_since_last > frame_interval * 2:
                        time.sleep(0.001)
                    else:
                        time.sleep(0.0001)
                
        except Exception as e:
            logger.error(f"Error in WebRTC streaming worker for client {client_id}: {e}")
            try:
                self.socketio.emit('webrtc_error', {
                    'error': str(e),
                    'code': 'STREAMING_ERROR'
                }, namespace='/webrtc', room=client_id)
            except:
                pass
        
        finally:
            logger.info(f"WebRTC streaming worker finished for client {client_id}")
    
    def _send_chunked_frame(self, client_id: str, frame_data: bytes, frame_id: str, timestamp: float):
        """Send frame using chunking for large frames."""
        try:
            chunker = self.chunkers[client_id]
            chunks = chunker.chunk_frame(frame_data, frame_id)
            
            conn_data = self.active_connections[client_id]
            conn_data['performance_stats']['frames_chunked'] += 1
            
            # Send frame metadata first
            self.socketio.emit('webrtc_frame_chunked', {
                'frame_id': frame_id,
                'timestamp': timestamp,
                'total_chunks': len(chunks),
                'total_size': len(frame_data),
                'quality': conn_data['quality']
            }, namespace='/webrtc', room=client_id)
            
            # Send chunks with small delays to prevent overwhelming
            for i, chunk in enumerate(chunks):
                self.socketio.emit('webrtc_chunk', {
                    'frame_id': chunk['frame_id'],
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'chunk_size': chunk['chunk_size'],
                    'frame_hash': chunk['frame_hash']
                }, namespace='/webrtc', room=client_id)
                
                # Send binary chunk data separately
                self.socketio.emit('webrtc_chunk_data', chunk['data'], 
                                 namespace='/webrtc', room=client_id)
                
                conn_data['performance_stats']['chunks_sent'] += 1
                
                # Small delay between chunks for very large frames
                if len(chunks) > 20:  # Only for very large frames
                    time.sleep(0.0001)
                    
        except Exception as e:
            logger.error(f"Error sending chunked frame to client {client_id}: {e}")
    
    def _send_single_frame(self, client_id: str, frame_data: bytes, frame_id: str, timestamp: float):
        """Send frame as single packet (no chunking)."""
        try:
            conn_data = self.active_connections[client_id]
            
            # Send frame metadata
            self.socketio.emit('webrtc_frame_single', {
                'frame_id': frame_id,
                'timestamp': timestamp,
                'frame_size': len(frame_data),
                'quality': conn_data['quality']
            }, namespace='/webrtc', room=client_id)
            
            # Send binary frame data
            self.socketio.emit('webrtc_frame_data', frame_data, 
                             namespace='/webrtc', room=client_id)
                             
        except Exception as e:
            logger.error(f"Error sending single frame to client {client_id}: {e}")
    
    def _update_performance_stats(self, client_id: str, frame_size: int, was_chunked: bool):
        """Update performance statistics for the client."""
        if client_id not in self.active_connections:
            return
        
        conn_data = self.active_connections[client_id]
        perf_stats = conn_data['performance_stats']
        
        # Update total bytes sent
        perf_stats['total_bytes_sent'] += frame_size
        
        # Update average frame size
        if perf_stats['avg_frame_size'] == 0:
            perf_stats['avg_frame_size'] = frame_size
        else:
            perf_stats['avg_frame_size'] = (perf_stats['avg_frame_size'] * 0.9) + (frame_size * 0.1)
    
    def _cleanup_worker(self):
        """Background worker to cleanup old frame chunks."""
        while True:
            try:
                time.sleep(1.0)  # Run cleanup every second
                
                for client_id, chunker in self.chunkers.items():
                    chunker.cleanup_old_frames(max_age=5.0)
                    
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics for all active WebRTC connections."""
        stats = {
            'total_connections': len(self.active_connections),
            'active_streams': sum(1 for conn in self.active_connections.values() if conn['streaming']),
            'stream_mode': 'webrtc',
            'connections': {}
        }
        
        for client_id, conn_data in self.active_connections.items():
            perf_stats = conn_data.get('performance_stats', {})
            stats['connections'][client_id] = {
                'streaming': conn_data['streaming'],
                'frame_count': conn_data['frame_count'],
                'connection_time': time.time() - conn_data['connection_time'],
                'camera_index': conn_data.get('camera_index'),
                'quality': conn_data.get('quality'),
                'target_fps': conn_data.get('target_fps'),
                'resolution': conn_data.get('resolution'),
                'chunk_size': conn_data.get('chunk_size'),
                'chunking_enabled': conn_data.get('enable_chunking'),
                'frames_chunked': perf_stats.get('frames_chunked', 0),
                'chunks_sent': perf_stats.get('chunks_sent', 0),
                'total_bytes_sent': perf_stats.get('total_bytes_sent', 0),
                'avg_frame_size': perf_stats.get('avg_frame_size', 0)
            }
        
        return stats


# Global WebRTC streamer instance
webrtc_streamer: Optional[WebRTCVideoStreamer] = None

def init_webrtc_streaming(socketio: SocketIO):
    """Initialize WebRTC streaming with the given SocketIO instance."""
    global webrtc_streamer
    webrtc_streamer = WebRTCVideoStreamer(socketio)
    logger.info("WebRTC video streaming initialized")
    return webrtc_streamer

def get_webrtc_streamer() -> Optional[WebRTCVideoStreamer]:
    """Get the global WebRTC streamer instance."""
    return webrtc_streamer
