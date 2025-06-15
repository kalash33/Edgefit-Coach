#!/usr/bin/env python3
"""
Edgefit-Coach Main Launcher
==========================

Main entry point for the Edgefit-Coach AI-Powered Posture Monitoring System.
This script provides a unified interface to launch different components of the application.

Usage:
    python edgefit_coach.py [mode] [options]

Modes:
    gui         - Launch GUI-based posture monitoring
    headless    - Launch headless posture monitoring with notifications
    web         - Launch complete web application (API + Frontend + WebSocket)
    api         - Launch API server only
    frontend    - Launch Streamlit frontend only
    websocket   - Launch WebSocket server only
    test        - Run system tests

Examples:
    python edgefit_coach.py web                    # Start complete web app
    python edgefit_coach.py headless               # Start headless monitoring
    python edgefit_coach.py gui                    # Start GUI monitoring
    python edgefit_coach.py test notifications     # Test notifications
"""

import sys
import os
import argparse
import subprocess
import time
import webbrowser
import threading
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def setup_environment():
    """Setup environment variables and paths."""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Ensure all directories exist
    directories = ['logs', 'temp', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def launch_gui_mode():
    """Launch GUI-based posture monitoring."""
    print("🖥️ Starting GUI-based posture monitoring...")
    try:
        subprocess.run([sys.executable, "src/core/main_webcam.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 GUI monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error launching GUI mode: {e}")

def launch_headless_mode():
    """Launch headless posture monitoring with notifications."""
    print("🤖 Starting headless posture monitoring with notifications...")
    try:
        subprocess.run([sys.executable, "src/core/main_webcam_headless1.py", "--headless"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Headless monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error launching headless mode: {e}")

def launch_web_mode():
    """Launch complete web application."""
    print("🌐 Starting complete web application...")
    try:
        subprocess.run([sys.executable, "scripts/start_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Web application stopped by user")
    except Exception as e:
        print(f"❌ Error launching web mode: {e}")

def launch_api_only():
    """Launch API server only."""
    print("🔧 Starting API server...")
    try:
        subprocess.run([sys.executable, "src/api/api_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 API server stopped by user")
    except Exception as e:
        print(f"❌ Error launching API server: {e}")

def launch_frontend_only():
    """Launch Streamlit frontend only."""
    print("🎨 Starting Streamlit frontend...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/frontend/frontend_test.py", 
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error launching frontend: {e}")

def launch_websocket_only():
    """Launch WebSocket server only."""
    print("🔌 Starting WebSocket server...")
    try:
        subprocess.run([sys.executable, "src/api/websocket_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 WebSocket server stopped by user")
    except Exception as e:
        print(f"❌ Error launching WebSocket server: {e}")

def run_tests(test_type=None):
    """Run system tests."""
    print("🧪 Running system tests...")
    
    if test_type == "notifications":
        print("📱 Testing desktop notifications...")
        subprocess.run([sys.executable, "tests/test_notifications.py"])
    elif test_type == "api":
        print("🔧 Testing API endpoints...")
        subprocess.run([sys.executable, "tests/test_api_endpoints.py"])
    elif test_type == "websocket":
        print("🔌 Testing WebSocket connection...")
        subprocess.run([sys.executable, "tests/test_websocket_client.py"])
    else:
        print("🔄 Running all tests...")
        subprocess.run([sys.executable, "tests/test_notifications.py"])
        time.sleep(2)
        subprocess.run([sys.executable, "tests/test_api_endpoints.py"])
        time.sleep(2)
        subprocess.run([sys.executable, "tests/test_websocket_client.py"])

def show_status():
    """Show system status and available components."""
    print("📊 Edgefit-Coach System Status")
    print("=" * 50)
    
    # Check if required files exist
    required_files = [
        "src/core/main_webcam.py",
        "src/core/main_webcam_headless1.py", 
        "src/api/api_server.py",
        "src/api/websocket_server.py",
        "src/frontend/frontend_test.py",
        "config/config.yaml"
    ]
    
    print("📁 File Status:")
    for file_path in required_files:
        status = "✅" if Path(file_path).exists() else "❌"
        print(f"   {status} {file_path}")
    
    print("\n🔧 Available Modes:")
    print("   🖥️  gui       - GUI-based monitoring")
    print("   🤖 headless  - Headless monitoring with notifications")
    print("   🌐 web       - Complete web application")
    print("   🔧 api       - API server only")
    print("   🎨 frontend  - Streamlit frontend only")
    print("   🔌 websocket - WebSocket server only")
    print("   🧪 test      - Run system tests")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Edgefit-Coach AI-Powered Posture Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["gui", "headless", "web", "api", "frontend", "websocket", "test", "status"],
        default="web",
        help="Launch mode (default: web)"
    )
    
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["notifications", "api", "websocket"],
        help="Specific test to run (only with test mode)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Edgefit-Coach v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Show banner
    print("🏥 Edgefit-Coach: AI-Powered Posture Monitoring System")
    print("=" * 60)
    
    # Route to appropriate function
    if args.mode == "gui":
        launch_gui_mode()
    elif args.mode == "headless":
        launch_headless_mode()
    elif args.mode == "web":
        launch_web_mode()
    elif args.mode == "api":
        launch_api_only()
    elif args.mode == "frontend":
        launch_frontend_only()
    elif args.mode == "websocket":
        launch_websocket_only()
    elif args.mode == "test":
        run_tests(args.test_type)
    elif args.mode == "status":
        show_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 