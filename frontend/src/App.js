import { useState, useEffect, useCallback } from "react";
import "./App.css";
import axios from "axios";

// IndexedDB Database Manager
class SinisterDatabase {
  constructor() {
    this.dbName = 'SinisterSnareDB';
    this.version = 1;
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Routes store
        if (!db.objectStoreNames.contains('routes')) {
          const routeStore = db.createObjectStore('routes', { keyPath: 'id', autoIncrement: true });
          routeStore.createIndex('route_code', 'route_code', { unique: false });
          routeStore.createIndex('commodity_name', 'commodity_name', { unique: false });
          routeStore.createIndex('timestamp', 'timestamp', { unique: false });
          routeStore.createIndex('origin_system', 'origin_system', { unique: false });
          routeStore.createIndex('destination_system', 'destination_system', { unique: false });
        }
        
        // Commodities store
        if (!db.objectStoreNames.contains('commodities')) {
          const commodityStore = db.createObjectStore('commodities', { keyPath: 'id', autoIncrement: true });
          commodityStore.createIndex('commodity_name', 'commodity_name', { unique: false });
          commodityStore.createIndex('terminal_name', 'terminal_name', { unique: false });
          commodityStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
        
        // Interception History store
        if (!db.objectStoreNames.contains('interceptions')) {
          const interceptionStore = db.createObjectStore('interceptions', { keyPath: 'id', autoIncrement: true });
          interceptionStore.createIndex('route_code', 'route_code', { unique: false });
          interceptionStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  async addRoutes(routes) {
    try {
      if (!this.db) await this.init();
      
      const transaction = this.db.transaction(['routes'], 'readwrite');
      const store = transaction.objectStore('routes');
      const timestamp = new Date().toISOString();
      
      const addedRoutes = [];
      
      for (const route of routes) {
        try {
          // Add ALL routes as historical data (don't check for duplicates)
          const routeData = {
            ...route,
            timestamp,
            origin_system: route.origin_name?.split(' - ')[0] || 'Unknown',
            destination_system: route.destination_name?.split(' - ')[0] || 'Unknown',
            data_source: 'api_fetch',
            // Add unique identifier for each fetch
            fetch_id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          };
          
          // Always add as new historical record
          await store.add(routeData);
          addedRoutes.push(routeData);
        } catch (routeError) {
          console.warn('Error adding individual route:', routeError);
          continue;
        }
      }
      
      return addedRoutes;
    } catch (error) {
      console.error('Error adding routes to database:', error);
      return [];
    }
  }

  async addCommodities(commodities) {
    if (!this.db) await this.init();
    
    const transaction = this.db.transaction(['commodities'], 'readwrite');
    const store = transaction.objectStore('commodities');
    const timestamp = new Date().toISOString();
    
    for (const commodity of commodities) {
      const commodityData = {
        ...commodity,
        timestamp,
        data_source: 'api_fetch'
      };
      await store.add(commodityData);
    }
  }

  async getRouteByCode(routeCode) {
    if (!this.db) await this.init();
    
    const transaction = this.db.transaction(['routes'], 'readonly');
    const store = transaction.objectStore('routes');
    const index = store.index('route_code');
    
    return new Promise((resolve) => {
      const request = index.get(routeCode);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
  }

  shouldUpdateRoute(existing, newRoute) {
    const existingTime = new Date(existing.timestamp);
    const now = new Date();
    const hoursDiff = (now - existingTime) / (1000 * 60 * 60);
    
    // Update if older than 1 hour or profit significantly different
    return hoursDiff > 1 || Math.abs(existing.profit - newRoute.profit) > (existing.profit * 0.1);
  }

  async getStats() {
    if (!this.db) await this.init();
    
    const routeCount = await this.getCountFromStore('routes');
    const commodityCount = await this.getCountFromStore('commodities');
    const interceptionCount = await this.getCountFromStore('interceptions');
    
    // Estimate database size
    const sizeBytes = await this.estimateDbSize();
    const sizeFormatted = this.formatBytes(sizeBytes);
    
    return {
      routes: routeCount,
      commodities: commodityCount,
      interceptions: interceptionCount,
      totalRecords: routeCount + commodityCount + interceptionCount,
      sizeBytes,
      sizeFormatted,
      lastUpdate: await this.getLastUpdateTime()
    };
  }

  async getCountFromStore(storeName) {
    const transaction = this.db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve) => {
      const request = store.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(0);
    });
  }

  async estimateDbSize() {
    if (!navigator.storage || !navigator.storage.estimate) {
      return 0;
    }
    
    try {
      const estimate = await navigator.storage.estimate();
      return estimate.usage || 0;
    } catch {
      return 0;
    }
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  async getLastUpdateTime() {
    const transaction = this.db.transaction(['routes'], 'readonly');
    const store = transaction.objectStore('routes');
    const index = store.index('timestamp');
    
    return new Promise((resolve) => {
      const request = index.openCursor(null, 'prev');
      request.onsuccess = () => {
        const cursor = request.result;
        resolve(cursor ? cursor.value.timestamp : null);
      };
      request.onerror = () => resolve(null);
    });
  }

  async clearAllData() {
    if (!this.db) await this.init();
    
    const transaction = this.db.transaction(['routes', 'commodities', 'interceptions'], 'readwrite');
    
    await Promise.all([
      transaction.objectStore('routes').clear(),
      transaction.objectStore('commodities').clear(),
      transaction.objectStore('interceptions').clear()
    ]);
  }

  async clearOldData(weeks) {
    if (!this.db) await this.init();
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - (weeks * 7));
    const cutoffTimestamp = cutoffDate.toISOString();
    
    const stores = ['routes', 'commodities', 'interceptions'];
    const transaction = this.db.transaction(stores, 'readwrite');
    
    for (const storeName of stores) {
      const store = transaction.objectStore(storeName);
      const index = store.index('timestamp');
      const range = IDBKeyRange.upperBound(cutoffTimestamp);
      
      const request = index.openCursor(range);
      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        }
      };
    }
  }

  async getRouteHistory(routeCode, days = 7) {
    if (!this.db) await this.init();
    
    const transaction = this.db.transaction(['routes'], 'readonly');
    const store = transaction.objectStore('routes');
    const index = store.index('route_code');
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return new Promise((resolve) => {
      const results = [];
      const request = index.openCursor(IDBKeyRange.only(routeCode));
      
      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          const route = cursor.value;
          if (new Date(route.timestamp) >= cutoffDate) {
            results.push(route);
          }
          cursor.continue();
        } else {
          resolve(results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
        }
      };
      request.onerror = () => resolve([]);
    });
  }

  async getBestInterceptionRoutes(limit = 20) {
    if (!this.db) await this.init();
    
    const transaction = this.db.transaction(['routes'], 'readonly');
    const store = transaction.objectStore('routes');
    
    // Get routes from the last 24 hours
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    return new Promise((resolve) => {
      const results = [];
      const request = store.openCursor();
      
      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          const route = cursor.value;
          if (new Date(route.timestamp) >= oneDayAgo && route.piracy_rating >= 40) {
            results.push(route);
          }
          cursor.continue();
        } else {
          // Sort by piracy rating and frequency, take top results
          const sorted = results
            .sort((a, b) => (b.piracy_rating * b.frequency_score) - (a.piracy_rating * a.frequency_score))
            .slice(0, limit);
          resolve(sorted);
        }
      };
      request.onerror = () => resolve([]);
    });
  }
}

