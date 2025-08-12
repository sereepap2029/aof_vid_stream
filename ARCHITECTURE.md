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

### ✅ Phase 2: Web Interface (COMPLETED)
- ✅ HTML5 web interface design  
- ✅ MVC architecture implementation
- ✅ Flask application with proper routing
- ✅ REST API endpoints
- ✅ HTTP server with development/production configs
- ✅ Template system with error handling
- ✅ CSS styling and responsive design
- [ ] Video display component (next - Phase 2.2)
- [ ] Real-time video streaming integration (next - Phase 2.3)

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

### 3. Web Application Layer ✅ IMPLEMENTED
**Location**: `src/webapp/`

```
Web Application Layer
├── __init__.py            # ✅ Package initialization
├── app.py                 # ✅ Flask application factory
├── config.py              # ✅ Environment configuration management
├── models/                # ✅ Models (M in MVC)
│   ├── __init__.py        # ✅ Model initialization
│   ├── camera_model.py    # ✅ Camera business logic
│   └── stream_model.py    # ✅ Stream session management
├── views/                 # ✅ Views (V in MVC) 
│   └── __init__.py        # ✅ Template utilities and filters
└── controllers/           # ✅ Controllers (C in MVC)
    ├── __init__.py        # ✅ Blueprint registration
    ├── main_controller.py # ✅ Main web routes
    ├── camera_controller.py # ✅ Camera operations API
    └── api_controller.py  # ✅ REST API endpoints
```

**Responsibilities**:
- ✅ Serve web interface with Flask
- ✅ Handle HTTP requests with proper routing
- ✅ Provide comprehensive REST API endpoints
- ✅ Manage configuration for different environments
- ✅ Template rendering with error handling
- ✅ MVC architecture implementation

**Key Components**:
- ✅ `app.py`: Application factory with Flask configuration
- ✅ `config.py`: Environment-based configuration classes
- ✅ `models/`: Business logic for camera and streaming operations
- ✅ `controllers/`: Request routing and API endpoint handling
- ✅ `views/`: Template utilities and formatting helpers

### 4. Frontend Layer ✅ IMPLEMENTED
**Location**: `static/` and `templates/`

```
Frontend Layer
├── templates/              # ✅ HTML templates
│   ├── base.html          # ✅ Base template with navigation
│   ├── index.html         # ✅ Home page with features
│   ├── camera.html        # ✅ Camera interface
│   └── errors/            # ✅ Error page templates
│       ├── 404.html       # ✅ Not found page
│       ├── 500.html       # ✅ Server error page
│       └── 403.html       # ✅ Forbidden page
└── static/                # ✅ Static web assets
    ├── css/
    │   └── style.css      # ✅ Complete application styles
    └── js/
        ├── camera.js      # ✅ Camera control logic
        └── main.js        # ✅ Common application utilities
```

**Responsibilities**:
- ✅ User interface rendering with responsive design
- ✅ Video display placeholder and controls
- ✅ Real-time status updates via JavaScript
- ✅ User interaction handling for camera operations
- ✅ Error page presentation

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

### 3. User Interaction Flow ✅ IMPLEMENTED
```
User Input → JavaScript → API Request → Backend Processing → Response
```

**Current Implementation:**
- ✅ Web interface at http://localhost:5000
- ✅ Camera controls via REST API endpoints
- ✅ Status monitoring and device management
- ✅ Error handling and user feedback

## Technical Stack

### Backend Technologies ✅ IMPLEMENTED
- **Framework**: Flask ✅ IMPLEMENTED with MVC architecture
- **Video Processing**: OpenCV (cv2) ✅ IMPLEMENTED
- **Configuration Management**: Environment-based configs ✅ IMPLEMENTED
- **REST API**: Comprehensive API endpoints ✅ IMPLEMENTED
- **Template Engine**: Jinja2 with custom filters ✅ IMPLEMENTED
- **Real-time Communication**: WebSockets (planned for Phase 3)
- **Async Processing**: asyncio (for async frameworks, planned)
- **Image Processing**: Pillow, NumPy ✅ INSTALLED

### Frontend Technologies ✅ IMPLEMENTED
- **HTML5**: Complete template system with inheritance ✅ IMPLEMENTED
- **CSS3**: Responsive design with animations ✅ IMPLEMENTED
- **JavaScript**: Camera controls and UI interactions ✅ IMPLEMENTED
- **Template System**: Jinja2 with custom filters ✅ IMPLEMENTED
- **WebSocket Client**: Real-time communication (planned for Phase 3)

