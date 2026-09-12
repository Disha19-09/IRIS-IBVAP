# IRIS — IBVAP Starter Kit

Intelligent Border Video Analytics Platform — a software-only AI layer that turns
existing CCTV footage into live detection, tracking, virtual-fence alerts, and ANPR.

This is your Day 1 starter. Everyone can run this independently and then plug in
their own piece.

---

## 0. One-time setup (everyone, do this first)

```bash
# 1. Create a virtual environment (recommended so installs don't clash across teammates' machines)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
```

The first time you run the CV pipeline, `ultralytics` will auto-download the
`yolov8n.pt` model weights (~6MB) — needs internet once, then it's cached locally.

Put a short test video (10-30 seconds, a road / parking lot / open area with people
and vehicles) into `sample_videos/test1.mp4`. Free stock CCTV-style clips work fine
from Pexels or Pixabay.

---

## 1. Run the CV pipeline (CV Lead + CV Support start here)

```bash
cd cv_pipeline
python detect_track_fence.py --source ../sample_videos/test1.mp4 --anpr
```

What you'll see:
- A window showing your video with bounding boxes, track IDs, and a dashed
  virtual fence line drawn across it.
- Every time a tracked person/vehicle crosses that line, an alert fires:
  a snapshot is saved to `snapshots/`, and a record is appended to
  `backend/alerts.json`.
- If `--anpr` is passed and a vehicle crosses, it attempts to read the plate.

**Tune it for your clip:**
- Open `detect_track_fence.py`, adjust `LINE_START` / `LINE_END` (pixel
  coordinates on the resized 640-wide frame) so the line sits somewhere
  people/vehicles actually cross in your footage.
- If it's laggy on your machine, increase `PROCESS_EVERY_N_FRAMES` to 2 or 3.
- If you're getting false alerts, increase `ALERT_CONSEC_FRAMES`.

Press `q` in the video window to stop early.

---

## 2. Run the backend (Backend Dev starts here)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/alerts` in a browser — you should see the same
JSON that the CV pipeline is writing to `alerts.json`. This is the API the
dashboard polls.

---

## 3. Open the dashboard (Frontend Dev starts here)

Just open `dashboard/index.html` directly in a browser (double-click it, or
right-click → Open with browser). It polls `http://localhost:8000/alerts`
every 2 seconds and renders the live feed, a stat bar, and a snapshot detail
panel when you click an alert row.

**Order of operations for a live demo:**
1. Start the backend (`uvicorn main:app ...`)
2. Open the dashboard in a browser
3. Run the CV pipeline on your test video
4. Watch alerts appear live on the dashboard as crossings happen

---

## 4. Team split from here

| Who | What to touch next |
|---|---|
| CV Lead | Tune detection confidence, tracking stability, test on 2-3 different clips |
| CV Support | Improve ANPR crop region, add face detection as a separate optional module |
| Backend Dev | Add a `/alerts/{id}` endpoint, consider swapping alerts.json for SQLite once stable |
| Frontend Dev | Polish dashboard styling, add filter by object class, add a "clear demo" button calling `DELETE /alerts` |
| Integration/DevOps | Make sure all 3 pieces run together smoothly on a clean machine, keep committing to GitHub |
| Research/Pitch Lead | Use real output (screenshots, alert JSON, snapshot images) in the PPT instead of mockups |

---

## Known limitations (be upfront about these in your pitch, don't hide them)

- Runs on CPU — fine for a demo, would need edge GPU (e.g. Jetson) for real deployment.
- ANPR accuracy depends heavily on plate visibility/angle in your test clip.
- Night-time detection is not specially tuned — same model runs on any clip, but
  low-light accuracy will be visibly weaker. That's fine to say out loud.
- The virtual fence line is manually set per video — a real system would let an
  operator draw it interactively on the dashboard (good "future work" slide point).
