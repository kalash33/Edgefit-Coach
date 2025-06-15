# Edgefit-Coach Startup Guide

## Quick Start (Recommended)

Use the new launcher script that starts all components in the correct order:

```bash
python start_app.py
```

This will automatically start:
1. 🔌 **WebSocket Server** (port 8001) - First
2. 🛠️ **API Server** (port 8000) - Second (after 3 seconds)
3. 🎨 **Streamlit Frontend** (port 8501) - Last (after 8 seconds total)

## Access Your Application

Once all components are running:
- **Frontend**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8001

## Manual Startup (Alternative)

If you prefer to start components manually:

```bash
# Terminal 1: Start WebSocket Server
python websocket_server.py

# Terminal 2: Start API Server (wait 3 seconds after WebSocket)
python api_server.py

# Terminal 3: Start Frontend (wait 5 seconds after API)
streamlit run frontend_test.py --server.port 8501
```

## Troubleshooting

### Encoding Error Fix
If you see `UnicodeEncodeError: 'charmap' codec can't encode character`, the new launcher automatically handles this by:
- Setting `PYTHONIOENCODING=utf-8`
- Using proper encoding parameters in subprocess calls
- Adding error handling for character encoding issues

### Component Startup Order
The correct startup order is crucial:
1. **WebSocket Server** must start first
2. **API Server** starts second and connects to WebSocket
3. **Streamlit Frontend** starts last and connects to both

### Port Conflicts
If you get port conflicts:
- Check if any components are already running
- Use `Ctrl+C` to stop the launcher (stops all components)
- Wait a few seconds before restarting

## Stopping the Application

When using `start_app.py`:
- Press `Ctrl+C` once to gracefully stop all components
- The launcher will automatically terminate all processes

## Legacy Startup (Deprecated)

The old method of running `python api_server.py` directly is still available but not recommended as it may have startup order issues. 