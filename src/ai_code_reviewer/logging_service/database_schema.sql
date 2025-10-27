-- AI-Powered Python Code Reviewer - Database Schema
-- Asynchronous Logging Service Database Schema
-- PostgreSQL DDL Statements
-- Run this script as PostgreSQL superuser (postgres)

-- Clean up any existing setup
DROP DATABASE IF EXISTS code_reviewer_logs;
DROP USER IF EXISTS logging_service_user;

-- Create database
CREATE DATABASE code_reviewer_logs;

-- Create user with correct password
CREATE USER logging_service_user WITH PASSWORD 'AhmmedSagor22';

-- Grant privileges on the database
GRANT ALL PRIVILEGES ON DATABASE code_reviewer_logs TO logging_service_user;

-- Connect to the database and create tables
\c code_reviewer_logs

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO logging_service_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO logging_service_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO logging_service_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO logging_service_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO logging_service_user;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for better performance
    CONSTRAINT users_username_check CHECK (char_length(username) >= 3)
);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Review sessions table
CREATE TABLE IF NOT EXISTS review_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT review_sessions_time_check CHECK (end_time IS NULL OR end_time >= start_time)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_review_sessions_user_id ON review_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_review_sessions_start_time ON review_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_review_sessions_end_time ON review_sessions(end_time);

-- Log events table
CREATE TABLE IF NOT EXISTS log_events (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES review_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT log_events_event_type_check CHECK (char_length(event_type) >= 1)
);

-- Create indexes for better performance and JSON queries
CREATE INDEX IF NOT EXISTS idx_log_events_session_id ON log_events(session_id);
CREATE INDEX IF NOT EXISTS idx_log_events_timestamp ON log_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_events_event_type ON log_events(event_type);
CREATE INDEX IF NOT EXISTS idx_log_events_payload_gin ON log_events USING GIN(payload);

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_log_events_session_timestamp ON log_events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_log_events_type_timestamp ON log_events(event_type, timestamp);

-- Optional: Create a view for easier querying with user information
CREATE OR REPLACE VIEW log_events_with_user AS
SELECT 
    le.id,
    le.session_id,
    le.timestamp,
    le.event_type,
    le.payload,
    rs.user_id,
    rs.start_time as session_start_time,
    rs.end_time as session_end_time,
    u.username
FROM log_events le
JOIN review_sessions rs ON le.session_id = rs.id
JOIN users u ON rs.user_id = u.id;

-- Insert some sample data for testing (optional)
-- INSERT INTO users (username) VALUES 
--     ('alice_dev'),
--     ('bob_reviewer'),
--     ('charlie_admin');

-- INSERT INTO review_sessions (user_id, start_time) VALUES 
--     (1, NOW() - INTERVAL '1 hour'),
--     (2, NOW() - INTERVAL '30 minutes'),
--     (3, NOW() - INTERVAL '15 minutes');

-- INSERT INTO log_events (session_id, event_type, payload) VALUES 
--     (1, 'review_started', '{"code_language": "python", "file_count": 3}'),
--     (1, 'llm_query_sent', '{"query_type": "style_check", "tokens": 150}'),
--     (1, 'llm_feedback_received', '{"response_time_ms": 1200, "suggestions_count": 5}'),
--     (2, 'review_started', '{"code_language": "javascript", "file_count": 1}'),
--     (3, 'security_scan_completed', '{"vulnerabilities_found": 0, "scan_duration_ms": 800}');

-- Grant final permissions on all created objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO logging_service_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO logging_service_user;

-- Insert some test data
INSERT INTO users (username) VALUES 
    ('test_user'),
    ('demo_user');

INSERT INTO review_sessions (user_id, start_time) VALUES 
    (1, NOW() - INTERVAL '1 hour'),
    (2, NOW() - INTERVAL '30 minutes');

-- Verify setup completed
SELECT 'Database setup completed successfully!' as status;
