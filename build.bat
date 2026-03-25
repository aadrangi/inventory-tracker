@echo off
echo Building Inventory Tracker...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or later from https://www.python.org
    pause
    exit /b 1
)

echo Python found.
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

if exist requirements.txt (
    echo Checking dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo WARNING: requirements.txt not found
)

echo Installing build tools...
pip install --upgrade pyinstaller

if exist build (
    echo Cleaning previous build artifacts...
    rmdir /s /q build
)
if exist dist (
    echo Cleaning previous distribution...
    rmdir /s /q dist
)
if exist *.spec (
    echo Cleaning previous spec files...
    del *.spec
)

echo Building Windows executable...
pyinstaller --onefile --windowed --name "Inventory-Tracker" inventory_tracker.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build complete!
echo Executable is located in: dist\Inventory-Tracker.exe
echo.
pause
