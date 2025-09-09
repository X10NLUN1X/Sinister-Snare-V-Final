@echo off
echo Starting Sinister Snare Backend...
echo.

cd /d "%~dp0backend"

echo Checking environment...
if not exist ".env" (
    echo Creating .env file...
    echo MONGO_URL="mongodb://localhost:27017" > .env
    echo DB_NAME="sinister_snare_db" >> .env
    echo MONGO_RETRY_ATTEMPTS=3 >> .env
    echo MONGO_RETRY_DELAY=1000 >> .env
    echo CORS_ORIGINS="http://localhost:3000,http://localhost:8001" >> .env
    echo API_TIMEOUT=30 >> .env
    echo API_RETRY_ATTEMPTS=3 >> .env
    echo RATE_LIMIT_PER_MINUTE=60 >> .env
    echo LOG_LEVEL="INFO" >> .env
    echo LOG_FILE="sinister_snare.log" >> .env
    echo ENABLE_WEB_CRAWLING=true >> .env
    echo ENABLE_FALLBACK_DATA=true >> .env
    echo ENABLE_CACHE=true >> .env
    echo CACHE_TTL_SECONDS=300 >> .env
    echo ✅ .env file created
)

echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo   SINISTER SNARE BACKEND STARTING
echo ========================================
echo   Backend URL: http://localhost:8001
echo   API Docs:    http://localhost:8001/docs
echo   Database:    MongoDB (local/optional)
echo ========================================
echo.

echo Starting FastAPI server...
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause