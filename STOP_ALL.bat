@echo off
echo ========================================
echo Stopping All IRIS-IBVAP Services
echo ========================================
echo.

echo Stopping MediaMTX...
taskkill /F /IM mediamtx.exe >nul 2>&1

echo Stopping FFmpeg...
taskkill /F /IM ffmpeg.exe >nul 2>&1

echo Stopping Python processes (Backend, CV Pipeline)...
taskkill /F /IM python.exe >nul 2>&1

echo Stopping Node.js (Dashboard)...
taskkill /F /IM node.exe >nul 2>&1

echo.
echo All services stopped!
echo.
pause
