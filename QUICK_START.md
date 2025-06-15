# 🚀 Edgefit-Coach Quick Start Guide

## Overview
Edgefit-Coach is a comprehensive posture monitoring system with AI coaching capabilities, real-time video streaming, dashboard analytics, and chat interface.

## 🔧 Setup & Installation

### 1. Install Dependencies
```bash
# Install API server dependencies
pip install -r requirements_api.txt

# Install frontend test dependencies (optional)
pip install -r requirements_frontend.txt
```

### 2. Start the API Server
```bash
# Option 1: Using the start script (recommended)
python start_api.py

# Option 2: Direct server start
python api_server.py
```

The server will start on `http://localhost:8000`

## 🧪 Testing the System

### Option 1: Command Line Testing
```bash
# Run comprehensive API tests
python test_api_endpoints.py
```

### Option 2: Frontend Test Application
```bash
# Start both API server and frontend
python run_frontend_test.py

# Or manually start frontend (with API server already running)
streamlit run frontend_test.py
```

The frontend will be available at `http://localhost:8501`

## 📋 Available Endpoints

### 🏥 Health & Status
- `GET /health` - API health check
- `GET /files/status` - Check file status

### 📹 Video Streaming
- `GET /video/start` - Start video stream
- `GET /video/stop` - Stop video stream  
- `GET /video/status` - Check stream status
- `WebSocket /ws/motivation` - Real-time motivation quotes

### 📊 Dashboard Data
- `GET /dashboard/data` - Get dashboard metrics
- `GET /dashboard/refresh` - Refresh dashboard data

### 🤖 Chat Interface
- `POST /chat/message` - Send chat message
- `GET /chat/history` - Get chat history
- `DELETE /chat/history` - Clear chat history

### 📈 Analysis & Reports
- `POST /analyze/report` - Generate AI analysis report ✅ **FIXED**
- `GET /analyze/report-file` - Get raw report file

## 🔍 Key Features

### ✅ Fixed Issues
- **Analysis Endpoint**: The `/analyze/report` endpoint now works correctly with proper error handling and debugging
- **File Encoding**: Fixed UTF-8 encoding issues for report generation
- **Error Handling**: Added comprehensive error handling and logging

### 🎯 Core Functionality
1. **Real-time Posture Monitoring**: Video stream with posture detection
2. **Stretching Detection**: Overhead reach and side stretch detection
3. **AI Chat Interface**: Context-aware health coaching
4. **Dashboard Analytics**: Comprehensive posture metrics
5. **Report Generation**: Automated analysis with AI insights
6. **WebSocket Support**: Real-time motivation quotes

### 📊 Frontend Test Features
- **Interactive Dashboard**: Visual metrics and charts
- **Chat Interface**: Test AI conversations
- **Video Controls**: Start/stop video streaming
- **Analysis Testing**: Generate and view reports
- **System Monitoring**: Real-time status updates

## 🚀 Quick Test Workflow

1. **Start the system**:
   ```bash
   python run_frontend_test.py
   ```

2. **Test video streaming**:
   - Navigate to "📹 Video Streaming" in the frontend
   - Click "Start Video Stream"
   - Check status with "Check Stream Status"

3. **Test dashboard data**:
   - Go to "📊 Dashboard Data"
   - Click "Fetch Dashboard Data"
   - View metrics and charts

4. **Test chat interface**:
   - Navigate to "🤖 Chat Interface"
   - Send a message about posture or health
   - View AI response

5. **Test analysis (FIXED)**:
   - Go to "📈 Analysis & Reports"
   - Click "Generate & Analyze Report"
   - Wait ~30-60 seconds for AI analysis
   - View comprehensive report analysis

## 📁 File Structure
```
Edgefit-Coach/
├── api_server.py              # Main FastAPI server
├── frontend_test.py           # Streamlit test application
├── run_frontend_test.py       # Launcher script
├── test_api_endpoints.py      # Command-line testing
├── main_webcam.py            # Video streaming with posture detection
├── dashboard_viewer.py        # Report generation
├── llm_handler.py            # AI chat functionality
├── requirements_api.txt       # API dependencies
├── requirements_frontend.txt  # Frontend dependencies
└── QUICK_START.md            # This guide
```

## 🔧 Troubleshooting

### Analysis Endpoint Issues ✅ RESOLVED
- **Issue**: 500 Internal Server Error on `/analyze/report`
- **Solution**: Fixed file encoding, error handling, and LLM integration
- **Status**: Now working correctly with ~30-60 second response time

### Common Issues
1. **Port conflicts**: Ensure ports 8000 (API) and 8501 (frontend) are available
2. **Missing dependencies**: Run `pip install -r requirements_api.txt`
3. **File permissions**: Ensure write permissions for report generation
4. **LLM timeout**: Analysis endpoint may take 30-60 seconds (normal)

## 📚 API Documentation
For detailed API documentation, visit `http://localhost:8000/docs` when the server is running.

## 🎯 Next Steps
1. **Production Deployment**: Configure CORS, authentication, and security
2. **Frontend Integration**: Build production React/Vue.js frontend
3. **Database Integration**: Add persistent storage for metrics
4. **Mobile Support**: Develop mobile applications
5. **Advanced Analytics**: Add more sophisticated posture analysis

---

**Status**: ✅ All core functionality working, analysis endpoint fixed, comprehensive test suite available 