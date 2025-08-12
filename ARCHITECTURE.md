# AOF Video Stream - Project Architecture

## System Architecture Overview

This document outlines the architecture for the AOF Video Stream project, which captures video from camera devices and displays it in a web application running on localhost.

## Implementation Status

### ✅ Phase 1: Camera Integration (COMPLETED)
- Camera device detection and enumeration
- Video capture with OpenCV
- Multi-camera device support
- Configurable resolution and FPS settings
- Continuous video capture with threading
- Comprehensive error handling and logging
- Resource management and cleanup

### 📋 Phase 2: Web Interface (NEXT)
- HTML5 web interface design
- Video display component
- Camera selection controls
- CSS styling and responsive design

### 🚧 Phase 3: Streaming Implementation (PLANNED)
- Real-time video streaming server
- WebSocket communication
- Frame encoding optimization
- Performance tuning

### 🎨 Phase 4: Enhancement (FUTURE)
- Recording capabilities
- Advanced camera controls
- Multi-stream support
- Performance monitoring

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Camera        │    │   Backend       │    │   Frontend      │
│   Device        │───▶│   Server        │───▶│   Web App       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### 1. Camera Layer ✅ IMPLEMENTED
**Location**: `src/camera/`

```
Camera Layer
├── __init__.py            # Package initialization and exports
├── camera_manager.py      # Main camera management ✅ COMPLETED
├── device_detector.py     # Camera device detection ✅ COMPLETED
├── video_capture.py       # Video capture handling ✅ COMPLETED
└── frame_processor.py     # Frame processing utilities (planned)
```

**Responsibilities**:
- Detect available camera devices ✅ IMPLEMENTED
- Initialize and manage camera connections ✅ IMPLEMENTED
- Capture video frames ✅ IMPLEMENTED
- Handle camera-specific configurations ✅ IMPLEMENTED
- Process raw video frames (basic implementation)

**Key Classes**:
- `CameraManager`: Central management of camera operations ✅ IMPLEMENTED
  - Device scanning and initialization
  - Camera switching and resource management
  - Status monitoring and cleanup
- `DeviceDetector`: Enumerate and validate camera devices ✅ IMPLEMENTED
  - Automatic camera detection (up to 10 devices)
  - Device capability assessment
  - Hardware compatibility checking
- `VideoCapture`: Handle video frame capture ✅ IMPLEMENTED
  - Real-time frame capture with threading
  - Configurable resolution and FPS
  - Continuous capture with buffer management
- `FrameProcessor`: Process and optimize video frames (planned for Phase 3)

### 2. Streaming Layer 🚧 PLANNED FOR PHASE 3
**Location**: `src/streaming/`

```
Streaming Layer
├── __init__.py            # Package initialization
├── stream_server.py       # Video streaming server (planned)
├── frame_encoder.py       # Frame encoding/compression (planned)
├── websocket_handler.py   # WebSocket communication (planned)
└── stream_manager.py      # Stream session management (planned)
```

**Responsibilities**:
- Encode video frames for web transmission
- Manage streaming sessions
- Handle WebSocket connections
- Optimize streaming performance
- Buffer management

**Key Classes**:
- `StreamServer`: Main streaming server
- `FrameEncoder`: Video frame encoding
- `WebSocketHandler`: Real-time communication
- `StreamManager`: Session and connection management

### 3. Web Application Layer 📋 NEXT - PHASE 2
**Location**: `src/webapp/`

```
Web Application Layer
├── __init__.py            # Package initialization
├── app.py                 # Main Flask/FastAPI application (planned)
├── routes.py              # Web routes and endpoints (planned)
├── api_handlers.py        # API request handlers (planned)
└── middleware.py          # Request/response middleware (planned)
```

**Responsibilities**:
- Serve web interface
- Handle HTTP requests
- Provide REST API endpoints
- Manage user sessions
- Route handling

**Key Components**:
- `app.py`: Application entry point and configuration
- `routes.py`: URL routing and view functions
- `api_handlers.py`: API logic and data processing
- `middleware.py`: Request preprocessing and response formatting

### 4. Frontend Layer 📋 NEXT - PHASE 2
**Location**: `static/` and `templates/`

```
Frontend Layer
├── templates/              # HTML templates (planned)
│   ├── base.html          # Base template
│   ├── index.html         # Main page template
│   └── camera.html        # Camera interface template
└── static/                # Static web assets (planned)
    ├── css/
    │   └── style.css      # Application styles
    ├── js/
    │   ├── camera.js      # Camera control logic
    │   ├── streaming.js   # Video streaming client
    │   └── main.js        # Main application logic
    └── images/            # Static images and icons
```

**Responsibilities**:
- User interface rendering
- Video display and controls
- Real-time communication with backend
- User interaction handling
- Responsive design

## Data Flow Architecture

### 1. Camera to Backend Flow ✅ IMPLEMENTED
```
Camera Device → OpenCV VideoCapture → Frame Processing → Memory Buffer
     ↓                    ↓                 ↓              ↓
Hardware Detection → Device Initialize → Continuous Capture → Frame Access
```

### 2. Backend to Frontend Flow 🚧 PHASE 2 & 3
```
Frame Buffer → Frame Encoding → WebSocket → Browser Display
```

