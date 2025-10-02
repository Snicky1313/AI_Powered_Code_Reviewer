# AI-Powered Python Code Reviewer - Logging Service

This directory contains the asynchronous logging service for creating secure audit trails of all review activities. The service consists of a FastAPI producer that accepts log events and a standalone consumer that processes them into a PostgreSQL database via RabbitMQ.

## Architecture

```
┌─────────────────┐    HTTP POST     ┌─────────────────┐    Simple Queue┌─────────────────┐    PostgreSQL    ┌─────────────────┐
│   Client Apps   │ ──────────────► │   Producer      │ ──────────────► │   Message       │ ──────────────► │   Database      │
│                 │    /log          │   (FastAPI)     │    Queue        │   Queue         │    Storage      │   (PostgreSQL)  │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘                 └─────────────────┘
                                            │                                     │                                     │
                                            │                                     │                                     │
                                    ┌─────────────────┐                 ┌─────────────────┐                 ┌─────────────────┐
                                    │   Health Check  │                 │   Persistent    │                 │   Audit Trail   │
                                    │   Queue Status  │                 │   Durable Queue │                 │   Log Events    │
                                    └─────────────────┘                 └─────────────────┘                 └─────────────────┘
```

## Components

### 1. Producer Service (`producer.py`)
- **FastAPI application** that accepts HTTP POST requests with log events
- **Publishes messages** to RabbitMQ queue for asynchronous processing
- **Robust error handling** with connection retry mechanisms
- **Health check endpoints** for monitoring

### 2. Consumer Service (`consumer.py`)
- **Standalone worker** that continuously processes messages from RabbitMQ
- **Database integration** with PostgreSQL for persistent storage
- **Retry logic** with configurable attempts and delays
- **Graceful shutdown** handling with signal management

### 3. Database Schema (`database_schema.sql`)
- **PostgreSQL tables** for users, review sessions, and log events
- **JSONB payload** storage for flexible event data
- **Indexes** for optimal query performance
- **Constraints** and validation rules

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp env_template.txt .env
```

Edit `.env` with your actual configuration values.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Create the PostgreSQL database and tables:
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE DATABASE code_reviewer_logs;
CREATE USER logging_service_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE code_reviewer_logs TO logging_service_user;

# Connect to the new database
\c code_reviewer_logs

# Run the schema creation script
\i database_schema.sql
```

### 4. Start RabbitMQ

Ensure RabbitMQ is running on your system:
```bash
# On Ubuntu/Debian
sudo systemctl start rabbitmq-server

# On macOS with Homebrew
brew services start rabbitmq

# On Windows
# Start RabbitMQ service from Services panel or command line
```

### 5. Run the Services

Start the consumer first:
```bash
python consumer.py
```

In another terminal, start the producer:
```bash
python producer.py
```

## API Usage

### Send Log Events

```bash
curl -X POST "http://localhost:8001/log" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": 123,
       "event_type": "review_started",
       "payload": {
         "code_language": "python",
         "file_count": 3,
         "user_agent": "VSCode/1.74.0"
       }
     }'
```

### Health Check

```bash
curl http://localhost:8001/health
```

### Queue Status

```bash
curl http://localhost:8001/queue/status
```

## Event Types

The system supports various event types for comprehensive audit trails:

- `review_started` - When a code review session begins
- `review_completed` - When a review session completes
- `review_cancelled` - When a review is cancelled
- `llm_query_sent` - When a query is sent to the LLM service
- `llm_feedback_received` - When feedback is received from LLM
- `llm_error` - When LLM processing encounters errors
- `syntax_analysis_started` - Beginning of syntax analysis
- `syntax_analysis_completed` - Completion of syntax analysis
- `style_analysis_started` - Beginning of style analysis
- `style_analysis_completed` - Completion of style analysis
- `security_scan_started` - Beginning of security scan
- `security_scan_completed` - Completion of security scan
- `performance_analysis_started` - Beginning of performance analysis
- `performance_analysis_completed` - Completion of performance analysis
- `report_generated` - When analysis report is generated
- `user_action` - General user interactions
- `system_event` - System-level events

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `code_reviewer_logs` |
| `DATABASE_USER` | Database user | `logging_service_user` |
| `DATABASE_PASSWORD` | Database password | Required |
| `RABBITMQ_HOST` | RabbitMQ host | `localhost` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `guest` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `guest` |
| `RABBITMQ_VHOST` | RabbitMQ virtual host | `/` |
| `RABBITMQ_QUEUE_NAME` | Queue name | `log_queue` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment type | `development` |
| `PRODUCER_HOST` | Producer service host | `0.0.0.0` |
| `PRODUCER_PORT` | Producer service port | `8001` |
| `CONSUMER_RETRY_ATTEMPTS` | Consumer retry attempts | `3` |
| `CONSUMER_RETRY_DELAY` | Consumer retry delay (seconds) | `5` |

## Monitoring and Observability

### Logging
Both services provide comprehensive logging with configurable levels:
- **INFO**: Normal operations and successful processing
- **WARNING**: Recoverable errors and unusual conditions
- **ERROR**: Serious errors that need attention
- **DEBUG**: Detailed debugging information

### Health Checks
- Producer health check: `GET /health`
- Queue status monitoring: `GET /queue/status`
- Database connectivity validation

### Error Handling
- **Connection failures**: Automatic retry with exponential backoff
- **Message processing errors**: Configurable retry attempts
- **Database errors**: Transaction rollback and error logging
- **Graceful shutdown**: Signal handling for clean service termination

## Production Considerations

### Security
- Use strong database passwords
- Configure RabbitMQ authentication
- Enable SSL/TLS for database and message queue connections
- Implement proper firewall rules
- Regular security updates

### Performance
- Monitor queue depth and processing rates
- Scale consumer instances based on load
- Optimize database queries and indexes
- Configure appropriate connection pooling

### Reliability
- Set up database replication
- Configure RabbitMQ clustering
- Implement proper backup strategies
- Monitor disk space and system resources

### Deployment
- Use Docker containers for consistent deployment
- Implement proper logging aggregation
- Set up monitoring and alerting
- Use environment-specific configurations

## Troubleshooting

### Common Issues

1. **Connection Refused Errors**
   - Verify RabbitMQ and PostgreSQL services are running
   - Check network connectivity and firewall settings
   - Validate connection parameters in `.env`

2. **Message Processing Failures**
   - Check database connectivity and permissions
   - Verify table schema matches expected structure
   - Review consumer logs for specific error details

3. **Queue Buildup**
   - Monitor consumer processing rate
   - Check for database performance issues
   - Consider scaling consumer instances

4. **Authentication Errors**
   - Verify database and RabbitMQ credentials
   - Check user permissions and privileges
   - Ensure password special characters are properly escaped

### Debug Commands

```bash
# Check RabbitMQ queue status
rabbitmqctl list_queues name messages consumers

# Test database connection
psql -h localhost -U logging_service_user -d code_reviewer_logs -c "SELECT COUNT(*) FROM log_events;"

# Monitor consumer processing
tail -f consumer.log | grep "Log event processed"

# Check producer health
curl -s http://localhost:8001/health | jq .
```

## License

This logging service is part of the AI-Powered Python Code Reviewer project. See the main project LICENSE file for details.

