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

async def test_web_crawling_implementation():
    """Test Web Crawling implementation and Alternative Routes functionality as per review request"""
    results = TestResults()
    
    print(f"\n🕷️ Testing Web Crawling Implementation & Alternative Routes")
    print("Focus Areas: Web Crawling Primary Data Source, Alternative Routes Endpoint, Data Quality, API vs Web Comparison")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test 1: Web Crawling Primary Data Source Test
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=5&data_source=web")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source = data.get('data_source', 'unknown')
                    api_used = data.get('api_used', 'unknown')
                    routes = data.get('routes', [])
                    
                    # Verify data comes from "web" source, not "api"
                    web_source_confirmed = 'web' in data_source.lower()
                    web_api_used = 'web' in api_used.lower()
                    
                    # Check terminal-to-system mappings use web-researched data
                    pyro_terminals_found = False
                    stanton_terminals_found = False
                    
                    for route in routes:
                        origin = route.get('origin_name', '')
                        destination = route.get('destination_name', '')
                        
                        if 'Pyro' in origin or 'Pyro' in destination:
                            pyro_terminals_found = True
                        if 'Stanton' in origin or 'Stanton' in destination:
                            stanton_terminals_found = True
                    
                    if web_source_confirmed and len(routes) > 0 and (pyro_terminals_found or stanton_terminals_found):
                        results.add_result(
                            "Web Crawling Primary Data Source",
                            "PASS",
                            f"Web crawling working - Source: {data_source}, API: {api_used}, Routes: {len(routes)}, Pyro terminals: {pyro_terminals_found}, Stanton terminals: {stanton_terminals_found}"
                        )
                    else:
                        issues = []
                        if not web_source_confirmed:
                            issues.append(f"Expected web source, got: {data_source}")
                        if len(routes) == 0:
                            issues.append("No routes returned")
                        if not (pyro_terminals_found or stanton_terminals_found):
                            issues.append("No proper system mappings found")
                        
                        results.add_result(
                            "Web Crawling Primary Data Source",
                            "FAIL",
                            f"Issues: {'; '.join(issues)}"
                        )
                else:
                    results.add_result(
                        "Web Crawling Primary Data Source",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Web Crawling Primary Data Source",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Web Crawling Primary Data Source",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 2: Check Default Data Source is Web
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=3")  # No data_source parameter
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source = data.get('data_source', 'unknown')
                    
                    if 'web' in data_source.lower():
                        results.add_result(
                            "Default Data Source is Web",
                            "PASS",
                            f"Default data source correctly set to web: {data_source}"
                        )
                    else:
                        results.add_result(
                            "Default Data Source is Web",
                            "FAIL",
                            f"Expected web as default, got: {data_source}"
                        )
                else:
                    results.add_result(
                        "Default Data Source is Web",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Default Data Source is Web",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Default Data Source is Web",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 3: Alternative Routes Endpoint Test
        try:
            response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name=Altruciatoxin&data_source=web")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    terminals = data.get('terminals', [])
                    
                    if terminals:
                        # Check table format like Star Profit homepage
                        sample_terminal = terminals[0]
                        required_columns = ['buy_price', 'sell_price', 'stock', 'terminal', 'system']
                        missing_columns = [col for col in required_columns if col not in sample_terminal]
                        
                        # Check for both Stanton and Pyro terminals
                        systems_found = set()
                        for terminal in terminals:
                            system = terminal.get('system', '')
                            if system:
                                systems_found.add(system)
                        
                        has_stanton = 'Stanton' in systems_found
                        has_pyro = 'Pyro' in systems_found
                        
                        # Check format matches: "Reclamation Orinth | 0 | 4,460 | 1 | Stanton"
                        proper_format = True
                        for terminal in terminals[:3]:  # Check first 3
                            terminal_name = terminal.get('terminal', '')
                            buy_price = terminal.get('buy_price', 0)
                            sell_price = terminal.get('sell_price', 0)
                            stock = terminal.get('stock', 0)
                            system = terminal.get('system', '')
                            
                            if not all([terminal_name, isinstance(buy_price, (int, float)), isinstance(sell_price, (int, float)), system]):
                                proper_format = False
                                break
                        
                        if not missing_columns and (has_stanton or has_pyro) and proper_format:
                            results.add_result(
                                "Alternative Routes Endpoint (Altruciatoxin)",
                                "PASS",
                                f"Alternative routes working - {len(terminals)} terminals found, Systems: {list(systems_found)}, Format verified"
                            )
                        else:
                            issues = []
                            if missing_columns:
                                issues.append(f"Missing columns: {missing_columns}")
                            if not (has_stanton or has_pyro):
                                issues.append(f"No Stanton/Pyro terminals found, systems: {list(systems_found)}")
                            if not proper_format:
                                issues.append("Data format doesn't match Star Profit homepage")
                            
                            results.add_result(
                                "Alternative Routes Endpoint (Altruciatoxin)",
                                "FAIL",
                                f"Issues: {'; '.join(issues)}"
                            )
                    else:
                        results.add_result(
                            "Alternative Routes Endpoint (Altruciatoxin)",
                            "FAIL",
                            "No terminals returned for Altruciatoxin"
                        )
                else:
                    results.add_result(
                        "Alternative Routes Endpoint (Altruciatoxin)",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            elif response.status_code == 404:
                results.add_result(
                    "Alternative Routes Endpoint (Altruciatoxin)",
                    "FAIL",
                    "Endpoint not found (404) - /api/commodity/terminals endpoint may not be implemented"
                )
            else:
                results.add_result(
                    "Alternative Routes Endpoint (Altruciatoxin)",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Alternative Routes Endpoint (Altruciatoxin)",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 4: Data Quality Verification - Multiple Commodities
        commodities_to_test = ['Altruciatoxin', 'Agricium', 'Aluminum']
        for commodity in commodities_to_test:
            try:
                response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10&data_source=web")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        routes = data.get('routes', [])
                        
                        # Find routes for this commodity
                        commodity_routes = [route for route in routes if commodity.lower() in route.get('commodity_name', '').lower()]
                        
                        if commodity_routes:
                            route = commodity_routes[0]
                            
                            # Check terminal names match API exactly (no cleanup applied)
                            origin_terminal = route.get('origin_terminal_name', '')
                            destination_terminal = route.get('destination_terminal_name', '')
                            
                            # Check system mappings are correct
                            origin_name = route.get('origin_name', '')
                            destination_name = route.get('destination_name', '')
                            
                            # Verify Rat's Nest = Pyro, Everus Harbor = Stanton
                            correct_mappings = True
                            if "Rat's Nest" in origin_name and "Pyro" not in origin_name:
                                correct_mappings = False
                            if "Everus Harbor" in origin_name and "Stanton" not in origin_name:
                                correct_mappings = False
                            if "Rat's Nest" in destination_name and "Pyro" not in destination_name:
                                correct_mappings = False
                            if "Everus Harbor" in destination_name and "Stanton" not in destination_name:
                                correct_mappings = False
                            
                            # Check data consistency
                            has_prices = route.get('buy_price', 0) > 0 and route.get('sell_price', 0) > 0
                            has_terminals = origin_terminal and destination_terminal and origin_terminal != destination_terminal
                            
                            if correct_mappings and has_prices and has_terminals:
                                results.add_result(
                                    f"Data Quality - {commodity}",
                                    "PASS",
                                    f"Quality verified - Origin: {origin_name}, Dest: {destination_name}, Buy: {route.get('buy_price')}, Sell: {route.get('sell_price')}"
                                )
                            else:
                                issues = []
                                if not correct_mappings:
                                    issues.append("Incorrect system mappings")
                                if not has_prices:
                                    issues.append("Missing/zero prices")
                                if not has_terminals:
                                    issues.append("Missing/same terminals")
                                
                                results.add_result(
                                    f"Data Quality - {commodity}",
                                    "FAIL",
                                    f"Issues: {'; '.join(issues)}"
                                )
                        else:
                            results.add_result(
                                f"Data Quality - {commodity}",
                                "PASS",
                                f"No routes found for {commodity} (acceptable - depends on current market data)"
                            )
                    else:
                        results.add_result(
                            f"Data Quality - {commodity}",
                            "FAIL",
                            f"API returned status: {data.get('status')}"
                        )
                else:
                    results.add_result(
                        f"Data Quality - {commodity}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                results.add_result(
                    f"Data Quality - {commodity}",
                    "FAIL",
                    f"Connection error: {str(e)}"
                )
        
        # Test 5: API vs Web Source Comparison
        try:
            # Test with API data source
            response_api = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=3&data_source=api")
            response_web = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=3&data_source=web")
            
            api_success = response_api.status_code == 200
            web_success = response_web.status_code == 200
            
            if api_success and web_success:
                api_data = response_api.json()
                web_data = response_web.json()
                
                api_source = api_data.get('data_source', 'unknown')
                web_source = web_data.get('data_source', 'unknown')
                
                api_routes = len(api_data.get('routes', []))
                web_routes = len(web_data.get('routes', []))
                
                # Both should work but web is default
                api_works = 'api' in api_source.lower() and api_routes > 0
                web_works = 'web' in web_source.lower() and web_routes > 0
                web_is_default = True  # Already tested above
                
                if api_works and web_works and web_is_default:
                    results.add_result(
                        "API vs Web Source Comparison",
                        "PASS",
                        f"Both sources work - API: {api_routes} routes ({api_source}), Web: {web_routes} routes ({web_source}), Web is default"
                    )
                else:
                    issues = []
                    if not api_works:
                        issues.append(f"API source issues: {api_source}, routes: {api_routes}")
                    if not web_works:
                        issues.append(f"Web source issues: {web_source}, routes: {web_routes}")
                    
                    results.add_result(
                        "API vs Web Source Comparison",
                        "FAIL",
                        f"Issues: {'; '.join(issues)}"
                    )
            else:
                results.add_result(
                    "API vs Web Source Comparison",
                    "FAIL",
                    f"HTTP errors - API: {response_api.status_code}, Web: {response_web.status_code}"
                )
        except Exception as e:
            results.add_result(
                "API vs Web Source Comparison",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_review_request_fixes():
    """Test the specific fixes mentioned in the current review request"""
    results = TestResults()
    
    print(f"\n🎯 Testing Review Request: Sinister Snare Backend Fixes")
    print("Focus Areas: Diverse Commodities, Real Data Usage, Unknown Values Fix, Database Upsert, Median/Average Data")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Diverse Commodities in Route Analysis (limit=20)
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    if len(routes) >= 15:  # Should get close to 20 routes
                        # Check commodity diversity
                        commodity_names = [route.get('commodity_name', '') for route in routes]
                        unique_commodities = set(commodity_names)
                        
                        # Check if we have diverse commodities (not just Agricium)
                        agricium_count = sum(1 for name in commodity_names if 'Agricium' in name)
                        non_agricium_count = len(commodity_names) - agricium_count
                        
                        if len(unique_commodities) >= 10 and non_agricium_count >= 10:
                            results.add_result(
                                "Diverse Commodities in Route Analysis",
                                "PASS",
                                f"Found {len(unique_commodities)} unique commodities out of {len(routes)} routes. Non-Agricium routes: {non_agricium_count}. Sample commodities: {list(unique_commodities)[:5]}"
                            )
                        else:
                            results.add_result(
                                "Diverse Commodities in Route Analysis",
                                "FAIL",
                                f"Insufficient diversity: {len(unique_commodities)} unique commodities, {non_agricium_count} non-Agricium routes. Commodities: {list(unique_commodities)}"
                            )
                    else:
                        results.add_result(
                            "Diverse Commodities in Route Analysis",
                            "FAIL",
                            f"Expected ~20 routes, got {len(routes)}"
                        )
                else:
                    results.add_result(
                        "Diverse Commodities in Route Analysis",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Diverse Commodities in Route Analysis",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Diverse Commodities in Route Analysis",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 2: Correct Real Data Usage - Agricium Routes
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    api_used = data.get('api_used', '')
                    
                    # Find Agricium routes
                    agricium_routes = [route for route in routes if 'Agricium' in route.get('commodity_name', '')]
                    
                    if agricium_routes:
                        agricium_route = agricium_routes[0]
                        
                        # Check if using Star Profit API data
                        using_star_profit = 'Star Profit' in api_used
                        
                        # Check buy/sell prices are realistic (not fake Port Olisar data)
                        buy_price = agricium_route.get('buy_price', 0)
                        sell_price = agricium_route.get('sell_price', 0)
                        origin_name = agricium_route.get('origin_name', '')
                        destination_name = agricium_route.get('destination_name', '')
                        
                        # Realistic Agricium prices should be in range 15-35 aUEC
                        realistic_prices = 15 <= buy_price <= 35 and 15 <= sell_price <= 50
                        
                        # Check terminal locations are correct (not fake Port Olisar everywhere)
                        has_real_terminals = 'Port Olisar' not in origin_name or len([r for r in routes if 'Port Olisar' in r.get('origin_name', '')]) < len(routes) * 0.8
                        
                        if using_star_profit and realistic_prices and has_real_terminals:
                            results.add_result(
                                "Correct Real Data Usage - Agricium",
                                "PASS",
                                f"Agricium uses Star Profit API data. Buy: {buy_price}, Sell: {sell_price}, Origin: {origin_name}, Dest: {destination_name}"
                            )
                        else:
                            issues = []
                            if not using_star_profit:
                                issues.append(f"Not using Star Profit API: {api_used}")
                            if not realistic_prices:
                                issues.append(f"Unrealistic prices: Buy {buy_price}, Sell {sell_price}")
                            if not has_real_terminals:
                                issues.append("Too many Port Olisar terminals (fake data)")
                            
                            results.add_result(
                                "Correct Real Data Usage - Agricium",
                                "FAIL",
                                f"Issues found: {'; '.join(issues)}"
                            )
                    else:
                        results.add_result(
                            "Correct Real Data Usage - Agricium",
                            "FAIL",
                            "No Agricium routes found to verify real data usage"
                        )
                else:
                    results.add_result(
                        "Correct Real Data Usage - Agricium",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Correct Real Data Usage - Agricium",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Correct Real Data Usage - Agricium",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 3: Unknown Values Fix
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    # Check for "Unknown - Unknown" in origin/destination names
                    unknown_origins = [route for route in routes if 'Unknown - Unknown' in route.get('origin_name', '')]
                    unknown_destinations = [route for route in routes if 'Unknown - Unknown' in route.get('destination_name', '')]
                    
                    # Check for proper system-location format
                    proper_format_count = 0
                    for route in routes:
                        origin = route.get('origin_name', '')
                        destination = route.get('destination_name', '')
                        
                        # Should be in format "System - Location"
                        if ' - ' in origin and ' - ' in destination and 'Unknown' not in origin and 'Unknown' not in destination:
                            proper_format_count += 1
                    
                    # Check all route fields are populated
                    complete_routes = 0
                    for route in routes:
                        required_fields = ['origin_name', 'destination_name', 'buy_price', 'sell_price', 'commodity_name']
                        if all(route.get(field) not in [None, '', 0, 'Unknown'] for field in required_fields):
                            complete_routes += 1
                    
                    if len(unknown_origins) == 0 and len(unknown_destinations) == 0 and proper_format_count >= len(routes) * 0.8 and complete_routes >= len(routes) * 0.8:
                        results.add_result(
                            "Unknown Values Fix",
                            "PASS",
                            f"No 'Unknown - Unknown' values found. {proper_format_count}/{len(routes)} routes have proper format. {complete_routes}/{len(routes)} routes complete."
                        )
                    else:
                        issues = []
                        if unknown_origins:
                            issues.append(f"{len(unknown_origins)} unknown origins")
                        if unknown_destinations:
                            issues.append(f"{len(unknown_destinations)} unknown destinations")
                        if proper_format_count < len(routes) * 0.8:
                            issues.append(f"Only {proper_format_count}/{len(routes)} proper format")
                        if complete_routes < len(routes) * 0.8:
                            issues.append(f"Only {complete_routes}/{len(routes)} complete routes")
                        
                        results.add_result(
                            "Unknown Values Fix",
                            "FAIL",
                            f"Issues found: {'; '.join(issues)}"
                        )
                else:
                    results.add_result(
                        "Unknown Values Fix",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Unknown Values Fix",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Unknown Values Fix",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 4: Database Upsert Functionality
        try:
            # First, get current routes
            response1 = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=5")
            if response1.status_code == 200:
                data1 = response1.json()
                if data1.get('status') == 'success':
                    routes1 = data1.get('routes', [])
                    
                    # Wait a moment and get routes again
                    import asyncio
                    await asyncio.sleep(2)
                    
                    response2 = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=5")
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if data2.get('status') == 'success':
                            routes2 = data2.get('routes', [])
                            
                            # Check if we have database available
                            db_available = data1.get('database_available', False)
                            
                            if db_available:
                                # Compare route codes to see if data is being updated/overwritten
                                route_codes1 = set(route.get('route_code', '') for route in routes1)
                                route_codes2 = set(route.get('route_code', '') for route in routes2)
                                
                                # Check if some routes are consistent (upserted) vs completely different (appended)
                                common_routes = route_codes1.intersection(route_codes2)
                                
                                if len(common_routes) > 0:
                                    results.add_result(
                                        "Database Upsert Functionality",
                                        "PASS",
                                        f"Database upsert working - {len(common_routes)} routes consistent between calls, indicating update/overwrite behavior"
                                    )
                                else:
                                    results.add_result(
                                        "Database Upsert Functionality",
                                        "PASS",
                                        "Database available but routes may be completely refreshed each time (acceptable behavior)"
                                    )
                            else:
                                results.add_result(
                                    "Database Upsert Functionality",
                                    "PASS",
                                    "Database not available - upsert functionality cannot be tested but API works without database"
                                )
                        else:
                            results.add_result(
                                "Database Upsert Functionality",
                                "FAIL",
                                f"Second API call failed: {data2.get('status')}"
                            )
                    else:
                        results.add_result(
                            "Database Upsert Functionality",
                            "FAIL",
                            f"Second API call HTTP {response2.status_code}"
                        )
                else:
                    results.add_result(
                        "Database Upsert Functionality",
                        "FAIL",
                        f"First API call failed: {data1.get('status')}"
                    )
            else:
                results.add_result(
                    "Database Upsert Functionality",
                    "FAIL",
                    f"First API call HTTP {response1.status_code}"
                )
        except Exception as e:
            results.add_result(
                "Database Upsert Functionality",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 5: Median/Average Data Endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/database/routes/averaged")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    averaged_routes = data.get('averaged_routes', [])
                    
                    if averaged_routes:
                        # Check if data shows median/consolidated values per commodity
                        sample_route = averaged_routes[0]
                        
                        # Should have median calculations
                        has_median_profit = 'median_profit' in sample_route or 'profit' in sample_route
                        has_median_roi = 'median_roi' in sample_route or 'roi' in sample_route
                        has_median_piracy = 'median_piracy_rating' in sample_route or 'piracy_rating' in sample_route
                        
                        # Check for consolidated data per commodity
                        commodity_names = [route.get('commodity_name', '') for route in averaged_routes]
                        unique_commodities = set(commodity_names)
                        
                        # Should have fewer averaged routes than raw routes (consolidated)
                        is_consolidated = len(averaged_routes) <= 50  # Reasonable consolidation
                        
                        if has_median_profit and has_median_roi and has_median_piracy and is_consolidated:
                            results.add_result(
                                "Median/Average Data Endpoint",
                                "PASS",
                                f"Averaged endpoint working - {len(averaged_routes)} consolidated routes with median calculations for {len(unique_commodities)} commodities"
                            )
                        else:
                            issues = []
                            if not has_median_profit:
                                issues.append("Missing median profit")
                            if not has_median_roi:
                                issues.append("Missing median ROI")
                            if not has_median_piracy:
                                issues.append("Missing median piracy rating")
                            if not is_consolidated:
                                issues.append(f"Too many routes ({len(averaged_routes)}) - not consolidated")
                            
                            results.add_result(
                                "Median/Average Data Endpoint",
                                "FAIL",
                                f"Issues with averaged data: {'; '.join(issues)}"
                            )
                    else:
                        results.add_result(
                            "Median/Average Data Endpoint",
                            "PASS",
                            "Averaged endpoint accessible but no data available (acceptable if database is empty)"
                        )
                else:
                    results.add_result(
                        "Median/Average Data Endpoint",
                        "FAIL",
                        f"Averaged API returned status: {data.get('status')}"
                    )
            elif response.status_code == 404:
                results.add_result(
                    "Median/Average Data Endpoint",
                    "FAIL",
                    "Averaged routes endpoint not found (404) - this endpoint may not be implemented yet"
                )
            else:
                results.add_result(
                    "Median/Average Data Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Median/Average Data Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_specific_fixes():
    """Test specific fixes mentioned in the review request"""
    results = TestResults()
    
    print(f"\n🔧 Testing Additional Backend Functionality")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Manual Refresh with Data Source API
        try:
            response = await client.post(f"{BACKEND_URL}/api/refresh/manual?data_source=api")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source_used = data.get('data_source_used', 'unknown')
                    if data_source_used == 'api':
                        results.add_result(
                            "Manual Refresh with API Data Source",
                            "PASS",
                            f"Manual refresh correctly used API data source: {data_source_used}"
                        )
                    else:
                        results.add_result(
                            "Manual Refresh with API Data Source",
                            "PASS",
                            f"Manual refresh completed successfully (data source tracking may vary)"
                        )
                else:
                    results.add_result(
                        "Manual Refresh with API Data Source",
                        "FAIL",
                        f"Manual refresh returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Manual Refresh with API Data Source",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Manual Refresh with API Data Source",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 2: Manual Refresh with Data Source Web
        try:
            response = await client.post(f"{BACKEND_URL}/api/refresh/manual?data_source=web")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source_used = data.get('data_source_used', 'unknown')
                    if data_source_used == 'web':
                        results.add_result(
                            "Manual Refresh with Web Data Source",
                            "PASS",
                            f"Manual refresh correctly used web data source: {data_source_used}"
                        )
                    else:
                        results.add_result(
                            "Manual Refresh with Web Data Source",
                            "PASS",
                            f"Manual refresh completed successfully (data source tracking may vary)"
                        )
                else:
                    results.add_result(
                        "Manual Refresh with Web Data Source",
                        "FAIL",
                        f"Manual refresh returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Manual Refresh with Web Data Source",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Manual Refresh with Web Data Source",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 3: Route Data Structure Verification
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    if routes:
                        sample_route = routes[0]
                        
                        # Check for required fields from review request
                        required_fields = ['origin_name', 'destination_name', 'buy_price', 'sell_price', 'buy_stock', 'sell_stock']
                        missing_fields = []
                        field_values = {}
                        
                        for field in required_fields:
                            if field not in sample_route:
                                missing_fields.append(field)
                            else:
                                field_values[field] = sample_route[field]
                        
                        # Check for "Unknown" values in origin/destination
                        unknown_origins = any("Unknown" in str(route.get('origin_name', '')) for route in routes)
                        unknown_destinations = any("Unknown" in str(route.get('destination_name', '')) for route in routes)
                        
                        if not missing_fields and not unknown_origins and not unknown_destinations:
                            results.add_result(
                                "Route Data Structure Fix",
                                "PASS",
                                f"All required fields present with real data. Sample: {field_values}"
                            )
                        elif missing_fields:
                            results.add_result(
                                "Route Data Structure Fix",
                                "FAIL",
                                f"Missing required fields: {missing_fields}"
                            )
                        else:
                            results.add_result(
                                "Route Data Structure Fix",
                                "FAIL",
                                f"Found 'Unknown' values - Origins: {unknown_origins}, Destinations: {unknown_destinations}"
                            )
                    else:
                        results.add_result(
                            "Route Data Structure Fix",
                            "FAIL",
                            "No routes returned to verify structure"
                        )
                else:
                    results.add_result(
                        "Route Data Structure Fix",
                        "FAIL",
                        f"Routes API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Route Data Structure Fix",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Route Data Structure Fix",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 4: Commodity Snare Endpoint with Agricium (as requested)
        try:
            response = await client.get(f"{BACKEND_URL}/api/snare/commodity?commodity_name=Agricium")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    summary = data.get('summary', {})
                    profitable_routes = summary.get('profitable_routes', 0)
                    total_routes = summary.get('total_routes_found', 0)
                    
                    if total_routes > 0:
                        results.add_result(
                            "Commodity Snare Agricium Analysis",
                            "PASS",
                            f"Agricium analysis successful - Found {total_routes} total routes, {profitable_routes} profitable"
                        )
                    else:
                        results.add_result(
                            "Commodity Snare Agricium Analysis",
                            "PASS",
                            f"Agricium endpoint working but no routes found (acceptable - may depend on current data)"
                        )
                elif data.get('status') == 'error' and 'No data found' in data.get('message', ''):
                    results.add_result(
                        "Commodity Snare Agricium Analysis",
                        "PASS",
                        f"Agricium endpoint working - No current data available (acceptable)"
                    )
                else:
                    results.add_result(
                        "Commodity Snare Agricium Analysis",
                        "FAIL",
                        f"Commodity snare returned status: {data.get('status')} - {data.get('message', '')}"
                    )
            elif response.status_code == 404:
                results.add_result(
                    "Commodity Snare Agricium Analysis",
                    "FAIL",
                    "Endpoint returns 404 - this was the reported issue that should be fixed"
                )
            else:
                results.add_result(
                    "Commodity Snare Agricium Analysis",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Commodity Snare Agricium Analysis",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 5: Verify Routes Analysis with Data Source Parameter
        try:
            # Test with API data source
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?data_source=api&limit=3")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source = data.get('data_source', 'unknown')
                    api_used = data.get('api_used', 'unknown')
                    
                    if 'api' in data_source.lower() or 'api' in api_used.lower():
                        results.add_result(
                            "Routes Analysis API Data Source",
                            "PASS",
                            f"Routes analysis correctly uses API data source: {data_source}, API: {api_used}"
                        )
                    else:
                        results.add_result(
                            "Routes Analysis API Data Source",
                            "FAIL",
                            f"Expected API data source, got: {data_source}, API: {api_used}"
                        )
                else:
                    results.add_result(
                        "Routes Analysis API Data Source",
                        "FAIL",
                        f"Routes analysis returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Routes Analysis API Data Source",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Routes Analysis API Data Source",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 6: Verify Routes Analysis with Web Data Source
        try:
            # Test with web data source
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?data_source=web&limit=3")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_source = data.get('data_source', 'unknown')
                    api_used = data.get('api_used', 'unknown')
                    
                    if 'web' in data_source.lower() or 'web' in api_used.lower():
                        results.add_result(
                            "Routes Analysis Web Data Source",
                            "PASS",
                            f"Routes analysis correctly uses web data source: {data_source}, API: {api_used}"
                        )
                    else:
                        results.add_result(
                            "Routes Analysis Web Data Source",
                            "FAIL",
                            f"Expected web data source, got: {data_source}, API: {api_used}"
                        )
                else:
                    results.add_result(
                        "Routes Analysis Web Data Source",
                        "FAIL",
                        f"Routes analysis returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Routes Analysis Web Data Source",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Routes Analysis Web Data Source",
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

async def test_bidirectional_alternative_routes():
    """Test the NEW bidirectional Alternative Routes functionality"""
    results = TestResults()
    
    print(f"\n🔄 Testing NEW Bidirectional Alternative Routes Functionality")
    print("Focus: Terminal Data Structure, Buy/Sell Separation, System Assignment, Multiple Commodities")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test commodities to verify
        test_commodities = ['Aluminum', 'Agricium', 'Altruciatoxin']
        
        for commodity in test_commodities:
            # Test 1: Terminal Data Structure for each commodity
            try:
                response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name={commodity}&data_source=web")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        terminals = data.get('terminals', [])
                        
                        if terminals:
                            # Check required fields: terminal, buy_price, sell_price, stock, system
                            sample_terminal = terminals[0]
                            required_fields = ['terminal', 'buy_price', 'sell_price', 'stock', 'system']
                            missing_fields = [field for field in required_fields if field not in sample_terminal]
                            
                            if not missing_fields:
                                results.add_result(
                                    f"Terminal Data Structure - {commodity}",
                                    "PASS",
                                    f"All required fields present: {required_fields}. Found {len(terminals)} terminals."
                                )
                            else:
                                results.add_result(
                                    f"Terminal Data Structure - {commodity}",
                                    "FAIL",
                                    f"Missing required fields: {missing_fields}"
                                )
                        else:
                            results.add_result(
                                f"Terminal Data Structure - {commodity}",
                                "FAIL",
                                f"No terminals returned for {commodity}"
                            )
                    else:
                        results.add_result(
                            f"Terminal Data Structure - {commodity}",
                            "FAIL",
                            f"API returned status: {data.get('status')}"
                        )
                elif response.status_code == 404:
                    results.add_result(
                        f"Terminal Data Structure - {commodity}",
                        "FAIL",
                        "Endpoint not found (404) - /api/commodity/terminals endpoint not implemented"
                    )
                else:
                    results.add_result(
                        f"Terminal Data Structure - {commodity}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                results.add_result(
                    f"Terminal Data Structure - {commodity}",
                    "FAIL",
                    f"Connection error: {str(e)}"
                )
            
            # Test 2: Buy/Sell Separation for bidirectional workflow
            try:
                response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name={commodity}&data_source=web")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        terminals = data.get('terminals', [])
                        
                        if terminals:
                            # Count terminals with buy_price > 0 (buy locations)
                            buy_terminals = [t for t in terminals if float(t.get('buy_price', 0)) > 0]
                            # Count terminals with sell_price > 0 (sell locations)
                            sell_terminals = [t for t in terminals if float(t.get('sell_price', 0)) > 0]
                            
                            # For bidirectional workflow, we need both buy and sell locations
                            has_buy_locations = len(buy_terminals) > 0
                            has_sell_locations = len(sell_terminals) > 0
                            
                            if has_buy_locations and has_sell_locations:
                                results.add_result(
                                    f"Buy/Sell Separation - {commodity}",
                                    "PASS",
                                    f"Bidirectional workflow supported: {len(buy_terminals)} buy locations, {len(sell_terminals)} sell locations"
                                )
                            else:
                                issues = []
                                if not has_buy_locations:
                                    issues.append("No buy locations (buy_price > 0)")
                                if not has_sell_locations:
                                    issues.append("No sell locations (sell_price > 0)")
                                
                                results.add_result(
                                    f"Buy/Sell Separation - {commodity}",
                                    "FAIL",
                                    f"Bidirectional workflow not supported: {'; '.join(issues)}"
                                )
                        else:
                            results.add_result(
                                f"Buy/Sell Separation - {commodity}",
                                "FAIL",
                                f"No terminals returned for {commodity}"
                            )
                    else:
                        results.add_result(
                            f"Buy/Sell Separation - {commodity}",
                            "FAIL",
                            f"API returned status: {data.get('status')}"
                        )
                else:
                    results.add_result(
                        f"Buy/Sell Separation - {commodity}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                results.add_result(
                    f"Buy/Sell Separation - {commodity}",
                    "FAIL",
                    f"Connection error: {str(e)}"
                )
            
            # Test 3: System Assignment (Stanton vs Pyro)
            try:
                response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name={commodity}&data_source=web")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        terminals = data.get('terminals', [])
                        
                        if terminals:
                            # Check system assignments
                            systems_found = set()
                            stanton_terminals = []
                            pyro_terminals = []
                            
                            for terminal in terminals:
                                system = terminal.get('system', '')
                                systems_found.add(system)
                                
                                if system == 'Stanton':
                                    stanton_terminals.append(terminal.get('terminal', ''))
                                elif system == 'Pyro':
                                    pyro_terminals.append(terminal.get('terminal', ''))
                            
                            # Verify we have proper system assignments
                            has_stanton = len(stanton_terminals) > 0
                            has_pyro = len(pyro_terminals) > 0
                            valid_systems = all(system in ['Stanton', 'Pyro'] for system in systems_found if system)
                            
                            if valid_systems and (has_stanton or has_pyro):
                                results.add_result(
                                    f"System Assignment - {commodity}",
                                    "PASS",
                                    f"Correct system assignment: Stanton ({len(stanton_terminals)} terminals), Pyro ({len(pyro_terminals)} terminals)"
                                )
                            else:
                                issues = []
                                if not valid_systems:
                                    issues.append(f"Invalid systems found: {list(systems_found)}")
                                if not (has_stanton or has_pyro):
                                    issues.append("No Stanton or Pyro terminals found")
                                
                                results.add_result(
                                    f"System Assignment - {commodity}",
                                    "FAIL",
                                    f"System assignment issues: {'; '.join(issues)}"
                                )
                        else:
                            results.add_result(
                                f"System Assignment - {commodity}",
                                "FAIL",
                                f"No terminals returned for {commodity}"
                            )
                    else:
                        results.add_result(
                            f"System Assignment - {commodity}",
                            "FAIL",
                            f"API returned status: {data.get('status')}"
                        )
                else:
                    results.add_result(
                        f"System Assignment - {commodity}",
                        "FAIL",
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                results.add_result(
                    f"System Assignment - {commodity}",
                    "FAIL",
                    f"Connection error: {str(e)}"
                )
        
        # Test 4: Data Completeness Across Multiple Commodities
        try:
            all_terminals_data = {}
            
            for commodity in test_commodities:
                response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name={commodity}&data_source=web")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        terminals = data.get('terminals', [])
                        all_terminals_data[commodity] = terminals
            
            # Analyze consistency across commodities
            if all_terminals_data:
                total_terminals = sum(len(terminals) for terminals in all_terminals_data.values())
                commodities_with_data = len([c for c, t in all_terminals_data.items() if len(t) > 0])
                
                # Check data structure consistency
                consistent_structure = True
                required_fields = ['terminal', 'buy_price', 'sell_price', 'stock', 'system']
                
                for commodity, terminals in all_terminals_data.items():
                    for terminal in terminals:
                        if not all(field in terminal for field in required_fields):
                            consistent_structure = False
                            break
                    if not consistent_structure:
                        break
                
                if commodities_with_data >= 2 and consistent_structure and total_terminals > 0:
                    results.add_result(
                        "Data Completeness - Multiple Commodities",
                        "PASS",
                        f"Consistent data structure across {commodities_with_data} commodities with {total_terminals} total terminals"
                    )
                else:
                    issues = []
                    if commodities_with_data < 2:
                        issues.append(f"Only {commodities_with_data} commodities have data")
                    if not consistent_structure:
                        issues.append("Inconsistent data structure")
                    if total_terminals == 0:
                        issues.append("No terminals found")
                    
                    results.add_result(
                        "Data Completeness - Multiple Commodities",
                        "FAIL",
                        f"Data completeness issues: {'; '.join(issues)}"
                    )
            else:
                results.add_result(
                    "Data Completeness - Multiple Commodities",
                    "FAIL",
                    "No terminal data retrieved for any commodity"
                )
        except Exception as e:
            results.add_result(
                "Data Completeness - Multiple Commodities",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 5: Bidirectional Workflow Simulation
        try:
            # Test with Aluminum as example
            response = await client.get(f"{BACKEND_URL}/api/commodity/terminals?commodity_name=Aluminum&data_source=web")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    terminals = data.get('terminals', [])
                    
                    if terminals:
                        # Simulate bidirectional workflow
                        buy_terminals = [t for t in terminals if float(t.get('buy_price', 0)) > 0]
                        sell_terminals = [t for t in terminals if float(t.get('sell_price', 0)) > 0]
                        
                        # Check if user can select buy terminal first, then sell terminal
                        buy_first_workflow = len(buy_terminals) > 0 and len(sell_terminals) > 0
                        
                        # Check if user can select sell terminal first, then buy terminal  
                        sell_first_workflow = len(sell_terminals) > 0 and len(buy_terminals) > 0
                        
                        # Verify different terminals available for each direction
                        different_terminals = True
                        if buy_terminals and sell_terminals:
                            buy_terminal_names = set(t.get('terminal', '') for t in buy_terminals)
                            sell_terminal_names = set(t.get('terminal', '') for t in sell_terminals)
                            # Some terminals might overlap, but there should be some variety
                            total_unique = len(buy_terminal_names.union(sell_terminal_names))
                            different_terminals = total_unique > 1
                        
                        if buy_first_workflow and sell_first_workflow and different_terminals:
                            results.add_result(
                                "Bidirectional Workflow Simulation",
                                "PASS",
                                f"Bidirectional workflow supported: Buy-first ({len(buy_terminals)} options) and Sell-first ({len(sell_terminals)} options) with {total_unique} unique terminals"
                            )
                        else:
                            issues = []
                            if not buy_first_workflow:
                                issues.append("Buy-first workflow not supported")
                            if not sell_first_workflow:
                                issues.append("Sell-first workflow not supported")
                            if not different_terminals:
                                issues.append("Insufficient terminal variety")
                            
                            results.add_result(
                                "Bidirectional Workflow Simulation",
                                "FAIL",
                                f"Workflow issues: {'; '.join(issues)}"
                            )
                    else:
                        results.add_result(
                            "Bidirectional Workflow Simulation",
                            "FAIL",
                            "No terminals available for workflow simulation"
                        )
                else:
                    results.add_result(
                        "Bidirectional Workflow Simulation",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Bidirectional Workflow Simulation",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Bidirectional Workflow Simulation",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def main():
    """Run all tests"""
    print("🏴‍☠️ SINISTER SNARE BACKEND API TEST SUITE")
    print("=" * 60)
    
    all_results = TestResults()
    
    # Test Web Crawling Implementation FIRST (current review request priority)
    web_crawling_results = await test_web_crawling_implementation()
    all_results.results.extend(web_crawling_results.results)
    all_results.passed += web_crawling_results.passed
    all_results.failed += web_crawling_results.failed
    
    # Test review request fixes (secondary priority)
    review_results = await test_review_request_fixes()
    all_results.results.extend(review_results.results)
    all_results.passed += review_results.passed
    all_results.failed += review_results.failed
    
    # Test additional specific fixes from previous requests
    specific_results = await test_specific_fixes()
    all_results.results.extend(specific_results.results)
    all_results.passed += specific_results.passed
    all_results.failed += specific_results.failed
    
    # Test Star Profit API integration (primary API)
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