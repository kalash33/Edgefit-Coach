#!/usr/bin/env python3
"""
Launcher script for Edgefit-Coach Frontend Test
Starts both the API server and the Streamlit frontend.
"""

import subprocess
import time
import sys
import os
import threading
import requests

def check_api_health():
    """Check if API server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """Start the API server in background."""
    print("🚀 Starting API server...")
    try:
        # Start API server
        api_process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("⏳ Waiting for API server to start...")
        for i in range(30):  # Wait up to 30 seconds
            if check_api_health():
                print("✅ API server is running!")
                return api_process
            time.sleep(1)
            print(f"   Checking... ({i+1}/30)")
        
        print("❌ API server failed to start within 30 seconds")
        api_process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend."""
    print("🎨 Starting frontend test application...")
    try:
        # Start Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "frontend_test.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def main():
    """Main launcher function."""
    print("=" * 60)
    print("🏥 EDGEFIT-COACH FRONTEND TEST LAUNCHER")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ["api_server.py", "frontend_test.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            return
    
    print("✅ All required files found")
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot start frontend without API server")
        return
    
    try:
        # Start frontend
        start_frontend()
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if api_process:
            print("🛑 Stopping API server...")
            api_process.terminate()
            api_process.wait()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    main() 