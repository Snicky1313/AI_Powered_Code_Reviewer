#!/usr/bin/env python3
"""
Test script for the AI-Powered Python Code Reviewer Logging Service

This script demonstrates how to send log events to the producer service
and verify that the logging system is working correctly.

Usage:
    python test_logging_service.py
"""

import json
import requests
import time
from datetime import datetime


def test_producer_health():
    """Test the producer service health endpoint."""
    try:
        response = requests.get("http://localhost:8001/health")
        if response.status_code == 200:
            print("[OK] Producer service is healthy")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"[ERROR] Producer health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to producer service: {e}")
        return False


def test_send_log_events():
    """Send various test log events to the producer."""
    test_events = [
        {
            "session_id": 1,
            "event_type": "review_started",
            "payload": {
                "code_language": "python",
                "file_count": 3,
                "user_agent": "Test Script"
            }
        },
        {
            "session_id": 1,
            "event_type": "llm_query_sent",
            "payload": {
                "query_type": "style_check",
                "tokens": 150,
                "model": "gpt-4"
            }
        },
        {
            "session_id": 1,
            "event_type": "llm_feedback_received",
            "payload": {
                "response_time_ms": 1200,
                "suggestions_count": 5,
                "confidence_score": 0.92
            }
        },
        {
            "session_id": 1,
            "event_type": "syntax_analysis_completed",
            "payload": {
                "errors_found": 0,
                "warnings_found": 2,
                "analysis_duration_ms": 45
            }
        },
        {
            "session_id": 1,
            "event_type": "review_completed",
            "payload": {
                "total_duration_ms": 15000,
                "overall_score": 85,
                "issues_found": 3
            }
        }
    ]
    
    successful_sends = 0
    
    for i, event in enumerate(test_events, 1):
        try:
            print(f"\n[SEND] Sending test event {i}/5: {event['event_type']}")
            
            response = requests.post(
                "http://localhost:8001/log",
                json=event,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 202:
                print(f"[OK] Event accepted: {response.json()['message']}")
                successful_sends += 1
            else:
                print(f"[ERROR] Event rejected: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send event: {e}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    return successful_sends


def test_queue_status():
    """Check the queue status."""
    try:
        response = requests.get("http://localhost:8001/queue/status")
        if response.status_code == 200:
            status = response.json()
            print(f"\n[STATUS] Queue Status:")
            print(f"   Queue Name: {status.get('queue_name', 'N/A')}")
            print(f"   Queue Type: {status.get('queue_type', 'N/A')}")
            print(f"   Queue Info: {status.get('queue_info', 'N/A')}")
            return True
        else:
            print(f"[ERROR] Queue status check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get queue status: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing AI Code Reviewer Logging Service")
    print("=" * 50)
    
    # Test producer health
    if not test_producer_health():
        print("\n[ERROR] Producer service is not available. Please ensure it's running.")
        print("   Start with: python producer_simple.py")
        return
    
    # Test sending log events
    print(f"\n[TEST] Testing log event submission...")
    successful_sends = test_send_log_events()
    print(f"\n[OK] Successfully sent {successful_sends}/5 log events")
    
    # Wait a moment for processing
    print("\n[WAIT] Waiting for message processing...")
    time.sleep(2)
    
    # Check queue status
    test_queue_status()
    
    print("\n[COMPLETE] Test completed!")
    print("\n[NEXT] Next steps:")
    print("   1. Check consumer logs to verify message processing")
    print("   2. Query the database to see stored log events:")
    print("      SELECT * FROM log_events ORDER BY timestamp DESC LIMIT 10;")
    print("   3. Monitor the queue status during high load scenarios")


if __name__ == "__main__":
    main()

