@echo off
echo Building ShougunRemoteX Service to .exe...

REM Activate virtual environment trước khi build
echo Activating virtual environment...
call "D:\project\H74\virtualenv\shougun-remote-x\Scripts\Activate.bat"

REM Cài đặt dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Chạy build
echo Starting build process...
python build.py

echo.
echo Build completed! Check 'dist' folder for .exe file.
pause
