# IRIS - IBVAP Starter Kit

Intelligent Border Video Analytics Platform — a software-only AI layer that turns
existing CCTV footage into live detection, tracking, virtual-fence alerts, and ANPR.

The repository contains a FastAPI backend with JWT authentication, a React/Vite dashboard, 
a YOLOv8 tracking pipeline, and a MediaMTX WebRTC bridge for displaying an RTSP camera
stream in a browser.

---

## 0. One-time setup

Run these commands from the repository root on Windows:

```powershell
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
pip install sqlalchemy

# Install JWT authentication dependencies
pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt

cd dashboard\app
npm.cmd ci
cd ..\..
```

**OR** use the provided installation script for auth dependencies:
```powershell
install_auth_deps.bat
```

The backend requires SQLAlchemy and JWT authentication libraries. The first pipeline run 
downloads the `yolov8n.pt` model weights (about 6 MB) and caches them in `cv_pipeline/`.

The repository includes sample videos in `sample_videos/`. To use another clip,
place a short road, parking-lot, or open-area video there.

### Streaming tools

The dashboard video panel expects MediaMTX WebRTC at
`http://127.0.0.1:8889/cam1/`. Install or download these tools and place the
executables at the following paths:

```text
tools\ffmpeg.exe
tools\mediamtx.exe
```

FFmpeg publishes the sample video as RTSP. MediaMTX converts that RTSP input to
WebRTC for the browser. The backend and dashboard can run without the stream,
but the video panel will show a connection error until these services are up.

---

## 1. Run the complete live demo

Open five PowerShell terminals from the repository root and run the following
commands in order.

### Terminal 1: MediaMTX

```powershell
.\tools\mediamtx.exe
```

MediaMTX listens for RTSP on port `8554` and serves WebRTC on port `8889`.

### Terminal 2: Publish a camera stream

```powershell
.\tools\ffmpeg.exe -re -stream_loop -1 -i .\sample_videos\test_4.mp4 `
  -c:v libx264 -preset ultrafast -tune zerolatency -g 30 `
  -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -an `
  -f rtsp rtsp://127.0.0.1:8554/cam1
```

### Terminal 3: Backend

```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000`. Alerts are stored in
`backend/alerts.db`, and snapshots are served from `snapshots/`.

**Default Admin Account** (auto-created on first run):
- Username: `admin`
- Password: `admin123`
- ⚠️ Change this password immediately!

Test authentication:
```powershell
..\venv\Scripts\python.exe ..\test_auth.py
```

Or visit the interactive API docs: `http://127.0.0.1:8000/docs`

### Terminal 4: Dashboard

```powershell
cd dashboard\app
npm.cmd run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/` in a browser.

### Terminal 5: Live CV pipeline

```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1
```

The pipeline sends crossing events to the backend, saves evidence snapshots,
and writes the annotated video to `snapshots/annotated_output.mp4`. Press `q`
in the CV window to stop it.

For ANPR, add `--anpr` to the pipeline command. ANPR loads an additional OCR
model the first time it is used.

---

## 2. Run the CV pipeline from a local file

```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
```

What you'll see:
- A window showing your video with bounding boxes, track IDs, and a dashed
  virtual fence line drawn across it.
- Every time a tracked person/vehicle crosses that line, an alert fires:
  a snapshot is saved to `snapshots/`, and an event is written to the backend
  database.
- If `--anpr` is passed and a vehicle crosses, it attempts to read the plate.

**Tune it for your clip:**
- Open `detect_track_fence.py`, adjust `LINE_START` / `LINE_END` (pixel
  coordinates on the resized 640-wide frame) so the line sits somewhere
  people/vehicles actually cross in your footage.
- If it's laggy on your machine, increase `PROCESS_EVERY_N_FRAMES` to 2 or 3.
- If you're getting false alerts, increase `ALERT_CONSEC_FRAMES`.

Press `q` in the video window to stop early.

---

## 3. Useful endpoints

### Authentication (NEW!)

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `POST /auth/login` | Login to get JWT tokens | No |
| `POST /auth/register` | Register new user (viewer role) | No |
| `GET /auth/me` | Get current user info | Yes |
| `GET /users` | List all users | Admin only |

For full authentication documentation, see [AUTH_GUIDE.md](AUTH_GUIDE.md) or [QUICK_START_AUTH.md](QUICK_START_AUTH.md)

### Service URLs

| Service | URL |
|---|---|
| Dashboard | `http://127.0.0.1:5173/` |
| Backend API | `http://127.0.0.1:8000/` |
| Interactive API Docs | `http://127.0.0.1:8000/docs` |
| Alerts API | `http://127.0.0.1:8000/alerts` (requires auth) |
| WebSocket alerts | `ws://127.0.0.1:8000/ws/alerts` |
| MediaMTX WebRTC | `http://127.0.0.1:8889/cam1/` |
| MediaMTX HLS | `http://127.0.0.1:8888/cam1/index.m3u8` |

---

## 4. Team split from here

| Who | What to touch next |
|---|---|
| CV Lead | Tune detection confidence, tracking stability, test on 2-3 different clips |
| CV Support | Improve ANPR crop region, add face detection as a separate optional module |
| Backend Dev | Implement JWT refresh tokens, add rate limiting, enhance user roles |
| Frontend Dev | Add login page, integrate JWT auth, add user management UI for admins |
| Integration/DevOps | Make sure all 3 pieces run together smoothly on a clean machine, keep committing to GitHub |
| Research/Pitch Lead | Use real output (screenshots, alert API data, snapshot images) in the PPT instead of mockups |

---

## 5. JWT Authentication (NEW!)

The backend now includes comprehensive JWT authentication with role-based access control.

**Quick Start:**
1. Install auth dependencies: `install_auth_deps.bat`
2. Restart backend - admin user is auto-created
3. Login: `admin` / `admin123`
4. Test: `venv\Scripts\python.exe test_auth.py`

**User Roles:**
- **viewer** - View alerts and dashboard
- **operator** - viewer + create events
- **admin** - operator + user management

**Documentation:**
- Quick start guide: [QUICK_START_AUTH.md](QUICK_START_AUTH.md)
- Full documentation: [AUTH_GUIDE.md](AUTH_GUIDE.md)
- Interactive API docs: http://localhost:8000/docs

**Protected Endpoints:**
- `/alerts` - requires viewer role
- `/api/events` - requires operator role
- `/users` - requires admin role
- `/api/events/public` - public (for CV pipeline)

---

## 6. Known limitations (be upfront about these in your pitch, don't hide them)

- Runs on CPU — fine for a demo, would need edge GPU (e.g. Jetson) for real deployment.
- ANPR accuracy depends heavily on plate visibility/angle in your test clip.
- Night-time detection is not specially tuned — same model runs on any clip, but
  low-light accuracy will be visibly weaker. That's fine to say out loud.
- The virtual fence line is manually set per video — a real system would let an
  operator draw it interactively on the dashboard (good "future work" slide point).
