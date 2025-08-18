#!/usr/bin/env python3
"""
Startup script for EMMA Healthcare Chatbot
"""

import os
import sys
import logging
from pathlib import Path

def setup_environment():
    """Setup environment variables and paths"""
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Create necessary directories
    directories = ['logs', 'data', 'uploads']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Set default environment variables if not set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    if not os.environ.get('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = 'true'

def main():
    """Main startup function"""
    try:
        # Setup environment
        setup_environment()
        
        # Import and run the app
        from app import app, socketio
        
        # Get configuration
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Starting EMMA Healthcare Chatbot...")
        print(f"📍 Server: http://{host}:{port}")
        print(f"🔧 Debug mode: {debug}")
        print(f"🌐 Environment: {os.environ.get('FLASK_ENV', 'development')}")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"📊 Health check: http://{host}:{port}/api/health")
        print(f"📈 Metrics: http://{host}:{port}/metrics")
        print(f"📋 Stats: http://{host}:{port}/stats")
        print("-" * 50)
        
        # Start the application
        socketio.run(app, host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        logging.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 