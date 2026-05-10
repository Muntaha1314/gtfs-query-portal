"""
Test script for GTFS Route Planning API
Tests all endpoints and validates responses
"""

import requests
import json
import sys
from typing import Optional, List, Dict, Any

# API Base URL - update if running on different host/port
BASE_URL = "http://localhost:8000"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


def print_test(text: str):
    """Print test name"""
    print(f"{Colors.BLUE}▶ {text}{Colors.ENDC}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.ENDC}")


def make_request(method: str, endpoint: str, params: Optional[Dict] = None, 
                 expected_status: int = 200) -> Optional[Dict[str, Any]]:
    """
    Make HTTP request and validate response
    
    Returns:
        Response JSON or None if request failed
    """
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        else:
            response = requests.request(method, url, params=params, timeout=5)
        
        if response.status_code == expected_status:
            print_success(f"{method} {endpoint} -> {response.status_code}")
            return response.json()
        else:
            print_error(f"{method} {endpoint} -> {response.status_code} (expected {expected_status})")
            if response.text:
                print_info(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"Connection refused. Is the API running at {BASE_URL}?")
        return None
    except requests.exceptions.Timeout:
        print_error(f"Request timeout")
        return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def test_health():
    """Test health endpoint"""
    print_test("Health Check")
    result = make_request("GET", "/health")
    if result:
        if result.get("status") == "healthy":
            print_success("Database connection is healthy")
        else:
            print_error("Database connection is unhealthy")
        return True
    return False


def test_root():
    """Test root endpoint"""
    print_test("Root Endpoint")
    result = make_request("GET", "/")
    if result:
        print_success(f"API version: {result.get('version', 'unknown')}")
        print_success(f"Message: {result.get('message', 'N/A')}")
        return True
    return False


def test_get_stops():
    """Test GET /stops endpoint"""
    print_test("Get Stops (limit=10)")
    result = make_request("GET", "/api/stops", {"limit": 10})
    if result:
        count = result.get("count", 0)
        print_success(f"Retrieved {count} stops")
        
        if result.get("stops"):
            first_stop = result["stops"][0]
            print_info(f"First stop: {first_stop.get('stop_name')} ({first_stop.get('stop_id')})")
            print_info(f"Location: {first_stop.get('stop_lat')}, {first_stop.get('stop_lon')}")
            return True, first_stop.get("stop_id")
        
    return False, None


def test_get_stop_detail(stop_id: str):
    """Test GET /stops/{stop_id} endpoint"""
    print_test(f"Get Stop Detail ({stop_id})")
    result = make_request("GET", f"/api/stops/{stop_id}")
    if result:
        print_success(f"Stop: {result.get('stop_name', 'N/A')}")
        print_info(f"Code: {result.get('stop_code', 'N/A')}")
        print_info(f"Description: {result.get('stop_desc', 'N/A')}")
        return True
    return False


def test_nearby_stops():
    """Test GET /stops/nearby endpoint"""
    print_test("Get Nearby Stops (lat=40.7128, lon=-74.0060, radius=1000)")
    result = make_request("GET", "/api/stops/nearby", {
        "lat": 40.7128,
        "lon": -74.0060,
        "radius": 1000
    })
    if result:
        count = result.get("count", 0)
        print_success(f"Found {count} stops within 1000m")
        
        if result.get("stops"):
            for i, stop in enumerate(result["stops"][:3]):
                dist = stop.get("distance_meters", 0)
                print_info(f"  {i+1}. {stop.get('stop_name')} - {dist:.0f}m away")
            return True, result["stops"]
        
    return False, None


def test_get_routes():
    """Test GET /routes endpoint"""
    print_test("Get Routes (limit=10)")
    result = make_request("GET", "/api/routes", {"limit": 10})
    if result:
        count = result.get("count", 0)
        print_success(f"Retrieved {count} routes")
        
        if result.get("routes"):
            for i, route in enumerate(result["routes"][:3]):
                print_info(f"  {i+1}. {route.get('route_short_name', 'N/A')} - {route.get('route_long_name', 'N/A')}")
            return True, result["routes"]
        
    return False, None


