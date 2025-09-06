import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Components
const Header = () => (
  <header className="bg-gradient-to-r from-red-900 to-black text-white p-6 shadow-lg">
    <div className="container mx-auto">
      <h1 className="text-4xl font-bold mb-2">⚔️ Sinister Snare</h1>
      <p className="text-xl opacity-90">Star Citizen Piracy Intelligence System</p>
      <p className="text-sm opacity-75 mt-1">Identify high-value trading routes for optimal interception opportunities</p>
    </div>
  </header>
);

const StatusCard = ({ title, value, status, icon }) => (
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-400 text-sm">{title}</p>
        <p className="text-white text-lg font-semibold">{value}</p>
      </div>
      <div className={`text-2xl ${status === 'good' ? 'text-green-400' : status === 'warning' ? 'text-yellow-400' : 'text-red-400'}`}>
        {icon}
      </div>
    </div>
  </div>
);

const RouteCard = ({ route }) => {
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'ELITE': return 'text-purple-400 bg-purple-900/20';
      case 'HIGH': return 'text-red-400 bg-red-900/20';
      case 'MODERATE': return 'text-yellow-400 bg-yellow-900/20';
      default: return 'text-green-400 bg-green-900/20';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-red-500 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white text-lg font-semibold mb-1">{route.commodity_name}</h3>
          <p className="text-gray-400 text-sm">{route.route_code}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(route.risk_level)}`}>
          {route.risk_level}
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Origin:</span>
          <span className="text-white">{route.origin_name}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Destination:</span>
          <span className="text-white">{route.destination_name}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-green-400">{(route.profit / 1000000).toFixed(2)}M</p>
          <p className="text-gray-400 text-xs">Profit (aUEC)</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-400">{route.piracy_rating}</p>
          <p className="text-gray-400 text-xs">Piracy Score</p>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="text-center">
          <p className="text-white font-medium">{route.roi.toFixed(1)}%</p>
          <p className="text-gray-400">ROI</p>
        </div>
        <div className="text-center">
          <p className="text-white font-medium">{(route.distance / 1000).toFixed(0)}k</p>
          <p className="text-gray-400">Distance (GM)</p>
        </div>
        <div className="text-center">
          <p className="text-white font-medium">{route.score}</p>
          <p className="text-gray-400">Traffic</p>
        </div>
      </div>
    </div>
  );
};

const PirateTargetCard = ({ target }) => (
  <div className="bg-gradient-to-r from-red-900/20 to-black/50 rounded-lg p-6 border border-red-700/50">
    <div className="flex justify-between items-start mb-4">
      <div>
        <h3 className="text-red-400 text-lg font-semibold mb-1">🎯 {target.commodity_name}</h3>
        <p className="text-gray-400 text-sm">{target.route_code}</p>
      </div>
      <div className="text-right">
        <p className="text-red-400 text-2xl font-bold">{target.piracy_score}</p>
        <p className="text-gray-400 text-xs">Priority Score</p>
      </div>
    </div>
    
    <div className="space-y-2 mb-4">
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Route:</span>
        <span className="text-white text-right">{target.origin_name} → {target.destination_name}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Expected Value:</span>
        <span className="text-green-400">{(target.expected_value / 1000000).toFixed(2)}M aUEC</span>
      </div>
    </div>
    
    <div className="bg-black/30 rounded p-3 mb-3">
      <p className="text-red-400 text-xs font-medium mb-2">🎯 Interception Points:</p>
      <ul className="text-xs text-gray-300 space-y-1">
        {target.interception_points.map((point, idx) => (
          <li key={idx}>• {point}</li>
        ))}
      </ul>
    </div>
    
    <div className="bg-black/30 rounded p-3">
      <p className="text-yellow-400 text-xs font-medium mb-2">⏰ Optimal Windows:</p>
      <ul className="text-xs text-gray-300 space-y-1">
        {target.optimal_time_windows.map((window, idx) => (
          <li key={idx}>• {window}</li>
        ))}
      </ul>
    </div>
  </div>
);

const HourlyChart = ({ hourlyData }) => {
  const maxScore = Math.max(...hourlyData.map(h => h.piracy_opportunity_score));
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-white text-lg font-semibold mb-4">📊 24-Hour Piracy Opportunity Analysis</h3>
      <div className="grid grid-cols-12 gap-1 mb-4">
        {hourlyData.map((hour) => (
          <div key={hour.hour} className="text-center">
            <div 
              className="bg-red-600 rounded-t mb-1 transition-all hover:bg-red-500"
              style={{
                height: `${(hour.piracy_opportunity_score / maxScore) * 100}px`,
                minHeight: '10px'
              }}
              title={`${hour.hour}:00 - Score: ${hour.piracy_opportunity_score}`}
            ></div>
            <span className="text-xs text-gray-400">{hour.hour}</span>
          </div>
        ))}
      </div>
      <div className="text-center">
        <p className="text-gray-400 text-sm">Hours (UTC) - Hover for details</p>
        <p className="text-red-400 text-sm mt-2">🔥 Peak Opportunity: 18:00-22:00 UTC</p>
      </div>
    </div>
  );
};

function App() {
  const [routes, setRoutes] = useState([]);
  const [targets, setTargets] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('routes');

  const fetchApiStatus = async () => {
    try {
      const response = await axios.get(`${API}/status`);
      setApiStatus(response.data);
    } catch (error) {
      console.error('Error fetching API status:', error);
      setApiStatus({ status: 'error', error: error.message });
    }
  };

  const fetchRoutes = async () => {
    try {
      const response = await axios.get(`${API}/routes/analyze?limit=20&min_score=10`);
      setRoutes(response.data.routes || []);
    } catch (error) {
      console.error('Error fetching routes:', error);
    }
  };

  const fetchTargets = async () => {
    try {
      const response = await axios.get(`${API}/targets/priority?limit=10`);
      setTargets(response.data.targets || []);
    } catch (error) {
      console.error('Error fetching targets:', error);
    }
  };

  const fetchHourlyData = async () => {
    try {
      const response = await axios.get(`${API}/analysis/hourly`);
      setHourlyData(response.data.hourly_analysis || []);
    } catch (error) {
      console.error('Error fetching hourly data:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchApiStatus(),
        fetchRoutes(),
        fetchTargets(),
        fetchHourlyData()
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-red-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Piracy Intelligence...</p>
          <p className="text-gray-400">Analyzing Star Citizen trade routes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Header />
      
      {/* Status Bar */}
      <div className="container mx-auto px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatusCard 
            title="UEX API Status" 
            value={apiStatus?.uex_api === 'connected' ? 'Connected' : 'Error'} 
            status={apiStatus?.uex_api === 'connected' ? 'good' : 'error'} 
            icon="🌐" 
          />
          <StatusCard 
            title="Database" 
            value={apiStatus?.database === 'connected' ? 'Online' : 'Error'} 
            status={apiStatus?.database === 'connected' ? 'good' : 'error'} 
            icon="💾" 
          />
          <StatusCard 
            title="Active Routes" 
            value={routes.length} 
            status="good" 
            icon="🛣️" 
          />
          <StatusCard 
            title="Priority Targets" 
            value={targets.length} 
            status="warning" 
            icon="🎯" 
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="container mx-auto px-6">
        <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
          <button 
            onClick={() => setActiveTab('routes')}
            className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'routes' ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            🛣️ Trade Routes
          </button>
          <button 
            onClick={() => setActiveTab('targets')}
            className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'targets' ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            🎯 Priority Targets
          </button>
          <button 
            onClick={() => setActiveTab('analysis')}
            className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'analysis' ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            📊 Time Analysis
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-6 py-6">
        {activeTab === 'routes' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">🛣️ Trade Route Analysis</h2>
              <button 
                onClick={fetchRoutes}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md transition-colors"
              >
                🔄 Refresh Data
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {routes.map((route, index) => (
                <RouteCard key={route.id || index} route={route} />
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
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md transition-colors"
              >
                🔄 Refresh Targets
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

        {activeTab === 'analysis' && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">📊 Temporal Analysis</h2>
            {hourlyData.length > 0 && <HourlyChart hourlyData={hourlyData} />}
            <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-white text-lg font-semibold mb-4">🧠 Intelligence Recommendations</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-black/30 rounded p-4">
                  <h4 className="text-red-400 font-medium mb-2">⏰ Peak Hours</h4>
                  <p className="text-gray-300 text-sm">18:00-22:00 UTC shows highest trader activity and profit potential</p>
                </div>
                <div className="bg-black/30 rounded p-4">
                  <h4 className="text-yellow-400 font-medium mb-2">🌟 High-Value Systems</h4>
                  <p className="text-gray-300 text-sm">Stanton system routes offer consistent high-value cargo opportunities</p>
                </div>
                <div className="bg-black/30 rounded p-4">
                  <h4 className="text-purple-400 font-medium mb-2">💎 Premium Commodities</h4>
                  <p className="text-gray-300 text-sm">Medical supplies and refined materials yield highest returns</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;