### Supporting Technologies ✅ IMPLEMENTED
- **Camera Access**: OpenCV VideoCapture ✅ WORKING
- **Image Encoding**: JPEG/PNG compression ✅ AVAILABLE
- **HTTP Server**: Flask development server ✅ RUNNING
- **Configuration**: Environment-based settings ✅ IMPLEMENTED
- **Error Handling**: Custom error pages ✅ IMPLEMENTED
- **Streaming Protocol**: WebSocket or WebRTC (planned for Phase 3)
- **Development Server**: Flask with auto-reload ✅ WORKING

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

## Web Application Architecture ✅ IMPLEMENTED

### MVC Implementation
The web application follows a strict Model-View-Controller architecture:

**Models (`src/webapp/models/`):**
- `CameraModel`: Manages camera devices, streaming operations, and hardware integration
- `StreamModel`: Handles streaming sessions, performance metrics, and session management
- Data classes for structured information (CameraDevice, CameraStatus, StreamSession, etc.)

**Views (`src/webapp/views/` and `templates/`):**
- Template utilities with custom filters for formatting
- Responsive HTML templates with inheritance
- Error handling pages (404, 500, 403)
- JavaScript utilities for UI interactions

**Controllers (`src/webapp/controllers/`):**
- `MainController`: Web page rendering and status endpoints
- `CameraController`: Camera operations and device management
- `ApiController`: RESTful API with comprehensive endpoints

### HTTP Server Features
- **Flask Application Factory**: Environment-based configuration
- **Development Server**: Auto-reload, debugging, CLI commands
- **Production Ready**: Configuration for deployment
- **Error Handling**: Custom error pages and API error responses
- **Static File Serving**: CSS, JavaScript, and asset management

### API Endpoints
```
Web Routes:
├── GET  /              # Home page
├── GET  /camera        # Camera interface
├── GET  /status        # System status JSON
└── GET  /config        # Configuration JSON

Camera API:
├── GET  /camera/devices    # List available cameras
├── POST /camera/start      # Start streaming
├── POST /camera/stop       # Stop streaming
├── GET  /camera/frame      # Latest frame as JPEG
├── GET  /camera/stream     # Video stream (multipart)
└── POST /camera/snapshot   # Take snapshot

REST API (/api/):
├── GET  /api/              # API documentation
├── GET  /api/cameras       # Camera management
├── GET  /api/streams       # Stream sessions
├── GET  /api/system/status # System health
└── GET  /api/system/health # Health check
```

## Deployment Architecture

### Local Development
```
Development Environment ✅ CURRENT SETUP
├── System Python Installation ✅ CONFIGURED
├── Local Camera Access ✅ WORKING (1 device detected)
├── Flask Development Server ✅ RUNNING (localhost:5000)
├── MVC Web Application ✅ IMPLEMENTED
├── REST API Endpoints ✅ AVAILABLE
└── Real-time Debugging ✅ IMPLEMENTED
```

**Current Project Structure**:
```
aof_vid_stream/
├── app.py                 # ✅ Main application entry point
├── src/                   # ✅ Source code modules
│   ├── camera/           # ✅ Camera handling (Phase 1 complete)
│   │   ├── __init__.py   # ✅ Package initialization
│   │   ├── camera_manager.py  # ✅ Main camera management
│   │   ├── device_detector.py # ✅ Device detection
│   │   └── video_capture.py   # ✅ Video capture
│   ├── webapp/           # ✅ Web application (Phase 2 complete)
│   │   ├── __init__.py   # ✅ Package initialization
│   │   ├── app.py        # ✅ Flask application factory
│   │   ├── config.py     # ✅ Configuration management
│   │   ├── models/       # ✅ Business logic models
│   │   ├── views/        # ✅ Template utilities
│   │   └── controllers/  # ✅ Request handlers
│   └── utils/            # ✅ Utility functions (ready)
├── templates/            # ✅ HTML templates
│   ├── base.html         # ✅ Base template
│   ├── index.html        # ✅ Home page
│   ├── camera.html       # ✅ Camera interface
│   └── errors/           # ✅ Error pages
├── static/               # ✅ Static web assets
│   ├── css/style.css     # ✅ Application styles
│   └── js/               # ✅ JavaScript files
├── tests/                # ✅ Test files
│   ├── __init__.py       # ✅ Test package
│   └── test_phase1.py    # ✅ Phase 1 validation
├── .gitignore           # ✅ Git ignore configuration
├── requirements.txt     # ✅ Dependencies installed
├── README.md           # ✅ Project documentation
├── GUIDELINES.md       # ✅ Development guidelines
└── ARCHITECTURE.md     # ✅ This architecture document
```

### Production Considerations
- Environment variable configuration
- Production-grade web server
- Performance monitoring
- Resource optimization

This architecture provides a solid foundation for the video streaming application while maintaining flexibility for future enhancements and scalability.
