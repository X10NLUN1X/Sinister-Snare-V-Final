#!/usr/bin/env python3
"""
Comprehensive API Test for Sinister Snare Backend
Tests all endpoints mentioned in the review request
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_comprehensive_api():
    print('🔍 COMPREHENSIVE SYSTEM DEBUG - Testing All Backend APIs')
    print('='*60)
    
    BACKEND_URL = 'http://localhost:8001'
    results = []
    
    # List of all endpoints to test based on review request
    endpoints = [
        ('GET', '/api/status', 'System Status'),
        ('GET', '/api/routes/analyze', 'Routes Analysis'),
        ('GET', '/api/tracking/status', 'Tracking Status'),
        ('GET', '/api/snare/commodity?commodity_name=Aluminum', 'Snare Commodity'),
        ('GET', '/api/targets', 'Targets API'),
        ('GET', '/api/alerts', 'Alerts System'),
        ('GET', '/api/database/routes/current', 'Database Routes Current'),
        ('GET', '/api/export/routes', 'Export Routes'),
        ('POST', '/api/routes/commodity-snare', 'Commodity Snare POST'),
        ('GET', '/api/targets/priority', 'Priority Targets'),
        ('GET', '/api/analysis/hourly', 'Hourly Analysis'),
        ('GET', '/api/trends/historical', 'Historical Trends'),
        ('GET', '/api/snare/now', 'Snare Now'),
        ('GET', '/api/interception/points', 'Interception Points'),
        ('POST', '/api/refresh/manual', 'Manual Refresh'),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for method, endpoint, name in endpoints:
            try:
                print(f'\n🧪 Testing {name} ({method} {endpoint})')
                
                if method == 'GET':
                    response = await client.get(f'{BACKEND_URL}{endpoint}')
                else:
                    response = await client.post(f'{BACKEND_URL}{endpoint}')
                
                status_symbol = '✅' if response.status_code == 200 else '❌'
                print(f'{status_symbol} {name}: HTTP {response.status_code}')
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f'   Response: {str(data)[:200]}...')
                        
                        # Check for specific issues mentioned in review
                        if 'targets' in endpoint and 'status' in data:
                            if data.get('status') == 0:
                                print('   ⚠️  CRITICAL: Targets API returns status 0!')
                        
                        results.append({
                            'endpoint': endpoint,
                            'name': name,
                            'status': 'PASS',
                            'http_code': response.status_code,
                            'response_preview': str(data)[:200]
                        })
                    except json.JSONDecodeError as e:
                        print(f'   ❌ JSON Parse Error: {e}')
                        print(f'   Raw response: {response.text[:200]}')
                        results.append({
                            'endpoint': endpoint,
                            'name': name,
                            'status': 'FAIL',
                            'http_code': response.status_code,
                            'error': f'JSON Parse Error: {e}'
                        })
                else:
                    print(f'   Error: {response.text[:200]}')
                    results.append({
                        'endpoint': endpoint,
                        'name': name,
                        'status': 'FAIL',
                        'http_code': response.status_code,
                        'error': response.text[:200]
                    })
                    
            except Exception as e:
                print(f'❌ {name}: Connection error - {e}')
                results.append({
                    'endpoint': endpoint,
                    'name': name,
                    'status': 'FAIL',
                    'http_code': 0,
                    'error': str(e)
                })
    
    # Summary
    passed = len([r for r in results if r['status'] == 'PASS'])
    failed = len([r for r in results if r['status'] == 'FAIL'])
    
    print('\n' + '='*60)
    print('COMPREHENSIVE API TEST SUMMARY')
    print('='*60)
    print(f'Total Endpoints: {len(results)}')
    print(f'Passed: {passed}')
    print(f'Failed: {failed}')
    print(f'Success Rate: {(passed/len(results)*100):.1f}%')
    
    if failed > 0:
        print('\n❌ FAILED ENDPOINTS:')
        for result in results:
            if result['status'] == 'FAIL':
                print(f'  - {result["name"]}: {result.get("error", "HTTP " + str(result["http_code"]))}')
    
    return results

if __name__ == "__main__":
    asyncio.run(test_comprehensive_api())