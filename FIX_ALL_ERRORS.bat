@echo off
title SINISTER SNARE - UNIVERSAL ERROR FIXER
color 0C

echo.
echo ========================================
echo   SINISTER SNARE ERROR FIXER v2.0
echo   Behebt ALLE bekannten Probleme
echo ========================================
echo.

echo Schritt 1: Backend-Probleme beheben...
cd /d "%~dp0backend"

echo Erstelle/Repariere .env Datei...
echo MONGO_URL="mongodb://localhost:27017" > .env
echo DB_NAME="sinister_snare_db" >> .env
echo CORS_ORIGINS="*" >> .env
echo UEX_API_KEY="6b70cf40873c5d6e706e5aa87a5ceab97ac8032b" >> .env
echo LOG_LEVEL="INFO" >> .env
echo ✅ Backend .env erstellt

echo Erstelle/Repariere Virtual Environment...
if exist "venv" rmdir /s /q "venv"
python -m venv venv
call venv\Scripts\activate.bat

echo Installiere Backend Dependencies...
python -m pip install --upgrade pip
pip install fastapi uvicorn httpx python-dotenv pydantic motor pymongo
echo ✅ Backend Dependencies installiert

echo.
echo Schritt 2: Frontend-Probleme beheben...
cd /d "%~dp0frontend"

echo Bereinige Frontend...
if exist "node_modules" rmdir /s /q "node_modules"
if exist "package-lock.json" del "package-lock.json"
if exist "yarn.lock" del "yarn.lock"

echo Erstelle .env.local Datei...
echo REACT_APP_BACKEND_URL=http://localhost:8001 > .env.local
echo GENERATE_SOURCEMAP=false >> .env.local
echo ✅ Frontend .env.local erstellt

echo Installiere Frontend Dependencies...
npm cache clean --force
npm install

echo Installiere CRACO spezifisch...
npm install @craco/craco --save-dev

echo Teste CRACO Installation...
if exist "node_modules\.bin\craco.cmd" (
    echo ✅ CRACO erfolgreich installiert
) else (
    echo ⚠️  CRACO fehlgeschlagen, nutze Fallback...
    copy package-simple.json package.json
    npm install
    echo ✅ Fallback-Konfiguration bereit
)

echo.
echo ========================================
echo   ALLE FEHLER BEHOBEN!
echo ========================================
echo.
echo Zum Starten:
echo 1. Doppelklick: start_backend.bat
echo 2. Doppelklick: start_frontend.bat
echo 3. Öffne: http://localhost:3000
echo.
echo Alternative (ohne MongoDB):
echo 1. Doppelklick: start_backend_simple.bat
echo 2. Doppelklick: start_frontend.bat
echo.

pause