def test_find_route(start_id: str, end_id: str):
    """Test GET /route endpoint"""
    print_test(f"Find Route ({start_id} -> {end_id})")
    result = make_request("GET", "/api/route", {
        "start": start_id,
        "end": end_id
    })
    if result:
        found = result.get("path_found", False)
        if found:
            path_stops = result.get("path", [])
            distance = result.get("distance_meters", 0)
            print_success(f"Route found with {len(path_stops)} stops")
            print_info(f"Distance: {distance:,.0f}m")
            
            for i, stop in enumerate(path_stops[:5]):
                print_info(f"  {i+1}. {stop.get('stop_name')} (seq {stop.get('sequence')})")
            
            if len(path_stops) > 5:
                print_info(f"  ... and {len(path_stops) - 5} more stops")
        else:
            print_info("No direct route found between these stops")
        return True
    return False


def test_invalid_stop():
    """Test error handling with invalid stop"""
    print_test("Get Non-existent Stop (error handling)")
    result = make_request("GET", "/api/stops/INVALID_STOP_ID", 
                         expected_status=404)
    if result is None:
        print_success("API correctly returns 404 for non-existent stop")
        return True
    return False


def test_invalid_parameters():
    """Test error handling with invalid parameters"""
    print_test("Get Stops with Invalid Latitude (error handling)")
    result = make_request("GET", "/api/stops/nearby", {
        "lat": 999.0,  # Invalid latitude
        "lon": -74.0060,
        "radius": 1000
    }, expected_status=422)
    if result is None:
        print_success("API correctly returns 422 for invalid parameters")
        return True
    return False


def run_all_tests():
    """Run all tests"""
    print_header("GTFS Route Planning API - Test Suite")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    if test_health():
        tests_passed += 1
    else:
        tests_failed += 1
        return  # Stop if no connection
    
    print()
    
    # Test 2: Root endpoint
    if test_root():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Test 3: Get stops
    stops_ok, first_stop_id = test_get_stops()
    if stops_ok:
        tests_passed += 1
    else:
        tests_failed += 1
        return
    
    print()
    
    # Test 4: Get stop detail
    if first_stop_id and test_get_stop_detail(first_stop_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Test 5: Get nearby stops
    nearby_ok, nearby_stops = test_nearby_stops()
    if nearby_ok:
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Test 6: Get routes
    routes_ok, routes = test_get_routes()
    if routes_ok:
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Test 7: Find route (if we have at least 2 different stops)
    if nearby_stops and len(nearby_stops) >= 2:
        start_stop = nearby_stops[0].get("stop_id")
        end_stop = nearby_stops[1].get("stop_id")
        if test_find_route(start_stop, end_stop):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        print_test("Find Route (skipped - need at least 2 nearby stops)")
    
    print()
    
    # Test 8: Error handling - invalid stop
    if test_invalid_stop():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Test 9: Error handling - invalid parameters
    if test_invalid_parameters():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print()
    
    # Summary
    print_header("Test Summary")
    
    total_tests = tests_passed + tests_failed
    
    if tests_passed > 0:
        print_success(f"Passed: {tests_passed}/{total_tests}")
    
    if tests_failed > 0:
        print_error(f"Failed: {tests_failed}/{total_tests}")
    
    if tests_failed == 0:
        print_header("✓ All Tests Passed!")
        print(f"{Colors.GREEN}{Colors.BOLD}The API is working correctly!{Colors.ENDC}\n")
        return 0
    else:
        print_header("✗ Some Tests Failed")
        print(f"{Colors.RED}{Colors.BOLD}Please check the errors above.{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code if exit_code is not None else 0)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.ENDC}")
        sys.exit(1)
