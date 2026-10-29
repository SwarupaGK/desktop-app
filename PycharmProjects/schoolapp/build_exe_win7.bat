@echo off
setlocal
REM StudentHub.exe for Windows 7 — requires Python 3.8 and PySide2 (Qt 5.15).
set SCHOOLAPP_QT=pyside2

where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found. Install Python 3.8 from https://www.python.org/downloads/release/python-3810/
  exit /b 1
)

py -3.8 -c "import sys; sys.exit(0)" 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.8 not found. Install Python 3.8 x64 for Windows 7 compatible builds.
  echo   py -3.8 -m pip install -r requirements-win7.txt
  exit /b 1
)

echo Installing Windows 7 build dependencies...
py -3.8 -m pip install -r requirements-win7.txt -q
if errorlevel 1 exit /b 1

echo Building StudentHub.exe with PySide2 / Python 3.8...
py -3.8 -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name StudentHub ^
  --add-data "logof.png;." ^
  --add-data "data\students.db;data" ^
  --add-data "data\admin_credentials.json;data" ^
  --add-data "NotoSansDevanagari-Regular.ttf;." ^
  --add-data "NotoSansDevanagari-Bold.ttf;." ^
  main.py

if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

if not exist "dist\data" mkdir "dist\data"
copy /Y "data\students.db" "dist\data\students.db" >nul
copy /Y "data\admin_credentials.json" "dist\data\admin_credentials.json" >nul

echo.
echo Windows 7 build complete: dist\StudentHub.exe
echo Test on Windows 7 or install VC++ 2015-2019 Redistributable if DLL errors appear.
endlocal
