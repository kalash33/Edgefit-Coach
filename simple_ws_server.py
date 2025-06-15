#!/usr/bin/env python3
"""
Simple, robust WebSocket server for AI Coach
"""
import asyncio
import websockets
import json
import os
import time
from datetime import datetime
from typing import Set

# Global variables
connected_clients: Set = set()
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MOTIVATION_FILE = os.path.join(PROJECT_ROOT, "data", "motivation_quotes.json")

async def handle_client(websocket):
    """Handle individual WebSocket client connections"""
    client_addr = websocket.remote_address
    print(f"🔗 Client connected: {client_addr}")
    
    try:
        connected_clients.add(websocket)
        
        # Send welcome message
        welcome = {
            "type": "connection",
            "message": "Connected to AI Coach WebSocket",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome))
        
        # Send latest quote if available
        try:
            if os.path.exists(MOTIVATION_FILE):
                with open(MOTIVATION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    quotes = data.get('quotes', [])
                    if quotes:
                        latest_quote = quotes[-1]
                        quote_msg = {
                            "type": "motivation",
                            "data": {
                                "quote": latest_quote.get('quote', ''),
                                "timestamp": latest_quote.get('timestamp', ''),
                                "good_percentage": latest_quote.get('good_percentage', 0)
                            }
                        }
                        await websocket.send(json.dumps(quote_msg, ensure_ascii=False))
        except Exception as e:
            print(f"⚠️ Could not send latest quote: {e}")
        
        # Handle incoming messages
        async for message in websocket:
            try:
                if message == "ping":
                    pong = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(pong))
                    print(f"🏓 Pong sent to {client_addr}")
                else:
                    print(f"📨 Received from {client_addr}: {message}")
            except Exception as e:
                print(f"❌ Error handling message from {client_addr}: {e}")
                break
                
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 Client {client_addr} disconnected normally")
    except Exception as e:
        print(f"❌ Error with client {client_addr}: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"🔌 Client {client_addr} removed. Total clients: {len(connected_clients)}")

async def broadcast_to_all(message):
    """Broadcast message to all connected clients"""
    if not connected_clients:
        return
    
    # Create a copy of the set to avoid modification during iteration
    clients_copy = connected_clients.copy()
    
    for client in clients_copy:
        try:
            await client.send(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Failed to send to client: {e}")
            connected_clients.discard(client)

def monitor_motivation_file():
    """Monitor motivation file for changes"""
    last_modified = 0
    last_quote_count = 0
    
    while True:
        try:
            if os.path.exists(MOTIVATION_FILE):
                # Check if file was modified
                current_modified = os.path.getmtime(MOTIVATION_FILE)
                
                if current_modified > last_modified:
                    last_modified = current_modified
                    
                    with open(MOTIVATION_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        quotes = data.get('quotes', [])
                        
                        if len(quotes) > last_quote_count:
                            # New quote detected
                            latest_quote = quotes[-1]
                            quote_text = latest_quote.get('quote', '')
                            
                            # Skip malformed quotes
                            if quote_text and len(quote_text.strip()) > 1 and not quote_text.startswith('<'):
                                message = {
                                    "type": "motivation",
                                    "data": {
                                        "quote": quote_text,
                                        "timestamp": latest_quote.get('timestamp', ''),
                                        "good_percentage": latest_quote.get('good_percentage', 0),
                                        "good_posture_count": latest_quote.get('good_posture_count', 0),
                                        "slouching_count": latest_quote.get('slouching_count', 0)
                                    },
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # Schedule broadcast
                                asyncio.create_task(broadcast_to_all(message))
                                print(f"💬 Broadcasting new quote: {quote_text[:50]}...")
                            
                            last_quote_count = len(quotes)
            
            time.sleep(1)  # Check every second
            
        except Exception as e:
            print(f"❌ Error monitoring file: {e}")
            time.sleep(5)

async def main():
    """Main server function"""
    print("🚀 Starting Simple AI Coach WebSocket Server")
    print("=" * 50)
    print(f"📡 Server: ws://localhost:8001/")
    print(f"📁 Monitoring: {MOTIVATION_FILE}")
    print("=" * 50)
    
    # Start file monitoring in background thread
    import threading
    monitor_thread = threading.Thread(target=monitor_motivation_file, daemon=True)
    monitor_thread.start()
    print("🎯 File monitoring started")
    
    # Start WebSocket server
    try:
        async with websockets.serve(handle_client, "localhost", 8001):
            print("✅ WebSocket server started on ws://localhost:8001/")
            print("🔗 Waiting for connections...")
            
            # Keep server running
            await asyncio.Future()  # Run forever
            
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}") 