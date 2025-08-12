"""
Video Capture Module

This module handles video capture from camera devices using OpenCV.
Provides functionality for capturing frames, managing video streams,
and handling camera configurations.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
import logging
import threading
import time
from .device_detector import DeviceDetector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoCapture:
    """
    Handles video capture from a camera device.
    """
    
    def __init__(self, device_id: int = 0):
        """
        Initialize video capture for a specific device.
        
        Args:
            device_id (int): Camera device ID (default: 0)
        """
        self.device_id = device_id
        self.device_detector = DeviceDetector()
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.current_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.capture_thread: Optional[threading.Thread] = None
        
        # Get supported resolutions for this device
        self.resolutions = self.device_detector.get_supported_resolutions(self.device_id)
        
        # Set default settings based on supported resolutions
        if self.resolutions:
            # Use the highest supported resolution (first in the list from our detector)
            best_resolution = self.resolutions[0]
            self.width = best_resolution['width']
            self.height = best_resolution['height']
            self.fps = best_resolution['fps']
            logger.info(f"Using best supported resolution: {self.width}x{self.height} @ {self.fps}fps")
            
            # Log available resolutions for debugging
            logger.info(f"Found {len(self.resolutions)} supported resolutions")
            for i, res in enumerate(self.resolutions[:3]):  # Show first 3 resolutions
                logger.info(f"  Resolution {i+1}: {res['width']}x{res['height']} @ {res['fps']}fps")
        else:
            # Fallback to standard defaults if no resolutions detected
            self.width = 640
            self.height = 480
            self.fps = 30
            logger.warning(f"No supported resolutions found for device {self.device_id}, using defaults: {self.width}x{self.height} @ {self.fps}fps")
        
    def initialize(self) -> bool:
        """
        Initialize the camera device.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info(f"Initializing camera device {self.device_id}")
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera device {self.device_id}")
                return False
            
            # Set default properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set camera resolution.
        
        Args:
            width (int): Frame width
            height (int): Frame height
            
        Returns:
            bool: True if resolution set successfully, False otherwise
        """
        if self.cap is None:
            logger.error("Camera not initialized")
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Verify the resolution was set
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.width = actual_width
            self.height = actual_height
            
            logger.info(f"Resolution set to {actual_width}x{actual_height}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting resolution: {e}")
            return False
    
    def set_fps(self, fps: float) -> bool:
        """
        Set camera frame rate.
        
        Args:
            fps (float): Frames per second
            
        Returns:
            bool: True if FPS set successfully, False otherwise
        """
        if self.cap is None:
            logger.error("Camera not initialized")
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = actual_fps
            
            logger.info(f"FPS set to {actual_fps}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting FPS: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a single frame from the camera.
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame)
        """
        if self.cap is None:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            return ret, frame
            
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return False, None
    
    def start_capture(self) -> bool:
        """
        Start continuous frame capture in a separate thread.
        
        Returns:
            bool: True if capture started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Capture already running")
            return True
        
        if self.cap is None:
            logger.error("Camera not initialized")
            return False
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        logger.info("Started continuous frame capture")
        return True
    
    def stop_capture(self):
        """Stop continuous frame capture."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        
        logger.info("Stopped continuous frame capture")
    
    def _capture_loop(self):
        """Internal method for continuous frame capture."""
        while self.is_running:
            ret, frame = self.read_frame()
            
            if ret and frame is not None:
                with self.frame_lock:
                    self.current_frame = frame.copy()
            else:
                logger.warning("Failed to read frame")
            
            time.sleep(1.0 / self.fps)  # Control frame rate
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame from continuous capture.
        
        Returns:
            Optional[np.ndarray]: Current frame or None if not available
        """
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
    
    def get_camera_properties(self) -> Dict[str, Any]:
        """
        Get current camera properties.
        
        Returns:
            Dict[str, Any]: Dictionary of camera properties
        """
        if self.cap is None:
            return {}
        
        properties = {
            'device_id': self.device_id,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'hue': self.cap.get(cv2.CAP_PROP_HUE),
            'is_running': self.is_running
        }
        
        return properties
    
    def get_supported_resolutions(self) -> List[Dict[str, Any]]:
        """
        Get all supported resolutions for this camera device.
        
        Returns:
            List[Dict[str, Any]]: List of supported resolutions
        """
        return self.resolutions
    
    def set_best_resolution(self) -> bool:
        """
        Set the camera to its best supported resolution.
        
        Returns:
            bool: True if resolution set successfully, False otherwise
        """
        if not self.resolutions:
            logger.warning("No supported resolutions available")
            return False
        
        best_resolution = self.resolutions[0]
        return self.set_resolution(best_resolution['width'], best_resolution['height'])
    
    def release(self):
        """Release the camera device and clean up resources."""
        self.stop_capture()
        
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        logger.info(f"Released camera device {self.device_id}")
    
    def __del__(self):
        """Destructor to ensure proper cleanup."""
        self.release()


def test_video_capture():
    """Test function for the VideoCapture class."""
    capture = VideoCapture(device_id=0)
    
    if not capture.initialize():
        print("Failed to initialize camera")
        return
    
    print("Camera properties:", capture.get_camera_properties())
    
    # Test single frame capture
    ret, frame = capture.read_frame()
    if ret:
        print(f"Single frame captured: {frame.shape}")
    
    # Test continuous capture
    capture.start_capture()
    time.sleep(2)  # Capture for 2 seconds
    
    current_frame = capture.get_current_frame()
    if current_frame is not None:
        print(f"Continuous frame captured: {current_frame.shape}")
    
    capture.stop_capture()
    capture.release()


if __name__ == "__main__":
    test_video_capture()
