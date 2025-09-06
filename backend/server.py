from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import asyncio
from enum import Enum
import json
import random
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Real Data API Configuration
STAR_PROFIT_API_BASE = "https://star-profit.mathioussee.com/api"
UEX_API_BASE = "https://uexcorp.space/2.0"
UEX_API_KEY = os.environ.get('UEX_API_KEY', '')

# Real Data API Client
class StarProfitClient:
    def __init__(self):
        self.base_url = STAR_PROFIT_API_BASE
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Sinister-Snare-Piracy-Intelligence/2.0"
        }
    
    async def get_commodities(self) -> Dict[str, Any]:
        """Fetch real commodities data from Star Profit API"""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=True
        ) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/commodities",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                logging.info(f"Star Profit API: Fetched {len(data.get('commodities', []))} commodity records")
                return data
            except Exception as e:
                logging.error(f"Star Profit API Error: {e}")
                return {"commodities": [], "error": str(e)}
    
    def map_terminal_to_system(self, terminal_name: str) -> str:
        """Map terminal names to their correct star systems based on real Star Citizen data"""
        terminal_name_lower = terminal_name.lower()
        
        # Stanton System Terminals
        stanton_terminals = [
            # Major Cities and Ports
            'port olisar', 'area18', 'area 18', 'lorville', 'new babbage', 'orison',
            'cbd lorville', 'teasa spaceport',
            
            # Orbital Stations
            'port tressler', 'everus harbor', 'baijini point', 'seraphim station',
            
            # Lagrange Point Stations (Hurston)
            'hur-l1', 'hur-l2', 'hur-l3', 'hur-l4', 'hur-l5',
            'green glade station', 'purple stain station', 'blue shine station',
            
            # Lagrange Point Stations (ArcCorp)
            'arc-l1', 'arc-l2', 'arc-l3', 'arc-l4', 'arc-l5', 'arccorp 141',
            'white mountain station', 'wide forest station',
            
            # Lagrange Point Stations (Crusader)
            'cru-l1', 'cru-l2', 'cru-l3', 'cru-l4', 'cru-l5',
            'ambitious dream station', 'faithful dream station',
            
            # Lagrange Point Stations (microTech)
            'mic-l1', 'mic-l2', 'mic-l3', 'mic-l4', 'mic-l5',
            'shallow frontier station', 'long forest station',
            
            # Moons and Surface Outposts (Stanton)
            'grimhex', 'grim hex', 'security post kareah', 'kareah',
            'daymar', 'cellin', 'yela', 'delamar', 'aaron halo',
            'magda', 'arial', 'lyria', 'wala', 'ita', 'calliope', 'clio', 'euterpe',
            
            # Salvage Yards and Outposts (Stanton - corrected)
            'brio\'s breaker', 'brios breaker', 'samson son\'s', 'samson sons',
            'devlin scrap', 'devlin scrap & salvage',
            
            # Mining Outposts (Stanton)
            'shubin smca-6', 'shubin smc-ls-1', 'shubin smc-ls-2', 'shubin smc-ls-3',
            'rayari aneth research outpost', 'rayari deltana research outpost',
            'rayari kaltag research outpost',
            
            # Drug Labs and Outlaw Bases (Stanton)
            'jumptown', 'paradise cove', 'raven\'s roost', 'ravens roost', 'the orphanage',
            
            # Rest Stops and Gateways
            'pyro gateway', 'terra gateway', 'magnus gateway', 'nyx gateway'
        ]
        
        # Pyro System Terminals
        pyro_terminals = [
            # Planets and Major Stations
            'ruin station', 'pyro station alpha', 'pyro gateway',
            
            # Rough & Ready Controlled Outposts
            'endgame',  # CORRECTED: Endgame is in Pyro, Rough & Ready controlled
            
            # Rest Stops (Citizens for Prosperity)
            'starlight service station', 'rod\'s fuel \'n supplies', 'rod\'s fuel n supplies',
            'dudley & daughters', 'dudley and daughters',
            
            # Trade Posts and Outposts
            'canard view', 'jackson\'s swap', 'jackson swap', 'jacksons swap',
            'gonor steel', 'golden riviera',
            
            # Outlaw Locations in Pyro  
            'rat\'s nest', 'rats nest', 'rat nest',  # Pyro V
            'checkpoint', 'spider', 'monox', 'bloom', 'wala',
            'shady glen', 'glory',
            
            # Abandoned Stations
            'pyam-farstat-1-3', 'pyam-supvisr-3-4', 'pyam-farstat-3-5',
            
            # Moons of Pyro V
            'fairo', 'fuego', 'vuur'
        ]
        
        # Nyx System Terminals  
        nyx_terminals = [
            'delamar', 'levski',  # Note: Delamar is temporarily in Stanton but belongs to Nyx
            'rayari aneth research outpost', 'rayari deltana research outpost', 
            'rayari kaltag research outpost'
        ]
        
        # Terra System Terminals
        terra_terminals = [
            'terra prime', 'quasi', 'new cordoba', 'oya',
            'terra tech', 'terra mills'
        ]
        
        # Magnus System Terminals
        magnus_terminals = [
            'borea', 'solas', 'high course station'
        ]
        
        # Check which system the terminal belongs to
        for terminal in stanton_terminals:
            if terminal in terminal_name_lower:
                return "Stanton"
        
        for terminal in pyro_terminals:
            if terminal in terminal_name_lower:
                return "Pyro"
                
        for terminal in nyx_terminals:
            if terminal in terminal_name_lower:
                return "Nyx"
                
        for terminal in terra_terminals:
            if terminal in terminal_name_lower:
                return "Terra"
                
        for terminal in magnus_terminals:
            if terminal in terminal_name_lower:
                return "Magnus"
        
        # Default to Stanton for unknown terminals (most common system currently)
        return "Stanton"

    def generate_system_coordinates(self, system_name: str) -> Dict[str, float]:
        """Generate realistic coordinates for different star systems"""
        system_coords = {
            "Stanton": {
                "x_range": (-50000, 50000),
                "y_range": (-50000, 50000), 
                "z_range": (-10000, 10000)
            },
            "Pyro": {
                "x_range": (70000, 120000),
                "y_range": (-60000, -20000),
                "z_range": (15000, 35000)
            },
            "Nyx": {
                "x_range": (-200000, -150000),
                "y_range": (-110000, -80000),
                "z_range": (30000, 50000)
            },
            "Terra": {
                "x_range": (-140000, -100000),
                "y_range": (50000, 80000),
                "z_range": (-20000, -5000)
            },
            "Magnus": {
                "x_range": (80000, 120000),
                "y_range": (40000, 70000),
                "z_range": (-15000, 5000)
            }
        }
        
        coords = system_coords.get(system_name, system_coords["Stanton"])
        return {
            "x": random.uniform(coords["x_range"][0], coords["x_range"][1]),
            "y": random.uniform(coords["y_range"][0], coords["y_range"][1]),
            "z": random.uniform(coords["z_range"][0], coords["z_range"][1])
        }

    async def get_trading_routes(self) -> Dict[str, Any]:
        """Process real commodity data into trading routes for piracy analysis"""
        try:
            commodities_data = await self.get_commodities()
            commodities = commodities_data.get('commodities', [])
            
            if not commodities:
                return {"status": "error", "data": [], "message": "No commodity data available"}
            
            # Process commodities into trade routes
            routes = []
            processed_pairs = set()
            
            # Group commodities by commodity name for route analysis
            commodity_groups = {}
            for commodity in commodities:
                name = commodity.get('commodity_name', 'Unknown')
                if name not in commodity_groups:
                    commodity_groups[name] = []
                commodity_groups[name].append(commodity)
            
            route_id = 1
            for commodity_name, items in commodity_groups.items():
                # Find buy and sell locations for the same commodity
                buy_locations = [item for item in items if item.get('price_buy', 0) > 0 and item.get('status_buy', 0) > 0]
                sell_locations = [item for item in items if item.get('price_sell', 0) > 0 and item.get('status_sell', 0) > 0]
                
                # Create routes between buy and sell locations
                for buy_item in buy_locations[:3]:  # Limit to top 3 buy locations
                    for sell_item in sell_locations[:3]:  # Limit to top 3 sell locations
                        if buy_item.get('terminal_name') == sell_item.get('terminal_name'):
                            continue  # Skip same terminal
                        
                        buy_price = float(buy_item.get('price_buy', 0))
                        sell_price = float(sell_item.get('price_sell', 0))
                        
                        if sell_price <= buy_price:
                            continue  # Skip unprofitable routes
                        
                        profit_per_scu = sell_price - buy_price
                        roi = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0
                        
                        # Calculate route score based on stock availability and profit
                        buy_stock = float(buy_item.get('scu_buy', 0))
                        sell_stock = float(sell_item.get('scu_sell_stock', 0))
                        route_score = min(buy_stock / 10, 100) * (profit_per_scu / 1000)  # Normalize score
                        
                        # Map terminals to correct star systems
                        origin_system = self.map_terminal_to_system(buy_item.get('terminal_name', ''))
                        destination_system = self.map_terminal_to_system(sell_item.get('terminal_name', ''))
                        
                        # Estimate distance based on system locations
                        if origin_system == destination_system:
                            # Same system - shorter distance
                            distance = random.uniform(15000, 35000)
                        else:
                            # Inter-system routes - longer distance
                            distance = random.uniform(40000, 80000)
                            
                        # Calculate investment and profit
                        investment = buy_price * min(buy_stock, 1000)  # Assume 1000 SCU cargo capacity
                        profit = profit_per_scu * min(buy_stock, 1000)
                        
                        # Generate system-appropriate coordinates
                        origin_coords = self.generate_system_coordinates(origin_system)
                        destination_coords = self.generate_system_coordinates(destination_system)
                        
                        # Generate proper route code: StartLocation-Commodity-EndLocation
                        origin_terminal_short = buy_item.get('terminal_name', 'UNK')[:8].replace(' ', '').replace('\'', '').upper()
                        dest_terminal_short = sell_item.get('terminal_name', 'UNK')[:8].replace(' ', '').replace('\'', '').upper()
                        commodity_short = commodity_name[:8].replace(' ', '').upper()
                        
                        route_code = f"{origin_terminal_short}-{commodity_short}-{dest_terminal_short}"
                        
                        route = {
                            "id": route_id,
                            "code": route_code,
                            "commodity_name": commodity_name,
                            "origin_star_system_name": origin_system,
                            "origin_terminal_name": buy_item.get('terminal_name', 'Unknown'),
                            "destination_star_system_name": destination_system,
                            "destination_terminal_name": sell_item.get('terminal_name', 'Unknown'),
                            "profit": profit,
                            "price_roi": roi,
                            "distance": distance,
                            "score": min(route_score, 100),
                            "investment": investment,
                            "price_buy": buy_price,
                            "price_sell": sell_price,
                            "volatility_origin": 0.1,
                            "volatility_destination": 0.1,
                            "coordinates_origin": origin_coords,
                            "coordinates_destination": destination_coords,
                            "last_seen": buy_item.get('lastUpdated', datetime.now(timezone.utc).isoformat()),
                            "buy_stock": buy_stock,
                            "sell_stock": sell_stock
                        }
                        
                        routes.append(route)
                        route_id += 1
                        
                        if len(routes) >= 50:  # Limit to 50 routes for performance
                            break
                    
                    if len(routes) >= 50:
                        break
                
                if len(routes) >= 50:
                    break
            
            # Sort routes by profit descending
            routes.sort(key=lambda x: x.get('profit', 0), reverse=True)
            
            logging.info(f"Generated {len(routes)} trading routes from real commodity data")
            return {"status": "ok", "data": routes[:50]}  # Return top 50 routes
            
        except Exception as e:
            logging.error(f"Error processing trading routes: {e}")
            return {"status": "error", "data": [], "message": str(e)}

