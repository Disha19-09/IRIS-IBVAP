# Alert Detection Fixes Applied

## 🔧 Changes Made

### 1. Dynamic Virtual Fence Positioning
**Problem:** Fixed fence at y=300 doesn't work for all videos with different resolutions/compositions.

**Solution:** Fence now positioned at configurable percentage of frame height.

```python
FENCE_HEIGHT_RATIO = 0.5  # 50% of frame height (middle of screen)
```

**Benefits:**
- Works automatically for any video resolution
- Adapts to different camera angles
- Shows calculated position in console: `[INFO] Virtual fence positioned at y=240 (50% of frame height 480px)`

### 2. Reduced Confirmation Frames
**Problem:** Required 2 consecutive frames to confirm crossing (too strict).

**Solution:** Reduced to 1 frame for immediate detection.

```python
ALERT_CONSEC_FRAMES = 1  # Was 2
```

### 3. More Sensitive Detection Thresholds
**Problem:** Hysteresis and distance thresholds were too conservative.

**Solution:** Reduced thresholds for better sensitivity.

```python
SIDE_HYSTERESIS = 3      # Was 5 (pixels buffer zone)
MIN_CROSS_DISTANCE = 5   # Was 10 (minimum crossing distance)
ALERT_COOLDOWN_TIME = 3.0  # Was 5.0 (seconds between alerts)
```

---

## 🧪 Testing Tools

### Quick Fence Position Test
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe test_fence_position.py
```

This will:
- Show the fence line on each sample video
- Display frame dimensions
- Confirm fence positioning
- Press any key to cycle through videos

### Run Detection with Verbose Output
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
```

Watch for:
- `[INFO] Virtual fence positioned at y=XXX`
- `[ALERT] Person has crossed the virtual fence (Track #X)`
- Detection window showing red line across frame

---

## ⚙️ Adjusting Fence Position

If alerts still don't trigger, adjust the fence ratio:

### Edit `detect_track_fence.py`:
```python
FENCE_HEIGHT_RATIO = 0.5  # Try these values:
# 0.3 = Upper third (for overhead cameras)
# 0.5 = Middle (default, works for most)
# 0.7 = Lower third (for low-angle cameras)
```

### Visual Guide:
```
Frame Height
┌─────────────┐
│             │ ← 0.0 = Top
│             │
│─────────────│ ← 0.3 = Upper third
│             │
│─────────────│ ← 0.5 = Middle (default)
│             │
│─────────────│ ← 0.7 = Lower third
│             │
└─────────────┘ ← 1.0 = Bottom
```

---

## 🎯 Per-Video Testing

Test each sample video individually:

### test.mp4
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
```

### test_2.mp4
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test_2.mp4
```

### test_3.mp4
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test_3.mp4
```

### test_4.mp4
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test_4.mp4
```

---

## 🔍 Diagnostic Checklist

### If No Alerts Generated:

1. **Check Fence Position**
   - Run `test_fence_position.py` to visualize
   - Ensure red line crosses where objects move
   - Adjust `FENCE_HEIGHT_RATIO` if needed

2. **Check Object Detection**
   - Watch the CV window
   - Verify bounding boxes appear around objects
   - If no boxes: increase `CONF_THRESHOLD` to 0.4 or 0.3

3. **Check Console Output**
   - Look for: `[INFO] Virtual fence positioned at y=XXX`
   - Look for: `[ALERT] ...` messages
   - No alerts = objects not crossing or fence mispositioned

4. **Check Video Content**
   - Some videos may have no crossings at the fence line
   - Try different `FENCE_HEIGHT_RATIO` values

### If Too Many False Alerts:

1. **Increase confidence threshold:**
   ```python
   CONF_THRESHOLD = 0.6  # Was 0.5
   ```

2. **Increase confirmation frames:**
   ```python
   ALERT_CONSEC_FRAMES = 2  # Was 1
   ```

3. **Increase cooldown time:**
   ```python
   ALERT_COOLDOWN_TIME = 5.0  # Was 3.0
   ```

---

## 📊 Expected Console Output

