@echo off
echo ========================================
echo IRIS-IBVAP Complete Startup
echo ========================================
echo.

cd /d "%~dp0"

echo Stopping any running services...
taskkill /F /IM mediamtx.exe >nul 2>&1
taskkill /F /IM ffmpeg.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Starting All Services...
echo ========================================
echo.

:: 1. MediaMTX
echo [1/5] Starting MediaMTX Server...
start "1-MediaMTX" cmd /k "cd /d "%~dp0\tools" && mediamtx.exe mediamtx.yml"
timeout /t 3 /nobreak >nul

:: 2. FFmpeg Publisher (Balanced Quality for CPU)
echo [2/5] Starting Video Stream...
start "2-FFmpeg" cmd /k "cd /d "%~dp0" && timeout /t 2 /nobreak >nul && tools\ffmpeg.exe -re -stream_loop -1 -i sample_videos\test_2.mp4 -vf scale=1280:720,fps=20 -c:v libx264 -preset veryfast -tune zerolatency -profile:v main -level 3.1 -g 40 -sc_threshold 0 -pix_fmt yuv420p -b:v 2000k -maxrate 2500k -bufsize 4000k -an -rtsp_transport tcp -f rtsp rtsp://127.0.0.1:8554/cam1"
timeout /t 3 /nobreak >nul

:: 3. Backend API
echo [3/5] Starting Backend API...
start "3-Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && cd backend && uvicorn main:app --reload --port 8000"
timeout /t 8 /nobreak >nul

:: 4. Dashboard
echo [4/5] Starting Dashboard...
start "4-Dashboard" cmd /k "cd /d "%~dp0\dashboard\app" && npm.cmd run dev -- --host 127.0.0.1"
timeout /t 8 /nobreak >nul

:: 5. CV Pipeline
echo [5/5] Starting CV Pipeline (ANPR Enabled)...
start "5-CV-Pipeline" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && cd cv_pipeline && timeout /t 3 /nobreak >nul && python detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1 --no-display --anpr"

echo.
echo ========================================
echo ALL SERVICES STARTED!
echo ========================================
echo.
echo Access the dashboard at:
echo http://127.0.0.1:5173/
echo.
echo Login credentials:
echo Username: admin
echo Password: admin123
echo.
echo Press any key to close this window...
echo (Services will continue running in background windows)
echo.
pause >nul
