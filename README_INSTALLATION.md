# 🎯 Sinister Snare - Installation Guide

## 🚀 Quick Start (Windows)

### Option 1: Universal Installer (Recommended)
```batch
# Run the universal dependency installer
INSTALL_ALL_DEPENDENCIES.bat
```
This will install all backend and frontend dependencies automatically.

### Option 2: Manual Installation

#### Backend Setup:
```batch
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

#### Frontend Setup:
```batch
cd frontend
yarn install
# OR
npm install
```

## 🐛 Bug Fixes Implemented

### ✅ All 10 Critical Bugs Fixed:

1. **Web-Parsing Error Handling** - Graceful fallback when HTML parsing fails
2. **Safe ROI Calculation** - No more division by zero errors
3. **Enhanced Terminal Mapping** - Better terminal name normalization
4. **MongoDB Health Check** - Retry mechanism and connection validation
5. **Dependencies Fixed** - httpx>=0.25.0, scipy>=1.13.0
6. **IndexedDB Error Boundaries** - Fallback to localStorage
7. **Race Condition Protection** - Debouncing and AbortController
8. **CORS Configuration** - Secure localhost origins
9. **Environment Variables** - Robust .env configuration
10. **Requirements Compatibility** - All versions harmonized

## 🎮 Starting the Application

### Start Backend:
```batch
start_backend.bat
```
Backend will run on: http://localhost:8001

### Start Frontend:
```batch
start_frontend.bat
```
Frontend will run on: http://localhost:3000

## 🔧 Troubleshooting

### Common Issues:

#### "ModuleNotFoundError: No module named 'numpy'"
**Solution**: Run `INSTALL_ALL_DEPENDENCIES.bat`

#### "CORS Error"
**Solution**: Make sure both frontend (3000) and backend (8001) are running

#### "Database Connection Failed"
**Solution**: Start MongoDB or check `backend/.env` for MONGO_URL

#### "Port already in use"
**Solution**: 
- Kill existing processes on ports 3000/8001
- Or change ports in .env files

## 📋 Requirements

- **Python**: 3.11+
- **Node.js**: 16+
- **MongoDB**: 4.4+ (local or remote)
- **RAM**: 4GB minimum
- **Disk**: 2GB free space

## 🎯 Advanced Features

### Advanced Snareplan
- 3D Quantum Interdiction Positioning
- Multi-route optimization
- Real-time tactical analysis

### Hardcore Mode
- ELITE/LEGENDARY routes only
- Enhanced piracy targets
- Advanced filtering

## 🚨 Production Notes

### Security:
- Change default CORS origins in production
- Use environment-specific .env files
- Enable HTTPS in production

### Performance:
- Enable Redis caching
- Use CDN for static assets
- Optimize bundle size

## 📞 Support

If you encounter issues:
1. Check this README
2. Run `INSTALL_ALL_DEPENDENCIES.bat`
3. Verify all services are running
4. Check logs in supervisor

---

**🎮 Happy Pirating in the 'Verse! 🚀**