@echo off
echo ================================================================
echo          SINISTER SNARE - UNIVERSAL DEPENDENCY INSTALLER
echo                     All Dependencies Setup
echo ================================================================
echo.

REM Change to app directory
cd /d "%~dp0"

echo [1/6] Setting up Python Virtual Environment...
echo ================================================================
cd backend
if not exist "venv" (
    echo Creating new virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists, using existing one...
)

echo.
echo [2/6] Activating Virtual Environment...
echo ================================================================
call venv\Scripts\activate.bat

echo.
echo [3/6] Upgrading pip and setuptools...
echo ================================================================
python -m pip install --upgrade pip setuptools wheel

echo.
echo [4/6] Installing Backend Dependencies...
echo ================================================================
echo Installing from requirements.txt...
pip install -r requirements.txt

echo.
echo Manually installing critical dependencies to ensure they work...
pip install fastapi==0.110.1
pip install uvicorn==0.25.0
pip install pymongo==4.5.0
pip install motor==3.3.1
pip install numpy>=1.26.0
pip install scipy>=1.13.0
pip install httpx>=0.25.0
pip install pydantic>=2.6.4
pip install python-dotenv>=1.0.1
pip install requests>=2.31.0
pip install pandas>=2.2.0

echo.
echo [5/6] Installing Frontend Dependencies...
echo ================================================================
cd ..\frontend

REM Check if node_modules exists
if exist "node_modules" (
    echo node_modules exists, cleaning...
    rmdir /s /q node_modules
)

REM Check if yarn.lock exists
if exist "yarn.lock" (
    echo Using Yarn for installation...
    call yarn install
) else (
    echo Using NPM for installation...
    call npm install
)

echo.
echo Installing critical frontend packages manually...
call npm install react@^18.2.0 react-dom@^18.2.0 axios@^1.6.0 lodash@^4.17.21

echo.
echo [6/6] Verifying Installation...
echo ================================================================
cd ..\backend
call venv\Scripts\activate.bat

echo Testing Python imports...
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
python -c "import numpy; print('✅ NumPy:', numpy.__version__)"
python -c "import scipy; print('✅ SciPy:', scipy.__version__)"
python -c "import pymongo; print('✅ PyMongo:', pymongo.__version__)"
python -c "import motor; print('✅ Motor: OK')"
python -c "import httpx; print('✅ HTTPX:', httpx.__version__)"

echo.
cd ..\frontend
echo Testing Node.js dependencies...
call npm list react react-dom axios lodash --depth=0

echo.
echo ================================================================
echo          🎉 INSTALLATION COMPLETE! 🎉
echo ================================================================
echo.
echo Backend Dependencies: ✅ Installed in backend/venv
echo Frontend Dependencies: ✅ Installed in frontend/node_modules
echo.
echo Next Steps:
echo 1. Start Backend: run start_backend.bat
echo 2. Start Frontend: run start_frontend.bat
echo.
echo ================================================================

pause