"""
Camera Manager Module

This module provides a high-level interface for managing camera operations,
including device detection, video capture, and camera switching.
"""

from typing import List, Dict, Optional
import logging
from .device_detector import DeviceDetector
from .video_capture import VideoCapture

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraManager:
    """
    High-level camera management class that coordinates device detection
    and video capture operations.
    """
    
    def __init__(self):
        """Initialize the camera manager."""
        self.device_detector = DeviceDetector()
        self.current_capture: Optional[VideoCapture] = None
        self.available_devices: List[Dict] = []
        self.current_device_id: Optional[int] = None
        
    def scan_devices(self) -> List[Dict]:
        """
        Scan for available camera devices.
        
        Returns:
            List[Dict]: List of available camera devices
        """
        logger.info("Scanning for camera devices...")
        self.available_devices = self.device_detector.detect_cameras()
        return self.available_devices
    
    def get_available_devices(self) -> List[Dict]:
        """
        Get list of available camera devices.
        
        Returns:
            List[Dict]: List of available camera devices
        """
        return self.available_devices
    
    def initialize_camera(self, device_id: Optional[int] = None) -> bool:
        """
        Initialize a camera device for video capture.
        
        Args:
            device_id (Optional[int]): Device ID to initialize. If None, uses default device.
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        # If no device specified, try to use default device
        if device_id is None:
            default_device = self.device_detector.get_default_device()
            if default_device is None:
                logger.error("No camera devices available")
                return False
            device_id = default_device['id']
        
        # Check if device is available
        if not self.device_detector.is_device_available(device_id):
            logger.error(f"Camera device {device_id} is not available")
            return False
        
        # Release current capture if any
        if self.current_capture is not None:
            self.release_camera()
        
        # Initialize new capture
        try:
            self.current_capture = VideoCapture(device_id)
            if self.current_capture.initialize():
                self.current_device_id = device_id
                logger.info(f"Successfully initialized camera device {device_id}")
                return True
            else:
                logger.error(f"Failed to initialize camera device {device_id}")
                self.current_capture = None
                return False
                
        except Exception as e:
            logger.error(f"Error initializing camera device {device_id}: {e}")
            self.current_capture = None
            return False
    
    def switch_camera(self, device_id: int) -> bool:
        """
        Switch to a different camera device.
        
        Args:
            device_id (int): The device ID to switch to
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        logger.info(f"Switching to camera device {device_id}")
        return self.initialize_camera(device_id)
    
    def start_capture(self) -> bool:
        """
        Start video capture from the current camera.
        
        Returns:
            bool: True if capture started successfully, False otherwise
        """
        if self.current_capture is None:
            logger.error("No camera initialized")
            return False
        
        return self.current_capture.start_capture()
    
    def stop_capture(self):
        """Stop video capture."""
        if self.current_capture is not None:
            self.current_capture.stop_capture()
    
    def get_current_frame(self):
        """
        Get the current frame from video capture.
        
        Returns:
            Optional[np.ndarray]: Current frame or None if not available
        """
        if self.current_capture is None:
            return None
        
        return self.current_capture.get_current_frame()
    
    def read_frame(self):
        """
        Read a single frame from the camera.
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame)
        """
        if self.current_capture is None:
            return False, None
        
        return self.current_capture.read_frame()
    
    def get_camera_properties(self) -> Dict:
        """
        Get properties of the current camera.
        
        Returns:
            Dict: Camera properties or empty dict if no camera active
        """
        if self.current_capture is None:
            return {}
        
        return self.current_capture.get_camera_properties()
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set camera resolution.
        
        Args:
            width (int): Frame width
            height (int): Frame height
            
        Returns:
            bool: True if resolution set successfully, False otherwise
        """
        if self.current_capture is None:
            logger.error("No camera initialized")
            return False
        
        return self.current_capture.set_resolution(width, height)
    
    def set_fps(self, fps: float) -> bool:
        """
        Set camera frame rate.
        
        Args:
            fps (float): Frames per second
            
        Returns:
            bool: True if FPS set successfully, False otherwise
        """
        if self.current_capture is None:
            logger.error("No camera initialized")
            return False
        
        return self.current_capture.set_fps(fps)
    
    def release_camera(self):
        """Release the current camera and clean up resources."""
        if self.current_capture is not None:
            self.current_capture.release()
            self.current_capture = None
            self.current_device_id = None
            logger.info("Released camera")
    
    def get_status(self) -> Dict:
        """
        Get current status of the camera manager.
        
        Returns:
            Dict: Status information
        """
        status = {
            'available_devices': len(self.available_devices),
            'current_device_id': self.current_device_id,
            'camera_initialized': self.current_capture is not None,
            'capture_running': False
        }
        
        if self.current_capture is not None:
            status['capture_running'] = self.current_capture.is_running
            status['camera_properties'] = self.get_camera_properties()
        
        return status
    
    def __del__(self):
        """Destructor to ensure proper cleanup."""
        self.release_camera()


def test_camera_manager():
    """Test function for the CameraManager class."""
    manager = CameraManager()
    
    # Scan for devices
    devices = manager.scan_devices()
    print(f"Found {len(devices)} camera devices:")
    for device in devices:
        print(f"  Device {device['id']}: {device['name']} - {device['width']}x{device['height']}")
    
    if not devices:
        print("No camera devices found")
        return
    
    # Initialize first camera
    if manager.initialize_camera():
        print("Camera initialized successfully")
        print("Camera properties:", manager.get_camera_properties())
        
        # Test frame capture
        ret, frame = manager.read_frame()
        if ret:
            print(f"Frame captured: {frame.shape}")
        
        # Test continuous capture
        manager.start_capture()
        import time
        time.sleep(1)
        
        current_frame = manager.get_current_frame()
        if current_frame is not None:
            print(f"Continuous frame: {current_frame.shape}")
        
        manager.stop_capture()
        
        print("Status:", manager.get_status())
        
        manager.release_camera()
    else:
        print("Failed to initialize camera")


if __name__ == "__main__":
    test_camera_manager()
