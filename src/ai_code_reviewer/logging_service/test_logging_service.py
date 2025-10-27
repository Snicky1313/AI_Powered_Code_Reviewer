#!/usr/bin/env python3
"""
Comprehensive test script for the AI-Powered Python Code Reviewer Logging Service

Tests all aspects of the logging service including:
- Redis connection and queue
- Database connection, tables, and indexes
- Producer health and metrics
- Authentication and rate limiting
- Log submission and validation
- Database persistence

Usage:
    python test_logging_service.py
"""

import json
import requests
import time
import sys
from datetime import datetime


# ==================== Database Tests ====================

def test_database_connection():
    """Test database connection and verify tables exist."""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        import os
        
        # Load .env from project root (4 levels up)
        load_dotenv('../../../.env')
        
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=int(os.getenv('DATABASE_PORT', 5432)),
            database=os.getenv('DATABASE_NAME', 'code_reviewer_logs'),
            user=os.getenv('DATABASE_USER', 'logging_service_user'),
            password=os.getenv('DATABASE_PASSWORD', 'AhmmedSagor22')
        )
        
        print("[✓] Database connection successful")
        
        # Check tables exist
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'review_sessions', 'log_events']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if not missing_tables:
                print(f"[✓] All required tables exist: {', '.join(tables)}")
            else:
                print(f"[✗] Missing tables: {missing_tables}")
            
            # Check indexes
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename IN ('log_events', 'review_sessions', 'users')
                ORDER BY tablename, indexname
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            print(f"[✓] Found {len(indexes)} indexes")
            
            # Show some indexes
            if indexes:
                print(f"   Sample indexes: {', '.join(indexes[:5])}")
        
        conn.close()
        return True
        
    except ImportError:
        print("[✗] psycopg2 not installed: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"[✗] Database connection failed: {e}")
        return False


def test_redis_connection():
    """Test Redis connection and queue initialization."""
    print("\n" + "="*60)
    print("TEST 2: Redis Connection")
    print("="*60)
    
    try:
        import redis
        from dotenv import load_dotenv
        import os
        
        # Load .env from project root (4 levels up)
        load_dotenv('../../../.env')
        
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=False
        )
        
        # Test connection
        response = r.ping()
        if response:
            print("[✓] Redis connection successful")
        
        # Test queue operations
        queue_name = os.getenv('REDIS_QUEUE_NAME', 'log_queue')
        queue_length = r.llen(queue_name)
        print(f"[✓] Queue '{queue_name}' accessible")
        print(f"   Current queue length: {queue_length}")
        
        return True
        
    except ImportError:
        print("[✗] redis not installed: pip install redis")
        return False
    except Exception as e:
        print(f"[✗] Redis connection failed: {e}")
        return False


# ==================== API Tests ====================

