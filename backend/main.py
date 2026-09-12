"""
IRIS - IBVAP Backend
---------------------
Serves the alerts.json file (written by the CV pipeline) to the dashboard,
and serves snapshot images as static files.

HOW TO RUN:
  cd backend
  uvicorn main:app --reload --port 8000

Then open dashboard/index.html in your browser (it polls this API).
"""

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="IRIS - IBVAP Backend")

# Allow the dashboard (opened as a local file or on another port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
ALERTS_JSON_PATH = os.path.join(BASE_DIR, "alerts.json")
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "..", "snapshots")

# Serve snapshot images at /snapshots/<filename>
app.mount("/snapshots", StaticFiles(directory=SNAPSHOTS_DIR), name="snapshots")


@app.get("/")
def root():
    return {"status": "IRIS IBVAP backend running"}


@app.get("/alerts")
def get_alerts():
    """Returns all alerts, most recent first."""
    if not os.path.exists(ALERTS_JSON_PATH):
        return []
    with open(ALERTS_JSON_PATH, "r") as f:
        try:
            alerts = json.load(f)
        except json.JSONDecodeError:
            alerts = []
    return list(reversed(alerts))


@app.get("/alerts/count")
def get_alert_count():
    alerts = get_alerts()
    return {"total": len(alerts)}


@app.delete("/alerts")
def clear_alerts():
    """Useful for resetting between demo runs."""
    with open(ALERTS_JSON_PATH, "w") as f:
        json.dump([], f)
    return {"status": "cleared"}
