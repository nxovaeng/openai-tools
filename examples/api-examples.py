#!/usr/bin/env python3
"""
API Usage Examples for Xray + Nginx OpenAPI Server

This file demonstrates how to use the API programmatically.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Change this to your actual API key

# Headers
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


# Example 1: Get API Information
def example_api_info():
    """Get API information"""
    response = requests.get(f"{BASE_URL}/")
    print_response("Example 1: API Information", response)


# Example 2: Health Check
def example_health_check():
    """Check API health"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Example 2: Health Check", response)


# Example 3: Add Xray Service
def example_add_xray_service():
    """Add a new Xray VLESS+XHTTP service"""
    data = {
        "domain": "proxy.example.com",
        "xray_port": 10000,
        "xray_path": None,  # Auto-generate
        "cdn_host": None
    }
    
    response = requests.post(
        f"{BASE_URL}/nginx/xray",
        json=data,
        headers=headers
    )
    print_response("Example 3: Add Xray Service", response)


# Example 4: Add Web Service
def example_add_web_service():
    """Add a web service or API"""
    data = {
        "domain": "api.example.com",
        "backend_port": 3000,
        "service_name": "My API Service",
        "enable_websocket": False,
        "enable_gzip": True,
        "client_max_body_size": "50M"
    }
    
    response = requests.post(
        f"{BASE_URL}/nginx/web",
        json=data,
        headers=headers
    )
    print_response("Example 4: Add Web Service", response)


# Example 5: List All Services
def example_list_services():
    """List all configured services"""
    response = requests.get(
        f"{BASE_URL}/nginx/services",
        headers=headers
    )
    print_response("Example 5: List Services", response)


# Example 6: Test Nginx Configuration
def example_test_nginx():
    """Test Nginx configuration syntax"""
    response = requests.get(
        f"{BASE_URL}/nginx/test",
        headers=headers
    )
    print_response("Example 6: Test Nginx Configuration", response)


# Example 7: Reload Nginx
def example_reload_nginx():
    """Reload Nginx configuration"""
    response = requests.post(
        f"{BASE_URL}/nginx/reload",
        headers=headers
    )
    print_response("Example 7: Reload Nginx", response)


# Example 8: Get Subscription Link
def example_get_subscription():
    """Get VLESS subscription link"""
    response = requests.get(
        f"{BASE_URL}/subscription?format=base64"
    )
    print_response("Example 8: Get Subscription", response)


# Example 9: Get Service Status
def example_get_status():
    """Get service status"""
    response = requests.get(
        f"{BASE_URL}/status",
        headers=headers
    )
    print_response("Example 9: Service Status", response)


# Example 10: Remove Service
def example_remove_service():
    """Remove a service configuration"""
    config_name = "xray-proxy-example-com.conf"
    
    response = requests.delete(
        f"{BASE_URL}/nginx/services/{config_name}",
        headers=headers
    )
    print_response("Example 10: Remove Service", response)


# Example 11: Add Xray Service with CDN
def example_add_xray_with_cdn():
    """Add Xray service with CDN configuration"""
    data = {
        "domain": "proxy.example.com",
        "xray_port": 10000,
        "cdn_host": "cdn.example.com"
    }
    
    response = requests.post(
        f"{BASE_URL}/nginx/xray",
        json=data,
        headers=headers
    )
    print_response("Example 11: Add Xray with CDN", response)


# Example 12: Add Web Service with WebSocket
def example_add_websocket_service():
    """Add web service with WebSocket support"""
    data = {
        "domain": "ws.example.com",
        "backend_port": 5000,
        "service_name": "WebSocket Service",
        "enable_websocket": True,
        "enable_gzip": True
    }
    
    response = requests.post(
        f"{BASE_URL}/nginx/web",
        json=data,
        headers=headers
    )
    print_response("Example 12: Add WebSocket Service", response)


def main():
    """Run all examples"""
    print("🧪 Xray + Nginx OpenAPI Server - API Examples")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {'*' * len(API_KEY)}")
    
    # Run examples
    examples = [
        ("API Information", example_api_info),
        ("Health Check", example_health_check),
        ("List Services", example_list_services),
        ("Test Nginx", example_test_nginx),
        ("Get Subscription", example_get_subscription),
        ("Get Status", example_get_status),
        
        # Uncomment to test write operations:
        # ("Add Xray Service", example_add_xray_service),
        # ("Add Web Service", example_add_web_service),
        # ("Add Xray with CDN", example_add_xray_with_cdn),
        # ("Add WebSocket Service", example_add_websocket_service),
        # ("Reload Nginx", example_reload_nginx),
        # ("Remove Service", example_remove_service),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✅ Examples completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
