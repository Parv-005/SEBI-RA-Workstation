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
echo Copying updater binary to output directory...
if exist "dist\updater.exe" (
    copy /Y "dist\updater.exe" "dist\SEBI_RA_Automation\updater.exe"
    echo   updater.exe copied.
) else (
    echo WARNING: updater.exe not found in dist\. Skipping copy.
)

echo.
echo Creating release ZIP...
set VERSION_FILE=core\version.py
for /f "tokens=2 delims===" %%v in ('findstr /c:"__version__" %VERSION_FILE%') do (
    set "VER=%%v"
)
set "VER=%VER: =%"
set "VER=%VER:"=%"
set "ZIP_NAME=SEBI_RA_Automation_v%VER%_Windows"
set "DIST_DIR=dist\SEBI_RA_Automation"

if exist "%DIST_DIR%" (
    if exist "dist\%ZIP_NAME%.zip" del "dist\%ZIP_NAME%.zip"
    powershell -Command "Compress-Archive -Path '%DIST_DIR%' -DestinationPath 'dist\%ZIP_NAME%.zip'"
    echo Release package created: dist\%ZIP_NAME%.zip
) else (
    echo WARNING: Could not find %DIST_DIR% to zip.
)

echo.
echo ============================================
echo  Build complete!
echo  Output: dist\SEBI_RA_Automation\
echo.
echo  To run:
echo    dist\SEBI_RA_Automation\SEBI_RA_Automation.exe
echo ============================================
pause