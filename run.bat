@echo off
echo Starting Inventory Tracker...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found.
    echo Please run setup.bat first to install dependencies.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
python inventory_tracker.py

REM Deactivate when done
deactivate
