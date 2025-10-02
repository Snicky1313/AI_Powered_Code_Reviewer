#!/usr/bin/env python3
"""
Simple in-memory queue system
This allows testing the logging service without external dependencies
"""

import json
import queue
import threading
import time
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class SimpleQueue:
    """
    Simple in-memory queue that mimics basic RabbitMQ functionality
    """
    
    def __init__(self):
        self.queues: Dict[str, queue.Queue] = {}
        self.consumers: Dict[str, threading.Thread] = {}
        self.running = True
        
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue (create if it doesn't exist)"""
        if queue_name not in self.queues:
            self.queues[queue_name] = queue.Queue()
            logger.info(f"Queue '{queue_name}' declared")
    
    def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a queue"""
        try:
            if queue_name not in self.queues:
                self.declare_queue(queue_name)
            
            # Serialize message
            message_str = json.dumps(message, default=str)
            self.queues[queue_name].put(message_str)
            logger.info(f"Message published to queue '{queue_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def consume(self, queue_name: str, callback: Callable[[str], None]):
        """Start consuming messages from a queue"""
        def consumer_thread():
            logger.info(f"Started consuming from queue '{queue_name}'")
            
            while self.running:
                try:
                    # Get message with timeout to allow graceful shutdown
                    message = self.queues[queue_name].get(timeout=1)
                    
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
            "consumers": 1 if queue_name in self.consumers else 0
        }

# Global queue instance
simple_queue = SimpleQueue()

def get_queue():
    """Get the global queue instance"""
    return simple_queue