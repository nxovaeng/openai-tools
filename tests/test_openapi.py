#!/usr/bin/env python3
"""
Test script for OpenAPI Server
Tests all endpoints to ensure compatibility with Open WebUI
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Change this to your actual API key

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Method: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            print(f"✅ Success")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Xray + Nginx OpenAPI Server")
    print(f"Base URL: {BASE_URL}")
    
    results = []
    
    # Test 1: Root endpoint
    results.append(test_endpoint(
        "GET", "/",
        description="Root endpoint - API information"
    ))
    
    # Test 2: Health check
    results.append(test_endpoint(
        "GET", "/health",
        description="Health check"
    ))
    
    # Test 3: OpenAPI schema
    results.append(test_endpoint(
        "GET", "/openapi.json",
        description="OpenAPI schema"
    ))
    
    # Test 4: List services
    results.append(test_endpoint(
        "GET", "/nginx/services",
        description="List all Nginx services"
    ))
    
    # Test 5: Test Nginx config
    results.append(test_endpoint(
        "GET", "/nginx/test",
        description="Test Nginx configuration"
    ))
    
    # Test 6: Get subscription (may fail if no services configured)
    results.append(test_endpoint(
        "GET", "/subscription",
        description="Get subscription link"
    ))
    
    # Test 7: Get status
    results.append(test_endpoint(
        "GET", "/status",
        description="Get service status"
    ))
    
    # Test 8: Add Xray service (optional - requires valid domain)
    # Uncomment to test:
    # results.append(test_endpoint(
    #     "POST", "/nginx/xray",
    #     data={
    #         "domain": "test.example.com",
    #         "xray_port": 10000
    #     },
    #     description="Add Xray service"
    # ))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
