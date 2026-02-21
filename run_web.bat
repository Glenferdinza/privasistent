@echo off
REM Irma Web Interface Launcher
REM Run this to start Irma with beautiful web GUI

echo.
echo ========================================
echo   IRMA VIRTUAL ASSISTANT - WEB GUI
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.py first to create virtual environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Flask is installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [ERROR] Flask not installed!
    echo Installing Flask dependencies...
    pip install flask flask-cors werkzeug
)

REM Start web interface
echo [INFO] Starting Irma Web Interface...
echo.
echo Web interface will open in your browser automatically.
echo Server running at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo.

cd web
python app.py

pause
