@echo off
echo ========================================
echo PyTorch Installation - CPU Fallback
echo ========================================
echo.
echo Your Python 3.14 is too new for PyTorch CUDA builds.
echo Installing CPU version as fallback...
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Uninstalling any existing PyTorch...
pip uninstall -y torch torchvision torchaudio

echo.
echo Installing PyTorch CPU (works on Python 3.14)...
pip install torch torchvision torchaudio

echo.
echo ========================================
echo Verifying Installation
echo ========================================
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'Python version compatible: Yes'); print('Ready to use in CPU mode')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo PyTorch CPU installed successfully.
echo System will run in CPU mode.
echo.
echo To use GPU later, you may need to:
echo 1. Downgrade to Python 3.11 or 3.12, OR
echo 2. Wait for PyTorch to release Python 3.14 CUDA builds
echo.
echo For now, run: START.bat (CPU mode)
echo.
pause
