"""
AOF Video Stream - Camera Model

This module contains the camera data model and business logic.
"""

from typing import List, Dict, Optional, Tuple, Any
import cv2
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Import camera components
from src.camera import CameraManager, DeviceDetector, VideoCapture

logger = logging.getLogger(__name__)


@dataclass
class CameraDevice:
    """Data class representing a camera device."""
    index: int
    name: str
    is_available: bool = True
    resolution: Tuple[int, int] = (640, 480)
    fps: int = 30
    last_seen: Optional[datetime] = None


@dataclass
class CameraStatus:
    """Data class representing camera status."""
    is_active: bool = False
    current_device: Optional[int] = None
    resolution: Tuple[int, int] = (640, 480)
    fps: int = 30
    frame_count: int = 0
    last_frame_time: Optional[datetime] = None
    error_message: Optional[str] = None


class CameraModel:
    """
    Camera model handling camera device management and video capture.
    
    This class provides a high-level interface for camera operations
    and maintains the state of camera devices and streaming.
    """
    
    # Class-level cache for devices to avoid repeated scanning
    _cached_devices: List[CameraDevice] = []
    _cache_timestamp: Optional[datetime] = None
    _cache_duration_seconds = 30  # Cache devices for 30 seconds
    
    def __init__(self):
        """Initialize the camera model."""
        self.camera_manager = CameraManager()
        self.device_detector = DeviceDetector()
        self.video_capture = VideoCapture()
        
        self._status = CameraStatus()
        self._current_frame: Optional[np.ndarray] = None
        
        # Use cached devices if available
        if self._is_cache_valid():
            self._devices = self._cached_devices.copy()
            logger.info(f"Camera model initialized using cached devices ({len(self._devices)} devices)")
        else:
            self._devices: List[CameraDevice] = []
            logger.info("Camera model initialized")
    
    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Check if the device cache is still valid."""
        if not cls._cached_devices or cls._cache_timestamp is None:
            return False
        
        cache_age = (datetime.now() - cls._cache_timestamp).total_seconds()
        return cache_age < cls._cache_duration_seconds
    
    @classmethod
    def _update_cache(cls, devices: List[CameraDevice]) -> None:
        """Update the device cache."""
        cls._cached_devices = devices.copy()
        cls._cache_timestamp = datetime.now()
    
    def get_devices(self, refresh: bool = False, quick_scan: bool = True) -> List[Dict[str, Any]]:
        """
        Get list of available camera devices.
        
        Args:
            refresh: Whether to refresh the device list
            quick_scan: Use quick scanning for faster detection
            
        Returns:
            List of camera device dictionaries
        """
        # Use cache if valid and not forcing refresh
        if not refresh and self._is_cache_valid() and self._devices:
            logger.info("Using cached camera devices")
            return [asdict(device) for device in self._devices]
        
        if refresh or not self._devices:
            self._refresh_devices(quick_scan=quick_scan)
        
        return [asdict(device) for device in self._devices]
    
    def _refresh_devices(self, quick_scan: bool = True) -> None:
        """
        Refresh the list of camera devices.
        
        Args:
            quick_scan: Use quick scanning for faster detection
        """
        try:
            logger.info(f"Refreshing camera devices with {'quick' if quick_scan else 'full'} scan...")
            detected_devices = self.device_detector.detect_cameras(max_devices=4, quick_scan=quick_scan)
            self._devices.clear()
            # Update camera manager's device detector with the same detected devices
            self.camera_manager.device_detector.available_devices = detected_devices
            
            for device_info in detected_devices:
                # Extract resolution from device_info
                width = device_info.get('width', 640)
                height = device_info.get('height', 480)
                fps_detected = device_info.get('fps', 30)
                
                camera_device = CameraDevice(
                    index=device_info['id'],
                    name=device_info['name'],
                    is_available=device_info['available'],
                    resolution=(width, height),
                    fps=int(fps_detected),
                    last_seen=datetime.now()
                )
                self._devices.append(camera_device)
            
            # Update class-level cache
            self._update_cache(self._devices)
            
            logger.info(f"Refreshed camera devices: {len(self._devices)} found")
            
        except Exception as e:
            logger.error(f"Error refreshing camera devices: {e}")
            self._status.error_message = str(e)
    
    def start_stream(self, camera_index: int, resolution: Tuple[int, int] = (640, 480), fps: int = 30, 
                    quick_start: bool = True) -> bool:
        """
        Start streaming from a camera device.
        
        Args:
            camera_index: Index of the camera device
            resolution: Video resolution as (width, height)
            fps: Frames per second
            quick_start: Use optimized startup sequence
            
        Returns:
            True if stream started successfully, False otherwise
        """
        try:
            logger.info(f"Starting {'quick' if quick_start else 'standard'} stream for camera {camera_index}")
            
            # Stop current stream if active
            if self._status.is_active:
                self.stop_stream()
            
            if quick_start:
                # Quick start: Skip device validation and use direct VideoCapture
                self.video_capture = VideoCapture(camera_index, quick_init=True)
                
                # Initialize camera with minimal configuration and shorter timeout
                if not self.video_capture.initialize(timeout_ms=1500):
                    self._status.error_message = f"Failed to initialize camera {camera_index}"
                    return False
                
                # Set basic settings
                self.video_capture.set_resolution(resolution[0], resolution[1])
                self.video_capture.set_fps(fps)
                
                # Start capture immediately
                capture_success = self.video_capture.start_capture()
                if not capture_success:
                    self._status.error_message = "Failed to start video capture"
                    return False
                
            else:
                # Standard start: Full validation and camera manager initialization
                success = self.camera_manager.initialize_camera(camera_index, skip_device_check=False)
                if not success:
                    self._status.error_message = f"Failed to initialize camera {camera_index}"
                    return False
                
                # Configure camera settings
                self.camera_manager.set_resolution(*resolution)
                self.camera_manager.set_fps(fps)
                
                # Start video capture
                self.video_capture = VideoCapture(camera_index, quick_init=False)
                self.video_capture.initialize()
                capture_success = self.video_capture.start_capture()
                if not capture_success:
                    self._status.error_message = "Failed to start video capture"
                    self.camera_manager.release_camera()
                    return False
            
            # Update status
            self._status.is_active = True
            self._status.current_device = camera_index
            self._status.resolution = resolution
            self._status.fps = fps
            self._status.frame_count = 0
            self._status.error_message = None
            
            logger.info(f"Started camera stream: device {camera_index}, {resolution[0]}x{resolution[1]}@{fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera stream: {e}")
            self._status.error_message = str(e)
            return False
    
    def stop_stream(self) -> bool:
        """
        Stop the current camera stream.
        
        Returns:
            True if stream stopped successfully, False otherwise
        """
        try:
            # Stop video capture
            self.video_capture.stop_capture()
            
            # Release camera
            self.camera_manager.release_camera()
            
            # Update status
            self._status.is_active = False
            self._status.current_device = None
            self._status.frame_count = 0
            self._status.last_frame_time = None
            self._status.error_message = None
            self._current_frame = None
            
            logger.info("Camera stream stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping camera stream: {e}")
            self._status.error_message = str(e)
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest frame from the camera.
        
        Returns:
            Latest frame as numpy array, or None if no frame available
        """
        if not self._status.is_active:
            return None
        
        try:
            # read_frame() returns (success, frame) tuple
            success, frame = self.video_capture.read_frame()
            if success and frame is not None:
                self._current_frame = frame
                self._status.frame_count += 1
                self._status.last_frame_time = datetime.now()
                return frame
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            self._status.error_message = str(e)
            return None
    
    def get_frame_as_jpeg(self, quality: int = 85) -> Optional[bytes]:
        """
        Get the latest frame encoded as JPEG.
        
        Args:
            quality: JPEG quality (1-100)
            
        Returns:
            JPEG encoded frame as bytes, or None if no frame available
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        try:
            # Validate frame is a proper numpy array
            if not isinstance(frame, np.ndarray):
                logger.error(f"Invalid frame type: {type(frame)}")
                return None
            
            if frame.size == 0:
                logger.error("Frame is empty")
                return None
            
            # Encode frame as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            else:
                logger.error("Failed to encode frame as JPEG")
                return None
                
        except Exception as e:
            logger.error(f"Error encoding frame as JPEG: {e}")
            logger.error(f"Frame type: {type(frame)}, shape: {getattr(frame, 'shape', 'No shape')}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current camera status.
        
        Returns:
            Dictionary containing camera status information
        """
        status_dict = asdict(self._status)
        
        # Add additional status information
        status_dict['available_devices'] = len(self._devices)
        status_dict['has_frame'] = self._current_frame is not None
        
        if self._current_frame is not None:
            status_dict['frame_shape'] = self._current_frame.shape
        
        return status_dict
    
    def update_settings(self, resolution: Optional[Tuple[int, int]] = None, fps: Optional[int] = None) -> bool:
        """
        Update camera settings while streaming.
        
        Args:
            resolution: New resolution as (width, height)
            fps: New frames per second
            
        Returns:
            True if settings updated successfully, False otherwise
        """
        if not self._status.is_active:
            return False
        
        try:
            if resolution:
                self.camera_manager.set_resolution(*resolution)
                self._status.resolution = resolution
            
            if fps:
                self.camera_manager.set_fps(fps)
                self._status.fps = fps
            
            logger.info(f"Updated camera settings: resolution={self._status.resolution}, fps={self._status.fps}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating camera settings: {e}")
            self._status.error_message = str(e)
            return False
    
    def take_snapshot(self) -> Optional[np.ndarray]:
        """
        Take a snapshot of the current frame.
        
        Returns:
            Snapshot frame as numpy array, or None if no frame available
        """
        if self._current_frame is not None:
            return self._current_frame.copy()
        else:
            return self.get_frame()
    
    def cleanup(self) -> None:
        """Clean up camera resources."""
        try:
            self.stop_stream()
            logger.info("Camera model cleanup completed")
        except Exception as e:
            logger.error(f"Error during camera cleanup: {e}")


# Global camera model instance with pre-initialized cache
camera_model = None

def get_camera_model() -> CameraModel:
    """
    Get the global camera model instance, creating it if necessary.
    This ensures we only have one instance and can cache device detection.
    """
    global camera_model
    if camera_model is None:
        logger.info("Creating global camera model instance...")
        camera_model = CameraModel()
        # Pre-populate cache with quick scan on first access
        try:
            camera_model.get_devices(refresh=True, quick_scan=True)
            logger.info("Pre-populated camera device cache")
        except Exception as e:
            logger.warning(f"Failed to pre-populate camera cache: {e}")
    return camera_model

# Export the getter function
__all__ = ['CameraModel', 'CameraDevice', 'CameraStatus', 'get_camera_model']

# For backward compatibility, create the instance
camera_model = get_camera_model()
