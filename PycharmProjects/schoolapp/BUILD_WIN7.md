# Building StudentHub for Windows 7

The app uses **Qt**. Windows 7 does **not** support Qt 6 / PySide6 / Python 3.9+.

## Requirements (on the build PC)

| Component | Version |
|-----------|---------|
| OS | Windows 7 SP1 or newer (build can be done on Win 10 with Python 3.8) |
| Python | **3.8.x** (last version that supports Windows 7) |
| GUI | **PySide2** 5.15 (Qt 5.15) |
| Packager | PyInstaller 5.x |

Do **not** use Python 3.14 or PySide6 for a Windows 7 `.exe` — it will not run on Windows 7.

## Quick build

1. Install [Python 3.8.10](https://www.python.org/downloads/release/python-3810/) (64-bit).
2. Open a command prompt in this folder.
3. Run:

```bat
build_exe_win7.bat
```

4. Copy `dist\StudentHub.exe` (and `dist\data\` if needed) to the Windows 7 PC.

## Manual build

```bat
set SCHOOLAPP_QT=pyside2
py -3.8 -m pip install -r requirements-win7.txt
py -3.8 -m PyInstaller --noconfirm --clean --onefile --windowed --name StudentHub ^
  --add-data "logof.png;." ^
  --add-data "data\students.db;data" ^
  --add-data "data\admin_credentials.json;data" ^
  --add-data "NotoSansDevanagari-Regular.ttf;." ^
  --add-data "NotoSansDevanagari-Bold.ttf;." ^
  main.py
```

## On the Windows 7 PC

- Install **Windows 7 SP1** and all updates.
- Install [Visual C++ 2015–2019 Redistributable (x64)](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) if the app reports missing `VCRUNTIME` / `MSVCP` DLLs.
- Screen resolution at least **1024×600** recommended.

## Development on Windows 10/11

You can keep using PySide6 locally (`pip install -r requirements.txt`). The code uses `qt_compat.py` so the same sources work with PySide2 when `SCHOOLAPP_QT=pyside2` is set (as in `build_exe_win7.bat`).
