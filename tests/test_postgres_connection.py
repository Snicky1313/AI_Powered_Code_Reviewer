#!/usr/bin/env python3
"""
Test PostgreSQL connection and setup the database for the logging service
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def test_postgres_connection():
    """Test connection to PostgreSQL as superuser."""
    print("Testing PostgreSQL connection as superuser...")
    try:
        connection = psycopg2.connect(
            host='localhost', port=5432, database='postgres',
            user='postgres', password='Och13ng', connect_timeout=10
        )
        print("✅ PostgreSQL is running and accessible!")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL version: {version[0]}")
        connection.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("\nPossible issues:\n1. Service not running\n2. Wrong password\n3. Not listening on localhost:5432\n4. User 'postgres' missing")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def setup_logging_database():
    """Set up the logging database and user."""
    print("\n" + "="*50)
    print("Setting up logging database...")
    try:
        connection = psycopg2.connect(
            host='localhost', port=5432, database='postgres',
            user='postgres', password='Och13ng', connect_timeout=10
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            print("🧹 Cleaning up existing database and user...")
            cursor.execute("DROP DATABASE IF EXISTS code_reviewer_logs")
            cursor.execute("DROP USER IF EXISTS logging_service_user")
            print("📊 Creating database 'code_reviewer_logs'...")
            cursor.execute("CREATE DATABASE code_reviewer_logs")
            print("👤 Creating user 'logging_service_user'...")
            cursor.execute("CREATE USER logging_service_user WITH PASSWORD 'SagorAhmmed22'")
            print("🔐 Granting privileges...")
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE code_reviewer_logs TO logging_service_user")
        connection.close()

        print("✅ Database and user created successfully!")
        print("\n📋 Creating tables...")
        connection = psycopg2.connect(
            host='localhost', port=5432, database='code_reviewer_logs',
            user='postgres', password='Och13ng', connect_timeout=10
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("GRANT ALL ON SCHEMA public TO logging_service_user")
            cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO logging_service_user")
            cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO logging_service_user")
            cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO logging_service_user")
            cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO logging_service_user")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT users_username_check CHECK (char_length(username) >= 3)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP WITH TIME ZONE,
                    CONSTRAINT review_sessions_time_check CHECK (end_time IS NULL OR end_time >= start_time)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_sessions_user_id ON review_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_sessions_start_time ON review_sessions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_sessions_end_time ON review_sessions(end_time)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_events (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER NOT NULL REFERENCES review_sessions(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    event_type VARCHAR(100) NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}',
                    CONSTRAINT log_events_event_type_check CHECK (char_length(event_type) >= 1)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_session_id ON log_events(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_timestamp ON log_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_event_type ON log_events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_payload_gin ON log_events USING GIN(payload)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_session_timestamp ON log_events(session_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_events_type_timestamp ON log_events(event_type, timestamp)")

            cursor.execute("""
                CREATE OR REPLACE VIEW log_events_with_user AS
                SELECT 
                    le.id, le.session_id, le.timestamp, le.event_type, le.payload,
                    rs.user_id, rs.start_time as session_start_time, rs.end_time as session_end_time,
                    u.username
                FROM log_events le
                JOIN review_sessions rs ON le.session_id = rs.id
                JOIN users u ON rs.user_id = u.id
            """)

            cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO logging_service_user")
            cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO logging_service_user")

            cursor.execute("INSERT INTO users (username) VALUES ('test_user'), ('demo_user')")
            cursor.execute("INSERT INTO review_sessions (user_id, start_time) VALUES (1, NOW() - INTERVAL '1 hour'), (2, NOW() - INTERVAL '30 minutes')")

            print("✅ Tables created successfully!")
        connection.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during setup: {str(e)}")
        return False

def test_logging_user_connection():
    """Test connection as the logging service user."""
    print("\n" + "="*50)
    print("Testing connection as logging_service_user...")
    try:
        connection = psycopg2.connect(
            host='localhost', port=5432, database='code_reviewer_logs',
            user='logging_service_user', password='SagorAhmmed22',
            cursor_factory=RealDictCursor, connect_timeout=10
        )
        print("✅ Logging service user can connect!")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            print(f"✅ Can read users table: {cursor.fetchone()['count']} records")
            cursor.execute("SELECT COUNT(*) as count FROM review_sessions")
            print(f"✅ Can read review_sessions table: {cursor.fetchone()['count']} records")
            cursor.execute("SELECT COUNT(*) as count FROM log_events")
            print(f"✅ Can read log_events table: {cursor.fetchone()['count']} records")
        connection.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Logging user connection failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function to run all tests and setup."""
    print("🔧 PostgreSQL Setup and Test Script")
    print("="*50)

    if not test_postgres_connection():
        print("\n❌ Cannot proceed without PostgreSQL connection.")
        return False
    if not setup_logging_database():
        print("\n❌ Database setup failed.")
        return False
    if not test_logging_user_connection():
        print("\n❌ Logging user connection failed.")
        return False

    print("\n🎉 All tests passed! Your database is ready for the logging service.")
    print("\nNext steps:")
    print("1. Start the consumer:")
    print("   PYTHONPATH=src python -m ai_code_reviewer.logging_service.consumer")
    print("2. In another terminal, start the producer:")
    print("   PYTHONPATH=src python -m ai_code_reviewer.logging_service.producer")
    print("3. Run the logging service tests:")
    print("   PYTHONPATH=src pytest -q tests/test_logging_service.py")
    return True

if __name__ == "__main__":
    main()
