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
from datetime import datetime
import csv
import requests

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# CONFIG - tune these for your demo
# ---------------------------------------------------------------------------

MODEL_PATH = "yolov8n.pt"          # Nano model -> fastest on CPU
CONF_THRESHOLD = 0.4               # Detection confidence cutoff
BACKEND_URL = "http://localhost:8000/api/events"
CAMERA_ID = "CAM_01"
RESIZE_WIDTH = 640                 # Resize frames for speed
PROCESS_EVERY_N_FRAMES = 1         # Set to 2 or 3 if video is laggy
ALERT_CONSEC_FRAMES = 3             # Frames required to confirm crossing
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
ANPR_CONFIDENCE_THRESHOLD = 0.3    # Minimum confidence for ANPR text detection


# ---------------------------------------------------------------------------
# VIRTUAL FENCE
# ---------------------------------------------------------------------------
# Coordinates are based on the resized 640px-wide frame.
# Change the Y value depending on where you want your security boundary.

LINE_START = (0, 300)
LINE_END = (640, 300)


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
    """
    Load EasyOCR only when needed.
    This avoids loading the OCR model when running normal detection.
    """

    global _ocr_reader

    if _ocr_reader is None:
        import easyocr

        print(
            "[INFO] Loading EasyOCR model "
            "(first time only, may take a minute)..."
        )

        _ocr_reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    return _ocr_reader


# ---------------------------------------------------------------------------
# ALERT FUNCTIONS
# ---------------------------------------------------------------------------

def load_alerts():
    """
    Load existing alerts from alerts.json.
    Returns an empty list if the file does not exist.
    """

    if os.path.exists(ALERTS_JSON_PATH):

        try:

            with open(
                ALERTS_JSON_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except (
            json.JSONDecodeError,
            FileNotFoundError
        ):

            return []

    return []


def save_alert(alert):
    """
    Send the alert to the backend's /api/events endpoint so it gets
    persisted to the database and broadcast over WebSocket.
    Falls back to a local JSON file if the backend is unreachable,
    so you don't lose alerts if the backend crashes mid-demo.
    """
    try:
        response = requests.post(BACKEND_URL, json=alert, timeout=2)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Backend unreachable, saving locally instead: {e}")
        alerts = load_alerts()
        alerts.append(alert)
        with open(ALERTS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2)


def send_tracking_data(tracking_info):
    """
    Send tracking data to the backend's /api/events endpoint for dashboard display.
    Falls back to local tracking file if backend is unreachable.
    """
    try:
        response = requests.post(BACKEND_URL, json=tracking_info, timeout=2)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Silently fail for tracking data to avoid spamming warnings
        # Tracking data is less critical than alerts
        pass


# ---------------------------------------------------------------------------
# VIRTUAL FENCE GEOMETRY
# ---------------------------------------------------------------------------

def side_of_line(point, line_start, line_end):
    """
    Returns the position of a point relative to the fence line.

    Positive value  -> one side
    Negative value  -> opposite side
    Zero             -> exactly on the line
    """

    x, y = point

    x1, y1 = line_start
    x2, y2 = line_end

    return (
        (x2 - x1) * (y - y1)
        - (y2 - y1) * (x - x1)
    )


def distance_from_point_to_line(point, line_start, line_end):
    """
    Returns the perpendicular distance from a point to a line defined by two points.
    """
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    # Calculate the area of the parallelogram formed by the points
    area = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1))

    # Calculate the length of the line segment
    line_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    # Avoid division by zero
    if line_length == 0:
        return 0

    # Distance = area / base_length
    return area / line_length


