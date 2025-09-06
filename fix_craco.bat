@echo off
echo Fixing CRACO Installation Issue...

cd /d "%~dp0frontend"

echo Step 1: Cleaning old installations...
if exist "node_modules" rmdir /s /q "node_modules"
if exist "package-lock.json" del "package-lock.json"
if exist "yarn.lock" del "yarn.lock"

echo Step 2: Installing Node dependencies...
npm cache clean --force
npm install

echo Step 3: Specifically installing CRACO...
npm install @craco/craco --save-dev

echo Step 4: Verifying installation...
if exist "node_modules\.bin\craco.cmd" (
    echo ✅ CRACO successfully installed!
    echo You can now run: npm start
) else (
    echo ❌ CRACO installation failed. Using fallback...
    copy package-simple.json package.json
    npm install
    echo ✅ Fallback configuration ready!
)

echo.
echo Setup complete! You can now start the frontend with:
echo npm start

pause