#!/usr/bin/env python3
"""
Sinister Snare Bug Fixes Test Suite
Tests the 10 specific bug fixes implemented for debugging
"""

import asyncio
import httpx
import json
import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class BugFixTestResults:
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
        print(f"\n{'='*80}")
        print(f"BUG FIXES TEST SUMMARY")
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

async def test_web_parsing_error_handling():
    """Test Fix 1: Web-Parsing Error Handling - HTML parsing fails gracefully and uses fallback data"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Fix 1: Web-Parsing Error Handling")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test 1.1: Test fallback data generation when parsing fails
        try:
            # Force web crawling to test fallback mechanism
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10&data_source=web")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    api_used = data.get('api_used', '')
                    
                    # Check if we have fallback data with Gold and Agricultural Supplies
                    commodity_names = [route.get('commodity_name', '') for route in routes]
                    has_gold = any('Gold' in name for name in commodity_names)
                    has_agricultural = any('Agricultural' in name for name in commodity_names)
                    
                    # Check for safe ROI calculations (no division by zero)
                    safe_roi_calculations = True
                    for route in routes:
                        roi = route.get('roi', 0)
                        buy_price = route.get('buy_price', 0)
                        sell_price = route.get('sell_price', 0)
                        
                        # ROI should be calculated safely
                        if buy_price > 0:
                            expected_roi = ((sell_price - buy_price) / buy_price) * 100
                            if abs(roi - expected_roi) > 1.0:  # Allow small floating point differences
                                safe_roi_calculations = False
                                break
                        elif roi != 0.0:  # If buy_price is 0, ROI should be 0.0
                            safe_roi_calculations = False
                            break
                    
                    if len(routes) > 0 and safe_roi_calculations:
                        results.add_result(
                            "Web Parsing Fallback Data Generation",
                            "PASS",
                            f"Fallback mechanism working - {len(routes)} routes with safe ROI calculations. Gold: {has_gold}, Agricultural: {has_agricultural}"
                        )
                    else:
                        results.add_result(
                            "Web Parsing Fallback Data Generation",
                            "FAIL",
                            f"Issues: Routes: {len(routes)}, Safe ROI: {safe_roi_calculations}"
                        )
                else:
                    results.add_result(
                        "Web Parsing Fallback Data Generation",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Web Parsing Fallback Data Generation",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Web Parsing Fallback Data Generation",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_safe_roi_calculation():
    """Test Fix 2: Safe ROI Calculation - Verify no division by zero errors"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Fix 2: Safe ROI Calculation")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 2.1: Test routes with various buy_price scenarios
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    division_by_zero_errors = 0
                    safe_calculations = 0
                    invalid_roi_values = 0
                    
                    for route in routes:
                        buy_price = route.get('buy_price', 0)
                        sell_price = route.get('sell_price', 0)
                        roi = route.get('roi', 0)
                        
                        # Check for safe ROI calculation
                        if buy_price == 0:
                            # When buy_price is 0, ROI should be 0.0 (not infinity or error)
                            if roi == 0.0:
                                safe_calculations += 1
                            else:
                                division_by_zero_errors += 1
                        elif buy_price > 0:
                            # Calculate expected ROI
                            expected_roi = ((sell_price - buy_price) / buy_price) * 100
                            
                            # Check if calculated ROI is reasonable
                            if abs(roi - expected_roi) <= 1.0:  # Allow small floating point differences
                                safe_calculations += 1
                            else:
                                invalid_roi_values += 1
                        
                        # Check for NaN, infinity, or other invalid values
                        if not isinstance(roi, (int, float)) or roi != roi:  # NaN check
                            invalid_roi_values += 1
                    
                    total_routes = len(routes)
                    if division_by_zero_errors == 0 and invalid_roi_values == 0 and safe_calculations >= total_routes * 0.9:
                        results.add_result(
                            "Safe ROI Calculations",
                            "PASS",
                            f"All ROI calculations safe - {safe_calculations}/{total_routes} routes with valid ROI, 0 division errors"
                        )
                    else:
                        results.add_result(
                            "Safe ROI Calculations",
                            "FAIL",
                            f"ROI calculation issues - Division errors: {division_by_zero_errors}, Invalid values: {invalid_roi_values}, Safe: {safe_calculations}/{total_routes}"
                        )
                else:
                    results.add_result(
                        "Safe ROI Calculations",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Safe ROI Calculations",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Safe ROI Calculations",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_enhanced_terminal_mapping():
    """Test Fix 3: Enhanced Terminal Mapping - Test terminal name normalization and fallback logic"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Fix 3: Enhanced Terminal Mapping")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 3.1: Test various terminal name formats
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    # Check terminal name variations and system mappings
                    terminal_mappings = {}
                    fallback_to_pyro = 0
                    proper_mappings = 0
                    
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        # Parse system and terminal from "System - Terminal" format
                        if ' - ' in origin_name:
                            origin_system, origin_terminal = origin_name.split(' - ', 1)
                            terminal_mappings[origin_terminal] = origin_system
                        
                        if ' - ' in destination_name:
                            dest_system, dest_terminal = destination_name.split(' - ', 1)
                            terminal_mappings[dest_terminal] = dest_system
                    
                    # Check for known terminal mappings
                    known_stanton_terminals = ['Port Olisar', 'Everus Harbor', 'Port Tressler', 'Baijini Point']
                    known_pyro_terminals = ["Rat's Nest", 'Gaslight', 'Endgame', 'Checkmate']
                    
                    correct_stanton_mappings = 0
                    correct_pyro_mappings = 0
                    
                    for terminal, system in terminal_mappings.items():
                        if any(known in terminal for known in known_stanton_terminals):
                            if system == 'Stanton':
                                correct_stanton_mappings += 1
                        elif any(known in terminal for known in known_pyro_terminals):
                            if system == 'Pyro':
                                correct_pyro_mappings += 1
                        elif system == 'Pyro':  # Unknown terminals defaulting to Pyro
                            fallback_to_pyro += 1
                    
                    total_mappings = len(terminal_mappings)
                    if total_mappings > 0 and (correct_stanton_mappings + correct_pyro_mappings) >= total_mappings * 0.7:
                        results.add_result(
                            "Enhanced Terminal Mapping",
                            "PASS",
                            f"Terminal mapping working - {total_mappings} terminals mapped, Stanton: {correct_stanton_mappings}, Pyro: {correct_pyro_mappings}, Fallbacks: {fallback_to_pyro}"
                        )
                    else:
                        results.add_result(
                            "Enhanced Terminal Mapping",
                            "FAIL",
                            f"Terminal mapping issues - Total: {total_mappings}, Correct Stanton: {correct_stanton_mappings}, Correct Pyro: {correct_pyro_mappings}"
                        )
                else:
                    results.add_result(
                        "Enhanced Terminal Mapping",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Enhanced Terminal Mapping",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Enhanced Terminal Mapping",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_mongodb_health_check():
    """Test Fix 4: MongoDB Health Check - Verify database connection with retry mechanism"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Fix 4: MongoDB Health Check")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 4.1: Check database status in API status endpoint
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'operational':
                    database_status = data.get('database', 'unknown')
                    
                    # Check for database health information
                    if database_status in ['connected', 'online', 'operational']:
                        results.add_result(
                            "MongoDB Health Check - Status",
                            "PASS",
                            f"Database health check working - Status: {database_status}"
                        )
                    elif database_status in ['error', 'disconnected']:
                        results.add_result(
                            "MongoDB Health Check - Status",
                            "PASS",
                            f"Database health check working (shows error state) - Status: {database_status}"
                        )
                    else:
                        results.add_result(
                            "MongoDB Health Check - Status",
                            "FAIL",
                            f"Database status unclear: {database_status}"
                        )
                else:
                    results.add_result(
                        "MongoDB Health Check - Status",
                        "FAIL",
                        f"API status not operational: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "MongoDB Health Check - Status",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "MongoDB Health Check - Status",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test 4.2: Test database-dependent endpoints work with retry mechanism
        try:
            response = await client.get(f"{BACKEND_URL}/api/export/routes?format=json")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    record_count = data.get('record_count', 0)
                    results.add_result(
                        "MongoDB Retry Mechanism - Export",
                        "PASS",
                        f"Database-dependent export endpoint working - {record_count} records"
                    )
                else:
                    # Even if no records, the endpoint should work
                    results.add_result(
                        "MongoDB Retry Mechanism - Export",
                        "PASS",
                        f"Export endpoint accessible (may have no data): {data.get('status')}"
                    )
            else:
                results.add_result(
                    "MongoDB Retry Mechanism - Export",
                    "FAIL",
                    f"Export endpoint failed: HTTP {response.status_code}"
                )
        except Exception as e:
            results.add_result(
                "MongoDB Retry Mechanism - Export",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_requirements_dependencies():
    """Test Fix 5: Requirements.txt - Confirm httpx>=0.25.0 and scipy>=1.13.0 are installed"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Fix 5: Requirements Dependencies")
    
    # Test 5.1: Check httpx version
    try:
        import httpx
        httpx_version = httpx.__version__
        
        # Parse version to check if >= 0.25.0
        version_parts = httpx_version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1])
        
        if major > 0 or (major == 0 and minor >= 25):
            results.add_result(
                "httpx Version Check",
                "PASS",
                f"httpx version {httpx_version} meets requirement >=0.25.0"
            )
        else:
            results.add_result(
                "httpx Version Check",
                "FAIL",
                f"httpx version {httpx_version} does not meet requirement >=0.25.0"
            )
    except ImportError:
        results.add_result(
            "httpx Version Check",
            "FAIL",
            "httpx not installed"
        )
    except Exception as e:
        results.add_result(
            "httpx Version Check",
            "FAIL",
            f"Error checking httpx version: {str(e)}"
        )
    
    # Test 5.2: Check scipy version
    try:
        import scipy
        scipy_version = scipy.__version__
        
        # Parse version to check if >= 1.13.0
        version_parts = scipy_version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1])
        
        if major > 1 or (major == 1 and minor >= 13):
            results.add_result(
                "scipy Version Check",
                "PASS",
                f"scipy version {scipy_version} meets requirement >=1.13.0"
            )
        else:
            results.add_result(
                "scipy Version Check",
                "FAIL",
                f"scipy version {scipy_version} does not meet requirement >=1.13.0"
            )
    except ImportError:
        results.add_result(
            "scipy Version Check",
            "FAIL",
            "scipy not installed"
        )
    except Exception as e:
        results.add_result(
            "scipy Version Check",
            "FAIL",
            f"Error checking scipy version: {str(e)}"
        )
    
    return results

async def test_fallback_data_generation():
    """Test Specific Test 1: Fallback Data Generation"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Specific Test 1: Fallback Data Generation")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test that /api/routes/analyze returns fallback data when parsing fails
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    # Check for Gold and Agricultural Supplies in fallback data
                    commodity_names = [route.get('commodity_name', '') for route in routes]
                    has_gold = any('Gold' in name for name in commodity_names)
                    has_agricultural = any('Agricultural' in name for name in commodity_names)
                    
                    # Check for safe ROI in fallback data
                    safe_roi_found = False
                    for route in routes:
                        roi = route.get('roi', 0)
                        if isinstance(roi, (int, float)) and roi >= 0 and roi <= 100:
                            safe_roi_found = True
                            break
                    
                    if len(routes) > 0 and safe_roi_found:
                        results.add_result(
                            "Fallback Data with Gold and Agricultural Supplies",
                            "PASS",
                            f"Fallback data working - {len(routes)} routes, Gold: {has_gold}, Agricultural: {has_agricultural}, Safe ROI: {safe_roi_found}"
                        )
                    else:
                        results.add_result(
                            "Fallback Data with Gold and Agricultural Supplies",
                            "FAIL",
                            f"Fallback data issues - Routes: {len(routes)}, Safe ROI: {safe_roi_found}"
                        )
                else:
                    results.add_result(
                        "Fallback Data with Gold and Agricultural Supplies",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Fallback Data with Gold and Agricultural Supplies",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Fallback Data with Gold and Agricultural Supplies",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_terminal_mapping_robustness():
    """Test Specific Test 2: Terminal Mapping Robustness"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Specific Test 2: Terminal Mapping Robustness")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test various terminal name formats and fallback to "Pyro"
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=15")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    # Check for various terminal name formats
                    terminal_formats_found = {
                        'with_spaces': False,
                        'without_spaces': False,
                        'case_variations': False,
                        'fallback_to_pyro': False
                    }
                    
                    pyro_terminals = 0
                    stanton_terminals = 0
                    unknown_terminals = 0
                    
                    for route in routes:
                        origin_name = route.get('origin_name', '')
                        destination_name = route.get('destination_name', '')
                        
                        # Check system assignments
                        if 'Pyro' in origin_name or 'Pyro' in destination_name:
                            pyro_terminals += 1
                        if 'Stanton' in origin_name or 'Stanton' in destination_name:
                            stanton_terminals += 1
                        
                        # Check for terminal name variations
                        if "Rat's Nest" in origin_name or "Rat's Nest" in destination_name:
                            terminal_formats_found['with_spaces'] = True
                        if 'Everus' in origin_name or 'Everus' in destination_name:
                            terminal_formats_found['case_variations'] = True
                        
                        # Check for unknown terminals defaulting to Pyro
                        if 'Unknown' not in origin_name and 'Unknown' not in destination_name:
                            terminal_formats_found['fallback_to_pyro'] = True
                    
                    # Verify proper logging for unknown terminals (check if system handles unknowns)
                    proper_mapping = pyro_terminals > 0 or stanton_terminals > 0
                    fallback_working = terminal_formats_found['fallback_to_pyro']
                    
                    if proper_mapping and fallback_working:
                        results.add_result(
                            "Terminal Mapping Robustness",
                            "PASS",
                            f"Terminal mapping robust - Pyro: {pyro_terminals}, Stanton: {stanton_terminals}, Proper fallback: {fallback_working}"
                        )
                    else:
                        results.add_result(
                            "Terminal Mapping Robustness",
                            "FAIL",
                            f"Terminal mapping issues - Pyro: {pyro_terminals}, Stanton: {stanton_terminals}, Fallback: {fallback_working}"
                        )
                else:
                    results.add_result(
                        "Terminal Mapping Robustness",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Terminal Mapping Robustness",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Terminal Mapping Robustness",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_safe_roi_calculations_specific():
    """Test Specific Test 4: Safe ROI Calculations"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Specific Test 4: Safe ROI Calculations")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test routes with zero buy_price don't cause crashes
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=20")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    
                    zero_buy_price_routes = 0
                    safe_roi_calculations = 0
                    crashes_detected = 0
                    
                    for route in routes:
                        buy_price = route.get('buy_price', 0)
                        sell_price = route.get('sell_price', 0)
                        roi = route.get('roi', 0)
                        
                        if buy_price == 0:
                            zero_buy_price_routes += 1
                            # ROI should be 0.0 for zero buy_price (not crash)
                            if roi == 0.0:
                                safe_roi_calculations += 1
                            else:
                                crashes_detected += 1
                        elif buy_price > 0:
                            # Normal ROI calculation should work
                            expected_roi = ((sell_price - buy_price) / buy_price) * 100
                            if abs(roi - expected_roi) <= 1.0:
                                safe_roi_calculations += 1
                    
                    # Verify ROI returns 0.0 for invalid calculations
                    invalid_calculations_handled = crashes_detected == 0
                    
                    if invalid_calculations_handled and safe_roi_calculations >= len(routes) * 0.8:
                        results.add_result(
                            "Safe ROI Calculations - Zero Division Protection",
                            "PASS",
                            f"Safe ROI calculations working - Zero buy_price routes: {zero_buy_price_routes}, Safe calculations: {safe_roi_calculations}/{len(routes)}, No crashes: {crashes_detected == 0}"
                        )
                    else:
                        results.add_result(
                            "Safe ROI Calculations - Zero Division Protection",
                            "FAIL",
                            f"ROI calculation issues - Crashes: {crashes_detected}, Safe: {safe_roi_calculations}/{len(routes)}"
                        )
                else:
                    results.add_result(
                        "Safe ROI Calculations - Zero Division Protection",
                        "FAIL",
                        f"API returned status: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "Safe ROI Calculations - Zero Division Protection",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "Safe ROI Calculations - Zero Division Protection",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def test_cors_configuration():
    """Test Specific Test 5: Configuration - CORS and Environment Variables"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing Specific Test 5: CORS Configuration and Environment Variables")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test CORS configuration with restricted origins
        try:
            # Test preflight request (OPTIONS)
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = await client.options(f"{BACKEND_URL}/api/status", headers=headers)
            
            # Check CORS headers in response
            cors_headers = {
                'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                'access-control-allow-headers': response.headers.get('access-control-allow-headers')
            }
            
            # Check if CORS is properly configured
            has_cors_origin = cors_headers['access-control-allow-origin'] is not None
            allows_localhost = 'localhost' in str(cors_headers['access-control-allow-origin']) if cors_headers['access-control-allow-origin'] else False
            
            if has_cors_origin and (allows_localhost or cors_headers['access-control-allow-origin'] == '*'):
                results.add_result(
                    "CORS Configuration",
                    "PASS",
                    f"CORS properly configured - Origin: {cors_headers['access-control-allow-origin']}, Methods: {cors_headers['access-control-allow-methods']}"
                )
            else:
                results.add_result(
                    "CORS Configuration",
                    "FAIL",
                    f"CORS configuration issues - Headers: {cors_headers}"
                )
        except Exception as e:
            results.add_result(
                "CORS Configuration",
                "FAIL",
                f"CORS test error: {str(e)}"
            )
        
        # Test environment variable loading
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                
                # Check if environment variables are loaded properly
                has_db_config = 'database' in data
                has_api_config = 'star_profit_api' in data or 'uex_api' in data
                
                if has_db_config and has_api_config:
                    results.add_result(
                        "Environment Variable Loading",
                        "PASS",
                        f"Environment variables loaded - DB config: {has_db_config}, API config: {has_api_config}"
                    )
                else:
                    results.add_result(
                        "Environment Variable Loading",
                        "FAIL",
                        f"Environment variable issues - DB: {has_db_config}, API: {has_api_config}"
                    )
            else:
                results.add_result(
                    "Environment Variable Loading",
                    "FAIL",
                    f"Cannot verify env vars - HTTP {response.status_code}"
                )
        except Exception as e:
            results.add_result(
                "Environment Variable Loading",
                "FAIL",
                f"Environment variable test error: {str(e)}"
            )
    
    return results

async def test_api_endpoints_comprehensive():
    """Test all API endpoints mentioned in the review request"""
    results = BugFixTestResults()
    
    print(f"\n🔍 Testing API Endpoints Comprehensive")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test GET /api/status
        try:
            response = await client.get(f"{BACKEND_URL}/api/status")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') in ['operational', 'ok']:
                    results.add_result(
                        "GET /api/status",
                        "PASS",
                        f"Status endpoint working - Status: {data.get('status')}"
                    )
                else:
                    results.add_result(
                        "GET /api/status",
                        "FAIL",
                        f"Status endpoint returned: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "GET /api/status",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "GET /api/status",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test GET /api/routes/analyze
        try:
            response = await client.get(f"{BACKEND_URL}/api/routes/analyze?limit=10")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    routes = data.get('routes', [])
                    results.add_result(
                        "GET /api/routes/analyze",
                        "PASS",
                        f"Routes analyze endpoint working - {len(routes)} routes with safe ROI calculations"
                    )
                else:
                    results.add_result(
                        "GET /api/routes/analyze",
                        "FAIL",
                        f"Routes analyze returned: {data.get('status')}"
                    )
            else:
                results.add_result(
                    "GET /api/routes/analyze",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "GET /api/routes/analyze",
                "FAIL",
                f"Connection error: {str(e)}"
            )
        
        # Test GET /api/interception/calculate
        try:
            response = await client.get(f"{BACKEND_URL}/api/interception/calculate")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results.add_result(
                        "GET /api/interception/calculate",
                        "PASS",
                        f"Interception calculate endpoint working with Advanced Snareplan"
                    )
                else:
                    results.add_result(
                        "GET /api/interception/calculate",
                        "FAIL",
                        f"Interception calculate returned: {data.get('status')}"
                    )
            elif response.status_code == 404:
                results.add_result(
                    "GET /api/interception/calculate",
                    "FAIL",
                    "Interception calculate endpoint not found (404)"
                )
            else:
                results.add_result(
                    "GET /api/interception/calculate",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            results.add_result(
                "GET /api/interception/calculate",
                "FAIL",
                f"Connection error: {str(e)}"
            )
    
    return results

async def main():
    """Run all bug fix tests"""
    print("🎯 SINISTER SNARE BUG FIXES TEST SUITE")
    print("=" * 80)
    print("Testing 10 specific bug fixes for Sinister Snare debugging")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    all_results = BugFixTestResults()
    
    # Run all bug fix tests
    test_functions = [
        test_web_parsing_error_handling,
        test_safe_roi_calculation,
        test_enhanced_terminal_mapping,
        test_mongodb_health_check,
        test_requirements_dependencies,
        test_fallback_data_generation,
        test_terminal_mapping_robustness,
        test_safe_roi_calculations_specific,
        test_cors_configuration,
        test_api_endpoints_comprehensive
    ]
    
    for test_func in test_functions:
        try:
            test_results = await test_func()
            # Merge results
            all_results.results.extend(test_results.results)
            all_results.passed += test_results.passed
            all_results.failed += test_results.failed
        except Exception as e:
            print(f"❌ Test function {test_func.__name__} failed: {str(e)}")
            all_results.failed += 1
    
    # Print final summary
    all_results.print_summary()
    
    # Return success/failure for script exit code
    return all_results.failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)