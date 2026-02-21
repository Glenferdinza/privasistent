@echo off
REM Setup Irma Auto-Start on Windows Boot
REM This script creates a Windows Task Scheduler task to run Irma on startup

echo.
echo ========================================
echo   IRMA AUTO-START SETUP
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges!
    echo Please right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo [INFO] Administrator privileges confirmed.
echo.

REM Get current directory
set "IRMA_DIR=%~dp0"
set "IRMA_DIR=%IRMA_DIR:~0,-1%"

echo [INFO] Irma directory: %IRMA_DIR%
echo.

REM Check if venv exists
if not exist "%IRMA_DIR%\venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.py first to create virtual environment.
    echo.
    pause
    exit /b 1
)

echo [INFO] Creating Windows Task Scheduler task...
echo.

REM Delete existing task if exists
schtasks /query /tn "IrmaVirtualAssistant" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Removing existing task...
    schtasks /delete /tn "IrmaVirtualAssistant" /f >nul 2>&1
)

REM Create new task
REM Task will run at user logon with highest privileges
schtasks /create ^
    /tn "IrmaVirtualAssistant" ^
    /tr "\"%IRMA_DIR%\run_web.bat\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Auto-start task created successfully!
    echo.
    echo Irma will now start automatically when you log in to Windows.
    echo.
    echo Task Details:
    echo   Name: IrmaVirtualAssistant
    echo   Trigger: At user logon
    echo   Action: Run web interface
    echo   Location: %IRMA_DIR%\run_web.bat
    echo.
    echo To verify: Open Task Scheduler and look for "IrmaVirtualAssistant"
    echo To disable: Run 'disable_autostart.bat'
    echo.
) else (
    echo.
    echo [ERROR] Failed to create auto-start task!
    echo Please check Task Scheduler manually.
    echo.
)

pause
