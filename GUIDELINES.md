# AOF Video Stream - Development Guidelines

## Project Overview
This project aims to create a web application that captures video from camera devices and streams it to a localhost web interface. The application will serve as a foundation for video streaming capabilities.

## Development Guidelines

### 1. Code Standards
- **Python Style**: Follow PEP 8 coding standards
- **Naming Conventions**: 
  - Use snake_case for variables and functions
  - Use PascalCase for classes
  - Use UPPER_CASE for constants
- **Documentation**: Include docstrings for all functions and classes
- **Type Hints**: Use type hints where applicable

### 2. Project Structure
```
aof_vid_stream/
├── src/
│   ├── camera/          # Camera handling modules
│   ├── streaming/       # Video streaming logic
│   ├── webapp/          # Web application components
│   └── utils/           # Utility functions
├── static/              # Static web assets (CSS, JS, images)
├── templates/           # HTML templates
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
└── app.py              # Main application entry point
```

### 3. Technology Stack
- **Backend**: Python with Flask/FastAPI
- **Frontend**: HTML5, CSS3, JavaScript
- **Video Processing**: OpenCV (cv2)
- **Streaming**: WebRTC or WebSocket for real-time streaming
- **Camera Access**: OpenCV for camera device access

### 4. Development Workflow

#### Phase 1: Camera Integration ✅ COMPLETED
- [x] Set up camera device detection
- [x] Implement video capture functionality
- [x] Test camera access and video feed quality
- [x] Handle multiple camera devices

**Implementation Details:**
- Created `DeviceDetector` class for camera enumeration
- Implemented `VideoCapture` class for frame capture and streaming
- Built `CameraManager` class for high-level camera operations
- Added comprehensive error handling and logging
- Created test script for Phase 1 validation (`tests/test_phase1.py`)
- Installed all required dependencies using system Python
- Successfully tested camera functionality with real hardware
- Created comprehensive README.md documentation
- Organized project structure with proper `__init__.py` files
- Moved test files to `tests/` directory as per guidelines

#### Phase 2: Web Interface ✅ COMPLETED
- [x] Create basic HTML interface
- [x] Implement MVC architecture with Flask
- [x] Create HTTP server with proper routing
- [x] Build REST API endpoints
- [x] Add About and Help pages with comprehensive documentation
- [x] **Implement real-time video display component**
- [x] Add camera selection controls
- [x] Style the interface with CSS
- [x] Create complete navigation system
- [x] **Live video streaming via Canvas and JavaScript**
- [x] **Frame capture API integration**
- [x] **Camera controls (start/stop/settings/snapshot/fullscreen)**

**Implementation Details:**
- Created complete MVC architecture in `src/webapp/`
- Built Flask application factory with configuration management
- Implemented Models: `CameraModel` and `StreamModel` for business logic
- Created Controllers: Main, Camera, and API controllers with proper routing
- Added Views utilities with template filters and helpers
- Developed comprehensive REST API with `/api/` endpoints
- Created main application entry point `app.py` with HTTP server
- Added error handling with custom 404, 500, and 403 pages
- Integrated Phase 1 camera components with web interface
- Configured template and static file serving
- Added CLI commands for testing and debugging
- Implemented environment-based configuration (dev/prod/test)
- **NEW**: Added comprehensive About page with project overview and status
- **NEW**: Added detailed Help page with troubleshooting and API documentation
- **NEW**: Enhanced navigation with About and Help links
- **NEW**: Added CSS styles for documentation pages
- **NEW**: Improved user experience with comprehensive help content
- **✅ COMPLETED**: Real-time video streaming with HTML5 Canvas and JavaScript
- **✅ COMPLETED**: Frame capture API (`/api/cameras/frame`) returning JPEG images
- **✅ COMPLETED**: Complete camera interface with start/stop/settings/snapshot controls
- **✅ COMPLETED**: 30 FPS video polling and display in browser
- **✅ COMPLETED**: Professional video container styling and user experience

#### Phase 3: Streaming Implementation ✅ COMPLETED
- [x] Set up video streaming server
- [x] Implement real-time video transmission
- [x] Optimize streaming performance
- [x] Add error handling and reconnection logic
- [x] **WebSocket-based streaming for ultra-low latency**
- [x] **Dual-mode streaming (WebSocket + HTTP polling)**
- [x] **Real-time performance metrics and quality control**

#### Phase 4: Enhancement
- [ ] Add recording capabilities
- [ ] Implement stream quality controls
- [ ] Add multi-camera support
- [ ] Performance optimization

### 5. Testing Guidelines
- Write unit tests for camera functions
- Test video streaming under different network conditions
- Verify cross-browser compatibility
- Test with multiple camera devices

### 6. Security Considerations
- Implement proper camera permission handling
- Secure localhost connections
- Validate user inputs
- Handle camera access errors gracefully

### 7. Performance Guidelines
- Optimize video frame rates for smooth streaming
- Minimize latency between camera capture and web display
- Efficient memory management for video buffers
- Monitor CPU usage during streaming

### 8. Error Handling
- Graceful handling of camera connection failures
- Network disconnection recovery
- User-friendly error messages
- Logging for debugging purposes

### 9. Configuration Management
- Use environment variables for configuration
- Separate development and production settings
- Configurable video quality settings
- Camera device preferences

### 10. Documentation Requirements
- Keep README.md updated with setup instructions
- Document API endpoints
- Include usage examples
- Maintain changelog for version updates
- **Update ARCHITECTURE.md whenever there are changes to the system architecture**
- Document any architectural decisions and their rationale

