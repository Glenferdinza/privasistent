@echo off
REM Disable Irma Auto-Start
REM This script removes the Windows Task Scheduler task

echo.
echo ========================================
echo   DISABLE IRMA AUTO-START
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

REM Check if task exists
schtasks /query /tn "IrmaVirtualAssistant" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Auto-start task does not exist.
    echo Nothing to disable.
    echo.
    pause
    exit /b 0
)

echo [INFO] Disabling auto-start task...
echo.

REM Delete task
schtasks /delete /tn "IrmaVirtualAssistant" /f

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Auto-start disabled successfully!
    echo.
    echo Irma will no longer start automatically on boot.
    echo You can still run it manually using run_web.bat
    echo.
    echo To re-enable: Run 'setup_autostart.bat'
    echo.
) else (
    echo.
    echo [ERROR] Failed to disable auto-start!
    echo Please check Task Scheduler manually.
    echo.
)

pause
