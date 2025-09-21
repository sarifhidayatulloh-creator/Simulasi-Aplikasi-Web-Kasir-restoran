#!/usr/bin/env python3
"""
Indonesian Restaurant POS Backend API Testing
Tests authentication, menu, orders, and dashboard functionality
"""

import requests
import json
import os
from datetime import datetime
import sys

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

API_URL = f"{BASE_URL}/api"
print(f"Testing backend API at: {API_URL}")

# Test data
TEST_USERS = [
    {"username": "admin", "password": "admin123"},
    {"username": "kasir", "password": "kasir123"}
]

# Global variables for test state
auth_tokens = {}
test_results = {
    "authentication": {"passed": 0, "failed": 0, "details": []},
    "menu": {"passed": 0, "failed": 0, "details": []},
    "orders": {"passed": 0, "failed": 0, "details": []},
    "dashboard": {"passed": 0, "failed": 0, "details": []}
}

def log_test(category, test_name, passed, details=""):
    """Log test results"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    
    test_results[category]["passed" if passed else "failed"] += 1
    test_results[category]["details"].append({
        "test": test_name,
        "passed": passed,
        "details": details
    })

def test_authentication():
    """Test authentication system"""
    print("\n=== TESTING AUTHENTICATION SYSTEM ===")
    
    # Test 1: Login with valid credentials
    for user in TEST_USERS:
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json=user,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    auth_tokens[user["username"]] = data["access_token"]
                    log_test("authentication", f"Login {user['username']}", True, 
                           f"Token received, user: {data['user']['name']}")
                else:
                    log_test("authentication", f"Login {user['username']}", False, 
                           f"Missing token or user data in response: {data}")
            else:
                log_test("authentication", f"Login {user['username']}", False, 
                       f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            log_test("authentication", f"Login {user['username']}", False, f"Exception: {str(e)}")
    
    # Test 2: Login with invalid credentials
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": "invalid", "password": "wrong"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 401:
            log_test("authentication", "Invalid login rejection", True, "Correctly rejected invalid credentials")
        else:
            log_test("authentication", "Invalid login rejection", False, 
                   f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_test("authentication", "Invalid login rejection", False, f"Exception: {str(e)}")
    
    # Test 3: Profile access with token
    if "admin" in auth_tokens:
        try:
            response = requests.get(
                f"{API_URL}/auth/profile",
                headers={"Authorization": f"Bearer {auth_tokens['admin']}"},
                timeout=10
            )
            
            if response.status_code == 200:
                profile = response.json()
                log_test("authentication", "Profile access", True, 
                       f"Profile: {profile.get('name', 'Unknown')}")
            else:
                log_test("authentication", "Profile access", False, 
                       f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            log_test("authentication", "Profile access", False, f"Exception: {str(e)}")

def test_menu_system():
    """Test menu system"""
    print("\n=== TESTING MENU SYSTEM ===")
    
    # Test 1: Get all menu items
    try:
        response = requests.get(f"{API_URL}/menu", timeout=10)
        
        if response.status_code == 200:
            menu_items = response.json()
            if len(menu_items) >= 12:
                log_test("menu", "Get menu items", True, 
                       f"Found {len(menu_items)} menu items")
                
                # Check if items have required fields
                sample_item = menu_items[0]
                required_fields = ["id", "name", "description", "price", "category", "image_url"]
                missing_fields = [field for field in required_fields if field not in sample_item]
                
                if not missing_fields:
                    log_test("menu", "Menu item structure", True, "All required fields present")
                else:
                    log_test("menu", "Menu item structure", False, 
                           f"Missing fields: {missing_fields}")
            else:
                log_test("menu", "Get menu items", False, 
                       f"Expected 12+ items, got {len(menu_items)}")
        else:
            log_test("menu", "Get menu items", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("menu", "Get menu items", False, f"Exception: {str(e)}")
    
    # Test 2: Get menu categories
    try:
        response = requests.get(f"{API_URL}/menu/categories", timeout=10)
        
        if response.status_code == 200:
            categories = response.json()
            if len(categories) > 0:
                log_test("menu", "Get categories", True, 
                       f"Found {len(categories)} categories: {[cat.get('category') for cat in categories]}")
            else:
                log_test("menu", "Get categories", False, "No categories found")
        else:
            log_test("menu", "Get categories", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("menu", "Get categories", False, f"Exception: {str(e)}")

def test_order_system():
    """Test order system"""
    print("\n=== TESTING ORDER SYSTEM ===")
    
    if "kasir" not in auth_tokens:
        log_test("orders", "Order creation", False, "No kasir token available")
        return
    
    # Test 1: Create order
    test_order = {
        "items": [
            {
                "menu_item_id": "test-item-1",
                "quantity": 2,
                "price": 25000,
                "name": "Nasi Goreng Seafood"
            },
            {
                "menu_item_id": "test-item-2", 
                "quantity": 1,
                "price": 20000,
                "name": "Soto Ayam"
            }
        ],
        "total_amount": 70000,
        "cash_received": 100000,
        "cashier_id": "kasir-id",
        "cashier_name": "Kasir Utama"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/orders",
            json=test_order,
            headers={
                "Authorization": f"Bearer {auth_tokens['kasir']}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            order = response.json()
            if "id" in order and "change_amount" in order:
                expected_change = test_order["cash_received"] - test_order["total_amount"]
                if order["change_amount"] == expected_change:
                    log_test("orders", "Order creation", True, 
                           f"Order created with ID: {order['id']}, Change: {order['change_amount']}")
                else:
                    log_test("orders", "Order creation", False, 
                           f"Incorrect change calculation: expected {expected_change}, got {order['change_amount']}")
            else:
                log_test("orders", "Order creation", False, 
                       f"Missing required fields in response: {order}")
        else:
            log_test("orders", "Order creation", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("orders", "Order creation", False, f"Exception: {str(e)}")
    
    # Test 2: Get orders
    try:
        response = requests.get(f"{API_URL}/orders", timeout=10)
        
        if response.status_code == 200:
            orders = response.json()
            log_test("orders", "Get orders", True, f"Retrieved {len(orders)} orders")
        else:
            log_test("orders", "Get orders", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("orders", "Get orders", False, f"Exception: {str(e)}")

def test_dashboard_system():
    """Test dashboard system"""
    print("\n=== TESTING DASHBOARD SYSTEM ===")
    
    # Test 1: Get dashboard stats
    try:
        response = requests.get(f"{API_URL}/dashboard/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            required_keys = ["today", "all_time"]
            if all(key in stats for key in required_keys):
                log_test("dashboard", "Get dashboard stats", True, 
                       f"Today: {stats['today']}, All time: {stats['all_time']}")
            else:
                log_test("dashboard", "Get dashboard stats", False, 
                       f"Missing required keys in response: {stats}")
        else:
            log_test("dashboard", "Get dashboard stats", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("dashboard", "Get dashboard stats", False, f"Exception: {str(e)}")
    
    # Test 2: Get today's orders
    try:
        response = requests.get(f"{API_URL}/orders/today", timeout=10)
        
        if response.status_code == 200:
            today_data = response.json()
            required_keys = ["date", "total_orders", "total_revenue", "popular_items"]
            if all(key in today_data for key in required_keys):
                log_test("dashboard", "Get today orders", True, 
                       f"Date: {today_data['date']}, Orders: {today_data['total_orders']}")
            else:
                log_test("dashboard", "Get today orders", False, 
                       f"Missing required keys in response: {today_data}")
        else:
            log_test("dashboard", "Get today orders", False, 
                   f"Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        log_test("dashboard", "Get today orders", False, f"Exception: {str(e)}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for category, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total_passed += passed
        total_failed += failed
        
        status = "✅" if failed == 0 else "❌"
        print(f"{status} {category.upper()}: {passed} passed, {failed} failed")
        
        # Show failed tests
        for detail in results["details"]:
            if not detail["passed"]:
                print(f"   ❌ {detail['test']}: {detail['details']}")
    
    print("-" * 60)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total_failed} TESTS FAILED - NEEDS ATTENTION")

def main():
    """Main test execution"""
    print("Indonesian Restaurant POS Backend API Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    print("="*60)
    
    # Run all tests
    test_authentication()
    test_menu_system()
    test_order_system()
    test_dashboard_system()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()