def preprocess_for_anpr(image):
    """
    Simple preprocessing to improve OCR accuracy on license plate regions.
    Converts to grayscale and applies contrast enhancement.
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # Apply slight Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

    return blurred


# change 2: Added is_night() function for night movement detection
def is_night():
    """
    Returns True if current time is within night hours.
    """
    now = datetime.now()
    hour = now.hour
    if NIGHT_START_HOUR > NIGHT_END_HOUR:
        # Night spans midnight (e.g., 22 to 6)
        return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR
    else:
        # Night within same day
        return NIGHT_START_HOUR <= hour < NIGHT_END_HOUR


# ---------------------------------------------------------------------------
# ANPR
# ---------------------------------------------------------------------------

def run_anpr(crop_img):
    """
    Runs OCR on a cropped vehicle image.

    NOTE:
    This is a prototype ANPR implementation using OCR on the
    complete vehicle crop. It is not a dedicated license-plate
    detection model.
    """

    try:

        reader = get_ocr_reader()

        # Preprocess the image to improve OCR accuracy
        processed_img = preprocess_for_anpr(crop_img)

        results = reader.readtext(processed_img)

        if not results:
            return None

        # Select the OCR result with the highest confidence
        best = max(
            results,
            key=lambda r: r[2]
        )

        text = best[1]
        conf = best[2]

        if conf > ANPR_CONFIDENCE_THRESHOLD:

            return text.strip().upper()

        return None

    except Exception as e:

        print(
            f"[WARN] ANPR failed: {e}"
        )

        return None


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def main(source, run_anpr_flag, output_path, track_all_flag=False):
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

    if isinstance(source, str) and source.lower().startswith("rtsp://"):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

    if not cap.isOpened():

        print(
            f"[ERROR] Could not open video source: {source}"
        )

        return


    # Get original video FPS
    fps = cap.get(cv2.CAP_PROP_FPS) or 20


    # Video writer will be initialized after the first frame
    writer = None


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


    # -----------------------------------------------------------------------
    # Frame counter
    # -----------------------------------------------------------------------

    frame_idx = 0


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


    # -----------------------------------------------------------------------
    # YOLO detection + tracking
    # -----------------------------------------------------------------------

    for result in model.track(
        source=source,
        conf=CONF_THRESHOLD,
        persist=True,
        tracker="bytetrack.yaml",
        stream=True,
        verbose=False,
    ):

        frame_idx += 1


        # Process every Nth frame
        if frame_idx % PROCESS_EVERY_N_FRAMES != 0:

            continue


        # -------------------------------------------------------------------
        # Get original frame
        # -------------------------------------------------------------------

        frame = result.orig_img

        h, w = frame.shape[:2]


        # Scale frame to RESIZE_WIDTH
        scale = RESIZE_WIDTH / w

        new_height = int(h * scale)

        frame = cv2.resize(
            frame,
            (RESIZE_WIDTH, new_height)
        )


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

                # change 10: Improved side determination with hysteresis
                # Calculate distance from line for hysteresis-based side determination
                distance_from_line = distance_from_point_to_line(
                    (cx, cy), LINE_START, LINE_END
                )

                # Apply hysteresis: only consider crossing if object has moved
                # sufficiently past the line (reduces jitter near boundary)
                effective_sign = 0
                if distance_from_line > SIDE_HYSTERESIS:
                    effective_sign = 1
                elif distance_from_line < -SIDE_HYSTERESIS:
                    effective_sign = -1
                # If within hysteresis zone, maintain previous sign to avoid jitter
                elif prev_sign is not None:
                    effective_sign = prev_sign

                prev_sign = last_side.get(track_id, 0)  # Default to 0 if no previous side

                if (
                    prev_sign is not None
                    and prev_sign != 0
                    and effective_sign != 0
                    and effective_sign != prev_sign
                ):
                    # Object changed sides with hysteresis applied.
                    #
                    # This is the first frame of the potential crossing.

                    # change 7: Add minimum distance threshold to reduce false positives
                    # Only consider crossing valid if object has moved sufficient distance
                    if distance_from_line >= MIN_CROSS_DISTANCE or distance_from_line <= -MIN_CROSS_DISTANCE:
                        crossing_confirm_count[track_id] = 1
                        crossing_direction[track_id] = effective_sign

                        # change 8: For hysteresis - track initial crossing point distance
                        # Store the distance from line when crossing was first detected
                        crossing_initial_distance[track_id] = distance_from_line


                # -----------------------------------------------------------
                # Confirm crossing
                # -----------------------------------------------------------

                elif (
                    track_id in crossing_confirm_count
                    and crossing_confirm_count[track_id] > 0
                ):

                    # The object already crossed.
                    # Check whether it remains on the new side.

                    # change 10: Apply hysteresis to current sign as well for consistency
                    distance_from_line_current = distance_from_point_to_line(
                        (cx, cy), LINE_START, LINE_END
                    )

                    effective_current_sign = 0
                    if distance_from_line_current > SIDE_HYSTERESIS:
                        effective_current_sign = 1
                    elif distance_from_line_current < -SIDE_HYSTERESIS:
                        effective_current_sign = -1
                    # If within hysteresis zone, maintain previous effective sign to avoid jitter
                    elif prev_sign is not None:
                        effective_current_sign = prev_sign

                    # change 8: Enhanced confirmation logic with directional consistency
                    # Check not just side consistency but also that movement is away from line
                    is_on_expected_side = (
                        effective_current_sign == crossing_direction.get(track_id)
                    )

                    # change 7: Additional distance check - object should continue to move away
                    # from the line or at least not move back significantly
                    initial_distance = crossing_initial_distance.get(track_id, 0)
                    distance_change = distance_from_line_current - initial_distance

                    # Object is considered still crossing if:
                    # 1. It's on the expected side (with hysteresis)
                    # 2. It has not moved back past the initial crossing point by more than hysteresis threshold
                    is_consistent_movement = is_on_expected_side and distance_change > -SIDE_HYSTERESIS

                    if is_consistent_movement:

                        crossing_confirm_count[track_id] += 1

                    else:

                        # Object did not remain on the new side or moved back.
                        # Treat it as a false crossing.

                        crossing_confirm_count[track_id] = 0

                        crossing_direction.pop(
                            track_id,
                            None
                        )

                        crossing_initial_distance.pop(
                            track_id,
                            None
                        )


                else:

                    # No crossing currently happening.

                    crossing_confirm_count[track_id] = 0

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
                                frame
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

                last_side[track_id] = current_sign


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
                    # Save evidence snapshot
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
                        frame
                    )


                    # -------------------------------------------------------
                    # Optional ANPR
                    # -------------------------------------------------------

                    plate_text = None


                    if (
                        run_anpr_flag
                        and cls_name in VEHICLE_CLASSES
                    ):

                        # Keep crop coordinates inside frame
                        crop_x1 = max(0, int(x1))
                        crop_y1 = max(0, int(y1))

                        crop_x2 = min(
                            frame.shape[1],
                            int(x2)
                        )

                        crop_y2 = min(
                            frame.shape[0],
                            int(y2)
                        )


                        crop = frame[
                            crop_y1:crop_y2,
                            crop_x1:crop_x2
                        ]


                        if crop.size > 0:

                            plate_text = run_anpr(
                                crop
                            )

                        # Draw plate number on frame if ANPR is enabled and we have a result
                        if plate_text and run_anpr_flag:
                            plate_label = f"Plate: {plate_text}"
                            # Draw plate number below the class label
                            cv2.putText(
                                frame,
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
                    # Create alert record
                    # -------------------------------------------------------

                    alert = {
                        "camera_id": CAMERA_ID,
                        "event_type": "night_movement_crossing" if is_night() else "virtual_fence_crossing",
                        "object_type": cls_name,
                        "track_id": track_id,
                        "confidence": round(confidence, 3),
                        "timestamp": datetime.now().isoformat(),
                        "snapshot_path": snap_name,
                        "plate_number": plate_text,
                    }


                    # -------------------------------------------------------
                    # Save alert to JSON
                    # -------------------------------------------------------

                    save_alert(alert)


                    # -------------------------------------------------------
                    # Terminal alert
                    # -------------------------------------------------------

                    plate_message = ""

                    if plate_text:

                        plate_message = (
                            f" | Plate: {plate_text}"
                        )


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


        # -------------------------------------------------------------------
        # Display live detection window
        # -------------------------------------------------------------------

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

    cap.release()


    if writer is not None:

        writer.release()


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
        args.track_all
    )
