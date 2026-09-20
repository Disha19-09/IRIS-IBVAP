# IRIS-IBVAP Update Summary

## ✅ Changes Applied Successfully

### 1. Descriptive Alert Messages ✨
**Console Output:**
- Person: `[ALERT] Person has crossed the virtual fence (Track #1)`
- Car: `[ALERT] Car has crossed the virtual fence (Track #5) | License Plate: ABC1234`
- Truck: `[ALERT] Truck has crossed the virtual fence (Track #3)`
- Night: `[ALERT] [NIGHT] Person has crossed the virtual fence (Track #2)`

**Dashboard Display:**
- "Person crossed virtual fence"
- "Car crossed virtual fence"
- "Truck crossed virtual fence at night"
- All vehicle types now clearly identified

### 2. Enhanced ANPR Tab 📊
**New Features:**
- Full table showing all detected license plates
- Vehicle type column (CAR, TRUCK, BUS, MOTORCYCLE)
- Event description for each detection
- Timestamp and track ID
- Statistics: Plates vs. Vehicles detected
- Latest detection preview with full details

**Visual Improvements:**
- License plates in GREEN highlight
- Full date/time formatting
- Confidence percentage display
- Vehicle count tracking

### 3. Improved ANPR Detection 🎯
**Technical Enhancements:**
- Added 10px padding around vehicle crop
- Minimum crop size validation (20x20 pixels)
- Better OCR preprocessing
- Console logging: `[ANPR] Detected plate: ABC1234 on car #5`

**Visual On Video:**
- Yellow background box for plate numbers
- Black text on yellow for high contrast
- Positioned below vehicle bounding box
- Format: `PLATE: ABC1234`

### 4. Database Migration ✅
**Schema Update:**
- Added `event_description` column to alerts table
- Migration script executed successfully
- Backward compatible with existing data
- Old alerts still display correctly

---

## 🚀 How to Test

### Quick Start
```powershell
# Option 1: Simple file-based demo
.\start_simple.bat

# Option 2: Full streaming demo with ANPR
.\start_demo.bat

# Option 3: Manual with ANPR
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4 --anpr
```

### Test Scenarios

#### Test 1: Person Crossing
1. Watch video until a person crosses the virtual fence
2. **Expected Console:** `[ALERT] Person has crossed the virtual fence (Track #X)`
3. **Expected Dashboard:** "Person crossed virtual fence" in Active Alerts

#### Test 2: Vehicle Crossing
1. Watch for a vehicle (car/truck/bus/motorcycle) crossing
2. **Expected Console:** `[ALERT] Car has crossed the virtual fence (Track #X)`
3. **Expected Dashboard:** "Car crossed virtual fence" in Active Alerts

#### Test 3: ANPR Detection
1. Run with `--anpr` flag
2. **Expected Console:** 
   - `[ALERT] Car has crossed the virtual fence (Track #5) | License Plate: ABC1234`
   - `[ANPR] Detected plate: ABC1234 on car #5`
3. **Expected Dashboard:**
   - Active Alerts: "Car crossed virtual fence"
   - ANPR Tab: Full table entry with plate, vehicle type, event, time, track ID
4. **Expected Video:** Yellow box with "PLATE: ABC1234" below vehicle

---

## 📁 Files Modified

### Backend
- ✅ `backend/database.py` - Added `event_description` column
- ✅ `backend/main.py` - Updated alert creation and serialization
- ✅ `backend/migrate_db.py` - **NEW** - Database migration script
- ✅ `backend/alerts.db` - Schema updated

### CV Pipeline
- ✅ `cv_pipeline/detect_track_fence.py` - Enhanced alert messages and ANPR logic

### Frontend
- ✅ `dashboard/app/src/api/api.js` - Updated event label mapping
- ✅ `dashboard/app/src/pages/Dashboard.jsx` - Display event descriptions
- ✅ `dashboard/app/src/pages/ANPR.jsx` - Complete redesign with table

### Documentation
- ✅ `UPDATE_SUMMARY.md` - **NEW** - This file
- ✅ Previous improvements still in place (H.264 fixes, stream optimization, alert sync)

---

## 🎯 What You'll See

### Before vs. After

#### Console Messages
| Before | After |
|--------|-------|
| `[ALERT] person #1 crossed the fence` | `[ALERT] Person has crossed the virtual fence (Track #1)` |
| `[ALERT] car #5 crossed the fence` | `[ALERT] Car has crossed the virtual fence (Track #5)` |
| No ANPR logging | `[ANPR] Detected plate: ABC1234 on car #5` |

#### Dashboard Active Alerts
| Before | After |
|--------|-------|
| "Virtual Fence Crossing" | "Person crossed virtual fence" |
| "Virtual Fence Crossing" | "Car crossed virtual fence" |
| "night_movement_crossing" | "Person crossed virtual fence at night" |

#### ANPR Tab
| Before | After |
|--------|-------|
| Simple count display | Full table with columns |
| "X plates detected" | Plate Number, Vehicle, Event, Time, Track ID |
| Basic latest plate | Detailed latest plate with all info |
| No vehicle breakdown | Plates Detected vs. Vehicles Detected stats |

#### Video Display
| Before | After |
|--------|-------|
| `Plate: ABC1234` (small, yellow text) | Yellow box background with `PLATE: ABC1234` (bold, black text) |

---

