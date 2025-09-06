@echo off
echo Starting Sinister Snare Backend...

cd /d "%~dp0backend"

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

echo Starting FastAPI server...
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause