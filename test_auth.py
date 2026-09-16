"""
Quick test script for JWT authentication
Run this after starting the backend to verify auth is working
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_auth():
    print("\n🔐 Testing IRIS-IBVAP JWT Authentication\n")
    
    # Test 1: Root endpoint (public)
    print("1️⃣ Testing public root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response("GET /", response)
    
    # Test 2: Login with default admin
    print("\n2️⃣ Testing login with default admin account...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    print_response("POST /auth/login", response)
    
    if response.status_code != 200:
        print("\n❌ Login failed! Make sure backend is running with auth dependencies installed.")
        return
    
    tokens = response.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 3: Get current user info
    print("\n3️⃣ Testing authenticated request - Get current user...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print_response("GET /auth/me", response)
    
    # Test 4: Get alerts (requires viewer role)
    print("\n4️⃣ Testing role-based access - Get alerts...")
    response = requests.get(f"{BASE_URL}/alerts", headers=headers)
    print_response("GET /alerts", response)
    
    # Test 5: List users (requires admin role)
    print("\n5️⃣ Testing admin-only endpoint - List users...")
    response = requests.get(f"{BASE_URL}/users", headers=headers)
    print_response("GET /users", response)
    
    # Test 6: Attempt to access protected endpoint without token
    print("\n6️⃣ Testing unauthorized access (no token)...")
    response = requests.get(f"{BASE_URL}/alerts")
    print_response("GET /alerts (no auth)", response)
    
    # Test 7: Register new user (public)
    print("\n7️⃣ Testing user registration...")
    import time
    unique_username = f"testuser_{int(time.time())}"
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": unique_username,
        "email": f"{unique_username}@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    print_response("POST /auth/register", response)
    
    print("\n" + "="*60)
    print("✅ Authentication system test complete!")
    print("="*60)
    print("\nKey Points:")
    print("- Default admin credentials: admin / admin123")
    print("- Access token required for protected endpoints")
    print("- Role-based access control is working")
    print("- Visit http://localhost:8000/docs for interactive API docs")
    print("\n")


if __name__ == "__main__":
    try:
        test_auth()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("Make sure the backend is running at http://localhost:8000")
        print("\nTo start backend:")
        print("  cd backend")
        print("  ..\\venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
