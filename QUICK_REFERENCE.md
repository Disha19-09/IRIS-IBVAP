# IRIS-IBVAP Quick Reference Card

## 🚀 Quick Start Commands

### Easiest Way (Recommended)
```powershell
.\start_demo.bat         # Full streaming demo
.\start_simple.bat       # File-based (most stable)
```

### Manual Start (5 Terminals)
```powershell
# Terminal 1: MediaMTX
.\tools\mediamtx.exe

# Terminal 2: FFmpeg Publisher
.\tools\ffmpeg.exe -re -stream_loop -1 -i .\sample_videos\test_4.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -profile:v baseline -level 3.0 -g 60 -keyint_min 60 -sc_threshold 0 -b:v 2M -maxrate 2M -bufsize 1M -pix_fmt yuv420p -err_detect ignore_err -an -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam1

# Terminal 3: Backend
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Terminal 4: Dashboard
cd dashboard\app
npm run dev -- --host 127.0.0.1

# Terminal 5: CV Pipeline
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1
```

---

## 🌐 Service URLs

| Service | URL | Login Required |
|---------|-----|----------------|
| Dashboard | http://localhost:5173 | Yes (admin/admin123) |
| API Docs | http://localhost:8000/docs | No |
| Backend API | http://localhost:8000 | Yes |
| Video Stream | http://localhost:8889/cam1/ | No |
| WebSocket | ws://localhost:8000/ws/alerts | No |

---

## 🔑 Default Credentials

**Username:** `admin`  
**Password:** `admin123`  
⚠️ **Change immediately in production!**

---

## 📊 Configuration Quick Reference

### CV Pipeline Settings (`detect_track_fence.py`)

| Setting | Default | Adjust For |
|---------|---------|------------|
| `PROCESS_EVERY_N_FRAMES` | 2 | Higher = faster but less accurate |
| `CONF_THRESHOLD` | 0.5 | Higher = fewer false positives |
| `ALERT_CONSEC_FRAMES` | 2 | Higher = more confirmation needed |
| `RESIZE_WIDTH` | 640 | Lower = faster processing |
| `LINE_START` | (0, 300) | Adjust for your video |
| `LINE_END` | (640, 300) | Adjust for your video |

### Performance Tuning

**High CPU Usage?**
```python
PROCESS_EVERY_N_FRAMES = 3    # Process fewer frames
CONF_THRESHOLD = 0.6          # Detect less
RESIZE_WIDTH = 480            # Lower resolution
```

**Need More Accuracy?**
```python
PROCESS_EVERY_N_FRAMES = 1    # Process every frame
CONF_THRESHOLD = 0.4          # Detect more
ALERT_CONSEC_FRAMES = 3       # More confirmation
```

---

## 🛠️ Common Commands

### Check If Services Are Running
```powershell
curl http://localhost:8000     # Backend
curl http://localhost:5173     # Dashboard
curl http://localhost:8889     # MediaMTX
```

### Stop All Services
Press `Ctrl+C` in each terminal window

### Clear Old Alerts
```powershell
curl -X DELETE http://localhost:8000/alerts -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Video File
```powershell
.\tools\ffmpeg.exe -v error -i sample_videos\test_4.mp4 -f null -
```

---

## 🐛 Quick Troubleshooting

### H.264 Errors Appearing?
```powershell
# Use the launcher (errors suppressed)
cd cv_pipeline
run_pipeline.bat
```

### Stream Lagging?
1. Check MediaMTX is running
2. Clear browser cache (Ctrl+Shift+Delete)
3. Reload dashboard (Ctrl+F5)

### Alerts Not Syncing?
1. Check backend: http://localhost:8000
2. Open browser console (F12)
3. Look for WebSocket connection status

### Backend Won't Start?
```powershell
.\install_auth_deps.bat
```

---

## 📝 File Locations

| Type | Location |
|------|----------|
| Snapshots | `snapshots/` |
| Alert DB | `backend/alerts.db` |
| Logs | `cv_pipeline/*.log` |
| Config | `cv_pipeline/detect_track_fence.py` |
| Sample Videos | `sample_videos/` |

---

## 🎯 CV Pipeline Options

```powershell
# Basic usage
python detect_track_fence.py --source VIDEO_PATH

# With ANPR
python detect_track_fence.py --source VIDEO_PATH --anpr

# Track all objects
python detect_track_fence.py --source VIDEO_PATH --track-all

# RTSP stream
python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1
```

---

## 🔒 API Authentication

### Login
```powershell
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}'
```

### Get Alerts (with token)
```powershell
curl http://localhost:8000/alerts `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🎓 User Roles

| Role | Permissions |
|------|-------------|
| **viewer** | View dashboard, alerts, events |
| **operator** | viewer + Create events, manage cameras |
| **admin** | operator + User management, system config |

---

## 📚 Documentation Files

- `README.md` - Full setup guide
- `TROUBLESHOOTING.md` - Detailed problem solving
- `AUTH_GUIDE.md` - Complete authentication docs
- `QUICK_START_AUTH.md` - Authentication quick start
- `QUICK_REFERENCE.md` - This file

---

## 💡 Pro Tips

1. **Always use `start_simple.bat` for initial testing** - most stable
2. **Check console outputs** - they show what's happening
3. **Browser DevTools (F12)** - shows WebSocket status
4. **Press 'q' in CV window** - graceful shutdown
5. **Adjust virtual fence** - edit LINE_START/LINE_END in detect_track_fence.py

---

## 🎬 Demo Workflow

1. Run `start_simple.bat` or `start_demo.bat`
2. Open http://localhost:5173
3. Login with admin/admin123
4. Watch dashboard for alerts
5. Press 'q' in CV window to stop
6. Close all terminals

---

## 📞 Need Help?

1. Check `TROUBLESHOOTING.md`
2. Review console logs
3. Open browser DevTools (F12)
4. Verify all services are running
5. Try `start_simple.bat` for minimal setup

**Quick health check:**
```powershell
# All should return 200 OK
curl -I http://localhost:8000
curl -I http://localhost:5173
curl -I http://localhost:8889
```
