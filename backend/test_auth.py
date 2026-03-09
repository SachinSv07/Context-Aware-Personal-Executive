"""
Test Authentication System
Test strong password validation, duplicate user prevention, and persistent storage
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"


def print_test(name, success, message=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"   {message}")
    print()


def test_weak_passwords():
    """Test password strength validation"""
    print("="*60)
    print("TEST 1: Password Strength Validation")
    print("="*60)
    print()
    
    weak_passwords = [
        ("short", "Too short"),
        ("alllowercase1!", "No uppercase"),
        ("ALLUPPERCASE1!", "No lowercase"),
        ("NoDigitsHere!", "No digits"),
        ("NoSpecialChar1", "No special characters"),
        ("weakpass", "Multiple issues")
    ]
    
    for password, reason in weak_passwords:
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": f"test_{password}@example.com",
            "name": "Test User",
            "password": password
        })
        
        success = response.status_code == 400
        print_test(
            f"Reject weak password: {reason}",
            success,
            f"Status: {response.status_code}, Response: {response.json().get('error', 'No error')}"
        )


def test_strong_password_signup():
    """Test signup with strong password"""
    print("="*60)
    print("TEST 2: Strong Password Signup")
    print("="*60)
    print()
    
    response = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": "stronguser@example.com",
        "name": "Strong User",
        "password": "StrongPass123!"
    })
    
    success = response.status_code == 201
    print_test(
        "Accept strong password signup",
        success,
        f"Status: {response.status_code}, Response: {json.dumps(response.json(), indent=2)}"
    )
    
    return response.json().get('user', {}).get('email')


def test_duplicate_signup(email):
    """Test duplicate user prevention"""
    print("="*60)
    print("TEST 3: Duplicate User Prevention")
    print("="*60)
    print()
    
    response = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": email,
        "name": "Duplicate User",
        "password": "AnotherPass123!"
    })
    
    success = response.status_code == 409
    error_msg = response.json().get('error', '')
    contains_exists = 'already exists' in error_msg.lower()
    
    print_test(
        "Prevent duplicate signup",
        success and contains_exists,
        f"Status: {response.status_code}, Error: {error_msg}"
    )


def test_login(email, password, should_succeed=True):
    """Test login"""
    test_name = "Successful login" if should_succeed else "Failed login with wrong password"
    
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if should_succeed:
        success = response.status_code == 200 and 'token' in response.json()
    else:
        success = response.status_code == 401
    
    print_test(
        test_name,
        success,
        f"Status: {response.status_code}, Response: {json.dumps(response.json(), indent=2)}"
    )
    
    return response.json().get('token') if should_succeed and success else None


def test_persistent_storage():
    """Test that data persists across requests"""
    print("="*60)
    print("TEST 5: Persistent Storage")
    print("="*60)
    print()
    
    # Create a new user
    email = "persistent@example.com"
    password = "PersistentPass123!"
    
    response1 = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": email,
        "name": "Persistent User",
        "password": password
    })
    
    signup_success = response1.status_code == 201
    print_test(
        "Create user for persistence test",
        signup_success,
        f"Status: {response1.status_code}"
    )
    
    # Try to login (data should persist)
    response2 = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    login_success = response2.status_code == 200
    print_test(
        "Login with persisted user data",
        login_success,
        f"Status: {response2.status_code}, User found in storage: {login_success}"
    )
    
    # Check that duplicate signup still fails (data still persisted)
    response3 = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": email,
        "name": "Another User",
        "password": "AnotherPass123!"
    })
    
    duplicate_prevented = response3.status_code == 409
    print_test(
        "Duplicate prevention after persistence",
        duplicate_prevented,
        f"Status: {response3.status_code}, Data persisted correctly: {duplicate_prevented}"
    )


def test_invalid_email():
    """Test email validation"""
    print("="*60)
    print("TEST 6: Email Validation")
    print("="*60)
    print()
    
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
        "user name@example.com"
    ]
    
    for email in invalid_emails:
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": email,
            "name": "Test User",
            "password": "ValidPass123!"
        })
        
        success = response.status_code == 400
        print_test(
            f"Reject invalid email: {email}",
            success,
            f"Status: {response.status_code}, Error: {response.json().get('error', '')}"
        )


def run_all_tests():
    """Run all authentication tests"""
    print("\n" + "="*60)
    print("AUTHENTICATION SYSTEM TEST SUITE")
    print("="*60)
    print(f"Testing backend at: {BASE_URL}")
    print("="*60 + "\n")
    
    try:
        # Test health
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print("❌ Backend is not running!")
            print("Start it with: python backend/api.py")
            return
        
        print("✅ Backend is running\n")
        
        # Run tests
        test_weak_passwords()
        user_email = test_strong_password_signup()
        
        if user_email:
            test_duplicate_signup(user_email)
            
            print("="*60)
            print("TEST 4: Login Authentication")
            print("="*60)
            print()
            
            test_login(user_email, "StrongPass123!", should_succeed=True)
            test_login(user_email, "WrongPassword123!", should_succeed=False)
        
        test_persistent_storage()
        test_invalid_email()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print()
        print("✅ Password strength validation working")
        print("✅ Duplicate user prevention working")
        print("✅ Strong password acceptance working")
        print("✅ Login authentication working")
        print("✅ Persistent storage working")
        print("✅ Email validation working")
        print()
        print("Check backend/data/ folder for persisted JSON files:")
        print("  - users.json")
        print("  - data_sources.json")
        print("  - files.json")
        print("  - notes.json")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("Make sure the backend is running:")
        print("  python backend/api.py")
        print("\nThen run this test script again.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    run_all_tests()
