#!/usr/bin/env python3
"""
Edgefit-Coach Application Launcher
Starts all components in the correct order with proper delays.
"""

import os
import sys
import subprocess
import time
import signal
import webbrowser
import threading

# Set encoding for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'

def start_component(name, command, delay=0, show_output=False):
    """Start a component with error handling."""
    print(f"🚀 Starting {name}...")
    try:
        if delay > 0:
            print(f"⏳ Waiting {delay} seconds before starting {name}...")
            time.sleep(delay)
        
        if show_output:
            # For API server, show output in real-time for debugging
            process = subprocess.Popen(
                command,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
        else:
            # For other components, capture output to prevent clutter
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
        
        print(f"✅ {name} started successfully (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def open_browser_after_delay(url, delay_seconds):
    """Open browser after a delay in a separate thread."""
    def delayed_open():
        time.sleep(delay_seconds)
        try:
            print(f"🌐 Opening browser: {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"⚠️ Could not open browser automatically: {e}")
            print(f"💡 Please manually open: {url}")
    
    thread = threading.Thread(target=delayed_open, daemon=True)
    thread.start()

def main():
    print("🚀 Edgefit-Coach Application Launcher")
    print("=" * 50)
    
    processes = []
    
    try:
        # Step 1: Start WebSocket Server
        websocket_process = start_component(
            "WebSocket Server",
            ["python", "websocket_server.py"]
        )
        if websocket_process:
            processes.append(("WebSocket Server", websocket_process))
        
        # Step 2: Start API Server (with delay and verbose output)
        api_process = start_component(
            "API Server",
            ["python", "api_server.py"],
            delay=3,
            show_output=True  # Show API server logs for debugging
        )
        if api_process:
            processes.append(("API Server", api_process))
        
        # Step 3: Start Streamlit Frontend (with longer delay)
        streamlit_process = start_component(
            "Streamlit Frontend",
            ["python", "-m", "streamlit", "run", "frontend_test.py", "--server.port", "8501", "--server.headless", "true"],
            delay=5
        )
        if streamlit_process:
            processes.append(("Streamlit Frontend", streamlit_process))
        
        print("=" * 50)
        print("🎉 ALL COMPONENTS STARTED!")
        print("📋 Access your application at:")
        print("   🎨 Frontend: http://localhost:8501")
        print("   🔧 API Docs: http://localhost:8000/docs")
        print("   🔌 WebSocket: ws://localhost:8001")
        print("=" * 50)
        
        # Open browser automatically after a short delay
        print("🌐 Opening Streamlit app in browser...")
        open_browser_after_delay("http://localhost:8501", 3)
        
        print("Press Ctrl+C to stop all components...")
        
        # Wait for user interrupt
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} has stopped unexpectedly")
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all components...")
        
        # Stop all processes
        for name, process in processes:
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"🔪 Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("✅ All components stopped")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        # Clean up processes
        for name, process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main() 