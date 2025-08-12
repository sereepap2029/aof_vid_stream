# AOF Video Stream

A web application that captures video from camera devices and streams it to a localhost web interface.

## 🎯 Project Overview

This project creates a real-time video streaming application that:
- Detects and manages camera devices
- Captures video frames from connected cameras
- Streams video to a web browser interface
- Provides camera controls and settings

## 📋 Current Status

### ✅ Phase 1: Camera Integration (COMPLETED)
- [x] Camera device detection and enumeration
- [x] Video capture functionality with OpenCV
- [x] Multi-camera device support
- [x] Camera settings management (resolution, FPS)
- [x] Continuous video capture with threading
- [x] Comprehensive error handling and logging

### 🚧 Phase 2: Web Interface (NEXT)
- [ ] Basic HTML interface
- [ ] Video display component
- [ ] Camera selection controls
- [ ] CSS styling

### 📋 Phase 3: Streaming Implementation (PLANNED)
- [ ] Video streaming server
- [ ] Real-time video transmission
- [ ] Performance optimization
- [ ] Error handling and reconnection

### 🎨 Phase 4: Enhancement (PLANNED)
- [ ] Recording capabilities
- [ ] Stream quality controls
- [ ] Advanced multi-camera support
- [ ] Performance monitoring

## 🏗️ Architecture

```
Camera Device → Python Backend → Web Interface
     ↓               ↓              ↓
OpenCV Capture → Flask Server → HTML5 Video
```

### Project Structure
```
aof_vid_stream/
├── src/
│   ├── camera/              # ✅ Camera handling modules
│   │   ├── __init__.py
│   │   ├── camera_manager.py    # High-level camera management
│   │   ├── device_detector.py   # Camera device detection
│   │   └── video_capture.py     # Video capture handling
│   ├── streaming/           # 🚧 Video streaming logic (coming next)
│   ├── webapp/              # 🚧 Web application components (coming next)
│   └── utils/               # Utility functions
├── static/                  # 🚧 Static web assets (CSS, JS, images)
├── templates/               # 🚧 HTML templates
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── test_phase1.py          # ✅ Phase 1 test script
├── GUIDELINES.md           # Development guidelines
├── ARCHITECTURE.md         # Project architecture documentation
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7+ (uses system Python installation)
- Camera device (webcam, USB camera, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aof_vid_stream
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test camera functionality**
   ```bash
   python tests\test_phase1.py
   ```

### Dependencies
- `opencv-python` - Camera access and video processing
- `numpy` - Array operations for image data
- `flask` - Web framework (for upcoming phases)
- `flask-socketio` - Real-time communication (for upcoming phases)
- `python-socketio` - WebSocket support (for upcoming phases)

## 🧪 Testing

### Phase 1 Testing
Run the camera integration test:
```bash
python tests\test_phase1.py
```

This test verifies:
- Camera device detection
- Video capture functionality
- Continuous frame capture
- Camera settings management
- Multiple camera handling (if available)
- Resource cleanup

## 🎥 Camera Features

### Implemented Features
- **Device Detection**: Automatically finds available camera devices
- **Video Capture**: Captures frames from camera devices
- **Resolution Control**: Set custom resolution (width x height)
- **FPS Control**: Configure frame rate
- **Continuous Capture**: Background thread for continuous video capture
- **Multi-Camera Support**: Handle multiple camera devices
- **Error Handling**: Graceful error handling with logging

### Usage Example
```python
from src.camera import CameraManager

# Initialize camera manager
manager = CameraManager()

# Scan for available cameras
devices = manager.scan_devices()
print(f"Found {len(devices)} cameras")

# Initialize default camera
if manager.initialize_camera():
    # Start continuous capture
    manager.start_capture()
    
    # Get current frame
    frame = manager.get_current_frame()
    
    # Stop and cleanup
    manager.stop_capture()
    manager.release_camera()
```

## 📊 Current Capabilities

- ✅ **Camera Detection**: Enumerates all available camera devices
- ✅ **Video Capture**: Real-time frame capture with OpenCV
- ✅ **Threading**: Non-blocking continuous capture
- ✅ **Configuration**: Adjustable resolution and frame rate
- ✅ **Error Handling**: Comprehensive error management
- ✅ **Logging**: Detailed logging for debugging
- ✅ **Resource Management**: Proper cleanup and resource release

## 🔧 Configuration

The application uses system Python installation for simplicity. Configuration options include:
- Camera device selection
- Video resolution settings
- Frame rate control
- Logging levels

## 📝 Development Guidelines

Please refer to `GUIDELINES.md` for:
- Code standards and conventions
- Development workflow
- Testing requirements
- Documentation standards

## 🏛️ Architecture Documentation

See `ARCHITECTURE.md` for detailed information about:
- System architecture overview
- Component relationships
- Data flow patterns
- Technology stack details

## 🤝 Contributing

1. Follow the development guidelines in `GUIDELINES.md`
2. Update `ARCHITECTURE.md` when making architectural changes
3. Write tests for new features
4. Update documentation as needed

## 📈 Next Steps

1. **Phase 2**: Create web interface with HTML5 video display
2. **Phase 3**: Implement real-time streaming with WebSockets
3. **Phase 4**: Add advanced features and optimizations

## 🐛 Known Issues

- OpenCV may show some warning messages about camera indices - these are normal
- FPS values may not be exact due to camera hardware limitations

## 📄 License

[Add license information here]

---

**Last Updated**: August 12, 2025  
**Current Phase**: Phase 1 Complete ✅ | Phase 2 Starting 🚧
