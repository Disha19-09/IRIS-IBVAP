@echo off
echo ========================================
echo CLEAR ALL DATA - Fresh Start
echo ========================================
echo.
echo This will delete:
echo   • All alerts from database
echo   • All snapshot images
echo   • Backend logs
echo.
echo WARNING: This cannot be undone!
echo.
pause

cd /d "%~dp0"

echo.
echo ========================================
echo Step 1: Stopping all services
echo ========================================
echo.
taskkill /F /IM mediamtx.exe >nul 2>&1
taskkill /F /IM ffmpeg.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo Services stopped.
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Step 2: Clearing database
echo ========================================
echo.
if exist backend\alerts.db (
    del /F /Q backend\alerts.db
    echo Database deleted: backend\alerts.db
) else (
    echo No database found (already clean)
)

if exist backend\alerts.json (
    del /F /Q backend\alerts.json
    echo JSON file deleted: backend\alerts.json
) else (
    echo No JSON file found
)

if exist backend\alerts.csv (
    del /F /Q backend\alerts.csv
    echo CSV file deleted: backend\alerts.csv
) else (
    echo No CSV file found
)

echo.
echo ========================================
echo Step 3: Clearing snapshots
echo ========================================
echo.
if exist snapshots\*.jpg (
    del /F /Q snapshots\*.jpg
    echo Deleted all JPEG snapshots
) else (
    echo No snapshots found
)

if exist snapshots\*.mp4 (
    del /F /Q snapshots\*.mp4
    echo Deleted all MP4 files
) else (
    echo No video files found
)

echo.
echo ========================================
echo Step 4: Clearing logs
echo ========================================
echo.
if exist cv_pipeline\*.log (
    del /F /Q cv_pipeline\*.log
    echo Deleted CV pipeline logs
) else (
    echo No CV pipeline logs found
)

if exist sample_videos\*.log (
    del /F /Q sample_videos\*.log
    echo Deleted sample video logs
) else (
    echo No sample video logs found
)

echo.
echo ========================================
echo CLEANUP COMPLETE!
echo ========================================
echo.
echo All data cleared. System ready for fresh run.
echo.
echo Next steps:
echo   1. Run: START.bat
echo   2. Open: http://127.0.0.1:5173/
echo   3. Login with: admin / admin123
echo   4. Fresh start with no previous data!
echo.
pause
