@echo off
title Sinister Snare v2.0 - Installation
color 0A

echo.
echo ========================================
echo   SINISTER SNARE v2.0 INSTALLATION
echo   Star Citizen Piracy Intelligence
echo ========================================
echo.

echo Schritt 1: Backend Setup...
cd /d "%~dp0backend"

if not exist "venv" (
    echo Erstelle Python Virtual Environment...
    python -m venv venv
)

echo Aktiviere Virtual Environment...
call venv\Scripts\activate.bat

echo Installiere Python Dependencies...
pip install -r requirements.txt

if not exist ".env" (
    echo Erstelle Backend .env Datei...
    copy .env.example .env
)

echo.
echo Schritt 2: Frontend Setup...
cd /d "%~dp0frontend"

echo Installiere Node Dependencies...
npm install

if not exist ".env.local" (
    echo Erstelle Frontend .env Datei...
    copy .env.example .env.local
)

echo.
echo ========================================
echo   INSTALLATION ABGESCHLOSSEN!
echo ========================================
echo.
echo Zum Starten:
echo 1. Doppelklick: start_backend.bat
echo 2. Doppelklick: start_frontend.bat
echo 3. Öffne: http://localhost:3000
echo.
echo Bei Problemen: fix_craco.bat ausführen
echo.

pause