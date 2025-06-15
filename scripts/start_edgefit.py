#!/usr/bin/env python3
"""
Edgefit-Coach Application Starter
Simple script to start the complete Edgefit-Coach application.
"""

import os
import sys
import subprocess
import time

def main():
    print("🚀 Edgefit-Coach Application Starter")
    print("=" * 50)
    print("🔧 Starting complete application...")
    print("   This will start all components automatically:")
    print("   • WebSocket Server")
    print("   • API Server") 
    print("   • Streamlit Frontend")
    print("=" * 50)
    
    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Start the API server (which will start all other components)
        print("⏳ Starting API server...")
        subprocess.run([sys.executable, "api_server.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Make sure you're in the correct directory and all files exist")

if __name__ == "__main__":
    main() 