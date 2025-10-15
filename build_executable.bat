@echo off
REM ========================================
REM Aurora FIS Analytics - Standalone Executable Builder  
REM This script creates a standalone executable with all dependencies included
REM ========================================

echo ========================================
echo Aurora FIS Analytics Executable Builder
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Check if all required packages are installed
echo Checking required packages...
python -c "import PIL, cv2, matplotlib, seaborn, pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo Some required packages are missing. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)
echo All required packages are available.
echo.

REM Clean up previous builds
echo Cleaning up previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "AuroraFISAnalytics.exe" del "AuroraFISAnalytics.exe"
echo Previous builds cleaned.
echo.

REM Create the executable using the spec file
echo Building standalone executable...
echo This may take several minutes...
echo.

python -m PyInstaller aurora_fis_analytics.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for error details.
    pause
    exit /b 1
)

REM Check if executable was created successfully
if not exist "dist\AuroraFISAnalytics.exe" (
    echo.
    echo ERROR: Executable was not created!
    echo Check the build output for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Executable location: dist\AuroraFISAnalytics.exe
echo File size:
for %%I in ("dist\AuroraFISAnalytics.exe") do echo   %%~zI bytes (%%~zI / 1024 / 1024 MB)
echo.

REM Test the executable (optional)
echo Testing the executable...
echo Starting AuroraFISAnalytics.exe for 3 seconds...
cd dist
start "" "AuroraFISAnalytics.exe"
cd ..

REM Wait and check if it's running
timeout /t 3 /nobreak >nul
tasklist /fi "imagename eq AuroraFISAnalytics.exe" 2>nul | find /i "AuroraFISAnalytics.exe" >nul
if not errorlevel 1 (
    echo ✓ Executable started successfully!
    echo Terminating test instance...
    taskkill /f /im "AuroraFISAnalytics.exe" >nul 2>&1
) else (
    echo Note: Test startup completed (executable may have closed normally)
)

echo.
echo ========================================
echo BUILD COMPLETE
echo ========================================
echo.
echo Your standalone executable is ready at:
echo   %CD%\dist\AuroraFISAnalytics.exe
echo.
echo This executable includes all dependencies and can be run on
echo any Windows machine without requiring Python to be installed.
echo.
echo To distribute:
echo 1. Copy the entire 'dist' folder to the target machine
echo 2. Run AuroraFISAnalytics.exe from the dist folder
echo.
echo Build artifacts:
echo   - dist\          (Contains the executable and runtime files)
echo   - build\         (Build cache - can be deleted)
echo   - aurora_fis_analytics.spec (Build configuration)
echo.

echo Clean up build cache? (Y/N)
set /p cleanup="Enter choice: "
if /i "%cleanup%"=="Y" (
    if exist "build" rmdir /s /q "build"
    echo Build cache cleaned.
)

echo.
pause