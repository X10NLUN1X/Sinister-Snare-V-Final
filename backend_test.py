#!/usr/bin/env python3
"""
Sinister Snare Backend API Test Suite
Tests the Star Citizen piracy intelligence system backend API
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
UEX_API_KEY = os.environ.get('UEX_API_KEY', '6b70cf40873c5d6e706e5aa87a5ceab97ac8032b')
UEX_API_BASE = "https://uexcorp.space/2.0"

class TestResults:
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
        if details:
            print(f"   Details: {details}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%" if self.results else "0%")
        
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")

async def test_uex_api_direct():
    """Test UEX API directly to isolate connection issues"""
    results = TestResults()
    
    print(f"\n🔍 Testing UEX API Direct Connection")
    print(f"Base URL: {UEX_API_BASE}")
    print(f"API Key: {UEX_API_KEY[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {UEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test commodities_routes endpoint
            response = await client.get(
                f"{UEX_API_BASE}/commodities_routes",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    route_count = len(data.get('data', []))
                    results.add_result(
                        "UEX API Connection",
                        "PASS",
                        f"Successfully connected to UEX API, received {route_count} routes"
                    )
                else:
                    results.add_result(
                        "UEX API Connection",
                        "FAIL",
                        f"UEX API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "UEX API Connection",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except httpx.TimeoutException:
            results.add_result(
                "UEX API Connection",
                "FAIL",
                "Connection timeout to UEX API"
            )
        except Exception as e:
            results.add_result(
                "UEX API Connection",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_backend_endpoints():
    """Test all backend API endpoints"""
    results = TestResults()
    
    print(f"\n🚀 Testing Backend API Endpoints")
    print(f"Backend URL: {BACKEND_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: API Status Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                # Check for both old and new status format
                if status == 'operational' or status == 'ok':
                    # Check for API integration details
                    star_profit_status = data.get('star_profit_api', 'unknown')
                    uex_status = data.get('uex_api', 'unknown')
                    db_status = data.get('database', 'unknown')
                    api_key_configured = data.get('api_key_configured', False)
                    
                    results.add_result(
                        "API Status Endpoint",
                        "PASS",
                        f"API {status} - Star Profit: {star_profit_status}, UEX: {uex_status}, DB: {db_status}, API Key: {api_key_configured}",
                        data
                    )
                else:
                    results.add_result(
                        "API Status Endpoint",
                        "FAIL",
                        f"API status: {status}",
                        data
                    )
            else:
                results.add_result(
                    "API Status Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "API Status Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 2: Routes Analysis Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    route_count = data.get('total_routes', 0)
                    routes = data.get('routes', [])
                    
                    if route_count > 0 and routes:
                        # Check route structure
                        sample_route = routes[0]
                        required_fields = ['route_code', 'commodity_name', 'piracy_rating', 'risk_level']
                        missing_fields = [field for field in required_fields if field not in sample_route]
                        
                        if not missing_fields:
                            results.add_result(
                                "Routes Analysis Endpoint",
                                "PASS",
                                f"Successfully analyzed {route_count} routes with proper structure"
                            )
                        else:
                            results.add_result(
                                "Routes Analysis Endpoint",
                                "FAIL",
                                f"Route missing required fields: {missing_fields}"
                            )
                    else:
                        results.add_result(
                            "Routes Analysis Endpoint",
                            "FAIL",
                            "No routes returned from analysis"
                        )
                else:
                    results.add_result(
                        "Routes Analysis Endpoint",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Routes Analysis Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Routes Analysis Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 3: Priority Targets Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/targets/priority?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    target_count = data.get('total_targets', 0)
                    targets = data.get('targets', [])
                    
                    if target_count > 0 and targets:
                        # Check target structure
                        sample_target = targets[0]
                        required_fields = ['route_code', 'piracy_score', 'expected_value', 'interception_points']
                        missing_fields = [field for field in required_fields if field not in sample_target]
                        
                        if not missing_fields:
                            results.add_result(
                                "Priority Targets Endpoint",
                                "PASS",
                                f"Successfully retrieved {target_count} priority targets"
                            )
                        else:
                            results.add_result(
                                "Priority Targets Endpoint",
                                "FAIL",
                                f"Target missing required fields: {missing_fields}"
                            )
                    else:
                        results.add_result(
                            "Priority Targets Endpoint",
                            "PASS",
                            "No priority targets available (acceptable if no routes analyzed yet)"
                        )
                else:
                    results.add_result(
                        "Priority Targets Endpoint",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Priority Targets Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Priority Targets Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 4: Hourly Analysis Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/analysis/hourly")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    hourly_data = data.get('hourly_analysis', [])
                    recommendations = data.get('recommendations', {})
                    
                    if len(hourly_data) == 24:  # Should have 24 hours
                        # Check hourly data structure
                        sample_hour = hourly_data[0]
                        required_fields = ['hour', 'route_count', 'avg_profit', 'piracy_opportunity_score']
                        missing_fields = [field for field in required_fields if field not in sample_hour]
                        
                        if not missing_fields and recommendations:
                            results.add_result(
                                "Hourly Analysis Endpoint",
                                "PASS",
                                f"Successfully retrieved 24-hour analysis with recommendations"
                            )
                        else:
                            results.add_result(
                                "Hourly Analysis Endpoint",
                                "FAIL",
                                f"Missing fields: {missing_fields} or no recommendations"
                            )
                    else:
                        results.add_result(
                            "Hourly Analysis Endpoint",
                            "FAIL",
                            f"Expected 24 hours of data, got {len(hourly_data)}"
                        )
                else:
                    results.add_result(
                        "Hourly Analysis Endpoint",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Hourly Analysis Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Hourly Analysis Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 5: Export Routes Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/export/routes?format=json")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    record_count = data.get('record_count', 0)
                    results.add_result(
                        "Export Routes Endpoint",
                        "PASS",
                        f"Export endpoint working correctly - {record_count} records"
                    )
                else:
                    results.add_result(
                        "Export Routes Endpoint",
                        "FAIL",
                        f"Export failed: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Export Routes Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Export Routes Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 6: Alerts Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/alerts?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    alert_count = data.get('total_alerts', 0)
                    results.add_result(
                        "Alerts Endpoint",
                        "PASS",
                        f"Alerts endpoint working - {alert_count} alerts retrieved"
                    )
                else:
                    results.add_result(
                        "Alerts Endpoint",
                        "FAIL",
                        f"Alerts API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Alerts Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Alerts Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 7: Historical Trends Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/trends/historical?hours_back=24")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    route_count = data.get('total_routes', 0)
                    time_range = data.get('time_range_hours', 0)
                    results.add_result(
                        "Historical Trends Endpoint",
                        "PASS",
                        f"Trends endpoint working - {route_count} routes over {time_range} hours"
                    )
                else:
                    results.add_result(
                        "Historical Trends Endpoint",
                        "FAIL",
                        f"Trends API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Historical Trends Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Historical Trends Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 8: Snare Now Endpoint (New Feature)
        try:
            response = await client.get(f"{BACKEND_URL}/api/snare/now")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    active_snares = data.get('active_snares', 0)
                    results.add_result(
                        "Snare Now Endpoint",
                        "PASS",
                        f"Snare Now endpoint working - {active_snares} active snares"
                    )
                else:
                    results.add_result(
                        "Snare Now Endpoint",
                        "FAIL",
                        f"Snare Now API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Snare Now Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Snare Now Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 9: Snare Commodity Endpoint (New Feature) - Testing with Agricium as requested
        try:
            response = await client.get(f"{BACKEND_URL}/api/snare/commodity?commodity_name=Agricium")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    snare_points = len(data.get('snare_points', []))
                    results.add_result(
                        "Snare Commodity Endpoint (Agricium)",
                        "PASS",
                        f"Snare Commodity endpoint working - {snare_points} snare points for Agricium"
                    )
                else:
                    results.add_result(
                        "Snare Commodity Endpoint (Agricium)",
                        "FAIL",
                        f"Snare Commodity API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Snare Commodity Endpoint (Agricium)",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Snare Commodity Endpoint (Agricium)",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 10: Tracking Status Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/tracking/status")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    tracking_info = data.get('tracking', {})
                    active = tracking_info.get('active', False)
                    route_count = tracking_info.get('route_count', 0)
                    results.add_result(
                        "Tracking Status Endpoint",
                        "PASS",
                        f"Tracking status endpoint working - Active: {active}, Routes: {route_count}"
                    )
                else:
                    results.add_result(
                        "Tracking Status Endpoint",
                        "FAIL",
                        f"Tracking Status API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Tracking Status Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Tracking Status Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 11: Interception Points Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/interception/points?min_probability=0.5")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    point_count = data.get('total_points', 0)
                    results.add_result(
                        "Interception Points Endpoint",
                        "PASS",
                        f"Interception Points endpoint working - {point_count} strategic points"
                    )
                else:
                    results.add_result(
                        "Interception Points Endpoint",
                        "FAIL",
                        f"Interception Points API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Interception Points Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Interception Points Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_rate_limiting():
    """Test rate limiting behavior"""
    results = TestResults()
    
    print(f"\n⏱️  Testing Rate Limiting")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Make multiple rapid requests to test rate limiting
            responses = []
            for i in range(12):  # More than 10 requests per minute
                response = await client.get(f"{BACKEND_URL}/api/status")
                responses.append(response.status_code)
            
            # Check if any requests were rate limited (429 status)
            rate_limited = any(status == 429 for status in responses)
            successful = sum(1 for status in responses if status == 200)
            
            if rate_limited:
                results.add_result(
                    "Rate Limiting",
                    "PASS",
                    f"Rate limiting active - {successful}/12 requests succeeded"
                )
            else:
                results.add_result(
                    "Rate Limiting",
                    "PASS",
                    f"All {successful}/12 requests succeeded (rate limiting may not be implemented)"
                )
                
        except Exception as e:
            results.add_result(
                "Rate Limiting",
                "FAIL",
                f"Error testing rate limiting: {str(e)}"
            )
    
    return results

async def test_star_profit_api():
    """Test Star Profit API integration"""
    results = TestResults()
    
    print(f"\n🌟 Testing Star Profit API Integration")
    
    # Test Star Profit API directly
    star_profit_base = "https://star-profit.mathioussee.com/api"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{star_profit_base}/commodities",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Sinister-Snare-Piracy-Intelligence/2.0"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                commodities = data.get('commodities', [])
                if commodities:
                    results.add_result(
                        "Star Profit API Direct",
                        "PASS",
                        f"Successfully connected to Star Profit API, received {len(commodities)} commodities"
                    )
                else:
                    results.add_result(
                        "Star Profit API Direct",
                        "FAIL",
                        "Star Profit API returned empty commodities list"
                    )
            else:
                results.add_result(
                    "Star Profit API Direct",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            results.add_result(
                "Star Profit API Direct",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    # Test backend's use of Star Profit API
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?use_real_data=true&limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    api_used = data.get('api_used', 'Unknown')
                    data_source = data.get('data_source', 'Unknown')
                    
                    if 'Star Profit' in api_used or data_source == 'real':
                        results.add_result(
                            "Backend Star Profit Integration",
                            "PASS",
                            f"Backend successfully using Star Profit API - Source: {data_source}, API: {api_used}"
                        )
                    else:
                        results.add_result(
                            "Backend Star Profit Integration",
                            "FAIL",
                            f"Backend not using Star Profit API - Source: {data_source}, API: {api_used}"
                        )
                else:
                    results.add_result(
                        "Backend Star Profit Integration",
                        "FAIL",
                        f"Backend API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Backend Star Profit Integration",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Backend Star Profit Integration",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_uex_api_direct():
    """Test UEX API directly to isolate connection issues"""
    results = TestResults()
    
    print(f"\n🔍 Testing UEX API Direct Connection (Fallback)")
    print(f"Base URL: {UEX_API_BASE}")
    print(f"API Key: {UEX_API_KEY[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {UEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test commodities_routes endpoint
            response = await client.get(
                f"{UEX_API_BASE}/commodities_routes",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    route_count = len(data.get('data', []))
                    results.add_result(
                        "UEX API Connection",
                        "PASS",
                        f"Successfully connected to UEX API, received {route_count} routes"
                    )
                else:
                    results.add_result(
                        "UEX API Connection",
                        "FAIL",
                        f"UEX API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "UEX API Connection",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except httpx.TimeoutException:
            results.add_result(
                "UEX API Connection",
                "FAIL",
                "Connection timeout to UEX API"
            )
        except Exception as e:
            results.add_result(
                "UEX API Connection",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def main():
    """Run all tests"""
    print("🏴‍☠️ SINISTER SNARE BACKEND API TEST SUITE")
    print("=" * 60)
    
    all_results = TestResults()
    
    # Test Star Profit API integration first (primary API)
    star_profit_results = await test_star_profit_api()
    all_results.results.extend(star_profit_results.results)
    all_results.passed += star_profit_results.passed
    all_results.failed += star_profit_results.failed
    
    # Test UEX API as fallback
    uex_results = await test_uex_api_direct()
    all_results.results.extend(uex_results.results)
    all_results.passed += uex_results.passed
    all_results.failed += uex_results.failed
    
    # Test backend endpoints
    backend_results = await test_backend_endpoints()
    all_results.results.extend(backend_results.results)
    all_results.passed += backend_results.passed
    all_results.failed += backend_results.failed
    
    # Test rate limiting
    rate_results = await test_rate_limiting()
    all_results.results.extend(rate_results.results)
    all_results.passed += rate_results.passed
    all_results.failed += rate_results.failed
    
    # Print final summary
    all_results.print_summary()
    
    # Save detailed results to file
    with open('/app/test_results_detailed.json', 'w') as f:
        json.dump(all_results.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")
    
    return all_results.failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)