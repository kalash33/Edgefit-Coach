#!/usr/bin/env python3
"""
Frontend Test Application for Edgefit-Coach API
A comprehensive Streamlit-based frontend to test all API endpoints.
"""

import streamlit as st
import requests
import json
import time
import os
import asyncio
import websockets
import threading
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/motivation"

# Page configuration
st.set_page_config(
    page_title="Edgefit-Coach Frontend Test",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .status-success {
        color: #2ca02c;
        font-weight: bold;
    }
    .status-error {
        color: #d62728;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    /* Dark mode support for analysis containers */
    :root {
        --background-color: #f8f9fa;
        --text-color: #333333;
        --border-color: #e9ecef;
    }
    
    /* Streamlit dark mode detection */
    [data-theme="dark"] {
        --background-color: #2b2b2b;
        --text-color: #ffffff;
        --border-color: #404040;
    }
    
    /* Auto-detect system dark mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-color: #2b2b2b;
            --text-color: #ffffff;
            --border-color: #404040;
            --status-bg: #2d3748;
            --status-text: #ffffff;
            --messages-bg: #1a202c;
            --messages-text: #ffffff;
            --loading-text: #a0aec0;
        }
    }
    
    /* WebSocket component dark mode variables */
    :root {
        --status-bg: #f8d7da;
        --status-text: #721c24;
        --messages-bg: #f8f9fa;
        --messages-text: #333333;
        --loading-text: #666666;
    }
    
    /* Dark mode overrides for WebSocket */
    [data-theme="dark"] {
        --status-bg: #2d3748;
        --status-text: #ffffff;
        --messages-bg: #1a202c;
        --messages-text: #ffffff;
        --loading-text: #a0aec0;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint, method="GET", data=None):
    """Make API request with error handling."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        # Set longer timeout for analysis and chat endpoints
        timeout = 90 if "/analyze/" in endpoint or "/chat/" in endpoint else 10
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        
        return response.status_code, response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        return None, {"error": str(e)}

def control_video_for_page(page_name):
    """Control video streaming based on current page."""
    try:
        data = {"page_name": page_name}
        status_code, response = make_api_request("/video/page-control", method="POST", data=data)
        
        if status_code == 200:
            print(f"✅ Video control for {page_name}: {response.get('message', 'Success')}")
            return True
        else:
            print(f"⚠️ Video control warning for {page_name}: {response.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error controlling video for {page_name}: {str(e)}")
        return False

def main():
    st.markdown('<h1 class="main-header">🏥 Edgefit Coach - AI Posture and Fitness Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        [
            "📹 Live Video & Motivation",
            "📊 Dashboard Data",
            "🤖 Chat Interface",
            "📈 Analysis & Reports",
            "🔧 System Status"
        ]
    )
    
    # Auto-control video streaming based on page selection
    if 'current_page' not in st.session_state:
        st.session_state.current_page = None
    
    # Only control video if page actually changed
    if st.session_state.current_page != page:
        if page == "📹 Live Video & Motivation":
            with st.spinner("🎬 Preparing video stream..."):
                control_video_for_page("video")
        elif page == "📊 Dashboard Data":
            with st.spinner("⏸️ Optimizing for dashboard..."):
                control_video_for_page("dashboard")
        elif page == "📈 Analysis & Reports":
            with st.spinner("⏸️ Pausing video for analysis..."):
                control_video_for_page("analysis")
        elif page == "🤖 Chat Interface":
            with st.spinner("⏸️ Pausing video for chat..."):
                control_video_for_page("chat")
        elif page == "🔧 System Status":
            with st.spinner("⏸️ Pausing video for system status..."):
                control_video_for_page("system")
        else:
            # For any other pages, pause video
            page_name = page.split()[1].lower() if len(page.split()) > 1 else "other"
            with st.spinner("⏸️ Pausing video stream..."):
                control_video_for_page(page_name)
        
        st.session_state.current_page = page
    
    if page == "📹 Live Video & Motivation":
        live_video_page()
    elif page == "📊 Dashboard Data":
        dashboard_page()
    elif page == "🤖 Chat Interface":
        chat_page()
    elif page == "📈 Analysis & Reports":
        analysis_page()
    elif page == "🔧 System Status":
        system_status_page()



def live_video_page():
    st.markdown('<h2 class="section-header"></h2>', unsafe_allow_html=True)
    
    # Show stream resumption status

    
    # Create compact header with WebSocket status in top right
    header_col1, header_col2 = st.columns([3, 1])
    

    
    with header_col2:
        # Compact WebSocket status indicator
        ws_status_file = "websocket_status.json"
        ws_connected = False
        
        try:
            if os.path.exists(ws_status_file):
                with open(ws_status_file, 'r') as f:
                    ws_data = json.load(f)
                    ws_connected = ws_data.get('connected', False)
        except:
            pass
        
        # if ws_connected:
        #     st.success("🤖 AI Coach: LIVE")
        # else:
        #     st.warning("🤖 AI Coach: Connecting...")
        
        # # Compact refresh button
        # if st.button("🔄", key="refresh_live_feed", help="Refresh Live Feed"):
        #     st.rerun()
    
    # Add auto-refresh every 5 seconds
    st.markdown("""
    <script>
    setTimeout(function() {
        window.location.reload();
    }, 5000);
    </script>
    """, unsafe_allow_html=True)
    
    # Main content area - Create two columns for video controls and motivation
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📹 Video Stream Control")
        
        # Video stream display
        video_placeholder = st.empty()
        
        # Check if video stream is running and display it
        status_code, response = make_api_request("/video/status")
        if status_code == 200 and response.get("status") == "running":
            try:
                stream_url = response.get("stream_url", "http://localhost:8000/video/stream")
                
                # Use simple MJPEG streaming that works reliably
                video_placeholder.markdown(f"""
                <div style="text-align: center; border: 2px solid #1f77b4; border-radius: 10px; padding: 10px;">
                    <h4>📹 Live Video Stream</h4>
                    <img src="{stream_url}" 
                         width="100%" 
                         style="border-radius: 10px; max-width: 640px; height: auto;"
                         alt="Live Video Stream"
                         id="videoStream">
                    <p><small>🟢 LIVE - Pose Detection Active</small></p>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                video_placeholder.error(f"❌ Video display error: {str(e)}")
                video_placeholder.info("📹 Video stream starting...")
        else:
            video_placeholder.info("📹 Video stream not running. Click 'Restart Stream' to start.")
        
        # Stream status display
        status_placeholder = st.empty()
        
        # Check current status
        status_code, response = make_api_request("/video/status")
        if status_code == 200:
            status = response.get("status", "unknown")
            if status == "running":
                status_placeholder.success(f"🟢 Stream Status: {status.upper()}")
                if response.get('pid'):
                    st.info(f"📊 Process ID: {response.get('pid')}")
            else:
                status_placeholder.warning(f"🟡 Stream Status: {status.upper()}")
        else:
            status_placeholder.error("🔴 Stream Status: UNKNOWN")
        
        # Control buttons
        col1a, col1b = st.columns(2)
        
        with col1a:
            if st.button("🔄 Restart Stream", key="restart_video"):
                with st.spinner("Restarting video stream..."):
                    # Stop first
                    make_api_request("/video/stop")
                    time.sleep(1)
                    # Then start
                    status_code, response = make_api_request("/video/start")
                    
                    if status_code == 200:
                        st.success("✅ Stream restarted!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to restart stream")
        
        with col1b:
            if st.button("⏹️ Stop Stream", key="stop_video"):
                with st.spinner("Stopping video stream..."):
                    status_code, response = make_api_request("/video/stop")
                    
                    if status_code == 200:
                        st.success("✅ Stream stopped!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to stop stream")
        
        # Video stream info
        # st.markdown("---")
        # st.markdown("**📋 Stream Information:**")
        # st.markdown("""
        # - **Web Mode**: Live video stream in frontend (current)
        # - **Direct Mode**: Full GUI with video display
        # - **Camera**: Default system camera
        # - **Detection**: Posture + Stretching exercises
        # - **Logging**: 30-second discrete windows
        # - **Output**: Real-time posture feedback with overlays
        # """)
        
        # # Instructions for GUI mode
        # st.info("""
        # 💡 **Video Stream Modes:**
        # - **Web Stream**: Video appears above with all text overlays
        # - **GUI Mode**: Run `python main_webcam_headless1.py` for desktop window
        # - **API Mode**: Background processing only (--headless flag)
        # """)
        
        # # Show recent posture data if available
        # if st.button("📊 Show Recent Data", key="show_recent"):
        #     dashboard_status, dashboard_response = make_api_request("/dashboard/data")
        #     if dashboard_status == 200 and "metrics" in dashboard_response:
        #         metrics = dashboard_response["metrics"]
        #         st.metric("Good Posture %", f"{metrics.get('good_posture_percentage', 0):.1f}%")
        #         st.metric("Total Sessions", metrics.get('total_sessions', 0))
    
    with col2:
        st.subheader("🤖 Live AI Coach Feed")
        
        # Live WebSocket Client for real-time AI coaching messages
        st.components.v1.html(f"""
        <style>
            /* Dark theme detection and styling */
            .websocket-container {{
                background: #f8f9fa;
                color: #333333;
                border-color: #ddd;
            }}
            
            .websocket-status {{
                background: #f8d7da;
                color: #721c24;
            }}
            
            .websocket-status.connected {{
                background: #d4edda;
                color: #155724;
            }}
            
            /* Dark mode styles */
            @media (prefers-color-scheme: dark) {{
                .websocket-container {{
                    background: #1a202c !important;
                    color: #ffffff !important;
                    border-color: #404040 !important;
                }}
                
                .websocket-status {{
                    background: #2d3748 !important;
                    color: #ffffff !important;
                }}
                
                .websocket-status.connected {{
                    background: #2d5a3d !important;
                    color: #68d391 !important;
                }}
                
                .message-content {{
                    background: #2d3748 !important;
                    color: #ffffff !important;
                    border-color: #4a5568 !important;
                }}
                
                .loading-text {{
                    color: #a0aec0 !important;
                }}
            }}
        </style>
        
        <div id="websocket-status" class="websocket-status" style="padding: 8px; border-radius: 5px; margin: 5px 0; font-size: 12px; text-align: center; font-weight: bold;">
            🔴 Connecting to AI Coach...
        </div>
        <div id="websocket-messages" class="websocket-container" style="max-height: 350px; overflow-y: auto; border: 1px solid; padding: 10px; border-radius: 5px;">
            <div class="loading-text" style="text-align: center; padding: 20px; font-weight: bold; color: #666;">🔄 Connecting to AI Coach WebSocket...</div>
        </div>
        
        <script>
        let ws = null;
        let messageCount = 0;
        const statusDiv = document.getElementById('websocket-status');
        const messagesDiv = document.getElementById('websocket-messages');
        
        function updateStatus(text, isConnected) {{
            statusDiv.textContent = text;
            statusDiv.className = isConnected ? 'websocket-status connected' : 'websocket-status';
        }}
        
        function addMessage(content, isImportant = false) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message-content';
            messageDiv.style.margin = '8px 0';
            messageDiv.style.padding = '10px';
            messageDiv.style.background = isImportant ? '#e8f5e8' : '#f1f3f4';
            messageDiv.style.borderRadius = '6px';
            messageDiv.style.borderLeft = isImportant ? '4px solid #28a745' : '4px solid #6c757d';
            messageDiv.style.fontSize = '13px';
            messageDiv.style.border = '1px solid #e9ecef';
            messageDiv.innerHTML = content;
            messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
            
            // Keep only last 5 messages
            while (messagesDiv.children.length > 5) {{
                messagesDiv.removeChild(messagesDiv.lastChild);
            }}
            
            messageCount++;
        }}
        
        function connectWebSocket() {{
            try {{
                updateStatus('🔄 Connecting to AI Coach...', false);
                
                ws = new WebSocket('ws://localhost:8001/');
                
                ws.onopen = function() {{
                    console.log('🟢 Connected to AI Coach WebSocket');
                    updateStatus('🟢 AI Coach Connected - LIVE', true);
                                            addMessage(`
                            <div style="text-align: center; color: #28a745; font-weight: bold;">
                                <strong>✅ CONNECTED TO AI COACH!</strong><br>
                                <small style="font-weight: normal; opacity: 0.8;">Ready to receive live motivation quotes...</small>
                            </div>
                        `);
                }};
                
                ws.onmessage = function(event) {{
                    try {{
                        const message = JSON.parse(event.data);
                        console.log('📨 WebSocket message received:', message);
                        
                        if (message.type === 'motivation' && message.data) {{
                            const quote = message.data.quote || 'Stay motivated!';
                            const goodCount = message.data.good_posture_count || 0;
                            const slouchCount = message.data.slouching_count || 0;
                            const percentage = message.data.good_percentage || 0;
                            
                            // Determine performance color
                            let perfColor = '#28a745'; // Green
                            if (percentage < 70) perfColor = '#ffc107'; // Yellow
                            if (percentage < 50) perfColor = '#dc3545'; // Red
                            
                            addMessage(`
                                <div>
                                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                                        <span style="font-size: 18px; margin-right: 6px;">🤖</span>
                                        <strong style="color: #1f77b4; font-weight: bold;">AI COACH SAYS:</strong>
                                        <span style="margin-left: auto; font-size: 11px; opacity: 0.7;">
                                            ${{new Date().toLocaleTimeString()}}
                                        </span>
                                    </div>
                                    <div style="background: rgba(31, 119, 180, 0.1); padding: 8px; border-radius: 4px; margin: 6px 0; border-left: 3px solid #1f77b4;">
                                        <em style="font-size: 14px; font-weight: bold;">"${{quote}}"</em>
                                    </div>
                                    <div style="display: flex; gap: 12px; font-size: 11px; font-weight: bold; opacity: 0.8;">
                                        <span>📊 Good: <strong>${{goodCount}}</strong></span>
                                        <span>📉 Slouch: <strong>${{slouchCount}}</strong></span>
                                        <span style="color: ${{perfColor}};">🎯 Performance: <strong>${{percentage}}%</strong></span>
                                    </div>
                                </div>
                            `, true);
                            
                        }} else if (message.type === 'connection') {{
                            addMessage(`
                                <div style="text-align: center; font-weight: bold; opacity: 0.7;">
                                    📋 <strong>System:</strong> ${{message.message}}
                                </div>
                            `);
                        }} else if (message.type === 'pong') {{
                            console.log('🏓 Pong received - connection alive');
                        }}
                    }} catch (e) {{
                        console.error('❌ Error processing WebSocket message:', e);
                    }}
                }};
                
                ws.onclose = function(event) {{
                    console.log('🔴 WebSocket connection closed:', event);
                    updateStatus('🔴 Disconnected - Reconnecting...', false);
                    addMessage(`
                        <div style="text-align: center; color: #dc3545; font-weight: bold;">
                            ❌ <strong>Connection Lost</strong><br>
                            <small style="font-weight: normal; opacity: 0.8;">Attempting to reconnect in 3 seconds...</small>
                        </div>
                    `);
                    setTimeout(connectWebSocket, 3000);
                }};
                
                ws.onerror = function(error) {{
                    console.error('❌ WebSocket error:', error);
                    updateStatus('❌ Connection Error', false);
                }};
                
            }} catch (e) {{
                console.error('❌ Failed to create WebSocket:', e);
                updateStatus('❌ Failed to Connect', false);
                setTimeout(connectWebSocket, 5000);
            }}
        }}
        
        // Start connection immediately
        connectWebSocket();
        
        // Send ping every 30 seconds to keep connection alive
        setInterval(function() {{
            if (ws && ws.readyState === WebSocket.OPEN) {{
                ws.send('ping');
                console.log('🏓 Ping sent to keep connection alive');
            }}
        }}, 30000);
        
        console.log('🚀 WebSocket client initialized for live AI coaching');
        </script>
        """, height=400)
        
        # Show quote statistics
        st.markdown("---")
        st.markdown("**📊 AI Coach Statistics:**")
        
        try:
            if os.path.exists("motivation_quotes.json"):
                with open("motivation_quotes.json", 'r') as f:
                    data = json.load(f)
                    quotes = data.get('quotes', [])
                    
                    if quotes:
                        total_quotes = len(quotes)
                        
                        # Calculate average performance
                        total_good = sum(q.get('good_posture_count', 0) for q in quotes)
                        total_slouch = sum(q.get('slouching_count', 0) for q in quotes)
                        total_readings = total_good + total_slouch
                        avg_performance = (total_good / total_readings * 100) if total_readings > 0 else 0
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        
                        with col_stat1:
                            st.metric("Total Quotes", total_quotes)
                        
                        with col_stat2:
                            st.metric("Avg Performance", f"{avg_performance:.1f}%")
                        
                        with col_stat3:
                            st.metric("Total Readings", total_readings)
                        
                        # Show latest quote timestamp
                        if quotes:
                            latest_quote = quotes[-1]
                            latest_time = latest_quote.get('timestamp', 'Unknown')
                            st.info(f"🕒 Latest AI quote: {latest_time}")
                    else:
                        st.info("No AI coaching data available yet.")
            else:
                st.warning("Start video streaming to generate AI coaching quotes.")
                
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
        
                # WebSocket connection info (simplified)
        # st.markdown("---")
        # st.info("💡 Live AI coaching messages appear above via WebSocket")
        # st.info("🔌 WebSocket endpoint: ws://localhost:8001/ (dedicated AI Coach server)")
        
#         if st.button("🚀 Open WebSocket Test Page", key="open_ws_test"):
#             # Create a simple HTML file for WebSocket testing
#             html_content = """
# <!DOCTYPE html>
# <html>
# <head>
#     <title>AI Coach WebSocket Test</title>
#     <style>
#         body { font-family: Arial, sans-serif; margin: 20px; background: #f0f2f6; }
#         .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
#         .message { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #1f77b4; }
#         .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
#         .connected { background: #d4edda; color: #155724; }
#         .disconnected { background: #f8d7da; color: #721c24; }
#         #messages { max-height: 400px; overflow-y: auto; }
#     </style>
# </head>
# <body>
#     <div class="container">
#         <h1>🤖 AI Coach - Live WebSocket Feed</h1>
#         <div id="status" class="status disconnected">🔴 Disconnected</div>
#         <div id="messages"></div>
#     </div>

#     <script>
#         let ws = null;
#         const statusDiv = document.getElementById('status');
#         const messagesDiv = document.getElementById('messages');
        
#         function connectWebSocket() {
#             try {
#                 ws = new WebSocket('ws://localhost:8000/ws/motivation');
                
#                 ws.onopen = function() {
#                     console.log('🟢 Connected to AI Coach WebSocket');
#                     statusDiv.textContent = '🟢 Connected to AI Coach';
#                     statusDiv.className = 'status connected';
#                 };
                
#                 ws.onmessage = function(event) {
#                     try {
#                         const message = JSON.parse(event.data);
#                         console.log('📨 Received message:', message);
                        
#                         if (message.type === 'motivation' && message.data) {
#                             const messageDiv = document.createElement('div');
#                             messageDiv.className = 'message';
#                             messageDiv.innerHTML = `
#                                 <strong>🤖 AI Coach:</strong><br>
#                                 "${message.data.quote}"<br>
#                                 <small>📊 Good: ${message.data.good_posture_count} | Slouch: ${message.data.slouching_count} | Performance: ${message.data.good_percentage}%</small><br>
#                                 <small>⏰ ${new Date().toLocaleTimeString()}</small>
#                             `;
#                             messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
                            
#                             // Keep only last 10 messages
#                             while (messagesDiv.children.length > 10) {
#                                 messagesDiv.removeChild(messagesDiv.lastChild);
#                             }
#                         } else if (message.type === 'connection') {
#                             console.log('📋 Connection message:', message.message);
#                         }
#                     } catch (e) {
#                         console.error('❌ Error processing message:', e);
#                     }
#                 };
                
#                 ws.onclose = function() {
#                     console.log('🔴 WebSocket connection closed');
#                     statusDiv.textContent = '🔴 Disconnected - Reconnecting...';
#                     statusDiv.className = 'status disconnected';
#                     setTimeout(connectWebSocket, 3000);
#                 };
                
#                 ws.onerror = function(error) {
#                     console.error('❌ WebSocket error:', error);
#                     statusDiv.textContent = '❌ Connection Error';
#                     statusDiv.className = 'status disconnected';
#                 };
                
#             } catch (e) {
#                 console.error('❌ Failed to connect WebSocket:', e);
#                 setTimeout(connectWebSocket, 3000);
#             }
#         }
        
#         // Start connection
#         connectWebSocket();
        
#         // Add initial message
#         messagesDiv.innerHTML = '<div class="message">🔄 Waiting for AI coaching messages...</div>';
#     </script>
# </body>
# </html>
#             """
            
            # # Save HTML file
            # with open("websocket_test.html", "w") as f:
            #     f.write(html_content)
            
            # st.success("✅ Created websocket_test.html - Open this file in your browser to see live WebSocket messages!")
            # st.info("📂 File location: websocket_test.html in your project directory")
    
    # # Manual refresh only
    # if st.button("🔄 Refresh Now", key="manual_refresh"):
    #     st.rerun()

def dashboard_page():
    st.markdown('<h2 class="section-header">📊 Posture Health Dashboard</h2>', unsafe_allow_html=True)
    
    # Auto-fetch data on page load
    if 'dashboard_data' not in st.session_state:
        st.session_state.dashboard_data = None
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Real-time Posture Monitoring Analytics**")
        # Show video stream status
        st.info("⏸️ Video stream paused while viewing dashboard (optimized performance)")
    
    with col2:
        if st.button("🔄 Refresh Data", key="refresh_dashboard"):
            st.session_state.dashboard_data = None
            st.rerun()
    
    # Fetch dashboard data
    if st.session_state.dashboard_data is None:
        with st.spinner("📊 Loading dashboard analytics..."):
            status_code, response = make_api_request("/dashboard/data")
            
            if status_code == 200:
                st.session_state.dashboard_data = response
            else:
                st.error(f"❌ Failed to load dashboard data: {status_code}")
                st.json(response)
                return
    
    # Display visualizations if data is available
    if st.session_state.dashboard_data and "data" in st.session_state.dashboard_data:
        data = st.session_state.dashboard_data["data"]
        
        # Extract metrics
        posture_health_score = data.get('posture_health_score', 0)
        slouch_conversions = data.get('slouch_to_good_conversions', 0)
        consistency_index = data.get('consistency_index', 0)
        session_success_rate = data.get('session_success_rate', 0)
        recent_trend_score = data.get('recent_trend_score', 0)
        total_good_minutes = data.get('total_good_posture_minutes', 0)
        
        # Row 1: Main Health Score (Large Circular Progress)
        st.markdown("### 🎯 Overall Posture Health Score")
        
        # Create large circular progress bar for main health score
        fig_health = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = posture_health_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Health Score"},
            delta = {'reference': 75, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_health.update_layout(height=300, font={'size': 16})
        st.plotly_chart(fig_health, use_container_width=True)
        
        # Row 2: Three Key Metrics
        st.markdown("### 📈 Performance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Consistency Index - Circular Progress
            fig_consistency = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = consistency_index,
                title = {'text': "Consistency Index"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [{'range': [0, 100], 'color': "lightgray"}],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}
                }
            ))
            fig_consistency.update_layout(height=250, font={'size': 12})
            st.plotly_chart(fig_consistency, use_container_width=True)
        
        with col2:
            # Session Success Rate - Circular Progress
            fig_success = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = session_success_rate,
                title = {'text': "Session Success Rate"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#ff7f0e"},
                    'steps': [{'range': [0, 100], 'color': "lightgray"}],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}
                }
            ))
            fig_success.update_layout(height=250, font={'size': 12})
            st.plotly_chart(fig_success, use_container_width=True)
        
        with col3:
            # Recent Trend Score - Circular Progress
            fig_trend = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = recent_trend_score,
                title = {'text': "Recent Trend Score"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#2ca02c"},
                    'steps': [{'range': [0, 100], 'color': "lightgray"}],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 85}
                }
            ))
            fig_trend.update_layout(height=250, font={'size': 12})
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Row 3: Progress Bars for Conversions and Time
        st.markdown("### 📊 Activity Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            # Slouch to Good Conversions - Progress Bar
            st.markdown("**🔄 Slouch to Good Conversions**")
            conversion_progress = min(slouch_conversions / 20 * 100, 100)  # Assuming 20 is a good target
            st.progress(conversion_progress / 100)
            st.metric("Conversions", slouch_conversions, delta=f"{conversion_progress:.1f}% of target")
            
            # Create bar chart for conversions
            fig_conv = go.Figure(go.Bar(
                x=['Conversions'],
                y=[slouch_conversions],
                marker_color='#d62728',
                text=[slouch_conversions],
                textposition='auto',
            ))
            fig_conv.update_layout(
                title="Posture Corrections",
                height=200,
                showlegend=False,
                yaxis_title="Count"
            )
            st.plotly_chart(fig_conv, use_container_width=True)
        
        with col2:
            # Total Good Posture Minutes - Progress Bar
            st.markdown("**⏱️ Good Posture Time**")
            time_progress = min(total_good_minutes / 120 * 100, 100)  # Assuming 120 min is daily target
            st.progress(time_progress / 100)
            st.metric("Good Posture Minutes", f"{total_good_minutes:.1f}", delta=f"{time_progress:.1f}% of daily target")
            
            # Create area chart for time visualization
            fig_time = go.Figure(go.Indicator(
                mode = "number+delta",
                value = total_good_minutes,
                title = {'text': "Minutes Today"},
                delta = {'reference': 60, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
                number = {'suffix': " min"}
            ))
            fig_time.update_layout(height=200)
            st.plotly_chart(fig_time, use_container_width=True)
        
        # Summary Cards
        st.markdown("### 📋 Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">🎯</h3>
                <h2 style="margin: 5px 0; color: white;">{posture_health_score:.1f}%</h2>
                <p style="margin: 0; color: white;">Health Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">🔄</h3>
                <h2 style="margin: 5px 0; color: white;">{slouch_conversions}</h2>
                <p style="margin: 0; color: white;">Corrections</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">📈</h3>
                <h2 style="margin: 5px 0; color: white;">{consistency_index:.1f}%</h2>
                <p style="margin: 0; color: white;">Consistency</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">⏱️</h3>
                <h2 style="margin: 5px 0; color: white;">{total_good_minutes:.0f}</h2>
                <p style="margin: 0; color: white;">Good Minutes</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Metadata info
        metadata = st.session_state.dashboard_data.get("metadata", {})
        st.markdown("---")
        st.info(f"📊 **Data Source**: {metadata.get('source', 'Unknown')} | **Last Updated**: {st.session_state.dashboard_data.get('generated_at', 'Unknown')}")
        
        # Manual video control option
        st.markdown("### 🎬 Video Stream Control")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Resume Video Stream", key="manual_resume_video"):
                with st.spinner("Resuming video stream..."):
                    control_video_for_page("video")
                    st.success("✅ Video stream resumed manually")
        
        with col2:
            if st.button("⏸️ Pause Video Stream", key="manual_pause_video"):
                with st.spinner("Pausing video stream..."):
                    control_video_for_page("dashboard")
                    st.success("✅ Video stream paused manually")
        
        # Optional: Raw data in expander
        with st.expander("🔍 View Raw Data"):
            st.json(st.session_state.dashboard_data)
    
    else:
        st.warning("⚠️ No dashboard data available. Please ensure the posture monitoring system is running.")

def chat_page():
    st.markdown('<h2 class="section-header">🤖 Chat Interface</h2>', unsafe_allow_html=True)
    
    # Show video stream status
    st.info("⏸️ Video stream paused while using chat interface (optimized performance)")
    
    # Chat history display
    st.subheader("💬 Chat History")
    if st.button("Load Chat History", key="load_chat"):
        with st.spinner("Loading chat history..."):
            status_code, response = make_api_request("/chat/history")
            
            if status_code == 200:
                st.success("✅ Chat history loaded!")
                
                conversations = response.get("conversations", [])
                if conversations:
                    for i, conv in enumerate(conversations[-5:]):  # Show last 5
                        with st.expander(f"Conversation {i+1} - {conv.get('timestamp', 'Unknown time')}"):
                            st.write("**User:**", conv.get('user_message', ''))
                            st.write("**Assistant:**", conv.get('assistant_response', ''))
                else:
                    st.info("No chat history found.")
                    
                with st.expander("📋 Raw Response"):
                    st.json(response)
            else:
                st.error(f"❌ Failed to load chat history: {status_code}")
                st.json(response)
    
    # Send message
    st.subheader("📝 Send Message")
    user_message = st.text_area("Enter your message:", placeholder="Ask about posture, ergonomics, or health...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Send Message", key="send_message"):
            if user_message.strip():
                with st.spinner("Sending message..."):
                    data = {"message": user_message}
                    status_code, response = make_api_request("/chat/message", method="POST", data=data)
                    
                    if status_code == 200:
                        st.success("✅ Message sent successfully!")
                        st.write("**Response:**", response.get("response", ""))
                        
                        with st.expander("📋 Full Response"):
                            st.json(response)
                    else:
                        st.error(f"❌ Failed to send message: {status_code}")
                        st.json(response)
            else:
                st.warning("Please enter a message.")
    
    with col2:
        if st.button("Clear Chat History", key="clear_chat"):
            with st.spinner("Clearing chat history..."):
                status_code, response = make_api_request("/chat/history", method="DELETE")
                
                if status_code == 200:
                    st.success("✅ Chat history cleared!")
                    st.json(response)
                else:
                    st.error(f"❌ Failed to clear chat history: {status_code}")
                    st.json(response)

def analysis_page():
    st.markdown('<h2 class="section-header">📈 AI Posture Analysis & Reports</h2>', unsafe_allow_html=True)
    
    # Initialize session state for analysis
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'analysis_loading' not in st.session_state:
        st.session_state.analysis_loading = False
    
    # Main analysis section
    st.markdown("### 🤖 AI-Powered Posture Analysis")
    st.info("Generate a comprehensive AI analysis of your posture data with personalized recommendations.")
    st.info("⏸️ Video stream paused while viewing analysis (optimized performance)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🔍 Generate AI Analysis Report", key="generate_analysis", type="primary"):
            st.session_state.analysis_loading = True
            st.session_state.analysis_data = None
            st.rerun()
    
    with col2:
        if st.session_state.analysis_data:
            if st.button("🔄 Generate New Analysis", key="refresh_analysis"):
                st.session_state.analysis_loading = True
                st.session_state.analysis_data = None
                st.rerun()
    
    # Handle analysis generation
    if st.session_state.analysis_loading:
        with st.spinner("🧠 AI is analyzing your posture data... This may take up to 69 seconds."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Show progress updates
            for i in range(10):
                progress_bar.progress((i + 1) / 10)
                if i < 3:
                    status_text.text("📊 Collecting posture data...")
                elif i < 6:
                    status_text.text("🤖 AI analyzing patterns...")
                else:
                    status_text.text("📝 Generating recommendations...")
                time.sleep(0.5)
            
            # Make the actual API call
            status_code, response = make_api_request("/analyze/report", method="POST")
            
            progress_bar.empty()
            status_text.empty()
            
            if status_code == 200:
                st.session_state.analysis_data = response
                st.session_state.analysis_loading = False
                st.success("✅ AI Analysis completed successfully!")
                st.rerun()
            else:
                st.session_state.analysis_loading = False
                st.error(f"❌ Failed to generate analysis: {status_code}")
                st.json(response)
                return
    
    # Display analysis results
    if st.session_state.analysis_data:
        analysis = st.session_state.analysis_data.get("analysis", {})
        analysis_response = analysis.get("analysis_response", "")
        
        if analysis_response:
            st.markdown("### 🎯 AI Analysis Results")
            
            # Create a compact container for the analysis
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       padding: 15px; border-radius: 8px; margin: 5px 0;">
                <h4 style="color: white; margin: 0;">🤖 AI Coach Analysis</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Display the analysis in a compact way
            try:
                st.markdown(f"""
                <div style="background: var(--background-color, #f8f9fa); 
                           color: var(--text-color, #333333);
                           padding: 15px; border-radius: 8px; 
                           border-left: 4px solid #667eea; margin: 5px 0;
                           border: 1px solid var(--border-color, #e9ecef);">
                    <div style="white-space: pre-wrap; font-size: 15px; line-height: 1.5;
                               color: inherit;">
                        {analysis_response}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                # Fallback to native Streamlit styling
                st.info("🤖 **AI Coach Analysis:**")
                st.write(analysis_response)
            
            # Compact metadata and actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Generated", 
                         datetime.fromisoformat(analysis.get("timestamp", "")).strftime("%H:%M:%S") 
                         if analysis.get("timestamp") else "Unknown")
            
            with col2:
                st.metric("Status", "✅ Complete")
            
            with col3:
                st.metric("Type", "AI-Powered")
            
            # Compact action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💬 Discuss with AI Coach", key="chat_about_analysis"):
                    st.info("💡 Go to the Chat Interface to ask follow-up questions about your analysis!")
            
            with col2:
                if st.button("📊 View Dashboard", key="view_dashboard"):
                    st.info("💡 Check the Dashboard Data page for detailed metrics!")
            
            with col3:
                if st.button("💬 Ask Follow-up", key="ask_followup"):
                    st.info("💡 Go to the Chat Interface to ask follow-up questions about your analysis!")
        
        # Expandable section for technical details only
        with st.expander("🔍 View Technical Data"):
            st.json(st.session_state.analysis_data)
    
    else:
        # Show placeholder when no analysis is available
        st.markdown("---")
        st.info("🤖 No analysis available yet. Click 'Generate AI Analysis Report' to start!")
        
        # Show some example of what the analysis includes
        st.markdown("### 📋 What's Included in the AI Analysis:")
        st.markdown("""
        - **🎯 Overall Posture Assessment** - Comprehensive health score evaluation
        - **📈 Trend Analysis** - How your posture has improved or declined over time
        - **⚠️ Problem Areas** - Specific issues identified in your posture patterns
        - **💡 Personalized Recommendations** - Actionable steps to improve your posture
        - **🏆 Achievements** - Recognition of positive changes and improvements
        - **📊 Data Insights** - Statistical analysis of your posture monitoring data
        """)
        
        # Show recent activity if available
        st.markdown("### 📊 Quick Stats")
        dashboard_status, dashboard_response = make_api_request("/dashboard/data")
        if dashboard_status == 200 and "data" in dashboard_response:
            data = dashboard_response["data"]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Health Score", f"{data.get('posture_health_score', 0):.1f}%")
            with col2:
                st.metric("Consistency", f"{data.get('consistency_index', 0):.1f}%")
            with col3:
                st.metric("Success Rate", f"{data.get('session_success_rate', 0):.1f}%")
            with col4:
                st.metric("Good Minutes", f"{data.get('total_good_posture_minutes', 0):.0f}")
        else:
            st.warning("⚠️ No posture data available for analysis. Please ensure the monitoring system is running.")

def system_status_page():
    st.markdown('<h2 class="section-header">🔧 System Status</h2>', unsafe_allow_html=True)
    
    # Show video stream status
    st.info("⏸️ Video stream paused while viewing system status (optimized performance)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 File Status")
        if st.button("Check File Status", key="file_status"):
            with st.spinner("Checking file status..."):
                status_code, response = make_api_request("/files/status")
                
                if status_code == 200:
                    st.success("✅ File status retrieved!")
                    
                    files = response.get("files", {})
                    for filename, info in files.items():
                        with st.expander(f"📄 {filename}"):
                            st.json(info)
                            
                else:
                    st.error(f"❌ Failed to get file status: {status_code}")
                    st.json(response)
    
    with col2:
        st.subheader("🔄 Auto-Refresh Status")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Enable Auto-Refresh (every 5 seconds)")
        
        if auto_refresh:
            # Create a placeholder for status updates
            status_placeholder = st.empty()
            
            # Auto-refresh loop
            for i in range(12):  # Run for 1 minute
                with status_placeholder.container():
                    st.info(f"🔄 Auto-refresh {i+1}/12")
                    
                    # Check API health
                    status_code, response = make_api_request("/health")
                    if status_code == 200:
                        st.success("✅ API is healthy")
                    else:
                        st.error("❌ API is not responding")
                    
                    # Check video status
                    status_code, response = make_api_request("/video/status")
                    if status_code == 200:
                        video_status = response.get("status", "unknown")
                        if video_status == "running":
                            st.success(f"📹 Video stream: {video_status}")
                        else:
                            st.warning(f"📹 Video stream: {video_status}")
                
                time.sleep(5)

if __name__ == "__main__":
    main() 