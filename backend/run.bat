@echo off
echo ========================================
echo  Food S Quare - Flask Backend Launcher
echo ========================================
echo.

REM Install dependencies
echo [1/2] Installing Python dependencies...
pip install -r requirements.txt
echo.

REM Start the Flask server
echo [2/2] Starting Flask server on port 8080...
echo.
echo  Admin credentials:
echo    Username : admin
echo    Password : admin123
echo.
echo  Server URL: http://localhost:8080
echo  Press Ctrl+C to stop the server
echo ========================================
python app.py
pause
