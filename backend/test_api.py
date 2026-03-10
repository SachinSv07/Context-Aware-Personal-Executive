"""
Backend API Test Script
Run this to test all API endpoints
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5000/api"

def print_response(response, endpoint):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "GET /api/health")
    return response.status_code == 200


def test_login():
    """Test login endpoint"""
    data = {
        "email": "user@example.com",
        "password": "demo123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print_response(response, "POST /api/auth/login")
    
    if response.status_code == 200:
        return response.json().get('token')
    return None


def test_signup():
    """Test signup endpoint"""
    data = {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/auth/signup", json=data)
    print_response(response, "POST /api/auth/signup")
    return response.status_code in [200, 201]


def test_query():
    """Test query endpoint"""
    data = {
        "query": "What emails are about meetings?"
    }
    response = requests.post(f"{BASE_URL}/query", json=data)
    print_response(response, "POST /api/query")
    return response.status_code == 200


def test_user_profile():
    """Test user profile endpoint"""
    response = requests.get(f"{BASE_URL}/user/profile")
    print_response(response, "GET /api/user/profile")
    return response.status_code == 200


def test_data_sources():
    """Test data sources endpoints"""
    # Get all data sources
    response = requests.get(f"{BASE_URL}/data-sources")
    print_response(response, "GET /api/data-sources")
    
    # Connect Gmail
    data = {"email": "test@gmail.com"}
    response = requests.post(f"{BASE_URL}/data-sources/gmail/connect", json=data)
    print_response(response, "POST /api/data-sources/gmail/connect")
    
    # Connect Calendar
    response = requests.post(f"{BASE_URL}/data-sources/calendar/connect")
    print_response(response, "POST /api/data-sources/calendar/connect")
    
    # Connect Drive
    data = {
        "file_id": "test_file_123",
        "file_name": "test_document.pdf"
    }
    response = requests.post(f"{BASE_URL}/data-sources/drive/connect", json=data)
    print_response(response, "POST /api/data-sources/drive/connect")
    
    return True


def test_notes():
    """Test notes endpoints"""
    # Save a note
    data = {"content": "This is a test note"}
    response = requests.post(f"{BASE_URL}/notes", json=data)
    print_response(response, "POST /api/notes")
    
    # Get all notes
    response = requests.get(f"{BASE_URL}/notes")
    print_response(response, "GET /api/notes")
    
    # Try to delete a note (might fail if no notes exist)
    if response.status_code == 200:
        notes = response.json().get('notes', [])
        if notes:
            note_id = notes[0]['id']
            response = requests.delete(f"{BASE_URL}/notes/{note_id}")
            print_response(response, f"DELETE /api/notes/{note_id}")
    
    return True


def test_files():
    """Test file endpoints"""
    # Get all files
    response = requests.get(f"{BASE_URL}/files")
    print_response(response, "GET /api/files")
    
    # Try file upload (requires a test file)
    # Create a test file
    test_file_path = Path("test_upload.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test file for upload")
    
    # Upload file
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_upload.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/files/upload", files=files)
        print_response(response, "POST /api/files/upload")
    
    # Clean up test file
    test_file_path.unlink(missing_ok=True)
    
    # Get files again to see the uploaded file
    response = requests.get(f"{BASE_URL}/files")
    print_response(response, "GET /api/files (after upload)")
    
    # Try to delete first file
    if response.status_code == 200:
        files = response.json().get('files', [])
        if files:
            file_id = files[0]['id']
            response = requests.delete(f"{BASE_URL}/files/{file_id}")
            print_response(response, f"DELETE /api/files/{file_id}")
    
    return True


def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("BACKEND API TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    try:
        # Test health first
        print("\n[1/8] Testing Health Check...")
        if not test_health():
            print("❌ Backend is not running! Start it with: python backend/api.py")
            return
        print("✅ Health check passed")
        
        # Test authentication
        print("\n[2/8] Testing Authentication...")
        test_login()
        test_signup()
        print("✅ Authentication tests completed")
        
        # Test query
        print("\n[3/8] Testing Query Endpoint...")
        test_query()
        print("✅ Query test completed")
        
        # Test user profile
        print("\n[4/8] Testing User Profile...")
        test_user_profile()
        print("✅ User profile test completed")
        
        # Test data sources
        print("\n[5/8] Testing Data Sources...")
        test_data_sources()
        print("✅ Data sources tests completed")
        
        # Test notes
        print("\n[6/8] Testing Notes Management...")
        test_notes()
        print("✅ Notes tests completed")
        
        # Test files
        print("\n[7/8] Testing File Management...")
        test_files()
        print("✅ File tests completed")
        
        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        print("\nCheck the responses above for details.")
        print("Note: Some 404 errors for DELETE operations are expected")
        print("if no data exists in the in-memory database.")
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
