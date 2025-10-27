#!/usr/bin/env python3
"""
AI-Powered Python Code Reviewer - Logging Service Consumer (Simple Queue Version)

This standalone worker service consumes log events from a simple in-memory queue
and stores them in a PostgreSQL database. No RabbitMQ required!

Author: Sagor Ahmmed
Created: 2025-09-28
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
try:
    from redis_queue import get_queue
except ImportError:
    from simple_queue import get_queue

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations.
    """
    
    def __init__(self):
        self.connection = None
        self.connection_params = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'database': os.getenv('DATABASE_NAME', 'code_reviewer_logs'),
            'user': os.getenv('DATABASE_USER', 'logging_service_user'),
            'password': os.getenv('DATABASE_PASSWORD', 'SagorAhmmed22')
        }
        
    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                **self.connection_params,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            self.connection.autocommit = False
            logger.info("Successfully connected to PostgreSQL database")
            
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    def ensure_connection(self):
        """Ensure database connection is active, reconnect if necessary."""
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            else:
                # Test connection with a simple query
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    
        except psycopg2.Error:
            logger.warning("Database connection lost, attempting to reconnect...")
            try:
                if self.connection:
                    self.connection.close()
            except:
                pass
            self.connect()
    
    def ensure_review_session(self, session_id: int) -> bool:
        """
        Ensure a review session exists in the database. Create it if it doesn't.
        
        Args:
            session_id: Review session ID
            
        Returns:
            bool: True if session exists or was created successfully
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                # Check if session exists
                cursor.execute("SELECT id FROM review_sessions WHERE id = %s", (session_id,))
                exists = cursor.fetchone()
                
                if not exists:
                    # Create the session with default values
                    insert_query = """
                        INSERT INTO review_sessions (id, user_id, start_time)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        session_id,
                        int(os.getenv('DEFAULT_USER_ID', 1)),
                        datetime.now()
                    ))
                    self.connection.commit()
                    logger.info(f"Created review session: {session_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring review session: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def insert_log_event(self, session_id: int, event_type: str, payload: Dict[str, Any], 
                        timestamp: str = None) -> bool:
        """
        Insert a log event into the database.
        
        Args:
            session_id: Review session ID
            event_type: Type of event
            payload: Event payload data
            timestamp: Event timestamp (ISO format)
            
        Returns:
            bool: True if insertion was successful
        """
        try:
            self.ensure_connection()
            
            # Ensure review session exists
            if not self.ensure_review_session(session_id):
                logger.warning(f"Failed to ensure review session {session_id}, attempting insert anyway")
            
            # Parse timestamp
            if timestamp:
                try:
                    # Handle both ISO format with and without timezone
                    if timestamp.endswith('Z'):
                        timestamp = timestamp.replace('Z', '+00:00')
                    event_timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {timestamp}, using current time")
                    event_timestamp = datetime.now()
            else:
                event_timestamp = datetime.now()
            
            # Insert the log event
            insert_query = """
                INSERT INTO log_events (session_id, timestamp, event_type, payload)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(insert_query, (
                    session_id,
                    event_timestamp,
                    event_type,
                    json.dumps(payload)
                ))
                
                result = cursor.fetchone()
                self.connection.commit()
                
                log_event_id = result['id']
                logger.info(
                    f"Log event stored successfully: id={log_event_id}, "
                    f"session_id={session_id}, event_type={event_type}"
                )
                
                return True
                
        except psycopg2.Error as e:
            logger.error(f"Database error inserting log event: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
        except Exception as e:
            logger.error(f"Unexpected error inserting log event: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
    
    def close(self):
        """Close database connection."""
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")


class SimpleQueueConsumer:
    """
    Manages simple queue connections and message consumption.
    """
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.queue_name = os.getenv('RABBITMQ_QUEUE_NAME', 'log_queue')
        self.retry_attempts = int(os.getenv('CONSUMER_RETRY_ATTEMPTS', 3))
        self.retry_delay = int(os.getenv('CONSUMER_RETRY_DELAY', 5))
        self.queue = get_queue()
        
    def process_message(self, message_body: str):
        """
        Process a single message from the queue.
        
        Args:
            message_body: JSON message body as string
        """
        message_processed = False
        
        try:
            # Decode message
            message_data = json.loads(message_body)
            
            logger.info(f"Processing message: {message_data.get('event_type', 'unknown')}")
            
            # Extract required fields
            session_id = message_data.get('session_id')
            event_type = message_data.get('event_type')
            payload = message_data.get('payload', {})
            timestamp = message_data.get('timestamp')
            
            # Validate required fields
            if not session_id or not event_type:
                logger.error(f"Invalid message format - missing required fields: {message_data}")
                return
            
            # Attempt to store in database with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    success = self.database_manager.insert_log_event(
                        session_id=session_id,
                        event_type=event_type,
                        payload=payload,
                        timestamp=timestamp
                    )
                    
                    if success:
                        message_processed = True
                        print(f"Log event processed and stored: session_id={session_id}, event_type={event_type}")
                        break
                    else:
                        logger.warning(f"Database insertion failed, attempt {attempt + 1}/{self.retry_attempts}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                        
                except Exception as e:
                    logger.error(f"Error during database insertion attempt {attempt + 1}: {str(e)}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
            
            if not message_processed:
                logger.error("Failed to process message after all retry attempts")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message body: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error processing message: {str(e)}")
    
    def start_consuming(self):
        """Start consuming messages from the queue."""
        try:
            logger.info(f"Starting consumer for queue '{self.queue_name}'")
            
            # Start consuming messages
            self.queue.consume(self.queue_name, self.process_message)
            
            logger.info("Consumer started. Waiting for messages. To exit press CTRL+C")
            
            # Keep running until shutdown is requested
            while not shutdown_requested:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming and close connections."""
        try:
            self.queue.stop()
            logger.info("Stopped consuming messages")
        except Exception as e:
            logger.error(f"Error stopping consumer: {str(e)}")


def main():
    """
    Main function to run the consumer service.
    """
    logger.info("Starting Code Review Logging Service - Consumer (Simple Queue)")
    
    # Initialize database manager
    database_manager = DatabaseManager()
    
    try:
        # Test database connection
        database_manager.connect()
        logger.info("Database connection established successfully")
        
        # Initialize and start consumer
        consumer = SimpleQueueConsumer(database_manager)
        consumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Consumer service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in consumer service: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        database_manager.close()
        logger.info("Consumer service shutdown completed")


if __name__ == "__main__":
    """
    Run the consumer service.
    
    Usage:
        python consumer_simple.py
    """
    main()
