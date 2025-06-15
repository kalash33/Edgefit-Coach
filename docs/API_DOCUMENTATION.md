# Edgefit-Coach API Documentation

## Overview

The Edgefit-Coach API is a comprehensive FastAPI backend that provides real-time posture monitoring, AI coaching, dashboard analytics, and interactive chat functionality. The API integrates with the existing posture detection system and provides WebSocket streaming for real-time updates.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   FastAPI        │◄──►│  main_webcam.py │
│   Dashboard     │    │   Server         │    │  (Video Stream) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Data Processing │
                    │  - posture_db.py │
                    │  - dashboard.py  │
                    │  - llm_handler   │
                    └──────────────────┘
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements_api.txt
```

### 2. Start the API Server
```bash
python api_server.py
```

### 3. Access API Documentation
- Interactive Docs: http://localhost:8000/docs
- OpenAPI Schema: http://localhost:8000/openapi.json

### 4. Test the API
```bash
python test_api_endpoints.py
```

## Endpoint Categories

## 2.1 Video Streaming & Motivation Endpoints

### Logic & Purpose
These endpoints manage the video streaming process and provide real-time motivation quotes via WebSocket. The system starts `main_webcam.py` as a subprocess and monitors the `motivation_quotes.json` file for new AI-generated quotes.

### Endpoints

#### `GET /video/start`
**Purpose**: Start the video streaming process with posture detection
**Logic**:
1. Check if video process is already running
2. Start `main_webcam.py` as subprocess
3. Initialize motivation monitoring thread
4. Return status confirmation

**Response**:
```json
{
  "status": "started",
  "message": "Video stream started successfully"
}
```

#### `GET /video/stop`
**Purpose**: Stop the video streaming process
**Logic**:
1. Check if video process exists and is running
2. Terminate the subprocess gracefully
3. Return status confirmation

#### `GET /video/status`
**Purpose**: Get current video stream status
**Response**:
```json
{
  "status": "running",
  "pid": 12345
}
```

#### `WebSocket /ws/motivation`
**Purpose**: Real-time motivation quote streaming
**Logic**:
1. Accept WebSocket connection
2. Monitor `motivation_quotes.json` for changes
3. Broadcast new quotes to all connected clients
4. Handle connection lifecycle (ping/pong)

**Message Format**:
```json
{
  "type": "motivation",
  "data": {
    "quote": "Keep your back straight!",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Frontend Integration
- Use WebSocket to receive real-time motivation quotes
- Display quotes in popup notifications or dedicated UI components
- Handle connection states (connected, disconnected, reconnecting)

---

## 2.2 Dashboard Data Endpoints

### Logic & Purpose
These endpoints generate dashboard metrics by processing posture data. The system runs `posture_db.py` to convert `posture_summary.json` into quantified metrics suitable for dashboard visualization.

### Endpoints

#### `GET /dashboard/data`
**Purpose**: Generate and return dashboard metrics
**Logic**:
1. Execute `PostureConverter` from `posture_db.py`
2. Process `posture_summary.json` → `endpoint_values.json`
3. Calculate 6 key metrics:
   - Posture Health Score (0-100%)
   - Slouch-to-Good Conversions (count)
   - Consistency Index (0-100%)
   - Session Success Rate (0-100%)
   - Recent Trend Score (0-100%)
   - Total Good Posture Minutes (count)
4. Return structured JSON response

**Response**:
```json
{
  "status": "success",
  "generated_at": "2024-01-01T12:00:00Z",
  "data": {
    "posture_health_score": 75.5,
    "slouch_to_good_conversions": 8,
    "consistency_index": 82.3,
    "session_success_rate": 68.0,
    "recent_trend_score": 78.2,
    "total_good_posture_minutes": 145.7
  },
  "metadata": {
    "description": "Real-time posture monitoring dashboard data",
    "endpoints_count": 6,
    "source": "posture_summary.json"
  }
}
```

#### `GET /dashboard/refresh`
**Purpose**: Force refresh of dashboard data
**Logic**: Same as `/dashboard/data` but explicitly for refresh operations

### Frontend Integration
- Call `/dashboard/data` on page load
- Use `/dashboard/refresh` for manual refresh buttons
- Display metrics using progress bars, circular indicators, or charts
- Color-code metrics based on thresholds (good/warning/poor)

---

## 2.3 Chat Interactive Panel Endpoints

### Logic & Purpose
Provides an AI-powered chat interface with context awareness and conversation history. The system maintains conversation context, applies system prompts to keep responses focused on health/posture topics, and logs all interactions.

### System Prompt
```
You are a professional posture and health coach assistant. Your role is to:
1. Provide helpful advice about posture, ergonomics, and workplace wellness
2. Analyze posture reports and give actionable recommendations
3. Answer questions about stretching, exercises, and healthy habits
4. Stay focused on health, posture, and wellness topics
5. Be encouraging, professional, and supportive
6. Keep responses concise and practical

Do not discuss topics unrelated to health, posture, or wellness.
```

### Endpoints

#### `POST /chat/message`
**Purpose**: Send chat message with context awareness
**Request Body**:
```json
{
  "message": "How can I improve my posture while working?"
}
```

**Logic**:
1. Load existing chat history from `chat_history.json`
2. Build context-aware prompt:
   - System prompt
   - Recent conversation history (last 20 exchanges)
   - Current user message
3. Send to LLM via `ask_llm()`
4. Create conversation entry with timestamp and ID
5. Save to chat history (keep last 100 conversations)
6. Return structured response

**Response**:
```json
{
  "response": "To improve your posture while working, try these tips: 1. Keep your feet flat on the floor...",
  "timestamp": "2024-01-01T12:00:00Z",
  "conversation_id": "conv_1704110400"
}
```

#### `GET /chat/history`
**Purpose**: Retrieve recent chat history
**Parameters**: `limit` (default: 20)
**Response**:
```json
{
  "status": "success",
  "conversations": [...],
  "total_conversations": 45,
  "system_prompt": "You are a professional posture..."
}
```

#### `DELETE /chat/history`
**Purpose**: Clear all chat history
**Logic**: Reinitialize `chat_history.json` with empty conversations array

### Frontend Integration
- Implement chat UI with message bubbles
- Send user messages to `/chat/message`
- Display AI responses with proper formatting
- Load chat history on page load
- Provide clear history option
- Handle loading states and error messages

---

## 2.4 Analysis & Report Endpoints

### Logic & Purpose
Generates comprehensive posture analysis reports and initiates AI-powered analysis. The system uses `dashboard_viewer.py` to create detailed reports, then feeds the report content to the AI for analysis and recommendations.

### Endpoints

#### `POST /analyze/report`
**Purpose**: Generate posture report and AI analysis
**Logic**:
1. Execute `PostureDashboard.process_and_generate_report()`
2. Generate `posture_report.txt` with comprehensive metrics
3. Read report content
4. Create AI analysis prompt with report data
5. Get AI analysis via `ask_llm()`
6. Save analysis as conversation in chat history
7. Return comprehensive response with analysis

**Response**:
```json
{
  "status": "success",
  "message": "Posture report analyzed successfully",
  "analysis": {
    "report_generated": true,
    "report_file": "posture_report.txt",
    "analysis_response": "Based on your posture report, I can see several positive trends...",
    "conversation_id": "analysis_1704110400",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "next_steps": {
    "chat_endpoint": "/chat/message",
    "description": "Continue conversation with follow-up questions about the analysis"
  }
}
```

#### `GET /analyze/report-file`
**Purpose**: Get raw posture report file content
**Response**:
```json
{
  "status": "success",
  "filename": "posture_report.txt",
  "content": "======================================\nPOSTURE MONITORING REPORT\n======================================\n...",
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### Frontend Integration
- Provide "Analyze" button that calls `/analyze/report`
- Display analysis results in dedicated section
- Redirect to chat interface after analysis
- Show report content in expandable section
- Handle long analysis responses with proper formatting

---

## Utility Endpoints

### `GET /`
Root endpoint with API information and available endpoints

### `GET /health`
Health check for all services (video stream, chat, dashboard, analysis)

### `GET /files/status`
Check status of important files (posture_summary.json, endpoint_values.json, etc.)

---

## Error Handling

All endpoints use consistent error handling:

```json
{
  "detail": "Error description",
  "status_code": 500
}
```

Common error codes:
- `404`: Resource not found
- `500`: Internal server error
- `422`: Validation error

---

## WebSocket Connection Management

### Connection Lifecycle
1. Client connects to `/ws/motivation`
2. Server sends welcome message
3. Client can send "ping" for keepalive
4. Server broadcasts motivation quotes to all connected clients
5. Server handles disconnections gracefully

### Message Types
- `connection`: Welcome message
- `motivation`: New motivation quote
- `pong`: Response to ping

---

## Data Flow

### Video Streaming Flow
```
main_webcam.py → motivation_quotes.json → WebSocket → Frontend
```

### Dashboard Data Flow
```
posture_summary.json → posture_db.py → endpoint_values.json → API → Frontend
```

### Chat Flow
```
User Message → Context Building → LLM → Response → chat_history.json → Frontend
```

### Analysis Flow
```
posture_summary.json → dashboard_viewer.py → posture_report.txt → LLM Analysis → Chat History → Frontend
```

---

## Testing

Use the interactive testing framework:

```bash
python test_api_endpoints.py
```

### Test Categories
1. **Server Health**: Basic connectivity and health checks
2. **Video Streaming**: Start/stop video, WebSocket connections
3. **Dashboard**: Data generation and refresh
4. **Chat**: Message sending, history management
5. **Analysis**: Report generation and AI analysis

---

## Production Considerations

### Security
- Configure CORS origins for production
- Add authentication/authorization
- Validate input data thoroughly
- Rate limiting for API endpoints

### Performance
- Implement caching for dashboard data
- Connection pooling for database operations
- Optimize WebSocket message broadcasting
- Monitor memory usage for long-running processes

### Monitoring
- Add logging for all operations
- Health check endpoints for monitoring
- Error tracking and alerting
- Performance metrics collection

---

## Frontend Integration Examples

### JavaScript WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/motivation');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'motivation') {
        showMotivationPopup(data.data.quote);
    }
};

// Keepalive
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);
```

### Dashboard Data Fetching
```javascript
async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard/data');
        const data = await response.json();
        updateDashboardMetrics(data.data);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}
```

### Chat Interface
```javascript
async function sendChatMessage(message) {
    try {
        const response = await fetch('/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        displayChatResponse(data.response);
    } catch (error) {
        console.error('Chat error:', error);
    }
}
```

This API provides a complete backend solution for the Edgefit-Coach application with real-time capabilities, AI integration, and comprehensive data processing. 