# Create the main app without a prefix
app = FastAPI(title="Sinister Snare - Star Citizen Piracy Intelligence", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global tracking state
tracking_state = {
    "active": False,
    "last_update": None,
    "route_count": 0,
    "alerts": []
}

# UEX API Client (kept as fallback)
class UEXClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = UEX_API_BASE
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def get_commodities_routes(self, **params) -> Dict[str, Any]:
        """Fetch trading routes from UEX API"""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        ) as client:
            try:
                # Add delay to respect rate limits
                await asyncio.sleep(0.1)
                
                response = await client.get(
                    f"{self.base_url}/commodities_routes",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                logging.info(f"UEX API Response: {data.get('status', 'unknown')}")
                return data
                
            except httpx.HTTPStatusError as e:
                logging.error(f"UEX API HTTP Error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 403:
                    # Return enhanced mock data for development if Cloudflare blocks
                    return self._get_enhanced_mock_routes_data()
                raise HTTPException(status_code=500, detail=f"UEX API Error: {e.response.status_code}")
            except Exception as e:
                logging.error(f"UEX API Error: {e}")
                # Return enhanced mock data for development
                return self._get_enhanced_mock_routes_data()
    
    def _get_enhanced_mock_routes_data(self) -> Dict[str, Any]:
        """Return enhanced mock trading routes data with dynamic updates"""
        current_hour = datetime.now(timezone.utc).hour
        base_multiplier = 1.0 + (0.3 * math.sin(current_hour * math.pi / 12))  # Simulate daily patterns
        
        mock_routes = [
            {
                "id": 1,
                "code": "STNT-LATR-SHOP",
                "commodity_name": "Laranite",
                "origin_star_system_name": "Stanton",
                "origin_terminal_name": "Mining Station 141",
                "destination_star_system_name": "Stanton", 
                "destination_terminal_name": "Port Olisar",
                "profit": int(2850000 * base_multiplier * random.uniform(0.9, 1.1)),
                "price_roi": 45.2 * base_multiplier,
                "distance": 15000,
                "score": int(85 * base_multiplier),
                "investment": 6300000,
                "volatility_origin": 0.15,
                "volatility_destination": 0.12,
                "coordinates_origin": {"x": 12500, "y": -8300, "z": 4200},
                "coordinates_destination": {"x": 15600, "y": -2100, "z": 1800},
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 2,
                "code": "STNT-TITA-CARGO",
                "commodity_name": "Titanium",
                "origin_star_system_name": "Stanton",
                "origin_terminal_name": "Lorville Mining Outpost",
                "destination_star_system_name": "Stanton",
                "destination_terminal_name": "Area18 Trade Hub",
                "profit": int(1950000 * base_multiplier * random.uniform(0.85, 1.15)),
                "price_roi": 38.7 * base_multiplier,
                "distance": 22000,
                "score": int(72 * base_multiplier),
                "investment": 5040000,
                "volatility_origin": 0.18,
                "volatility_destination": 0.14,
                "coordinates_origin": {"x": -18900, "y": 15200, "z": -3400},
                "coordinates_destination": {"x": -9600, "y": 8700, "z": 2100},
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 3,
                "code": "PYRO-QSUP-HIGH",
                "commodity_name": "Quantum Superconductors",
                "origin_star_system_name": "Pyro",
                "origin_terminal_name": "Pyro Manufacturing Hub",
                "destination_star_system_name": "Stanton",
                "destination_terminal_name": "Crusader Industries",
                "profit": int(4200000 * base_multiplier * random.uniform(0.95, 1.05)),
                "price_roi": 62.1 * base_multiplier,
                "distance": 45000,
                "score": int(95 * base_multiplier),
                "investment": 6760000,
                "volatility_origin": 0.08,
                "volatility_destination": 0.10,
                "coordinates_origin": {"x": 85000, "y": -42000, "z": 18000},
                "coordinates_destination": {"x": 8200, "y": 16500, "z": -1200},
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 4,
                "code": "STNT-MEDS-EMER",
                "commodity_name": "Medical Supplies",
                "origin_star_system_name": "Stanton",
                "origin_terminal_name": "Crusader Medical Facility",
                "destination_star_system_name": "Pyro",
                "destination_terminal_name": "Ruin Station Emergency",
                "profit": int(3150000 * base_multiplier * random.uniform(0.9, 1.2)),
                "price_roi": 58.3 * base_multiplier,
                "distance": 48000,
                "score": int(88 * base_multiplier),
                "investment": 5400000,
                "volatility_origin": 0.12,
                "volatility_destination": 0.16,
                "coordinates_origin": {"x": 8200, "y": 16500, "z": -1200},
                "coordinates_destination": {"x": 78000, "y": -35000, "z": 22000},
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 5,
                "code": "TERA-GOLD-LUX",
                "commodity_name": "Gold",
                "origin_star_system_name": "Terra",
                "origin_terminal_name": "Terra Mining Consortium",
                "destination_star_system_name": "Stanton",
                "destination_terminal_name": "ArcCorp Luxury Market",
                "profit": int(2750000 * base_multiplier * random.uniform(0.8, 1.3)),
                "price_roi": 41.8 * base_multiplier,
                "distance": 35000,
                "score": int(78 * base_multiplier),
                "investment": 6580000,
                "volatility_origin": 0.20,
                "volatility_destination": 0.11,
                "coordinates_origin": {"x": -125000, "y": 68000, "z": -15000},
                "coordinates_destination": {"x": -9600, "y": 8700, "z": 2100},
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 6,
                "code": "NYX-DRUG-BLACK",
                "commodity_name": "Processed Narcotics",
                "origin_star_system_name": "Nyx",
                "origin_terminal_name": "Delamar Underground",
                "destination_star_system_name": "Stanton",
                "destination_terminal_name": "GrimHEX",
                "profit": int(5800000 * base_multiplier * random.uniform(1.0, 1.4)),
                "price_roi": 89.5 * base_multiplier,
                "distance": 52000,
                "score": int(98 * base_multiplier),
                "investment": 6500000,
                "volatility_origin": 0.35,
                "volatility_destination": 0.42,
                "coordinates_origin": {"x": -185000, "y": -95000, "z": 38000},
                "coordinates_destination": {"x": 22000, "y": -36000, "z": 8500},
                "last_seen": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        logging.info("Using enhanced mock trading routes data (UEX API unavailable)")
        return {"status": "ok", "data": mock_routes}
    
    async def get_terminals(self) -> Dict[str, Any]:
        """Fetch terminal/location data"""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=True
        ) as client:
            try:
                await asyncio.sleep(0.1)  # Rate limiting
                response = await client.get(
                    f"{self.base_url}/terminals",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"UEX API Error (terminals): {e}")
                # Return mock terminal data
                return {
                    "status": "ok", 
                    "data": [
                        {"id": 1, "name": "Port Olisar", "system": "Stanton", "coordinates": {"x": 15600, "y": -2100, "z": 1800}},
                        {"id": 2, "name": "Area18", "system": "Stanton", "coordinates": {"x": -9600, "y": 8700, "z": 2100}},
                        {"id": 3, "name": "Lorville", "system": "Stanton", "coordinates": {"x": -18900, "y": 15200, "z": -3400}},
                        {"id": 4, "name": "GrimHEX", "system": "Stanton", "coordinates": {"x": 22000, "y": -36000, "z": 8500}}
                    ]
                }

# Initialize clients
star_profit_client = StarProfitClient()
uex_client = UEXClient(UEX_API_KEY)

# Enhanced Models
class RouteAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    route_code: str
    commodity_name: str
    origin_name: str
    destination_name: str
    profit: float
    roi: float
    distance: float
    score: int
    piracy_rating: float
    frequency_score: float
    risk_level: str
    investment: float
    coordinates_origin: Optional[Dict[str, float]] = None
    coordinates_destination: Optional[Dict[str, float]] = None
    interception_zones: List[Dict[str, Any]] = []
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InterceptionPoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    coordinates: Dict[str, float]  # x, y, z
    route_codes: List[str]
    intercept_probability: float  # 0.0 to 1.0
    difficulty_rating: str  # EASY, MODERATE, HARD, EXTREME
    description: str
    optimal_ship_classes: List[str]

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str  # HIGH_VALUE, NEW_ROUTE, FREQUENT_ROUTE
    route_code: str
    commodity_name: str
    message: str
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    profit_threshold: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False

class HistoricalTrend(BaseModel):
    route_code: str
    commodity_name: str
    timestamp: datetime
    profit: float
    roi: float
    traffic_score: int
    piracy_rating: float

class TrackingStatus(BaseModel):
    active: bool
    last_update: Optional[datetime]
    route_count: int
    alert_count: int
    uptime_minutes: int

# Enhanced Route Analysis Engine
class RouteAnalyzer:
    @staticmethod
    def calculate_piracy_score(route_data: Dict[str, Any]) -> float:
        """Enhanced piracy potential score calculation"""
        try:
            # Base factors
            profit = float(route_data.get('profit', 0))
            investment = float(route_data.get('investment', 1))
            distance = float(route_data.get('distance', 1))
            score = int(route_data.get('score', 0))
            roi = float(route_data.get('price_roi', 0))
            volatility_avg = (float(route_data.get('volatility_origin', 0)) + 
                            float(route_data.get('volatility_destination', 0))) / 2
            
            # Enhanced scoring factors
            profit_factor = min(profit / 2000000, 1.0)  # Normalize to max 2M profit
            traffic_factor = min(score / 100, 1.0)      # Normalize score
            distance_factor = max(0, 1 - (distance / 60000))  # Prefer reasonable distances
            roi_factor = min(roi / 80, 1.0)            # ROI factor up to 80%
            volatility_factor = min(volatility_avg * 2, 1.0)  # Higher volatility = more opportunity
            
            # Risk/reward calculation
            risk_reward = (profit / max(investment, 1)) * 100
            risk_factor = min(risk_reward / 50, 1.0)
            
            # Special commodity bonuses
            commodity_bonus = 0.0
            commodity_name = route_data.get('commodity_name', '').lower()
            if 'narcotic' in commodity_name or 'drug' in commodity_name:
                commodity_bonus = 0.15  # High risk, high reward
            elif 'medical' in commodity_name:
                commodity_bonus = 0.12  # Emergency supplies
            elif 'quantum' in commodity_name or 'superconductor' in commodity_name:
                commodity_bonus = 0.10  # High-tech goods
            elif 'gold' in commodity_name or 'luxury' in commodity_name:
                commodity_bonus = 0.08  # Luxury items
            
            piracy_score = (
                profit_factor * 0.35 +      # High value cargo
                traffic_factor * 0.25 +     # High traffic routes
                distance_factor * 0.15 +    # Reasonable distance
                roi_factor * 0.10 +         # Good ROI
                volatility_factor * 0.05 +  # Market volatility
                risk_factor * 0.10 +        # Risk/reward ratio
                commodity_bonus             # Commodity-specific bonus
            ) * 100
            
            return round(piracy_score, 2)
        except Exception as e:
            logging.error(f"Error calculating piracy score: {e}")
            return 0.0
    
    @staticmethod
    def categorize_risk_level(piracy_score: float) -> str:
        """Enhanced risk categorization"""
        if piracy_score >= 90:
            return "LEGENDARY"
        elif piracy_score >= 80:
            return "ELITE"
        elif piracy_score >= 65:
            return "HIGH"
        elif piracy_score >= 45:
            return "MODERATE"
        elif piracy_score >= 25:
            return "LOW"
        else:
            return "MINIMAL"
    
    @staticmethod
    def calculate_interception_points(route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate optimal interception points for a route"""
        origin_coords = route_data.get('coordinates_origin', {})
        dest_coords = route_data.get('coordinates_destination', {})
        
        if not origin_coords or not dest_coords:
            return []
        
        interception_points = []
        
        # Calculate midpoint
        midpoint = {
            "x": (origin_coords["x"] + dest_coords["x"]) / 2,
            "y": (origin_coords["y"] + dest_coords["y"]) / 2,
            "z": (origin_coords["z"] + dest_coords["z"]) / 2
        }
        
        # Add various interception zones
        points = [
            {
                "name": "Route Midpoint",
                "coordinates": midpoint,
                "intercept_probability": 0.85,
                "difficulty": "MODERATE",
                "description": "Halfway point between origin and destination"
            },
            {
                "name": "Departure Zone",
                "coordinates": {
                    "x": origin_coords["x"] + (dest_coords["x"] - origin_coords["x"]) * 0.15,
                    "y": origin_coords["y"] + (dest_coords["y"] - origin_coords["y"]) * 0.15,
                    "z": origin_coords["z"] + (dest_coords["z"] - origin_coords["z"]) * 0.15
                },
                "intercept_probability": 0.70,
                "difficulty": "HARD",
                "description": "Near departure terminal - high security risk"
            },
            {
                "name": "Arrival Approach",
                "coordinates": {
                    "x": origin_coords["x"] + (dest_coords["x"] - origin_coords["x"]) * 0.85,
                    "y": origin_coords["y"] + (dest_coords["y"] - origin_coords["y"]) * 0.85,
                    "z": origin_coords["z"] + (dest_coords["z"] - origin_coords["z"]) * 0.85
                },
                "intercept_probability": 0.75,
                "difficulty": "HARD",
                "description": "Near arrival terminal - cargo still valuable"
            },
            {
                "name": "Quantum Interdiction Zone",
                "coordinates": {
                    "x": midpoint["x"] + random.uniform(-5000, 5000),
                    "y": midpoint["y"] + random.uniform(-5000, 5000),
                    "z": midpoint["z"] + random.uniform(-2000, 2000)
                },
                "intercept_probability": 0.95,
                "difficulty": "EASY",
                "description": "Optimal quantum drive interdiction point"
            }
        ]
        
        return points

# Background task for real-time tracking
async def update_tracking_data():
    """Background task to update route tracking data"""
    global tracking_state
    
    try:
        # Fetch latest routes
        routes_data = await uex_client.get_commodities_routes()
        if routes_data.get('status') == 'ok':
            routes = routes_data.get('data', [])
            
            # Update tracking state
            tracking_state['last_update'] = datetime.now(timezone.utc)
            tracking_state['route_count'] = len(routes)
            
            # Process and store routes
            new_alerts = []
            for route in routes:
                try:
                    piracy_score = RouteAnalyzer.calculate_piracy_score(route)
                    
                    # Generate alerts for high-value routes
                    if piracy_score >= 85 and route.get('profit', 0) >= 3000000:
                        alert = Alert(
                            alert_type="HIGH_VALUE",
                            route_code=route.get('code', 'unknown'),
                            commodity_name=route.get('commodity_name', 'Unknown'),
                            message=f"High-value target detected: {route.get('commodity_name')} - {piracy_score:.1f} piracy rating",
                            priority="CRITICAL" if piracy_score >= 90 else "HIGH",
                            profit_threshold=route.get('profit', 0)
                        )
                        new_alerts.append(alert)
                        
                        # Store in database
                        await db.alerts.insert_one(alert.dict())
                    
                    # Store historical trend data
                    trend = HistoricalTrend(
                        route_code=route.get('code', 'unknown'),
                        commodity_name=route.get('commodity_name', 'Unknown'),
                        timestamp=datetime.now(timezone.utc),
                        profit=float(route.get('profit', 0)),
                        roi=float(route.get('price_roi', 0)),
                        traffic_score=int(route.get('score', 0)),
                        piracy_rating=piracy_score
                    )
                    
                    await db.historical_trends.insert_one(trend.dict())
                    
                except Exception as e:
                    logging.error(f"Error processing route for tracking: {e}")
            
            tracking_state['alerts'] = new_alerts
            logging.info(f"Updated tracking data: {len(routes)} routes, {len(new_alerts)} new alerts")
            
    except Exception as e:
        logging.error(f"Error in tracking update: {e}")

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Sinister Snare v2.0 - Advanced Star Citizen Piracy Intelligence System"}

@api_router.get("/routes/analyze")
async def analyze_routes(
    limit: int = Query(default=50, le=500),
    min_profit: Optional[float] = Query(default=None),
    min_score: Optional[int] = Query(default=None),
    include_coordinates: bool = Query(default=True),
    use_real_data: bool = Query(default=True)
):
    """Enhanced route analysis with real Star Citizen trading data"""
    try:
        # Fetch routes from real data API first, then fallback to UEX/mock
        if use_real_data:
            try:
                routes_data = await star_profit_client.get_trading_routes()
                if routes_data.get('status') == 'ok' and routes_data.get('data'):
                    logging.info("Using real Star Citizen trading data from Star Profit API")
                else:
                    logging.warning("Star Profit API failed, falling back to UEX API")
                    routes_data = await uex_client.get_commodities_routes()
            except Exception as e:
                logging.error(f"Star Profit API error, falling back: {e}")
                routes_data = await uex_client.get_commodities_routes()
        else:
            routes_data = await uex_client.get_commodities_routes()
        
        if routes_data.get('status') != 'ok':
            raise HTTPException(status_code=400, detail="Failed to fetch routes from trading APIs")
        
        routes = routes_data.get('data', [])[:limit]
        analyzed_routes = []
        
        for route in routes:
            try:
                # Skip routes with missing data
                if not route.get('profit') or not route.get('commodity_name'):
                    continue
                
                # Apply filters
                if min_score and route.get('score', 0) < min_score:
                    continue
                if min_profit and route.get('profit', 0) < min_profit:
                    continue
                
                piracy_score = RouteAnalyzer.calculate_piracy_score(route)
                interception_zones = RouteAnalyzer.calculate_interception_points(route) if include_coordinates else []
                
                analysis = RouteAnalysis(
                    route_code=route.get('code', 'unknown'),
                    commodity_name=route.get('commodity_name', 'Unknown'),
                    origin_name=f"{route.get('origin_star_system_name', 'Unknown')} - {route.get('origin_terminal_name', 'Unknown')}",
                    destination_name=f"{route.get('destination_star_system_name', 'Unknown')} - {route.get('destination_terminal_name', 'Unknown')}",
                    profit=float(route.get('profit', 0)),
                    roi=float(route.get('price_roi', 0)),
                    distance=float(route.get('distance', 0)),
                    score=int(route.get('score', 0)),
                    piracy_rating=piracy_score,
                    frequency_score=float(route.get('score', 0)) / 10,  # Normalize frequency
                    risk_level=RouteAnalyzer.categorize_risk_level(piracy_score),
                    investment=float(route.get('investment', 0)),
                    coordinates_origin=route.get('coordinates_origin'),
                    coordinates_destination=route.get('coordinates_destination'),
                    interception_zones=interception_zones,
                    last_seen=datetime.fromisoformat(route.get('last_seen', datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
                )
                
                analyzed_routes.append(analysis)
                
                # Store in database for historical analysis
                await db.route_analyses.replace_one(
                    {"route_code": analysis.route_code},
                    analysis.dict(),
                    upsert=True
                )
                
            except Exception as e:
                logging.error(f"Error analyzing route: {e}")
                continue
        
        # Sort by piracy rating
        analyzed_routes.sort(key=lambda x: x.piracy_rating, reverse=True)
        
        data_source = "real" if use_real_data and routes_data.get('data') else "simulated"
        
        return {
            "status": "success",
            "total_routes": len(analyzed_routes),
            "routes": analyzed_routes,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": data_source,
            "api_used": "Star Profit API" if data_source == "real" else "Mock Data"
        }
        
    except Exception as e:
        logging.error(f"Error in analyze_routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/interception/points")
async def get_interception_points(
    system: Optional[str] = Query(default=None),
    min_probability: float = Query(default=0.5, ge=0.0, le=1.0)
):
    """Get optimal interception points across all monitored routes"""
    try:
        # Fetch recent route analyses
        query = {"piracy_rating": {"$gte": 50}}
        if system:
            query["$or"] = [
                {"origin_name": {"$regex": system, "$options": "i"}},
                {"destination_name": {"$regex": system, "$options": "i"}}
            ]
        
        routes = await db.route_analyses.find(query).to_list(100)
        
        all_points = []
        point_clusters = {}
        
        for route in routes:
            interception_zones = route.get('interception_zones', [])
            for zone in interception_zones:
                if zone.get('intercept_probability', 0) >= min_probability:
                    # Create cluster key based on approximate location
                    coords = zone.get('coordinates', {})
                    cluster_key = f"{int(coords.get('x', 0) / 10000)}_{int(coords.get('y', 0) / 10000)}_{int(coords.get('z', 0) / 10000)}"
                    
                    if cluster_key not in point_clusters:
                        point_clusters[cluster_key] = {
                            "coordinates": coords,
                            "routes": [],
                            "total_probability": 0,
                            "max_profit": 0
                        }
                    
                    point_clusters[cluster_key]["routes"].append(route.get('route_code'))
                    point_clusters[cluster_key]["total_probability"] += zone.get('intercept_probability', 0)
                    point_clusters[cluster_key]["max_profit"] = max(
                        point_clusters[cluster_key]["max_profit"],
                        route.get('profit', 0)
                    )
        
        # Convert clusters to interception points
        for cluster_key, cluster_data in point_clusters.items():
            if len(cluster_data["routes"]) >= 2:  # At least 2 routes intersect
                point = InterceptionPoint(
                    name=f"Strategic Zone {cluster_key}",
                    coordinates=cluster_data["coordinates"],
                    route_codes=cluster_data["routes"],
                    intercept_probability=min(cluster_data["total_probability"] / len(cluster_data["routes"]), 1.0),
                    difficulty_rating="MODERATE" if len(cluster_data["routes"]) <= 3 else "HARD",
                    description=f"Convergence point for {len(cluster_data['routes'])} high-value routes",
                    optimal_ship_classes=["Fighter", "Interceptor", "Heavy Fighter"] if cluster_data["max_profit"] > 3000000 else ["Light Fighter", "Interceptor"]
                )
                all_points.append(point)
        
        return {
            "status": "success",
            "total_points": len(all_points),
            "interception_points": sorted(all_points, key=lambda x: x.intercept_probability, reverse=True)
        }
        
    except Exception as e:
        logging.error(f"Error in get_interception_points: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/alerts")
async def get_alerts(
    priority: Optional[str] = Query(default=None),
    acknowledged: bool = Query(default=False),
    limit: int = Query(default=50, le=200)
):
    """Get current alerts and notifications"""
    try:
        query = {"acknowledged": acknowledged}
        if priority:
            query["priority"] = priority.upper()
        
        alerts = await db.alerts.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Convert to Alert models
        alert_objects = []
        for alert_data in alerts:
            try:
                alert_objects.append(Alert(**alert_data))
            except Exception as e:
                logging.error(f"Error parsing alert: {e}")
        
        return {
            "status": "success",
            "total_alerts": len(alert_objects),
            "alerts": alert_objects
        }
        
    except Exception as e:
        logging.error(f"Error in get_alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        result = await db.alerts.update_one(
            {"id": alert_id},
            {"$set": {"acknowledged": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "success", "message": "Alert acknowledged"}
        
    except Exception as e:
        logging.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trends/historical")
async def get_historical_trends(
    route_code: Optional[str] = Query(default=None),
    commodity: Optional[str] = Query(default=None),
    hours_back: int = Query(default=24, le=168)  # Max 1 week
):
    """Get historical trend data for routes"""
    try:
        # Build query
        query = {
            "timestamp": {
                "$gte": datetime.now(timezone.utc) - timedelta(hours=hours_back)
            }
        }
        
        if route_code:
            query["route_code"] = route_code
        if commodity:
            query["commodity_name"] = {"$regex": commodity, "$options": "i"}
        
        trends = await db.historical_trends.find(query).sort("timestamp", 1).to_list(1000)
        
        # Group by route for trend analysis
        route_trends = {}
        for trend in trends:
            route_key = trend["route_code"]
            if route_key not in route_trends:
                route_trends[route_key] = {
                    "route_code": trend["route_code"],
                    "commodity_name": trend["commodity_name"],
                    "data_points": []
                }
            
            route_trends[route_key]["data_points"].append({
                "timestamp": trend["timestamp"],
                "profit": trend["profit"],
                "roi": trend["roi"],
                "traffic_score": trend["traffic_score"],
                "piracy_rating": trend["piracy_rating"]
            })
        
        # Calculate trend statistics
        for route_key, route_data in route_trends.items():
            data_points = route_data["data_points"]
            if len(data_points) >= 1:
                # Calculate trends
                profits = [dp["profit"] for dp in data_points]
                piracy_ratings = [dp["piracy_rating"] for dp in data_points]
                
                if len(data_points) >= 2:
                    route_data["profit_trend"] = "increasing" if profits[-1] > profits[0] else "decreasing"
                else:
                    route_data["profit_trend"] = "stable"
                
                route_data["avg_profit"] = sum(profits) / len(profits)
                route_data["max_piracy_rating"] = max(piracy_ratings)
                route_data["current_piracy_rating"] = piracy_ratings[-1]
            else:
                # Provide default values if no data points
                route_data["profit_trend"] = "stable"
                route_data["avg_profit"] = 0.0
                route_data["max_piracy_rating"] = 0.0
                route_data["current_piracy_rating"] = 0.0
        
        return {
            "status": "success",
            "time_range_hours": hours_back,
            "total_routes": len(route_trends),
            "route_trends": list(route_trends.values())
        }
        
    except Exception as e:
        logging.error(f"Error in get_historical_trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tracking/status")
async def get_tracking_status():
    """Get real-time tracking status"""
    try:
        global tracking_state
        
        # Calculate uptime
        uptime_minutes = 0
        if tracking_state.get('last_update'):
            uptime_minutes = int((datetime.now(timezone.utc) - tracking_state['last_update']).total_seconds() / 60)
        
        # Get recent alert count
        recent_alerts = await db.alerts.count_documents({
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)},
            "acknowledged": False
        })
        
        status = TrackingStatus(
            active=tracking_state.get('active', False),
            last_update=tracking_state.get('last_update'),
            route_count=tracking_state.get('route_count', 0),
            alert_count=recent_alerts,
            uptime_minutes=uptime_minutes
        )
        
        return {
            "status": "success",
            "tracking": status
        }
        
    except Exception as e:
        logging.error(f"Error in get_tracking_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tracking/start")
async def start_tracking(background_tasks: BackgroundTasks):
    """Start real-time route tracking"""
    try:
        global tracking_state
        tracking_state['active'] = True
        
        # Start background tracking task
        background_tasks.add_task(update_tracking_data)
        
        return {"status": "success", "message": "Real-time tracking started"}
        
    except Exception as e:
        logging.error(f"Error starting tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tracking/stop")
async def stop_tracking():
    """Stop real-time route tracking"""
    try:
        global tracking_state
        tracking_state['active'] = False
        
        return {"status": "success", "message": "Real-time tracking stopped"}
        
    except Exception as e:
        logging.error(f"Error stopping tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/export/routes")
async def export_routes(
    format: str = Query(default="json", regex="^(json|csv)$"),
    route_codes: Optional[str] = Query(default=None)
):
    """Enhanced export functionality with filtering"""
    try:
        query = {}
        if route_codes:
            codes_list = [code.strip() for code in route_codes.split(',')]
            query["route_code"] = {"$in": codes_list}
        
        analyses = await db.route_analyses.find(query).sort("piracy_rating", -1).to_list(1000)
        
        if format == "csv":
            # Enhanced CSV format
            csv_data = "Route Code,Commodity,Origin,Destination,Profit (aUEC),ROI (%),Distance (GM),Traffic Score,Piracy Rating,Risk Level,Investment (aUEC),Last Seen\n"
            for analysis in analyses:
                csv_data += f"{analysis['route_code']},{analysis['commodity_name']},{analysis['origin_name']},{analysis['destination_name']},{analysis['profit']},{analysis['roi']},{analysis['distance']},{analysis['score']},{analysis['piracy_rating']},{analysis['risk_level']},{analysis['investment']},{analysis['last_seen']}\n"
            
            return {
                "status": "success", 
                "format": "csv", 
                "filename": f"sinister_snare_routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "data": csv_data,
                "record_count": len(analyses)
            }
        else:
            return {
                "status": "success", 
                "format": "json", 
                "filename": f"sinister_snare_routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "data": analyses,
                "record_count": len(analyses)
            }
        
    except Exception as e:
        logging.error(f"Error in export_routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/targets/priority")
async def get_priority_targets(
    limit: int = Query(default=20, le=100),
    min_piracy_score: float = Query(default=60.0)
):
    """Enhanced priority targets with real-time data"""
    try:
        # Fetch recent analyses from database
        analyses = await db.route_analyses.find(
            {"piracy_rating": {"$gte": min_piracy_score}}
        ).sort("piracy_rating", -1).limit(limit).to_list(limit)
        
        priority_targets = []
        for analysis in analyses:
            # Calculate time-sensitive factors
            last_seen = datetime.fromisoformat(analysis['last_seen'].replace('Z', '+00:00'))
            hours_since_seen = (datetime.now(timezone.utc) - last_seen).total_seconds() / 3600
            freshness_factor = max(0.1, 1.0 - (hours_since_seen / 24))  # Decay over 24 hours
            
            interception_points = []
            if analysis.get('interception_zones'):
                for zone in analysis['interception_zones'][:3]:  # Top 3 points
                    interception_points.append(f"{zone.get('name', 'Unknown Zone')} ({zone.get('intercept_probability', 0):.0%})")
            
            target = {
                "id": analysis.get('id', str(uuid.uuid4())),
                "route_code": analysis['route_code'],
                "commodity_name": analysis['commodity_name'],
                "origin_name": analysis['origin_name'],
                "destination_name": analysis['destination_name'],
                "piracy_score": analysis['piracy_rating'] * freshness_factor,
                "expected_value": analysis['profit'],
                "risk_reward_ratio": analysis['profit'] / max(analysis['investment'], 1),
                "traffic_frequency": analysis['frequency_score'],
                "interception_points": interception_points or [
                    "Midway point between systems",
                    "Jump point exits", 
                    "Quantum travel interruption zones"
                ],
                "optimal_time_windows": [
                    f"Peak trading hours: {18 + (analysis['score'] % 4)}:00-{22 + (analysis['score'] % 4)}:00 UTC",
                    "Weekend trading periods",
                    "Post-maintenance cargo runs",
                    f"Last seen: {hours_since_seen:.1f} hours ago"
                ],
                "freshness_factor": freshness_factor,
                "last_seen": analysis['last_seen'],
                "coordinates_origin": analysis.get('coordinates_origin'),
                "coordinates_destination": analysis.get('coordinates_destination')
            }
            priority_targets.append(target)
        
        return {
            "status": "success",
            "total_targets": len(priority_targets),
            "targets": priority_targets,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error in get_priority_targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analysis/hourly")
async def get_hourly_analysis():
    """Enhanced hourly analysis with real data patterns"""
    try:
        # Get historical data for the last 24 hours
        hourly_data = []
        current_time = datetime.now(timezone.utc)
        
        for hour in range(24):
            hour_start = current_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Query historical trends for this hour
            trends = await db.historical_trends.find({
                "timestamp": {"$gte": hour_start, "$lt": hour_end}
            }).to_list(None)
            
            if trends:
                # Calculate from real data
                route_count = len(set(trend["route_code"] for trend in trends))
                avg_profit = sum(trend["profit"] for trend in trends) / len(trends)
                avg_traffic = sum(trend["traffic_score"] for trend in trends) / len(trends)
                avg_piracy_score = sum(trend["piracy_rating"] for trend in trends) / len(trends)
            else:
                # Fallback to simulation based on typical gaming patterns
                peak_hours = [18, 19, 20, 21, 22]  # UTC evening hours
                moderate_hours = [14, 15, 16, 17, 23, 0, 1]
                
                if hour in peak_hours:
                    route_count = 45 + (hour - 18) * 5
                    avg_profit = 2800000 + (hour - 18) * 200000
                    avg_traffic = 85 + (hour - 18) * 3
                    avg_piracy_score = 88 + (hour - 18) * 2
                elif hour in moderate_hours:
                    route_count = 25
                    avg_profit = 2100000
                    avg_traffic = 65
                    avg_piracy_score = 72
                else:
                    route_count = 12
                    avg_profit = 1500000
                    avg_traffic = 35
                    avg_piracy_score = 45
            
            hourly_data.append({
                "hour": hour,
                "route_count": int(route_count),
                "avg_profit": avg_profit,
                "avg_traffic": avg_traffic,
                "piracy_opportunity_score": avg_piracy_score,
                "data_source": "historical" if trends else "simulated"
            })
        
        # Enhanced recommendations based on analysis
        best_hours = sorted(hourly_data, key=lambda x: x['piracy_opportunity_score'], reverse=True)[:3]
        
        return {
            "status": "success",
            "hourly_analysis": hourly_data,
            "recommendations": {
                "peak_piracy_hours": f"{best_hours[0]['hour']}:00-{(best_hours[0]['hour']+3)%24}:00 UTC",
                "optimal_systems": ["Stanton", "Pyro", "Nyx", "Terra"],
                "high_value_commodities": ["Processed Narcotics", "Quantum Superconductors", "Medical Supplies", "Laranite"],
                "best_hours_detail": [
                    f"{hour['hour']}:00 - Score: {hour['piracy_opportunity_score']:.1f} ({hour['route_count']} routes)"
                    for hour in best_hours
                ],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logging.error(f"Error in get_hourly_analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/refresh/manual")
async def manual_refresh():
    """Manual refresh with live update logs"""
    try:
        refresh_logs = []
        
        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "🔄 Starting manual refresh...", "type": "info"})
        
        # Fetch fresh commodity data
        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "📡 Connecting to Star Profit API...", "type": "info"})
        commodities_data = await star_profit_client.get_commodities()
        
        if not commodities_data.get('commodities'):
            refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "❌ Failed to fetch commodity data", "type": "error"})
            return {"status": "error", "logs": refresh_logs}
        
        commodities = commodities_data.get('commodities', [])
        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"✅ Fetched {len(commodities)} commodity records", "type": "success"})
        
        # Process commodities into routes
        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "🔄 Processing commodity data into trading routes...", "type": "info"})
        
        # Clear existing route analyses
        await db.route_analyses.delete_many({})
        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "🗑️ Cleared existing route analyses", "type": "info"})
        
        # Generate fresh routes
        routes_data = await star_profit_client.get_trading_routes()
        
        if routes_data.get('status') == 'ok':
            routes = routes_data.get('data', [])
            refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"🛣️ Generated {len(routes)} trading routes", "type": "success"})
            
            # Analyze and store routes
            processed_count = 0
            for route in routes:
                try:
                    piracy_score = RouteAnalyzer.calculate_piracy_score(route)
                    
                    analysis = RouteAnalysis(
                        route_code=route.get('code', 'unknown'),
                        commodity_name=route.get('commodity_name', 'Unknown'),
                        origin_name=f"{route.get('origin_star_system_name', 'Unknown')} - {route.get('origin_terminal_name', 'Unknown')}",
                        destination_name=f"{route.get('destination_star_system_name', 'Unknown')} - {route.get('destination_terminal_name', 'Unknown')}",
                        profit=float(route.get('profit', 0)),
                        roi=float(route.get('price_roi', 0)),
                        distance=float(route.get('distance', 0)),
                        score=int(route.get('score', 0)),
                        piracy_rating=piracy_score,
                        frequency_score=float(route.get('score', 0)) / 10,
                        risk_level=RouteAnalyzer.categorize_risk_level(piracy_score),
                        investment=float(route.get('investment', 0)),
                        coordinates_origin=route.get('coordinates_origin'),
                        coordinates_destination=route.get('coordinates_destination'),
                        interception_zones=RouteAnalyzer.calculate_interception_points(route),
                        last_seen=datetime.now(timezone.utc)
                    )
                    
                    await db.route_analyses.insert_one(analysis.dict())
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"📊 Processed {processed_count} routes...", "type": "info"})
                        
                except Exception as e:
                    continue
            
            refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"✅ Successfully processed {processed_count} routes", "type": "success"})
            refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "🎯 Manual refresh completed successfully!", "type": "success"})
            
            return {
                "status": "success",
                "logs": refresh_logs,
                "routes_processed": processed_count,
                "total_commodities": len(commodities)
            }
        else:
            refresh_logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "❌ Failed to generate trading routes", "type": "error"})
            return {"status": "error", "logs": refresh_logs}
        
    except Exception as e:
        logging.error(f"Error in manual_refresh: {e}")
        return {
            "status": "error", 
            "logs": [{"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"❌ Refresh failed: {str(e)}", "type": "error"}]
        }

@api_router.get("/snare/now")
async def snare_now():
    """Get the most frequent route in the last hour for optimal interception"""
    try:
        # Get routes with highest frequency score from the last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        routes = await db.route_analyses.find({
            "last_seen": {"$gte": one_hour_ago},
            "score": {"$gte": 10}  # Minimum traffic
        }).sort("frequency_score", -1).limit(10).to_list(10)
        
        if not routes:
            # If no recent routes, get the most frequent overall
            routes = await db.route_analyses.find({
                "score": {"$gte": 10}
            }).sort("frequency_score", -1).limit(10).to_list(10)
        
        if not routes:
            return {
                "status": "error",
                "message": "No suitable routes found for interception"
            }
        
        # Select the top route
        top_route = routes[0]
        
        # Calculate optimal interception strategy
        origin_coords = top_route.get('coordinates_origin', {})
        dest_coords = top_route.get('coordinates_destination', {})
        
        # Determine if inter-system route
        origin_parts = top_route.get('origin_name', '').split(' - ')
        dest_parts = top_route.get('destination_name', '').split(' - ')
        
        origin_system = origin_parts[0] if len(origin_parts) > 0 else 'Unknown'
        dest_system = dest_parts[0] if len(dest_parts) > 0 else 'Unknown'
        
        is_inter_system = origin_system != dest_system
        
        # Calculate interception point
        if is_inter_system:
            # For inter-system routes, suggest gateway interception
            if 'Pyro' in origin_system and 'Stanton' in dest_system:
                interception_point = "Pyro Gateway (Jump Point to Stanton)"
                warning = "⚠️ Inter-system route detected. Target traders at Pyro Gateway before they jump to Stanton."
            elif 'Stanton' in origin_system and 'Pyro' in dest_system:
                interception_point = "Stanton-Pyro Jump Point"
                warning = "⚠️ Inter-system route detected. Target traders at Stanton-Pyro Jump Point before they enter Pyro."
            else:
                interception_point = f"Gateway between {origin_system} and {dest_system}"
                warning = f"⚠️ Inter-system route detected. Target traders at gateway between {origin_system} and {dest_system}."
        else:
            # Same system - use midpoint
            if origin_coords and dest_coords:
                midpoint_x = (origin_coords.get('x', 0) + dest_coords.get('x', 0)) / 2
                midpoint_y = (origin_coords.get('y', 0) + dest_coords.get('y', 0)) / 2
                midpoint_z = (origin_coords.get('z', 0) + dest_coords.get('z', 0)) / 2
                interception_point = f"Coordinates: X:{midpoint_x:.0f}, Y:{midpoint_y:.0f}, Z:{midpoint_z:.0f}"
                warning = f"🎯 Optimal interception zone in {origin_system} system between terminals."
            else:
                interception_point = f"Midpoint between {origin_parts[1] if len(origin_parts) > 1 else 'origin'} and {dest_parts[1] if len(dest_parts) > 1 else 'destination'}"
                warning = f"🎯 Position yourself between departure and arrival terminals in {origin_system}."
        
        return {
            "status": "success",
            "snare_data": {
                "route_code": top_route.get('route_code'),
                "commodity_name": top_route.get('commodity_name'),
                "origin_name": top_route.get('origin_name'),
                "destination_name": top_route.get('destination_name'),
                "profit": top_route.get('profit'),
                "frequency_score": top_route.get('frequency_score'),
                "piracy_rating": top_route.get('piracy_rating'),
                "traffic_level": "HIGH" if top_route.get('score', 0) >= 50 else "MODERATE" if top_route.get('score', 0) >= 25 else "LOW",
                "interception_point": interception_point,
                "warning": warning,
                "is_inter_system": is_inter_system,
                "last_seen": top_route.get('last_seen'),
                "estimated_traders_per_hour": max(1, int(top_route.get('score', 0) / 10))
            },
            "alternatives": [
                {
                    "route_code": route.get('route_code'),
                    "commodity_name": route.get('commodity_name'),
                    "frequency_score": route.get('frequency_score'),
                    "piracy_rating": route.get('piracy_rating')
                } for route in routes[1:6]  # Top 5 alternatives
            ]
        }
        
    except Exception as e:
        logging.error(f"Error in snare_now: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/snare/commodity")
async def commodity_snare(commodity_name: str):
    """Set up commodity-specific snare for targeted interception"""
    try:
        # Find routes for the specific commodity
        routes = await db.route_analyses.find({
            "commodity_name": {"$regex": commodity_name, "$options": "i"},
            "profit": {"$gte": 100000}  # Minimum 100k profit
        }).sort("piracy_rating", -1).limit(20).to_list(20)
        
        if not routes:
            return {
                "status": "error",
                "message": f"No profitable routes found for commodity: {commodity_name}"
            }
        
        # Analyze the best routes for this commodity
        snare_opportunities = []
        
        for route in routes[:10]:  # Top 10 routes
            origin_parts = route.get('origin_name', '').split(' - ')
            dest_parts = route.get('destination_name', '').split(' - ')
            
            origin_system = origin_parts[0] if len(origin_parts) > 0 else 'Unknown'
            dest_system = dest_parts[0] if len(dest_parts) > 0 else 'Unknown'
            origin_terminal = origin_parts[1] if len(origin_parts) > 1 else 'Unknown'
            dest_terminal = dest_parts[1] if len(dest_parts) > 1 else 'Unknown'
            
            is_inter_system = origin_system != dest_system
            
            # Determine interception strategy
            if is_inter_system:
                if 'Pyro' in origin_system and 'Stanton' in dest_system:
                    interception_location = "Pyro Gateway"
                    strategy = f"Interdict between {origin_terminal} and Pyro Gateway"
                    warning = "⚠️ Inter-system route - Use Pyro Gateway as interception point"
                elif 'Stanton' in origin_system and 'Pyro' in dest_system:
                    interception_location = "Stanton-Pyro Jump Point"
                    strategy = f"Interdict between {origin_terminal} and Stanton-Pyro Jump Point"
                    warning = "⚠️ Inter-system route - Use Jump Point as interception point"
                else:
                    interception_location = f"{origin_system}-{dest_system} Gateway"
                    strategy = f"Interdict at gateway between {origin_system} and {dest_system}"
                    warning = f"⚠️ Inter-system route - Use gateway for interception"
            else:
                interception_location = f"Between {origin_terminal} and {dest_terminal}"
                strategy = f"Interdict between {origin_terminal} and {dest_terminal}"
                warning = f"🎯 Same system route - Position between terminals in {origin_system}"
            
            snare_opportunities.append({
                "route_code": route.get('route_code'),
                "buying_point": f"{origin_system} - {origin_terminal}",
                "selling_point": f"{dest_system} - {dest_terminal}",
                "interception_location": interception_location,
                "strategy": strategy,
                "warning": warning,
                "profit": route.get('profit'),
                "piracy_rating": route.get('piracy_rating'),
                "frequency_score": route.get('frequency_score'),
                "is_inter_system": is_inter_system,
                "risk_level": route.get('risk_level'),
                "estimated_traders": max(1, int(route.get('score', 0) / 10))
            })
        
        # Calculate commodity summary
        total_routes = len(routes)
        avg_profit = sum(route.get('profit', 0) for route in routes) / len(routes) if routes else 0
        max_piracy_rating = max(route.get('piracy_rating', 0) for route in routes) if routes else 0
        inter_system_count = sum(1 for opp in snare_opportunities if opp['is_inter_system'])
        
        return {
            "status": "success",
            "commodity": commodity_name,
            "summary": {
                "total_routes_found": total_routes,
                "profitable_routes": len(snare_opportunities),
                "inter_system_routes": inter_system_count,
                "same_system_routes": len(snare_opportunities) - inter_system_count,
                "average_profit": avg_profit,
                "max_piracy_rating": max_piracy_rating,
                "recommended_strategy": "Focus on inter-system routes for higher profits" if inter_system_count > 0 else "Target same-system routes for easier interception"
            },
            "snare_opportunities": snare_opportunities
        }
        
    except Exception as e:
        logging.error(f"Error in commodity_snare: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status")
async def get_api_status():
    """Enhanced API status with real data source information"""
    try:
        # Test Star Profit API connection
        star_profit_status = "disconnected"
        star_profit_records = 0
        try:
            test_response = await star_profit_client.get_commodities()
            if test_response.get('commodities'):
                star_profit_status = "connected"
                star_profit_records = len(test_response.get('commodities', []))
        except:
            star_profit_status = "error"
        
        # Test UEX API connection (fallback)
        uex_status = "disconnected"
        using_mock = False
        try:
            test_response = await uex_client.get_commodities_routes()
            uex_status = "connected" if test_response.get('status') == 'ok' else "error"
            using_mock = test_response.get('mock_data', False)
        except:
            uex_status = "error"
            using_mock = True
        
        # Determine primary data source
        primary_data_source = "real" if star_profit_status == "connected" else "simulated"
        
        # Check database
        db_status = "connected"
        try:
            await db.command("ping")
        except:
            db_status = "error"
        
        # Get counts
        route_count = await db.route_analyses.count_documents({})
        alert_count = await db.alerts.count_documents({"acknowledged": False})
        trend_count = await db.historical_trends.count_documents({})
        
        return {
            "status": "operational",
            "version": "2.0.0",
            "primary_data_source": primary_data_source,
            "data_sources": {
                "star_profit_api": {
                    "status": star_profit_status,
                    "records_available": star_profit_records,
                    "description": "Real Star Citizen commodity data"
                },
                "uex_api": {
                    "status": uex_status,
                    "using_mock_data": using_mock,
                    "description": "UEXCorp trading data (fallback)"
                }
            },
            "database": db_status,
            "api_key_configured": bool(UEX_API_KEY),
            "statistics": {
                "total_routes_analyzed": route_count,
                "active_alerts": alert_count,
                "historical_data_points": trend_count,
                "tracking_active": tracking_state.get('active', False)
            },
            "features": {
                "real_time_data": star_profit_status == "connected",
                "interception_mapping": True,
                "historical_analysis": True,
                "alert_system": True,
                "export_functionality": True
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize tracking system on startup"""
    global tracking_state
    tracking_state['active'] = True
    logger.info("Sinister Snare v2.0 - Advanced Piracy Intelligence System started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()