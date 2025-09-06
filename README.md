# ⚔️ Sinister Snare v2.0 - Star Citizen Piracy Intelligence System

## 🎯 Überblick

**Sinister Snare** ist ein fortschrittliches Star Citizen Piracy Intelligence System, das Echtzeit-Handelsdaten analysiert und optimale Interception-Möglichkeiten für Piraterie-Operationen identifiziert.

## ✨ Features

### 🔥 Live Intelligence
- **Real-time Daten**: 2,261+ live Star Citizen Commodity Records
- **Multi-System Tracking**: Stanton, Pyro, Terra, Nyx Systeme
- **Echte Terminals**: Rat's Nest, Brio's Breaker, ARC-L4, Endgame, etc.

### 🎯 Piracy Tools
- **SNARE NOW**: Beste aktuelle Interception-Targets
- **Commodity Snare**: Spezifische Waren-Jagd (Gold, Laranite, Medical Supplies)
- **Route Codes**: `ENDGAME-AGRICIUM-ARC-L4` Format
- **Interception Points**: Gateway-basierte Inter-System Strategien

### 💾 Lokale Datenbank
- **IndexedDB Storage**: Unbegrenzte lokale Datenspeicherung
- **Historische Analyse**: Sammelt Daten für genauere Vorhersagen
- **Smart Data Management**: Ergänzung statt Überschreibung
- **Zeitbasierte Bereinigung**: 1-4 Wochen Datenaufbewahrung

### 📊 Intelligence Dashboard
- **24-Hour Heatmap**: Optimale Piracy-Zeiten
- **Real-time Alerts**: High-value Target Benachrichtigungen
- **Multi-Tab Interface**: Dashboard, Routes, Targets, Map, Alerts, Trends, Database
- **Export Functions**: CSV/JSON Datenexport

## 🚀 Quick Start

### Windows Benutzer (Einfach):
1. Doppelklick auf `fix_craco.bat` (behebt Installation)
2. Doppelklick auf `start_backend.bat` (Terminal 1)
3. Doppelklick auf `start_frontend.bat` (Terminal 2)
4. Öffne http://localhost:3000

### Manuelles Setup:
Siehe `SETUP_GUIDE.md` für detaillierte Anweisungen.

## 🏴‍☠️ Verwendung

### 1. Dashboard
- Überblick über aktuelle Piracy-Opportunities
- 24-Stunden Aktivitätsheatmap
- Live Alerts für high-value targets

### 2. SNARE NOW
- Klicke "🎯 SNARE NOW" für beste aktuelle Targets
- Zeigt Interception-Strategien für Inter-System Routen
- Geschätzte Trader-Frequenz pro Stunde

### 3. Commodity Snare
- Wähle spezifische Commodities (Gold, Medical Supplies, etc.)
- Automatische Berechnung von Kauf-/Verkaufspunkten
- Gateway-Warnungen für System-übergreifende Routen

### 4. Database Management
- Zeigt lokale Datenbankstatistiken (Routen, Commodities, Größe)
- Datenbereinigung (1-4 Wochen oder komplett)
- Automatische Datensammlung bei API-Calls

## 📋 Technische Details

### Backend (Python/FastAPI)
- **API**: UEXCorp + Star Profit Integration
- **Database**: MongoDB für Persistierung
- **Real-time**: WebSocket Support
- **Port**: 8001

### Frontend (React)
- **Framework**: React 18 mit Tailwind CSS
- **Database**: IndexedDB für lokale Speicherung
- **Build Tool**: CRACO (Create React App Configuration Override)
- **Port**: 3000

### Datenquellen
- **Primary**: Star Profit API (Live Data)
- **Fallback**: UEXCorp API
- **Mock Data**: Wenn APIs blockiert sind

## 🎮 Star Citizen Integration

### Systeme
- **Stanton**: Area18, Lorville, New Babbage, Port Olisar
- **Pyro**: Rat's Nest, Endgame, Ruin Station
- **Terra**: Terra Prime, New Cordoba
- **Nyx**: Delamar, Levski

### Route Codes
```
Format: STARTLOCATION-COMMODITY-ENDLOCATION
Beispiele:
- ENDGAME-AGRICIUM-ARC-L4 (Pyro → Stanton)
- RATSNE-ALTRUCIA-BRIOSB (Pyro → Stanton)
- TERRA-GOLD-AREA18 (Terra → Stanton)
```

### Piracy Intelligence
- **Risk Levels**: LEGENDARY, ELITE, HIGH, MODERATE, LOW
- **Profit Analysis**: aUEC Berechnungen basierend auf realen Marktdaten
- **Traffic Scoring**: Trader-Frequenz Schätzungen
- **Inter-System Warnings**: Gateway Interception Strategien

## 🔧 Problembehandlung

### Häufige Probleme:
1. **"craco command not found"** → Führe `fix_craco.bat` aus
2. **Backend startet nicht** → Überprüfe Python/MongoDB Installation
3. **CORS Errors** → Überprüfe .env Konfiguration
4. **Keine Daten** → UEX API kann blockiert sein (verwendet Mock-Daten)

### Logs:
- **Backend**: Terminal zeigt API-Requests und Datenbankoperationen
- **Frontend**: Browser Developer Console (F12)
- **Database**: IndexedDB durch Browser Developer Tools einsehbar

## 📊 Performance

### Datenbank Performance
- **IndexedDB**: Schnelle lokale Speicherung
- **Indexed Searches**: Route_code, commodity_name, timestamp
- **Storage**: Automatische Größenerkennung (KB/MB/GB)

### API Performance
- **Rate Limiting**: 10 Requests/Minute (UEX API)
- **Caching**: Lokale Datenspeicherung reduziert API-Calls
- **Fallbacks**: Mehrere Datenquellen für Ausfallsicherheit

## 🌟 Advanced Features

### Historical Analysis
- Route-spezifische 7-Tage Historie
- Trend-Erkennung für Profit-Entwicklung
- Confidence Levels basierend auf Datenmenge

### Real-time Intelligence
- Live Route Tracking mit Background Updates
- Automatische Alert-Generierung bei High-Value Targets
- Smart Update Logic (nur bei signifikanten Änderungen)

### Multi-System Operations
- Accurate Terminal-zu-System Mapping
- Distance Calculations (Intra-system vs Inter-system)
- Gateway-based Interception Strategies

## 📄 Lizenz

Dieses Projekt ist für Star Citizen Spieler zur privaten Nutzung bestimmt.

## 🆘 Support

Bei Problemen oder Fragen:
1. Überprüfe `SETUP_GUIDE.md`
2. Führe `fix_craco.bat` aus
3. Überprüfe .env Dateien
4. Stelle sicher, dass MongoDB läuft

---

**🏴‍☠️ Bereit für Piraterie-Operationen im Star Citizen Universum! ⚔️**