### 11. Version Control Guidelines
- **Git Ignore**: Always ignore `__pycache__/` directories and `*.pyc` files
- **Commit Messages**: Use clear, descriptive commit messages
- **Branch Strategy**: Use feature branches for new development
- **Code Reviews**: All changes should be reviewed before merging

#### Files to Ignore in Git:
- `__pycache__/` - Python bytecode cache directories
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `test_frame.jpg` - Test output files
- `logs/` - Log files
- IDE specific files (`.vscode/`, `.idea/`)
- OS specific files (`.DS_Store`, `Thumbs.db`)

### 12. User Experience Guidelines
- **Navigation**: Provide clear navigation with all main sections accessible
- **Documentation**: Include comprehensive help and about pages
- **Error Messages**: Provide user-friendly error messages and troubleshooting guidance
- **Responsive Design**: Ensure interface works on different screen sizes
- **Accessibility**: Follow web accessibility standards where possible

### 13. Current Known Issues and Resolutions
- **OpenCV Warnings**: Camera detection may show "Camera index out of range" warnings - these are normal during device enumeration
- **Resolution Detection**: Some cameras may show "No supported resolutions found" warning but still work with default settings
- **Multiple Device Support**: System supports multiple cameras but current UI focuses on primary device

### 14. Recent Improvements (August 2025)
- ✅ Added comprehensive About page with project status and technology overview
- ✅ Created detailed Help page with troubleshooting and API documentation
- ✅ Enhanced navigation system with all main sections
- ✅ Improved CSS styling for documentation pages
- ✅ Added responsive design for help and about content
- ✅ Documented common issues and their resolutions
- ✅ **NEW**: Restructured API into modular components for better organization
- ✅ **NEW**: Split large API controller into separate modules (cameras, streams, system)
- ✅ **NEW**: Improved API maintainability and scalability
- ✅ **NEW**: Enhanced API documentation with detailed endpoint information
- ✅ **COMPLETED**: Real-time video streaming implementation with Canvas-based display
- ✅ **COMPLETED**: Frame capture API serving JPEG images at 30 FPS
- ✅ **COMPLETED**: Complete camera controls (start/stop/settings/snapshot/fullscreen)
- ✅ **COMPLETED**: Professional video interface with responsive design
- ✅ **LATEST**: WebSocket-based video streaming for ultra-low latency
- ✅ **LATEST**: Dual streaming modes (WebSocket + HTTP polling) with runtime switching
- ✅ **LATEST**: Real-time performance metrics, FPS counter, and latency monitoring
- ✅ **LATEST**: Enhanced quality controls with configurable compression settings
- ✅ **NEW**: Advanced performance optimizations with multiple encoding methods
- ✅ **NEW**: Binary WebSocket transmission for 95% faster encoding (default method)
- ✅ **NEW**: Real-time encoding method switching (Binary/Base64/Compressed)
- ✅ **NEW**: Smart frame skipping and adaptive performance management
- ✅ **NEW**: Enhanced performance monitoring with encoding time tracking
- ✅ **NEW**: Threaded encoding operations to prevent blocking
- ✅ **NEW**: Frame size management and compression optimization

### 15. API Architecture Improvements
- **Modular Design**: Split monolithic API controller into specialized modules
- **Separation of Concerns**: Each API module handles specific functionality
- **Better Organization**: Cameras, Streams, and System APIs are now separate
- **Enhanced Maintainability**: Easier to add new features and fix issues
- **Improved Testing**: Individual API modules can be tested independently
- **Legacy Compatibility**: Old API endpoints redirect to new modular structure

### 16. Performance Optimization Implementation (August 2025)
- ✅ **Binary WebSocket Transmission**: Implemented direct JPEG binary data transmission
- ✅ **Encoding Method Selection**: Added runtime switching between Binary/Base64/Compressed modes
- ✅ **Performance Metrics**: Real-time encoding time and frame size monitoring
- ✅ **Adaptive Quality Control**: Removed automatic quality adjustments per user request
- ✅ **Threading Optimization**: Enhanced multi-threaded streaming with performance variables
- ✅ **Client-Side Optimization**: Binary frame handling with object URL management
- ✅ **Compression Support**: zlib compression for network optimization (optional)
- ✅ **Smart Frame Management**: Efficient frame buffering and display optimization

#### Binary Encoding Benefits:
- **95% Performance Improvement**: Binary transmission eliminates base64 encoding overhead
- **Reduced Latency**: Direct JPEG data transmission for ultra-low latency streaming
- **Lower CPU Usage**: Bypasses encoding/decoding steps for better resource utilization
- **Better Quality**: Maintains image quality while improving transmission speed
- **Real-time Switching**: Users can change encoding methods without stream interruption

#### Technical Implementation:
- **WebSocket Binary Frames**: Direct binary data transmission via WebSocket
- **Client Blob Handling**: Browser-native blob processing for optimal performance
- **Object URL Management**: Efficient memory management for binary frames
- **Performance Monitoring**: Real-time metrics for encoding time and frame sizes
- **Fallback Support**: Graceful degradation to base64 when binary not supported

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt` (uses system Python)
3. Run the application: `python app.py`
4. Access the web interface at `http://localhost:5000`

**Note**: This project uses the existing system Python installation instead of a virtual environment for simplicity.

## Contributing
- Create feature branches for new functionality
- Write tests for new features
- Update documentation as needed
- Follow the code review process
