#!/usr/bin/env python3
"""
Simple startup script for Edgefit-Coach API Server
"""

import sys
import os

def main():
    """Start the API server with proper error handling."""
    print("🚀 Starting Edgefit-Coach API Server...")
    print("=" * 50)
    
    try:
        # Import and run the API server
        from api_server import app
        import uvicorn
        
        print("✅ All dependencies loaded successfully!")
        print("📋 Server will start on: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔧 To stop the server: Press Ctrl+C")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Please install dependencies: pip install -r requirements_api.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 