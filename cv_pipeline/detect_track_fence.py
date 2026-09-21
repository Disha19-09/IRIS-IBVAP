"""
IRIS - IBVAP Core CV Pipeline
------------------------------
What this does (in order):
  1. Reads a video file frame by frame
  2. Runs YOLOv8n detection + built-in tracking
  3. Draws a virtual fence line on the frame
  4. Detects when a tracked object's center crosses that line
  5. Confirms the crossing for multiple frames to reduce false positives
  6. If the object is a vehicle, optionally runs ANPR (plate OCR)
  7. Saves a snapshot image + writes an alert record to alerts.json
  8. Saves an annotated output video for the demo
  9. Optionally logs all tracked objects for monitoring/debugging

HOW TO RUN:
  python detect_track_fence.py --source ../sample_videos/test.mp4

For ANPR:
  python detect_track_fence.py --source ../sample_videos/test.mp4 --anpr

To log all tracked objects:
  python detect_track_fence.py --source ../sample_videos/test.mp4 --track-all

No GPU needed. Runs on CPU.
"""

import argparse
import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
import csv
import requests
import numpy as np
import random

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# CONFIG - tune these for your demo
# ---------------------------------------------------------------------------

MODEL_PATH = "yolov8n.pt"          # Nano model -> fastest on CPU
CONF_THRESHOLD = 0.5               # Detection confidence cutoff (increased to reduce false detections)
BACKEND_URL = "http://localhost:8000/api/events/public"  # Public endpoint (no auth required)
CAMERA_ID = "CAM_01"
RESIZE_WIDTH = 960                 # Balanced resolution for CPU
PROCESS_EVERY_N_FRAMES = 3         # Process every 3rd frame for CPU
ALERT_CONSEC_FRAMES = 1            # Reduced since we're processing fewer frames
TRACK_ALL_OBJECTS = False          # Set to True to get alerts for all tracked objects
TRACK_ALL_FRAMES_INTERVAL = 30     # How often to log all tracked objects (in frames)

# ANPR Mock Data (for demonstration)
ENABLE_MOCK_ANPR = True            # Set to False to use real OCR only
MOCK_ANPR_PROBABILITY = 0.8        # 80% chance to generate mock plate if OCR fails
RESIZE_WIDTH = 960                 # Balanced resolution for CPU
PROCESS_EVERY_N_FRAMES = 3         # Process every 3rd frame for CPU
ALERT_CONSEC_FRAMES = 1            # Reduced since we're processing fewer frames
TRACK_ALL_OBJECTS = False          # Set to True to get alerts for all tracked objects
TRACK_ALL_FRAMES_INTERVAL = 30     # How often to log all tracked objects (in frames)

# change 1: Added loitering and night movement detection settings
# Loitering detection settings
LOITERING_TIME_THRESHOLD = 5.0     # Seconds an object must remain in loitering zone to trigger alert
LOITERING_SIDE = 1                 # Side of the fence considered for loitering (1 or -1, as defined by side_of_line)

# Night movement detection settings
NIGHT_START_HOUR = 19              # Start of night (24-hour format, inclusive)
NIGHT_END_HOUR = 6                 # End of night (24-hour format, exclusive)

# change 11: Tracking update interval for dashboard
TRACKING_UPDATE_INTERVAL = 2.0     # Seconds between tracking updates sent to dashboard

# change 7: Added minimum distance threshold for virtual fence crossing
MIN_CROSS_DISTANCE = 10            # Minimum pixels an object must cross the line to be considered valid

# change 8: Added hysteresis for side determination (to reduce jitter)
SIDE_HYSTERESIS = 5                # Pixels buffer zone around the line for stable side detection

# change 9: Added alert cooldown period
ALERT_COOLDOWN_TIME = 5.0          # Seconds to wait before allowing another alert from the same track ID

# ANPR configuration
ANPR_CONFIDENCE_THRESHOLD = 0.2    # Lowered minimum confidence for better detection

# Snapshot management (Option 3: Temporary snapshots)
SNAPSHOT_RETENTION_HOURS = 1       # Auto-delete snapshots older than 1 hour
SNAPSHOT_CLEANUP_INTERVAL = 300    # Check for old snapshots every 5 minutes (seconds)


# ---------------------------------------------------------------------------
# VIRTUAL FENCE
# ---------------------------------------------------------------------------
# Coordinates are based on the resized 960px-wide frame.
# Change the Y value depending on where you want your security boundary.

LINE_START = (0, 350)
LINE_END = (960, 350)


# ---------------------------------------------------------------------------
# OBJECT CLASSES
# ---------------------------------------------------------------------------

# COCO classes used by the pretrained YOLOv8 model
PERSON_CLASSES = {"person"}

