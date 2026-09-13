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

HOW TO RUN:
  python detect_track_fence.py --source ../sample_videos/test.mp4

For ANPR:
  python detect_track_fence.py --source ../sample_videos/test.mp4 --anpr

No GPU needed. Runs on CPU.
"""

import argparse
import json
import os
import threading
import time
from datetime import datetime

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# CONFIG - tune these for your demo
# ---------------------------------------------------------------------------

MODEL_PATH = "yolov8n.pt"          # Nano model -> fastest on CPU
CONF_THRESHOLD = 0.4               # Detection confidence cutoff
RESIZE_WIDTH = 640                 # Resize frames for speed
PROCESS_EVERY_N_FRAMES = 1         # Set to 2 or 3 if video is laggy
ALERT_CONSEC_FRAMES = 3             # Frames required to confirm crossing


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
    Append a new alert to alerts.json.
    """

    alerts = load_alerts()

    alerts.append(alert)

    with open(
        ALERTS_JSON_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            alerts,
            f,
            indent=2
        )


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

        results = reader.readtext(crop_img)

        if not results:
            return None

        # Select the OCR result with the highest confidence
        best = max(
            results,
            key=lambda r: r[2]
        )

        text = best[1]
        conf = best[2]

        if conf > 0.3:

            return text.strip().upper()

        return None

    except Exception as e:

        print(
            f"[WARN] ANPR failed: {e}"
        )

        return None

# ---------------------------------------------------------------------------
# RTSP HELPERS
# ---------------------------------------------------------------------------

def is_rtsp(source):
    """
    Check whether the source is an RTSP stream.
    """
    return (
        isinstance(source, str)
        and source.lower().startswith("rtsp://")
    )


class LatestFrameCapture:
    """
    Continuously reads an RTSP stream in a background thread.

    Only the latest frame is kept, so the AI pipeline does not
    build up a backlog of old frames.
    """

    def __init__(self, source):

        self.source = source

        self.cap = cv2.VideoCapture(source)

        if is_rtsp(source):
            self.cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

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

            self.thread.join(
                timeout=1
            )

        self.cap.release()

# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def main(source, run_anpr_flag, output_path):

    # -----------------------------------------------------------------------
    # Load YOLO model
    # -----------------------------------------------------------------------

    print("[INFO] Loading YOLO model...")

    model = YOLO(MODEL_PATH)


    # -----------------------------------------------------------------------
    # Open video source
    # -----------------------------------------------------------------------

    rtsp_mode = is_rtsp(source)

    if rtsp_mode:

        latest_capture = LatestFrameCapture(source).start()

        # Give the capture thread a moment to receive the first frame
        time.sleep(0.5)

        if not latest_capture.cap.isOpened():

            print(
                f"[ERROR] Could not open RTSP source: {source}"
            )

            latest_capture.stop()

            return

        # RTSP streams may not report FPS correctly
        fps = latest_capture.cap.get(
            cv2.CAP_PROP_FPS
        ) or 20

    else:

        latest_capture = None

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():

            print(
                f"[ERROR] Could not open video source: {source}"
            )

            return

        # Get original video FPS
        fps = cap.get(
            cv2.CAP_PROP_FPS
        ) or 20


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


    # track IDs that have already generated an alert
    already_alerted = set()


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

        # Run YOLO + ByteTrack on the current frame
        results = model.track(
            source=frame,
            conf=CONF_THRESHOLD,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        result = results[0]

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

                if (
                    prev_sign is not None
                    and current_sign != 0
                    and prev_sign != 0
                    and current_sign != prev_sign
                ):

                    # Object changed sides.
                    #
                    # This is the first frame of the potential crossing.

                    crossing_confirm_count[track_id] = 1

                    crossing_direction[track_id] = current_sign


                # -----------------------------------------------------------
                # Confirm crossing
                # -----------------------------------------------------------

                elif (
                    track_id in crossing_confirm_count
                    and crossing_confirm_count[track_id] > 0
                ):

                    # The object already crossed.
                    # Check whether it remains on the new side.

                    if (
                        current_sign
                        == crossing_direction.get(track_id)
                    ):

                        crossing_confirm_count[track_id] += 1

                    else:

                        # Object did not remain on the new side.
                        # Treat it as a false crossing.

                        crossing_confirm_count[track_id] = 0

                        crossing_direction.pop(
                            track_id,
                            None
                        )


                else:

                    # No crossing currently happening.

                    crossing_confirm_count[track_id] = 0


                # Save current side for the next frame

                last_side[track_id] = current_sign


                # ===========================================================
                # FIRE SECURITY ALERT
                # ===========================================================

                if (
                    crossing_confirm_count.get(track_id, 0)
                    >= ALERT_CONSEC_FRAMES
                    and track_id not in already_alerted
                ):

                    # -------------------------------------------------------
                    # Prevent duplicate alert for this track
                    # -------------------------------------------------------

                    already_alerted.add(track_id)


                    # -------------------------------------------------------
                    # Timestamp
                    # -------------------------------------------------------

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
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


                    # -------------------------------------------------------
                    # Create alert record
                    # -------------------------------------------------------

                    alert = {

                        "id":
                            f"{timestamp}_{track_id}",

                        "type":
                            "virtual_fence_crossing",

                        "object_class":
                            cls_name,

                        "track_id":
                            track_id,

                        "confidence":
                            round(confidence, 3),

                        "timestamp":
                            datetime.now().isoformat(),

                        "snapshot":
                            snap_name,

                        "plate_text":
                            plate_text,
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


                    print(
                        f"[ALERT] "
                        f"{cls_name} "
                        f"#{track_id} "
                        f"crossed the fence"
                        f"{plate_message}"
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

    if rtsp_mode:

        latest_capture.stop()

    else:

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
        args.output
    )
