#!/usr/bin/env python3
"""
Interactive Testing Framework for Edgefit-Coach API Endpoints
Comprehensive testing suite with user-friendly interface.
"""

import asyncio
import json
import requests
import time
import websockets
from datetime import datetime
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

class APITester:
    """Interactive API testing framework."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.ws_url = WS_BASE_URL
        self.session = requests.Session()
        
    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"🧪 {title}")
        print("=" * 70)
    
    def print_section(self, title: str):
        """Print formatted section."""
        print(f"\n📋 {title}")
        print("-" * 50)
    
    def print_result(self, success: bool, message: str, data: Any = None):
        """Print formatted test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        if data and isinstance(data, dict):
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
        elif data:
            print(f"   Data: {str(data)[:200]}...")
    
    def test_server_health(self):
        """Test server health and basic connectivity."""
        self.print_section("Server Health Check")
        
        try:
            # Test root endpoint
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.print_result(True, "Root endpoint accessible", response.json())
            else:
                self.print_result(False, f"Root endpoint failed: {response.status_code}")
            
            # Test health endpoint
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.print_result(True, "Health check passed", health_data)
            else:
                self.print_result(False, f"Health check failed: {response.status_code}")
            
            # Test file status
            response = self.session.get(f"{self.base_url}/files/status")
            if response.status_code == 200:
                self.print_result(True, "File status check passed", response.json())
            else:
                self.print_result(False, f"File status check failed: {response.status_code}")
                
        except Exception as e:
            self.print_result(False, f"Server connectivity error: {str(e)}")
    
    def test_video_streaming_endpoints(self):
        """Test video streaming related endpoints."""
        self.print_section("Video Streaming Endpoints")
        
        try:
            # Test video status
            response = self.session.get(f"{self.base_url}/video/status")
            if response.status_code == 200:
                status_data = response.json()
                self.print_result(True, f"Video status: {status_data['status']}", status_data)
            else:
                self.print_result(False, f"Video status check failed: {response.status_code}")
            
            # Test video start
            print("\n🎥 Testing video stream start...")
            response = self.session.get(f"{self.base_url}/video/start")
            if response.status_code == 200:
                start_data = response.json()
                self.print_result(True, f"Video start: {start_data['status']}", start_data)
                
                # Wait a moment and check status again
                time.sleep(2)
                response = self.session.get(f"{self.base_url}/video/status")
                if response.status_code == 200:
                    status_data = response.json()
                    self.print_result(True, f"Video running status: {status_data['status']}", status_data)
            else:
                self.print_result(False, f"Video start failed: {response.status_code}")
            
            # Ask user if they want to stop the video
            user_input = input("\n🤔 Stop video stream? (y/n): ").lower().strip()
            if user_input == 'y':
                response = self.session.get(f"{self.base_url}/video/stop")
                if response.status_code == 200:
                    stop_data = response.json()
                    self.print_result(True, f"Video stop: {stop_data['status']}", stop_data)
                else:
                    self.print_result(False, f"Video stop failed: {response.status_code}")
                    
        except Exception as e:
            self.print_result(False, f"Video streaming test error: {str(e)}")
    
    async def test_websocket_motivation(self):
        """Test WebSocket motivation endpoint."""
        self.print_section("WebSocket Motivation Stream")
        
        try:
            uri = f"{self.ws_url}/ws/motivation"
            print(f"🔌 Connecting to WebSocket: {uri}")
            
            async with websockets.connect(uri) as websocket:
                self.print_result(True, "WebSocket connection established")
                
                # Send ping
                await websocket.send("ping")
                
                # Listen for messages for a short time
                print("📡 Listening for messages (10 seconds)...")
                try:
                    for i in range(5):  # Listen for 10 seconds
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        print(f"   📨 Received: {data['type']} - {data.get('message', 'N/A')}")
                        
                except asyncio.TimeoutError:
                    print("   ⏰ No messages received (timeout)")
                
                self.print_result(True, "WebSocket test completed successfully")
                
        except Exception as e:
            self.print_result(False, f"WebSocket test error: {str(e)}")
    
    def test_dashboard_endpoints(self):
        """Test dashboard data endpoints."""
        self.print_section("Dashboard Data Endpoints")
        
        try:
            # Test dashboard data generation
            print("📊 Testing dashboard data generation...")
            response = self.session.get(f"{self.base_url}/dashboard/data")
            
            if response.status_code == 200:
                dashboard_data = response.json()
                self.print_result(True, "Dashboard data generated successfully")
                
                # Display key metrics
                if 'data' in dashboard_data:
                    print("   📈 Key Metrics:")
                    for key, value in dashboard_data['data'].items():
                        print(f"      - {key.replace('_', ' ').title()}: {value}")
                
            else:
                self.print_result(False, f"Dashboard data generation failed: {response.status_code}")
            
            # Test dashboard refresh
            print("\n🔄 Testing dashboard refresh...")
            response = self.session.get(f"{self.base_url}/dashboard/refresh")
            if response.status_code == 200:
                self.print_result(True, "Dashboard refresh successful")
            else:
                self.print_result(False, f"Dashboard refresh failed: {response.status_code}")
                
        except Exception as e:
            self.print_result(False, f"Dashboard test error: {str(e)}")
    
    def test_chat_endpoints(self):
        """Test chat interface endpoints."""
        self.print_section("Chat Interface Endpoints")
        
        try:
            # Test chat history retrieval
            response = self.session.get(f"{self.base_url}/chat/history")
            if response.status_code == 200:
                history_data = response.json()
                self.print_result(True, f"Chat history retrieved ({history_data['total_conversations']} conversations)")
            else:
                self.print_result(False, f"Chat history retrieval failed: {response.status_code}")
            
            # Test chat message
            test_messages = [
                "What is good posture?",
                "How can I improve my sitting posture?",
                "What are some desk exercises I can do?"
            ]
            
            print(f"\n💬 Testing chat messages...")
            for i, message in enumerate(test_messages, 1):
                print(f"   {i}. Testing: '{message}'")
                
                chat_data = {"message": message}
                response = self.session.post(f"{self.base_url}/chat/message", json=chat_data)
                
                if response.status_code == 200:
                    chat_response = response.json()
                    self.print_result(True, f"Chat response received")
                    print(f"      Response: {chat_response['response'][:100]}...")
                else:
                    self.print_result(False, f"Chat message failed: {response.status_code}")
                
                time.sleep(1)  # Brief pause between messages
            
            # Ask user if they want to test custom message
            user_input = input("\n🤔 Test custom chat message? (y/n): ").lower().strip()
            if user_input == 'y':
                custom_message = input("Enter your message: ")
                chat_data = {"message": custom_message}
                response = self.session.post(f"{self.base_url}/chat/message", json=chat_data)
                
                if response.status_code == 200:
                    chat_response = response.json()
                    self.print_result(True, "Custom chat message successful")
                    print(f"   Response: {chat_response['response']}")
                else:
                    self.print_result(False, f"Custom chat message failed: {response.status_code}")
                    
        except Exception as e:
            self.print_result(False, f"Chat test error: {str(e)}")
    
    def test_analysis_endpoints(self):
        """Test analysis and report endpoints."""
        self.print_section("Analysis & Report Endpoints")
        
        try:
            # Test report file retrieval (if exists)
            response = self.session.get(f"{self.base_url}/analyze/report-file")
            if response.status_code == 200:
                report_data = response.json()
                self.print_result(True, f"Report file retrieved ({report_data['filename']})")
                print(f"   Content preview: {report_data['content'][:200]}...")
            else:
                print("   ℹ️  No existing report file found (this is normal)")
            
            # Test analysis report generation
            print("\n📊 Testing analysis report generation...")
            analysis_data = {"generate_report": True}
            response = self.session.post(f"{self.base_url}/analyze/report", json=analysis_data)
            
            if response.status_code == 200:
                analysis_response = response.json()
                self.print_result(True, "Analysis report generated successfully")
                
                if 'analysis' in analysis_response:
                    analysis_info = analysis_response['analysis']
                    print(f"   📄 Report file: {analysis_info.get('report_file', 'N/A')}")
                    print(f"   🤖 Analysis preview: {analysis_info.get('analysis_response', '')[:150]}...")
                    print(f"   💬 Conversation ID: {analysis_info.get('conversation_id', 'N/A')}")
                
            else:
                self.print_result(False, f"Analysis report generation failed: {response.status_code}")
                
        except Exception as e:
            self.print_result(False, f"Analysis test error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all tests in sequence."""
        self.print_header("COMPREHENSIVE API ENDPOINT TESTING")
        
        print("🚀 Starting comprehensive test suite...")
        print("⚠️  Make sure the API server is running on http://localhost:8000")
        
        user_input = input("\nContinue with testing? (y/n): ").lower().strip()
        if user_input != 'y':
            print("Testing cancelled.")
            return
        
        # Run all tests
        self.test_server_health()
        self.test_video_streaming_endpoints()
        
        # WebSocket test (async)
        print("\n🔌 Running WebSocket test...")
        asyncio.run(self.test_websocket_motivation())
        
        self.test_dashboard_endpoints()
        self.test_chat_endpoints()
        self.test_analysis_endpoints()
        
        self.print_header("TESTING COMPLETE")
        print("✅ All endpoint tests completed!")
        print("📊 Check the results above for any failures.")
    
    def interactive_menu(self):
        """Interactive testing menu."""
        while True:
            self.print_header("EDGEFIT-COACH API TESTING FRAMEWORK")
            print("Choose a testing option:")
            print("1. 🏥 Server Health Check")
            print("2. 🎥 Video Streaming Endpoints")
            print("3. 🔌 WebSocket Motivation Stream")
            print("4. 📊 Dashboard Data Endpoints")
            print("5. 💬 Chat Interface Endpoints")
            print("6. 📋 Analysis & Report Endpoints")
            print("7. 🚀 Run All Tests (Comprehensive)")
            print("8. 📖 Show Endpoint Documentation")
            print("9. ❌ Exit")
            
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                self.test_server_health()
            elif choice == '2':
                self.test_video_streaming_endpoints()
            elif choice == '3':
                asyncio.run(self.test_websocket_motivation())
            elif choice == '4':
                self.test_dashboard_endpoints()
            elif choice == '5':
                self.test_chat_endpoints()
            elif choice == '6':
                self.test_analysis_endpoints()
            elif choice == '7':
                self.run_comprehensive_test()
            elif choice == '8':
                self.show_endpoint_documentation()
            elif choice == '9':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def show_endpoint_documentation(self):
        """Show detailed endpoint documentation."""
        self.print_header("API ENDPOINT DOCUMENTATION")
        
        endpoints = {
            "2.1 Video Streaming & Motivation": {
                "GET /video/start": "Start video streaming process (main_webcam.py)",
                "GET /video/stop": "Stop video streaming process",
                "GET /video/status": "Get current video stream status",
                "WS /ws/motivation": "WebSocket for real-time motivation quotes"
            },
            "2.2 Dashboard Data": {
                "GET /dashboard/data": "Generate and return dashboard metrics (runs posture_db.py)",
                "GET /dashboard/refresh": "Force refresh dashboard data"
            },
            "2.3 Chat Interface": {
                "POST /chat/message": "Send chat message with context awareness",
                "GET /chat/history": "Retrieve chat conversation history",
                "DELETE /chat/history": "Clear all chat history"
            },
            "2.4 Analysis & Reports": {
                "POST /analyze/report": "Generate posture report and AI analysis",
                "GET /analyze/report-file": "Get raw posture report file content"
            },
            "Utility Endpoints": {
                "GET /": "Root endpoint with API information",
                "GET /health": "Health check for all services",
                "GET /files/status": "Check status of important files"
            }
        }
        
        for category, category_endpoints in endpoints.items():
            self.print_section(category)
            for endpoint, description in category_endpoints.items():
                print(f"   {endpoint:<25} - {description}")
        
        print(f"\n🌐 Base URL: {self.base_url}")
        print(f"📚 Interactive API Docs: {self.base_url}/docs")
        print(f"🔧 OpenAPI Schema: {self.base_url}/openapi.json")


def main():
    """Main function to run the testing framework."""
    print("🧪 Edgefit-Coach API Testing Framework")
    print("=" * 50)
    
    tester = APITester()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running!")
            tester.interactive_menu()
        else:
            print(f"⚠️  API server responded with status: {response.status_code}")
            print("Please check if the server is running properly.")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server!")
        print(f"Please make sure the server is running on {API_BASE_URL}")
        print("Run: python api_server.py")
    except Exception as e:
        print(f"❌ Error checking server status: {str(e)}")


if __name__ == "__main__":
    main() 