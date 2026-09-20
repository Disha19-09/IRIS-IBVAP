@echo off
REM IRIS-IBVAP Complete Demo Launcher
REM This script opens all required terminals for the full demo

echo ========================================
echo IRIS-IBVAP Complete Demo Launcher
echo ========================================
echo.
echo This will open 5 PowerShell windows:
echo   1. MediaMTX (streaming server)
echo   2. FFmpeg Publisher (video source)
echo   3. Backend API (FastAPI)
echo   4. Dashboard (React frontend)
echo   5. CV Pipeline (YOLOv8 detection)
echo.
echo Press any key to start...
pause > nul

echo.
echo [1/5] Starting MediaMTX...
start "IRIS - MediaMTX" powershell -NoExit -Command "cd '%~dp0'; Write-Host 'Starting MediaMTX...' -ForegroundColor Green; .\tools\mediamtx.exe"
timeout /t 2 > nul

echo [2/5] Starting FFmpeg Publisher...
start "IRIS - FFmpeg Publisher" powershell -NoExit -Command "cd '%~dp0'; Write-Host 'Publishing video stream...' -ForegroundColor Green; .\tools\ffmpeg.exe -re -stream_loop -1 -i .\sample_videos\test_4.mp4 -c:v libx264 -preset ultrafast -tune zerolatency -profile:v baseline -level 3.0 -g 60 -keyint_min 60 -sc_threshold 0 -b:v 2M -maxrate 2M -bufsize 1M -pix_fmt yuv420p -err_detect ignore_err -an -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam1"
timeout /t 3 > nul

echo [3/5] Starting Backend...
start "IRIS - Backend" powershell -NoExit -Command "cd '%~dp0\backend'; Write-Host 'Starting FastAPI backend...' -ForegroundColor Green; ..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
timeout /t 5 > nul

echo [4/5] Starting Dashboard...
start "IRIS - Dashboard" powershell -NoExit -Command "cd '%~dp0\dashboard\app'; Write-Host 'Starting React dashboard...' -ForegroundColor Green; npm run dev -- --host 127.0.0.1"
timeout /t 5 > nul

echo [5/5] Starting CV Pipeline...
start "IRIS - CV Pipeline" powershell -NoExit -Command "cd '%~dp0\cv_pipeline'; Write-Host 'Starting CV detection pipeline...' -ForegroundColor Green; $env:OPENCV_FFMPEG_CAPTURE_OPTIONS='loglevel;quiet'; $env:OPENCV_LOG_LEVEL='ERROR'; ..\venv\Scripts\python.exe detect_track_fence.py --source rtsp://127.0.0.1:8554/cam1"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Open these URLs in your browser:
echo   Dashboard:  http://localhost:5173
echo   API Docs:   http://localhost:8000/docs
echo   Video Feed: http://localhost:8889/cam1/
echo.
echo Login Credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo Press Ctrl+C in each window to stop services.
echo Close this window when done.
pause
