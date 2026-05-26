@echo off
echo ============================================
echo  SEBI RA Automation - Windows Build Script
echo ============================================
echo.

pip install pyinstaller>=6.0
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller sebi_ra.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Build complete!
echo  Output: dist\SEBI_RA_Automation\
echo.
echo  To run:
echo    1. Copy config_example.json to config.json
echo    2. Fill in your credentials in config.json
echo    3. Run SEBI_RA_Automation.exe
echo ============================================
pause
