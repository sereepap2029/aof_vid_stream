"""
AOF Video Stream - Flask Application Factory

This module contains the Flask application factory and initialization logic.
"""

from flask import Flask, render_template, jsonify
from typing import Type
from .config import BaseConfig
from .controllers import register_blueprints
from .models import init_models
from .views import register_template_filters, register_template_globals


def create_app(config: Type[BaseConfig]) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration class to use
        
    Returns:
        Configured Flask application instance
    """
    
    # Create Flask application
    app = Flask(
        __name__,
        static_folder='../../static',
        template_folder='../../templates'
    )
    
    # Load configuration
    app.config.from_object(config)
    
    # Initialize extensions and components
    init_extensions(app)
    init_models(app)
    
    # Register template utilities
    register_template_filters(app)
    register_template_globals(app)
    
    # Register blueprints (controllers)
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    init_context_processors(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions.
    
    Args:
        app: Flask application instance
    """
    # Initialize any Flask extensions here
    # For example: db.init_app(app), migrate.init_app(app), etc.
    pass


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        return render_template('errors/403.html'), 403


def register_cli_commands(app: Flask) -> None:
    """
    Register custom CLI commands.
    
    Args:
        app: Flask application instance
    """
    
    @app.cli.command()
    def test_cameras():
        """Test camera detection and functionality."""
        from src.camera import CameraManager
        
        print("Testing camera functionality...")
        camera_manager = CameraManager()
        
        # Test camera detection
        devices = camera_manager.detect_cameras()
        print(f"Found {len(devices)} camera device(s)")
        
        for device in devices:
            print(f"  - Camera {device['index']}: {device['name']}")
        
        # Test camera initialization if devices found
        if devices:
            camera_id = devices[0]['index']
            print(f"\nTesting camera {camera_id}...")
            
            success = camera_manager.initialize_camera(camera_id)
            if success:
                print("✅ Camera initialization successful")
                
                # Test frame capture
                frame = camera_manager.get_frame()
                if frame is not None:
                    print("✅ Frame capture successful")
                    print(f"Frame shape: {frame.shape}")
                else:
                    print("❌ Frame capture failed")
                
                camera_manager.release_camera()
            else:
                print("❌ Camera initialization failed")
    
    @app.cli.command()
    def show_routes():
        """Display all application routes."""
        print("\nRegistered Routes:")
        print("-" * 50)
        
        for rule in app.url_map.iter_rules():
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"{rule.endpoint:30} {methods:15} {rule.rule}")
    
    @app.cli.command()
    def show_config():
        """Display current configuration."""
        print(f"\nCurrent Configuration:")
        print("-" * 50)
        print(f"Environment: {app.config.get('ENV', 'Unknown')}")
        print(f"Debug Mode: {app.config.get('DEBUG', False)}")
        print(f"Host: {app.config.get('HOST', 'localhost')}")
        print(f"Port: {app.config.get('PORT', 5000)}")
        print(f"Secret Key Set: {'Yes' if app.config.get('SECRET_KEY') else 'No'}")
        print(f"Camera Mock Mode: {app.config.get('CAMERA_MOCK_MODE', False)}")
        print(f"Default Resolution: {app.config.get('DEFAULT_RESOLUTION', (640, 480))}")
        print(f"Default FPS: {app.config.get('DEFAULT_FPS', 30)}")


# Application context processors
def init_context_processors(app: Flask) -> None:
    """
    Initialize template context processors.
    
    Args:
        app: Flask application instance
    """
    
    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates."""
        return {
            'app_name': 'AOF Video Stream',
            'app_version': '1.0.0',
            'debug_mode': app.config.get('DEBUG', False)
        }
