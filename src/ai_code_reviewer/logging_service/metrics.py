#!/usr/bin/env python3
"""
Prometheus Metrics for Logging Service

Provides Prometheus metrics for monitoring system health and performance.

Author: Code Review Enhancement Team
Created: 2025-01-XX
"""

import logging
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)

# ========== Counter Metrics ==========

# Log events received
log_events_total = Counter(
    'log_events_total',
    'Total number of log events received',
    ['event_type', 'status']
)

# API requests
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

# LLM queries
llm_queries_total = Counter(
    'llm_queries_total',
    'Total number of LLM queries',
    ['model', 'provider', 'status']
)

# ========== Histogram Metrics ==========

# Request duration
request_duration_seconds = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# LLM query duration
llm_query_duration_seconds = Histogram(
    'llm_query_duration_seconds',
    'LLM query duration in seconds',
    ['model', 'provider'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)

# Analysis duration
analysis_duration_seconds = Histogram(
    'analysis_duration_seconds',
    'Analysis duration in seconds',
    ['analysis_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ========== Gauge Metrics ==========

# Queue size
queue_size = Gauge(
    'queue_size',
    'Current queue size',
    ['queue_name']
)

# Active sessions
active_sessions = Gauge(
    'active_sessions',
    'Number of active review sessions'
)

# Database connections
database_connections = Gauge(
    'database_connections',
    'Number of active database connections',
    ['state']  # idle, active, etc.
)

# Cache hit rate
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    ['cache_type']
)

# ========== Info Metrics ==========

# Service version
service_info = Info(
    'service_info',
    'Service information'
)

# Initialize service info
service_info.info({
    'version': '2.0.0',
    'name': 'logging_service',
    'environment': 'production'
})


# ========== Helper Functions ==========

def increment_log_event(event_type: str, status: str = 'success'):
    """Increment log event counter."""
    log_events_total.labels(event_type=event_type, status=status).inc()


def increment_api_request(method: str, endpoint: str, status_code: int):
    """Increment API request counter."""
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()


def increment_llm_query(model: str, provider: str, status: str = 'success'):
    """Increment LLM query counter."""
    llm_queries_total.labels(
        model=model,
        provider=provider,
        status=status
    ).inc()


def record_request_duration(method: str, endpoint: str, duration: float):
    """Record request duration."""
    request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_llm_query_duration(model: str, provider: str, duration: float):
    """Record LLM query duration."""
    llm_query_duration_seconds.labels(
        model=model,
        provider=provider
    ).observe(duration)


def record_analysis_duration(analysis_type: str, duration: float):
    """Record analysis duration."""
    analysis_duration_seconds.labels(
        analysis_type=analysis_type
    ).observe(duration)


def set_queue_size(queue_name: str, size: int):
    """Set queue size gauge."""
    queue_size.labels(queue_name=queue_name).set(size)


def set_active_sessions(count: int):
    """Set active sessions gauge."""
    active_sessions.set(count)


def get_metrics():
    """Get metrics in Prometheus format."""
    return generate_latest()


# ========== Decorators ==========

import time
from functools import wraps

def track_duration(func):
    """Decorator to track function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            
            # Track duration based on function name
            func_name = func.__name__
            if 'llm' in func_name:
                record_llm_query_duration('unknown', 'unknown', duration)
            elif 'analysis' in func_name:
                record_analysis_duration('unknown', duration)
            
            return result
        except Exception as e:
            raise
        finally:
            duration = time.time() - start
            logger.debug(f"{func_name} took {duration:.2f}s")
    
    return wrapper

