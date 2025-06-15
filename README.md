# Edgefit-Coach 🏋️‍♂️

**AI-Powered Real-Time Posture Monitoring & Coaching System**

Edgefit-Coach is a comprehensive posture monitoring application built for the Qualcomm Edge AI Developer Hackathon. It combines real-time computer vision, AI coaching, and interactive dashboards to help users maintain healthy posture while working.

> 📄 **[View Complete Project Presentation: EdgeFit Coach.pdf](./EdgeFit%20Coach.pdf)**  
> *Comprehensive overview with architecture diagrams, features, and technical specifications*

> 🎥 **[Watch Live Demo: Live Demo Presentation.mp4](https://drive.google.com/file/d/1gv0Hv2sh6jbghxgc2iXLexxYRfdu_8K0/view?usp=sharing)**  
> *Real-time demonstration of posture monitoring, AI coaching, and system features*


## 🌟 Key Features

### 🎯 Core Functionality
- **Real-Time Posture Detection**: Advanced MediaPipe-based pose estimation with ONNX optimization
- **AI-Powered Coaching**: Intelligent motivational quotes and personalized feedback
- **Stretching Exercise Detection**: Automatic recognition of overhead reach and side stretch exercises
- **Desktop Notifications**: Cross-platform notifications (Windows Toast, Linux notify2)
- **Interactive Dashboard**: Comprehensive analytics with 6 key posture metrics
- **Chat Interface**: AI-powered health coaching conversations
- **WebSocket Streaming**: Real-time data updates and motivation quotes

### 📊 Analytics & Insights
- **Posture Health Score**: Overall posture quality (0-100%)
- **Slouch-to-Good Conversions**: Improvement tracking
- **Consistency Index**: Posture stability measurement
- **Session Success Rate**: Performance over time
- **Recent Trend Score**: Short-term progress tracking
- **Total Good Posture Minutes**: Cumulative healthy posture time

### 🔧 Technical Features
- **FastAPI Backend**: High-performance REST API with automatic documentation
- **Streamlit Frontend**: Interactive web interface for testing and monitoring
- **WebSocket Support**: Real-time bidirectional communication
- **ONNX Runtime**: Optimized model inference for edge devices
- **Cross-Platform**: Windows and Linux support
- **Headless Operation**: Can run without GUI for server deployments

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Webcam/Camera access
- Windows 10+ or Linux

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Edgefit-Coach
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python start_app.py
   ```

That's it! The application will automatically:
- Start the WebSocket server (port 8001)
- Launch the API server (port 8000) 
- Start the Streamlit frontend (port 8501)
- Begin posture monitoring with `main_webcam_headless1.py`
- Open your browser to `http://localhost:8501`

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │◄──►│   FastAPI        │◄──►│  Webcam Stream  │
│   Frontend      │    │   Server         │    │  (Headless)     │
│  (Port 8501)    │    │  (Port 8000)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │  WebSocket       │    │  AI Processing  │
                    │  Server          │    │  - LLM Handler  │
                    │  (Port 8001)     │    │  - Pose Analysis│
                    └──────────────────┘    │  - Notifications│
                                           └─────────────────┘
```

## 📁 Project Structure

```
Edgefit-Coach/
├── 🚀 start_app.py                 # Main application launcher
├── 🔧 api_server.py               # FastAPI backend server
├── 📹 main_webcam_headless1.py    # Headless posture monitoring
├── 🌐 websocket_server.py         # WebSocket communication
├── 🎨 frontend_test.py            # Streamlit web interface
├── 🤖 llm_handler.py              # AI chat and coaching
├── 📊 posture_db.py               # Data processing and analytics
├── 📈 dashboard_viewer.py         # Report generation
├── ⚙️ config.yaml                 # Configuration settings
├── 📋 requirements.txt            # Python dependencies
├── 📚 API_DOCUMENTATION.md        # Detailed API docs
├── 🚀 QUICK_START.md              # Quick setup guide
├── 📖 STARTUP_GUIDE.md            # Comprehensive startup guide
└── 📄 EdgeFit Coach.pdf           # Project presentation & overview
```

## 🔌 API Endpoints

### Health & Status
- `GET /health` - API health check
- `GET /files/status` - File system status

### Video Streaming
- `GET /video/start` - Start posture monitoring
- `GET /video/stop` - Stop monitoring
- `GET /video/status` - Check stream status
- `WebSocket /ws/motivation` - Real-time motivation quotes

### Dashboard Analytics
- `GET /dashboard/data` - Get comprehensive metrics
- `GET /dashboard/refresh` - Force data refresh

### AI Chat Interface
- `POST /chat/message` - Send chat message
- `GET /chat/history` - Retrieve conversation history
- `DELETE /chat/history` - Clear chat history

### Analysis & Reports
- `POST /analyze/report` - Generate AI analysis report
- `GET /analyze/report-file` - Download raw report

## 🎮 Usage Examples

### Starting the System
```bash
# Single command to start everything
python start_app.py
```

### Testing Individual Components
```bash
# Test API endpoints
python test_api_endpoints.py

# Run frontend only (requires API server running)
streamlit run frontend_test.py

# Start API server only
python api_server.py
```

### Configuration
Edit `config.yaml` to customize:
```yaml
api_key: "your-api-key"
model_server_base_url: "http://localhost:3001/api/v1"
workspace_slug: "edgefit"
stream: true
stream_timeout: 60
```

## 🔍 Key Components

### Posture Detection Engine
- **MediaPipe Integration**: Advanced pose landmark detection
- **ONNX Optimization**: Faster inference on edge devices
- **Real-time Processing**: 13+ FPS video analysis
- **Posture Classification**: Good posture vs. slouching detection

### AI Coaching System
- **Context-Aware Chat**: Health and posture-focused conversations
- **Motivational Quotes**: Dynamic, personalized encouragement
- **Performance Analysis**: Detailed posture reports with recommendations
- **Goal Setting**: Adaptive targets based on user progress

### Stretching Exercise Detection
- **Overhead Reach**: Both arms raised above head detection
- **Side Stretch**: Left/right side stretching recognition
- **Real-time Feedback**: Immediate exercise validation

### Analytics Dashboard
- **6 Core Metrics**: Comprehensive posture health indicators
- **Trend Analysis**: Historical performance tracking
- **Visual Charts**: Interactive data visualization
- **Export Capabilities**: Report generation and download

## 🛠️ Development

### Running Tests
```bash
# Comprehensive API testing
python test_api_endpoints.py

# WebSocket testing
python test_websocket_client.py

# Notification testing
python test_notifications.py
```

### Adding New Features
1. **API Endpoints**: Add to `api_server.py`
2. **Frontend Components**: Modify `frontend_test.py`
3. **Posture Logic**: Update `main_webcam_headless1.py`
4. **AI Features**: Extend `llm_handler.py`

### Dependencies
- **Core**: FastAPI, OpenCV, MediaPipe, Streamlit
- **AI**: Custom LLM integration
- **Notifications**: win10toast (Windows), notify2 (Linux)
- **Optimization**: ONNX Runtime
- **WebSocket**: websockets, uvicorn

## 🚨 Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 8000, 8001, 8501 are available
2. **Camera Access**: Check webcam permissions and availability
3. **Dependencies**: Run `pip install -r requirements.txt`
4. **Performance**: Enable ONNX Runtime for better performance

### System Requirements
- **CPU**: Multi-core processor recommended
- **RAM**: 4GB+ for optimal performance
- **Camera**: USB webcam or built-in camera
- **OS**: Windows 10+ or Linux with GUI support

## 📈 Performance Metrics

- **Video Processing**: 13+ FPS real-time analysis
- **Response Time**: <100ms for posture detection
- **AI Chat**: 30-60 seconds for detailed analysis
- **Memory Usage**: ~500MB typical operation
- **CPU Usage**: 15-25% on modern processors

## 🎯 Use Cases

### Personal Health
- **Remote Work**: Maintain good posture during long work sessions
- **Health Monitoring**: Track posture improvements over time
- **Exercise Guidance**: Learn proper stretching techniques

### Professional Applications
- **Corporate Wellness**: Deploy in office environments
- **Healthcare**: Physical therapy and rehabilitation support
- **Education**: Ergonomics training and awareness

## 🔮 Future Enhancements

- **Mobile App**: iOS/Android companion applications
- **Cloud Integration**: Multi-user dashboard and analytics
- **Advanced AI**: More sophisticated posture analysis
- **Wearable Integration**: Smartwatch and fitness tracker support
- **Team Features**: Group challenges and leaderboards

## 📋 Documentation

### 📄 Project Presentation
For a comprehensive overview of the project, including architecture, features, and technical details, see:
- **[EdgeFit Coach.pdf](EdgeFit%20Coach.pdf)** - Complete project presentation with visual diagrams, use cases, and technical specifications

### 📚 Additional Documentation
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Detailed API endpoint documentation
- **[QUICK_START.md](QUICK_START.md)** - Fast setup and testing guide
- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - Comprehensive startup instructions
- **[POSTURE_LOGGING_GUIDE.md](POSTURE_LOGGING_GUIDE.md)** - Posture detection and logging details
- **[STRETCHING_DETECTION_README.md](STRETCHING_DETECTION_README.md)** - Exercise detection algorithms
- **[LLM_USAGE.md](LLM_USAGE.md)** - AI integration and usage guide

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🤝 Contributing

Built for the Qualcomm Edge AI Developer Hackathon. Contributions and feedback are welcome!

---

**🚀 Get started in seconds with `python start_app.py`**
