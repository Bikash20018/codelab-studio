@echo off
setlocal
title Build CodeLab Studio
cd /d "%~dp0"

echo [1/4] Checking Python...
python --version || (echo Python 3.9 or newer is required: https://www.python.org/downloads/ & pause & exit /b 1)

echo [2/4] Installing PyInstaller...
python -m pip install --upgrade pyinstaller || goto :fail

echo [3/4] Building CodeLabStudio.exe...
python -m PyInstaller --noconfirm --clean --windowed --onedir ^
  --name CodeLabStudio ^
  --icon assets\app.ico ^
  --add-data "assets\app.ico;assets" ^
  --add-data "assets\app.png;assets" ^
  --add-data "tools;tools" ^
  --add-data "licenses;licenses" ^
  codelab_studio.py || goto :fail

echo [4/4] Bundling the GCC compiler...
if exist "mingw64\bin\g++.exe" (
  robocopy "mingw64" "dist\CodeLabStudio\mingw64" /E /NFL /NDL /NJH /NJS /NP >nul
  if errorlevel 8 goto :fail
) else (
  echo   WARNING: mingw64\bin\g++.exe was not found next to build.bat.
  echo   Download WinLibs GCC ^(Win64, UCRT, zip^) from https://winlibs.com
  echo   extract it, put the "mingw64" folder here, and run build.bat again.
)

echo.
echo Done:  dist\CodeLabStudio\CodeLabStudio.exe
pause
exit /b 0

:fail
echo.
echo Build failed - read the messages above.
pause
exit /b 1
