#!/usr/bin/env python3
"""
FastAPI Server for Edgefit-Coach
Comprehensive backend with video streaming, dashboard, chat, and analysis endpoints.
"""

import asyncio
import json
import os
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

import cv2
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import local modules
from llm_handler import ask_llm, is_error_response
from posture_db import PostureConverter
from dashboard_viewer import PostureDashboard
from video_streamer_pose import start_pose_streaming, stop_pose_streaming, is_pose_streaming, get_pose_stream_url, get_pose_frame_generator

# Global variables for video streaming
video_process = None
motivation_queue = None  # Will be initialized in lifespan
connected_websockets = set()

# Global variables for subprocess management
websocket_process = None
streamlit_process = None

# Chat history storage
chat_history_file = "chat_history.json"
SYSTEM_PROMPT = """You are a professional posture and health coach assistant. Your role is to:
1. Provide helpful advice about posture, ergonomics, and workplace wellness
2. Analyze posture reports and give actionable recommendations
3. Answer questions about stretching, exercises, and healthy habits
4. Stay focused on health, posture, and wellness topics
5. Be encouraging, professional, and supportive
6. Keep responses concise and practical

Do not discuss topics unrelated to health, posture, or wellness. Always maintain a helpful and professional tone."""

def initialize_chat_history():
    """Initialize chat history file if it doesn't exist."""
    if not os.path.exists(chat_history_file):
        initial_data = {
            "system_prompt": SYSTEM_PROMPT,
            "conversations": [],
            "created": datetime.now().isoformat()
        }
        with open(chat_history_file, 'w') as f:
            json.dump(initial_data, f, indent=2)