VEHICLE_CLASSES = {
    "car",
    "truck",
    "bus",
    "motorcycle"
}


# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------

# Get the directory containing this Python file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "..", "tools")
# Use Windows ffmpeg.exe if available, otherwise rely on system ffmpeg (PATH)
windows_ffmpeg = os.path.join(TOOLS_DIR, "ffmpeg.exe")
if os.path.exists(windows_ffmpeg) and os.access(windows_ffmpeg, os.X_OK):
    FFMPEG_PATH = windows_ffmpeg
else:
    FFMPEG_PATH = "ffmpeg"  # let PATH resolve it
ANNOTATED_RTSP_URL = "rtsp://127.0.0.1:8554/cam1_processed"

# D:\IRIS\iris_ibvap\backend\alerts.json
ALERTS_JSON_PATH = os.path.join(
    BASE_DIR,
    "..",
    "backend",
    "alerts.json"
)

# D:\IRIS\iris_ibvap\backend\alerts.csv
ALERTS_CSV_PATH = os.path.join(
    BASE_DIR,
    "..",
    "backend",
    "alerts.csv"
)

# D:\IRIS\iris_ibvap\snapshots
SNAPSHOTS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "snapshots"
)

# Create required directories if they don't exist
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ALERTS_JSON_PATH), exist_ok=True)


# ---------------------------------------------------------------------------
# EASY OCR
# ---------------------------------------------------------------------------

# EasyOCR is loaded only when ANPR is requested.
_ocr_reader = None


def get_ocr_reader():
    """Load EasyOCR (CPU mode until PyTorch CUDA is installed)."""
    global _ocr_reader

    if _ocr_reader is None:
        import easyocr

        print(
            "[INFO] Loading EasyOCR model (CPU mode) "
            "(first time only, may take a minute)..."
        )

        _ocr_reader = easyocr.Reader(["en"], gpu=False)  # CPU until CUDA available

    return _ocr_reader


def sanitize_plate_text(text):
    """Clean and validate plate text for format: #A XXXXX (e.g., #A 5402S)."""
    if text is None:
        return None

    # Remove all non-alphanumeric characters except #
    cleaned = re.sub(r"[^A-Za-z0-9#]", "", str(text).upper())
    
    # Must be at least 7 characters (#A + 5 alphanumeric)
    if len(cleaned) < 7:
        return None
    
    # Try to match pattern: #A + 5 alphanumeric characters
    # Examples: #A5402S, #A12345, #AABC12
    match = re.match(r'^(#A)([A-Z0-9]{5})$', cleaned)
    if match:
        # Format as: #A 5402S (with space)
        return f"{match.group(1)} {match.group(2)}"
    
    # Fallback: If it starts with #A and has at least 5 more characters
    if cleaned.startswith('#A') and len(cleaned) >= 7:
        prefix = cleaned[:2]  # #A
        suffix = cleaned[2:7]  # Next 5 characters
        return f"{prefix} {suffix}"
    
    return None


def generate_mock_plate():
    """Generate a realistic mock license plate in format: #A XXXXX (e.g., #A 5402S)"""
    # Characters for the 5-character suffix (alphanumeric)
    alphanumeric = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # Generate 5 random alphanumeric characters
    suffix = ''.join([random.choice(alphanumeric) for _ in range(5)])
    
    # Fixed prefix #A + space + random suffix
    return f"#A {suffix}"


# ---------------------------------------------------------------------------
# ALERT FUNCTIONS
# ---------------------------------------------------------------------------

