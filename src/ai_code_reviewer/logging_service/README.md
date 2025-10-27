# AI-Powered Python Code Reviewer - Enhanced Logging Service

**Version:** 2.0.0  
**Status:** Production Ready  
**Phases Implemented:** Phase 1, 2, 3 (Complete)

## Overview

This directory contains the enhanced asynchronous logging service for creating secure audit trails of all review activities. The service now includes:

- **Phase 1:** Redis-based persistent queue, API Gateway integration
- **Phase 2:** Query endpoints and analytics
- **Phase 3:** API authentication, rate limiting, Prometheus metrics

## Architecture

```
┌─────────────────┐    POST /log     ┌─────────────────┐    Redis Queue   ┌─────────────────┐
│   API Gateway   │ ──────────────► │    Producer     │ ──────────────► │    PostgreSQL    │
│   (main.py)     │   (Auth + Rate  │   (Port 8001)   │   Persistent   │    (Port 5432)   │
│                 │     Limiting)   │   + Metrics     │    Storage      │    Audit Trail   │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
                                             │
                                             │ /metrics
                                             ▼
                                    ┌─────────────────┐
                                    │  Prometheus     │
                                    │   Monitoring    │
                                    └─────────────────┘

┌─────────────────┐    GET /analytics/*     ┌─────────────────┐
│   Client Apps    │ ────────────────────► │  Query Service  │
│                 │   (Query & Analysis)   │   (Port 8002)   │
└─────────────────┘                        └─────────────────┘
```

## Services

### 1. Producer Service (`producer.py`)
- **Port:** 8001
- **Purpose:** Accept log events via HTTP POST
- **Security:** API key authentication, rate limiting (1000 req/min)
- **Monitoring:** Prometheus metrics endpoint at `/metrics`
- **Queue:** Redis (with fallback to in-memory)

### 2. Consumer Service (`consumer.py`)
- **Purpose:** Consumes events from Redis queue
- **Storage:** Stores events in PostgreSQL
- **Features:** Automatic retry logic, graceful shutdown

### 3. Query Service (`query_service.py`)
- **Port:** 8002
- **Purpose:** Query and analytics endpoints
- **Features:**
  - `/events` - Query logs with filters
  - `/events/types` - List event types
  - `/analytics/usage` - Usage statistics
  - `/analytics/llm` - LLM usage analytics
  - `/analytics/performance` - Performance metrics

## Quick Start

### 1. Install Dependencies

```bash
# Python packages
pip install -r requirements.txt

# Or specific packages
pip install redis==5.0.0
pip install prometheus-client==0.19.0
pip install psycopg2-binary==2.9.9
```

### 2. Start Redis

```bash
docker run -d --name redis-logging -p 6379:6379 redis:latest
```

### 3. Set Up Database

```bash
# Run setup script
psql -U postgres -f setup_database.sql

# Or manually
psql -U postgres
CREATE DATABASE code_reviewer_logs;
CREATE USER logging_service_user WITH PASSWORD 'AhmmedSagor22';
GRANT ALL PRIVILEGES ON DATABASE code_reviewer_logs TO logging_service_user;
\q

# Load schema
psql -U logging_service_user -d code_reviewer_logs -f database_schema.sql
```

### 4. Configure Environment

```bash
cp ../env.template ../.env
# Edit .env with your actual values
```

### 5. Start Services

```bash
# Terminal 1: Producer
cd logging_service
python producer.py

# Terminal 2: Consumer
cd logging_service
python consumer.py

# Terminal 3: Query Service (Phase 2)
cd logging_service
python query_service.py

# Terminal 4: API Gateway
python ../main.py
```

## API Usage

### Send Log Events (Requires API Key)

```bash
curl -X POST "http://localhost:8001/log" \
  -H "X-API-Key: test_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 123,
    "event_type": "review_started",
    "payload": {
      "code_language": "python",
      "file_count": 3
    }
  }'
```

### Query Events (Phase 2)

```bash
# Get recent events
curl http://localhost:8002/events?limit=10&page=1

# Filter by event type
curl http://localhost:8002/events?event_type=review_started

# Filter by session
curl http://localhost:8002/events?session_id=123
```

### Get Analytics

```bash
# Usage analytics
curl http://localhost:8002/analytics/usage?days=7

# LLM usage analytics
curl http://localhost:8002/analytics/llm?days=7

# Performance analytics
curl http://localhost:8002/analytics/performance?days=7
```

