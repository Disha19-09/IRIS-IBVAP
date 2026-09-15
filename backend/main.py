"""
IRIS - IBVAP Backend
---------------------
Receives alerts from the CV pipeline via POST /api/events, stores them
in a SQLite database, broadcasts them live over WebSocket, and serves
them to the dashboard. Also serves snapshot images as static files.

HOW TO RUN:
  cd backend
  uvicorn main:app --reload --port 8000
"""

import os
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import SessionLocal, Alert

app = FastAPI(title="IRIS - IBVAP Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "..", "snapshots")

app.mount("/snapshots", StaticFiles(directory=SNAPSHOTS_DIR), name="snapshots")


@app.middleware("http")
async def disable_live_data_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/alerts") or request.url.path.startswith("/snapshots/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/")
def root():
    return {"status": "IRIS IBVAP backend running"}


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keeps the connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Event ingestion (called by the CV pipeline)
# ---------------------------------------------------------------------------

def _alert_to_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "camera_id": alert.camera_id,
        "event_type": alert.event_type,
        "object_type": alert.object_type,
        "track_id": alert.track_id,
        "confidence": alert.confidence,
        "timestamp": alert.timestamp.isoformat(),
        "snapshot_path": alert.snapshot_path,
        "plate_number": alert.plate_number,
    }


@app.post("/api/events")
async def create_event(event: dict):
    db = SessionLocal()
    alert = Alert(
        camera_id=event.get("camera_id", "CAM_01"),
        event_type=event.get("event_type"),
        object_type=event.get("object_type"),
        track_id=event.get("track_id"),
        confidence=event.get("confidence"),
        timestamp=datetime.fromisoformat(event["timestamp"]) if event.get("timestamp") else datetime.utcnow(),
        snapshot_path=event.get("snapshot_path"),
        plate_number=event.get("plate_number"),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    db.close()

    await manager.broadcast(_alert_to_dict(alert))

    return {"status": "logged", "id": alert.id}


# ---------------------------------------------------------------------------
# Existing routes — now backed by the database instead of the JSON file
# ---------------------------------------------------------------------------

@app.get("/alerts")
def get_alerts(limit: int = 100):
    db = SessionLocal()
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
    db.close()
    return [_alert_to_dict(a) for a in alerts]


@app.get("/alerts/count")
def get_alert_count():
    db = SessionLocal()
    count = db.query(Alert).count()
    db.close()
    return {"total": count}


@app.delete("/alerts")
def clear_alerts():
    """Useful for resetting between demo runs."""
    db = SessionLocal()
    db.query(Alert).delete()
    db.commit()
    db.close()
    return {"status": "cleared"}