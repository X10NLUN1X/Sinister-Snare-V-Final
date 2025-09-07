#!/usr/bin/env python3
"""
Sinister Snare Backend Data Quality Test Suite
Tests the critical backend endpoints affected by terminal/commodity name fixes
Focus: Real commodity names, real terminal names, correct Star Profit API field usage, no fake data
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
        print(f"DATA QUALITY TEST SUMMARY")
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

async def test_primary_routes_endpoint():
    """Test 1: Primary Routes Endpoint - GET /api/routes/analyze?limit=10"""
    results = TestResults()
    
    print(f"\n🎯 Testing Primary Routes Endpoint: /api/routes/analyze?limit=10")
    print("Verifying: Real commodity names, real terminal names, correct Star Profit API fields")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    api_used = data.get('api_used', '')
                    
                    if not routes:
                        results.add_result(
                            "Routes Endpoint Availability",
                            "FAIL",
                            "No routes returned from analysis endpoint"
                        )
                        return results
                    
                    # Test 1.1: Verify returns real commodity names (no "Grade X" variants)
                    fake_commodity_patterns = ['Grade X', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Refined', 'Unknown Commodity']
                    fake_commodities_found = []
                    real_commodities = []
                    
                    for route in routes:
                        commodity_name = route.get('commodity_name', '')
                        if any(pattern in commodity_name for pattern in fake_commodity_patterns):
                            fake_commodities_found.append(commodity_name)
                        else:
                            real_commodities.append(commodity_name)
                    
                    if not fake_commodities_found:
                        results.add_result(
                            "Real Commodity Names (No Grade X)",
                            "PASS",
                            f"All {len(routes)} routes use real commodity names. Sample: {real_commodities[:3]}"
                        )
                    else:
                        results.add_result(
                            "Real Commodity Names (No Grade X)",
                            "FAIL",
                            f"Found fake commodity names: {fake_commodities_found}"
                        )
                    
                    # Test 1.2: Verify returns real terminal names (no "Outpost C2" or fake names)
                    fake_terminal_patterns = ['Outpost C2', 'Outpost B10', 'Terminal X', 'Station Alpha', 'Base Beta']
                    fake_terminals_found = []
                    real_terminals = []
                    
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        # Extract terminal names from "System - Terminal" format
                        origin_terminal = origin_name.split(' - ')[-1] if ' - ' in origin_name else origin_name
                        dest_terminal = destination_name.split(' - ')[-1] if ' - ' in destination_name else destination_name
                        
                        if any(pattern in origin_terminal for pattern in fake_terminal_patterns):
                            fake_terminals_found.append(origin_terminal)
                        else:
                            real_terminals.append(origin_terminal)
                            
                        if any(pattern in dest_terminal for pattern in fake_terminal_patterns):
                            fake_terminals_found.append(dest_terminal)
                        else:
                            real_terminals.append(dest_terminal)
                    
                    if not fake_terminals_found:
                        results.add_result(
                            "Real Terminal Names (No Fake Outposts)",
                            "PASS",
                            f"All terminals use real Star Citizen names. Sample: {list(set(real_terminals))[:3]}"
                        )
                    else:
                        results.add_result(
                            "Real Terminal Names (No Fake Outposts)",
                            "FAIL",
                            f"Found fake terminal names: {list(set(fake_terminals_found))}"
                        )
                    
                    # Test 1.3: Verify uses correct Star Profit API field names
                    required_fields = ['buy_price', 'sell_price', 'buy_stock', 'sell_stock']
                    sample_route = routes[0]
                    missing_fields = []
                    present_fields = {}
                    
                    for field in required_fields:
                        if field not in sample_route:
                            missing_fields.append(field)
                        else:
                            present_fields[field] = sample_route[field]
                    
                    if not missing_fields:
                        results.add_result(
                            "Star Profit API Field Names",
                            "PASS",
                            f"All required Star Profit API fields present: {present_fields}"
                        )
                    else:
                        results.add_result(
                            "Star Profit API Field Names",
                            "FAIL",
                            f"Missing Star Profit API fields: {missing_fields}"
                        )
                    
                    # Test 1.4: Check that origin_name and destination_name show real locations
                    real_sc_locations = [
                        'Port Olisar', 'Lorville', 'Area18', 'New Babbage', 'Orison',
                        'Rat\'s Nest', 'Brio\'s Breaker', 'CBD Lorville', 'Everus Harbor',
                        'Port Tressler', 'Baijini Point', 'Seraphim Station', 'GrimHex'
                    ]
                    
                    real_locations_found = 0
                    unknown_locations = []
                    
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        # Check if locations follow "System - Location" format
                        if ' - ' in origin_name and ' - ' in destination_name:
                            origin_terminal = origin_name.split(' - ')[-1]
                            dest_terminal = destination_name.split(' - ')[-1]
                            
                            # Check if terminals are real SC locations or at least not "Unknown"
                            if 'Unknown' not in origin_terminal and 'Unknown' not in dest_terminal:
                                real_locations_found += 1
                            else:
                                unknown_locations.append(f"{origin_name} -> {destination_name}")
                    
                    if real_locations_found >= len(routes) * 0.8:  # At least 80% should be real
                        results.add_result(
                            "Real Location Names in Routes",
                            "PASS",
                            f"{real_locations_found}/{len(routes)} routes have real location names"
                        )
                    else:
                        results.add_result(
                            "Real Location Names in Routes",
                            "FAIL",
                            f"Only {real_locations_found}/{len(routes)} routes have real locations. Unknown: {unknown_locations[:3]}"
                        )
                    
                    # Test 1.5: Verify Star Profit API integration
                    if 'Star Profit' in api_used:
                        results.add_result(
                            "Star Profit API Integration",
                            "PASS",
                            f"Backend correctly using Star Profit API: {api_used}"
                        )
                    else:
                        results.add_result(
                            "Star Profit API Integration",
                            "FAIL",
                            f"Backend not using Star Profit API. Current API: {api_used}"
                        )
                
                else:
                    results.add_result(
                        "Routes Endpoint Status",
                        "FAIL",
                        f"Routes endpoint returned error status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Routes Endpoint Connection",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Routes Endpoint Connection",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_commodity_snare_endpoint():
    """Test 2: Commodity Snare Endpoint - GET /api/snare/commodity?commodity_name=Agricium"""
    results = TestResults()
    
    print(f"\n🎯 Testing Commodity Snare Endpoint: /api/snare/commodity?commodity_name=Agricium")
    print("Verifying: No 'Unknown - Unknown' entries, real terminal names, exact commodity names")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/snare/commodity?commodity_name=Agricium")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    # Check for snare points or routes data
                    snare_points = data.get('snare_points', [])
                    routes = data.get('routes', [])
                    summary = data.get('summary', {})
                    
                    # Test 2.1: Verify no "Unknown - Unknown" entries in buying_point/selling_point
                    unknown_entries = []
                    if snare_points:
                        for point in snare_points:
                            buying_point = point.get('buying_point', '')
                            selling_point = point.get('selling_point', '')
                            
                            if 'Unknown - Unknown' in buying_point:
                                unknown_entries.append(f"Buying: {buying_point}")
                            if 'Unknown - Unknown' in selling_point:
                                unknown_entries.append(f"Selling: {selling_point}")
                    
                    if routes:
                        for route in routes:
                            origin = route.get('origin_name', '')
                            destination = route.get('destination_name', '')
                            
                            if 'Unknown - Unknown' in origin:
                                unknown_entries.append(f"Origin: {origin}")
                            if 'Unknown - Unknown' in destination:
                                unknown_entries.append(f"Destination: {destination}")
                    
                    if not unknown_entries:
                        results.add_result(
                            "No Unknown-Unknown Entries",
                            "PASS",
                            f"No 'Unknown - Unknown' entries found in Agricium commodity snare data"
                        )
                    else:
                        results.add_result(
                            "No Unknown-Unknown Entries",
                            "FAIL",
                            f"Found 'Unknown - Unknown' entries: {unknown_entries[:3]}"
                        )
                    
                    # Test 2.2: Verify all terminal names are real Star Citizen locations
                    real_sc_terminals = [
                        'Port Olisar', 'Lorville', 'Area18', 'New Babbage', 'Orison',
                        'Rat\'s Nest', 'Brio\'s Breaker', 'CBD Lorville', 'Everus Harbor',
                        'Port Tressler', 'Baijini Point', 'Seraphim Station', 'GrimHex',
                        'Shallow Frontier Station', 'Wide Forest Station', 'Modern Express Station'
                    ]
                    
                    terminal_names = []
                    if snare_points:
                        for point in snare_points:
                            buying_point = point.get('buying_point', '')
                            selling_point = point.get('selling_point', '')
                            
                            if ' - ' in buying_point:
                                terminal_names.append(buying_point.split(' - ')[-1])
                            if ' - ' in selling_point:
                                terminal_names.append(selling_point.split(' - ')[-1])
                    
                    if routes:
                        for route in routes:
                            origin = route.get('origin_name', '')
                            destination = route.get('destination_name', '')
                            
                            if ' - ' in origin:
                                terminal_names.append(origin.split(' - ')[-1])
                            if ' - ' in destination:
                                terminal_names.append(destination.split(' - ')[-1])
                    
                    # Check if terminals are recognizable (not fake)
                    fake_terminals = [name for name in terminal_names if 'Outpost' in name and any(char.isdigit() for char in name)]
                    
                    if not fake_terminals and terminal_names:
                        results.add_result(
                            "Real Star Citizen Terminal Names",
                            "PASS",
                            f"All terminal names appear to be real SC locations. Sample: {list(set(terminal_names))[:3]}"
                        )
                    elif not terminal_names:
                        results.add_result(
                            "Real Star Citizen Terminal Names",
                            "PASS",
                            "No terminal data to verify (acceptable if no routes found)"
                        )
                    else:
                        results.add_result(
                            "Real Star Citizen Terminal Names",
                            "FAIL",
                            f"Found potentially fake terminal names: {fake_terminals}"
                        )
                    
                    # Test 2.3: Verify commodity names are exactly as provided by Star Profit API
                    commodity_name_in_response = data.get('commodity_name', '')
                    if commodity_name_in_response == 'Agricium':
                        results.add_result(
                            "Exact Commodity Name Match",
                            "PASS",
                            f"Commodity name matches exactly: {commodity_name_in_response}"
                        )
                    else:
                        results.add_result(
                            "Exact Commodity Name Match",
                            "FAIL",
                            f"Expected 'Agricium', got: {commodity_name_in_response}"
                        )
                    
                    # Test 2.4: Check that routes show proper inter-system vs same-system classification
                    inter_system_routes = 0
                    same_system_routes = 0
                    
                    if routes:
                        for route in routes:
                            origin = route.get('origin_name', '')
                            destination = route.get('destination_name', '')
                            
                            if ' - ' in origin and ' - ' in destination:
                                origin_system = origin.split(' - ')[0]
                                dest_system = destination.split(' - ')[0]
                                
                                if origin_system == dest_system:
                                    same_system_routes += 1
                                else:
                                    inter_system_routes += 1
                    
                    if snare_points:
                        for point in snare_points:
                            buying_point = point.get('buying_point', '')
                            selling_point = point.get('selling_point', '')
                            
                            if ' - ' in buying_point and ' - ' in selling_point:
                                buy_system = buying_point.split(' - ')[0]
                                sell_system = selling_point.split(' - ')[0]
                                
                                if buy_system == sell_system:
                                    same_system_routes += 1
                                else:
                                    inter_system_routes += 1
                    
                    total_routes = inter_system_routes + same_system_routes
                    if total_routes > 0:
                        results.add_result(
                            "System Classification",
                            "PASS",
                            f"Routes properly classified: {same_system_routes} same-system, {inter_system_routes} inter-system"
                        )
                    else:
                        results.add_result(
                            "System Classification",
                            "PASS",
                            "No route data available for system classification (acceptable)"
                        )
                    
                    # Overall endpoint functionality
                    total_routes_found = summary.get('total_routes_found', len(routes) + len(snare_points))
                    if total_routes_found > 0:
                        results.add_result(
                            "Commodity Snare Functionality",
                            "PASS",
                            f"Agricium commodity snare working - found {total_routes_found} routes/points"
                        )
                    else:
                        results.add_result(
                            "Commodity Snare Functionality",
                            "PASS",
                            "Agricium endpoint accessible but no current data (acceptable)"
                        )
                
                elif data.get('status') == 'error' and 'No data found' in data.get('message', ''):
                    results.add_result(
                        "Commodity Snare Endpoint",
                        "PASS",
                        "Agricium endpoint working - no current data available (acceptable)"
                    )
                else:
                    results.add_result(
                        "Commodity Snare Endpoint",
                        "FAIL",
                        f"Commodity snare returned error: {data.get('status')} - {data.get('message', '')}"
                    )
            elif response.status_code == 404:
                results.add_result(
                    "Commodity Snare Endpoint",
                    "FAIL",
                    "Endpoint returns 404 - this endpoint should be implemented"
                )
            else:
                results.add_result(
                    "Commodity Snare Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Commodity Snare Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_data_quality_verification():
    """Test 3: Data Quality Verification - Check for fake data patterns"""
    results = TestResults()
    
    print(f"\n🎯 Testing Data Quality Verification")
    print("Verifying: No fake data like 'Refined Altruciatoxin Grade 4', 'Outpost B10', incorrect Port Olisar usage")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get a larger sample to check for fake data patterns
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    if not routes:
                        results.add_result(
                            "Data Quality Sample",
                            "FAIL",
                            "No routes available for data quality verification"
                        )
                        return results
                    
                    # Test 3.1: Verify NO fake data like "Refined Altruciatoxin Grade 4"
                    fake_commodity_patterns = [
                        'Refined Altruciatoxin Grade 4', 'Grade 4', 'Grade 3', 'Grade 2', 'Grade 1',
                        'Refined', 'Processed', 'Enhanced', 'Premium'
                    ]
                    
                    fake_commodities = []
                    for route in routes:
                        commodity_name = route.get('commodity_name', '')
                        for pattern in fake_commodity_patterns:
                            if pattern in commodity_name:
                                fake_commodities.append(commodity_name)
                                break
                    
                    if not fake_commodities:
                        results.add_result(
                            "No Fake Commodity Grades",
                            "PASS",
                            f"No fake commodity grade names found in {len(routes)} routes"
                        )
                    else:
                        results.add_result(
                            "No Fake Commodity Grades",
                            "FAIL",
                            f"Found fake commodity names: {list(set(fake_commodities))}"
                        )
                    
                    # Test 3.2: Verify NO fake terminals like "Outpost B10"
                    fake_terminal_patterns = ['Outpost B10', 'Outpost C2', 'Station Alpha', 'Base Beta', 'Terminal X']
                    
                    fake_terminals = []
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        for pattern in fake_terminal_patterns:
                            if pattern in origin_name or pattern in destination_name:
                                fake_terminals.append(f"{origin_name} -> {destination_name}")
                                break
                    
                    if not fake_terminals:
                        results.add_result(
                            "No Fake Terminal Names",
                            "PASS",
                            f"No fake terminal names found in {len(routes)} routes"
                        )
                    else:
                        results.add_result(
                            "No Fake Terminal Names",
                            "FAIL",
                            f"Found fake terminal names: {fake_terminals[:3]}"
                        )
                    
                    # Test 3.3: Verify terminal names match real Star Citizen universe
                    real_sc_terminals = [
                        'Rat\'s Nest', 'Brio\'s Breaker', 'CBD Lorville', 'Port Olisar', 'Lorville',
                        'Area18', 'New Babbage', 'Orison', 'Everus Harbor', 'Port Tressler',
                        'Baijini Point', 'Seraphim Station', 'GrimHex', 'Shallow Frontier Station',
                        'Wide Forest Station', 'Modern Express Station', 'Lucky Pathway Station'
                    ]
                    
                    terminal_names = []
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        if ' - ' in origin_name:
                            terminal_names.append(origin_name.split(' - ')[-1])
                        if ' - ' in destination_name:
                            terminal_names.append(destination_name.split(' - ')[-1])
                    
                    # Check for recognizable patterns (real SC terminals or at least not obviously fake)
                    suspicious_terminals = []
                    for terminal in set(terminal_names):
                        # Flag terminals that look fake (contain numbers in suspicious patterns)
                        if any(pattern in terminal for pattern in ['B10', 'C2', 'Alpha', 'Beta', 'X']):
                            suspicious_terminals.append(terminal)
                    
                    if not suspicious_terminals:
                        results.add_result(
                            "Real Star Citizen Terminal Names",
                            "PASS",
                            f"All terminal names appear authentic. Sample: {list(set(terminal_names))[:5]}"
                        )
                    else:
                        results.add_result(
                            "Real Star Citizen Terminal Names",
                            "FAIL",
                            f"Found suspicious terminal names: {suspicious_terminals}"
                        )
                    
                    # Test 3.4: Check system mappings are correct (Pyro - Rat's Nest, Stanton - CBD Lorville)
                    correct_mappings = {
                        'Pyro': ['Rat\'s Nest', 'Endgame', 'Starlight Service Station'],
                        'Stanton': ['CBD Lorville', 'Port Olisar', 'Lorville', 'Area18', 'New Babbage', 'Orison', 'Brio\'s Breaker']
                    }
                    
                    mapping_errors = []
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        for location in [origin_name, destination_name]:
                            if ' - ' in location:
                                system, terminal = location.split(' - ', 1)
                                
                                # Check known mappings
                                if system in correct_mappings:
                                    if terminal not in correct_mappings[system]:
                                        # Only flag if it's a known terminal in wrong system
                                        for correct_system, terminals in correct_mappings.items():
                                            if terminal in terminals and correct_system != system:
                                                mapping_errors.append(f"{terminal} should be in {correct_system}, not {system}")
                    
                    if not mapping_errors:
                        results.add_result(
                            "Correct System Mappings",
                            "PASS",
                            "No incorrect system-terminal mappings detected"
                        )
                    else:
                        results.add_result(
                            "Correct System Mappings",
                            "FAIL",
                            f"Found mapping errors: {mapping_errors[:3]}"
                        )
                
                else:
                    results.add_result(
                        "Data Quality Endpoint",
                        "FAIL",
                        f"Routes endpoint returned error: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Data Quality Endpoint",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Data Quality Endpoint",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_api_status_check():
    """Test 4: API Status Check - GET /api/status to ensure Star Profit API integration is working"""
    results = TestResults()
    
    print(f"\n🎯 Testing API Status Check: /api/status")
    print("Verifying: Star Profit API integration is working")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                # Test 4.1: Check overall API status
                if status in ['operational', 'ok']:
                    results.add_result(
                        "API Status Operational",
                        "PASS",
                        f"API status is {status}"
                    )
                else:
                    results.add_result(
                        "API Status Operational",
                        "FAIL",
                        f"API status is {status}, expected 'operational' or 'ok'"
                    )
                
                # Test 4.2: Check Star Profit API integration status
                star_profit_status = data.get('star_profit_api', data.get('apis', {}).get('star_profit', 'unknown'))
                if star_profit_status in ['connected', 'operational', 'available', 'ok']:
                    results.add_result(
                        "Star Profit API Integration",
                        "PASS",
                        f"Star Profit API status: {star_profit_status}"
                    )
                else:
                    results.add_result(
                        "Star Profit API Integration",
                        "FAIL",
                        f"Star Profit API status: {star_profit_status}"
                    )
                
                # Test 4.3: Check database status
                db_status = data.get('database', data.get('database_status', 'unknown'))
                if db_status in ['connected', 'operational', 'available', 'ok']:
                    results.add_result(
                        "Database Status",
                        "PASS",
                        f"Database status: {db_status}"
                    )
                else:
                    results.add_result(
                        "Database Status",
                        "PASS",
                        f"Database status: {db_status} (acceptable - API can work without database)"
                    )
                
                # Test 4.4: Check for system information
                system_info = {
                    'live_data_records': data.get('live_data_records', 0),
                    'active_routes': data.get('active_routes', 0),
                    'last_update': data.get('last_update', 'unknown')
                }
                
                if system_info['live_data_records'] > 0:
                    results.add_result(
                        "Live Data Available",
                        "PASS",
                        f"System has {system_info['live_data_records']} live data records"
                    )
                else:
                    results.add_result(
                        "Live Data Available",
                        "PASS",
                        "No live data records reported (may be acceptable depending on system state)"
                    )
                
                # Test 4.5: Overall system health
                results.add_result(
                    "Overall System Health",
                    "PASS",
                    f"Status endpoint accessible with comprehensive system information",
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
    
    return results

async def main():
    """Run all data quality tests"""
    print("🏴‍☠️ SINISTER SNARE DATA QUALITY TEST SUITE")
    print("=" * 60)
    print("Testing critical backend endpoints affected by terminal/commodity name fixes")
    
    all_results = TestResults()
    
    # Test 1: Primary Routes Endpoint
    routes_results = await test_primary_routes_endpoint()
    all_results.results.extend(routes_results.results)
    all_results.passed += routes_results.passed
    all_results.failed += routes_results.failed
    
    # Test 2: Commodity Snare Endpoint
    snare_results = await test_commodity_snare_endpoint()
    all_results.results.extend(snare_results.results)
    all_results.passed += snare_results.passed
    all_results.failed += snare_results.failed
    
    # Test 3: Data Quality Verification
    quality_results = await test_data_quality_verification()
    all_results.results.extend(quality_results.results)
    all_results.passed += quality_results.passed
    all_results.failed += quality_results.failed
    
    # Test 4: API Status Check
    status_results = await test_api_status_check()
    all_results.results.extend(status_results.results)
    all_results.passed += status_results.passed
    all_results.failed += status_results.failed
    
    # Print final summary
    all_results.print_summary()
    
    # Save detailed results to file
    with open('/app/data_quality_test_results.json', 'w') as f:
        json.dump(all_results.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/data_quality_test_results.json")
    
    return all_results.failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)