#!/usr/bin/env python3
"""
AOF Video Stream - Main Application Entry Point

This is the main entry point for the AOF Video Stream web application.
It initializes the Flask app and starts the HTTP server.

Usage:
    python app.py

Author: AOF Video Stream Project
Date: August 2025
"""

import os
import sys
from flask import Flask
from src.webapp.app import create_app
from src.webapp.config import DevelopmentConfig, ProductionConfig

def main():
    """Main application entry point."""
    
    # Determine environment
    env = os.getenv('FLASK_ENV', 'development').lower()
    debug = env == 'development'
    
    # Create Flask application
    if env == 'production':
        config = ProductionConfig
    else:
        config = DevelopmentConfig
    
    app = create_app(config)
    
    # Print startup information
    print("=" * 60)
    print("🚀 AOF Video Stream Server Starting...")
    print("=" * 60)
    print(f"Environment: {env.title()}")
    print(f"Debug Mode: {debug}")
    print(f"Host: {config.HOST}")
    print(f"Port: {config.PORT}")
    print(f"URL: http://{config.HOST}:{config.PORT}")
    print("=" * 60)
    print("📋 Available Routes:")
    print("  • Home Page: http://localhost:5000/")
    print("  • Camera Interface: http://localhost:5000/camera")
    print("  • API Documentation: http://localhost:5000/api")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the development server
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("🛑 Server stopped by user")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
