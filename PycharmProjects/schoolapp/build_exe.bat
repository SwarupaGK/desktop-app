@echo off
setlocal
REM Windows 10/11 build (PySide6). For Windows 7 use build_exe_win7.bat instead.

python -m PyInstaller ^
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

echo.
if not exist "dist\data" mkdir "dist\data"
copy /Y "data\students.db" "dist\data\students.db" >nul
copy /Y "data\admin_credentials.json" "dist\data\admin_credentials.json" >nul
echo Build complete. Run dist\StudentHub.exe. Current data was copied to dist\data.
endlocal
