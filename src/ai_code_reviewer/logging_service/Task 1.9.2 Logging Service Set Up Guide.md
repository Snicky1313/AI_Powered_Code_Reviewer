# Logging Service Setup Guide

Complete setup guide for the enhanced logging service.

## Prerequisites

### 1. Install Dependencies

```bash
# Python packages
pip install -r requirements.txt
pip install -r logging_service/requirements.txt

# Or install specific packages
pip install redis==5.0.0
pip install prometheus-client==0.19.0
pip install psycopg2-binary==2.9.9
```

### 2. Install Redis

#### Using Docker (Recommended)

```bash
docker run -d \
  --name redis-logging \
  -p 6379:6379 \
  redis:latest

# Verify Redis is running
redis-cli PING  # Should return PONG
```

#### Using APT (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### Using Homebrew (macOS)

```bash
brew install redis
brew services start redis
```

### 3. Install PostgreSQL

#### Using Docker

```bash
docker run -d \
  --name postgres-logging \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=code_reviewer_logs \
  -e POSTGRES_USER=logging_service_user \
  -p 5432:5432 \
  postgres:15
```

#### Using APT (Ubuntu/Debian)

```bash
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 4. Set Up Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE code_reviewer_logs;
CREATE USER logging_service_user WITH PASSWORD 'AhmmedSagor22';
GRANT ALL PRIVILEGES ON DATABASE code_reviewer_logs TO logging_service_user;

# Exit psql
\q

# Run setup script
psql -U logging_service_user -d code_reviewer_logs -f logging_service/setup_database.sql
```

## Configuration

### 1. Create Environment File

```bash
cp env.template .env
```

### 2. Edit `.env` File

```bash
# Logging Configuration
LOGGING_ENABLED=true
LOGGING_SERVICE_URL=http://localhost:8001/log

# Redis Configuration
USE_REDIS_QUEUE=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_QUEUE_NAME=log_queue
REDIS_QUEUE_TTL=604800  # 7 days

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=code_reviewer_logs
DATABASE_USER=logging_service_user
DATABASE_PASSWORD=AhmmedSagor22

# API Keys
ADMIN_API_KEY=admin_key_789
API_KEY=test_key_123

# Service Ports
PRODUCER_PORT=8001
QUERY_SERVICE_PORT=8002

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Set API Keys

```bash
export API_KEY=test_key_123
export ADMIN_API_KEY=admin_key_789
```

## Starting Services

### Development Mode

```bash
# Terminal 1: Producer
cd logging_service
python producer.py
# Running on http://localhost:8001

# Terminal 2: Consumer
cd logging_service
python consumer.py

# Terminal 3: Query Service (Phase 2)
cd logging_service
python query_service.py
# Running on http://localhost:8002

# Terminal 4: API Gateway
python main.py
# Running on http://localhost:8000
```

### Production Mode

```bash
# Using systemd (Linux)

# Create service file for producer
sudo nano /etc/systemd/system/logging-producer.service

[Unit]
Description=Logging Producer Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/AI_Code_Reviewer-main/logging_service
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python producer.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable logging-producer
sudo systemctl start logging-producer

# Do the same for consumer and query-service
```

## Verification

### 1. Test Producer

```bash
# Health check
curl http://localhost:8001/health

# Should return:
{
  "status": "healthy",
  "service": "producer",
  "timestamp": "2025-01-XX...",
  "queue_info": {...}
}
```

### 2. Test Logging

```bash
# Send a test log event
curl -X POST http://localhost:8001/log \
  -H "X-API-Key: test_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 123,
    "event_type": "test_event",
    "payload": {"message": "Test log event"}
  }'

# Should return 202 Accepted
```

### 3. Verify in Database

```bash
# Connect to PostgreSQL
psql -U logging_service_user -d code_reviewer_logs

# Query recent events
SELECT * FROM log_events ORDER BY timestamp DESC LIMIT 10;

# Exit
\q
```

### 4. Test Query Service (Phase 2)

```bash
# Get recent events
curl http://localhost:8002/events?limit=10

# Get event types
curl http://localhost:8002/events/types

