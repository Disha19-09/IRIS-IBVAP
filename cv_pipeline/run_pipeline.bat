@echo off
REM IRIS CV Pipeline Launcher with Error Suppression
REM This script sets environment variables to suppress H.264 decoding warnings

echo Starting IRIS CV Pipeline...
echo.

REM Suppress FFmpeg/libav logging in OpenCV
set OPENCV_FFMPEG_CAPTURE_OPTIONS=loglevel;quiet
set OPENCV_LOG_LEVEL=ERROR
set AV_LOG_FORCE_NOCOLOR=1

REM Use the provided source or default to test.mp4
set SOURCE=%1
if "%SOURCE%"=="" set SOURCE=..\sample_videos\test.mp4

echo Source: %SOURCE%
echo.

REM Activate virtual environment and run pipeline with ANPR enabled
cd /d "%~dp0"
call ..\venv\Scripts\activate.bat
python detect_track_fence.py --source "%SOURCE%" --anpr

pause
