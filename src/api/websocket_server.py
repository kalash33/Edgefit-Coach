#!/usr/bin/env python3
"""
Dedicated WebSocket server for AI Coach motivation quotes
Runs on port 8001 and monitors motivation_quotes.json for new quotes
"""

import asyncio
import websockets
import json
import os
import time
from datetime import datetime
import threading

# Get project root directory (two levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Global variables
connected_clients = set()
last_quote_count = 0
quote_queue = None

def monitor_motivation_file():
    """Monitor motivation_quotes.json for new quotes and broadcast them"""
    global last_quote_count, quote_queue
    motivation_file = os.path.join(DATA_DIR, "motivation_quotes.json")
    
    while True:
        try:
            if os.path.exists(motivation_file):
                # Check file size first to avoid reading empty/corrupted files
                if os.path.getsize(motivation_file) < 10:
                    print(f"⚠️ Motivation file too small, skipping: {motivation_file}")
                    time.sleep(2)
                    continue
                    
                with open(motivation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    quotes = data.get('quotes', [])
                    
                    if len(quotes) > last_quote_count:
                        # New quote available
                        new_quote = quotes[-1]  # Get the latest quote
                        print(f"💬 New AI quote detected: {new_quote.get('quote', 'Unknown')[:50]}...")
                        
                        # Add to queue for broadcasting (thread-safe)
                        if quote_queue:
                            try:
                                # Use put_nowait since we're in a thread
                                quote_queue.put_nowait(new_quote)
                                print(f"📤 Added quote to broadcast queue (queue size: {quote_queue.qsize()})")
                            except asyncio.QueueFull:
                                print(f"⚠️ Quote queue is full ({quote_queue.maxsize}), clearing old items")
                                # Clear some old items from queue
                                try:
                                    for _ in range(5):  # Remove 5 old items
                                        try:
                                            quote_queue.get_nowait()
                                        except asyncio.QueueEmpty:
                                            break
                                    quote_queue.put_nowait(new_quote)  # Add new quote
                                    print(f"✅ Added quote after clearing queue")
                                except Exception as clear_error:
                                    print(f"❌ Could not clear queue: {clear_error}")
                            except Exception as e:
                                print(f"❌ Error adding to queue: {e}")
                        
                        last_quote_count = len(quotes)
            else:
                print(f"⚠️ Motivation file not found: {motivation_file}")
            
            time.sleep(1)  # Check every 1 second
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error in motivation file: {e}")
            print(f"🔧 Attempting to fix corrupted file...")
            try:
                # Try to recreate the file with proper structure
                with open(motivation_file, 'w', encoding='utf-8') as f:
                    json.dump({"quotes": []}, f, indent=2)
                print(f"✅ Fixed corrupted motivation file")
            except Exception as fix_error:
                print(f"❌ Could not fix file: {fix_error}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Error monitoring motivation file: {e}")
            time.sleep(5)

async def broadcast_quote(quote_data):
    """Broadcast quote to all connected WebSocket clients"""
    global connected_clients
    if not connected_clients:
        return
    
    message = {
        "type": "motivation",
        "data": {
            "quote": quote_data.get('quote', ''),
            "timestamp": quote_data.get('timestamp', ''),
            "good_percentage": quote_data.get('good_percentage', 0),
            "good_posture_count": quote_data.get('good_posture_count', 0),
            "slouching_count": quote_data.get('slouching_count', 0)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to all connected clients
    disconnected = set()
    for websocket in connected_clients.copy():
        try:
            await websocket.send(json.dumps(message))
            print(f"📤 Sent quote to WebSocket client: {quote_data.get('quote', '')[:50]}...")
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(websocket)
        except Exception as e:
            print(f"❌ Error sending to client: {e}")
            disconnected.add(websocket)
    
    # Remove disconnected clients
    connected_clients -= disconnected

def update_websocket_status(connected=False, last_message=None):
    """Update WebSocket status file for Streamlit to read"""
    try:
        status_data = {
            "connected": connected,
            "last_message_time": last_message or datetime.now().isoformat(),
            "client_count": len(connected_clients),
            "updated": datetime.now().isoformat()
        }
        status_file = os.path.join(TEMP_DIR, "websocket_status.json")
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not update status file: {e}")

async def handle_client(websocket):
    """Handle individual WebSocket client connections"""
    global connected_clients, quote_queue
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    print(f"🔗 WebSocket client connected from {client_ip}. Total clients: {len(connected_clients)}")
    
    # Update status file
    update_websocket_status(connected=True)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "message": "Connected to AI Coach motivation stream",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_message))
        
        # Send latest quote if available
        try:
            motivation_file = os.path.join(DATA_DIR, "motivation_quotes.json")
            if os.path.exists(motivation_file):
                with open(motivation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    quotes = data.get('quotes', [])
                    if quotes:
                        latest_quote = quotes[-1]
                        await broadcast_quote(latest_quote)
                        update_websocket_status(connected=True, last_message=latest_quote.get('timestamp'))
        except Exception as e:
            print(f"⚠️ Could not send latest quote: {e}")
        
        # Main loop to handle messages and broadcast quotes
        while True:
            try:
                # Check for new quotes to broadcast
                if quote_queue:
                    try:
                        new_quote = quote_queue.get_nowait()
                        await broadcast_quote(new_quote)
                    except asyncio.QueueEmpty:
                        pass
                
                # Handle incoming messages with timeout
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    if message == "ping":
                        pong_message = {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(pong_message))
                        print(f"🏓 Pong sent to {client_ip}")
                    else:
                        print(f"📨 Received message from {client_ip}: {message}")
                except asyncio.TimeoutError:
                    pass  # No message received, continue loop
                except websockets.exceptions.ConnectionClosed:
                    break
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f"❌ Error in client loop for {client_ip}: {e}")
                break
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"❌ WebSocket error with {client_ip}: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"🔌 WebSocket client {client_ip} disconnected. Remaining clients: {len(connected_clients)}")
        # Update status file
        update_websocket_status(connected=len(connected_clients) > 0)

def start_file_monitor():
    """Start the file monitoring thread"""
    monitor_thread = threading.Thread(target=monitor_motivation_file, daemon=True)
    monitor_thread.start()
    print("🎯 Started motivation file monitoring thread")

async def main():
    """Main WebSocket server function"""
    global quote_queue
    
    print("🚀 Starting AI Coach WebSocket Server")
    print("=" * 50)
    print("📡 WebSocket server: ws://localhost:8001/")
    print("📁 Monitoring file: data/motivation_quotes.json")
    print("🔄 Auto-broadcasting new AI quotes to connected clients")
    print("=" * 50)
    
    # Initialize the queue in the async context
    quote_queue = asyncio.Queue(maxsize=50)  # Increased from 10 to 50
    print("📬 Quote broadcast queue initialized (maxsize=50)")
    
    # Start file monitoring
    start_file_monitor()
    
    # Start WebSocket server using the new API
    async with websockets.serve(handle_client, "localhost", 8001):
        print("✅ WebSocket server started on ws://localhost:8001/")
        print("🔗 Waiting for client connections...")
        
        # Keep server running indefinitely
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 WebSocket server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}") 