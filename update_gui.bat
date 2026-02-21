@echo off
REM Update Irma Web Interface to v2.0
REM This script backs up the old version and activates the new one

echo.
echo ========================================
echo   IRMA GUI UPDATE TO V2.0
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Current directory: %CD%
echo.

REM Check if web\templates folder exists
if not exist "web\templates\" (
    echo [ERROR] web\templates folder not found!
    echo Please run this script from Irma project root directory.
    pause
    exit /b 1
)

REM Check if new version exists
if not exist "web\templates\index_v2.html" (
    echo [ERROR] index_v2.html not found!
    echo New version file is missing.
    pause
    exit /b 1
)

echo [INFO] Backing up current version...
if exist "web\templates\index.html" (
    copy "web\templates\index.html" "web\templates\index_v1_backup.html" >nul
    if %errorlevel% equ 0 (
        echo [SUCCESS] Backup created: index_v1_backup.html
    ) else (
        echo [ERROR] Failed to create backup!
        pause
        exit /b 1
    )
) else (
    echo [WARNING] No existing index.html found. Proceeding anyway...
)

echo.
echo [INFO] Activating new version...
copy "web\templates\index_v2.html" "web\templates\index.html" >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] New version activated!
) else (
    echo [ERROR] Failed to activate new version!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   UPDATE COMPLETE
echo ========================================
echo.
echo New features:
echo   - Chat Management (Voice + Text chats)
echo   - Dark Theme (Auto OS detection)
echo   - Professional UI (Gemini-like)
echo   - Enhanced Statistics
echo   - Better Animations
echo.
echo Backup saved as: index_v1_backup.html
echo.
echo Next step: Restart web server
echo   1. Stop current server (Ctrl+C)
echo   2. Run: run_web.bat
echo   3. Open: http://localhost:5000
echo.
echo To revert to old version:
echo   copy web\templates\index_v1_backup.html web\templates\index.html
echo.

pause
