@echo off
echo ========================================
echo Installing PyTorch with CUDA Support
echo ========================================
echo.
echo Detecting Python version...
call venv\Scripts\activate.bat
python --version
echo.

cd /d "%~dp0"

echo ========================================
echo Step 1: Uninstalling existing PyTorch
echo ========================================
echo.
pip uninstall -y torch torchvision torchaudio

echo.
echo ========================================
echo Step 2: Installing PyTorch with CUDA
echo ========================================
echo.
echo Trying CUDA 12.1 (compatible with Python 3.14)...
echo This may take 5-10 minutes...
echo.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo ========================================
echo Verifying Installation
echo ========================================
echo.
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'Device count: {torch.cuda.device_count()}'); print(f'GPU Names:'); [print(f'  GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())] if torch.cuda.is_available() else print('  No CUDA devices')"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
if errorlevel 1 (
    echo [ERROR] Installation failed!
    echo.
    echo Your Python 3.14 might not be compatible with PyTorch CUDA builds yet.
    echo.
    echo Fallback option: Install CPU version
    echo Run this command manually:
    echo   pip install torch torchvision torchaudio
    echo.
) else (
    echo If CUDA available = True, your NVIDIA GPU is ready!
    echo.
    echo Next: Enable GPU in configuration files
    echo See: GPU_CONFIGURATION.txt for instructions
)
echo.
pause



