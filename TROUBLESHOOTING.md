# IRIS-IBVAP Troubleshooting Guide

## Common Issues and Solutions

### 1. H.264 Decoding Errors

**Symptoms:**
```
[h264 @ 000001807f960000] corrupted macroblock
[h264 @ 000001807f960000] error while decoding MB
```

**Causes:**
- Corrupted video file
- Network issues in RTSP stream
- FFmpeg encoding parameters causing instability

**Solutions:**

#### A. Use the Enhanced Launcher (Recommended)
```powershell
cd cv_pipeline
run_pipeline.bat
```
This automatically suppresses H.264 warnings.

#### B. Update FFmpeg Publishing Parameters
Use this improved command for publishing:
```powershell
.\tools\ffmpeg.exe -re -stream_loop -1 -i .\sample_videos\test_4.mp4 `
  -c:v libx264 -preset ultrafast -tune zerolatency `
  -profile:v baseline -level 3.0 `
  -g 60 -keyint_min 60 -sc_threshold 0 `
  -b:v 2M -maxrate 2M -bufsize 1M `
  -pix_fmt yuv420p -err_detect ignore_err `
  -an -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam1
```

#### C. Run from Local File (Most Stable)
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
```

**Technical Details:**
- The errors are usually non-fatal - video continues playing
- New optimizations skip corrupted frames automatically
- Reduced frame processing (`PROCESS_EVERY_N_FRAMES = 2`) improves stability

---

### 2. Lagging Live Stream

**Symptoms:**
- Dashboard video is 5-10 seconds behind
- Choppy or frozen video playback
- High CPU usage

**Solutions:**

#### A. Optimized Processing (Applied)
The CV pipeline now processes every 2nd frame instead of every 5th:
```python
PROCESS_EVERY_N_FRAMES = 2  # Balance between performance and responsiveness
```

#### B. Check MediaMTX Configuration
Ensure MediaMTX is running:
```powershell
.\tools\mediamtx.exe
```

#### C. Reduce Video Quality (if needed)
Lower the bitrate in FFmpeg publishing:
```powershell
-b:v 1M -maxrate 1M -bufsize 512K
```

#### D. Clear Browser Cache
In your browser:
1. Press `Ctrl + Shift + Delete`
2. Clear cached images and files
3. Reload the dashboard (`Ctrl + F5`)

**What Was Fixed:**
- Added bitrate control to FFmpeg streaming
- Optimized GOP settings (keyframe every 2 seconds)
- Added error resilience with `-err_detect ignore_err`
- Reduced buffer sizes for lower latency

---

### 3. Alerts Not Syncing with Dashboard

**Symptoms:**
- Dashboard shows "BACKEND OFFLINE"
- Alerts appear 2-3 seconds late
- WebSocket disconnection errors in console

**Solutions:**

#### A. Check Backend is Running
```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Verify at: http://localhost:8000

#### B. Check WebSocket Connection
Open browser DevTools (F12) → Console tab. You should see:
```
[WebSocket] Connected to alerts stream
```

If you see disconnection messages:
1. Verify backend is running on port 8000
2. Check no firewall is blocking WebSocket connections
3. Try restarting the backend

#### C. Verify Alert Generation
Check CV pipeline console for alert messages:
```
[ALERT] Virtual fence crossing: person #1
```

**What Was Fixed:**
- Reduced polling interval from 2s to 1s
- Faster WebSocket reconnection (1s instead of 2s)
- Improved error handling for authentication issues

---

### 4. Backend Not Starting

**Symptoms:**
```
ModuleNotFoundError: No module named 'jose'
```

**Solution:**
Install authentication dependencies:
```powershell
.\install_auth_deps.bat
```

Or manually:
```powershell
venv\Scripts\activate
pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt sqlalchemy
```

---

### 5. Dashboard Shows White Screen

**Symptoms:**
- Blank page at http://localhost:5173
- Console errors about authentication

**Solutions:**

#### A. Login Required
Navigate to http://localhost:5173/login and login:
- Username: `admin`
- Password: `admin123`

#### B. Rebuild Dashboard
```powershell
cd dashboard\app
npm install
npm run dev -- --host 127.0.0.1
```

---

### 6. Performance Issues

**Symptoms:**
- High CPU usage (>80%)
- Dropped frames
- Slow detection

**Solutions:**

#### A. Reduce Processing Load
Edit `cv_pipeline/detect_track_fence.py`:
```python
PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame
CONF_THRESHOLD = 0.6        # Higher threshold = fewer detections
```

#### B. Disable ANPR (if not needed)
Run without `--anpr` flag:
```powershell
python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1
```

#### C. Use Lower Resolution
Edit configuration:
```python
RESIZE_WIDTH = 480  # Lower resolution
```

---

## Quick Diagnostic Commands

### Check Services Status
```powershell
# Backend
curl http://localhost:8000

# Dashboard
curl http://localhost:5173

# MediaMTX
curl http://localhost:8889
```

### View Logs
```powershell
# CV Pipeline logs
Get-Content cv_pipeline\pipeline-live.out.log -Tail 20

# Backend startup
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Test Video Files
```powershell
# Check file integrity
.\tools\ffmpeg.exe -v error -i sample_videos\test_4.mp4 -f null -
```

---

## Environment Variables Reference

Set these in PowerShell before running the pipeline:

```powershell
# Suppress OpenCV FFmpeg warnings
$env:OPENCV_FFMPEG_CAPTURE_OPTIONS="loglevel;quiet"
$env:OPENCV_LOG_LEVEL="ERROR"

# Suppress color in logs
$env:AV_LOG_FORCE_NOCOLOR="1"
```

---

## Performance Optimization Summary

| Component | Before | After | Impact |
|-----------|--------|-------|---------|
| Frame Processing | Every 5th frame | Every 2nd frame | Better responsiveness |
| Alert Polling | 2 seconds | 1 second | Faster updates |
| WebSocket Reconnect | 2 seconds | 1 second | Faster recovery |
| FFmpeg Bitrate | Variable | 2 Mbps fixed | Stable streaming |
| H.264 Error Handling | Logged | Suppressed/Skipped | Cleaner output |

---

## Still Having Issues?

1. **Check all 5 services are running:**
   - MediaMTX (port 8554/8889)
   - FFmpeg publisher
   - Backend (port 8000)
   - Dashboard (port 5173)
   - CV Pipeline

2. **Review the logs:**
   - CV pipeline console output
   - Backend terminal output
   - Browser DevTools console (F12)

3. **Try the simplest setup first:**
   ```powershell
   # Terminal 1: Backend only
   cd backend
   ..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   
   # Terminal 2: Dashboard only
   cd dashboard\app
   npm run dev -- --host 127.0.0.1
   
   # Terminal 3: CV pipeline from file (no streaming)
   cd cv_pipeline
   ..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
   ```

4. **Check the README.md** for full setup instructions

5. **Contact support** with:
   - Error messages (full text)
   - Commands you ran
   - Which terminal/step failed
