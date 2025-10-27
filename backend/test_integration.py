"""
Backend Integration Test Script
Run this to verify all backend endpoints are working correctly
"""

import requests
import json

# Configuration
BACKEND_URL = "http://localhost:8000"
# BACKEND_URL = "https://cjcf4dl2-8000.inc1.devtunnels.ms"

def test_root():
    """Test root endpoint"""
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_config():
    """Test config endpoint"""
    print("\n2. Testing config endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/config")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_signup():
    """Test user signup"""
    print("\n3. Testing user signup...")
    test_user = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "testpass123"
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/users/signup",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User created: ID={data.get('id')}, Username={data.get('username')}")
            return data
        elif response.status_code == 400:
            print(f"   User already exists (OK for testing)")
            return test_user
        else:
            print(f"   Error: {response.json()}")
            return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def test_login(username, password):
    """Test user login"""
    print("\n4. Testing user login...")
    credentials = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/users/login",
            json=credentials,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Login successful: User ID={data.get('id')}")
            return data
        else:
            print(f"   Error: {response.json()}")
            return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def test_history(user_id):
    """Test getting user history"""
    print(f"\n5. Testing history endpoint for user {user_id}...")
    try:
        response = requests.get(f"{BACKEND_URL}/history/{user_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   History items: {len(data)}")
            if data:
                print(f"   Latest detection: {data[0].get('results')}")
            return True
        else:
            print(f"   Error: {response.json()}")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_detection(user_id, video_path=None):
    """Test video detection endpoint"""
    print(f"\n6. Testing detection endpoint...")
    if not video_path:
        print("   Skipping (no video file provided)")
        print("   To test: Uncomment and provide video path in script")
        return None
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BACKEND_URL}/detect/{user_id}",
                files=files
            )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Detected objects: {data}")
            return True
        else:
            print(f"   Error: {response.json()}")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("="*60)
    print("BACKEND INTEGRATION TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Root endpoint
    results.append(("Root Endpoint", test_root()))
    
    # Test 2: Config endpoint
    results.append(("Config Endpoint", test_config()))
    
    # Test 3: Signup
    user_data = test_signup()
    results.append(("User Signup", user_data is not None))
    
    if user_data:
        # Test 4: Login
        username = user_data.get('username', 'testuser123')
        password = 'testpass123'
        login_data = test_login(username, password)
        results.append(("User Login", login_data is not None))
        
        if login_data:
            user_id = login_data.get('id')
            
            # Test 5: History
            results.append(("User History", test_history(user_id)))
            
            # Test 6: Detection (optional - requires video file)
            # Uncomment and provide video path to test
            # VIDEO_PATH = "path/to/test/video.mp4"
            # results.append(("Video Detection", test_detection(user_id, VIDEO_PATH)))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    print("="*60)

if __name__ == "__main__":
    main()
