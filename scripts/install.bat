@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo [1/3] Instalando ffmpeg...
winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
echo [2/3] Creando entorno virtual...
python -m venv venv
echo [3/3] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt
python -m playwright install chromium
echo.
echo Listo. Usa: scripts\sync.bat "URL_DE_LA_PLAYLIST"
pause
