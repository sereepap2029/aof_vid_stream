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
from src.camera.hardware_encoder import get_hardware_encoder, cleanup_hardware_encoder

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
        
        # Hardware encoding support
        self._hardware_encoder = None
        self._use_hardware_encoding = True  # Enable by default
        self._selected_codec = 'auto'  # Default codec selection
        
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
                    quick_start: bool = True, codec: str = '') -> bool:
        """
        Start streaming from a camera device.
        
        Args:
            camera_index: Index of the camera device
            resolution: Video resolution as (width, height)
            fps: Frames per second
            quick_start: Use optimized startup sequence
            codec: Video codec to use for encoding (empty string for auto-selection)
            
        Returns:
            True if stream started successfully, False otherwise
        """
        try:
            logger.info(f"Starting {'quick' if quick_start else 'standard'} stream for camera {camera_index} with codec: {codec or 'auto'}")
            
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
            
            # Store selected codec for hardware encoding
            self._selected_codec = codec or 'auto'
            
            # Initialize hardware encoder if hardware encoding is enabled
            if self._use_hardware_encoding:
                try:
                    self.reinitialize_hardware_encoder(resolution[0], resolution[1], fps, self._selected_codec)
                    logger.info(f"Initialized hardware encoder with codec: {self._selected_codec}")
                except Exception as e:
                    logger.warning(f"Failed to initialize hardware encoder: {e}, falling back to software")
            
            logger.info(f"Started camera stream: device {camera_index}, {resolution[0]}x{resolution[1]}@{fps}fps, codec: {self._selected_codec}")
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
    
    def get_frame_as_jpeg(self, quality: int = 85, use_hardware: bool = True, codec: str = None) -> Optional[bytes]:
        """
        Get the latest frame encoded using the specified codec with hardware acceleration when available.
        
        Args:
            quality: Encoding quality (1-100)
            use_hardware: Whether to use hardware encoding if available
            codec: Codec to use (None for auto, 'H264', 'H265', 'VP8', 'VP9', 'MJPG', 'JPEG')
            
        Returns:
            Encoded frame as bytes, or None if no frame available
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        # Use selected codec if none specified
        if codec is None:
            codec = getattr(self, '_selected_codec', 'auto')
        
        try:
            # Validate frame is a proper numpy array
            if not isinstance(frame, np.ndarray):
                logger.error(f"Invalid frame type: {type(frame)}")
                return None
            
            if frame.size == 0:
                logger.error("Frame is empty")
                return None
            
            # Use hardware encoding if enabled and available
            if use_hardware and self._use_hardware_encoding:
                return self._encode_frame_hardware(frame, quality, codec)
            else:
                return self._encode_frame_software(frame, quality)
            if use_hardware and self._use_hardware_encoding:
                return self._encode_frame_hardware(frame, quality)
            else:
                return self._encode_frame_software(frame, quality)
                
        except Exception as e:
            logger.error(f"Error encoding frame as JPEG: {e}")
            logger.error(f"Frame type: {type(frame)}, shape: {getattr(frame, 'shape', 'No shape')}")
            # Fallback to software encoding
            return self._encode_frame_software(frame, quality)
    
    def _encode_frame_hardware(self, frame: np.ndarray, quality: int, codec: str = 'auto') -> Optional[bytes]:
        """Encode frame using hardware acceleration."""
        try:
            # Initialize hardware encoder if needed
            if self._hardware_encoder is None:
                height, width = frame.shape[:2]
                fps = self._status.fps or 30
                self._hardware_encoder = get_hardware_encoder(width, height, fps, codec)
            
            # Reinitialize if codec changed
            elif hasattr(self._hardware_encoder, 'requested_codec') and self._hardware_encoder.requested_codec != codec:
                height, width = frame.shape[:2]
                fps = self._status.fps or 30
                self._hardware_encoder.cleanup()
                self._hardware_encoder = get_hardware_encoder(width, height, fps, codec)
            
            # Use hardware encoder
            encoded_data = self._hardware_encoder.encode_frame(frame, quality)
            
            if encoded_data is not None:
                return encoded_data
            else:
                logger.warning("Hardware encoding failed, falling back to software")
                return self._encode_frame_software(frame, quality)
                
        except Exception as e:
            logger.error(f"Hardware encoding error: {e}")
            return self._encode_frame_software(frame, quality)
    
    def _encode_frame_software(self, frame: np.ndarray, quality: int) -> Optional[bytes]:
        """Encode frame using software (CPU) encoding."""
        try:
            # Standard JPEG encoding
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, encoded_frame = cv2.imencode('.jpg', frame, encode_params)
            
            if success:
                return encoded_frame.tobytes()
            else:
                logger.error("Failed to encode frame as JPEG")
                return None
                
        except Exception as e:
            logger.error(f"Software encoding error: {e}")
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
    
    def set_hardware_encoding(self, enabled: bool) -> bool:
        """
        Enable or disable hardware encoding.
        
        Args:
            enabled: Whether to enable hardware encoding
            
        Returns:
            bool: True if setting was changed successfully
        """
        try:
            self._use_hardware_encoding = enabled
            
            if not enabled and self._hardware_encoder:
                # Clean up hardware encoder if disabling
                self._hardware_encoder.cleanup()
                self._hardware_encoder = None
            
            logger.info(f"Hardware encoding {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting hardware encoding: {e}")
            return False
    
    def is_hardware_encoding_enabled(self) -> bool:
        """Check if hardware encoding is enabled."""
        return self._use_hardware_encoding
    
    def get_encoding_performance(self) -> Dict[str, Any]:
        """
        Get hardware encoding performance statistics.
        
        Returns:
            Dictionary containing encoding performance data
        """
        if self._hardware_encoder:
            return self._hardware_encoder.get_performance_stats()
        else:
            return {
                'encoding_method': 'Software (JPEG)',
                'frames_encoded': 0,
                'avg_encode_time': 0,
                'fps_capability': 0,
                'hardware_available': {
                    'nvenc': False,
                    'quicksync': False,
                    'vaapi': False,
                    'cuda': False
                }
            }
    
    def reinitialize_hardware_encoder(self, width: int = None, height: int = None, fps: int = None, codec: str = 'auto'):
        """
        Reinitialize hardware encoder with new parameters.
        
        Args:
            width: Video width (uses current if None)
            height: Video height (uses current if None)
            fps: Frames per second (uses current if None)
            codec: Codec to use ('auto', 'H264', 'H265', 'VP8', 'VP9', 'MJPG', 'JPEG')
        """
        try:
            if self._hardware_encoder:
                self._hardware_encoder.cleanup()
                self._hardware_encoder = None
            
            if self._use_hardware_encoding:
                # Use provided dimensions or current status
                w = width or self._status.resolution[0]
                h = height or self._status.resolution[1] 
                f = fps or self._status.fps or 30
                
                self._hardware_encoder = get_hardware_encoder(w, h, f, codec)
                logger.info(f"Hardware encoder reinitialized: {w}x{h}@{f}fps with codec {codec}")
            
        except Exception as e:
            logger.error(f"Error reinitializing hardware encoder: {e}")
    
    def get_available_codecs(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get list of available codecs on the system.
        
        Returns:
            Dictionary with codec names and their variants
        """
        try:
            from src.camera.hardware_encoder import get_available_codecs
            return get_available_codecs()
        except Exception as e:
            logger.error(f"Error getting available codecs: {e}")
            return {'JPEG': [{'fourcc': 'JPEG', 'format': 'jpg', 'hardware_support': False}]}
    
    def set_codec(self, codec: str) -> bool:
        """
        Set the codec for hardware encoding.
        
        Args:
            codec: Codec name ('auto', 'H264', 'H265', 'VP8', 'VP9', 'MJPG', 'JPEG')
            
        Returns:
            bool: True if codec was set successfully
        """
        try:
            # Reinitialize encoder with new codec
            self.reinitialize_hardware_encoder(codec=codec)
            logger.info(f"Codec set to: {codec}")
            return True
        except Exception as e:
            logger.error(f"Error setting codec: {e}")
            return False
    
    def get_current_codec_info(self) -> Dict[str, Any]:
        """
        Get information about the currently selected codec.
        
        Returns:
            Dictionary with current codec information
        """
        if self._hardware_encoder and hasattr(self._hardware_encoder, 'current_codec_info'):
            return self._hardware_encoder.current_codec_info
        else:
            return {
                'codec': 'JPEG',
                'fourcc': 'JPEG',
                'format': 'jpg',
                'hardware_support': False
            }

    def cleanup(self) -> None:
        """Clean up camera resources."""
        try:
            self.stop_stream()
            
            # Clean up hardware encoder
            if self._hardware_encoder:
                self._hardware_encoder.cleanup()
                self._hardware_encoder = None
            
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
