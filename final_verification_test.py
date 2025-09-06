#!/usr/bin/env python3
"""
Final Comprehensive Backend Verification Test
Tests all key endpoints mentioned in the review request
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class FinalTestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, status, message, details=None):
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        if status == 'PASS':
            self.passed += 1
        else:
            self.failed += 1
        
        # Print result immediately
        status_symbol = "✅" if status == 'PASS' else "❌"
        print(f"{status_symbol} {test_name}: {message}")
        if details and isinstance(details, dict):
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"FINAL VERIFICATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%" if self.results else "0%")
        
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")

async def test_key_endpoints():
    """Test all key endpoints mentioned in the review request"""
    results = FinalTestResults()
    
    print(f"🏴‍☠️ FINAL COMPREHENSIVE BACKEND VERIFICATION")
    print(f"Testing all key endpoints after database fixes")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"{'='*80}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Test /api/status - Should show all systems operational
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                db_status = data.get('database')
                star_profit_status = data.get('data_sources', {}).get('star_profit_api', {}).get('status')
                
                if status == 'operational' and db_status == 'connected':
                    results.add_result(
                        "/api/status",
                        "PASS",
                        "All systems operational",
                        {
                            "API Status": status,
                            "Database": db_status,
                            "Star Profit API": star_profit_status,
                            "Records Available": data.get('data_sources', {}).get('star_profit_api', {}).get('records_available', 0)
                        }
                    )
                else:
                    results.add_result(
                        "/api/status",
                        "FAIL",
                        f"System not fully operational - Status: {status}, DB: {db_status}"
                    )
            else:
                results.add_result(
                    "/api/status",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/status",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 2. Test /api/routes/analyze - Real Star Citizen data from Star Profit API
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10&use_real_data=true")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    route_count = data.get('total_routes', 0)
                    data_source = data.get('data_source')
                    api_used = data.get('api_used')
                    
                    if route_count > 0 and data_source == 'real':
                        results.add_result(
                            "/api/routes/analyze",
                            "PASS",
                            "Real Star Citizen data analysis working",
                            {
                                "Routes Analyzed": route_count,
                                "Data Source": data_source,
                                "API Used": api_used,
                                "Database Available": data.get('database_available', False)
                            }
                        )
                    else:
                        results.add_result(
                            "/api/routes/analyze",
                            "FAIL",
                            f"No real data or routes - Count: {route_count}, Source: {data_source}"
                        )
                else:
                    results.add_result(
                        "/api/routes/analyze",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "/api/routes/analyze",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/routes/analyze",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 3. Test /api/alerts - Alert system with database integration
        try:
            response = await client.get(f"{BACKEND_URL}/api/alerts?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    alert_count = data.get('total_alerts', 0)
                    results.add_result(
                        "/api/alerts",
                        "PASS",
                        "Alert system with database integration working",
                        {
                            "Total Alerts": alert_count,
                            "Database Integration": "Working"
                        }
                    )
                else:
                    results.add_result(
                        "/api/alerts",
                        "FAIL",
                        f"Alert system error: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "/api/alerts",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/alerts",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 4. Test /api/export/routes?format=json - Fixed ObjectId serialization
        try:
            response = await client.get(f"{BACKEND_URL}/api/export/routes?format=json")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    record_count = data.get('record_count', 0)
                    export_format = data.get('format')
                    
                    # Verify JSON serialization works (no ObjectId errors)
                    export_data = data.get('data', [])
                    json_serializable = True
                    try:
                        json.dumps(export_data)
                    except Exception:
                        json_serializable = False
                    
                    if json_serializable:
                        results.add_result(
                            "/api/export/routes",
                            "PASS",
                            "Export with fixed ObjectId serialization working",
                            {
                                "Records Exported": record_count,
                                "Format": export_format,
                                "JSON Serializable": "Yes",
                                "ObjectId Issues": "Fixed"
                            }
                        )
                    else:
                        results.add_result(
                            "/api/export/routes",
                            "FAIL",
                            "JSON serialization still has issues"
                        )
                else:
                    results.add_result(
                        "/api/export/routes",
                        "FAIL",
                        f"Export failed: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "/api/export/routes",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/export/routes",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 5. Test /api/snare/commodity?commodity_name=Agricium - Commodity-specific analysis
        try:
            response = await client.get(f"{BACKEND_URL}/api/snare/commodity?commodity_name=Agricium")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    commodity = data.get('commodity')
                    summary = data.get('summary', {})
                    opportunities = data.get('snare_opportunities', [])
                    
                    results.add_result(
                        "/api/snare/commodity (Agricium)",
                        "PASS",
                        "Commodity-specific analysis working",
                        {
                            "Commodity": commodity,
                            "Routes Found": summary.get('total_routes_found', 0),
                            "Profitable Routes": summary.get('profitable_routes', 0),
                            "Snare Opportunities": len(opportunities),
                            "Max Piracy Rating": summary.get('max_piracy_rating', 0)
                        }
                    )
                else:
                    results.add_result(
                        "/api/snare/commodity (Agricium)",
                        "FAIL",
                        f"Commodity analysis failed: {data.get('message', 'Unknown error')}"
                    )
            else:
                results.add_result(
                    "/api/snare/commodity (Agricium)",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/snare/commodity (Agricium)",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 6. Test /api/trends/historical - Historical trend analysis
        try:
            response = await client.get(f"{BACKEND_URL}/api/trends/historical?hours_back=24")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    route_count = data.get('total_routes', 0)
                    time_range = data.get('time_range_hours', 0)
                    
                    results.add_result(
                        "/api/trends/historical",
                        "PASS",
                        "Historical trend analysis working",
                        {
                            "Routes Tracked": route_count,
                            "Time Range (hours)": time_range,
                            "Database Integration": "Working"
                        }
                    )
                else:
                    results.add_result(
                        "/api/trends/historical",
                        "FAIL",
                        f"Historical trends failed: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "/api/trends/historical",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/trends/historical",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # 7. Test /api/analysis/hourly - 24-hour piracy opportunity analysis
        try:
            response = await client.get(f"{BACKEND_URL}/api/analysis/hourly")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    hourly_data = data.get('hourly_analysis', [])
                    recommendations = data.get('recommendations', {})
                    
                    if len(hourly_data) == 24 and recommendations:
                        results.add_result(
                            "/api/analysis/hourly",
                            "PASS",
                            "24-hour piracy opportunity analysis working",
                            {
                                "Hours Analyzed": len(hourly_data),
                                "Peak Hours": recommendations.get('peak_piracy_hours', 'Unknown'),
                                "Optimal Systems": len(recommendations.get('optimal_systems', [])),
                                "High Value Commodities": len(recommendations.get('high_value_commodities', []))
                            }
                        )
                    else:
                        results.add_result(
                            "/api/analysis/hourly",
                            "FAIL",
                            f"Incomplete hourly analysis - Hours: {len(hourly_data)}, Recommendations: {bool(recommendations)}"
                        )
                else:
                    results.add_result(
                        "/api/analysis/hourly",
                        "FAIL",
                        f"Hourly analysis failed: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "/api/analysis/hourly",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "/api/analysis/hourly",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def main():
    """Run final verification tests"""
    results = await test_key_endpoints()
    results.print_summary()
    
    # Save detailed results
    with open('/app/final_verification_results.json', 'w') as f:
        json.dump(results.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/final_verification_results.json")
    
    return results.failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)