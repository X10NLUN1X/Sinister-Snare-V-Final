import React, { useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// Terminal zu Planet/System Zuordnung
const TERMINAL_MAPPING = {
  // Stanton System
  'TDD New Babbage': { planet: 'Microtech', system: 'Stanton' },
  'New Babbage': { planet: 'Microtech', system: 'Stanton' },
  'Port Tressler': { planet: 'Microtech', system: 'Stanton' },
  'Area18': { planet: 'ArcCorp', system: 'Stanton' },
  'Lorville': { planet: 'Hurston', system: 'Stanton' },
  'Orison': { planet: 'Crusader', system: 'Stanton' },
  'Port Olisar': { planet: 'Crusader', system: 'Stanton' },
  'Grim HEX': { planet: 'Yela', system: 'Stanton' },
  'Seraphim Station': { planet: 'Vanguard', system: 'Stanton' },
  'Deakins Research': { planet: 'Microtech', system: 'Stanton' },
  'CRU-L5': { planet: 'Crusader', system: 'Stanton' },
  'HUR-L1': { planet: 'Hurston', system: 'Stanton' },
  'HUR-L2': { planet: 'Hurston', system: 'Stanton' },
  'HUR-L3': { planet: 'Hurston', system: 'Stanton' },
  'HUR-L4': { planet: 'Hurston', system: 'Stanton' },
  'HUR-L5': { planet: 'Hurston', system: 'Stanton' },
  'ARC-L1': { planet: 'ArcCorp', system: 'Stanton' },
  'ARC-L2': { planet: 'ArcCorp', system: 'Stanton' },
  'ARC-L3': { planet: 'ArcCorp', system: 'Stanton' },
  'ARC-L4': { planet: 'ArcCorp', system: 'Stanton' },
  'ARC-L5': { planet: 'ArcCorp', system: 'Stanton' },
  'MIC-L1': { planet: 'Microtech', system: 'Stanton' },
  'MIC-L2': { planet: 'Microtech', system: 'Stanton' },
  'MIC-L3': { planet: 'Microtech', system: 'Stanton' },
  'MIC-L4': { planet: 'Microtech', system: 'Stanton' },
  'MIC-L5': { planet: 'Microtech', system: 'Stanton' },
  
  // Pyro System
  'Checkmate': { planet: 'Pyro VI', system: 'Pyro' },
  'Ruin Station': { planet: 'Pyro I', system: 'Pyro' },
  'Terminus': { planet: 'Pyro III', system: 'Pyro' },
  'Shady Glen': { planet: 'Pyro IV', system: 'Pyro' },
  'The Good Doctor': { planet: 'Pyro V', system: 'Pyro' },
  
  // Magnus Gateway
  'Magnus Gateway': { planet: 'Magnus', system: 'Stanton' },
  
  // Andere
  'Everus Harbor': { planet: 'Hurston', system: 'Stanton' },
  'Baijini Point': { planet: 'Hurston', system: 'Stanton' }
};

const getLocationInfo = (locationName) => {
  // Suche nach exakter Übereinstimmung
  if (TERMINAL_MAPPING[locationName]) {
    return TERMINAL_MAPPING[locationName];
  }
  
  // Suche nach partieller Übereinstimmung
  for (const [terminal, info] of Object.entries(TERMINAL_MAPPING)) {
    if (locationName.includes(terminal) || terminal.includes(locationName)) {
      return info;
    }
  }
  
  // Fallback basierend auf bekannten Schlüsselwörtern
  if (locationName.includes('Babbage') || locationName.includes('TDD')) {
    return { planet: 'Microtech', system: 'Stanton' };
  }
  if (locationName.includes('Area18') || locationName.includes('ArcCorp')) {
    return { planet: 'ArcCorp', system: 'Stanton' };
  }
  if (locationName.includes('Lorville') || locationName.includes('Hurston')) {
    return { planet: 'Hurston', system: 'Stanton' };
  }
  if (locationName.includes('Orison') || locationName.includes('Crusader')) {
    return { planet: 'Crusader', system: 'Stanton' };
  }
  if (locationName.includes('Checkmate') || locationName.includes('Pyro')) {
    return { planet: 'Pyro VI', system: 'Pyro' };
  }
  
  // Standard Fallback
  return { planet: 'Unknown', system: 'Unknown' };
};

const AdvancedSnareplanModal = ({ isOpen, onClose, routes }) => {
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [playerCoordinates, setPlayerCoordinates] = useState({ x: '', y: '', z: '' });
  const [interdictionData, setInterdictionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('route_selection');
  const [positionAnalysis, setPositionAnalysis] = useState(null);

  if (!isOpen) return null;

  const handleRouteSelect = (route) => {
    setSelectedRoute(route);
    calculateInterdiction(route);
  };

  const calculateInterdiction = async (route = selectedRoute) => {
    if (!route) return;

    setLoading(true);
    try {
      const routeData = {
        name: `${route.origin_name} → ${route.destination_name}`,
        origin_coordinates: route.coordinates_origin ? 
          [route.coordinates_origin.x, route.coordinates_origin.y, route.coordinates_origin.z] : [0, 0, 0],
        destination_coordinates: route.coordinates_destination ? 
          [route.coordinates_destination.x, route.coordinates_destination.y, route.coordinates_destination.z] : [100000, 0, 0]
      };

      const response = await axios.post(`${API}/interception/calculate`, {
        routes: [routeData],
        mantis_position: [0, 0, 0]
      });

      setInterdictionData(response.data);
      setActiveTab('overview_map');
    } catch (error) {
      console.error('Error calculating interdiction:', error);
      alert('Fehler bei der Interdiction-Berechnung. Bitte versuchen Sie es erneut.');
    } finally {
      setLoading(false);
    }
  };

  const analyzePlayerPosition = () => {
    if (!playerCoordinates.x || !playerCoordinates.y || !playerCoordinates.z || !selectedRoute) {
      alert('Bitte geben Sie gültige Koordinaten ein und wählen Sie eine Route aus.');
      return;
    }

    const playerPos = [
      parseFloat(playerCoordinates.x),
      parseFloat(playerCoordinates.y), 
      parseFloat(playerCoordinates.z)
    ];

    const optimalPos = interdictionData?.single_route_intercepts?.[0]?.intercept_data?.intercept_point || [0, 0, 0];
    
    const distance = Math.sqrt(
      Math.pow(playerPos[0] - optimalPos[0], 2) +
      Math.pow(playerPos[1] - optimalPos[1], 2) +
      Math.pow(playerPos[2] - optimalPos[2], 2)
    );

    const maxDistance = 20000;
    const coverage = Math.max(0, Math.min(100, ((maxDistance - distance) / maxDistance) * 100));

    const directions = {
      x: playerPos[0] < optimalPos[0] ? 'RECHTS' : playerPos[0] > optimalPos[0] ? 'LINKS' : 'OK',
      y: playerPos[1] < optimalPos[1] ? 'NORDEN' : playerPos[1] > optimalPos[1] ? 'SÜDEN' : 'OK',
      z: playerPos[2] < optimalPos[2] ? 'OBEN' : playerPos[2] > optimalPos[2] ? 'UNTEN' : 'OK'
    };

    setPositionAnalysis({
      distance: distance,
      coverage: coverage,
      directions: directions,
      optimal: coverage > 80,
      playerPosition: playerPos,
      optimalPosition: optimalPos
    });
  };

  const formatDistance = (distanceMeters) => {
    if (distanceMeters >= 1000000000) {
      return `${(distanceMeters / 1000000000).toFixed(1)} GM`;
    } else if (distanceMeters >= 1000000) {
      return `${(distanceMeters / 1000000).toFixed(1)} MM`;
    } else if (distanceMeters >= 1000) {
      return `${(distanceMeters / 1000).toFixed(1)} km`;
    } else {
      return `${distanceMeters.toFixed(0)} m`;
    }
  };

  const renderRouteSelection = () => (
    <div className="space-y-6">
      <div className="bg-red-900/20 border border-red-600 rounded-lg p-4">
        <h4 className="text-red-400 font-bold text-lg mb-2">🎯 Route für Interdiction auswählen</h4>
        <p className="text-gray-300 text-sm">Wählen Sie eine Handelsroute aus, um optimale Interdiction-Positionen zu berechnen.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto">
        {routes?.map((route, index) => {
          const originInfo = getLocationInfo(route.origin_name || '');
          const destInfo = getLocationInfo(route.destination_name || '');
          
          return (
            <div 
              key={route.id || index}
              className={`bg-gray-800 rounded-lg p-4 border cursor-pointer transition-all duration-300 ${
                selectedRoute?.id === route.id 
                  ? 'border-red-500 bg-red-900/20 shadow-lg shadow-red-500/20' 
                  : 'border-gray-700 hover:border-red-400 hover:shadow-lg'
              }`}
              onClick={() => handleRouteSelect(route)}
            >
              <div className="mb-4">
                <h5 className="text-white font-bold text-lg mb-2">{route.commodity_name}</h5>
                <div className="text-sm text-gray-400 mb-1">Route: {route.route_code}</div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-blue-400">🚀 Von:</span>
                  <div className="text-white font-medium">
                    <div>{originInfo.planet}</div>
                    <div className="text-xs text-gray-400">{route.origin_name}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-orange-400">🎯 Nach:</span>
                  <div className="text-white font-medium">
                    <div>{destInfo.planet}</div>
                    <div className="text-xs text-gray-400">{route.destination_name}</div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {originInfo.system} → {destInfo.system}
                </div>
              </div>
              
              <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-700">
                <div className="text-center">
                  <div className="text-green-400 font-bold">{((route.profit || 0) / 1000000).toFixed(2)}M</div>
                  <div className="text-gray-400 text-xs">Profit</div>
                </div>
                <div className="text-center">
                  <div className="text-red-400 font-bold">{route.piracy_rating}</div>
                  <div className="text-gray-400 text-xs">Piracy Score</div>
                </div>
                <div className="text-center">
                  <div className={`px-2 py-1 rounded text-xs font-bold ${
                    route.risk_level === 'ELITE' ? 'bg-red-600 text-white' :
                    route.risk_level === 'HIGH' ? 'bg-orange-600 text-white' :
                    route.risk_level === 'MODERATE' ? 'bg-yellow-600 text-black' :
                    'bg-green-600 text-white'
                  }`}>
                    {route.risk_level}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderOverviewMap = () => {
    if (!selectedRoute || !interdictionData) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <div className="text-gray-400">Keine Route ausgewählt oder Daten nicht verfügbar</div>
          </div>
        </div>
      );
    }

    const interceptData = interdictionData.single_route_intercepts?.[0]?.intercept_data;
    const coverage = interceptData?.coverage?.coverage_percentage || 0;
    const isInterdictionPossible = coverage > 10;
    
    const originInfo = getLocationInfo(selectedRoute.origin_name || '');
    const destInfo = getLocationInfo(selectedRoute.destination_name || '');

    return (
      <div className="space-y-6">
        {/* Interdiction Status */}
        <div className={`p-6 rounded-lg border-2 ${
          isInterdictionPossible 
            ? 'bg-red-900/30 border-red-500' 
            : 'bg-gray-900/30 border-gray-500'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`text-2xl font-bold ${isInterdictionPossible ? 'text-red-400' : 'text-gray-400'}`}>
                {isInterdictionPossible ? 'INTERDICTION MÖGLICH' : 'INTERDICTION NICHT MÖGLICH'}
              </h3>
              <p className="text-gray-300 mt-2">
                {isInterdictionPossible 
                  ? 'Verwenden Sie die nachfolgenden Anweisungen, um die Interdiction-Position zu erreichen.'
                  : 'Die aktuelle Route bietet keine optimalen Interdiction-Möglichkeiten.'
                }
              </p>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${isInterdictionPossible ? 'text-red-400' : 'text-gray-400'}`}>
                {coverage.toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Coverage</div>
            </div>
          </div>
        </div>

        {/* Overview Map */}
        <div className="bg-gray-900 rounded-lg p-6 border border-red-600">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-red-400 font-bold text-xl">OVERVIEW MAP</h4>
            <div className="flex space-x-4">
              <button className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white text-sm">
                📤 share
              </button>
              <button className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded text-white text-sm">
                📊 raw data
              </button>
            </div>
          </div>

          {/* Route Visualization */}
          <div className="bg-gray-800 rounded-lg p-8 mb-6 relative" style={{ minHeight: '400px' }}>
            <div className="flex items-center justify-between relative">
              {/* Origin */}
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold mb-3 border-2 border-blue-400">
                  🌍
                </div>
                <div className="text-white font-bold text-lg">{originInfo.planet}</div>
                <div className="text-gray-400 text-sm">{selectedRoute.origin_name}</div>
                <div className="text-gray-500 text-xs mt-1">{originInfo.system} System</div>
              </div>

              {/* Route Line with QED Position */}
              <div className="flex-1 mx-12 relative">
                <div className="h-3 bg-gradient-to-r from-blue-600 to-orange-600 rounded-full relative">
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <div className="w-6 h-6 bg-red-500 rounded-full border-4 border-yellow-400 pulse-animation"></div>
                    <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 text-yellow-400 text-sm font-bold whitespace-nowrap bg-black/80 px-2 py-1 rounded">
                      QED ZONE
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-between mt-6 text-sm text-gray-400">
                  <span>Start: {formatDistance(0)}</span>
                  <span>QED: {formatDistance(interceptData?.mantis_travel_distance / 2 || 0)}</span>
                  <span>Ende: {formatDistance(interceptData?.mantis_travel_distance || 0)}</span>
                </div>
                
                {/* Distance Markers */}
                <div className="mt-4 text-center">
                  <div className="text-white font-bold">Gesamtdistanz: {formatDistance(interceptData?.mantis_travel_distance || 0)}</div>
                </div>
              </div>

              {/* Destination */}
              <div className="text-center">
                <div className="w-20 h-20 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold mb-3 border-2 border-orange-400">
                  🏭
                </div>
                <div className="text-white font-bold text-lg">{destInfo.planet}</div>
                <div className="text-gray-400 text-sm">{selectedRoute.destination_name}</div>
                <div className="text-gray-500 text-xs mt-1">{destInfo.system} System</div>
              </div>
            </div>

            {/* ComArray Status */}
            <div className="absolute bottom-4 right-4 bg-red-900/50 rounded-lg p-4 border border-red-600">
              <div className="text-red-400 text-sm font-bold mb-1">ComArray Status</div>
              <div className="text-white text-sm">
                {coverage > 50 ? '✅ In Reichweite' : '❌ Außerhalb der Reichweite'}
              </div>
              <div className="text-gray-400 text-xs mt-1">
                QED Radius: 20km
              </div>
            </div>
          </div>

          {/* Route Instructions */}
          <div className="bg-red-900/20 rounded-lg p-6 border border-red-600">
            <h4 className="text-red-400 font-bold text-lg mb-4">🧭 ROUTE INSTRUCTIONS</h4>
            
            <div className="space-y-4">
              <div className="flex items-start space-x-4">
                <div className="bg-red-600 rounded-full p-3 text-white font-bold text-sm min-w-[100px] text-center">
                  Waypoint 1
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-blue-400">🔵</span>
                    <span className="text-white font-medium text-lg">
                      Jump from {originInfo.planet} to {destInfo.planet}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-orange-400">🗺️</span>
                    <span className="text-gray-300">
                      Route: {selectedRoute.origin_name} → {selectedRoute.destination_name}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-yellow-400">⚠️</span>
                    <span className="text-gray-300">
                      Stoppe bei {formatDistance(interceptData?.mantis_travel_distance || 0)} für QED Aktivierung.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-6">
              <div className="w-full bg-gray-700 rounded-full h-4">
                <div 
                  className="bg-gradient-to-r from-red-500 to-red-400 h-4 rounded-full transition-all duration-300" 
                  style={{ width: `${Math.min(coverage, 100)}%` }}
                ></div>
              </div>
              <div className="text-right mt-2 text-sm text-gray-400">
                Interdiction Coverage: {coverage.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPositionVerification = () => (
    <div className="space-y-6">
      <div className="bg-red-900/20 border border-red-600 rounded-lg p-6">
        <h4 className="text-red-400 font-bold text-xl mb-4">📍 POSITION VERIFICATION</h4>
        <p className="text-gray-300 mb-6">
          Geben Sie Ihre aktuellen Star Citizen Koordinaten ein (verwenden Sie <code className="bg-gray-800 px-2 py-1 rounded">/showlocation</code> im Spiel).
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="text-red-400 font-bold block mb-2">X-Koordinate</label>
            <input
              type="number"
              value={playerCoordinates.x}
              onChange={(e) => setPlayerCoordinates({...playerCoordinates, x: e.target.value})}
              placeholder="z.B. 12891.816"
              className="w-full bg-gray-800 text-white p-3 rounded border border-gray-600 focus:border-red-500"
            />
          </div>
          <div>
            <label className="text-red-400 font-bold block mb-2">Y-Koordinate</label>
            <input
              type="number"
              value={playerCoordinates.y}
              onChange={(e) => setPlayerCoordinates({...playerCoordinates, y: e.target.value})}
              placeholder="z.B. 50513.343"
              className="w-full bg-gray-800 text-white p-3 rounded border border-gray-600 focus:border-red-500"
            />
          </div>
          <div>
            <label className="text-red-400 font-bold block mb-2">Z-Koordinate</label>
            <input
              type="number"
              value={playerCoordinates.z}
              onChange={(e) => setPlayerCoordinates({...playerCoordinates, z: e.target.value})}
              placeholder="z.B. -1234.567"
              className="w-full bg-gray-800 text-white p-3 rounded border border-gray-600 focus:border-red-500"
            />
          </div>
        </div>

        <button
          onClick={analyzePlayerPosition}
          className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg text-white font-bold transition-all duration-300"
        >
          🎯 Position analysieren
        </button>
      </div>

      {positionAnalysis && (
        <div className="space-y-6">
          <div className={`p-6 rounded-lg border-2 ${
            positionAnalysis.optimal 
              ? 'bg-red-900/30 border-red-500' 
              : 'bg-gray-900/30 border-gray-500'
          }`}>
            <div className="text-center mb-4">
              <div className={`text-4xl font-bold ${positionAnalysis.optimal ? 'text-red-400' : 'text-gray-400'}`}>
                {positionAnalysis.coverage.toFixed(1)}% Coverage
              </div>
              <div className="text-gray-300 mt-2">
                Distanz zur optimalen Position: {formatDistance(positionAnalysis.distance)}
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 border border-gray-600">
            <h5 className="text-white font-bold text-lg mb-4">🧭 Positionierungs-Anweisungen</h5>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="text-center">
                <h6 className="text-red-400 font-bold mb-4">From the top</h6>
                <div className={`inline-block px-4 py-2 rounded text-white font-bold ${
                  positionAnalysis.coverage > 50 ? 'bg-red-600' : 'bg-gray-600'
                }`}>
                  {positionAnalysis.coverage.toFixed(0)}% coverage
                </div>
                
                <div className="mt-4 relative">
                  <div className="w-32 h-32 bg-gray-700 rounded-full mx-auto flex items-center justify-center border-2 border-red-500">
                    <div className="text-white text-2xl">🚀</div>
                  </div>
                  
                  {positionAnalysis.directions.x !== 'OK' && (
                    <div className={`absolute top-1/2 ${positionAnalysis.directions.x === 'RECHTS' ? 'right-0' : 'left-0'} transform -translate-y-1/2 text-yellow-400 text-3xl`}>
                      {positionAnalysis.directions.x === 'RECHTS' ? '➡️' : '⬅️'}
                    </div>
                  )}
                  {positionAnalysis.directions.y !== 'OK' && (
                    <div className={`absolute left-1/2 ${positionAnalysis.directions.y === 'NORDEN' ? 'top-0' : 'bottom-0'} transform -translate-x-1/2 text-yellow-400 text-3xl`}>
                      {positionAnalysis.directions.y === 'NORDEN' ? '⬆️' : '⬇️'}
                    </div>
                  )}
                </div>
              </div>

              <div className="text-center">
                <h6 className="text-red-400 font-bold mb-4">From the back</h6>
                <div className={`inline-block px-4 py-2 rounded text-white font-bold ${
                  positionAnalysis.coverage > 50 ? 'bg-red-600' : 'bg-gray-600'
                }`}>
                  {positionAnalysis.coverage.toFixed(0)}% coverage
                </div>
                
                <div className="mt-4 relative">
                  <div className="w-32 h-32 bg-gray-700 rounded-full mx-auto flex items-center justify-center border-2 border-red-500">
                    <div className="text-white text-xl font-bold">
                      {selectedRoute ? getLocationInfo(selectedRoute.origin_name || '').planet.charAt(0) : 'H'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-900/20 rounded-lg border border-yellow-600">
              <h6 className="text-yellow-400 font-bold mb-2">Bewegungsanweisungen:</h6>
              <div className="text-white text-sm space-y-1">
                {positionAnalysis.directions.x !== 'OK' && (
                  <div>• Bewegen Sie sich nach {positionAnalysis.directions.x}</div>
                )}
                {positionAnalysis.directions.y !== 'OK' && (
                  <div>• Bewegen Sie sich nach {positionAnalysis.directions.y}</div>
                )}
                {positionAnalysis.directions.z !== 'OK' && (
                  <div>• Bewegen Sie sich nach {positionAnalysis.directions.z}</div>
                )}
                {positionAnalysis.optimal && (
                  <div className="text-red-400 font-bold">✅ Ihre Position ist optimal!</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg w-[95vw] h-[95vh] overflow-y-auto border-2 border-red-600">
        <div className="flex justify-between items-center p-6 border-b border-red-600 bg-red-900/20">
          <div>
            <h3 className="text-red-400 text-2xl font-bold">🎯 Advanced Snareplan</h3>
            <p className="text-gray-300 text-sm mt-1">Star Citizen Quantum Interdiction System</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">✕</button>
        </div>

        <div className="flex space-x-2 p-6 border-b border-gray-700">
          <button 
            onClick={() => setActiveTab('route_selection')}
            className={`px-6 py-3 rounded-lg font-bold transition-all duration-300 ${
              activeTab === 'route_selection' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            ROUTE INSTRUCTIONS
          </button>
          <button 
            onClick={() => setActiveTab('overview_map')}
            className={`px-6 py-3 rounded-lg font-bold transition-all duration-300 ${
              activeTab === 'overview_map' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            disabled={!selectedRoute}
          >
            POSITION VERIFICATION
          </button>
          <button 
            onClick={() => setActiveTab('position_verification')}
            className={`px-6 py-3 rounded-lg font-bold transition-all duration-300 ${
              activeTab === 'position_verification' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            disabled={!selectedRoute}
          >
            POSITION NAVIGATION
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">⏳</div>
              <div className="text-red-400 font-bold">Berechne Interdiction-Daten...</div>
            </div>
          )}

          {!loading && activeTab === 'route_selection' && renderRouteSelection()}
          {!loading && activeTab === 'overview_map' && renderOverviewMap()}
          {!loading && activeTab === 'position_verification' && renderPositionVerification()}
        </div>
      </div>
    </div>
  );
};

export default AdvancedSnareplanModal;