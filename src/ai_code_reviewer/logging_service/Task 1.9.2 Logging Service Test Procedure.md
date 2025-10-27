# Logging Service - Comprehensive Test Procedure

This document provides step-by-step instructions for testing the AI Code Reviewer Logging Service.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Starting Services](#starting-services)
3. [Database Verification](#database-verification)
4. [Redis Verification](#redis-verification)
5. [Running Tests](#running-tests)
6. [Viewing Logs](#viewing-logs)
7. [Verifying Results](#verifying-results)
8. [Stopping Services](#stopping-services)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have the following installed and configured:
- Python 3.9+ with virtual environment
- PostgreSQL (version 13+)
- Redis (version 6+)
- Required Python packages (from `requirements.txt`)



### Verify Prerequisites

```bash
# Check Python version
python3 --version

# Check PostgreSQL
psql --version

# Check Redis
redis-cli --version

# Check virtual environment
source ../.venv/bin/activate
pip list
```

---

## Starting Services

### 1. Start PostgreSQL

```bash
# Start PostgreSQL service (if not running)
sudo systemctl start postgresql

# Verify PostgreSQL is running
sudo systemctl status postgresql

# Connect to PostgreSQL to verify database exists
sudo -u postgres psql -c "\l" | grep code_reviewer_logs
```

### 2. Start Redis

```bash
# Start Redis service (if not running)
sudo systemctl start redis

# Verify Redis is running
redis-cli ping
# Expected output: PONG

# Check Redis info
redis-cli info
```

### 3. Verify Database Setup

```bash
# Activate virtual environment
cd /home/yogo/AI_Code_Reviewer-main/logging_service
source ../.venv/bin/activate

# Check database connection
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
print('Database connection successful')
conn.close()
"
```

### 4. View Database Tables and Indexes

```bash
# List all tables
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute(\"\"\"
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
\"\"\")
print('Tables:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')
conn.close()
"
```

```bash
# List all indexes
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute(\"\"\"
    SELECT indexname, tablename 
    FROM pg_indexes 
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname
\"\"\")
print('Indexes:')
for row in cursor.fetchall():
    print(f'  {row[0]} on {row[1]}')
conn.close()
"
```

```bash
# Check users
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
print('Users in database:')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

### 5. Start Producer Service

```bash
# Navigate to logging_service directory
cd /home/yogo/AI_Code_Reviewer-main/logging_service

# Activate virtual environment
source ../.venv/bin/activate

# Start producer in background
python3 producer.py > /tmp/producer.log 2>&1 &
echo $! > /tmp/producer.pid

# Wait a few seconds for startup
sleep 5

# Verify producer is running
ps aux | grep "python.*producer" | grep -v grep

# Check producer health
curl http://localhost:8001/health
```

### 6. Start Consumer Service

```bash
# Ensure you're in the logging_service directory with venv activated
cd /home/yogo/AI_Code_Reviewer-main/logging_service
source ../.venv/bin/activate

# Start consumer in background
python3 consumer.py > /tmp/consumer.log 2>&1 &
echo $! > /tmp/consumer.pid

# Wait a few seconds for startup
sleep 5

# Verify consumer is running
ps aux | grep "python.*consumer" | grep -v grep
```

### 7. Verify All Services Are Running

```bash
# Check all processes
echo "=== Service Status ==="
ps aux | grep -E "producer|consumer|redis|postgres" | grep -v grep

# Check service endpoints
curl -s http://localhost:8001/health | jq
curl -s http://localhost:8001/queue/status | jq
curl -s http://localhost:8001/metrics | head -20
```

---

## Database Verification

### Check Database Status

```bash
# Connect to database and check status
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)

# Get database size
cursor = conn.cursor()
cursor.execute('SELECT pg_size_pretty(pg_database_size(current_database()))')
size = cursor.fetchone()[0]
print(f'Database size: {size}')

# Count records per table
for table in ['log_events', 'review_sessions', 'users']:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} records')

conn.close()
"
```

### View Recent Log Events

```bash
python3 -c "
import psycopg2
import json
from datetime import datetime

conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()

cursor.execute('''
    SELECT id, session_id, event_type, timestamp, payload
    FROM log_events 
    ORDER BY timestamp DESC 
    LIMIT 10
''')

print('Recent log events:')
for row in cursor.fetchall():
    print(f\"Event ID: {row[0]}, Session: {row[1]}, Type: {row[2]}, Time: {row[3]}\")

conn.close()
"
```

---

## Redis Verification

### Check Redis Status

```bash
# Check Redis connection
redis-cli ping

# Check queue length
redis-cli LLEN log_queue

# View all keys
redis-cli KEYS "*"

# Get queue info
redis-cli INFO memory
redis-cli INFO clients
redis-cli INFO stats
```

### Monitor Queue Activity (Real-time)

```bash
# Watch queue length in real-time
watch -n 1 'redis-cli LLEN log_queue'

# Or use redis-cli monitor to see all commands
redis-cli MONITOR
```

---

## Running Tests

### Option 1: Run Full Test Suite

```bash
cd /home/yogo/AI_Code_Reviewer-main/logging_service
source ../.venv/bin/activate
python3 test_logging_service.py
```

This will run 8 comprehensive tests:
1. Database Connection
2. Redis Connection
3. Producer Health Check
4. Authentication
5. Prometheus Metrics
6. Log Event Submission
7. Queue Status
8. Database Persistence

### Option 2: Run Specific Test Components

```bash
# Test database only
python3 -c "
import sys
sys.path.insert(0, '.')
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
print('✓ Database connection successful')
conn.close()
"

# Test Redis only
python3 -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.ping()
print('✓ Redis connection successful')
print(f'✓ Queue length: {r.llen(\"log_queue\")}')
"

# Test Producer API
curl -H "X-API-Key: test_key_123" http://localhost:8001/health

# Test Metrics
curl http://localhost:8001/metrics | grep -E "log_events_total|api_requests_total"
```

### Option 3: Submit Test Events Manually

```bash
# Send a test log event
curl -X POST http://localhost:8001/log \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key_123" \
  -d '{
    "session_id": 100,
    "event_type": "test_event",
    "payload": {"message": "Test from manual curl"},
    "timestamp": "2025-10-27T07:00:00Z"
  }'

# Check if it was queued
redis-cli LLEN log_queue

# Wait a few seconds, then check database
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('SELECT * FROM log_events WHERE event_type = %s', ('test_event',))
rows = cursor.fetchall()
print(f'Found {len(rows)} test events')
conn.close()
"
```

---

## Viewing Logs

### Producer Logs

```bash
# View producer log
tail -50 /tmp/producer.log

# Follow producer log in real-time
tail -f /tmp/producer.log

# Search for errors in producer log
grep -i "error\|exception\|failed" /tmp/producer.log

# View producer log with timestamps
tail -100 /tmp/producer.log | grep -E "INFO|ERROR|WARNING"
```

### Consumer Logs

```bash
# View consumer log
tail -50 /tmp/consumer.log

# Follow consumer log in real-time
tail -f /tmp/consumer.log

# Search for errors in consumer log
grep -i "error\|exception\|failed" /tmp/consumer.log

# View successful message processing
grep "Log event stored successfully" /tmp/consumer.log
```

### Combined Service Status

```bash
# Create a script to monitor all logs
cat > /tmp/monitor_logging.sh << 'EOF'
#!/bin/bash
echo "=== Producer Logs (Last 10 lines) ==="
tail -10 /tmp/producer.log
echo ""
echo "=== Consumer Logs (Last 10 lines) ==="
tail -10 /tmp/consumer.log
echo ""
echo "=== Process Status ==="
ps aux | grep -E "producer|consumer" | grep -v grep
echo ""
echo "=== Redis Queue Length ==="
redis-cli LLEN log_queue
EOF

chmod +x /tmp/monitor_logging.sh
/tmp/monitor_logging.sh
```

---

## Verifying Results

### Check Test Results

After running the test suite, verify the results:

```bash
# The test output should show:
# Total: 8/8 tests passed
cd /home/yogo/AI_Code_Reviewer-main/logging_service
python3 test_logging_service.py 2>&1 | grep -A 20 "TEST SUMMARY"
```

### Verify Database Persistence

```bash
# Count total events
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM log_events')
total = cursor.fetchone()[0]
print(f'Total log events: {total}')
conn.close()
"

# Event type breakdown
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('''
    SELECT event_type, COUNT(*) 
    FROM log_events 
    GROUP BY event_type 
    ORDER BY COUNT(*) DESC
''')
print('Event type breakdown:')
for event_type, count in cursor.fetchall():
    print(f'  {event_type}: {count}')
conn.close()
"
```

### Verify Queue Processing

```bash
# Check queue length (should be low after processing)
redis-cli LLEN log_queue

# Check session creation
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM review_sessions')
count = cursor.fetchone()[0]
print(f'Review sessions created: {count}')
conn.close()
"
```

### Prometheus Metrics Verification

```bash
# Get current metrics
curl -s http://localhost:8001/metrics | grep -E "log_events_total|api_requests_total|request_duration_seconds|queue_size"

# Parse metrics
curl -s http://localhost:8001/metrics | grep "log_events_total"
curl -s http://localhost:8001/metrics | grep "api_requests_total"
curl -s http://localhost:8001/metrics | grep "request_duration_seconds"
```

---

## Stopping Services

### Stop Services Gracefully

```bash
# Stop producer
if [ -f /tmp/producer.pid ]; then
    kill $(cat /tmp/producer.pid)
    echo "Producer stopped"
fi

# Stop consumer
if [ -f /tmp/consumer.pid ]; then
    kill $(cat /tmp/consumer.pid)
    echo "Consumer stopped"
fi

# Verify processes are stopped
ps aux | grep -E "producer|consumer" | grep -v grep

# Or forcefully kill all Python processes related to logging
pkill -f "python.*producer.py"
pkill -f "python.*consumer.py"

# Stop Redis (optional - only if you want to stop Redis)
sudo systemctl stop redis

# Stop PostgreSQL (optional - only if you want to stop PostgreSQL)
sudo systemctl stop postgresql
```

### Clean Up Logs (Optional)

```bash
# Clear log files
rm -f /tmp/producer.log
rm -f /tmp/consumer.log
rm -f /tmp/producer.pid
rm -f /tmp/consumer.pid

# Clear Redis queue (optional)
redis-cli DEL log_queue

# Clear database logs (optional - be careful!)
# python3 -c "
# import psycopg2
# conn = psycopg2.connect(
#     dbname='code_reviewer_logs',
#     user='logging_service_user',
#     password='AhmmedSagor22',
#     host='localhost'
# )
# cursor = conn.cursor()
# cursor.execute('TRUNCATE TABLE log_events CASCADE')
# conn.commit()
# print('Database cleared')
# conn.close()
# "
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Producer Not Starting

```bash
# Check if port is already in use
netstat -tulpn | grep 8001

# Check producer log for errors
tail -50 /tmp/producer.log

# Try starting producer with verbose output
cd /home/yogo/AI_Code_Reviewer-main/logging_service
source ../.venv/bin/activate
python3 producer.py
```

#### 2. Consumer Not Processing Messages

```bash
# Check consumer log
tail -50 /tmp/consumer.log

# Verify database connection
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='code_reviewer_logs',
        user='logging_service_user',
        password='AhmmedSagor22',
        host='localhost'
    )
    print('✓ Database connection OK')
    conn.close()
except Exception as e:
    print(f'✗ Database error: {e}')
"

# Check if consumer is running
ps aux | grep consumer | grep -v grep
```

#### 3. Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis

# Check Redis configuration
redis-cli CONFIG GET "*"
```

#### 4. Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -c "\l" | grep code_reviewer_logs

# Verify user exists
sudo -u postgres psql -c "\du" | grep logging_service_user

# Test connection manually
psql -h localhost -U logging_service_user -d code_reviewer_logs
```

#### 5. Foreign Key Constraint Errors

If you see errors about missing users or sessions:

```bash
# Create a default user if missing
python3 -c "
import psycopg2
conn = psycopg2.connect(
    dbname='code_reviewer_logs',
    user='logging_service_user',
    password='AhmmedSagor22',
    host='localhost'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
if count == 0:
    cursor.execute(\"INSERT INTO users (id, username, created_at) VALUES (1, 'test_user', NOW())\")
    conn.commit()
    print('Default user created')
else:
    print(f'Users already exist: {count}')
conn.close()
"
```

### Advanced Debugging

```bash
# Enable Python debug logging
export LOG_LEVEL=DEBUG

# Start services with debug output
python3 producer.py --log-level DEBUG
python3 consumer.py --log-level DEBUG

# Monitor system resources
htop

# Check for port conflicts
netstat -tulpn | grep -E "8001|6379|5432"

# Check file descriptors
lsof -p $(cat /tmp/producer.pid) 2>/dev/null
lsof -p $(cat /tmp/consumer.pid) 2>/dev/null
```

---

## Quick Start Script

For convenience, here's a script to start everything at once:

```bash
#!/bin/bash
# Save as: start_logging_service.sh

set -e

echo "Starting Logging Service Components..."

# Activate virtual environment
source ../.venv/bin/activate

# Start Producer
echo "Starting Producer..."
python3 producer.py > /tmp/producer.log 2>&1 &
echo $! > /tmp/producer.pid
sleep 3

# Start Consumer
echo "Starting Consumer..."
python3 consumer.py > /tmp/consumer.log 2>&1 &
echo $! > /tmp/consumer.pid
sleep 3

# Verify services
echo ""
echo "Service Status:"
ps aux | grep -E "producer|consumer" | grep -v grep

echo ""
echo "Health Check:"
curl -s http://localhost:8001/health | jq || echo "Waiting for services..."

echo ""
echo "Services started. Logs in /tmp/producer.log and /tmp/consumer.log"
```

Save and run:

```bash
chmod +x start_logging_service.sh
./start_logging_service.sh
```

---

## Summary

This procedure ensures:
- ✅ All required services (PostgreSQL, Redis) are running
- ✅ Producer and Consumer services are active
- ✅ Database tables, indexes, and users are configured
- ✅ Full test suite passes (8/8 tests)
- ✅ Log events are properly queued and processed
- ✅ Data persistence is verified
- ✅ Metrics are being collected
- ✅ Authentication and rate limiting work correctly

For questions or issues, refer to `README.md` in the logging_service directory or check the service logs.

