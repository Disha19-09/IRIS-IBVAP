# ANPR Fix - Plate Recognition Now Enabled

## Problem
The ANPR (Automatic Number Plate Recognition) feature was not working because the `--anpr` flag was not being passed to the CV pipeline when starting the system.

## What Was Fixed
1. **START.bat** - Added `--anpr` flag to enable plate recognition on system startup
2. **cv_pipeline/run_pipeline.bat** - Added `--anpr` flag for manual pipeline runs

## Solution Details

### The Issue
The CV pipeline code includes full ANPR functionality using EasyOCR, but it's disabled by default. The `--anpr` command-line flag must be passed to activate it:

```bash
python detect_track_fence.py --source <video> --anpr
```

Without the `--anpr` flag, the pipeline:
- ✅ Detects vehicles (car, truck, bus, motorcycle)
- ✅ Tracks them across frames
- ✅ Logs fence crossing events
- ❌ Does NOT run plate recognition (plate_number stays null)

With the `--anpr` flag, the pipeline:
- ✅ All of the above, PLUS:
- ✅ Crops vehicle bounding boxes
- ✅ Runs EasyOCR on the license plate area
- ✅ Saves recognized plate numbers to the database
- ✅ Displays plate numbers on the video overlay

### Changes Made

**File: START.bat**
```batch
# Before:
python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1 --no-display

# After:
python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1 --no-display --anpr
```

**File: cv_pipeline/run_pipeline.bat**
```batch
# Before:
python detect_track_fence.py --source "%SOURCE%"

# After:
python detect_track_fence.py --source "%SOURCE%" --anpr
```

## How to Apply the Fix

### Option 1: Restart the System (Recommended)
1. **Stop all services:**
   - Double-click `STOP_ALL.bat`
   - Wait for all processes to terminate

2. **Start the system with ANPR enabled:**
   - Double-click `START.bat`
   - Wait ~30 seconds for all services to start

3. **Open the dashboard:**
   - Go to http://127.0.0.1:5173/
   - Login with admin/admin123
   - Navigate to the ANPR tab

### Option 2: Restart Only the CV Pipeline
If you want to avoid restarting everything:

1. **Stop the CV Pipeline window:**
   - Find the window titled "5-CV-Pipeline"
   - Close it or press Ctrl+C

2. **Start the CV Pipeline with ANPR:**
   - Open Command Prompt
   - Navigate to the project folder:
     ```cmd
     cd c:\Users\DR4KEN\Documents\HC\IRIS-IBVAP
     ```
   - Activate the virtual environment:
     ```cmd
     call venv\Scripts\activate.bat
     ```
   - Run the pipeline with ANPR:
     ```cmd
     cd cv_pipeline
     python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1 --no-display --anpr
     ```

## Verifying ANPR is Working

### In the Terminal
When ANPR is enabled, you'll see:
```
[INFO] Loading EasyOCR model (first time only, may take a minute)...
[ALERT] car #123 crossed the fence | Plate: ABC1234
```

### In the Dashboard
1. Go to the **ANPR** tab
2. Wait for vehicles to cross the virtual fence
3. You should see:
   - Plate numbers appearing in the "Latest Detection" panel
   - Plate information in the "Plate Information" panel
   - Recognition log showing all detected plates

### In the Database
Check the database directly:
```cmd
cd backend
sqlite3 alerts.db "SELECT id, object_type, plate_number, timestamp FROM alerts WHERE plate_number IS NOT NULL LIMIT 10;"
```

## Technical Details

### ANPR Pipeline Flow
1. **Vehicle Detection**: YOLOv8 detects cars, trucks, buses, motorcycles
2. **Fence Crossing**: Object crosses virtual fence line
3. **Crop Vehicle**: Extract vehicle bounding box from frame
4. **Localize Plate**: Focus on lower-middle section (typical plate location)
5. **Preprocessing**: Enhance image with CLAHE and Gaussian blur
6. **OCR**: EasyOCR reads text from plate region
7. **Sanitization**: Clean OCR result (remove special chars, uppercase)
8. **Validation**: Ensure minimum 3 characters
9. **Save to Database**: Store plate_number in alerts table
10. **Display**: Show on video overlay and dashboard

### Performance Notes
- **First Run**: EasyOCR downloads language models (~50MB) on first use
- **CPU Performance**: ANPR adds ~100-200ms per vehicle detection
- **Accuracy**: Depends on video quality, lighting, plate angle
- **Confidence Threshold**: 0.3 minimum (configurable in code)

### Configuration Options
In `detect_track_fence.py`, you can adjust:
```python
ANPR_CONFIDENCE_THRESHOLD = 0.3    # Minimum confidence for plate text
```

Lower values = more detections but more false positives
Higher values = fewer detections but higher accuracy

## Troubleshooting

### No Plates Detected
1. **Check ANPR is enabled**: Look for "Loading EasyOCR model" in terminal
2. **Check video quality**: Plates must be readable to humans
3. **Check vehicle types**: Only car/truck/bus/motorcycle trigger ANPR
4. **Check fence crossings**: Plates only recorded when vehicle crosses fence

### EasyOCR Not Loading
1. **Check dependencies**:
   ```cmd
   cd c:\Users\DR4KEN\Documents\HC\IRIS-IBVAP
   call venv\Scripts\activate.bat
   pip show easyocr
   ```
2. **Reinstall if needed**:
   ```cmd
   pip install --upgrade easyocr
   ```

### Low Recognition Rate
- Increase video resolution in START.bat (currently 640x480)
- Improve lighting conditions in test videos
- Use videos with clearer, front-facing plate views
- Lower ANPR_CONFIDENCE_THRESHOLD in detect_track_fence.py

## Summary
✅ **ANPR functionality exists and is fully implemented**
✅ **Fix applied: Added --anpr flag to startup scripts**
✅ **Ready to use: Just restart the system**

The ANPR feature was already coded but simply needed to be enabled. Now it will automatically recognize and record license plates for all vehicles that cross the virtual fence.