// Initialize database
const sinisterDB = new SinisterDatabase();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Enhanced Components
const Header = ({ dataSource, setDataSource, showAverageData, setShowAverageData }) => (
  <header className="bg-gradient-to-r from-red-900 via-black to-red-900 text-white p-6 shadow-2xl border-b border-red-800">
    <div className="container mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-5xl font-bold mb-2 gradient-text">⚔️ Sinister Snare</h1>
          <p className="text-xl opacity-90">Advanced Star Citizen Piracy Intelligence System v5.0</p>
          <p className="text-sm opacity-75 mt-1">Real-time tracking • Interception mapping • Historical analysis • Alert system</p>
        </div>
        <div className="text-right">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 font-medium">OPERATIONAL</span>
          </div>
          <p className="text-xs opacity-75">{new Date().toLocaleString()}</p>
        </div>
      </div>
      
      {/* Data Source Selector */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <label className="text-sm text-gray-400">Datenquelle:</label>
          <select 
            value={dataSource}
            onChange={(e) => setDataSource(e.target.value)}
            className="bg-gray-800 text-white px-3 py-1 rounded border border-gray-600 focus:border-red-500 text-sm"
          >
            <option value="web">🌐 Web Crawling</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-4">
          <label className="text-sm text-gray-400">Ansicht:</label>
          <button
            onClick={() => setShowAverageData(!showAverageData)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              showAverageData 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-800 text-gray-400 border border-gray-600'
            }`}
          >
            {showAverageData ? '📊 Durchschnittsdaten' : '📈 Aktuelle Daten'}
          </button>
        </div>
      </div>
    </div>
  </header>
);

const StatusCard = ({ title, value, status, icon, subtitle, trend }) => (
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-red-500 transition-all duration-300 transform hover:scale-105">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-400 text-sm">{title}</p>
        <p className="text-white text-2xl font-bold">{value}</p>
        {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
        {trend && (
          <div className="flex items-center mt-1">
            <span className={`text-xs ${trend.direction === 'up' ? 'text-green-400' : 'text-red-400'}`}>
              {trend.direction === 'up' ? '↗' : '↘'} {trend.value}
            </span>
          </div>
        )}
      </div>
      <div className={`text-3xl ${status === 'good' ? 'text-green-400' : status === 'warning' ? 'text-yellow-400' : 'text-red-400'}`}>
        {icon}
      </div>
    </div>
  </div>
);

const RouteCard = ({ route, onSelect }) => {
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LEGENDARY': return 'text-purple-300 bg-purple-900/30 border-purple-500';
      case 'ELITE': return 'text-purple-400 bg-purple-900/20 border-purple-600';
      case 'HIGH': return 'text-red-400 bg-red-900/20 border-red-600';
      case 'MODERATE': return 'text-yellow-400 bg-yellow-900/20 border-yellow-600';
      case 'LOW': return 'text-green-400 bg-green-900/20 border-green-600';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-600';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    return diffHours < 1 ? 'Just now' : diffHours < 24 ? `${diffHours}h ago` : `${Math.floor(diffHours/24)}d ago`;
  };

  return (
    <div 
      className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-red-500 transition-all duration-300 cursor-pointer transform hover:scale-105 route-card"
      onClick={() => onSelect && onSelect(route)}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white text-lg font-semibold mb-1">{route.commodity_name}</h3>
          <p className="text-gray-400 text-sm font-mono">{route.route_code}</p>
          <p className="text-gray-500 text-xs mt-1">Last seen: {formatTime(route.last_seen)}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(route.risk_level)}`}>
          {route.risk_level}
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Origin:</span>
          <span className="text-white text-right">{route.origin_name}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Destination:</span>
          <span className="text-white text-right">{route.destination_name}</span>
        </div>
        {(route.buy_price > 0 || route.sell_price > 0) && (
          <div className="grid grid-cols-2 gap-2 text-xs mt-2 pt-2 border-t border-gray-700">
            <div className="flex justify-between">
              <span className="text-gray-400">Buy Price:</span>
              <span className="text-yellow-400">{route.buy_price ? route.buy_price.toFixed(2) : 'N/A'} aUEC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Sell Price:</span>
              <span className="text-green-400">{route.sell_price ? route.sell_price.toFixed(2) : 'N/A'} aUEC</span>
            </div>
          </div>
        )}
        {(route.buy_stock > 0 || route.sell_stock > 0) && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Buy Stock:</span>
              <span className="text-blue-400">{route.buy_stock || 'N/A'} SCU</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Sell Stock:</span>
              <span className="text-purple-400">{route.sell_stock || 'N/A'} SCU</span>
            </div>
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center bg-black/30 rounded p-3">
          <p className="text-2xl font-bold text-green-400">{(route.profit / 1000000).toFixed(2)}M</p>
          <p className="text-gray-400 text-xs">Profit (aUEC)</p>
        </div>
        <div className="text-center bg-black/30 rounded p-3">
          <p className="text-2xl font-bold text-red-400">{route.piracy_rating}</p>
          <p className="text-gray-400 text-xs">Piracy Score</p>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-2 text-xs">
        <div className="text-center">
          <p className="text-white font-medium">{route.roi.toFixed(1)}%</p>
          <p className="text-gray-400">ROI</p>
        </div>
        <div className="text-center">
          <p className="text-white font-medium">{(route.distance / 1000).toFixed(0)}k</p>
          <p className="text-gray-400">Distance</p>
        </div>
        <div className="text-center">
          <p className="text-white font-medium">{route.score}</p>
          <p className="text-gray-400">Traffic</p>
        </div>
        <div className="text-center">
          <p className="text-white font-medium">{(route.investment / 1000000).toFixed(1)}M</p>
          <p className="text-gray-400">Investment</p>
        </div>
      </div>
      
      {route.interception_zones && route.interception_zones.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-700">
          <p className="text-red-400 text-xs font-medium mb-2">🎯 Interception Points:</p>
          <div className="grid grid-cols-2 gap-1">
            {route.interception_zones.slice(0, 4).map((zone, idx) => (
              <span key={idx} className="text-xs text-gray-300 bg-black/20 rounded px-2 py-1">
                {zone.name} ({(zone.intercept_probability * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const PirateTargetCard = ({ target, onTrack }) => (
  <div className="bg-gradient-to-br from-red-900/20 via-black/50 to-purple-900/20 rounded-lg p-6 border border-red-700/50 hover:border-red-500 transition-all duration-300">
    <div className="flex justify-between items-start mb-4">
      <div>
        <h3 className="text-red-400 text-lg font-semibold mb-1 flex items-center">
          🎯 {target.commodity_name}
          {target.freshness_factor > 0.8 && <span className="ml-2 text-green-400 text-sm">🔥 HOT</span>}
        </h3>
        <p className="text-gray-400 text-sm font-mono">{target.route_code}</p>
      </div>
      <div className="text-right">
        <p className="text-red-400 text-2xl font-bold">{target.piracy_score.toFixed(1)}</p>
        <p className="text-gray-400 text-xs">Priority Score</p>
        <div className="mt-1">
          <div className="w-16 bg-gray-700 rounded-full h-2">
            <div 
              className="bg-red-500 h-2 rounded-full" 
              style={{width: `${Math.min(target.freshness_factor * 100, 100)}%`}}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">Freshness</p>
        </div>
      </div>
    </div>
    
    <div className="space-y-2 mb-4">
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Route:</span>
        <span className="text-white text-right text-xs">{target.origin_name} → {target.destination_name}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Expected Value:</span>
        <span className="text-green-400 font-bold">{(target.expected_value / 1000000).toFixed(2)}M aUEC</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Risk/Reward:</span>
        <span className="text-yellow-400">{target.risk_reward_ratio.toFixed(2)}x</span>
      </div>
    </div>
    
    <div className="bg-black/30 rounded p-3 mb-3">
      <p className="text-red-400 text-xs font-medium mb-2">🎯 Interception Points:</p>
      <ul className="text-xs text-gray-300 space-y-1">
        {target.interception_points.slice(0, 3).map((point, idx) => (
          <li key={idx}>• {point}</li>
        ))}
      </ul>
    </div>
    
    <div className="bg-black/30 rounded p-3 mb-3">
      <p className="text-yellow-400 text-xs font-medium mb-2">⏰ Optimal Windows:</p>
      <ul className="text-xs text-gray-300 space-y-1">
        {target.optimal_time_windows.slice(0, 3).map((window, idx) => (
          <li key={idx}>• {window}</li>
        ))}
      </ul>
    </div>
    
    <div className="flex space-x-2">
      <button 
        onClick={() => onTrack && onTrack(target)}
        className="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium transition-colors"
      >
        🔍 Track Route
      </button>
      <button className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm transition-colors">
        📍 View Map
      </button>
    </div>
  </div>
);

const InterceptionMap = ({ routes, targets }) => {
  const [selectedSystem, setSelectedSystem] = useState('All Systems');
  const systems = ['All Systems', 'Stanton', 'Pyro', 'Terra', 'Nyx'];
  
  const getSystemRoutes = () => {
    if (selectedSystem === 'All Systems') return routes;
    return routes.filter(route => 
      route.origin_name.includes(selectedSystem) || route.destination_name.includes(selectedSystem)
    );
  };

  const systemRoutes = getSystemRoutes();

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white text-lg font-semibold">🗺️ Interception Map Analysis</h3>
        <select 
          value={selectedSystem} 
          onChange={(e) => setSelectedSystem(e.target.value)}
          className="bg-gray-700 text-white rounded px-3 py-1 text-sm border border-gray-600"
        >
          {systems.map(system => (
            <option key={system} value={system}>{system}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-black/30 rounded p-4">
          <h4 className="text-yellow-400 font-medium mb-3">📊 System Analysis</h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Active Routes:</span>
              <span className="text-white font-medium">{systemRoutes.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Avg Profit:</span>
              <span className="text-green-400 font-medium">
                {systemRoutes.length > 0 ? (systemRoutes.reduce((sum, r) => sum + r.profit, 0) / systemRoutes.length / 1000000).toFixed(2) + 'M' : '0M'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">High Risk Routes:</span>
              <span className="text-red-400 font-medium">
                {systemRoutes.filter(r => ['ELITE', 'LEGENDARY', 'HIGH'].includes(r.risk_level)).length}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-black/30 rounded p-4">
          <h4 className="text-red-400 font-medium mb-3">🎯 Hot Zones</h4>
          <div className="space-y-3">
            {systemRoutes.slice(0, 4).map((route, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div>
                  <p className="text-white text-sm font-medium">{route.commodity_name}</p>
                  <p className="text-gray-400 text-xs">{route.route_code}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${
                      route.piracy_rating >= 80 ? 'bg-red-500' : 
                      route.piracy_rating >= 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}></div>
                    <span className="text-xs text-gray-300">{route.piracy_rating.toFixed(0)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 bg-black/20 rounded p-4">
        <h4 className="text-purple-400 font-medium mb-3">🚀 Recommended Ship Classes</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { name: 'Light Fighter', routes: systemRoutes.filter(r => r.profit < 2000000).length, icon: '🛩️' },
            { name: 'Heavy Fighter', routes: systemRoutes.filter(r => r.profit >= 2000000 && r.profit < 4000000).length, icon: '🚀' },
            { name: 'Interceptor', routes: systemRoutes.filter(r => r.distance < 30000).length, icon: '⚡' },
            { name: 'Multi-crew', routes: systemRoutes.filter(r => r.profit >= 4000000).length, icon: '🛸' }
          ].map((shipClass, idx) => (
            <div key={idx} className="text-center bg-gray-700/30 rounded p-3">
              <div className="text-2xl mb-1">{shipClass.icon}</div>
              <p className="text-white text-sm font-medium">{shipClass.name}</p>
              <p className="text-gray-400 text-xs">{shipClass.routes} suitable routes</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AlertsPanel = ({ alerts, onAcknowledge }) => (
  <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
    <div className="flex justify-between items-center mb-4">
      <h3 className="text-white text-lg font-semibold">🚨 Active Alerts</h3>
      <span className="bg-red-600 text-white px-2 py-1 rounded-full text-xs font-medium">
        {alerts.filter(a => !a.acknowledged).length} New
      </span>
    </div>
    
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {alerts.slice(0, 10).map((alert, idx) => (
        <div key={alert.id || idx} className={`p-3 rounded border-l-4 ${
          alert.priority === 'CRITICAL' ? 'bg-red-900/20 border-red-500' :
          alert.priority === 'HIGH' ? 'bg-orange-900/20 border-orange-500' :
          'bg-yellow-900/20 border-yellow-500'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-white font-medium text-sm">{alert.message}</p>
              <p className="text-gray-400 text-xs mt-1">
                {alert.route_code} • {new Date(alert.created_at).toLocaleTimeString()}
              </p>
            </div>
            {!alert.acknowledged && (
              <button 
                onClick={() => onAcknowledge(alert.id)}
                className="text-gray-400 hover:text-white text-xs bg-gray-700 px-2 py-1 rounded"
              >
                Ack
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
    
    {alerts.length === 0 && (
      <div className="text-center py-8">
        <p className="text-gray-400">No active alerts</p>
        <p className="text-gray-500 text-sm mt-1">System monitoring all routes</p>
      </div>
    )}
  </div>
);

const HourlyChart = ({ hourlyData }) => {
  const maxScore = Math.max(...hourlyData.map(h => h.piracy_opportunity_score));
  const currentHour = new Date().getHours();
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-white text-lg font-semibold mb-4">📊 24-Hour Piracy Opportunity Analysis</h3>
      <div className="grid grid-cols-12 gap-1 mb-4">
        {hourlyData.map((hour) => (
          <div key={hour.hour} className="text-center">
            <div 
              className={`rounded-t mb-1 transition-all hover:opacity-80 ${
                hour.hour === currentHour ? 'bg-yellow-500' : 'bg-red-600'
              }`}
              style={{
                height: `${Math.max((hour.piracy_opportunity_score / maxScore) * 100, 5)}px`,
                minHeight: '5px'
              }}
              title={`${hour.hour}:00 - Score: ${hour.piracy_opportunity_score.toFixed(1)} (${hour.data_source})`}
            ></div>
            <span className={`text-xs ${hour.hour === currentHour ? 'text-yellow-400 font-bold' : 'text-gray-400'}`}>
              {hour.hour}
            </span>
          </div>
        ))}
      </div>
      <div className="text-center">
        <p className="text-gray-400 text-sm">Hours (UTC) - Current hour highlighted • Hover for details</p>
        <div className="flex justify-center items-center space-x-4 mt-3">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-red-600 rounded"></div>
            <span className="text-xs text-gray-400">Opportunity Score</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span className="text-xs text-gray-400">Current Hour</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const HistoricalTrends = ({ trends }) => (
  <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
    <h3 className="text-white text-lg font-semibold mb-4">📈 Historical Trends</h3>
    <div className="space-y-4">
      {trends.slice(0, 5).map((trend, idx) => (
        <div key={idx} className="bg-black/30 rounded p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h4 className="text-white font-medium">{trend.commodity_name || 'Unknown'}</h4>
              <p className="text-gray-400 text-sm">{trend.route_code || 'Unknown'}</p>
            </div>
            <div className="text-right">
              <span className={`text-sm font-medium ${
                trend.profit_trend === 'increasing' ? 'text-green-400' : 
                trend.profit_trend === 'decreasing' ? 'text-red-400' : 'text-gray-400'
              }`}>
                {trend.profit_trend === 'increasing' ? '↗' : trend.profit_trend === 'decreasing' ? '↘' : '→'} {trend.profit_trend || 'stable'}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Avg Profit</p>
              <p className="text-white font-medium">{((trend.avg_profit || 0) / 1000000).toFixed(2)}M</p>
            </div>
            <div>
              <p className="text-gray-400">Max Score</p>
              <p className="text-red-400 font-medium">{(trend.max_piracy_rating || 0).toFixed(1)}</p>
            </div>
            <div>
              <p className="text-gray-400">Data Points</p>
              <p className="text-blue-400 font-medium">{trend.data_points?.length || 0}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
    {trends.length === 0 && (
      <div className="text-center py-8">
        <p className="text-gray-400">No historical trend data available</p>
        <p className="text-gray-500 text-sm mt-1">Data will appear as routes are analyzed over time</p>
      </div>
    )}
  </div>
);

const RefreshModal = ({ isOpen, onClose, logs, isRefreshing }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-white text-lg font-semibold">🔄 Manual Refresh Progress</h3>
          {!isRefreshing && (
            <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
          )}
        </div>
        
        <div className="bg-black rounded p-4 h-64 overflow-y-auto font-mono text-sm">
          {logs.map((log, idx) => (
            <div key={idx} className={`mb-1 ${
              log.type === 'error' ? 'text-red-400' : 
              log.type === 'success' ? 'text-green-400' : 'text-gray-300'
            }`}>
              <span className="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span> {log.message}
            </div>
          ))}
          {isRefreshing && (
            <div className="text-yellow-400 animate-pulse">
              ⏳ Refreshing in progress...
            </div>
          )}
        </div>
        
        {!isRefreshing && (
          <div className="mt-4 text-center">
            <button 
              onClick={onClose}
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// SnarePlan Location Mapping Database (synced with snareplan.dolus.eu)
const SNAREPLAN_LOCATIONS = {
  // STANTON SYSTEM
  'Stanton': {
    // Lagrange Points
    'ARC-L1 Wide Forest Station': 'Wide Forest Station',
    'ARC-L2 Lucky Pathway Station': 'Lucky Pathway Station', 
    'ARC-L3 Modern Express Station': 'Modern Express Station',
    'ARC-L4 Faint Glen Station': 'Faint Glen Station',
    'ARC-L5 Yellow Cave Station': 'Yellow Cave Station',
    'ARC-L5 Beautiful Glen Station': 'Beautiful Glen Station',
    
    'CRU-L2 Centipede Dream Station': 'Centipede Dream Station',
    'CRU-L4 Shallow Fields Station': 'Shallow Fields Station',
    
    'HUR-L1': 'HUR-L1',
    'HUR-L2': 'HUR-L2', 
    'HUR-L3': 'HUR-L3',
    'HUR-L4 Melodic Fields Station': 'Melodic Fields Station',
    'HUR-L5 High Course Station': 'High Course Station',
    'HUR-L5 Thundering Express Station': 'Thundering Express Station',
    
    'MIC-L1 Shallow Frontier Station': 'Shallow Frontier Station',
    'MIC-L2 Long Forest Station': 'Long Forest Station',
    'MIC-L3 Endless Odyssey Station': 'Endless Odyssey Station',
    'MIC-L4 Red Crossroads Station': 'Red Crossroads Station', 
    'MIC-L5 Modern Icarus Station': 'Modern Icarus Station',
    
    // Major Locations
    'Stanton': 'Stanton',
    'Terra Gateway': 'Terra Gateway',
    'Pyro Gateway': 'Pyro Gateway',
    'Whala Emergency Station': 'Whala Emergency Station',
    'Whala Emergency': 'Whala Emergency',
    
    // Planets and Moons (common variations)
    'MicroTech': 'MicroTech',
    'ArcCorp': 'ArcCorp', 
    'Hurston': 'Hurston',
    'Crusader': 'Crusader',
    'Area18': 'Area18',
    'Lorville': 'Lorville',
    'New Babbage': 'New Babbage',
    'Orison': 'Orison',
    
    // Common Station Names 
    'Port Olisar': 'Port Olisar',
    'Port Tressler': 'Port Tressler',
    'Everus Harbor': 'Everus Harbor',
    'Baijini Point': 'Baijini Point'
  },
  
  // PYRO SYSTEM  
  'Pyro': {
    'Pyro Gateway': 'Pyro Gateway',
    'Rat\'s Nest': 'Rats Nest',
    'Ruin Station': 'Ruin Station',
    'Pyro I': 'Pyro I',
    'Pyro II': 'Pyro II', 
    'Pyro III': 'Pyro III',
    'Pyro IV': 'Pyro IV',
    'Pyro V': 'Pyro V',
    'Pyro VI': 'Pyro VI'
  },
  
  // NYX SYSTEM
  'Nyx': {
    'Levski': 'Levski',
    'Delamar': 'Delamar'
  }
};

// SnarePlan URL Generator Helper Function (Updated with exact terminology)
const generateSnarePlanUrl = (routeData) => {
  if (!routeData) return null;
  
  // Extract system information from origin/destination names
  const extractSystemAndLocation = (locationName) => {
    if (!locationName) return { system: 'Stanton', location: 'Unknown' };
    
    // Parse "System - Location" format
    const parts = locationName.split(' - ');
    let system = 'Stanton'; // Default system
    let location = locationName;
    
    if (parts.length >= 2) {
      const potentialSystem = parts[0].trim();
      const potentialLocation = parts[1].trim();
      
      // Determine system
      if (potentialSystem.toLowerCase().includes('pyro')) {
        system = 'Pyro';
      } else if (potentialSystem.toLowerCase().includes('nyx')) {
        system = 'Nyx';
      } else if (potentialSystem.toLowerCase().includes('stanton')) {
        system = 'Stanton';
      }
      
      location = potentialLocation;
    }
    
    // Map location name to SnarePlan exact terminology
    let mappedLocation = location;
    if (SNAREPLAN_LOCATIONS[system] && SNAREPLAN_LOCATIONS[system][location]) {
      mappedLocation = SNAREPLAN_LOCATIONS[system][location];
    } else {
      // Try to find partial matches for complex names
      for (const [key, value] of Object.entries(SNAREPLAN_LOCATIONS[system] || {})) {
        if (location.includes(key) || key.includes(location)) {
          mappedLocation = value;
          break;
        }
      }
    }
    
    return { system, location: mappedLocation };
  };
  
  const origin = extractSystemAndLocation(routeData.origin_name);
  const destination = extractSystemAndLocation(routeData.destination_name);
  
  // Build SnarePlan URL with correct parameter structure and exact terminology
  const params = new URLSearchParams({
    'version': '4.3 LIVE',
    'system': origin.system,
    'origins': `${origin.location}:g`,
    'qedOrigin': 'c',
    'destinations': destination.location,
    'dd': '24',
    'edd': '24', 
    'dr': '60',
    'min': '0',
    'max': '100',
    'br': '2079',
    'calc': 'yes'
  });
  
  return `https://snareplan.dolus.eu/?${params.toString()}`;
};

const SnareModal = ({ isOpen, onClose, snareData }) => {
  if (!isOpen || !snareData) return null;

  // SnarePlan Integration Function with correct URL structure
  const openInSnarePlan = () => {
    const snarePlanUrl = generateSnarePlanUrl(snareData);
    if (snarePlanUrl) {
      window.open(snarePlanUrl, '_blank', 'noopener,noreferrer');
    } else {
      console.error('Could not generate SnarePlan URL for route data:', snareData);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-3xl w-full mx-4 border border-red-700">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-red-400 text-xl font-bold">🎯 SNARE NOW - OPTIMAL TARGET</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
        </div>
        
        <div className="bg-red-900/20 border border-red-600 rounded p-4 mb-4">
          <div className="flex items-center mb-2">
            <span className="text-red-400 text-2xl mr-2">⚠️</span>
            <h4 className="text-white font-semibold">PRIORITY INTERCEPTION TARGET</h4>
          </div>
          <p className="text-gray-300">{snareData.warning}</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-black/30 rounded p-4">
            <h4 className="text-yellow-400 font-semibold mb-3">📊 Route Details</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Route Code:</span>
                <span className="text-white font-mono">{snareData.route_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Commodity:</span>
                <span className="text-white">{snareData.commodity_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Origin:</span>
                <span className="text-white text-xs">{snareData.origin_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Destination:</span>
                <span className="text-white text-xs">{snareData.destination_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Expected Value:</span>
                <span className="text-green-400 font-bold">{(snareData.profit / 1000000).toFixed(2)}M aUEC</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Traffic Level:</span>
                <span className={`font-bold ${
                  snareData.traffic_level === 'HIGH' ? 'text-red-400' : 
                  snareData.traffic_level === 'MODERATE' ? 'text-yellow-400' : 'text-green-400'
                }`}>{snareData.traffic_level}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-black/30 rounded p-4">
            <h4 className="text-red-400 font-semibold mb-3">🎯 Interception Strategy</h4>
            <div className="space-y-3">
              <div>
                <p className="text-gray-400 text-sm mb-1">Optimal Position:</p>
                <p className="text-white font-semibold">{snareData.interception_point}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Estimated Traders/Hour:</p>
                <p className="text-yellow-400 font-bold text-lg">{snareData.estimated_traders_per_hour}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Piracy Rating:</p>
                <p className="text-red-400 font-bold text-lg">{snareData.piracy_rating.toFixed(1)}</p>
              </div>
            </div>
          </div>
        </div>
        
        {snareData.alternatives && snareData.alternatives.length > 0 && (
          <div className="mt-6 bg-black/30 rounded p-4">
            <h4 className="text-purple-400 font-semibold mb-3">🔄 Alternative Targets</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {snareData.alternatives.map((alt, idx) => (
                <div key={idx} className="bg-gray-700/30 rounded p-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-white">{alt.commodity_name}</span>
                    <span className="text-red-400 font-semibold">{alt.piracy_rating.toFixed(1)}</span>
                  </div>
                  <p className="text-gray-400 text-xs font-mono">{alt.route_code}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            onClick={openInSnarePlan}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded text-white font-semibold flex items-center justify-center"
          >
            🗺️ Open in SnarePlan
          </button>
          <button 
            onClick={onClose}
            className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded text-white font-semibold"
          >
            🏴‍☠️ Begin Hunt
          </button>
        </div>
      </div>
    </div>
  );
};

// Route Detail Modal Component  
// Alternative Routes Dropdown Component
const AlternativeRoutesDropdown = ({ commodity }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [terminals, setTerminals] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAlternativeRoutes = async () => {
    if (!commodity || terminals.length > 0) return; // Don't fetch if already loaded
    
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/commodity/terminals?commodity_name=${encodeURIComponent(commodity)}&data_source=web`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setTerminals(data.terminals || []);
      } else {
        console.error('Failed to fetch alternative routes:', data.message);
        setTerminals([]);
      }
    } catch (error) {
      console.error('Error fetching alternative routes:', error);
      setTerminals([]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      fetchAlternativeRoutes();
    }
  };

  const formatPrice = (price) => price > 0 ? price.toLocaleString('de-DE') : '-';
  const formatStock = (stock) => stock > 0 ? stock.toLocaleString('de-DE') : '-';

  return (
    <div className="mt-4 border-t border-gray-600 pt-4">
      <button 
        onClick={handleToggle}
        className="w-full flex items-center justify-between text-left text-blue-400 hover:text-blue-300 transition-colors"
      >
        <span className="font-semibold">📋 Alternative Routes ({commodity})</span>
        <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
      </button>
      
      {isOpen && (
        <div className="mt-3 bg-gray-800/50 rounded-lg p-3 max-h-96 overflow-y-auto">
          {loading ? (
            <div className="text-center text-gray-400 py-4">
              <div className="animate-spin inline-block w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full mr-2"></div>
              Loading alternative routes...
            </div>
          ) : terminals.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-600">
                    <th className="text-left text-gray-400 py-2 px-1">Terminal</th>
                    <th className="text-right text-gray-400 py-2 px-1">Buy Price</th>
                    <th className="text-right text-gray-400 py-2 px-1">Sell Price</th>
                    <th className="text-right text-gray-400 py-2 px-1">Stock</th>
                    <th className="text-center text-gray-400 py-2 px-1">System</th>
                  </tr>
                </thead>
                <tbody>
                  {terminals.map((terminal, idx) => (
                    <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                      <td className="py-2 px-1">
                        <div className="text-white font-medium">{terminal.terminal}</div>
                      </td>
                      <td className="text-right py-2 px-1">
                        <span className={terminal.buy_price > 0 ? 'text-red-400' : 'text-gray-500'}>
                          {formatPrice(terminal.buy_price)}
                        </span>
                      </td>
                      <td className="text-right py-2 px-1">
                        <span className={terminal.sell_price > 0 ? 'text-green-400' : 'text-gray-500'}>
                          {formatPrice(terminal.sell_price)}
                        </span>
                      </td>
                      <td className="text-right py-2 px-1">
                        <span className="text-blue-400">{formatStock(terminal.stock)}</span>
                      </td>
                      <td className="text-center py-2 px-1">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          terminal.system === 'Pyro' ? 'bg-red-600/20 text-red-400' : 'bg-blue-600/20 text-blue-400'
                        }`}>
                          {terminal.system}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-3 text-xs text-gray-400 text-center">
                📊 Showing {terminals.length} terminals • Data from Web Crawling • Updated from Star Profit
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-4">
              No alternative routes found for {commodity}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RouteDetailModal = ({ isOpen, onClose, route }) => {
  if (!isOpen || !route) return null;

  // SnarePlan Integration Function with correct URL structure
  const openInSnarePlan = () => {
    const snarePlanUrl = generateSnarePlanUrl(route);
    if (snarePlanUrl) {
      window.open(snarePlanUrl, '_blank', 'noopener,noreferrer');
    } else {
      console.error('Could not generate SnarePlan URL for route data:', route);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 border border-blue-700">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-blue-400 text-xl font-bold">📊 Route Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Route Info */}
          <div className="bg-black/30 rounded p-4">
            <h4 className="text-yellow-400 font-semibold mb-3">🛣️ Route Information</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Route Code:</span>
                <span className="text-white font-mono">{route.route_code}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Commodity:</span>
                <span className="text-white">{route.commodity_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Origin:</span>
                <span className="text-white text-xs">{route.origin_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Destination:</span>
                <span className="text-white text-xs">{route.destination_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Distance:</span>
                <span className="text-white">{route.distance?.toLocaleString()} GM</span>
              </div>
            </div>
          </div>

          {/* Financial Info */}
          <div className="bg-black/30 rounded p-4">
            <h4 className="text-green-400 font-semibold mb-3">💰 Financial Analysis</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Profit:</span>
                <span className="text-green-400 font-bold">{(route.profit / 1000000).toFixed(2)}M aUEC</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Investment:</span>
                <span className="text-white">{(route.investment / 1000000).toFixed(2)}M aUEC</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">ROI:</span>
                <span className="text-yellow-400">{route.roi?.toFixed(1)}%</span>
              </div>
              {route.buy_price > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Buy Price:</span>
                  <span className="text-yellow-400">{route.buy_price.toFixed(2)} aUEC</span>
                </div>
              )}
              {route.sell_price > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Sell Price:</span>
                  <span className="text-green-400">{route.sell_price.toFixed(2)} aUEC</span>
                </div>
              )}
              {route.buy_stock > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Buy Stock:</span>
                  <span className="text-blue-400">{route.buy_stock} SCU</span>
                </div>
              )}
              {route.sell_stock > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Sell Stock:</span>
                  <span className="text-purple-400">{route.sell_stock} SCU</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Risk Level:</span>
                <span className={`font-bold ${
                  route.risk_level === 'HIGH' ? 'text-red-400' : 
                  route.risk_level === 'MODERATE' ? 'text-yellow-400' : 'text-green-400'
                }`}>{route.risk_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Piracy Rating:</span>
                <span className="text-red-400 font-bold">{route.piracy_rating?.toFixed(1)}</span>
              </div>
            </div>
            
            {/* Alternative Routes Dropdown */}
            <AlternativeRoutesDropdown commodity={route.commodity_name} />
          </div>
        </div>

        {/* Interception Points */}
        {route.interception_zones && route.interception_zones.length > 0 && (
          <div className="mt-6 bg-black/30 rounded p-4">
            <h4 className="text-red-400 font-semibold mb-3">🎯 Interception Points</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {route.interception_zones.map((zone, idx) => (
                <div key={idx} className="bg-gray-700/30 rounded p-3 text-sm">
                  <div className="text-white font-semibold">{zone.name}</div>
                  <div className="text-gray-400 text-xs">Risk: {zone.risk_level}</div>
                  <div className="text-yellow-400 text-xs">Success: {zone.success_probability}%</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Coordinates */}
        {(route.coordinates_origin || route.coordinates_destination) && (
          <div className="mt-6 bg-black/30 rounded p-4">
            <h4 className="text-purple-400 font-semibold mb-3">🗺️ Coordinates</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {route.coordinates_origin && (
                <div>
                  <p className="text-gray-400 mb-1">Origin:</p>
                  <p className="text-white font-mono text-xs">
                    {route.coordinates_origin.x}, {route.coordinates_origin.y}, {route.coordinates_origin.z}
                  </p>
                </div>
              )}
              {route.coordinates_destination && (
                <div>
                  <p className="text-gray-400 mb-1">Destination:</p>
                  <p className="text-white font-mono text-xs">
                    {route.coordinates_destination.x}, {route.coordinates_destination.y}, {route.coordinates_destination.z}
                  </p>
                </div>  
              )}
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            onClick={openInSnarePlan}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded text-white font-semibold flex items-center justify-center"
          >
            🗺️ Open in SnarePlan
          </button>
          <button 
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded text-white font-semibold"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};

const CommoditySnareModal = ({ isOpen, onClose, onSnare }) => {
  const [selectedCommodity, setSelectedCommodity] = useState('');
  const [snareResults, setSnareResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Complete list of 106 Star Citizen commodities (alphabetically sorted)
  const allCommodities = [
    'Agricium', 'Altruciatoxin', 'Aluminum', 'Astatine', 'Beryl', 'Bexalite', 'Borase',
    'Chlorine', 'Compboard', 'Copper', 'Corundum', 'Diamond', 'Distilled Spirits', 'Dolivine',
    'E-Tam', 'Fluorine', 'Gold', 'Hephaestanite', 'Hydrogen', 'Iodine', 'Laranite',
    'Medical Supplies', 'Neon', 'Processed Food', 'Processed Narcotics', 'Quantanium',
    'Quantum Superconductors', 'Revenant Tree Pollen', 'SLAM', 'Scrap', 'Stims', 'Taranite',
    'Titanium', 'Tungsten', 'WiDoW',
    
    // Additional refined and processed commodities
    'Agricultural Supplies', 'Antimatter Containment Unit', 'Astatine Crystals', 'Audio Visual Equipment',
    'Beryl Crystal', 'Biological Samples', 'Black Market Goods', 'Ceramics', 'Chemical Compounds',
    'Composite Materials', 'Computer Components', 'Construction Materials', 'Coolant Systems',
    'Data Storage Devices', 'Deuterium', 'Electronics', 'Emergency Supplies', 'Energy Cells',
    'Engineering Components', 'Entertainment Equipment', 'Environmental Systems', 'Fabrics',
    'Farm Fresh Food', 'Fertilizer', 'Food Rations', 'Fuel Pods', 'Fusion Cores',
    'Gems', 'Glass', 'Grain', 'Heavy Metals', 'Holographic Data Storage',
    'Industrial Equipment', 'Industrial Gases', 'Industrial Lubricants', 'Ion Batteries',
    'Laser Components', 'Life Support Systems', 'Liquids', 'Luxury Goods', 'Maze',
    'Mechanical Components', 'Medical Equipment', 'Mining Equipment', 'Ore', 'Oxygen',
    'Personal Weapons', 'Pharmaceuticals', 'Plastics', 'Power Generators', 'Precious Metals',
    'Processed Ore', 'Quantum Components', 'Quantum Processors', 'Rare Earth Elements', 'Raw Materials',
    'Refined Fuel', 'Research Equipment', 'Salvage Materials', 'Semiconductors', 'Ship Components',
    'Specialized Tools', 'Synthetic Materials', 'Technical Manuals', 'Terraforming Equipment', 'Textiles',
    'Thermal Regulators', 'Tools', 'Trade Goods', 'Waste Products', 'Water', 'Weapons Components',
    
    // Rare and exotic materials
    'Antimatter', 'Artificial Intelligence Cores', 'Exotic Matter', 'Gravitational Wave Detectors',
    'Hypermatter', 'Metamaterials', 'Nanotubes', 'Neutronium', 'Plasma Conduits', 'Quantum Entangled Particles',
    'Rare Isotopes', 'Singularity Cores', 'Superconductors', 'Temporal Crystals', 'Unobtainium',
    
    // Food and agricultural products
    'Algae', 'Coffee', 'Fruit', 'Livestock', 'Meat', 'Milk Products', 'Protein Bars',
    'Seeds', 'Spices', 'Tea', 'Vegetables', 'Vitamins', 'Wine'
  ].sort(); // Alphabetically sorted

  const handleSnare = async () => {
    if (!selectedCommodity) return;
    
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/snare/commodity?commodity_name=${selectedCommodity}`);
      if (response.data.status === 'success') {
        setSnareResults(response.data);
      } else {
        console.error('Snare API error:', response.data);
        setSnareResults({
          status: 'error',
          commodity: selectedCommodity,
          message: response.data.message || 'Failed to analyze commodity routes',
          summary: {
            total_routes_found: 0,
            profitable_routes: 0,
            inter_system_routes: 0,
            same_system_routes: 0,
            average_profit: 0,
            max_piracy_rating: 0,
            recommended_strategy: 'No routes found'
          },
          snare_opportunities: []
        });
      }
    } catch (error) {
      console.error('Error setting commodity snare:', error);
      setSnareResults({
        status: 'error',
        commodity: selectedCommodity,
        message: error.response?.data?.message || error.message || 'Failed to connect to API',
        summary: {
          total_routes_found: 0,
          profitable_routes: 0,
          inter_system_routes: 0,
          same_system_routes: 0,
          average_profit: 0,
          max_piracy_rating: 0,
          recommended_strategy: 'Connection error'
        },
        snare_opportunities: []
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setSnareResults(null);
    setSelectedCommodity('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-screen overflow-y-auto border border-yellow-600">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-yellow-400 text-xl font-bold">💎 COMMODITY SNARE</h3>
          <button onClick={handleClose} className="text-gray-400 hover:text-white text-xl">✕</button>
        </div>
        
        {!snareResults && (
          <div>
            <div className="mb-6">
              <label className="block text-white font-semibold mb-2">Select Target Commodity:</label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 mb-4">
                {allCommodities.map(commodity => (
                  <button
                    key={commodity}
                    onClick={() => setSelectedCommodity(commodity)}
                    className={`p-2 rounded text-sm font-medium transition-colors ${
                      selectedCommodity === commodity 
                        ? 'bg-yellow-600 text-white' 
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {commodity}
                  </button>
                ))}
              </div>
              
              <input
                type="text"
                placeholder="Or enter custom commodity name..."
                value={selectedCommodity}
                onChange={(e) => setSelectedCommodity(e.target.value)}
                className="w-full bg-gray-700 text-white p-3 rounded border border-gray-600 focus:border-yellow-400"
              />
            </div>
            
            <div className="text-center">
              <button
                onClick={handleSnare}
                disabled={!selectedCommodity || isLoading}
                className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 px-6 py-3 rounded text-white font-bold"
              >
                {isLoading ? '⏳ Analyzing...' : '🎯 Set Commodity Snare'}
              </button>
            </div>
          </div>
        )}
        
        {snareResults && (
          <div>
            {snareResults.status === 'error' ? (
              <div className="bg-red-900/20 border border-red-600 rounded p-4 mb-6">
                <h4 className="text-red-400 font-bold text-lg mb-2">❌ {snareResults.commodity} Analysis Failed</h4>
                <p className="text-gray-300">{snareResults.message}</p>
              </div>
            ) : (
              <>
                <div className="bg-yellow-900/20 border border-yellow-600 rounded p-4 mb-6">
                  <h4 className="text-yellow-400 font-bold text-lg mb-2">📊 {snareResults.commodity} Analysis</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <p className="text-yellow-400 font-semibold">{snareResults.summary?.total_routes_found || 0}</p>
                      <p className="text-gray-400">Total Routes</p>
                    </div>
                    <div className="text-center">
                      <p className="text-green-400 font-semibold">{snareResults.summary?.profitable_routes || 0}</p>
                      <p className="text-gray-400">Profitable Routes</p>
                    </div>
                    <div className="text-center">
                      <p className="text-red-400 font-semibold">{snareResults.summary?.inter_system_routes || 0}</p>
                      <p className="text-gray-400">Inter-System</p>
                    </div>
                    <div className="text-center">
                      <p className="text-purple-400 font-semibold">{((snareResults.summary?.average_profit || 0) / 1000000).toFixed(2)}M</p>
                      <p className="text-gray-400">Avg Profit</p>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {(snareResults.snare_opportunities || []).slice(0, 10).map((opportunity, idx) => (
                    <div key={idx} className="bg-black/30 rounded p-4 border border-gray-600">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h5 className="text-white font-semibold">{opportunity.route_code || 'Unknown Route'}</h5>
                          <p className="text-yellow-400 text-sm">{opportunity.strategy || 'No strategy available'}</p>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            opportunity.risk_level === 'ELITE' ? 'bg-purple-900 text-purple-400' :
                            opportunity.risk_level === 'HIGH' ? 'bg-red-900 text-red-400' :
                            'bg-yellow-900 text-yellow-400'
                          }`}>
                            {opportunity.risk_level || 'UNKNOWN'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-gray-400">Buying Point:</p>
                          <p className="text-white">{opportunity.buying_point || 'Unknown'}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Selling Point:</p>
                          <p className="text-white">{opportunity.selling_point || 'Unknown'}</p>
                        </div>
                      </div>
                      
                      <div className="bg-gray-700/30 rounded p-2">
                        <p className={`text-sm font-medium ${
                          (opportunity.warning || '').includes('⚠️') ? 'text-orange-400' : 'text-green-400'
                        }`}>
                          {opportunity.warning || 'No additional information'}
                        </p>
                      </div>
                      
                      <div className="flex justify-between items-center mt-3 text-sm">
                        <span className="text-green-400 font-semibold">{((opportunity.profit || 0) / 1000000).toFixed(2)}M aUEC</span>
                        <span className="text-red-400 font-semibold">Score: {(opportunity.piracy_rating || 0).toFixed(1)}</span>
                        <span className="text-blue-400">{opportunity.estimated_traders || 0} traders/hour</span>
                      </div>
                    </div>
                  ))}
                </div>
                
                {(!snareResults.snare_opportunities || snareResults.snare_opportunities.length === 0) && (
                  <div className="text-center py-8">
                    <p className="text-gray-400 text-lg">No profitable routes found for {snareResults.commodity}</p>
                    <p className="text-gray-500 text-sm mt-2">Try a different commodity or check back later</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
        
        <div className="mt-6 text-center">
          <button 
            onClick={handleClose}
            className="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

const DatabasePanel = ({ dbStats, onRefreshStats, onClearAll, onClearOld, showAverageData }) => {
  const [mergeLoading, setMergeLoading] = useState(false);
  const [mergeStats, setMergeStats] = useState(null);
  
  const handleMergeRoutes = async () => {
    setMergeLoading(true);
    try {
      const response = await axios.post(`${API}/database/merge`);
      if (response.data.status === 'success') {
        setMergeStats(response.data.statistics);
        onRefreshStats(); // Refresh database stats
        alert(`✅ MERGE erfolgreich!\n\n${response.data.statistics.merged_routes} Routen zusammengefasst\n${response.data.statistics.duplicates_removed} Duplikate entfernt`);
      } else {
        throw new Error(response.data.message || 'Merge failed');
      }
    } catch (error) {
      console.error('Merge error:', error);
      alert(`❌ MERGE Fehler: ${error.message}`);
    } finally {
      setMergeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Database Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-700">
          <div className="text-center">
            <p className="text-blue-400 text-3xl font-bold">{dbStats?.routes || 0}</p>
            <p className="text-gray-400 text-sm">Routen analysiert</p>
          </div>
        </div>
        
        <div className="bg-green-900/20 rounded-lg p-4 border border-green-700">
          <div className="text-center">
            <p className="text-green-400 text-3xl font-bold">{dbStats?.commodities || 0}</p>
            <p className="text-gray-400 text-sm">Commodity Datensätze</p>
          </div>
        </div>
        
        <div className="bg-purple-900/20 rounded-lg p-4 border border-purple-700">
          <div className="text-center">
            <p className="text-purple-400 text-3xl font-bold">{dbStats?.interceptions || 0}</p>
            <p className="text-gray-400 text-sm">Interception Historie</p>
          </div>
        </div>
        
        <div className="bg-yellow-900/20 rounded-lg p-4 border border-yellow-700">
          <div className="text-center">
            <p className="text-yellow-400 text-3xl font-bold">{dbStats?.sizeFormatted || '0 B'}</p>
            <p className="text-gray-400 text-sm">Datenbankgröße</p>
          </div>
        </div>
      </div>

      {/* MERGE Statistics */}
      {mergeStats && (
        <div className="bg-green-900/10 border border-green-700 rounded-lg p-4">
          <h4 className="text-green-400 font-semibold mb-3">📊 Letzter MERGE Vorgang</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Original Routen:</p>
              <p className="text-white font-semibold">{mergeStats.total_original_routes}</p>
            </div>
            <div>
              <p className="text-gray-400">Einzigartige Routen:</p>
              <p className="text-white font-semibold">{mergeStats.unique_routes}</p>
            </div>
            <div>
              <p className="text-gray-400">Zusammengefasste:</p>
              <p className="text-green-400 font-semibold">{mergeStats.merged_routes}</p>
            </div>
            <div>
              <p className="text-gray-400">Duplikate entfernt:</p>
              <p className="text-red-400 font-semibold">{mergeStats.duplicates_removed}</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-black/30 rounded-lg p-4 mb-6">
        <h4 className="text-white font-semibold mb-3">📊 Datenbank Details</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-400">Gesamtdatensätze:</p>
            <p className="text-white font-semibold">{dbStats?.totalRecords || 0}</p>
          </div>
          <div>
            <p className="text-gray-400">Letztes Update:</p>
            <p className="text-white font-semibold">
              {dbStats?.lastUpdate ? new Date(dbStats.lastUpdate).toLocaleString('de-DE') : 'Nie'}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Speicherverbrauch:</p>
            <p className="text-white font-semibold">{dbStats?.sizeBytes || 0} Bytes</p>
          </div>
          <div>
            <p className="text-gray-400">Browser Storage:</p>
            <p className="text-white font-semibold">IndexedDB</p>
          </div>
        </div>
      </div>

      {/* Database Management Buttons */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h4 className="text-white font-semibold mb-4">🔧 Datenbank Verwaltung</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={onRefreshStats}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white font-medium transition-colors"
          >
            🔄 Statistiken aktualisieren
          </button>
          
          <button
            onClick={handleMergeRoutes}
            disabled={mergeLoading}
            className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 px-4 py-2 rounded text-white font-medium transition-colors"
          >
            {mergeLoading ? '⏳ Merging...' : '🔀 MERGE Duplikate'}
          </button>
          
          <button
            onClick={() => onClearOld(30)}
            className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded text-white font-medium transition-colors"
          >
            🗑️ Alte Daten löschen
          </button>
          
          <button
            onClick={onClearAll}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white font-medium transition-colors"
          >
            ⚠️ Alle Daten löschen
          </button>
        </div>
        
        <div className="mt-4 text-xs text-gray-400">
          <p>• MERGE: Zusammenfassen doppelter Routen mit Durchschnittswerten</p>
          <p>• Alte Daten: Löscht Einträge älter als 30 Tage</p>
          <p>• Alle Daten: Löscht komplette lokale Datenbank (nicht rückgängig machbar)</p>
        </div>
      </div>

      {/* Data Type Selector for Routes */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h4 className="text-white font-semibold mb-4">📈 Routen-Datenansicht</h4>
        <div className="flex items-center space-x-4 mb-4">
          <span className="text-gray-400">Aktuelle Ansicht:</span>
          <div className="flex space-x-2">
            <span className={`px-3 py-1 rounded text-sm ${showAverageData ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
              📊 {showAverageData ? 'Durchschnittsdaten' : 'Aktuelle Daten'}
            </span>
          </div>
        </div>
        <p className="text-xs text-gray-400">
          {showAverageData 
            ? '📊 Zeigt gemergerte Durchschnittswerte von zusammengefassten Routen' 
            : '📈 Zeigt die neuesten individuellen Routen-Analysen'
          }
        </p>
      </div>
    </div>
  );
};

const ExportPanel = ({ onExport, exportLoading }) => (
  <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
    <h3 className="text-white text-lg font-semibold mb-4">📁 Export Data</h3>
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <button 
          onClick={() => onExport('json')}
          disabled={exportLoading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-3 rounded font-medium transition-colors"
        >
          {exportLoading ? '⏳' : '📄'} Export JSON
        </button>
        <button 
          onClick={() => onExport('csv')}
          disabled={exportLoading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-3 rounded font-medium transition-colors"
        >
          {exportLoading ? '⏳' : '📊'} Export CSV
        </button>
      </div>
      
      <div className="bg-black/30 rounded p-3">
        <p className="text-gray-400 text-sm mb-2">Export includes:</p>
        <ul className="text-xs text-gray-300 space-y-1">
          <li>• Complete route analysis data</li>
          <li>• Piracy scores and risk levels</li>
          <li>• Profit margins and ROI</li>
          <li>• Interception coordinates</li>
          <li>• Historical trend data</li>
        </ul>
      </div>
    </div>
  </div>
);

function App() {
  const [routes, setRoutes] = useState([]);
  const [targets, setTargets] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [trackingStatus, setTrackingStatus] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [exportLoading, setExportLoading] = useState(false);
  
  // New state for enhanced features
  const [refreshModal, setRefreshModal] = useState({ open: false, logs: [], isRefreshing: false });
  const [snareModal, setSnareModal] = useState({ open: false, data: null });
  const [commoditySnareModal, setCommoditySnareModal] = useState(false);
  const [routeDetailModal, setRouteDetailModal] = useState({ open: false, route: null });
  const [dbStats, setDbStats] = useState(null);
  const [dataSource, setDataSource] = useState('api'); // 'api' or 'web'
  const [showAverageData, setShowAverageData] = useState(false); // Toggle between average and current data

  const fetchApiStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/status`);
      setApiStatus(response.data);
    } catch (error) {
      console.error('Error fetching API status:', error);
      setApiStatus({ status: 'error', error: error.message });
    }
  }, []);

  const fetchDbStats = useCallback(async () => {
    try {
      const stats = await sinisterDB.getStats();
      setDbStats(stats);
    } catch (error) {
      console.error('Error fetching database stats:', error);
      setDbStats({
        routes: 0,
        commodities: 0,
        interceptions: 0,
        totalRecords: 0,
        sizeBytes: 0,
        sizeFormatted: '0 B',
        lastUpdate: null
      });
    }
  }, []);

  const fetchRoutes = useCallback(async () => {
    try {
      const dataTypeParam = showAverageData ? 'averaged' : 'current';
      let response;
      
      if (showAverageData) {
        // Fetch averaged/merged data from backend
        response = await axios.get(`${API}/database/routes/${dataTypeParam}`);
        const routes = response.data.routes || [];
        setRoutes(routes);
        console.log(`✅ Fetched ${routes.length} ${dataTypeParam} routes`);
      } else {
        // Fetch current data with specified data source
        response = await axios.get(`${API}/routes/analyze?limit=20&min_score=10&include_coordinates=true&data_source=${dataSource}`);
        const newRoutes = response.data.routes || [];
        setRoutes(newRoutes);
        
        // Store routes in local database for historical analysis
        if (newRoutes.length > 0) {
          try {
            await sinisterDB.addRoutes(newRoutes);
            console.log(`✅ Stored ${newRoutes.length} routes from ${dataSource} in local database`);
            // Update database stats after adding routes
            await fetchDbStats();
          } catch (dbError) {
            console.warn('Database storage failed, continuing without local storage:', dbError);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching routes:', error);
    }
  }, [dataSource, showAverageData, fetchDbStats]);

  const fetchTargets = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/targets/priority?limit=15&min_piracy_score=60`);
      setTargets(response.data.targets || []);
    } catch (error) {
      console.error('Error fetching targets:', error);
    }
  }, []);

  // Route Detail Modal Handler
  const handleRouteClick = (route) => {
    setRouteDetailModal({ open: true, route });
  };

  const handleClearAllData = async () => {
    try {
      await sinisterDB.clearAllData();
      await fetchDbStats();
      console.log('All local data cleared');
    } catch (error) {
      console.error('Error clearing data:', error);
    }
  };

  const handleClearOldData = async (weeks) => {
    try {
      await sinisterDB.clearOldData(weeks);
      await fetchDbStats();
      console.log(`Cleared data older than ${weeks} weeks`);
    } catch (error) {
      console.error('Error clearing old data:', error);
    }
  };

  const getEnhancedSnareRecommendations = async () => {
    try {
      // Get best routes from local database with historical data
      const localRoutes = await sinisterDB.getBestInterceptionRoutes(10);
      
      if (localRoutes.length > 0) {
        // Use local data for more accurate predictions
        const bestRoute = localRoutes[0];
        const routeHistory = await sinisterDB.getRouteHistory(bestRoute.route_code, 7);
        
        console.log(`Found ${localRoutes.length} local routes, ${routeHistory.length} historical entries for best route`);
        
        return {
          route: bestRoute,
          history: routeHistory,
          confidence: routeHistory.length > 5 ? 'HIGH' : routeHistory.length > 2 ? 'MEDIUM' : 'LOW'
        };
      }
      
      return null;
    } catch (error) {
      console.error('Error getting enhanced recommendations:', error);
      return null;
    }
  };

  const fetchHourlyData = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/analysis/hourly`);
      setHourlyData(response.data.hourly_analysis || []);
    } catch (error) {
      console.error('Error fetching hourly data:', error);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/alerts?limit=20`);
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, []);

  const fetchTrends = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/trends/historical?hours_back=24`);
      setTrends(response.data.route_trends || []);
    } catch (error) {
      console.error('Error fetching trends:', error);
    }
  }, []);

  const fetchTrackingStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/tracking/status`);
      setTrackingStatus(response.data.tracking);
    } catch (error) {
      console.error('Error fetching tracking status:', error);
    }
  }, []);

  const acknowledgeAlert = async (alertId) => {
    try {
      await axios.post(`${API}/alerts/${alertId}/acknowledge`);
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ));
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleExport = async (format) => {
    setExportLoading(true);
    try {
      const response = await axios.get(`${API}/export/routes?format=${format}`);
      const data = response.data;
      
      if (format === 'csv') {
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    } finally {
      setExportLoading(false);
    }
  };

  const handleManualRefresh = async () => {
    setRefreshModal({ open: true, logs: [], isRefreshing: true });
    
    try {
      const response = await axios.post(`${API}/refresh/manual?data_source=${dataSource}`);
      
      if (response.data.status === 'success') {
        setRefreshModal(prev => ({ 
          ...prev, 
          logs: response.data.logs,
          isRefreshing: false 
        }));
        
        // Refresh the displayed data and update database stats
        setTimeout(async () => {
          await loadAllData();
          console.log('Data refreshed and stored in local database');
        }, 1000);
      } else {
        setRefreshModal(prev => ({ 
          ...prev, 
          logs: response.data.logs || [{ 
            timestamp: new Date().toISOString(), 
            message: "Refresh failed", 
            type: "error" 
          }],
          isRefreshing: false 
        }));
      }
    } catch (error) {
      setRefreshModal(prev => ({ 
        ...prev, 
        logs: [{ 
          timestamp: new Date().toISOString(), 
          message: `Error: ${error.message}`, 
          type: "error" 
        }],
        isRefreshing: false 
      }));
    }
  };

  const handleSnareNow = async () => {
    try {
      const response = await axios.get(`${API}/snare/now`);
      if (response.data.status === 'success') {
        setSnareModal({ open: true, data: response.data.snare_data });
      }
    } catch (error) {
      console.error('Error getting snare data:', error);
    }
  };

  const startTracking = async () => {
    try {
      await axios.post(`${API}/tracking/start`);
      setTrackingStatus(prev => ({ ...prev, active: true }));
    } catch (error) {
      console.error('Error starting tracking:', error);
    }
  };

  const stopTracking = async () => {
    try {
      await axios.post(`${API}/tracking/stop`);
      setTrackingStatus(prev => ({ ...prev, active: false }));
    } catch (error) {
      console.error('Error stopping tracking:', error);
    }
  };

  const loadAllData = useCallback(async () => {
    setLoading(true);
    await Promise.all([
      fetchApiStatus(),
      fetchRoutes(),
      fetchTargets(),
      fetchHourlyData(),
      fetchAlerts(),
      fetchTrends(),
      fetchTrackingStatus(),
      fetchDbStats()
    ]);
    setLoading(false);
  }, [fetchApiStatus, fetchRoutes, fetchTargets, fetchHourlyData, fetchAlerts, fetchTrends, fetchTrackingStatus, fetchDbStats]);

  useEffect(() => {
    const initializeApp = async () => {
      setLoading(true);
      
      // Initialize database with error handling
      try {
        await sinisterDB.init();
        console.log('✅ Sinister Database initialized successfully');
        await fetchDbStats();
      } catch (error) {
        console.error('❌ Error initializing database:', error);
        // Set default stats if database fails
        setDbStats({
          routes: 0,
          commodities: 0,
          interceptions: 0,
          totalRecords: 0,
          sizeBytes: 0,
          sizeFormatted: '0 B',
          lastUpdate: null
        });
      }
      
      // Load other data
      try {
        await Promise.all([
          fetchApiStatus(),
          fetchRoutes(),
          fetchTargets(),
          fetchHourlyData(),
          fetchAlerts(),
          fetchTrends(),
          fetchTrackingStatus()
        ]);
      } catch (error) {
        console.error('Error loading app data:', error);
      }
      
      setLoading(false);
    };

    initializeApp();
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      if (activeTab === 'dashboard' || activeTab === 'routes') {
        fetchRoutes();
        fetchTargets();
      }
      if (activeTab === 'alerts') {
        fetchAlerts();
      }
      fetchApiStatus();
      fetchTrackingStatus();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, activeTab, fetchRoutes, fetchTargets, fetchAlerts, fetchApiStatus, fetchTrackingStatus]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-white text-xl font-semibold">Loading Piracy Intelligence...</p>
          <p className="text-gray-400 mt-2">Analyzing Star Citizen trade routes</p>
          <div className="flex items-center justify-center space-x-2 mt-4">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Header 
        dataSource={dataSource}
        setDataSource={setDataSource}
        showAverageData={showAverageData}
        setShowAverageData={setShowAverageData}
      />
      
      {/* Enhanced Status Bar */}
      <div className="container mx-auto px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatusCard 
            title="Data Source" 
            value={apiStatus?.primary_data_source === 'real' ? 'Live Data' : 'Mock Data'} 
            status={apiStatus?.primary_data_source === 'real' ? 'good' : 'warning'} 
            icon="🌐" 
            subtitle={apiStatus?.primary_data_source === 'real' ? 
              `${apiStatus?.data_sources?.star_profit_api?.records_available || 0} live records` : 
              "Using simulation data"
            }
          />
          <StatusCard 
            title="Database" 
            value={apiStatus?.database === 'connected' ? 'Online' : 'Error'} 
            status={apiStatus?.database === 'connected' ? 'good' : 'error'} 
            icon="💾" 
            subtitle={`${apiStatus?.statistics?.total_routes_analyzed || 0} routes analyzed`}
          />
          <StatusCard 
            title="Active Routes" 
            value={routes.length} 
            status="good" 
            icon="🛣️" 
            subtitle={`${routes.filter(r => ['ELITE', 'LEGENDARY'].includes(r.risk_level)).length} high-value`}
          />
          <StatusCard 
            title="Live Alerts" 
            value={alerts.filter(a => !a.acknowledged).length} 
            status={alerts.filter(a => !a.acknowledged).length > 0 ? 'warning' : 'good'} 
            icon="🚨" 
            subtitle={`${alerts.filter(a => a.priority === 'CRITICAL').length} critical`}
          />
          <StatusCard 
            title="Tracking" 
            value={trackingStatus?.active ? 'Active' : 'Inactive'} 
            status={trackingStatus?.active ? 'good' : 'warning'} 
            icon="📡" 
            subtitle={trackingStatus?.active ? `${trackingStatus.uptime_minutes}m uptime` : 'Click to start'}
          />
        </div>
      </div>

      {/* Enhanced Navigation */}
      <div className="container mx-auto px-6">
        <div className="flex flex-wrap gap-1 bg-gray-800 rounded-lg p-1">
          {[
            { id: 'dashboard', label: '🎛️ Dashboard', desc: 'Overview' },
            { id: 'routes', label: '🛣️ Routes', desc: 'Trade Analysis' },
            { id: 'targets', label: '🎯 Targets', desc: 'Priority Hits' },
            { id: 'map', label: '🗺️ Map', desc: 'Interception' },
            { id: 'alerts', label: '🚨 Alerts', desc: 'Notifications' },
            { id: 'trends', label: '📈 Trends', desc: 'Historical' },
            { id: 'database', label: '💾 Database', desc: 'Lokale Daten' },
            { id: 'export', label: '📁 Export', desc: 'Data Export' }
          ].map(tab => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md transition-all duration-200 ${
                activeTab === tab.id 
                  ? 'bg-red-600 text-white shadow-lg' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <div className="text-sm font-medium">{tab.label}</div>
              <div className="text-xs opacity-75">{tab.desc}</div>
            </button>
          ))}
        </div>
        
        {/* Auto-refresh toggle */}
        <div className="flex justify-end mt-2">
          <label className="flex items-center space-x-2 text-sm text-gray-400">
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span>Auto-refresh (30s)</span>
          </label>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-6 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                {hourlyData.length > 0 && <HourlyChart hourlyData={hourlyData} />}
              </div>
              <div>
                <AlertsPanel alerts={alerts} onAcknowledge={acknowledgeAlert} />
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">🔥 Top Priority Targets</h3>
                <div className="space-y-4">
                  {targets.slice(0, 3).map((target, index) => (
                    <PirateTargetCard key={target.id || index} target={target} />
                  ))}
                </div>
              </div>
              <div>
                <InterceptionMap routes={routes} targets={targets} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'routes' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">🛣️ Trade Route Analysis</h2>
              <div className="flex space-x-3">
                <button 
                  onClick={handleSnareNow}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md transition-colors font-medium flex items-center"
                >
                  🎯 SNARE NOW
                </button>
                <button 
                  onClick={handleManualRefresh}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-md transition-colors font-medium flex items-center"
                >
                  🔄 Manual Refresh
                </button>
                <button 
                  onClick={() => setCommoditySnareModal(true)}
                  className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-md transition-colors font-medium flex items-center"
                >
                  💎 Commodity Snare
                </button>
                <button 
                  onClick={loadAllData}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-md transition-colors font-medium"
                >
                  ↻ Quick Refresh
                </button>
                <button 
                  onClick={trackingStatus?.active ? stopTracking : startTracking}
                  className={`px-4 py-2 rounded-md transition-colors font-medium ${
                    trackingStatus?.active 
                      ? 'bg-yellow-600 hover:bg-yellow-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {trackingStatus?.active ? '⏹️ Stop Tracking' : '▶️ Start Tracking'}
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {routes.map((route, index) => (
                <RouteCard 
                  key={route.id || index} 
                  route={route} 
                  onSelect={handleRouteClick}
                />
              ))}
            </div>
            {routes.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No routes available. Check API connection.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'targets' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">🎯 Priority Piracy Targets</h2>
              <button 
                onClick={fetchTargets}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md transition-colors font-medium"
              >
                🔄 Refresh Targets
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {targets.map((target, index) => (
                <PirateTargetCard key={target.id || index} target={target} />
              ))}
            </div>
            {targets.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No priority targets identified yet.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'map' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">🗺️ Interception Map Analysis</h2>
            <InterceptionMap routes={routes} targets={targets} />
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">🚨 Alert Management</h2>
            <AlertsPanel alerts={alerts} onAcknowledge={acknowledgeAlert} />
          </div>
        )}

        {activeTab === 'trends' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">📈 Historical Trends</h2>
            <HistoricalTrends trends={trends} />
            {hourlyData.length > 0 && (
              <div className="mt-6">
                <HourlyChart hourlyData={hourlyData} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'database' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">💾 Lokale Datenbank Verwaltung</h2>
            <DatabasePanel 
              dbStats={dbStats}
              onRefreshStats={fetchDbStats}
              onClearAll={handleClearAllData}
              onClearOld={handleClearOldData}
              showAverageData={showAverageData}
            />
          </div>
        )}

        {activeTab === 'export' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">📁 Data Export</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ExportPanel onExport={handleExport} exportLoading={exportLoading} />
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-white text-lg font-semibold mb-4">📊 Export Statistics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Routes:</span>
                    <span className="text-white font-medium">{routes.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Priority Targets:</span>
                    <span className="text-white font-medium">{targets.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Historical Data Points:</span>
                    <span className="text-white font-medium">{apiStatus?.statistics?.historical_data_points || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Active Alerts:</span>
                    <span className="text-white font-medium">{alerts.filter(a => !a.acknowledged).length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Modals */}
      <RefreshModal 
        isOpen={refreshModal.open}
        onClose={() => setRefreshModal(prev => ({ ...prev, open: false }))}
        logs={refreshModal.logs}
        isRefreshing={refreshModal.isRefreshing}
      />
      
      <SnareModal 
        isOpen={snareModal.open}
        onClose={() => setSnareModal({ open: false, data: null })}
        snareData={snareModal.data}
      />
      
      <RouteDetailModal 
        isOpen={routeDetailModal.open}
        onClose={() => setRouteDetailModal({ open: false, route: null })}
        route={routeDetailModal.route}
      />
      
      <CommoditySnareModal 
        isOpen={commoditySnareModal}
        onClose={() => setCommoditySnareModal(false)}
      />
    </div>
  );
}

export default App;