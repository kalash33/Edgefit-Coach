#!/usr/bin/env python3
"""
Simple WebSocket client to test AI Coach motivation endpoint
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8001/"
    
    try:
        print(f"🔄 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a ping
            await websocket.send("ping")
            print("🏓 Sent ping")
            
            # Listen for messages
            message_count = 0
            while message_count < 10:  # Listen for up to 10 messages
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        print(f"\n📨 Message {message_count}:")
                        print(f"   Type: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'motivation' and data.get('data'):
                            quote_data = data['data']
                            print(f"   🤖 AI Quote: {quote_data.get('quote', 'No quote')}")
                            print(f"   📊 Good: {quote_data.get('good_posture_count', 0)}")
                            print(f"   📊 Slouch: {quote_data.get('slouching_count', 0)}")
                            print(f"   📊 Performance: {quote_data.get('good_percentage', 0)}%")
                        elif data.get('type') == 'connection':
                            print(f"   📋 Connection: {data.get('message', 'No message')}")
                        elif data.get('type') == 'pong':
                            print(f"   🏓 Pong received")
                        else:
                            print(f"   📄 Raw: {json.dumps(data, indent=2)}")
                            
                    except json.JSONDecodeError:
                        print(f"   📄 Raw text: {message}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No message received in 5 seconds, sending ping...")
                    await websocket.send("ping")
                    
            print(f"\n✅ Test completed - received {message_count} messages")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused - is the API server running on localhost:8000?")
    except websockets.exceptions.InvalidURI:
        print("❌ Invalid WebSocket URI")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing AI Coach WebSocket Connection")
    print("=" * 50)
    asyncio.run(test_websocket()) 