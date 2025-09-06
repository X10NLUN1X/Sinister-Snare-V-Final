from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import asyncio
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# UEXCorp API Configuration
UEX_API_BASE = "https://uexcorp.space/2.0"
UEX_API_KEY = os.environ.get('UEX_API_KEY', '')

# Create the main app without a prefix
app = FastAPI(title="Sinister Snare - Star Citizen Piracy Intelligence", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# UEX API Client
class UEXClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = UEX_API_BASE
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_commodities_routes(self, **params) -> Dict[str, Any]:
        """Fetch trading routes from UEX API"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/commodities_routes",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"UEX API Error: {e}")
                raise HTTPException(status_code=500, detail=f"UEX API Error: {str(e)}")
    
    async def get_terminals(self) -> Dict[str, Any]:
        """Fetch terminal/location data"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/terminals",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"UEX API Error: {e}")
                raise HTTPException(status_code=500, detail=f"UEX API Error: {str(e)}")

# Initialize UEX client
uex_client = UEXClient(UEX_API_KEY)

# Models
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
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PiracyTarget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    route_code: str
    commodity_name: str
    origin_name: str
    destination_name: str
    piracy_score: float
    expected_value: float
    risk_reward_ratio: float
    traffic_frequency: float
    interception_points: List[str]
    optimal_time_windows: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimeBasedAnalysis(BaseModel):
    hour: int
    route_count: int
    avg_profit: float
    avg_traffic: float
    piracy_opportunity_score: float

# Route Analysis Engine
class RouteAnalyzer:
    @staticmethod
    def calculate_piracy_score(route_data: Dict[str, Any]) -> float:
        """Calculate piracy potential score for a route"""
        try:
            # Base factors
            profit = float(route_data.get('profit', 0))
            investment = float(route_data.get('investment', 1))
            distance = float(route_data.get('distance', 1))
            score = int(route_data.get('score', 0))
            roi = float(route_data.get('price_roi', 0))
            
            # Piracy score calculation
            # High profit, high traffic (score), reasonable distance
            profit_factor = min(profit / 1000000, 1.0)  # Normalize to max 1M profit
            traffic_factor = min(score / 100, 1.0)      # Normalize score
            distance_factor = max(0, 1 - (distance / 50000))  # Prefer shorter routes
            roi_factor = min(roi / 100, 1.0)           # ROI factor
            
            piracy_score = (
                profit_factor * 0.4 +      # High value cargo
                traffic_factor * 0.3 +     # High traffic routes
                distance_factor * 0.2 +    # Reasonable distance
                roi_factor * 0.1           # Good ROI
            ) * 100
            
            return round(piracy_score, 2)
        except Exception as e:
            logging.error(f"Error calculating piracy score: {e}")
            return 0.0
    
    @staticmethod
    def categorize_risk_level(piracy_score: float) -> str:
        """Categorize risk level based on piracy score"""
        if piracy_score >= 80:
            return "ELITE"
        elif piracy_score >= 60:
            return "HIGH"
        elif piracy_score >= 40:
            return "MODERATE"
        else:
            return "LOW"

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Sinister Snare - Star Citizen Piracy Intelligence System"}

@api_router.get("/routes/analyze")
async def analyze_routes(
    limit: int = Query(default=50, le=500),
    min_profit: Optional[float] = Query(default=None),
    min_score: Optional[int] = Query(default=None)
):
    """Analyze trading routes and identify piracy opportunities"""
    try:
        # Fetch routes from UEX API
        params = {}
        if min_profit:
            params['investment'] = int(min_profit)
        
        routes_data = await uex_client.get_commodities_routes(**params)
        
        if routes_data.get('status') != 'ok':
            raise HTTPException(status_code=400, detail="Failed to fetch routes from UEX API")
        
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
                    frequency_score=float(route.get('score', 0)) / 10,  # Normalize frequency
                    risk_level=RouteAnalyzer.categorize_risk_level(piracy_score),
                    investment=float(route.get('investment', 0))
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
        
        return {
            "status": "success",
            "total_routes": len(analyzed_routes),
            "routes": analyzed_routes
        }
        
    except Exception as e:
        logging.error(f"Error in analyze_routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/targets/priority")