def test_producer_health():
    """Test the producer service health endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Producer Health Check")
    print("="*60)
    
    # Wait for producer to start
    print("   Waiting for producer to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8001/health", timeout=2)
            if response.status_code == 200:
                break
        except:
            time.sleep(1)
    else:
        print("[✗] Producer service not responding")
        return False
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("[✓] Producer service is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Queue Type: {data.get('queue_type')}")
            
            queue_info = data.get('queue_info', {})
            print(f"   Queue: {queue_info.get('queue_name', 'N/A')}")
            print(f"   Message Count: {queue_info.get('message_count', 0)}")
            
            return True
        else:
            print(f"[✗] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Failed to connect to producer service: {e}")
        print("   Make sure producer is running: python producer.py")
        return False


def test_authentication():
    """Test that authentication is working correctly."""
    print("\n" + "="*60)
    print("TEST 4: Authentication")
    print("="*60)
    
    # Test without API key
    try:
        response = requests.post(
            "http://localhost:8001/log",
            json={"session_id": 999, "event_type": "test", "payload": {}},
            timeout=5
        )
        if response.status_code == 401:
            print("[✓] Authentication working: requests without API key rejected")
        else:
            print(f"[✗] Unexpected response: {response.status_code}")
            print(f"   Expected: 401, Got: {response.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Authentication test failed: {e}")
        return False
    
    # Test with API key
    try:
        response = requests.post(
            "http://localhost:8001/log",
            json={"session_id": 999, "event_type": "test", "payload": {}},
            headers={"X-API-Key": "test_key_123"},
            timeout=5
        )
        if response.status_code == 202:
            print("[✓] Authentication working: requests with valid API key accepted")
            return True
        else:
            print(f"[✗] Valid API key rejected: {response.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Authentication test failed: {e}")
        return False


def test_prometheus_metrics():
    """Test Prometheus metrics endpoint."""
    print("\n" + "="*60)
    print("TEST 5: Prometheus Metrics")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8001/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.text
            print("[✓] Metrics endpoint accessible")
            
            # Check for key metrics
            metrics_to_check = [
                'api_requests_total',
                'log_events_total',
                'request_duration_seconds',
                'queue_size'
            ]
            
            found_metrics = [m for m in metrics_to_check if m in metrics]
            print(f"   Found {len(found_metrics)}/{len(metrics_to_check)} key metrics")
            
            if found_metrics:
                print(f"   Metrics: {', '.join(found_metrics[:3])}")
            
            return True
        else:
            print(f"[✗] Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Metrics test failed: {e}")
        return False


# ==================== Logging Tests ====================

def test_send_log_events():
    """Send various test log events to the producer."""
    print("\n" + "="*60)
    print("TEST 6: Log Event Submission")
    print("="*60)
    
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
            print(f"\n  [{i}/{len(test_events)}] Sending: {event['event_type']}")
            
            response = requests.post(
                "http://localhost:8001/log",
                json=event,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": "test_key_123"
                },
                timeout=5
            )
            
            if response.status_code == 202:
                print(f"     [✓] Accepted: {response.json().get('message', '')[:40]}...")
                successful_sends += 1
            else:
                print(f"     [✗] Rejected: {response.status_code} - {response.text[:50]}")
                
        except Exception as e:
            print(f"     [✗] Failed: {e}")
        
        time.sleep(0.3)
    
    print(f"\n  Summary: {successful_sends}/{len(test_events)} events sent successfully")
    return successful_sends == len(test_events)


def test_queue_status():
    """Check the queue status."""
    print("\n" + "="*60)
    print("TEST 7: Queue Status")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8001/queue/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("[✓] Queue status accessible")
            print(f"   Queue Name: {status.get('queue_name', 'N/A')}")
            print(f"   Queue Type: {status.get('queue_type', 'N/A')}")
            
            queue_info = status.get('queue_info', {})
            print(f"   Messages: {queue_info.get('message_count', 0)}")
            print(f"   Type: {queue_info.get('type', 'N/A')}")
            
            return True
        else:
            print(f"[✗] Queue status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Queue status test failed: {e}")
        return False


def test_database_persistence():
    """Test that logs are being persisted to database."""
    print("\n" + "="*60)
    print("TEST 8: Database Persistence")
    print("="*60)
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        import os
        
        # Load .env from project root (4 levels up)
        load_dotenv('../../../.env')
        
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=int(os.getenv('DATABASE_PORT', 5432)),
            database=os.getenv('DATABASE_NAME', 'code_reviewer_logs'),
            user=os.getenv('DATABASE_USER', 'logging_service_user'),
            password=os.getenv('DATABASE_PASSWORD', 'AhmmedSagor22')
        )
        
        with conn.cursor() as cursor:
            # Check for log events
            cursor.execute("SELECT COUNT(*) FROM log_events")
            count = cursor.fetchone()[0]
            
            print(f"[✓] Found {count} log events in database")
            
            # Get recent events
            cursor.execute("""
                SELECT event_type, COUNT(*) 
                FROM log_events 
                GROUP BY event_type 
                ORDER BY COUNT(*) DESC
            """)
            events = cursor.fetchall()
            
            if events:
                print("   Event breakdown:")
                for event_type, event_count in events:
                    print(f"     - {event_type}: {event_count}")
            
            # Check for test events
            cursor.execute("""
                SELECT COUNT(*) 
                FROM log_events 
                WHERE session_id = 1
            """)
            test_events = cursor.fetchone()[0]
            
            if test_events > 0:
                print(f"[✓] Test events found in database: {test_events}")
            else:
                print("[⚠] Test events not yet in database (consumer may still be processing)")
        
        conn.close()
        return count > 0
        
    except Exception as e:
        print(f"[✗] Database persistence test failed: {e}")
        return False


# ==================== Main Test Function ====================

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" "*10 + "AI Code Reviewer Logging Service - Comprehensive Tests")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Infrastructure tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Redis Connection", test_redis_connection()))
    
    # Service tests
    results.append(("Producer Health", test_producer_health()))
    results.append(("Authentication", test_authentication()))
    results.append(("Prometheus Metrics", test_prometheus_metrics()))
    
    # Logging tests
    results.append(("Log Submission", test_send_log_events()))
    results.append(("Queue Status", test_queue_status()))
    
    # Wait for consumer processing
    print("\n[WAIT] Waiting for consumer processing...")
    time.sleep(3)
    
    # Persistence test
    results.append(("Database Persistence", test_database_persistence()))
    
    # Summary
    print("\n" + "="*70)
    print(" " + "TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    print("\n[NEXT STEPS]")
    print("  1. Check producer logs for any issues")
    print("  2. Start consumer to process queue:")
    print("     python consumer.py")
    print("  3. Query database for stored events:")
    print("     SELECT * FROM log_events ORDER BY timestamp DESC LIMIT 10;")
    print("  4. Start query service for analytics:")
    print("     python query_service.py")
    print("  5. Check Prometheus metrics:")
    print("     curl http://localhost:8001/metrics")
    
    sys.exit(0 if all(result for _, result in results) else 1)


if __name__ == "__main__":
    main()