### 3. User Interaction Flow 📋 PHASE 2
```
User Input → JavaScript → API Request → Backend Processing → Response
```

## Technical Stack

### Backend Technologies ✅ PARTIALLY IMPLEMENTED
- **Framework**: Flask or FastAPI (to be implemented in Phase 2)
- **Video Processing**: OpenCV (cv2) ✅ IMPLEMENTED
- **Real-time Communication**: WebSockets (planned for Phase 3)
- **Async Processing**: asyncio (for async frameworks, planned)
- **Image Processing**: Pillow, NumPy ✅ INSTALLED

### Frontend Technologies 📋 PHASE 2
- **HTML5**: Video element and canvas for display (planned)
- **CSS3**: Responsive design and animations (planned)
- **JavaScript**: Real-time video handling and UI controls (planned)
- **WebSocket Client**: Real-time communication (planned)

### Supporting Technologies ✅ IMPLEMENTED
- **Camera Access**: OpenCV VideoCapture ✅ WORKING
- **Image Encoding**: JPEG/PNG compression ✅ AVAILABLE
- **Streaming Protocol**: WebSocket or WebRTC (planned)
- **Development Server**: Built-in Flask/FastAPI server (planned)

## Database Architecture (Future)
```
┌─────────────────┐
│   Configuration │
│   Database      │
├─────────────────┤
│ - Camera Settings
│ - User Preferences
│ - Stream History
│ - System Logs
└─────────────────┘
```

## Security Architecture

### Authentication & Authorization
- Basic authentication for camera access
- Session management for web interface
- CORS handling for cross-origin requests

### Data Security
- Secure camera permission handling
- Input validation and sanitization
- Error handling without data exposure

## Performance Architecture

### Optimization Strategies
- **Frame Rate Optimization**: Configurable FPS settings
- **Compression**: Efficient image compression for streaming
- **Buffering**: Smart frame buffering to prevent lag
- **Caching**: Static asset caching for web interface

### Scalability Considerations
- Modular design for easy feature addition
- Configurable streaming quality
- Multiple camera support architecture
- Resource monitoring and management

## Configuration Architecture

### Environment Configuration
```
config/
├── development.py         # Development settings
├── production.py          # Production settings
└── base.py               # Base configuration
```

### Runtime Configuration
- Camera device preferences
- Streaming quality settings
- Network configuration
- UI customization options

## Error Handling Architecture

### Error Categories
1. **Camera Errors**: Device access, connection failures
2. **Streaming Errors**: Network issues, encoding problems
3. **Web Errors**: HTTP errors, client-side issues
4. **System Errors**: Resource limitations, configuration issues

### Error Handling Strategy
- Graceful degradation for non-critical errors
- User-friendly error messages
- Comprehensive logging for debugging
- Automatic retry mechanisms where appropriate

## Testing Architecture ✅ IMPLEMENTED

### Test Structure
```
tests/
├── __init__.py           # Test package initialization
└── test_phase1.py        # Camera integration tests
```

### Testing Strategy
- **Unit Testing**: Individual component testing
- **Integration Testing**: Camera hardware integration ✅ IMPLEMENTED
- **Performance Testing**: Frame rate and resource usage validation ✅ IMPLEMENTED
- **Hardware Testing**: Multiple camera device support ✅ IMPLEMENTED

### Test Coverage (Phase 1)
- ✅ Camera device detection (1 device found)
- ✅ Camera initialization and configuration
- ✅ Single frame capture validation
- ✅ Continuous video capture (3-second test)
- ✅ Resolution and FPS adjustment
- ✅ Resource cleanup and status monitoring
- ✅ Error handling verification

### Test Execution
```bash
# Run Phase 1 tests
python tests\test_phase1.py
```

**Test Results**: All Phase 1 camera integration tests pass successfully with 640x480@30fps video capture.

## Deployment Architecture

### Local Development
```
Development Environment ✅ CURRENT SETUP
├── System Python Installation ✅ CONFIGURED
├── Local Camera Access ✅ WORKING (1 device detected)
├── Development Server (localhost:5000) 📋 PHASE 2
└── Real-time Debugging ✅ IMPLEMENTED
```

**Current Project Structure**:
```
aof_vid_stream/
├── src/                    # ✅ Source code modules
│   ├── camera/            # ✅ Camera handling (Phase 1 complete)
│   │   ├── __init__.py    # ✅ Package initialization
│   │   ├── camera_manager.py  # ✅ Main camera management
│   │   ├── device_detector.py # ✅ Device detection
│   │   └── video_capture.py   # ✅ Video capture
│   └── utils/             # ✅ Utility functions (ready)
├── tests/                 # ✅ Test files
│   ├── __init__.py        # ✅ Test package
│   └── test_phase1.py     # ✅ Phase 1 validation
├── .gitignore            # ✅ Git ignore configuration
├── requirements.txt      # ✅ Dependencies installed
├── README.md            # ✅ Project documentation
├── GUIDELINES.md        # ✅ Development guidelines
└── ARCHITECTURE.md      # ✅ This architecture document
```

### Production Considerations
- Environment variable configuration
- Production-grade web server
- Performance monitoring
- Resource optimization

This architecture provides a solid foundation for the video streaming application while maintaining flexibility for future enhancements and scalability.