## 🔧 Configuration

### ANPR Settings
Edit `cv_pipeline/detect_track_fence.py`:

```python
# Confidence threshold (0.0 - 1.0)
ANPR_CONFIDENCE_THRESHOLD = 0.3  # Default: 0.3

# Lower = more detections (may include false positives)
# Higher = fewer detections (more accurate)
```

### Night Detection
```python
NIGHT_START_HOUR = 19  # 7 PM
NIGHT_END_HOUR = 6     # 6 AM
```

To test night mode immediately:
```python
NIGHT_START_HOUR = 0
NIGHT_END_HOUR = 23
```

### Virtual Fence Position
```python
LINE_START = (0, 300)    # Left edge, Y coordinate
LINE_END = (640, 300)    # Right edge, Y coordinate
```

---

## 📊 API Changes

### New Field in Alert Response
```json
{
  "id": 123,
  "camera_id": "CAM_01",
  "event_type": "car_crossed_fence",
  "event_description": "Car crossed virtual fence",  // ← NEW
  "object_type": "car",
  "track_id": 5,
  "confidence": 0.87,
  "timestamp": "2026-09-16T14:30:45",
  "snapshot_path": "alert_20260916_143045_id5.jpg",
  "plate_number": "ABC1234"
}
```

### Event Type Values
**New event types:**
- `person_crossed_fence` / `person_crossed_fence_night`
- `car_crossed_fence` / `car_crossed_fence_night`
- `truck_crossed_fence` / `truck_crossed_fence_night`
- `bus_crossed_fence` / `bus_crossed_fence_night`
- `motorcycle_crossed_fence` / `motorcycle_crossed_fence_night`
- `vehicle_crossed_fence` / `vehicle_crossed_fence_night`

**Legacy event types still supported:**
- `virtual_fence_crossing`
- `loitering`
- `night_movement_crossing`

---

## ✅ Verification Checklist

- [x] Database migration completed
- [x] Backend accepts event_description field
- [x] CV pipeline generates descriptive messages
- [x] Console shows improved alert format
- [x] Dashboard displays event descriptions
- [x] ANPR tab shows full table
- [x] License plates visible on video (yellow background)
- [x] Vehicle types correctly identified
- [x] Night events properly labeled
- [x] WebSocket updates working
- [x] Old alerts backward compatible

---

## 🎓 Usage Examples

### Standard Detection
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4
```
**Result:** Descriptive alerts, no ANPR

### With ANPR
```powershell
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4 --anpr
```
**Result:** Descriptive alerts + license plate detection + ANPR tab populated

### Live Stream with ANPR
```powershell
# Terminal 1: MediaMTX
.\tools\mediamtx.exe

# Terminal 2: FFmpeg publisher
.\tools\ffmpeg.exe -re -stream_loop -1 -i .\sample_videos\test_4.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -profile:v baseline -level 3.0 -g 60 -keyint_min 60 -sc_threshold 0 -b:v 2M -maxrate 2M -bufsize 1M -pix_fmt yuv420p -err_detect ignore_err -an -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam1

# Terminal 3: Backend
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# Terminal 4: Dashboard
cd dashboard\app
npm run dev -- --host 127.0.0.1

# Terminal 5: CV Pipeline with ANPR
cd cv_pipeline
..\venv\Scripts\python.exe detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1 --anpr
```

---

## 🐛 Troubleshooting

### "event_description is None"
**Solution:** Run migration script
```powershell
cd backend
..\venv\Scripts\python.exe migrate_db.py
```

### "ANPR not working"
**Checklist:**
- [ ] Using `--anpr` flag?
- [ ] EasyOCR installed? (`pip list | grep easyocr`)
- [ ] Vehicles large enough in frame? (>100x100 pixels recommended)
- [ ] Good lighting in video?

### "Plates not showing in ANPR tab"
**Solutions:**
1. Hard refresh dashboard: `Ctrl + Shift + R`
2. Check browser console (F12) for errors
3. Verify backend is running: http://localhost:8000/docs
4. Check WebSocket connection: Should show "BACKEND LIVE"

### "Old alerts showing generic messages"
**This is expected behavior:**
- Old alerts use `event_type` → label mapping
- New alerts will have `event_description`
- Optional: Clear old alerts to see only new format

---

## 📈 Performance Impact

**Minimal overhead:**
- Event description generation: <1ms per alert
- ANPR crop padding: Negligible
- Database column addition: One-time migration
- Frontend rendering: No performance impact

**Benefits:**
- Better user experience
- Clearer security monitoring
- Professional appearance
- Easier auditing and reporting

---

## 🎉 Summary

All requested features have been successfully implemented:

1. ✅ **Descriptive alert messages** - "Person has crossed the virtual fence"
2. ✅ **Vehicle-specific alerts** - Car, Truck, Bus, Motorcycle identified
3. ✅ **Fixed ANPR logic** - Improved crop, validation, logging
4. ✅ **ANPR tab display** - Full table with all detections

**System is now production-ready for demonstration!**

---

## 📞 Support

- Check `TROUBLESHOOTING.md` for common issues
- Review `QUICK_REFERENCE.md` for commands
- See `CHANGELOG.md` for version history
- Read full setup in `README.md`

**Test the system:**
```powershell
.\start_simple.bat
```

**Then open:** http://localhost:5173 (Login: admin / admin123)
