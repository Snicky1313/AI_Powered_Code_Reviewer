#!/usr/bin/env python3
"""
Authentication and Rate Limiting Middleware for Logging Service

Provides API key authentication and rate limiting for endpoints.

Author: Code Review Enhancement Team
Created: 2025-01-XX
"""

import os
import time
import logging
import hashlib
from typing import Optional
from fastapi import HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps

logger = logging.getLogger(__name__)

# API Keys (in production, store in secure vault)
API_KEYS = {
    'test_key_123': 'test_client',
    'prod_key_456': 'production_client'
}

# Rate limiting storage (in-memory, use Redis in production)
_rate_limits = {}


class RateLimit:
    """Simple rate limiter."""
    
    def __init__(self, requests: int, window: int):
        """
        Initialize rate limiter.
        
        Args:
            requests: Number of requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
    
    def check_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Client identifier (API key or IP)
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        
        if key not in _rate_limits:
            _rate_limits[key] = []
        
        # Clean old requests
        _rate_limits[key] = [
            req_time for req_time in _rate_limits[key]
            if now - req_time < self.window
        ]
        
        # Check limit
        if len(_rate_limits[key]) >= self.requests:
            return False
        
        # Add current request
        _rate_limits[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        if key not in _rate_limits:
            return self.requests
        
        now = time.time()
        _rate_limits[key] = [
            req_time for req_time in _rate_limits[key]
            if now - req_time < self.window
        ]
        
        return max(0, self.requests - len(_rate_limits[key]))


# Security
security = HTTPBearer(auto_error=False)


def verify_api_key(api_key: str) -> Optional[str]:
    """
    Verify API key and return client name.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        Client name if valid, None otherwise
    """
    return API_KEYS.get(api_key)


def require_api_key(func):
    """Decorator to require API key authentication."""
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        # Remove 'Bearer ' prefix if present
        if api_key and api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        # Verify API key
        client = verify_api_key(api_key) if api_key else None
        
        if not client:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Provide X-API-Key header."
            )
        
        # Add client to request state
        request.state.client = client
        
        return await func(*args, request=request, **kwargs)
    
    return wrapper


def rate_limit(requests: int = 100, window: int = 60):
    """
    Decorator to apply rate limiting.
    
    Args:
        requests: Number of requests allowed per window
        window: Time window in seconds
    """
    def decorator(func):
        limiter = RateLimit(requests, window)
        
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            # Get identifier (API key or IP)
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]
            
            identifier = api_key if api_key else request.client.host
            
            # Check rate limit
            if not limiter.check_limit(identifier):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "requests_allowed": requests,
                        "window_seconds": window,
                        "try_again_after": limiter.window
                    }
                )
            
            # Add rate limit headers
            response = await func(*args, request=request, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(requests)
                response.headers['X-RateLimit-Remaining'] = str(limiter.get_remaining(identifier))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + window))
            
            return response
        
        return wrapper
    return decorator


def get_client_from_request(request: Request) -> Optional[str]:
    """Get client name from request."""
    if hasattr(request.state, 'client'):
        return request.state.client
    return 'anonymous'


# Configuration
ADMIN_KEY = os.getenv('ADMIN_API_KEY', 'admin_key_789')
PROD_KEY = os.getenv('PROD_API_KEY', 'prod_key_456')


def is_admin(request: Request) -> bool:
    """Check if request is from admin."""
    api_key = request.headers.get('X-API-Key')
    return api_key == ADMIN_KEY


# Default rate limits
DEFAULT_RATE_LIMIT = RateLimit(requests=100, window=60)  # 100 requests per minute
STRICT_RATE_LIMIT = RateLimit(requests=10, window=60)    # 10 requests per minute

