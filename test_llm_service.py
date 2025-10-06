#!/usr/bin/env python3
"""
Test script for LLM Feedback Service (Task 1.7)
Tests the LLM feedback generation with various code samples.
"""

import requests
import json
import sys
import time
from typing import Dict, Any
import io

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Configuration
LLM_SERVICE_URL = "http://localhost:5003"
API_GATEWAY_URL = "http://localhost:8000"


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result: Dict[str, Any], verbose: bool = True):
    """Print test result in a formatted way."""
    if result.get('success'):
        print("✓ SUCCESS")
        if verbose and 'feedback' in result:
            print("\n--- AI Feedback ---")
            print(result['feedback'])
            print("\n--- Summary ---")
            summary = result.get('summary', {})
            print(f"Analyzers Run: {', '.join(summary.get('analyzers_run', []))}")
            print(f"Issues by Category: {summary.get('issues_by_category', {})}")
            print(f"Overall Grade: {summary.get('overall_grade', 'N/A')}")
            if 'tokens_used' in result:
                print(f"Tokens Used: {result['tokens_used']}")
    else:
        print("✗ FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'suggestion' in result:
            print(f"Suggestion: {result['suggestion']}")


def test_health_check():
    """Test 1: Health check endpoint."""
    print_header("Test 1: Health Check")
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service is healthy")
            print(f"  Service: {data.get('service')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Model: {data.get('model')}")
            print(f"  OpenAI Configured: {data.get('openai_configured')}")
            return data.get('openai_configured', False)
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to LLM service")
        print("  Make sure the service is running: python analyzers/llm_feedback.py")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        return False


def test_api_connectivity():
    """Test 2: Test OpenAI API connectivity."""
    print_header("Test 2: OpenAI API Connectivity")
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/test", timeout=10)
        data = response.json()
        print_result(data, verbose=False)
        if data.get('success'):
            print(f"  Test Response: {data.get('test_response')}")
        return data.get('success', False)
    except Exception as e:
        print(f"✗ API connectivity test failed: {str(e)}")
        return False


def test_good_code_feedback():
    """Test 3: Generate feedback for good code."""
    print_header("Test 3: Feedback for Good Code")
    
    good_code = """def calculate_average(numbers: list) -> float:
    \"\"\"Calculate the average of a list of numbers.\"\"\"
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

# Example usage
data = [1, 2, 3, 4, 5]
result = calculate_average(data)
print(f"Average: {result}")
"""
    
    # Simulate analysis results (good code has no issues)
    analysis_results = {
        "syntax": {
            "ok": True,
            "findings": [],
            "filename": "good_code.py"
        },
        "style": {
            "success": True,
            "style_score": 95.0,
            "violations": [],
            "summary": {
                "total_violations": 0,
                "errors": 0,
                "warnings": 0,
                "grade": "A"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/feedback",
            json={
                'code': good_code,
                'analysis_results': analysis_results,
                'user_id': 'test_user',
                'submission_id': 'test_good_001'
            },
            timeout=30
        )
        
        result = response.json()
        print_result(result)
        return result.get('success', False)
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_bad_code_feedback():
    """Test 4: Generate feedback for code with issues."""
    print_header("Test 4: Feedback for Code with Issues")
    
    bad_code = """def add(a,b):
\treturn  a+ b  

if True
    print (hello')
x=1
"""
    
    # Simulate analysis results (bad code has issues)
    analysis_results = {
        "syntax": {
            "ok": False,
            "findings": [
                {
                    "id": "SYN001-4-9-1",
                    "message": "invalid syntax",
                    "location": {"start": {"line": 4, "column": 9}},
                    "suggestion": "Add a colon (:) at the end of the statement header."
                },
                {
                    "id": "SYN001-5-11-2",
                    "message": "EOL while scanning string literal",
                    "location": {"start": {"line": 5, "column": 11}},
                    "suggestion": "Close the string with matching quotes."
                }
            ],
            "filename": "bad_code.py"
        },
        "style": {
            "success": True,
            "style_score": 65.0,
            "violations": [
                {
                    "line": 1,
                    "column": 8,
                    "code": "E231",
                    "text": "missing whitespace after ','",
                    "severity": "warning"
                },
                {
                    "line": 2,
                    "column": 1,
                    "code": "E101",
                    "text": "Mixed tabs and spaces",
                    "severity": "error"
                },
                {
                    "line": 2,
                    "column": 13,
                    "code": "W291",
                    "text": "Trailing whitespace",
                    "severity": "warning"
                }
            ],
            "summary": {
                "total_violations": 3,
                "errors": 1,
                "warnings": 2,
                "grade": "D"
            }
        },
        "security": {
            "ok": True,
            "findings": [],
            "filename": "bad_code.py"
        }
    }
    
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/feedback",
            json={
                'code': bad_code,
                'analysis_results': analysis_results,
                'user_id': 'test_user',
                'submission_id': 'test_bad_001'
            },
            timeout=30
        )
        
        result = response.json()
        print_result(result)
        return result.get('success', False)
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_security_issues_feedback():
    """Test 5: Generate feedback for code with security issues."""
    print_header("Test 5: Feedback for Code with Security Issues")
    
    insecure_code = """import subprocess
import hashlib

def run_command(cmd):
    subprocess.call(cmd, shell=True)  # Security issue!

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # Weak hashing!

# Usage
run_command("ls -la")
hashed = hash_password("mypassword")
"""
    
    # Simulate analysis results (security issues)
    analysis_results = {
        "syntax": {
            "ok": True,
            "findings": [],
            "filename": "insecure_code.py"
        },
        "style": {
            "success": True,
            "style_score": 88.0,
            "violations": [],
            "summary": {
                "total_violations": 0,
                "errors": 0,
                "warnings": 0,
                "grade": "B"
            }
        },
        "security": {
            "ok": False,
            "findings": [
                {
                    "message": "subprocess call with shell=True identified, security issue.",
                    "severity": "HIGH",
                    "location": {"start": {"line": 5, "col": 1}},
                    "suggestion": "Avoid using shell=True. Use subprocess.run() with a list of args."
                },
                {
                    "message": "Use of insecure MD5 hash function.",
                    "severity": "MEDIUM",
                    "location": {"start": {"line": 8, "col": 1}},
                    "suggestion": "Replace MD5 with SHA-256 or stronger."
                }
            ],
            "filename": "insecure_code.py"
        }
    }
    
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/feedback",
            json={
                'code': insecure_code,
                'analysis_results': analysis_results,
                'user_id': 'test_user',
                'submission_id': 'test_security_001'
            },
            timeout=30
        )
        
        result = response.json()
        print_result(result)
        return result.get('success', False)
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_end_to_end():
    """Test 6: End-to-end test through API Gateway."""
    print_header("Test 6: End-to-End Test via API Gateway")
    
    test_code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
    
    try:
        # Submit code to API Gateway
        response = requests.post(
            f"{API_GATEWAY_URL}/submit",
            json={
                'code': test_code,
                'user_id': 'test_user',
                'language': 'python',
                'analysis_types': ['syntax'],
                'include_llm_feedback': True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Submission successful")
            print(f"  Submission ID: {result.get('submission_id')}")
            print(f"  Status: {result.get('status')}")
            
            analysis_results = result.get('analysis_results', {})
            if 'llm_feedback' in analysis_results:
                print("\n✓ LLM feedback generated")
                llm_feedback = analysis_results['llm_feedback']
                if llm_feedback.get('success'):
                    print("\n--- AI Feedback Preview ---")
                    feedback = llm_feedback.get('feedback', '')
                    # Print first 500 characters
                    preview = feedback[:500] + "..." if len(feedback) > 500 else feedback
                    print(preview)
                    return True
                else:
                    print(f"✗ LLM feedback generation failed: {llm_feedback.get('error')}")
                    return False
            else:
                print("⚠ No LLM feedback in response (service may not be running)")
                return False
        else:
            print(f"✗ Submission failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API Gateway")
        print("  Make sure the API Gateway is running: python main.py")
        return False
    except Exception as e:
        print(f"✗ End-to-end test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "LLM Feedback Service Test Suite" + " " * 21 + "║")
    print("║" + " " * 25 + "Task 1.7" + " " * 35 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = []
    
    # Test 1: Health Check
    has_api_key = test_health_check()
    results.append(("Health Check", True))  # Service availability
    
    if not has_api_key:
        print("\n" + "!" * 70)
        print("WARNING: OpenAI API key not configured!")
        print("Set the OPENAI_API_KEY environment variable to run full tests.")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        print("!" * 70)
        print("\nSkipping tests that require OpenAI API...")
        return
    
    # Test 2: API Connectivity
    time.sleep(1)
    api_ok = test_api_connectivity()
    results.append(("API Connectivity", api_ok))
    
    if not api_ok:
        print("\nCannot proceed with remaining tests due to API connectivity issues.")
        return
    
    # Test 3: Good Code
    time.sleep(1)
    results.append(("Good Code Feedback", test_good_code_feedback()))
    
    # Test 4: Bad Code
    time.sleep(1)
    results.append(("Bad Code Feedback", test_bad_code_feedback()))
    
    # Test 5: Security Issues
    time.sleep(1)
    results.append(("Security Issues Feedback", test_security_issues_feedback()))
    
    # Test 6: End-to-End
    time.sleep(1)
    results.append(("End-to-End Integration", test_end_to_end()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! LLM Feedback Service is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

