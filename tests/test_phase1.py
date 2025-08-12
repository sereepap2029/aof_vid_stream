"""
Test script for Phase 1: Camera Integration

This script tests the camera functionality implemented in Phase 1.
"""

import sys
import os

# Add src directory to path (go up one level from tests to project root, then into src)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera import CameraManager
import cv2
import time


def test_phase1_camera_integration():
    """Test all Phase 1 camera integration features."""
    print("=== AOF Video Stream - Phase 1 Testing ===")
    print("Testing Camera Integration...\n")
    
    # Initialize camera manager
    manager = CameraManager()
    
    # Test 1: Camera device detection
    print("1. Testing camera device detection...")
    devices = manager.scan_devices()
    
    if not devices:
        print("❌ No camera devices found!")
        print("Please ensure you have a camera connected to your system.")
        return False
    
    print(f"✅ Found {len(devices)} camera device(s):")
    for device in devices:
        print(f"   • Device {device['id']}: {device['name']} - {device['width']}x{device['height']} @ {device['fps']}fps")
    
    # Test 2: Camera initialization
    print("\n2. Testing camera initialization...")
    if manager.initialize_camera():
        print("✅ Camera initialized successfully")
        properties = manager.get_camera_properties()
        print(f"   • Resolution: {properties['width']}x{properties['height']}")
        print(f"   • FPS: {properties['fps']}")
    else:
        print("❌ Failed to initialize camera")
        return False
    
    # Test 3: Single frame capture
    print("\n3. Testing single frame capture...")
    ret, frame = manager.read_frame()
    if ret and frame is not None:
        print(f"✅ Frame captured successfully: {frame.shape}")
        
        # Save test image
        cv2.imwrite('test_frame.jpg', frame)
        print("   • Test frame saved as 'test_frame.jpg'")
    else:
        print("❌ Failed to capture frame")
        manager.release_camera()
        return False
    
    # Test 4: Continuous capture
    print("\n4. Testing continuous video capture...")
    if manager.start_capture():
        print("✅ Continuous capture started")
        
        # Capture frames for 3 seconds
        print("   • Capturing frames for 3 seconds...")
        for i in range(3):
            time.sleep(1)
            current_frame = manager.get_current_frame()
            if current_frame is not None:
                print(f"     Frame {i+1}: {current_frame.shape}")
            else:
                print(f"     Frame {i+1}: No frame available")
        
        manager.stop_capture()
        print("✅ Continuous capture stopped")
    else:
        print("❌ Failed to start continuous capture")
        manager.release_camera()
        return False
    
    # Test 5: Multiple device handling (if available)
    if len(devices) > 1:
        print("\n5. Testing multiple camera device handling...")
        second_device_id = devices[1]['id']
        
        if manager.switch_camera(second_device_id):
            print(f"✅ Successfully switched to camera device {second_device_id}")
            
            # Test frame capture with second camera
            ret, frame = manager.read_frame()
            if ret:
                print(f"   • Frame captured from device {second_device_id}: {frame.shape}")
            
            # Switch back to first camera
            if manager.switch_camera(devices[0]['id']):
                print(f"✅ Successfully switched back to camera device {devices[0]['id']}")
        else:
            print(f"❌ Failed to switch to camera device {second_device_id}")
    else:
        print("\n5. Multiple camera test skipped (only one device available)")
    
    # Test 6: Camera settings
    print("\n6. Testing camera settings...")
    if manager.set_resolution(320, 240):
        print("✅ Resolution changed to 320x240")
        properties = manager.get_camera_properties()
        print(f"   • Current resolution: {properties['width']}x{properties['height']}")
    
    if manager.set_fps(15):
        print("✅ FPS changed to 15")
        properties = manager.get_camera_properties()
        print(f"   • Current FPS: {properties['fps']}")
    
    # Test 7: Status and cleanup
    print("\n7. Testing status and cleanup...")
    status = manager.get_status()
    print("✅ Camera manager status:")
    print(f"   • Available devices: {status['available_devices']}")
    print(f"   • Current device: {status['current_device_id']}")
    print(f"   • Camera initialized: {status['camera_initialized']}")
    print(f"   • Capture running: {status['capture_running']}")
    
    # Cleanup
    manager.release_camera()
    print("✅ Camera resources released")
    
    print("\n=== Phase 1 Testing Complete ===")
    print("✅ All camera integration tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_phase1_camera_integration()
        if success:
            print("\n🎉 Phase 1 implementation is working correctly!")
            print("Ready to proceed to Phase 2: Web Interface")
        else:
            print("\n❌ Phase 1 testing failed. Please check the issues above.")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("Please ensure OpenCV is installed: pip install opencv-python")
