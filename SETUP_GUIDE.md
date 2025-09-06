# 🚀 Sinister Snare - Lokales Setup Guide

## ⚠️ WICHTIG: Vollständige Neuinstallation erforderlich

Das Problem mit `craco` tritt auf, weil die node_modules nicht vollständig sind. Hier ist die komplette Lösung:

## 📋 Voraussetzungen

- **Node.js** 18.x oder höher
- **Python** 3.9 oder höher
- **MongoDB** (lokal oder Cloud)
- **Git** (optional)

## 🛠️ Schritt-für-Schritt Installation

### 1. Repository klonen oder Dateien herunterladen

```bash
# Option A: Git clone (empfohlen)
git clone <repository-url>
cd sinister-snare

# Option B: ZIP herunterladen und entpacken
# Navigiere zum Projektordner
```

### 2. Backend Setup (Python/FastAPI)

```bash
# Navigiere zum Backend-Ordner
cd backend

# Erstelle virtuelles Environment
python -m venv venv

# Aktiviere virtuelles Environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Installiere Dependencies
pip install -r requirements.txt

# Erstelle .env Datei
copy .env.example .env
# Oder erstelle manuell eine .env Datei mit:
```

#### Backend .env Datei Inhalt:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="sinister_snare_db"
CORS_ORIGINS="http://localhost:3000,http://localhost:3001"
UEX_API_KEY="6b70cf40873c5d6e706e5aa87a5ceab97ac8032b"
```

### 3. Frontend Setup (React)

```bash
# Navigiere zum Frontend-Ordner (neuer Terminal oder cd ..)
cd frontend

# WICHTIG: Lösche node_modules und package-lock files
rm -rf node_modules
rm package-lock.json
rm yarn.lock

# Installiere Dependencies neu
npm install
# ODER mit Yarn (empfohlen):
npm install -g yarn
yarn install

# Erstelle .env Datei
copy .env.example .env.local
# Oder erstelle manuell eine .env.local Datei mit:
```

#### Frontend .env.local Datei Inhalt:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
DISABLE_HOT_RELOAD=false
```

### 4. MongoDB Setup

#### Option A: Lokale MongoDB Installation
```bash
# Windows (mit Chocolatey):
choco install mongodb

# macOS (mit Homebrew):
brew tap mongodb/brew
brew install mongodb-community

# Ubuntu/Debian:
sudo apt-get install mongodb

# Starte MongoDB
mongod
```

#### Option B: MongoDB Cloud (Atlas)
1. Erstelle Account bei [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Erstelle neuen Cluster
3. Füge Connection String in backend/.env ein

### 5. Anwendung starten

#### Terminal 1 - Backend starten:
```bash
cd backend
# Environment aktivieren falls nicht aktiv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Backend starten
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2 - Frontend starten:
```bash
cd frontend
# Frontend starten
npm start
# ODER
yarn start
```

## 🎯 Zugriff auf die Anwendung

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## 🔍 Problembehandlung

### Problem: "craco command not found"
**Lösung:**
```bash
cd frontend
rm -rf node_modules
rm package-lock.json
npm install
```

### Problem: Backend startet nicht
**Lösung:**
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: CORS Errors
**Lösung:** Überprüfe .env Dateien und stelle sicher, dass CORS_ORIGINS korrekt gesetzt ist

### Problem: MongoDB Connection
**Lösung:** 
1. Stelle sicher, dass MongoDB läuft
2. Überprüfe MONGO_URL in backend/.env
3. Teste Connection: `python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').admin.command('ping'))"`

### Problem: API Key funktioniert nicht
**Lösung:** UEX API kann durch Cloudflare blockiert sein - die App funktioniert mit Mock-Daten

## 📦 Erweiterte Konfiguration

### Entwicklungsmodus
```bash
# Frontend mit detailliertem Debugging
cd frontend
REACT_APP_DEBUG=true npm start

# Backend mit detailliertem Logging
cd backend
LOG_LEVEL=DEBUG python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Produktionsbuild
```bash
# Frontend Build
cd frontend
npm run build

# Backend für Produktion
cd backend
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🚀 Features nach dem Setup

Nach erfolgreichem Setup hast du Zugang zu:

- ✅ **Live Star Citizen Daten** (2,261+ Commodity Records)
- ✅ **Lokale Datenbank** (IndexedDB) für historische Analyse  
- ✅ **Real-time Route Tracking**
- ✅ **Snare Now** - Beste aktuelle Interception-Targets
- ✅ **Commodity Snare** - Spezifische Waren-Jagd
- ✅ **Manual Refresh** mit Live-Logs
- ✅ **Database Management** - Datenbereinigung und -verwaltung
- ✅ **Multi-System Support** - Stanton, Pyro, Terra, etc.
- ✅ **Export Funktionen** - CSV/JSON Export

## 🆘 Support

Falls du weiterhin Probleme hast:

1. Überprüfe alle .env Dateien
2. Stelle sicher, dass alle Dependencies installiert sind
3. Überprüfe Firewall/Antivirus-Einstellungen
4. Versuche es mit einem anderen Port (3001 statt 3000)

**Das Setup sollte jetzt vollständig funktionieren!** 🎯⚔️🏴‍☠️