### Prometheus Metrics (Phase 3)

```bash
curl http://localhost:8001/metrics
```

## Event Types

Supported event types:
- `review_started` - Code review begins
- `review_completed` - Review completes
- `syntax_analysis_started` - Syntax analysis begins
- `syntax_analysis_completed` - Syntax analysis completes
- `llm_query_sent` - LLM query made
- `llm_feedback_received` - LLM response received
- `error_occurred` - Error event

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOGGING_ENABLED` | Enable/disable logging | `true` |
| `LOGGING_SERVICE_URL` | Producer URL | `http://localhost:8001/log` |
| `USE_REDIS_QUEUE` | Use Redis or in-memory | `true` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `code_reviewer_logs` |
| `DATABASE_USER` | Database user | `logging_service_user` |
| `DATABASE_PASSWORD` | Database password | (Required) |
| `ADMIN_API_KEY` | Admin API key | (Required) |
| `PRODUCER_PORT` | Producer port | `8001` |
| `QUERY_SERVICE_PORT` | Query service port | `8002` |

## Security Features (Phase 3)

- **API Key Authentication:** All endpoints require valid API key
- **Rate Limiting:** 1000 requests/minute (configurable)
- **Prometheus Metrics:** Real-time monitoring
- **Health Checks:** Service availability monitoring

## Monitoring

### Key Metrics

- `api_requests_total` - Total API requests
- `log_events_total` - Total log events
- `queue_size` - Current queue depth
- `request_duration_seconds` - Response time
- `llm_queries_total` - LLM usage

### Grafana Dashboard

Import Prometheus data source and create dashboards for:
- Request rate and latency
- Queue depth over time
- LLM usage and costs
- Error rates

## Testing

```bash
# Run test script
python test_logging_service.py

# Test all endpoints
curl http://localhost:8001/health
curl -H "X-API-Key: test_key_123" http://localhost:8001/log
curl http://localhost:8002/events
curl http://localhost:8002/analytics/usage
curl http://localhost:8001/metrics
```

## Troubleshooting

### Service Won't Start

```bash
# Check Redis
redis-cli PING

# Check database
psql -U logging_service_user -d code_reviewer_logs

# Check ports
netstat -tuln | grep -E '8001|8002|5432'
```

### Authentication Failures

```bash
# Verify API key
curl -H "X-API-Key: test_key_123" http://localhost:8001/health
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U logging_service_user -d code_reviewer_logs
```

## Files

### Core Services
- `producer.py` - Producer service (Phase 1, 3)
- `consumer.py` - Consumer service (Phase 1)
- `query_service.py` - Query and analytics service (Phase 2)

### Infrastructure
- `redis_queue.py` - Redis queue implementation (Phase 1)
- `auth.py` - Authentication and rate limiting (Phase 3)
- `metrics.py` - Prometheus metrics (Phase 3)

### Configuration
- `requirements.txt` - Python dependencies
- `setup_database.sql` - Database setup script
- `database_schema.sql` - Database schema
- `.env` - Environment configuration (copy from ../env.template)

### Testing
- `test_logging_service.py` - Test script

## Production Deployment

### Systemd Services

```bash
# Create service files
sudo nano /etc/systemd/system/logging-producer.service
sudo nano /etc/systemd/system/logging-consumer.service
sudo nano /etc/systemd/system/logging-query.service

# Enable and start
sudo systemctl enable logging-producer
sudo systemctl enable logging-consumer
sudo systemctl enable logging-query
sudo systemctl start logging-producer
sudo systemctl start logging-consumer
sudo systemctl start logging-query
```

### Monitoring Setup

```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz

# Configure scrape targets
# Edit prometheus.yml to include localhost:8001

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

## Next Steps

1. Set up production API keys
2. Configure monitoring alerts
3. Set up log rotation
4. Implement backup strategy
5. Configure SSL/TLS

## Support

For issues or questions:
- Check service health: `curl http://localhost:8001/health`
- View metrics: `curl http://localhost:8001/metrics`
- Review logs: Check service terminal output
- Consult documentation: See `LOGGING_ENHANCEMENT_COMPLETE.md`

---

**Status:** Production Ready ✅  
**Version:** 2.0.0  
**Last Updated:** 2025-01-XX
