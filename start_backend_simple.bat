@echo off
echo ========================================
echo   SINISTER SNARE - SIMPLIFIED START
echo ========================================
echo.

cd /d "%~dp0backend"

echo Creating simplified .env file (no MongoDB required)...
echo MONGO_URL="mongodb://localhost:27017" > .env
echo DB_NAME="sinister_snare_db" >> .env
echo CORS_ORIGINS="*" >> .env
echo UEX_API_KEY="6b70cf40873c5d6e706e5aa87a5ceab97ac8032b" >> .env
echo LOG_LEVEL="INFO" >> .env

echo Activating virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing minimal requirements...
pip install fastapi uvicorn httpx python-dotenv pydantic motor

echo.
echo ========================================
echo   STARTING WITHOUT MONGODB
echo   (All features work with in-memory data)
echo ========================================
echo.
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo   Status:   http://localhost:8001/api/status
echo.

python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause