"""
AOF Video Stream - Stream Model

This module contains the streaming data model and business logic.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import logging
import json

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """Enumeration of possible stream states."""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"


class StreamQuality(Enum):
    """Enumeration of stream quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class StreamSettings:
    """Data class for stream configuration settings."""
    quality: StreamQuality = StreamQuality.MEDIUM
    fps: int = 30
    resolution: tuple = (640, 480)
    compression: int = 85  # JPEG quality
    buffer_size: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'quality': self.quality.value,
            'fps': self.fps,
            'resolution': self.resolution,
            'compression': self.compression,
            'buffer_size': self.buffer_size
        }


@dataclass
class StreamMetrics:
    """Data class for stream performance metrics."""
    start_time: Optional[datetime] = None
    total_frames: int = 0
    dropped_frames: int = 0
    average_fps: float = 0.0
    current_fps: float = 0.0
    bandwidth_mbps: float = 0.0
    latency_ms: float = 0.0
    active_connections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'total_frames': self.total_frames,
            'dropped_frames': self.dropped_frames,
            'average_fps': round(self.average_fps, 2),
            'current_fps': round(self.current_fps, 2),
            'bandwidth_mbps': round(self.bandwidth_mbps, 2),
            'latency_ms': round(self.latency_ms, 2),
            'active_connections': self.active_connections,
            'uptime_seconds': self._get_uptime_seconds()
        }
    
    def _get_uptime_seconds(self) -> int:
        """Calculate uptime in seconds."""
        if self.start_time:
            return int((datetime.now() - self.start_time).total_seconds())
        return 0


class StreamSession:
    """
    Represents an individual streaming session.
    """
    
    def __init__(self, session_id: str, camera_index: int, settings: StreamSettings):
        """
        Initialize a stream session.
        
        Args:
            session_id: Unique identifier for the session
            camera_index: Index of the camera being streamed
            settings: Stream configuration settings
        """
        self.session_id = session_id
        self.camera_index = camera_index
        self.settings = settings
        self.state = StreamState.STOPPED
        self.metrics = StreamMetrics()
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Performance tracking
        self._frame_times: List[float] = []
        self._lock = threading.Lock()
        
        logger.info(f"Created stream session {session_id} for camera {camera_index}")
    
    def update_metrics(self, frame_size_bytes: int) -> None:
        """
        Update stream metrics with new frame data.
        
        Args:
            frame_size_bytes: Size of the current frame in bytes
        """
        with self._lock:
            current_time = time.time()
            self._frame_times.append(current_time)
            
            # Keep only last 30 frames for FPS calculation
            if len(self._frame_times) > 30:
                self._frame_times.pop(0)
            
            self.metrics.total_frames += 1
            self.last_activity = datetime.now()
            
            # Calculate current FPS
            if len(self._frame_times) >= 2:
                time_diff = self._frame_times[-1] - self._frame_times[0]
                if time_diff > 0:
                    self.metrics.current_fps = (len(self._frame_times) - 1) / time_diff
            
            # Calculate average FPS
            if self.metrics.start_time:
                uptime = (datetime.now() - self.metrics.start_time).total_seconds()
                if uptime > 0:
                    self.metrics.average_fps = self.metrics.total_frames / uptime
            
            # Calculate bandwidth (rough estimate)
            if self.metrics.current_fps > 0:
                self.metrics.bandwidth_mbps = (frame_size_bytes * self.metrics.current_fps * 8) / (1024 * 1024)
    
    def start(self) -> None:
        """Start the stream session."""
        with self._lock:
            self.state = StreamState.STARTING
            self.metrics.start_time = datetime.now()
            self.error_message = None
            logger.info(f"Starting stream session {self.session_id}")
    
    def activate(self) -> None:
        """Mark the stream session as active."""
        with self._lock:
            self.state = StreamState.ACTIVE
            logger.info(f"Stream session {self.session_id} is now active")
    
    def stop(self) -> None:
        """Stop the stream session."""
        with self._lock:
            self.state = StreamState.STOPPING
            logger.info(f"Stopping stream session {self.session_id}")
    
    def set_error(self, error_message: str) -> None:
        """Set error state for the stream session."""
        with self._lock:
            self.state = StreamState.ERROR
            self.error_message = error_message
            logger.error(f"Stream session {self.session_id} error: {error_message}")
    
    def is_active(self) -> bool:
        """Check if the stream session is active."""
        return self.state == StreamState.ACTIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stream session to dictionary."""
        return {
            'session_id': self.session_id,
            'camera_index': self.camera_index,
            'state': self.state.value,
            'settings': self.settings.to_dict(),
            'metrics': self.metrics.to_dict(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }


class StreamModel:
    """
    Stream model managing streaming sessions and configuration.
    
    This class handles the business logic for video streaming,
    session management, and performance monitoring.
    """
    
    def __init__(self):
        """Initialize the stream model."""
        self._sessions: Dict[str, StreamSession] = {}
        self._active_session: Optional[StreamSession] = None
        self._default_settings = StreamSettings()
        self._lock = threading.Lock()
        
        # Stream event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {
            'session_started': [],
            'session_stopped': [],
            'session_error': [],
            'frame_received': []
        }
        
        logger.info("Stream model initialized")
    
    def create_session(self, session_id: str, camera_index: int, settings: Optional[StreamSettings] = None) -> StreamSession:
        """
        Create a new streaming session.
        
        Args:
            session_id: Unique identifier for the session
            camera_index: Index of the camera to stream
            settings: Stream configuration settings
            
        Returns:
            Created stream session
        """
        if settings is None:
            settings = self._default_settings
        
        with self._lock:
            session = StreamSession(session_id, camera_index, settings)
            self._sessions[session_id] = session
            
            logger.info(f"Created stream session: {session_id}")
            return session
    
    def start_session(self, session_id: str) -> bool:
        """
        Start a streaming session.
        
        Args:
            session_id: ID of the session to start
            
        Returns:
            True if session started successfully, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Stop current active session if any
            if self._active_session and self._active_session.is_active():
                self.stop_session(self._active_session.session_id)
            
            try:
                session.start()
                self._active_session = session
                
                # Trigger event callbacks
                self._trigger_event('session_started', session)
                
                return True
                
            except Exception as e:
                session.set_error(str(e))
                logger.error(f"Failed to start session {session_id}: {e}")
                return False
    
    def stop_session(self, session_id: str) -> bool:
        """
        Stop a streaming session.
        
        Args:
            session_id: ID of the session to stop
            
        Returns:
            True if session stopped successfully, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            try:
                session.stop()
                
                if self._active_session and self._active_session.session_id == session_id:
                    self._active_session = None
                
                # Trigger event callbacks
                self._trigger_event('session_stopped', session)
                
                return True
                
            except Exception as e:
                session.set_error(str(e))
                logger.error(f"Failed to stop session {session_id}: {e}")
                return False
    
    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """
        Get a streaming session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Stream session or None if not found
        """
        return self._sessions.get(session_id)
    
    def get_active_session(self) -> Optional[StreamSession]:
        """
        Get the currently active streaming session.
        
        Returns:
            Active stream session or None
        """
        return self._active_session
    
    def get_all_sessions(self) -> List[StreamSession]:
        """
        Get all streaming sessions.
        
        Returns:
            List of all stream sessions
        """
        return list(self._sessions.values())
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a streaming session.
        
        Args:
            session_id: ID of the session to remove
            
        Returns:
            True if session removed successfully, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            # Stop session if active
            if session.is_active():
                self.stop_session(session_id)
            
            # Remove from sessions
            del self._sessions[session_id]
            
            if self._active_session and self._active_session.session_id == session_id:
                self._active_session = None
            
            logger.info(f"Removed stream session: {session_id}")
            return True
    
    def update_frame_metrics(self, session_id: str, frame_size_bytes: int) -> None:
        """
        Update frame metrics for a session.
        
        Args:
            session_id: ID of the session
            frame_size_bytes: Size of the frame in bytes
        """
        session = self._sessions.get(session_id)
        if session:
            session.update_metrics(frame_size_bytes)
            self._trigger_event('frame_received', session)
    
    def get_stream_status(self) -> Dict[str, Any]:
        """
        Get overall streaming status.
        
        Returns:
            Dictionary containing streaming status information
        """
        active_session = self.get_active_session()
        
        return {
            'is_streaming': active_session is not None and active_session.is_active(),
            'active_session': active_session.to_dict() if active_session else None,
            'total_sessions': len(self._sessions),
            'session_list': [session.to_dict() for session in self._sessions.values()]
        }
    
    def register_event_callback(self, event_name: str, callback: Callable) -> None:
        """
        Register a callback for stream events.
        
        Args:
            event_name: Name of the event
            callback: Callback function to register
        """
        if event_name in self._event_callbacks:
            self._event_callbacks[event_name].append(callback)
    
    def _trigger_event(self, event_name: str, session: StreamSession) -> None:
        """
        Trigger event callbacks.
        
        Args:
            event_name: Name of the event
            session: Stream session that triggered the event
        """
        for callback in self._event_callbacks.get(event_name, []):
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Error in event callback {event_name}: {e}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """
        Clean up old inactive sessions.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, session in self._sessions.items():
            if not session.is_active() and session.created_at < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.remove_session(session_id)
            logger.info(f"Cleaned up old session: {session_id}")


# Global stream model instance
stream_model = StreamModel()
