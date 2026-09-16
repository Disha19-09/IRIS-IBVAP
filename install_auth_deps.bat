@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt
echo.
echo Installation complete!
echo Press any key to exit...
pause >nul
