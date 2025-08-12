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

#### Phase 2: Web Interface
- [x] Create basic HTML interface
- [x] Implement MVC architecture with Flask
- [x] Create HTTP server with proper routing
- [x] Build REST API endpoints
- [ ] Implement video display component
- [ ] Add camera selection controls
- [x] Style the interface with CSS

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

#### Phase 3: Streaming Implementation
- [ ] Set up video streaming server
- [ ] Implement real-time video transmission
- [ ] Optimize streaming performance
- [ ] Add error handling and reconnection logic

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
