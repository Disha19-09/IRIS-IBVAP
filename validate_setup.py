"""
Setup Validation Script
-----------------------
Checks if all required files exist and dependencies are installed
"""

import os
import sys

def check_file(path, description):
    """Check if file exists."""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} MISSING: {path}")
        return False

def check_python_package(package_name):
    """Check if Python package is installed."""
    try:
        __import__(package_name)
        print(f"✅ Python package: {package_name}")
        return True
    except ImportError:
        print(f"❌ Python package MISSING: {package_name}")
        return False

def main():
    print("="*70)
    print("IRIS-IBVAP Setup Validation")
    print("="*70)
    
    errors = 0
    
    # Check critical files
    print("\n📁 Checking project files...")
    files_to_check = [
        ("backend/main.py", "Backend main"),
        ("backend/auth.py", "Authentication module"),
        ("backend/database.py", "Database module"),
        ("cv_pipeline/detect_track_fence.py", "CV Pipeline"),
        ("README.md", "README"),
        ("AUTH_GUIDE.md", "Auth guide"),
        ("QUICK_START_AUTH.md", "Quick start guide"),
        ("install_auth_deps.bat", "Install script"),
        ("test_auth.py", "Auth test script"),
    ]
    
    for filepath, desc in files_to_check:
        if not check_file(filepath, desc):
            errors += 1
    
    # Check Python dependencies
    print("\n📦 Checking Python dependencies...")
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "requests",
        "cv2",  # opencv-python
        "ultralytics",
    ]
    
    for package in packages:
        if not check_python_package(package):
            errors += 1
    
    # Check auth dependencies
    print("\n🔐 Checking authentication dependencies...")
    auth_packages = [
        ("jose", "python-jose[cryptography]"),
        ("passlib", "passlib[bcrypt]"),
    ]
    
    for package, install_name in auth_packages:
        try:
            __import__(package)
            print(f"✅ Auth package: {install_name}")
        except ImportError:
            print(f"⚠️  Auth package NOT INSTALLED: {install_name}")
            print(f"   Run: pip install {install_name}")
            errors += 1
    
    # Check database
    print("\n🗄️  Checking database...")
    if os.path.exists("backend/alerts.db"):
        print("✅ Database file exists: backend/alerts.db")
        
        # Try to check if User table exists
        try:
            from database import User, Alert
            print("✅ Database models imported successfully")
        except Exception as e:
            print(f"⚠️  Database models issue: {e}")
    else:
        print("ℹ️  Database will be created on first backend run")
    
    # Check tools
    print("\n🛠️  Checking streaming tools...")
    if os.path.exists("tools/mediamtx.exe"):
        print("✅ MediaMTX: tools/mediamtx.exe")
    else:
        print("❌ MediaMTX MISSING: tools/mediamtx.exe")
        errors += 1
    
    if os.path.exists("tools/ffmpeg.exe"):
        print("✅ FFmpeg: tools/ffmpeg.exe")
    else:
        print("❌ FFmpeg MISSING: tools/ffmpeg.exe")
        errors += 1
    
    # Summary
    print("\n" + "="*70)
    if errors == 0:
        print("✅ All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && ..\\venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000")
        print("2. Test authentication: venv\\Scripts\\python.exe test_auth.py")
        print("3. Visit API docs: http://localhost:8000/docs")
    else:
        print(f"⚠️  Found {errors} issue(s). Please fix them before running the system.")
        print("\nTo fix auth dependencies:")
        print("  install_auth_deps.bat")
        print("\nOr manually:")
        print("  pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt")
    print("="*70)
    
    return errors

if __name__ == "__main__":
    sys.exit(main())
