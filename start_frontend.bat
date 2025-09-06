@echo off
echo Starting Sinister Snare Frontend...

cd /d "%~dp0frontend"

echo Checking for node_modules...
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo Checking for craco...
if exist "node_modules\.bin\craco.cmd" (
    echo Starting with craco...
    npm start
) else (
    echo Craco not found, trying alternative...
    if exist "package-simple.json" (
        echo Using simplified package.json...
        copy package-simple.json package.json.backup
        copy package-simple.json package.json
        npm install
        npm start
    ) else (
        echo Please run: npm install @craco/craco
        pause
    )
)

pause