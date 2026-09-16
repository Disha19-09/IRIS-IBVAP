"""
IRIS - IBVAP Backend
---------------------
Receives alerts from the CV pipeline via POST /api/events, stores them
in a SQLite database, broadcasts them live over WebSocket, and serves
them to the dashboard. Also serves snapshot images as static files.

Features:
- JWT Authentication with role-based access control
- User management (admin, operator, viewer roles)
- Protected API endpoints
- WebSocket alerts broadcasting

HOW TO RUN:
  cd backend
  uvicorn main:app --reload --port 8000

Default Admin Account:
  Username: admin
  Password: admin123
  (Created automatically on first run)
"""

import os
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import SessionLocal, Alert, User
from auth import (
    get_db,
    get_current_user,
    get_current_active_user,
    authenticate_user,
    create_tokens,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_password_hash,
    verify_password,
    require_admin,
    require_operator,
    require_viewer,
    RoleChecker,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    PasswordChange,
)

app = FastAPI(
    title="IRIS - IBVAP Backend",
    description="Intelligent Border Video Analytics Platform API with JWT Authentication",
    version="2.0.0"
)

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


# ---------------------------------------------------------------------------
# Startup: Create default admin user
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def create_default_admin():
    """Create default admin user on first run."""
    db = SessionLocal()
    try:
        admin = get_user_by_username(db, "admin")
        if not admin:
            admin_user = UserCreate(
                username="admin",
                email="admin@iris-ibvap.local",
                password="admin123",
                full_name="System Administrator",
                roles=["admin", "operator", "viewer"]
            )
            create_user(db, admin_user)
            print("[INFO] Default admin user created: admin / admin123")
        else:
            print("[INFO] Admin user already exists")
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "status": "IRIS IBVAP backend running",
        "version": "2.0.0",
        "features": ["JWT Authentication", "Role-Based Access Control", "WebSocket Alerts"]
    }


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (public endpoint).
    Default role is 'viewer'. Only admins can create users with elevated roles.
    """
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Only allow viewer role for public registration
    user_data.roles = ["viewer"]
    
    user = create_user(db, user_data)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user.roles.split(",") if user.roles else [],
        is_active=user.is_active,
        created_at=user.created_at
    )


@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username and password to get JWT tokens.
    Returns both access_token and refresh_token.
    """
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return create_tokens(user)


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=current_user.roles.split(",") if current_user.roles else [],
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@app.post("/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# ---------------------------------------------------------------------------
# User Management Routes (Admin only)
# ---------------------------------------------------------------------------

@app.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(db: Session = Depends(get_db)):
    """List all users (admin only)."""
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles.split(",") if user.roles else [],
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in users
    ]


@app.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def create_new_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with any role (admin only)."""
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    user = create_user(db, user_data)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user.roles.split(",") if user.roles else [],
        is_active=user.is_active,
        created_at=user.created_at
    )


@app.put("/users/{user_id}/roles", dependencies=[Depends(require_admin)])
async def update_user_roles(
    user_id: int,
    roles: List[str],
    db: Session = Depends(get_db)
):
    """Update user roles (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate roles
    valid_roles = ["admin", "operator", "viewer"]
    for role in roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {role}. Valid roles: {', '.join(valid_roles)}"
            )
    
    user.roles = ",".join(roles)
    db.commit()
    
    return {"message": "User roles updated", "roles": roles}


@app.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting the last admin
    if "admin" in user.roles.split(","):
        admin_count = db.query(User).filter(User.roles.contains("admin")).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin user"
            )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


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
# Event ingestion (protected - requires operator or admin role)
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
async def create_event(
    event: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    Create a new event/alert (requires operator or admin role).
    Called by CV pipeline to log detection events.
    """
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

    await manager.broadcast(_alert_to_dict(alert))

    return {"status": "logged", "id": alert.id}


# ---------------------------------------------------------------------------
# Alert routes (protected - requires viewer role or higher)
# ---------------------------------------------------------------------------

@app.get("/alerts")
async def get_alerts(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Get recent alerts (requires viewer role or higher)."""
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
    return [_alert_to_dict(a) for a in alerts]


@app.get("/alerts/count")
async def get_alert_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Get total alert count (requires viewer role or higher)."""
    count = db.query(Alert).count()
    return {"total": count}


@app.delete("/alerts", dependencies=[Depends(require_admin)])
async def clear_alerts(db: Session = Depends(get_db)):
    """Clear all alerts (admin only). Useful for resetting between demo runs."""
    db.query(Alert).delete()
    db.commit()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Public event ingestion endpoint (for CV pipeline without auth)
# ---------------------------------------------------------------------------

@app.post("/api/events/public")
async def create_event_public(event: dict, db: Session = Depends(get_db)):
    """
    Public endpoint for CV pipeline to submit events without authentication.
    Use this temporarily or secure it with API key if needed.
    """
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

    await manager.broadcast(_alert_to_dict(alert))

    return {"status": "logged", "id": alert.id}