def start_websocket_server():
    """Start the WebSocket server subprocess."""
    global websocket_process
    try:
        websocket_process = subprocess.Popen(
            ["python", "websocket_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return True
    except Exception as e:
        print(f"❌ Failed to start WebSocket server: {e}")
        return False

def start_streamlit_frontend():
    """Start the Streamlit frontend subprocess."""
    global streamlit_process
    try:
        streamlit_process = subprocess.Popen(
            ["python", "-m", "streamlit", "run", "frontend_test.py", "--server.port", "8501", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return True
    except Exception as e:
        print(f"❌ Failed to start Streamlit frontend: {e}")
        return False

def stop_subprocesses():
    """Stop all subprocess components."""
    global websocket_process, streamlit_process
    
    if websocket_process:
        try:
            websocket_process.terminate()
            websocket_process.wait(timeout=5)
            print("✅ WebSocket server stopped")
        except:
            websocket_process.kill()
            print("🔪 WebSocket server force killed")
    
    if streamlit_process:
        try:
            streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
            print("✅ Streamlit frontend stopped")
        except:
            streamlit_process.kill()
            print("🔪 Streamlit frontend force killed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global motivation_queue
    # Startup
    print("🛠️ Starting API Server...")
    
    # Initialize API components
    motivation_queue = asyncio.Queue(maxsize=10)  # Initialize queue in async context
    print("📬 Motivation queue initialized")
    initialize_chat_history()
    print("💬 Chat history initialized")
    print("✅ API Server ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down API Server...")
    stop_subprocesses()
    print("✅ API Server stopped")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Edgefit-Coach API",
    description="Real-time posture monitoring with AI coaching",
    version="1.0.0",
    lifespan=lifespan
)

# Note: Streamlit startup is now handled by start_app.py launcher
# This ensures proper startup order: WebSocket -> API -> Streamlit

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    conversation_id: str

class AnalysisRequest(BaseModel):
    generate_report: bool = True


# ============================================================================
# 2.1 VIDEO STREAMING & MOTIVATION ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Edgefit-Coach API Server",
        "version": "1.0.0",
        "endpoints": {
            "video_stream": "/video/stream",
            "motivation_websocket": "/ws/motivation",
            "dashboard_data": "/dashboard/data",
            "chat": "/chat/message",
            "analyze": "/analyze/report"
        }
    }

class PageControlRequest(BaseModel):
    page_name: str

@app.post("/video/page-control")
async def control_video_for_page(request: PageControlRequest):
    """Control video streaming based on current page."""
    page_name = request.page_name
    try:
        if page_name in ["dashboard", "analysis", "chat", "system", "other"]:
            # Stop video when accessing non-video pages
            if is_pose_streaming():
                stop_pose_streaming()
                page_descriptions = {
                    "dashboard": "dashboard",
                    "analysis": "analysis page", 
                    "chat": "chat interface",
                    "system": "system status",
                    "other": "other page"
                }
                description = page_descriptions.get(page_name, page_name)
                return {
                    "status": f"paused_for_{page_name}",
                    "message": f"Video stream paused while viewing {description}",
                    "page": page_name
                }
            else:
                return {
                    "status": "already_stopped",
                    "message": "Video stream was already stopped",
                    "page": page_name
                }
        
        elif page_name == "video":
            # Start video when accessing video page
            if not is_pose_streaming():
                success = start_pose_streaming()
                if success:
                    # Start motivation monitoring if not running
                    motivation_thread_running = any(thread.name == "motivation_monitor" for thread in threading.enumerate())
                    if not motivation_thread_running:
                        motivation_thread = threading.Thread(target=monitor_motivation_quotes, daemon=True, name="motivation_monitor")
                        motivation_thread.start()
                    
                    return {
                        "status": "resumed_for_video",
                        "message": "Video stream resumed for video page",
                        "stream_url": get_pose_stream_url(),
                        "page": page_name
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to resume video stream")
            else:
                return {
                    "status": "already_running",
                    "message": "Video stream was already running",
                    "stream_url": get_pose_stream_url(),
                    "page": page_name
                }
        
        else:
            # For other pages, maintain current state
            current_status = "running" if is_pose_streaming() else "stopped"
            return {
                "status": f"maintained_{current_status}",
                "message": f"Video stream state maintained for {page_name} page",
                "page": page_name
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to control video for page: {str(e)}")

@app.get("/video/start")
async def start_video_stream():
    """Start the video streaming process with pose detection."""
    try:
        if is_pose_streaming():
            return {"status": "already_running", "message": "Video stream is already active"}
        
        # Start the enhanced pose detection video streamer
        success = start_pose_streaming()
        
        if success:
            # Start motivation monitoring thread (only if not already running)
            motivation_thread_running = any(thread.name == "motivation_monitor" for thread in threading.enumerate())
            if not motivation_thread_running:
                motivation_thread = threading.Thread(target=monitor_motivation_quotes, daemon=True, name="motivation_monitor")
                motivation_thread.start()
                print("🎯 Motivation monitoring thread started")
            
            return {
                "status": "started", 
                "message": "Video stream started successfully with pose detection and posture monitoring",
                "stream_url": get_pose_stream_url(),
                "features": ["pose_detection", "posture_monitoring", "stretching_detection"],
                "motivation_monitoring": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start video stream")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start video stream: {str(e)}")

@app.get("/video/stop")
async def stop_video_stream():
    """Stop the video streaming process."""
    try:
        if is_pose_streaming():
            stop_pose_streaming()
            return {"status": "stopped", "message": "Video stream stopped successfully"}
        else:
            return {"status": "not_running", "message": "Video stream was not running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop video stream: {str(e)}")

@app.get("/video/status")
async def video_stream_status():
    """Get current video stream status."""
    if is_pose_streaming():
        return {
            "status": "running", 
            "stream_url": get_pose_stream_url(),
            "message": "Video stream with pose detection is active",
            "features": ["pose_detection", "posture_monitoring", "stretching_detection"]
        }
    else:
        return {"status": "stopped"}

def generate_video_frames():
    """Generate video frames for streaming."""
    while True:
        try:
            # Read the current frame from file
            if os.path.exists("current_frame.jpg"):
                with open("current_frame.jpg", "rb") as f:
                    frame_bytes = f.read()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Send a placeholder frame if no frame is available
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for video stream...", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error generating frame: {e}")
        
        time.sleep(0.033)  # ~30 FPS

@app.get("/video/stream")
async def video_stream():
    """Stream video frames as MJPEG with pose detection."""
    if is_pose_streaming():
        return StreamingResponse(
            get_pose_frame_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    else:
        # Fallback to old method if pose streamer is not running
        return StreamingResponse(
            generate_video_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

# Mount static files for HLS streaming
app.mount("/hls", StaticFiles(directory="data/processed"), name="hls")

@app.get("/hls/stream.m3u8")
async def get_hls_playlist():
    """Serve HLS playlist file."""
    playlist_path = "data/processed/stream.m3u8"
    if os.path.exists(playlist_path):
        return FileResponse(playlist_path, media_type="application/vnd.apple.mpegurl")
    else:
        raise HTTPException(status_code=404, detail="HLS stream not available")

@app.get("/hls/{filename}")
async def get_hls_segment(filename: str):
    """Serve HLS segment files."""
    segment_path = f"data/processed/{filename}"
    if os.path.exists(segment_path):
        if filename.endswith('.ts'):
            return FileResponse(segment_path, media_type="video/mp2t")
        elif filename.endswith('.m3u8'):
            return FileResponse(segment_path, media_type="application/vnd.apple.mpegurl")
        else:
            return FileResponse(segment_path)
    else:
        raise HTTPException(status_code=404, detail="Segment not found")

def monitor_motivation_quotes():
    """Monitor motivation_quotes.json for new quotes and broadcast via WebSocket."""
    motivation_file = "motivation_quotes.json"
    last_quote_count = 0
    
    while True:
        try:
            if os.path.exists(motivation_file):
                with open(motivation_file, 'r') as f:
                    data = json.load(f)
                    quotes = data.get('quotes', [])
                    
                    if len(quotes) > last_quote_count:
                        # New quote available
                        new_quote = quotes[-1]  # Get the latest quote
                        print(f"💬 New AI quote detected: {new_quote.get('quote', 'Unknown')}")
                        
                        # Add to motivation queue for WebSocket broadcasting
                        try:
                            if motivation_queue is not None:
                                motivation_queue.put_nowait(new_quote)
                                print(f"📤 Added quote to WebSocket queue: {new_quote.get('quote', '')[:50]}...")
                            else:
                                print("⚠️ Motivation queue not initialized yet")
                        except asyncio.QueueFull:
                            print("⚠️ Motivation queue is full, skipping quote")
                        except Exception as queue_error:
                            print(f"❌ Error adding to motivation queue: {queue_error}")
                        
                        last_quote_count = len(quotes)
            
            time.sleep(1)  # Check every 1 second for faster updates
            
        except Exception as e:
            print(f"❌ Error monitoring motivation quotes: {e}")
            time.sleep(5)

# Removed broadcast_motivation function - now using queue-based approach in WebSocket handler

@app.websocket("/ws/motivation")
async def motivation_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time motivation quotes."""
    await websocket.accept()
    connected_websockets.add(websocket)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "message": "Connected to AI Coach motivation stream",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(welcome_message)
        print(f"🔗 WebSocket client connected. Total clients: {len(connected_websockets)}")
        
        # Main loop to handle both incoming messages and outgoing motivation quotes
        while True:
            try:
                # Check for new motivation quotes (non-blocking)
                try:
                    if motivation_queue is not None:
                        new_quote = motivation_queue.get_nowait()
                        # Send the new quote to this client
                        quote_message = {
                            "type": "motivation",
                            "data": {
                                "quote": new_quote.get('quote', ''),
                                "timestamp": new_quote.get('timestamp', ''),
                                "good_percentage": new_quote.get('good_percentage', 0),
                                "good_posture_count": new_quote.get('good_posture_count', 0),
                                "slouching_count": new_quote.get('slouching_count', 0)
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send_json(quote_message)
                        print(f"📤 Sent AI quote to WebSocket client: {new_quote.get('quote', '')[:50]}...")
                    
                except asyncio.QueueEmpty:
                    pass  # No new quotes
                
                # Handle incoming messages with timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    if data == "ping":
                        await websocket.send_json({
                            "type": "pong", 
                            "timestamp": datetime.now().isoformat()
                        })
                except asyncio.TimeoutError:
                    pass  # No incoming message, continue loop
                except WebSocketDisconnect:
                    break
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
                break
            
    except WebSocketDisconnect:
        pass
    finally:
        connected_websockets.discard(websocket)
        print(f"🔌 WebSocket client disconnected. Remaining clients: {len(connected_websockets)}")


# ============================================================================
# 2.2 DASHBOARD DATA ENDPOINT
# ============================================================================

@app.get("/dashboard/data")
async def get_dashboard_data():
    """
    Get dashboard data by first running posture_db.py to generate endpoint_values.json,
    then returning the contents as JSON response.
    """
    try:
        # Step 1: Run posture_db.py to generate endpoint_values.json
        print("📊 Generating dashboard data...")
        converter = PostureConverter()
        
        if not converter.convert_to_endpoints():
            raise HTTPException(status_code=500, detail="Failed to generate endpoint values")
        
        # Step 2: Read the generated endpoint_values.json
        endpoint_values_file = "endpoint_values.json"
        if not os.path.exists(endpoint_values_file):
            raise HTTPException(status_code=404, detail="Endpoint values file not found")
        
        with open(endpoint_values_file, 'r') as f:
            endpoint_data = json.load(f)
        
        # Step 3: Add metadata
        response_data = {
            "status": "success",
            "generated_at": datetime.now().isoformat(),
            "data": endpoint_data,
            "metadata": {
                "description": "Real-time posture monitoring dashboard data",
                "endpoints_count": len(endpoint_data),
                "source": "posture_summary.json"
            }
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard data: {str(e)}")

@app.get("/dashboard/refresh")
async def refresh_dashboard_data():
    """Force refresh of dashboard data."""
    return await get_dashboard_data()


# ============================================================================
# 2.3 CHAT INTERACTIVE PANEL ENDPOINT
# ============================================================================

def load_chat_history() -> dict:
    """Load chat history from JSON file."""
    try:
        with open(chat_history_file, 'r') as f:
            return json.load(f)
    except:
        initialize_chat_history()
        with open(chat_history_file, 'r') as f:
            return json.load(f)

def save_chat_history(chat_data: dict):
    """Save chat history to JSON file."""
    with open(chat_history_file, 'w') as f:
        json.dump(chat_data, f, indent=2)

def build_context_prompt(message: str, conversation_history: list) -> str:
    """Build a prompt with system context and conversation history."""
    context_parts = [SYSTEM_PROMPT, "\n\nConversation History:"]
    
    # Add recent conversation history (last 10 exchanges)
    recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
    
    for entry in recent_history:
        context_parts.append(f"User: {entry['user_message']}")
        context_parts.append(f"Assistant: {entry['assistant_response']}")
    
    context_parts.append(f"\nCurrent User Message: {message}")
    context_parts.append("\nPlease respond as a professional posture and health coach:")
    
    return "\n".join(context_parts)

@app.post("/chat/message")
async def chat_message(chat_msg: ChatMessage):
    """
    Handle chat messages with context awareness and system prompts.
    Maintains conversation history and provides contextual responses.
    """
    try:
        # Load existing chat history
        chat_data = load_chat_history()
        
        # Build context-aware prompt
        context_prompt = build_context_prompt(chat_msg.message, chat_data['conversations'])
        
        # Get response from LLM
        response = ask_llm(context_prompt)
        
        if is_error_response(response):
            raise HTTPException(status_code=500, detail=f"LLM Error: {response}")
        
        # Create conversation entry
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": chat_msg.message,
            "assistant_response": response,
            "conversation_id": f"conv_{int(time.time())}"
        }
        
        # Add to history
        chat_data['conversations'].append(conversation_entry)
        
        # Keep only last 100 conversations to prevent file from growing too large
        if len(chat_data['conversations']) > 100:
            chat_data['conversations'] = chat_data['conversations'][-100:]
        
        # Save updated history
        save_chat_history(chat_data)
        
        return ChatResponse(
            response=response,
            timestamp=conversation_entry['timestamp'],
            conversation_id=conversation_entry['conversation_id']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/chat/history")
async def get_chat_history(limit: int = 20):
    """Get recent chat history."""
    try:
        chat_data = load_chat_history()
        recent_conversations = chat_data['conversations'][-limit:] if len(chat_data['conversations']) > limit else chat_data['conversations']
        
        return {
            "status": "success",
            "conversations": recent_conversations,
            "total_conversations": len(chat_data['conversations']),
            "system_prompt": chat_data['system_prompt']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.delete("/chat/history")
async def clear_chat_history():
    """Clear all chat history."""
    try:
        initialize_chat_history()
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")


# ============================================================================
# 2.4 ANALYZE BUTTON ENDPOINT
# ============================================================================

@app.post("/analyze/report")
async def analyze_posture_report(request: AnalysisRequest = None):
    """
    Generate posture analysis report and initiate chat with report context.
    First calls dashboard_viewer.py to generate posture_report.txt,
    then uses that as initial context for chat interface.
    """
    try:
        # Step 1: Generate posture report using dashboard_viewer.py
        print("📊 Generating posture analysis report...")
        
        dashboard = PostureDashboard()
        success = dashboard.process_and_generate_report()
        
        if not success:
            print("❌ Dashboard report generation failed")
            raise HTTPException(status_code=500, detail="Failed to generate posture report")
        
        print("✅ Dashboard report generated successfully")
        
        # Step 2: Read the generated posture_report.txt
        report_file = "posture_report.txt"
        if not os.path.exists(report_file):
            print(f"❌ Report file not found: {report_file}")
            raise HTTPException(status_code=404, detail="Posture report file not found")
        
        print(f"✅ Report file found: {report_file}")
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            print(f"✅ Report content read successfully ({len(report_content)} characters)")
        except Exception as read_error:
            print(f"❌ Error reading report file: {read_error}")
            raise HTTPException(status_code=500, detail=f"Error reading report file: {str(read_error)}")
        
        # Step 3: Create initial chat context with the report
        initial_prompt = f"""I have generated a comprehensive posture monitoring report. Please analyze this report and provide:

1. Key insights and observations
2. Areas of concern or improvement needed
3. Specific actionable recommendations
4. Positive aspects to acknowledge

Here is the complete posture report:

{report_content}

Please provide a detailed analysis and recommendations based on this data."""
        
        print("📝 Sending report to LLM for analysis...")
        
        # Step 4: Get AI analysis of the report
        try:
            analysis_response = ask_llm(initial_prompt)
            print("✅ LLM analysis completed")
        except Exception as llm_error:
            print(f"❌ LLM analysis failed: {llm_error}")
            raise HTTPException(status_code=500, detail=f"LLM analysis error: {str(llm_error)}")
        
        if is_error_response(analysis_response):
            print(f"❌ LLM returned error response: {analysis_response}")
            raise HTTPException(status_code=500, detail=f"Analysis error: {analysis_response}")
        
        # Step 5: Save this as the initial conversation in chat history
        try:
            chat_data = load_chat_history()
            
            analysis_conversation = {
                "timestamp": datetime.now().isoformat(),
                "user_message": "Please analyze my posture report and provide recommendations.",
                "assistant_response": analysis_response,
                "conversation_id": f"analysis_{int(time.time())}",
                "type": "analysis",
                "report_content": report_content
            }
            
            chat_data['conversations'].append(analysis_conversation)
            save_chat_history(chat_data)
            print("✅ Analysis saved to chat history")
        except Exception as chat_error:
            print(f"⚠️ Warning: Could not save to chat history: {chat_error}")
            # Don't fail the entire request if chat history fails
        
        # Step 6: Return comprehensive response
        return {
            "status": "success",
            "message": "Posture report analyzed successfully",
            "analysis": {
                "report_generated": True,
                "report_file": report_file,
                "analysis_response": analysis_response,
                "conversation_id": f"analysis_{int(time.time())}",
                "timestamp": datetime.now().isoformat()
            },
            "next_steps": {
                "chat_endpoint": "/chat/message",
                "description": "Continue conversation with follow-up questions about the analysis"
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error in analyze_posture_report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/analyze/report-file")
async def get_report_file():
    """Get the raw posture report file content."""
    try:
        report_file = "posture_report.txt"
        if not os.path.exists(report_file):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        with open(report_file, 'r') as f:
            content = f.read()
        
        return {
            "status": "success",
            "filename": report_file,
            "content": content,
            "generated_at": datetime.fromtimestamp(os.path.getmtime(report_file)).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report file: {str(e)}")


# ============================================================================
# HEALTH CHECK AND UTILITY ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for all components."""
    global websocket_process, streamlit_process
    
    # Check subprocess status
    websocket_status = "running" if websocket_process and websocket_process.poll() is None else "stopped"
    streamlit_status = "running" if streamlit_process and streamlit_process.poll() is None else "stopped"
    video_status = "running" if video_process and video_process.poll() is None else "stopped"
    
    # Overall system status
    all_running = all([
        websocket_status == "running",
        streamlit_status == "running"
    ])
    
    return {
        "status": "healthy" if all_running else "partial",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api_server": "running",
            "websocket_server": websocket_status,
            "streamlit_frontend": streamlit_status,
            "video_stream": video_status,
            "chat_system": "active",
            "dashboard": "active",
            "analysis": "active"
        },
        "urls": {
            "frontend": "http://localhost:8501",
            "api_docs": "http://localhost:8000/docs",
            "websocket": "ws://localhost:8001"
        }
    }

@app.get("/files/status")
async def check_file_status():
    """Check status of important files."""
    files_to_check = [
        "posture_summary.json",
        "endpoint_values.json",
        "posture_report.txt",
        "chat_history.json",
        "motivation_quotes.json"
    ]
    
    file_status = {}
    for file_name in files_to_check:
        if os.path.exists(file_name):
            stat = os.stat(file_name)
            file_status[file_name] = {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            file_status[file_name] = {"exists": False}
    
    return {
        "status": "success",
        "files": file_status,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("🛠️ Starting Edgefit-Coach API Server...")
    print("💡 For complete application startup, use: python start_app.py")
    print("=" * 50)
    
    # Set environment for better subprocess handling
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to prevent subprocess issues
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API server...")
        stop_subprocesses()
    except Exception as e:
        print(f"❌ Error running API server: {e}")
        stop_subprocesses() 