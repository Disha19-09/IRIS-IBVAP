@echo off
REM IRIS-IBVAP Simple Demo (File-based, no streaming)
REM Best for testing and development

echo ========================================
echo IRIS-IBVAP Simple Demo
echo ========================================
echo.
echo This will open 3 PowerShell windows:
echo   1. Backend API
echo   2. Dashboard
echo   3. CV Pipeline (from local file)
echo.
echo This mode is more stable and doesn't require
echo MediaMTX or FFmpeg streaming.
echo.
echo Press any key to start...
pause > nul

echo.
echo [1/3] Starting Backend...
start "IRIS - Backend" powershell -NoExit -Command "cd '%~dp0\backend'; Write-Host 'Starting FastAPI backend...' -ForegroundColor Green; ..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
timeout /t 5 > nul

echo [2/3] Starting Dashboard...
start "IRIS - Dashboard" powershell -NoExit -Command "cd '%~dp0\dashboard\app'; Write-Host 'Starting React dashboard...' -ForegroundColor Green; npm run dev -- --host 127.0.0.1"
timeout /t 5 > nul

echo [3/3] Starting CV Pipeline...
start "IRIS - CV Pipeline" powershell -NoExit -Command "cd '%~dp0\cv_pipeline'; Write-Host 'Starting CV detection from file...' -ForegroundColor Green; $env:OPENCV_FFMPEG_CAPTURE_OPTIONS='loglevel;quiet'; $env:OPENCV_LOG_LEVEL='ERROR'; ..\venv\Scripts\python.exe detect_track_fence.py --source ..\sample_videos\test.mp4"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Open these URLs in your browser:
echo   Dashboard:  http://localhost:5173
echo   API Docs:   http://localhost:8000/docs
echo.
echo Login Credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo The CV pipeline will process test.mp4
echo Press 'q' in the CV window to stop processing.
echo Close windows when done.
pause
