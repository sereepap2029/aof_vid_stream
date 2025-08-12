"""
Camera Device Detection Module

This module handles the detection and enumeration of available camera devices
on the system using OpenCV.
"""

import cv2
from typing import List, Dict, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceDetector:
    """
    Handles detection and enumeration of camera devices.
    """
    
    def __init__(self):
        """Initialize the device detector."""
        self.available_devices: List[Dict] = []
    
    def detect_cameras(self, max_devices: int = 4, quick_scan: bool = True) -> List[Dict]:
        """
        Detect available camera devices on the system.
        
        Args:
            max_devices (int): Maximum number of devices to check (default: 4 for faster scanning)
            quick_scan (bool): If True, use quick detection with minimal testing
            
        Returns:
            List[Dict]: List of available camera devices with their properties
        """
        logger.info(f"Starting {'quick' if quick_scan else 'full'} camera device detection...")
        self.available_devices = []
        
        for device_id in range(max_devices):
            try:
                # Try to open the camera device with minimal timeout
                cap = cv2.VideoCapture(device_id)
                
                # Set shorter timeout for faster detection
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)  # 1 second timeout
                
                if cap.isOpened():
                    if quick_scan:
                        # Quick scan: use default resolution and test basic functionality
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        # Quick frame test - just try to read one frame
                        ret, _ = cap.read()
                        
                        if ret:
                            device_info = {
                                'id': device_id,
                                'name': f'Camera {device_id}',
                                'width': width if width > 0 else 640,
                                'height': height if height > 0 else 480,
                                'fps': fps if fps > 0 else 30,
                                'available': True
                            }
                            self.available_devices.append(device_info)
                            logger.info(f"Quick detected camera device {device_id}: {width}x{height} @ {fps}fps")
                    else:
                        # Full scan with resolution testing (original behavior)
                        test_resolutions = [
                            (1920, 1080),  # 1080p
                            (1280, 720),   # 720p
                            (640, 480),    # VGA (reduced list for speed)
                        ]
                        
                        best_width, best_height = 640, 480  # Default fallback
                        
                        # Test each resolution to find the highest supported one
                        for test_width, test_height in test_resolutions:
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, test_width)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, test_height)
                            
                            # Verify what was actually set
                            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            
                            # If we got close to what we requested, use it
                            if actual_width >= test_width * 0.9 and actual_height >= test_height * 0.9:
                                best_width, best_height = actual_width, actual_height
                                break
                        
                        # Set FPS to 30 (skip multiple FPS testing for speed)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        # Test if we can actually read from the camera
                        ret, frame = cap.read()
                        
                        if ret and frame is not None:
                            device_info = {
                                'id': device_id,
                                'name': f'Camera {device_id}',
                                'width': best_width,
                                'height': best_height,
                                'fps': fps if fps > 0 else 30,
                                'available': True
                            }
                            self.available_devices.append(device_info)
                            logger.info(f"Full detected camera device {device_id}: {best_width}x{best_height} @ {fps}fps")
                    
                    cap.release()
                    
            except Exception as e:
                logger.debug(f"Device {device_id} not available: {e}")
                continue
        
        logger.info(f"Detection complete. Found {len(self.available_devices)} camera devices.")
        return self.available_devices
    
    def get_device_info(self, device_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific camera device.
        
        Args:
            device_id (int): The camera device ID
            
        Returns:
            Optional[Dict]: Device information or None if not found
        """
        for device in self.available_devices:
            if device['id'] == device_id:
                return device
        return None
    
    def get_available_devices(self) -> List[Dict]:
        """
        Get list of all available camera devices.
        
        Returns:
            List[Dict]: List of available camera devices
        """
        return self.available_devices
    
    def is_device_available(self, device_id: int) -> bool:
        """
        Check if a specific camera device is available.
        
        Args:
            device_id (int): The camera device ID
            
        Returns:
            bool: True if device is available, False otherwise
        """
        return any(device['id'] == device_id for device in self.available_devices)
    
    def get_default_device(self) -> Optional[Dict]:
        """
        Get the default camera device (usually the first available one).
        
        Returns:
            Optional[Dict]: Default device information or None if no devices available
        """
        if self.available_devices:
            return self.available_devices[0]
        return None
    
    def get_supported_resolutions(self, device_id: int) -> List[Dict]:
        """
        Get all supported resolutions for a specific camera device.
        
        Args:
            device_id (int): The camera device ID
            
        Returns:
            List[Dict]: List of supported resolutions with format {'width': int, 'height': int, 'fps': float}
        """
        supported_resolutions = []
        
        try:
            cap = cv2.VideoCapture(device_id)
            if not cap.isOpened():
                return supported_resolutions
            
            # Common resolutions to test
            test_resolutions = [
                #(3840, 2160),  # 4K
                #(2560, 1440),  # 1440p
                (1920, 1080),  # 1080p
                (1280, 720),   # 720p
                (960, 540),    # qHD
                (800, 600),    # SVGA
                (640, 480),    # VGA
                (320, 240),    # QVGA
            ]
            
            for width, height in test_resolutions:
                # Try to set the resolution
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Check what was actually set
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Test if we can capture a frame at this resolution
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Test different FPS values
                    for test_fps in [60, 30, 15]:
                        cap.set(cv2.CAP_PROP_FPS, test_fps)
                        actual_fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        resolution_info = {
                            'width': actual_width,
                            'height': actual_height,
                            'fps': actual_fps
                        }
                        
                        # Avoid duplicates
                        if resolution_info not in supported_resolutions:
                            supported_resolutions.append(resolution_info)
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Error getting supported resolutions for device {device_id}: {e}")
        
        return supported_resolutions


def test_device_detector():
    """Test function for the DeviceDetector class."""
    detector = DeviceDetector()
    devices = detector.detect_cameras()
    
    print(f"Found {len(devices)} camera devices:")
    for device in devices:
        print(f"  Device {device['id']}: {device['name']} - {device['width']}x{device['height']} @ {device['fps']}fps")
        
        # Show supported resolutions
        print("  Supported resolutions:")
        resolutions = detector.get_supported_resolutions(device['id'])
        for res in resolutions[:5]:  # Show first 5 resolutions
            print(f"    {res['width']}x{res['height']} @ {res['fps']}fps")
        if len(resolutions) > 5:
            print(f"    ... and {len(resolutions) - 5} more")
    
    if devices:
        default_device = detector.get_default_device()
        print(f"Default device: {default_device}")


if __name__ == "__main__":
    test_device_detector()
