#!/usr/bin/env python3
"""
Redis-based Queue Manager
Replaces the in-memory queue for production-ready persistent storage.

Author: Code Review Enhancement Team
Created: 2025-01-XX
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional, Callable
import redis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RedisQueueManager:
    """
    Redis-based queue manager for persistent log storage.
    Provides the same interface as the simple queue for backward compatibility.
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = None
        self.queue_name = os.getenv('REDIS_QUEUE_NAME', 'log_queue')
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD', None)
        self.connection_timeout = int(os.getenv('REDIS_CONNECTION_TIMEOUT', 10))
        self.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
        
    def connect(self) -> bool:
        """
        Establish connection to Redis.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password if self.password else None,
                socket_connect_timeout=self.connection_timeout,
                socket_timeout=self.socket_timeout,
                decode_responses=False,  # We'll handle JSON encoding/decoding
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {self.host}:{self.port}")
            return True
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            return False
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """
        Declare a queue (Redis list).
        
        Args:
            queue_name: Name of the queue
            durable: Ignored (Redis lists are always persistent if Redis is configured for persistence)
        """
        # Redis lists don't need explicit declaration
        # They're created on first use
        logger.info(f"Queue '{queue_name}' declared")
    
    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to the queue using Redis LPUSH.
        
        Args:
            queue_name: Name of the queue
            message: Message dictionary to publish
            
        Returns:
            bool: True if message was published successfully
        """
        try:
            # Ensure connection
            if not self.redis_client or not self._ping():
                if not self.connect():
                    return False
            
            # Serialize message to JSON
            message_str = json.dumps(message, default=str)
            
            # Push to Redis list (using LPUSH for queue-like behavior)
            self.redis_client.lpush(queue_name, message_str)
            
            # Set TTL on the queue for cleanup (optional, 7 days default)
            queue_ttl = int(os.getenv('REDIS_QUEUE_TTL', 604800))
            self.redis_client.expire(queue_name, queue_ttl)
            
            logger.info(f"Message published to Redis queue '{queue_name}'")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error publishing message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            return False
    
    def _ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def consume(self, queue_name: str, callback: Callable[[str], None], block_timeout: int = 1):
        """
        Start consuming messages from the queue using Redis blocking pop.
        
        Args:
            queue_name: Name of the queue
            callback: Function to call with each message
            block_timeout: Timeout in seconds for blocking pop (default 1)
        """
        def consumer_thread():
            logger.info(f"Started consuming from Redis queue '{queue_name}'")
            
            while True:
                try:
                    # Blocking pop from Redis list (using BRPOP with 0 for blocking)
                    # Returns tuple (queue_name, message) or (None, None) on timeout
                    result = self.redis_client.brpop(queue_name, timeout=block_timeout)
                    
                    if result is None:
                        # Timeout occurred, check for shutdown
                        continue
                    
                    _, message_bytes = result
                    
                    # Decode message
                    message_str = message_bytes.decode('utf-8')
                    
                    # Process message
                    callback(message_str)
                    
                except redis.ConnectionError:
                    logger.error("Redis connection lost, attempting to reconnect...")
                    time.sleep(5)
                    if not self.connect():
                        logger.error("Failed to reconnect to Redis")
                        return
                except Exception as e:
                    logger.error(f"Error processing message from Redis: {e}")
        
        # Start consumer thread
        import threading
        thread = threading.Thread(target=consumer_thread, daemon=True)
        thread.start()
        
        logger.info(f"Consumer thread started for queue '{queue_name}'")
        return thread
    
    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """
        Get information about a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Dict containing queue information
        """
        try:
            if not self.redis_client or not self._ping():
                return {"exists": False, "error": "Not connected"}
            
            queue_length = self.redis_client.llen(queue_name)
            
            return {
                "exists": True,
                "message_count": queue_length,
                "queue_name": queue_name,
                "type": "redis"
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis error getting queue info: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting queue info: {e}")
            return {"error": str(e)}
    
    def stop(self):
        """Stop the Redis connection."""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global queue instance (with fallback support)
_redis_queue = None
_simple_queue = None

def get_queue():
    """
    Get the global queue instance.
    Attempts to use Redis first, falls back to simple queue if Redis unavailable.
    
    Returns:
        Queue instance (RedisQueueManager or SimpleQueue)
    """
    global _redis_queue, _simple_queue
    
    # Try to use Redis if configured
    use_redis = os.getenv('USE_REDIS_QUEUE', 'true').lower() == 'true'
    
    if use_redis:
        if _redis_queue is None:
            _redis_queue = RedisQueueManager()
            
        # Test Redis connection
        if _redis_queue.connect():
            return _redis_queue
        else:
            logger.warning("Redis unavailable, falling back to in-memory queue")
    
    # Fall back to simple queue
    if _simple_queue is None:
        from simple_queue import SimpleQueue
        _simple_queue = SimpleQueue()
        logger.info("Using in-memory queue (Redis not available)")
    
    return _simple_queue

