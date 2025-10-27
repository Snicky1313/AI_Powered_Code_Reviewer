"""
Logging Helper Module
Provides easy-to-use functions for logging events across the system.
Handles connection to the logging service and graceful degradation.

Author: Code Review Enhancement Team
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Configuration
LOGGING_SERVICE_URL = os.getenv('LOGGING_SERVICE_URL', 'http://localhost:8001/log')
LOGGING_ENABLED = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'


def log_event(
    session_id: int,
    event_type: str,
    payload: Dict[str, Any] = None,
    timeout: int = 5
) -> bool:
    """
    Log an event to the logging service.
    
    Args:
        session_id: Review session ID
        event_type: Type of event (e.g., 'review_started', 'syntax_analysis_completed')
        payload: Event-specific data
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if event was logged successfully (or logging is disabled)
    
    Examples:
        >>> # Log a review submission
        >>> log_event(
        ...     session_id=123,
        ...     event_type='review_started',
        ...     payload={'user_id': 'user123', 'language': 'python'}
        ... )
        
        >>> # Log analysis completion
        >>> log_event(
        ...     session_id=123,
        ...     event_type='syntax_analysis_completed',
        ...     payload={'issues': 2, 'warnings': 1}
        ... )
    """
    if not LOGGING_ENABLED:
        return True
    
    if payload is None:
        payload = {}
    
    try:
        response = requests.post(
            LOGGING_SERVICE_URL,
            json={
                'session_id': session_id,
                'event_type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            },
            timeout=timeout
        )
        
        if response.status_code in [200, 202]:
            logger.debug(f"Logged event: {event_type} for session {session_id}")
            return True
        else:
            logger.warning(f"Failed to log event: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.debug("Logging service unavailable (connection error)")
        return False
    except requests.exceptions.Timeout:
        logger.debug("Logging service unavailable (timeout)")
        return False
    except Exception as e:
        logger.debug(f"Error logging event: {str(e)}")
        return False


def log_review_started(session_id: int, user_id: str, language: str, code_length: int) -> bool:
    """Log when a review session starts."""
    return log_event(
        session_id=session_id,
        event_type='review_started',
        payload={
            'user_id': user_id,
            'language': language,
            'code_length': code_length
        }
    )


def log_review_completed(session_id: int, analysis_count: int, success: bool) -> bool:
    """Log when a review session completes."""
    return log_event(
        session_id=session_id,
        event_type='review_completed',
        payload={
            'analysis_count': analysis_count,
            'success': success
        }
    )


def log_analysis_started(session_id: int, analysis_type: str) -> bool:
    """Log when an analysis starts."""
    return log_event(
        session_id=session_id,
        event_type=f'{analysis_type}_analysis_started',
        payload={'analysis_type': analysis_type}
    )


def log_analysis_completed(session_id: int, analysis_type: str, results: Dict[str, Any]) -> bool:
    """Log when an analysis completes."""
    return log_event(
        session_id=session_id,
        event_type=f'{analysis_type}_analysis_completed',
        payload={
            'analysis_type': analysis_type,
            'results': results
        }
    )


def log_llm_query(session_id: int, model: str, tokens_used: int, cost: float) -> bool:
    """Log when an LLM query is made."""
    return log_event(
        session_id=session_id,
        event_type='llm_query_sent',
        payload={
            'model': model,
            'tokens_used': tokens_used,
            'cost': cost
        }
    )


def log_llm_feedback_received(session_id: int, model: str, feedback_length: int) -> bool:
    """Log when LLM feedback is received."""
    return log_event(
        session_id=session_id,
        event_type='llm_feedback_received',
        payload={
            'model': model,
            'feedback_length': feedback_length
        }
    )


def log_error(session_id: int, error_type: str, error_message: str) -> bool:
    """Log an error event."""
    return log_event(
        session_id=session_id,
        event_type='error_occurred',
        payload={
            'error_type': error_type,
            'error_message': error_message
        }
    )

