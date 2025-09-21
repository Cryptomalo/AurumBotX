@echo off
echo 🚀 AurumBotX Launcher for Windows
echo ================================
cd /d "%~dp0"
echo 📁 Current directory: %CD%
echo 🔍 Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python found
echo 🚀 Starting AurumBotX GUI...
python aurumbotx_gui.py
if errorlevel 1 (
    echo ❌ Error starting AurumBotX
    echo 🔧 Trying installer first...
    python install.py
    echo 🚀 Retrying AurumBotX...
    python aurumbotx_gui.py
)
pause
