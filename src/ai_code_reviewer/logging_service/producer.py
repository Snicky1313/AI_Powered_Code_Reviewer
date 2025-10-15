#!/usr/bin/env python3
"""
AI-Powered Python Code Reviewer - Logging Service Producer (Simple Queue Version)

This FastAPI application serves as the producer in the asynchronous logging system.
It accepts log events via HTTP POST requests and publishes them to a simple in-memory queue
for processing by the consumer service. No RabbitMQ required!

Author: AI Code Reviewer Team
Created: 2025-09-28
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from simple_queue import get_queue

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Code Review Logging Service - Producer (Simple Queue)",
    description="Asynchronous logging service producer for secure audit trails - No RabbitMQ required!",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LogEvent(BaseModel):
    """
    Log event model that defines the structure of incoming log data.
    """
    session_id: int = Field(..., description="Review session ID", gt=0)
    event_type: str = Field(
        ..., 
        description="Type of event (e.g., 'review_started', 'llm_query_sent')",
        min_length=1,
        max_length=100
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible JSON payload containing event-specific data"
    )
    timestamp: Optional[str] = Field(
        None,
        description="Event timestamp (ISO format). If not provided, current time will be used"
    )
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Validate that event_type contains only allowed characters."""
        allowed_events = {
            'review_started', 'review_completed', 'review_cancelled',
            'llm_query_sent', 'llm_feedback_received', 'llm_error',
            'syntax_analysis_started', 'syntax_analysis_completed',
            'style_analysis_started', 'style_analysis_completed',
            'security_scan_started', 'security_scan_completed',
            'performance_analysis_started', 'performance_analysis_completed',
            'report_generated', 'user_action', 'system_event'
        }
        
        # Allow any event type but log unknown ones for monitoring
        if v not in allowed_events:
            logger.warning(f"Unknown event type received: {v}")
        
        return v
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is in ISO format or set to current time."""
        if v is None:
            return datetime.now().isoformat()
        
        # Validate ISO format
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Timestamp must be in ISO format")


class LogResponse(BaseModel):
    """Response model for successful log submissions."""
    status: str = "accepted"
    message: str
    event_id: Optional[str] = None
    timestamp: str


class SimpleQueueManager:
    """
    Manages simple queue operations for the producer service.
    """
    
    def __init__(self):
        self.queue = get_queue()
        self.queue_name = os.getenv('RABBITMQ_QUEUE_NAME', 'log_queue')
        
    def connect(self):
        """Initialize the queue (declare it)."""
        try:
            self.queue.declare_queue(self.queue_name, durable=True)
            logger.info(f"Successfully initialized queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize queue: {str(e)}")
            raise
    
    def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Publish a message to the queue.
        
        Args:
            message: The log event message to publish
            
        Returns:
            bool: True if message was published successfully
        """
        try:
            success = self.queue.publish(self.queue_name, message)
            
            if success:
                logger.info(f"Successfully published message to queue: {self.queue_name}")
            else:
                logger.error(f"Failed to publish message to queue: {self.queue_name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue status information."""
        try:
            return self.queue.get_queue_info(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue info: {str(e)}")
            return {"error": str(e)}


# Global queue manager instance
queue_manager = SimpleQueueManager()


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    try:
        queue_manager.connect()
        logger.info("Producer service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize producer service: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    try:
        queue_manager.queue.stop()
        logger.info("Producer service shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Code Review Logging Service - Producer (Simple Queue)",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "queue_type": "in-memory",
        "endpoints": {
            "log": "/log",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        queue_info = queue_manager.get_queue_info()
        
        return {
            "status": "healthy",
            "service": "producer",
            "timestamp": datetime.now().isoformat(),
            "queue_type": "in-memory",
            "queue_info": queue_info
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "producer",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/log", response_model=LogResponse, status_code=202)
async def log_event(log_event: LogEvent):
    """
    Accept and queue log events for processing.
    
    This endpoint accepts log events and publishes them to the simple queue for
    asynchronous processing by the consumer service.
    
    Args:
        log_event: The log event data to be processed
        
    Returns:
        LogResponse: Confirmation of log acceptance
    """
    try:
        # Prepare the message for the queue
        message = {
            "session_id": log_event.session_id,
            "event_type": log_event.event_type,
            "payload": log_event.payload,
            "timestamp": log_event.timestamp or datetime.now().isoformat(),
            "producer_timestamp": datetime.now().isoformat()
        }
        
        # Publish to queue
        success = queue_manager.publish_message(message)
        
        if not success:
            raise HTTPException(
                status_code=503,
                detail="Failed to queue log event. Service temporarily unavailable."
            )
        
        # Log the successful submission
        logger.info(
            f"Log event accepted: session_id={log_event.session_id}, "
            f"event_type={log_event.event_type}"
        )
        
        return LogResponse(
            message="Log event accepted and queued for processing",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing log event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/queue/status")
async def queue_status():
    """
    Get queue status information (for monitoring/debugging).
    """
    try:
        queue_info = queue_manager.get_queue_info()
        
        return {
            "queue_name": queue_manager.queue_name,
            "queue_type": "in-memory",
            "queue_info": queue_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve queue status: {str(e)}"
        )


if __name__ == "__main__":
    """
    Run the producer service.
    
    Usage:
        python producer_simple.py
    """
    host = os.getenv('PRODUCER_HOST', '0.0.0.0')
    port = int(os.getenv('PRODUCER_PORT', 8001))
    
    logger.info(f"Starting producer service on {host}:{port}")
    
    uvicorn.run(
        "producer_simple:app",
        host=host,
        port=port,
        reload=os.getenv('ENVIRONMENT') == 'development',
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )
