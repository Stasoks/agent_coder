@echo off
cls

echo.
echo ========================================
echo       Lua AI Studio - Build Installer
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH!
    echo Please install Python 3.11+ and add it to PATH.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Found: %PYTHON_VERSION%
echo.

REM ===== STEP 1/6: Setup Virtual Environment =====
echo ===== STEP 1/6: Setup Virtual Environment =====
if not exist ".venv311gpu\" (
    echo Creating virtual environment...
    python -m venv .venv311gpu
    if errorlevel 1 (
        echo [ERROR] Failed to create venv!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo Activating virtual environment...
call .venv311gpu\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate venv!
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM ===== STEP 2/6: Update pip =====
echo ===== STEP 2/6: Update pip and tools =====
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo [ERROR] Failed to update pip!
    pause
    exit /b 1
)
echo [OK] pip upgraded
echo.

REM ===== STEP 3/6: Install Requirements =====
echo ===== STEP 3/6: Install requirements =====
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some requirements failed, trying individually...
    pip install PySide6 transformers accelerate safetensors pyinstaller markdown --quiet
)
echo [OK] Requirements installed
echo.

REM ===== STEP 4/6: Install PyTorch with CUDA =====
echo ===== STEP 4/6: Install PyTorch with CUDA 13.0 =====
echo Installing torch, torchvision, torchaudio...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130 --upgrade --quiet
if errorlevel 1 (
    echo [WARNING] PyTorch CUDA installation had issues
    echo Retrying with upgraded pip...
    pip install --upgrade pip
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130 --force-reinstall --quiet
)
echo [OK] PyTorch installed
echo.

REM ===== STEP 5/6: Clean old builds =====
echo ===== STEP 5/6: Cleaning old build files =====
if exist "build\" rmdir /s /q build 2>nul
if exist "dist\" rmdir /s /q dist 2>nul
if exist "__pycache__\" rmdir /s /q __pycache__ 2>nul
echo [OK] Old builds cleaned
echo.

REM ===== STEP 6/6: Build with PyInstaller =====
echo ===== STEP 6/6: Building executable =====
echo This may take 5-10 minutes...
echo.
pyinstaller lua_ai_studio.spec --distpath "dist" --workpath "build" -y

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo        Build Complete - SUCCESS!
echo ========================================
echo.
echo Executable: dist\lua_ai_studio\lua_ai_studio.exe
echo.

REM ===== STEP 7/6: Creating Windows Installer =====
echo ===== STEP 7/6: Creating Windows Installer =====
echo Checking for Inno Setup...
where iscc >nul 2>&1
if errorlevel 1 (
    echo [INFO] Inno Setup not found
    echo Install from: https://jrsoftware.org/isdl.php
    echo Or: choco install innosetup
    echo.
    echo You can still distribute: dist\lua_ai_studio\lua_ai_studio.exe
    echo.
    pause
    exit /b 0
)

echo Building Windows Installer...
iscc installer.iss
if errorlevel 1 (
    echo [WARNING] Inno Setup build had issues
    pause
    exit /b 0
)

echo.
echo ========================================
echo      Ready for Distribution - SUCCESS!
echo ========================================
echo.
echo Installer: dist\installer\LuaAIStudio-Setup.exe
echo Portable:  dist\lua_ai_studio\lua_ai_studio.exe
echo.
echo Send to users: dist\installer\LuaAIStudio-Setup.exe
echo.
pause
