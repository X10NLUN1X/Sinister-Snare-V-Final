@echo off
echo Starting Sinister Snare Backend...
echo.

cd /d "%~dp0backend"

echo Checking environment...
if not exist ".env" (
    echo Creating .env file...
    echo MONGO_URL="mongodb://localhost:27017" > .env
    echo DB_NAME="sinister_snare_db" >> .env
    echo CORS_ORIGINS="*" >> .env
    echo UEX_API_KEY="6b70cf40873c5d6e706e5aa87a5ceab97ac8032b" >> .env
    echo LOG_LEVEL="INFO" >> .env
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