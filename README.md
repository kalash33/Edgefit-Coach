# Edgefit-Coach: AI-Powered Posture Monitoring System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)]()

A comprehensive real-time posture monitoring application with AI coaching, desktop notifications, and web-based dashboard interface. Built with MediaPipe, FastAPI, Streamlit, and ONNX for optimized performance.

## 🌟 Features

### 🎯 **Core Functionality**
- **Real-time Posture Detection**: MediaPipe-based pose estimation with 30+ landmark tracking
- **AI-Powered Coaching**: Intelligent motivational quotes and posture correction suggestions
- **Desktop Notifications**: Cross-platform popup notifications for posture alerts
- **Stretching Detection**: Automatic recognition of overhead reach and side stretch exercises
- **Performance Analytics**: Comprehensive metrics and trend analysis

### 🖥️ **User Interfaces**
- **Web Dashboard**: Beautiful Streamlit-based interface with real-time charts
- **Live Video Stream**: Real-time pose visualization with overlay annotations
- **AI Chat Interface**: Interactive conversation with posture coaching AI
- **System Monitoring**: Health checks and component status monitoring

### ⚡ **Performance & Optimization**
- **ONNX Model Support**: Optimized inference with NPU acceleration
- **Qualcomm NPU Integration**: Hardware-accelerated pose detection
- **Efficient Logging**: Discrete 30-second window-based data collection
- **WebSocket Communication**: Real-time bidirectional data streaming

## 📁 Project Structure

```
Edgefit-Coach/
├── src/                          # Source code
│   ├── core/                     # Core posture detection logic
│   │   ├── main_webcam.py        # GUI-based monitoring
│   │   ├── main_webcam_headless.py  # Headless monitoring
│   │   └── main_webcam_headless1.py # Enhanced with notifications
│   ├── api/                      # API and WebSocket servers
│   │   ├── api_server.py         # FastAPI REST API
│   │   └── websocket_server.py   # WebSocket communication
│   ├── frontend/                 # Web interface
│   │   └── frontend_test.py      # Streamlit dashboard
│   ├── utils/                    # Utility functions
│   │   ├── llm_handler.py        # AI communication
│   │   ├── posture_db.py         # Data processing
│   │   ├── dashboard_viewer.py   # Report generation
│   │   └── video_streamer*.py    # Video streaming
│   └── models/                   # AI models and inference
│       ├── *.onnx               # Pre-trained models
│       └── main_*.py            # Model implementations
├── scripts/                      # Startup and utility scripts
├── tests/                        # Test files
├── docs/                         # Documentation
├── config/                       # Configuration files
├── temp/                         # Temporary data files
└── logs/                         # Application logs
```

## 🚀 Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd Edgefit-Coach

# Install dependencies
pip install -r requirements.txt

# For Windows notifications
pip install win10toast plyer

# For Linux notifications  
pip install notify2
```

### 2. **Configuration**

Create `config/config.yaml`:
```yaml
model_server_base_url: "your-ai-api-url"
api_key: "your-api-key"
workspace_slug: "your-workspace"
```

### 3. **Launch Application**

```bash
# Start all components (Recommended)
python edgefit_coach.py web

# Or start components individually:
python src/api/websocket_server.py     # Terminal 1
python src/api/api_server.py           # Terminal 2  
streamlit run src/frontend/frontend_test.py --server.port 8501  # Terminal 3
```

### 4. **Access Interfaces**

- **🎨 Web Dashboard**: http://localhost:8501
- **🔧 API Documentation**: http://localhost:8000/docs
- **🔌 WebSocket**: ws://localhost:8001

## 📖 Usage Guide

### **Posture Monitoring Modes**

#### 🖥️ **GUI Mode** (With Visual Interface)
```bash
python src/core/main_webcam.py
```
- Full GUI with video display
- Real-time posture overlays
- Interactive controls

#### 🤖 **Headless Mode** (Background Processing)
```bash
python src/core/main_webcam_headless1.py --headless
```
- Background processing only
- Desktop notifications
- Optimized performance

#### 🌐 **Web Stream Mode** (Browser Interface)
```bash
python scripts/start_app.py
```
- Web-based video streaming
- Dashboard analytics
- AI chat interface

### **Key Features Usage**

#### 📊 **Dashboard Analytics**
- View real-time posture metrics
- Analyze performance trends
- Generate comprehensive reports
- Export data for external analysis

#### 🤖 **AI Coaching**
- Receive motivational quotes every 30 seconds
- Get personalized posture recommendations
- Chat with AI for specific advice
- Performance-based feedback intensity

#### 🔔 **Desktop Notifications**
- **Low Priority** (>70% good posture): Encouragement
- **Normal Priority** (40-70%): Gentle reminders
- **Critical Priority** (<40%): Urgent corrections

## 🛠️ API Reference

### **Core Endpoints**

#### **Health & Status**
- `GET /health` - System health check
- `GET /files/status` - File system status

#### **Video Streaming**
- `POST /video/start` - Start video stream
- `POST /video/stop` - Stop video stream
- `GET /video/status` - Stream status
- `POST /video/page-control` - Control based on page

#### **Dashboard Data**
- `GET /dashboard/data` - Get analytics data
- `POST /dashboard/refresh` - Refresh metrics

#### **AI Chat Interface**
- `POST /chat/message` - Send message to AI
- `GET /chat/history` - Get conversation history
- `DELETE /chat/history` - Clear chat history

#### **Analysis & Reports**
- `POST /analyze/report` - Generate AI analysis
- `GET /analyze/report-file` - Get report file

### **WebSocket Communication**
- **Endpoint**: `ws://localhost:8001/`
- **Real-time motivation quotes**
- **Performance statistics**
- **Connection status updates**

## 🧪 Testing

### **Run All Tests**
```bash
# Test desktop notifications
python tests/test_notifications.py

# Test API endpoints
python tests/test_api_endpoints.py

# Test WebSocket connection
python tests/test_websocket_client.py
```

### **Performance Benchmarking**
```bash
# Compare model performance
python src/models/benchmark_comparison.py

# Test NPU acceleration
python src/models/test_qualcomm_npu.py
```

## ⚙️ Configuration

### **Environment Variables**
```bash
PYTHONIOENCODING=utf-8          # Character encoding
EDGEFIT_LOG_LEVEL=INFO          # Logging level
EDGEFIT_DATA_DIR=./temp         # Data directory
```

### **Model Configuration**
- **Detection Confidence**: 0.5 (adjustable)
- **Tracking Confidence**: 0.5 (adjustable)
- **Log Interval**: 3 seconds
- **Window Duration**: 30 seconds
- **Notification Timeout**: 8 seconds

## 🔧 Troubleshooting

### **Common Issues**

#### **Notifications Not Appearing**
```bash
# Windows: Check notification settings
# Settings > System > Notifications & actions

# Linux: Install notify2
pip install notify2

# Test notifications
python tests/test_notifications.py
```

#### **Camera Not Detected**
```bash
# Check available cameras
python -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).isOpened()])"
```

#### **API Connection Issues**
```bash
# Check if ports are available
netstat -an | findstr "8000 8001 8501"

# Restart all services
python scripts/start_app.py
```

#### **Model Loading Errors**
```bash
# Verify ONNX models exist
ls src/models/*.onnx

# Test model loading
python src/models/test_model_info.py
```

## 📊 Performance Metrics

### **System Requirements**
- **CPU**: Intel i5 or equivalent
- **RAM**: 4GB minimum, 8GB recommended
- **Camera**: USB webcam or built-in camera
- **OS**: Windows 10+ or Linux Ubuntu 18.04+

### **Performance Benchmarks**
- **Pose Detection**: ~30 FPS (CPU), ~60 FPS (NPU)
- **Memory Usage**: ~200MB baseline
- **Startup Time**: ~10 seconds (all components)
- **Response Time**: <100ms (API endpoints)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please:
1. Check the [documentation](docs/)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information

---

**Made with ❤️ by the Edgefit-Coach Team** 
