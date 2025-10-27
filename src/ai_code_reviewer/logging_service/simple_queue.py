#!/usr/bin/env python3
"""
Simple in-memory queue system - DEPRECATED
This file is kept for backward compatibility with the fallback mechanism.

The service now uses Redis for persistent storage (see redis_queue.py).
This simple queue is only used as a fallback when Redis is unavailable.

DO NOT USE THIS IN PRODUCTION - Use Redis instead!
"""

import json
import queue
import threading
import time
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class SimpleQueue:
    """
    Simple in-memory queue that mimics basic RabbitMQ functionality.
    DEPRECATED: Use Redis for production deployments.
    """
    
    def __init__(self):
        self.queues: Dict[str, queue.Queue] = {}
        self.consumers: Dict[str, threading.Thread] = {}
        self.running = True
        
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue (create if it doesn't exist)"""
        if queue_name not in self.queues:
            self.queues[queue_name] = queue.Queue()
            logger.warning(f"Using in-memory queue for '{queue_name}' - NOT PERSISTENT!")
            
    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a queue"""
        try:
            if queue_name not in self.queues:
                self.declare_queue(queue_name)
            
            # Serialize message
            message_str = json.dumps(message, default=str)
            self.queues[queue_name].put(message_str)
            logger.info(f"Message published to in-memory queue '{queue_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def consume(self, queue_name: str, callback: Callable[[str], None], block_timeout: int = 1):
        """Start consuming messages from the queue"""
        def consumer_thread():
            logger.warning(f"Consuming from in-memory queue '{queue_name}' - NOT PERSISTENT!")
            
            while self.running:
                try:
                    # Get message with timeout to allow graceful shutdown
                    message = self.queues[queue_name].get(timeout=block_timeout)
                    
                    # Process message
                    callback(message)
                    
                    # Mark task as done
                    self.queues[queue_name].task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        # Ensure queue exists
        if queue_name not in self.queues:
            self.declare_queue(queue_name)
        
        # Start consumer thread
        thread = threading.Thread(target=consumer_thread, daemon=True)
        thread.start()
        self.consumers[queue_name] = thread
        
        return thread
    
    def stop(self):
        """Stop all consumers"""
        self.running = False
        
        # Wait for consumers to finish
        for thread in self.consumers.values():
            if thread.is_alive():
                thread.join(timeout=2)
        
        logger.info("Simple queue stopped")
    
    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get information about a queue"""
        if queue_name not in self.queues:
            return {"exists": False}
        
        return {
            "exists": True,
            "message_count": self.queues[queue_name].qsize(),
            "consumers": 1 if queue_name in self.consumers else 0,
            "type": "in-memory",
            "warning": "NOT PERSISTENT - Data will be lost on restart!"
        }

# Global queue instance
simple_queue = SimpleQueue()

def get_queue():
    """Get the global queue instance"""
    return simple_queue