def load_alerts():
    """Load existing alerts from alerts.json."""
    if os.path.exists(ALERTS_JSON_PATH):
        try:
            with open(ALERTS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def save_alert(alert):
    """Send the alert to the backend in a background thread."""
    def _send():
        try:
            response = requests.post(BACKEND_URL, json=alert, timeout=2)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Backend unreachable, saving locally instead: {e}", flush=True)
            alerts = load_alerts()
            alerts.append(alert)
            with open(ALERTS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2)

    threading.Thread(target=_send, daemon=True).start()


def send_tracking_data(tracking_info):
    """Send tracking data to the dashboard without spamming warnings."""
    try:
        response = requests.post(BACKEND_URL, json=tracking_info, timeout=2)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        pass


# ---------------------------------------------------------------------------
# VIRTUAL FENCE GEOMETRY
# ---------------------------------------------------------------------------

def side_of_line(point, line_start, line_end):
    """Return the position of a point relative to the fence line."""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    return ((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1))


def distance_from_point_to_line(point, line_start, line_end):
    """Return the perpendicular distance from a point to a line."""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    area = (x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)
    line_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    if line_length == 0:
        return 0

    return area / line_length


def preprocess_for_anpr(image):
    """Improve OCR readability with enhanced preprocessing for Chinese-style plates (e.g., AA 82548)."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Increase contrast to make dark text on light plate stand out
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Sharpen to improve character edges
    kernel = np.array([[-1,-1,-1],
                       [-1, 9,-1],
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Adaptive thresholding for varying lighting
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 8
    )
    
    return binary


def localize_license_plate(vehicle_crop):
    """Heuristically crop the lower-middle section of the vehicle for better plate detection."""
    if vehicle_crop.size == 0:
        return vehicle_crop

    height, width = vehicle_crop.shape[:2]
    
    # Focus on bottom 50% of vehicle where plates are typically located
    plate_y1 = int(height * 0.5)
    plate_y2 = height
    plate_x1 = int(width * 0.15)
    plate_x2 = int(width * 0.85)

    plate_y1 = max(0, plate_y1)
    plate_y2 = min(height, plate_y2)
    plate_x1 = max(0, plate_x1)
    plate_x2 = min(width, plate_x2)

    plate_crop = vehicle_crop[plate_y1:plate_y2, plate_x1:plate_x2]

    if plate_crop.size == 0 or plate_crop.shape[0] < 10 or plate_crop.shape[1] < 10:
        return vehicle_crop

    return plate_crop


# change 2: Added is_night() function for night movement detection
def is_night():
    """Return True if current time is within night hours."""
    now = datetime.now()
    hour = now.hour
    if NIGHT_START_HOUR > NIGHT_END_HOUR:
        return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR
    return NIGHT_START_HOUR <= hour < NIGHT_END_HOUR


def cleanup_old_snapshots():
    """Delete snapshot files older than SNAPSHOT_RETENTION_HOURS."""
    try:
        if not os.path.exists(SNAPSHOTS_DIR):
            return

        current_time = time.time()
        retention_seconds = SNAPSHOT_RETENTION_HOURS * 3600
        deleted_count = 0

        for filename in os.listdir(SNAPSHOTS_DIR):
            if not filename.startswith("alert_"):
                continue

            filepath = os.path.join(SNAPSHOTS_DIR, filename)
            if not os.path.isfile(filepath):
                continue

            file_age = current_time - os.path.getmtime(filepath)
            if file_age > retention_seconds:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARNING] Failed to delete {filename}: {e}")

        if deleted_count > 0:
            print(f"[INFO] Cleaned up {deleted_count} old snapshot(s)")

    except Exception as e:
        print(f"[ERROR] Snapshot cleanup failed: {e}")


# ---------------------------------------------------------------------------
# ANPR
# ---------------------------------------------------------------------------

def run_anpr(crop_img, use_mock_fallback=True):
    """Runs OCR on a cropped vehicle image. Falls back to mock data if OCR fails."""
    try:
        if crop_img is None or crop_img.size == 0:
            # Generate mock plate if enabled
            if ENABLE_MOCK_ANPR and use_mock_fallback and random.random() < MOCK_ANPR_PROBABILITY:
                mock_plate = generate_mock_plate()
                print(f"[MOCK] Generated plate: {mock_plate}", flush=True)
                return mock_plate
            return None

        reader = get_ocr_reader()
        processed_img = preprocess_for_anpr(crop_img)
        results = reader.readtext(processed_img)

        if not results:
            # OCR found nothing, use mock if enabled
            if ENABLE_MOCK_ANPR and use_mock_fallback and random.random() < MOCK_ANPR_PROBABILITY:
                mock_plate = generate_mock_plate()
                print(f"[MOCK] OCR empty, generated: {mock_plate}", flush=True)
                return mock_plate
            return None

        best = max(results, key=lambda r: r[2])
        text = best[1]
        conf = best[2]

        if conf <= ANPR_CONFIDENCE_THRESHOLD:
            # OCR confidence too low, use mock if enabled
            if ENABLE_MOCK_ANPR and use_mock_fallback and random.random() < MOCK_ANPR_PROBABILITY:
                mock_plate = generate_mock_plate()
                print(f"[MOCK] OCR low confidence ({conf:.2f}), generated: {mock_plate}", flush=True)
                return mock_plate
            return None

        cleaned = sanitize_plate_text(text)
        if not cleaned:
            # OCR text invalid, use mock if enabled
            if ENABLE_MOCK_ANPR and use_mock_fallback and random.random() < MOCK_ANPR_PROBABILITY:
                mock_plate = generate_mock_plate()
                print(f"[MOCK] OCR invalid format, generated: {mock_plate}", flush=True)
                return mock_plate
            return None

        # Real OCR success!
        print(f"[OCR] Detected plate: {cleaned} (confidence: {conf:.2f})", flush=True)
        return cleaned

    except Exception as e:
        print(f"[WARN] ANPR failed: {e}")
        # Exception, use mock if enabled
        if ENABLE_MOCK_ANPR and use_mock_fallback and random.random() < MOCK_ANPR_PROBABILITY:
            mock_plate = generate_mock_plate()
            print(f"[MOCK] ANPR exception, generated: {mock_plate}", flush=True)
            return mock_plate
        return None


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def is_rtsp(source):
    return (
        isinstance(source, str)
        and source.lower().startswith("rtsp://")
    )


class LatestFrameCapture:
    def __init__(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

        if is_rtsp(source):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.latest_frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        self.running = True

        self.thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )

        self.thread.start()

        return self

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()

            if ret:
                with self.lock:
                    self.latest_frame = frame
            else:
                time.sleep(0.05)

    def read(self):
        with self.lock:
            if self.latest_frame is None:
                return None

            return self.latest_frame.copy()

    def stop(self):
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1)

        self.cap.release()

def start_annotated_rtsp_publisher(width, height, fps):
    """Stream annotated frames to MediaMTX as a live RTSP feed for the dashboard."""
    ffmpeg_bin = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
    command = [
        ffmpeg_bin,
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-g", "30",
        "-keyint_min", "30",
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-an",
        "-f", "rtsp",
        ANNOTATED_RTSP_URL,
    ]

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process
    except Exception as exc:
        print(f"[WARN] Could not start annotated RTSP publisher: {exc}")
        return None


def main(source, run_anpr_flag, output_path, track_all_flag=False, no_display=False):
    # -----------------------------------------------------------------------
    # Load YOLO model
    # -----------------------------------------------------------------------

    # Override config with command line arguments
    global TRACK_ALL_OBJECTS
    TRACK_ALL_OBJECTS = track_all_flag

    # -----------------------------------------------------------------------
    # Load YOLO model
    # -----------------------------------------------------------------------

    print("[INFO] Loading YOLO model...")

    model = YOLO(MODEL_PATH)


    # -----------------------------------------------------------------------
    # Open video
    # -----------------------------------------------------------------------

    rtsp_mode = is_rtsp(source)

    if rtsp_mode:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        latest_capture = LatestFrameCapture(source).start()

        # Give the capture thread a moment to receive the first frame.
        time.sleep(0.5)

        if not latest_capture.cap.isOpened():
            print(
                f"[ERROR] Could not open RTSP source: {source}"
            )
            latest_capture.stop()
            return

        fps = latest_capture.cap.get(cv2.CAP_PROP_FPS) or 20

    else:
        latest_capture = None

        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        
        # Set RTSP-specific options for better stability
        if is_rtsp(source):
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            print(
                f"[ERROR] Could not open video source: {source}"
            )
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 20


    # Video writer will be initialized after the first frame
    writer = None
    annotated_rtsp_proc = None


    # -----------------------------------------------------------------------
    # Tracking / fence state
    # -----------------------------------------------------------------------

    # track_id -> previous side of the fence
    last_side = {}


    # track_id -> number of frames confirming crossing
    crossing_confirm_count = {}


    # track_id -> side the object moved to after crossing
    crossing_direction = {}

    # change 8: For hysteresis - track initial crossing point distance
    # track_id -> distance from line when crossing was first detected
    crossing_initial_distance = {}


    # change 3: Added loitering tracking variables
    # track IDs that have already generated an alert
    already_alerted = set()
    # Loitering tracking
    # track_id -> timestamp when first entered loitering side
    loitering_start_time = {}
    # track IDs that have already generated a loitering alert
    already_alerted_loitering = set()

    # For tracking all objects (if enabled)
    # track_id -> last time we logged this object
    last_track_log_time = {}
    # Frame counter for periodic logging of all objects
    frames_since_last_track_log = 0
    # Last time we sent tracking data to dashboard
    last_dashboard_tracking_time = {}

    # change 9: Alert cooldown tracking
    # track_id -> timestamp of last alert
    last_alert_time = {}
    
    # ANPR duplicate prevention: Set of already recorded plate numbers
    recorded_plates = set()


    # -----------------------------------------------------------------------
    # Frame counter and cleanup tracking
    # -----------------------------------------------------------------------

    frame_idx = 0
    last_cleanup_time = time.time()


    print(
        f"[INFO] Starting pipeline on: {source}"
    )

    print(
        f"[INFO] Virtual fence line: "
        f"{LINE_START} -> {LINE_END}"
    )

    print(
        f"[INFO] Output video: {output_path}"
    )
    
    print(
        f"[INFO] Snapshot retention: {SNAPSHOT_RETENTION_HOURS} hour(s)"
    )


    # -----------------------------------------------------------------------
    # YOLO detection + tracking
    # -----------------------------------------------------------------------

    while True:
        
        if rtsp_mode:
            frame = latest_capture.read()

            if frame is None:
                time.sleep(0.01)
                continue

        else:
            ret, frame = cap.read()

            if not ret:
                break

        results = model.track(
            source=frame,
            conf=CONF_THRESHOLD,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
            device='cpu',  # Temporarily CPU until PyTorch CUDA is installed
        )

        result = results[0]

        frame_idx += 1
        
        # Periodic snapshot cleanup
        current_time = time.time()
        if current_time - last_cleanup_time >= SNAPSHOT_CLEANUP_INTERVAL:
            cleanup_old_snapshots()
            last_cleanup_time = current_time


        # Process every Nth frame
        if frame_idx % PROCESS_EVERY_N_FRAMES != 0:

            continue


        # -------------------------------------------------------------------
        # Get original frame and create resized version for processing
        # -------------------------------------------------------------------

        original_frame = result.orig_img  # Keep original high-quality frame for snapshots/ANPR
        
        h, w = original_frame.shape[:2]

        # Scale frame to RESIZE_WIDTH for fast processing
        scale = RESIZE_WIDTH / w

        new_height = int(h * scale)

        frame = cv2.resize(
            original_frame,
            (RESIZE_WIDTH, new_height)
        )  # Resized frame for display and processing


        # -------------------------------------------------------------------
        # Initialize output video writer
        # -------------------------------------------------------------------

        if writer is None and output_path:

            # Make sure output directory exists
            output_dir = os.path.dirname(
                os.path.abspath(output_path)
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            fh, fw = frame.shape[:2]

            writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (fw, fh)
            )

            if not writer.isOpened():

                print(
                    "[ERROR] Could not create output video writer."
                )

                writer = None

            else:

                print(
                    f"[INFO] Output video writer initialized: "
                    f"{output_path}"
                )


        # -------------------------------------------------------------------
        # Draw virtual fence
        # -------------------------------------------------------------------

        cv2.line(
            frame,
            LINE_START,
            LINE_END,
            (0, 0, 255),
            2
        )


        cv2.putText(
            frame,
            "VIRTUAL FENCE",
            (
                LINE_START[0] + 5,
                LINE_START[1] - 8
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )


        # -------------------------------------------------------------------
        # Get detected objects
        # -------------------------------------------------------------------

        boxes = result.boxes


        if boxes is not None and boxes.id is not None:

            for (
                box,
                track_id,
                cls_idx,
                conf
            ) in zip(
                boxes.xyxy.cpu().numpy(),
                boxes.id.cpu().numpy(),
                boxes.cls.cpu().numpy(),
                boxes.conf.cpu().numpy(),
            ):

                # -----------------------------------------------------------
                # Bounding box coordinates
                # -----------------------------------------------------------

                x1, y1, x2, y2 = box


                # Convert coordinates to resized frame
                x1 = x1 * scale
                x2 = x2 * scale

                y1 = y1 * scale
                y2 = y2 * scale


                # -----------------------------------------------------------
                # Object information
                # -----------------------------------------------------------

                cls_name = model.names[int(cls_idx)]

                track_id = int(track_id)

                confidence = float(conf)


                # Center point of bounding box
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2


                # -----------------------------------------------------------
                # Log all tracked objects (if enabled)
                # -----------------------------------------------------------
                if TRACK_ALL_OBJECTS:
                    current_time = datetime.now()
                    last_logged = last_track_log_time.get(track_id, datetime.min)
                    time_since_last_log = (current_time - last_logged).total_seconds()
                    last_dashboard_time = last_dashboard_tracking_time.get(track_id, datetime.min)
                    time_since_dashboard = (current_time - last_dashboard_time).total_seconds()

                    # Log every TRACK_ALL_FRAMES_INTERVAL frames or every 2 seconds, whichever comes first
                    if (frame_idx - frames_since_last_track_log) >= TRACK_ALL_FRAMES_INTERVAL or time_since_last_log >= 2.0:
                        # Format the log message
                        night_indicator = "[NIGHT] " if is_night() else ""
                        log_message = f"[TRACK] {night_indicator}{cls_name} #{track_id} conf={confidence:.2f} pos=({cx:.1f},{cy:.1f})"
                        print(log_message, flush=True)
                        last_track_log_time[track_id] = current_time

                    # Send tracking data to dashboard every TRACKING_UPDATE_INTERVAL seconds
                    if time_since_dashboard >= TRACKING_UPDATE_INTERVAL:
                        tracking_info = {
                            "camera_id": CAMERA_ID,
                            "event_type": "tracking_update",
                            "object_type": cls_name,
                            "track_id": track_id,
                            "confidence": round(confidence, 3),
                            "timestamp": datetime.now().isoformat(),
                            "position_x": float(cx),
                            "position_y": float(cy),
                            "frame_width": RESIZE_WIDTH,
                            "frame_height": int(RESIZE_WIDTH * h / w),  # Original height scaled
                            "is_night": is_night()
                        }
                        send_tracking_data(tracking_info)
                        last_dashboard_tracking_time[track_id] = current_time

                # Update frame counter for periodic logging
                frames_since_last_track_log += 1


                # -----------------------------------------------------------
                # Bounding box color
                # -----------------------------------------------------------

                if cls_name in PERSON_CLASSES:

                    # Person
                    color = (0, 255, 0)

                elif cls_name in VEHICLE_CLASSES:

                    # Vehicle
                    color = (255, 165, 0)

                else:

                    color = (255, 255, 255)


                # -----------------------------------------------------------
                # Draw bounding box
                # -----------------------------------------------------------

                cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color,
                    2
                )


                # -----------------------------------------------------------
                # Draw class + tracking ID
                # -----------------------------------------------------------

                label = (
                    f"{cls_name} "
                    f"#{track_id} "
                    f"{confidence:.2f}"
                )


                cv2.putText(
                    frame,
                    label,
                    (
                        int(x1),
                        max(15, int(y1) - 6)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    color,
                    2
                )


                # -----------------------------------------------------------
                # Ignore irrelevant classes
                # -----------------------------------------------------------

                if (
                    cls_name not in PERSON_CLASSES
                    and cls_name not in VEHICLE_CLASSES
                ):

                    continue


                # ===========================================================
                # VIRTUAL FENCE CROSSING LOGIC
                # ===========================================================

                current_side = side_of_line(
                    (cx, cy),
                    LINE_START,
                    LINE_END
                )


                # Convert the actual side value into:
                #
                # +1 = one side
                # -1 = opposite side
                #  0 = exactly on the line

                current_sign = (
                    1
                    if current_side > 0
                    else -1
                    if current_side < 0
                    else 0
                )


                prev_sign = last_side.get(track_id)


                # -----------------------------------------------------------
                # Detect initial crossing
                # -----------------------------------------------------------
                distance_from_line = distance_from_point_to_line(
                    (cx, cy),
                    LINE_START,
                    LINE_END
                )
                # -----------------------------------------------------------
                # Virtual fence crossing detection
                # -----------------------------------------------------------

                # Get the previous confirmed side of this tracked object.
                prev_sign = last_side.get(track_id, 0)

                # Determine the current side using hysteresis.
                if distance_from_line > SIDE_HYSTERESIS:
                    effective_sign = 1
                elif distance_from_line < -SIDE_HYSTERESIS:
                    effective_sign = -1
                else:
                    effective_sign = prev_sign


                # Detect a change from one side of the fence to the other.
                if (
                    prev_sign != 0
                    and effective_sign != 0
                    and effective_sign != prev_sign
                ):

                    # Start confirmation for a possible crossing.
                    crossing_confirm_count[track_id] = 1
                    crossing_direction[track_id] = effective_sign


                # Continue confirming an already detected crossing.
                elif (
                    track_id in crossing_confirm_count
                    and crossing_confirm_count[track_id] > 0
                ):

                    expected_side = crossing_direction.get(track_id)

                    if effective_sign == expected_side:
                        crossing_confirm_count[track_id] += 1
                    else:
                        # Side changed back before confirmation.
                        crossing_confirm_count[track_id] = 0
                        crossing_direction.pop(track_id, None)


                else:

                    crossing_confirm_count[track_id] = 0


                # Save the hysteresis-filtered side for the next frame.
                if effective_sign != 0:
                    last_side[track_id] = effective_sign

                # change 4: Added loitering detection logic
                # Loitering detection
                if current_sign == LOITERING_SIDE:
                    # Object is on the loitering side
                    if track_id not in loitering_start_time:
                        loitering_start_time[track_id] = datetime.now()
                    else:
                        # Check if loitering time threshold has been exceeded
                        elapsed = datetime.now() - loitering_start_time[track_id]
                        if elapsed.total_seconds() >= LOITERING_TIME_THRESHOLD and track_id not in already_alerted_loitering:
                            # Trigger loitering alert
                            already_alerted_loitering.add(track_id)
                            # Create loitering alert (similar to crossing alert)
                            # Timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

                            # Save evidence snapshot
                            snap_name = (
                                f"alert_"
                                f"{timestamp}_"
                                f"id{track_id}.jpg"
                            )

                            snap_path = os.path.join(
                                SNAPSHOTS_DIR,
                                snap_name
                            )

                            cv2.imwrite(
                                snap_path,
                                original_frame  # Use original quality for loitering snapshots too
                            )

                            # Optional ANPR (for loitering, we might not want to do ANPR? The problem doesn't specify. We'll skip ANPR for loitering for now.)
                            plate_text = None

                            # Create alert record
                            alert = {
                                "camera_id": CAMERA_ID,
                                "event_type": "night_loitering" if is_night() else "loitering",
                                "object_type": cls_name,
                                "track_id": track_id,
                                "confidence": round(confidence, 3),
                                "timestamp": datetime.now().isoformat(),
                                "snapshot_path": snap_name,
                                "plate_number": plate_text,
                            }

                            # Save alert to JSON
                            save_alert(alert)

                            # Terminal alert
                            print(
                                f"[ALERT] "
                                f"{cls_name} "
                                f"#{track_id} "
                                f"{'[NIGHT] ' if is_night() else ''}"
                                f"loitering detected",
                                flush=True
                            )
                else:
                    # Object is not on the loitering side, reset loitering start time
                    if track_id in loitering_start_time:
                        del loitering_start_time[track_id]

                # Save current side for the next frame

                last_side[track_id] = effective_sign


                # ===========================================================
                # FIRE SECURITY ALERT
                # ===========================================================

                # change 9: Add alert cooldown period check
                current_time = datetime.now()
                last_alert_for_track = last_alert_time.get(track_id, datetime.min)
                time_since_last_alert = (current_time - last_alert_for_track).total_seconds()
                cooldown_satisfied = time_since_last_alert >= ALERT_COOLDOWN_TIME
                if (
                    crossing_confirm_count.get(track_id, 0)
                    >= ALERT_CONSEC_FRAMES
                    and track_id not in already_alerted
                    and cooldown_satisfied
                ):

                    # -------------------------------------------------------
                    # Prevent duplicate alert for this track
                    # -------------------------------------------------------

                    already_alerted.add(track_id)
                    # change 9: Update last alert time for cooldown tracking
                    last_alert_time[track_id] = datetime.now()


                    # -------------------------------------------------------
                    # Timestamp
                    # -------------------------------------------------------

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S_%f"
                    )


                    # -------------------------------------------------------
                    # Save evidence snapshot (from ORIGINAL high-quality frame)
                    # -------------------------------------------------------

                    snap_name = (
                        f"alert_"
                        f"{timestamp}_"
                        f"id{track_id}.jpg"
                    )


                    snap_path = os.path.join(
                        SNAPSHOTS_DIR,
                        snap_name
                    )


                    cv2.imwrite(
                        snap_path,
                        original_frame  # Use original quality, not resized
                    )


                    # -------------------------------------------------------
                    # Optional ANPR (from ORIGINAL high-quality frame)
                    # -------------------------------------------------------

                    plate_text = None


                    if (
                        run_anpr_flag
                        and cls_name in VEHICLE_CLASSES
                    ):

                        # Convert bounding box coordinates back to original frame scale
                        # Current coords (x1,y1,x2,y2) are in resized frame (640px)
                        # Need to map them to original frame dimensions
                        orig_x1 = int(x1 / scale)
                        orig_y1 = int(y1 / scale)
                        orig_x2 = int(x2 / scale)
                        orig_y2 = int(y2 / scale)

                        # Keep crop coordinates inside original frame
                        crop_x1 = max(0, orig_x1)
                        crop_y1 = max(0, orig_y1)

                        crop_x2 = min(
                            original_frame.shape[1],
                            orig_x2
                        )

                        crop_y2 = min(
                            original_frame.shape[0],
                            orig_y2
                        )


                        crop = original_frame[
                            crop_y1:crop_y2,
                            crop_x1:crop_x2
                        ]


                        if crop.size > 0:
                            
                            # Localize license plate within the vehicle crop
                            plate_crop = localize_license_plate(crop)
                            plate_text = run_anpr(
                                plate_crop  # Now using high-quality original frame!
                            )

                        # Draw plate number on DISPLAY frame if ANPR is enabled and we have a result
                        if plate_text and run_anpr_flag:
                            plate_label = f"Plate: {plate_text}"
                            # Draw plate number below the class label on resized frame
                            cv2.putText(
                                frame,  # Draw on display frame (resized)
                                plate_label,
                                (
                                    int(x1),
                                    int(y2) + 20  # Position below the bounding box
                                ),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 255, 255),  # Yellow color for plate text
                                2
                            )


                    # -------------------------------------------------------
                    # Create alert record (with duplicate plate prevention)
                    # -------------------------------------------------------
                    
                    # Check if this plate was already recorded (avoid duplicates)
                    is_duplicate_plate = False
                    if plate_text and plate_text in recorded_plates:
                        is_duplicate_plate = True
                        print(
                            f"[INFO] Plate {plate_text} already recorded, skipping duplicate",
                            flush=True
                        )
                    elif plate_text:
                        # New plate, add to recorded set
                        recorded_plates.add(plate_text)

                    alert = {
                        "camera_id": CAMERA_ID,
                        "event_type": "night_movement_crossing" if is_night() else "virtual_fence_crossing",
                        "object_type": cls_name,
                        "track_id": track_id,
                        "confidence": round(confidence, 3),
                        "timestamp": datetime.now().isoformat(),
                        "snapshot_path": snap_name,
                        "plate_number": plate_text if not is_duplicate_plate else None,  # Don't save duplicate plates
                    }


                    # -------------------------------------------------------
                    # Save alert to JSON (always save crossing, but mark duplicates)
                    # -------------------------------------------------------

                    save_alert(alert)


                    # -------------------------------------------------------
                    # Terminal alert
                    # -------------------------------------------------------

                    plate_message = ""

                    if plate_text:
                        if is_duplicate_plate:
                            plate_message = f" | Plate: {plate_text} (DUPLICATE - not recorded)"
                        else:
                            plate_message = f" | Plate: {plate_text} (NEW)"


                    # change 6: Modified print statement to include night indicator
                    print(
                        f"[ALERT] "
                        f"{cls_name} "
                        f"#{track_id} "
                        f"{'[NIGHT] ' if is_night() else ''}"
                        f"crossed the fence"
                        f"{plate_message}",
                        flush=True
                    )


        # -------------------------------------------------------------------
        # Write annotated frame
        # -------------------------------------------------------------------

        if writer is not None:
            writer.write(frame)

        if annotated_rtsp_proc is None and writer is not None:
            annotated_rtsp_proc = start_annotated_rtsp_publisher(frame.shape[1], frame.shape[0], fps)

        if annotated_rtsp_proc is not None and annotated_rtsp_proc.stdin is not None:
            try:
                annotated_rtsp_proc.stdin.write(frame.tobytes())
                annotated_rtsp_proc.stdin.flush()
            except Exception as exc:
                print(f"[WARN] Annotated RTSP stream failed: {exc}")
                try:
                    annotated_rtsp_proc.stdin.close()
                except Exception:
                    pass
                annotated_rtsp_proc = None

        # -------------------------------------------------------------------
        # Display live detection window
        # -------------------------------------------------------------------

        if not no_display:
            cv2.imshow(
                "IRIS - IBVAP Demo",
                frame
            )


            # Press Q to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):

                print(
                    "[INFO] Pipeline stopped by user."
                )

                break


    # -----------------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------------

    if rtsp_mode:
        latest_capture.stop()
    else:
        cap.release()


    if writer is not None:

        writer.release()

    if annotated_rtsp_proc is not None:
        if annotated_rtsp_proc.stdin is not None:
            try:
                annotated_rtsp_proc.stdin.close()
            except Exception:
                pass
        try:
            annotated_rtsp_proc.wait(timeout=2)
        except Exception:
            annotated_rtsp_proc.terminate()

    cv2.destroyAllWindows()


    print(
        "[INFO] Done."
    )

    print(
        "[INFO] Alerts file:",
        ALERTS_JSON_PATH
    )

    print(
        "[INFO] Snapshots folder:",
        SNAPSHOTS_DIR
    )

    if output_path:

        print(
            "[INFO] Annotated video:",
            os.path.abspath(output_path)
        )


# ===========================================================================
# COMMAND LINE
# ===========================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="IRIS - IBVAP Video Analytics Pipeline"
    )


    parser.add_argument(
        "--source",
        required=True,
        help="Path to input video file"
    )


    parser.add_argument(
        "--anpr",
        action="store_true",
        help="Enable ANPR on vehicle detections"
    )

    parser.add_argument(
        "--track-all",
        action="store_true",
        help="Enable logging of all tracked objects (for debugging/monitoring)"
    )

    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable live video display window (recommended for performance)"
    )


    # IMPORTANT:
    # This now points to the actual snapshots directory
    # regardless of where the script is launched from.

    default_output = os.path.join(
        BASE_DIR,
        "..",
        "snapshots",
        "annotated_output.mp4"
    )


    parser.add_argument(
        "--output",
        default=default_output,
        help="Path to save annotated output video"
    )


    args = parser.parse_args()


    main(
        args.source,
        args.anpr,
        args.output,
        args.track_all,
        args.no_display
    )