# Get analytics
curl http://localhost:8002/analytics/usage?days=7
```

### 5. Test Metrics (Phase 3)

```bash
# Get Prometheus metrics
curl http://localhost:8001/metrics

# Should return Prometheus format metrics
```

## Monitoring Setup

### 1. Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64

# Create config file
nano prometheus.yml
```

### 2. Configure Prometheus

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'logging-service'
    static_configs:
      - targets: ['localhost:8001']
```

### 3. Start Prometheus

```bash
./prometheus --config.file=prometheus.yml
# Running on http://localhost:9090
```

### 4. Install Grafana (Optional)

```bash
# Download Grafana
wget https://dl.grafana.com/oss/release/grafana-9.5.0.linux-amd64.tar.gz
tar xvfz grafana-9.5.0.linux-amd64.tar.gz
cd grafana-9.5.0

# Start Grafana
./bin/grafana-server
# Running on http://localhost:3000
```

## Common Issues

### Issue 1: Redis Connection Failed

**Error:** `Redis connection error`

**Solution:**
```bash
# Check Redis is running
redis-cli PING

# If not running, start it
sudo systemctl start redis
# or
docker start redis-logging
```

### Issue 2: Database Connection Failed

**Error:** `Database connection error`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U logging_service_user -d code_reviewer_logs

# Verify credentials in .env
cat .env | grep DATABASE
```

### Issue 3: API Key Authentication Failed

**Error:** `401 Invalid or missing API key`

**Solution:**
```bash
# Check API key is set
echo $API_KEY

# Add header to curl
curl -H "X-API-Key: test_key_123" http://localhost:8001/log
```

### Issue 4: Rate Limit Exceeded

**Error:** `429 Rate limit exceeded`

**Solution:**
```bash
# Wait for rate limit window
# Default: 1000 requests per minute

# Or adjust in producer.py
@rate_limit(requests=2000, window=60)
```

### Issue 5: Queue Full

**Error:** `Queue processing slow`

**Solution:**
```bash
# Check queue size
curl http://localhost:8001/queue/status

# If too large, add more consumers
# Or reduce TTL
REDIS_QUEUE_TTL=259200  # 3 days instead of 7
```

## Performance Tuning

### Redis Performance

```bash
# Configure Redis memory limit
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor memory
redis-cli INFO memory
```

### PostgreSQL Performance

```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_log_events_timestamp ON log_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_events_event_type ON log_events(event_type);
CREATE INDEX IF NOT EXISTS idx_log_events_session_id ON log_events(session_id);

-- Analyze tables
ANALYZE log_events;
```

### Python Performance

```bash
# Use uvicorn with multiple workers
uvicorn producer:app --host 0.0.0.0 --port 8001 --workers 4

# Or use gunicorn
gunicorn producer:app --workers 4 --bind 0.0.0.0:8001
```

## Security Checklist

- [ ] Change default API keys
- [ ] Use strong passwords for database
- [ ] Enable SSL/TLS for PostgreSQL
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Enable authentication for Prometheus
- [ ] Secure Grafana dashboard
- [ ] Regular backups of database
- [ ] Monitor for suspicious activity
- [ ] Update dependencies regularly

## Backup and Recovery

### Database Backup

```bash
# Create backup
pg_dump -U logging_service_user -d code_reviewer_logs > backup.sql

# Restore backup
psql -U logging_service_user -d code_reviewer_logs < backup.sql
```

### Redis Backup

```bash
# Save Redis data
redis-cli SAVE

# Or enable AOF (Append-Only File)
redis-cli CONFIG SET appendonly yes
```

## Next Steps

1. **Monitor Production:** Set up alerts for errors and performance
2. **Scale Services:** Add more consumers if queue grows
3. **Optimize Queries:** Add indexes based on usage patterns
4. **Set Up Alerts:** Configure Prometheus alerts
5. **Document APIs:** Update API documentation with examples

## Support

For issues or questions:
- Check logs in each service terminal
- Review error messages
- Test individual components
- Consult documentation

---

**Congratulations!** Your enhanced logging service is now fully operational with Phase 1, 2, and 3 features. 🎉