async def get_priority_targets(limit: int = Query(default=20, le=100)):
    """Get top priority piracy targets"""
    try:
        # Fetch recent analyses from database
        analyses = await db.route_analyses.find(
            {"piracy_rating": {"$gte": 40}}
        ).sort("piracy_rating", -1).limit(limit).to_list(limit)
        
        priority_targets = []
        for analysis in analyses:
            target = PiracyTarget(
                route_code=analysis['route_code'],
                commodity_name=analysis['commodity_name'],
                origin_name=analysis['origin_name'],
                destination_name=analysis['destination_name'],
                piracy_score=analysis['piracy_rating'],
                expected_value=analysis['profit'],
                risk_reward_ratio=analysis['profit'] / max(analysis['investment'], 1),
                traffic_frequency=analysis['frequency_score'],
                interception_points=[
                    "Midway point between systems",
                    "Jump point exits",
                    "Quantum travel interruption zones"
                ],
                optimal_time_windows=[
                    "Peak trading hours: 18:00-22:00 UTC",
                    "Weekend trading periods",
                    "Post-patch cargo runs"
                ]
            )
            priority_targets.append(target)
        
        return {
            "status": "success",
            "total_targets": len(priority_targets),
            "targets": priority_targets
        }
        
    except Exception as e:
        logging.error(f"Error in get_priority_targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analysis/hourly")
async def get_hourly_analysis():
    """Get time-based route analysis for optimal piracy timing"""
    try:
        # This would ideally use historical data
        # For now, we'll provide a simulated hourly analysis
        hourly_data = []
        
        # Simulate peak trading hours based on typical gaming patterns
        peak_hours = [18, 19, 20, 21, 22]  # UTC evening hours
        moderate_hours = [14, 15, 16, 17, 23, 0]
        
        for hour in range(24):
            if hour in peak_hours:
                route_count = 45 + (hour - 18) * 3
                avg_profit = 2500000 + (hour - 18) * 100000
                piracy_score = 85 + (hour - 18) * 2
            elif hour in moderate_hours:
                route_count = 25
                avg_profit = 1800000
                piracy_score = 65
            else:
                route_count = 10
                avg_profit = 1200000
                piracy_score = 35
            
            hourly_data.append(TimeBasedAnalysis(
                hour=hour,
                route_count=route_count,
                avg_profit=avg_profit,
                avg_traffic=route_count * 2.5,
                piracy_opportunity_score=piracy_score
            ))
        
        return {
            "status": "success",
            "hourly_analysis": hourly_data,
            "recommendations": {
                "peak_piracy_hours": "18:00-22:00 UTC",
                "optimal_systems": ["Stanton", "Pyro", "Nyx"],
                "high_value_commodities": ["Laranite", "Titanium", "Medical Supplies"]
            }
        }
        
    except Exception as e:
        logging.error(f"Error in get_hourly_analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/export/routes")
async def export_routes(format: str = Query(default="json", regex="^(json|csv)$")):
    """Export route analysis data"""
    try:
        analyses = await db.route_analyses.find().sort("piracy_rating", -1).to_list(1000)
        
        if format == "csv":
            # Convert to CSV format
            csv_data = "Route Code,Commodity,Origin,Destination,Profit,ROI,Distance,Score,Piracy Rating,Risk Level\n"
            for analysis in analyses:
                csv_data += f"{analysis['route_code']},{analysis['commodity_name']},{analysis['origin_name']},{analysis['destination_name']},{analysis['profit']},{analysis['roi']},{analysis['distance']},{analysis['score']},{analysis['piracy_rating']},{analysis['risk_level']}\n"
            
            return {"status": "success", "format": "csv", "data": csv_data}
        else:
            return {"status": "success", "format": "json", "data": analyses}
        
    except Exception as e:
        logging.error(f"Error in export_routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/status")
async def get_api_status():
    """Check API and UEX connection status"""
    try:
        # Test UEX API connection
        test_response = await uex_client.get_commodities_routes()
        uex_status = "connected" if test_response.get('status') == 'ok' else "error"
        
        # Check database
        db_status = "connected"
        try:
            await db.command("ping")
        except:
            db_status = "error"
        
        return {
            "status": "operational",
            "uex_api": uex_status,
            "database": db_status,
            "api_key_configured": bool(UEX_API_KEY),
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()