### On Startup:
```
[INFO] Loading YOLO model...
[INFO] Starting pipeline on: ..\sample_videos\test.mp4
[INFO] Virtual fence positioned at y=240 (50% of frame height 480px)
[INFO] Output video: ..\snapshots\annotated_output.mp4
```

### During Detection:
```
[ALERT] Person has crossed the virtual fence (Track #1)
[ALERT] Car has crossed the virtual fence (Track #5)
[ALERT] Person has crossed the virtual fence (Track #2)
```

### With ANPR:
```
[ANPR] Detected plate: ABC1234 on car #5
[ALERT] Car has crossed the virtual fence (Track #5) | License Plate: ABC1234
```

---

## 🎨 Visual Indicators

### On Video Window:
- **Red dashed line** = Virtual fence
- **Green boxes** = Person detected
- **Orange boxes** = Vehicle detected
- **Yellow background box** = License plate (with ANPR)

### Dashboard:
- **Active Alerts** = Shows last 60 seconds of alerts
- **ANPR Tab** = Shows all license plates detected

---

## 🚀 Quick Fix Commands

### If Fence Too High (Missing Ground-Level Crossings):
```python
# Edit detect_track_fence.py
FENCE_HEIGHT_RATIO = 0.7  # Move to lower third
```

### If Fence Too Low (Missing Overhead Crossings):
```python
# Edit detect_track_fence.py
FENCE_HEIGHT_RATIO = 0.3  # Move to upper third
```

### If Detection Too Slow:
```python
# Edit detect_track_fence.py
PROCESS_EVERY_N_FRAMES = 1  # Process every frame (was 2)
```

### If Too Sensitive:
```python
# Edit detect_track_fence.py
ALERT_CONSEC_FRAMES = 3    # Require 3 frames confirmation
CONF_THRESHOLD = 0.6        # Higher confidence needed
```

---

## 🔄 Restart After Changes

After modifying `detect_track_fence.py`:

1. Stop the CV pipeline (press 'q' or Ctrl+C)
2. Restart:
   ```powershell
   cd cv_pipeline
   ..\venv\Scripts\python.exe detect_track_fence.py --source VIDEO_PATH
   ```

---

## 📝 Configuration Summary

### Current Settings (Optimized):
```python
FENCE_HEIGHT_RATIO = 0.5       # Middle of frame
ALERT_CONSEC_FRAMES = 1        # Immediate detection
PROCESS_EVERY_N_FRAMES = 2     # Balance speed/accuracy
CONF_THRESHOLD = 0.5           # Standard confidence
SIDE_HYSTERESIS = 3            # Moderate buffer
MIN_CROSS_DISTANCE = 5         # Minimum crossing pixels
ALERT_COOLDOWN_TIME = 3.0      # 3 seconds between alerts
```

### For High-Accuracy (Fewer False Positives):
```python
ALERT_CONSEC_FRAMES = 2
CONF_THRESHOLD = 0.6
ALERT_COOLDOWN_TIME = 5.0
```

### For High-Sensitivity (More Detections):
```python
ALERT_CONSEC_FRAMES = 1
CONF_THRESHOLD = 0.4
SIDE_HYSTERESIS = 2
```

---

## ✅ Success Indicators

You should see:
- [x] Console shows fence position on startup
- [x] Red line visible in CV window
- [x] Objects detected (bounding boxes visible)
- [x] `[ALERT]` messages when objects cross line
- [x] Dashboard updates with new alerts
- [x] No errors in console

---

## 🐛 Still Having Issues?

1. **Run fence position test:**
   ```powershell
   cd cv_pipeline
   ..\venv\Scripts\python.exe test_fence_position.py
   ```

2. **Check if objects are detected at all:**
   - Look for bounding boxes in CV window
   - If none: YOLO model issue, not fence issue

3. **Manually adjust fence:**
   ```python
   # Temporarily use manual positioning
   LINE_START = (0, 200)   # Try different Y values
   LINE_END = (640, 200)
   ```

4. **Try a different video:**
   - Some videos may have no crossings
   - test_4.mp4 usually has most activity

---

## 📞 Debug Output

Enable verbose tracking (optional):
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4 --track-all
```

This logs every tracked object, helping diagnose detection issues.
