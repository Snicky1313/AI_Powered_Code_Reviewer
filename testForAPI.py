import requests
import json
import time

# API Gateway base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check has passed")
            print(f"   Response: {response.json()}")
        else:
            print(f" The health check failed: {response.status_code}")
    except Exception as e:
        print(f" There is a health check error: {e}")

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ The root endpoint passed")
            print(f"   Response: {response.json()}")
        else:
            print(f" Root endpoint has failed: {response.status_code}")
    except Exception as e:
        print(f" Root endpoint has an error: {e}")

def test_code_submission():
    """Test code submission"""
    print("\n🔍 Testing code submission...")
    
    # Sample  code
    sample_code = """
def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

result = calculate_factorial(5)
print(f"Factorial of 5 is: {result}")
"""
    
    submission_data = {
        "code": sample_code,
        "user_id": "test_user_123",
        "language": "python",
        "analysis_types": ["syntax", "style", "security"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/submit",
            json=submission_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Code submission passed")
            result = response.json()
            print(f"   Submission ID: {result['submission_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            return result['submission_id']
        else:
            print(f" The code submission has failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f" There was a code submission error: {e}")
        return None

def test_get_submission(submission_id):
    """Test getting submission details"""
    if not submission_id:
        return
    
    print(f"\n🔍 Testing get submission {submission_id}...")
    try:
        response = requests.get(f"{BASE_URL}/submission/{submission_id}")
        if response.status_code == 200:
            print("✅ Get submission passed")
            result = response.json()
            print(f"   User ID: {result['user_id']}")
            print(f"   Language: {result['language']}")
            print(f"   Analysis Types: {result['analysis_types']}")
        else:
            print(f" Get submission has failed: {response.status_code}")
    except Exception as e:
        print(f" There was an error getting the submission: {e}")

def test_list_submissions():
    """Test listing all submissions"""
    print("\n🔍 Testing list submissions...")
    try:
        response = requests.get(f"{BASE_URL}/submissions")
        if response.status_code == 200:
            print("✅ List submissions passed")
            result = response.json()
            print(f"   Total submissions: {result['total_submissions']}")
            print(f"   Submission IDs: {result['submissions']}")
        else:
            print(f" List submissions failed: {response.status_code}")
    except Exception as e:
        print(f" List submissions error: {e}")

def test_delete_submission(submission_id):
    """Test deleting a submission"""
    if not submission_id:
        return
    
    print(f"\n🔍 Testing delete submission {submission_id}...")
    try:
        response = requests.delete(f"{BASE_URL}/submission/{submission_id}")
        if response.status_code == 200:
            print("✅ Delete submission passed")
            print(f"   Response: {response.json()}")
        else:
            print(f" Request to delete submission failed: {response.status_code}")
    except Exception as e:
        print(f" Your request to delete submission error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting API Gateway Tests")
    print("=" * 50)
    
    #  for server to be ready
    time.sleep(2)
    
    # Run tests
    test_health_check()
    test_root_endpoint()
    submission_id = test_code_submission()
    test_get_submission(submission_id)
    test_list_submissions()
    test_delete_submission(submission_id)
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main()