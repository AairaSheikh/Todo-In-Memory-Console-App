"""Middleware for rate limiting and other cross-cutting concerns."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse.
    
    Applies rate limiting to chat endpoint (10 requests per minute per user).
    Returns 429 Too Many Requests when limit exceeded.
    
    **Validates: Requirements 10.1, 10.2**
    """
    
    def __init__(self, app, requests_per_minute: int = 10):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per user (default: 10)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Store request history: {user_id: [(timestamp, request_count), ...]}
        self.request_history: Dict[str, list] = {}
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and apply rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler
            
        Returns:
            Response: The response from the next handler or 429 if rate limited
            
        **Validates: Requirements 10.1, 10.2**
        """
        # Only apply rate limiting to chat endpoint
        if not request.url.path.endswith("/chat"):
            return await call_next(request)
        
        # Extract user_id from path
        path_parts = request.url.path.split("/")
        if len(path_parts) < 3:
            return await call_next(request)
        
        user_id = path_parts[2]
        
        # Check rate limit
        async with self.lock:
            is_limited = self._check_rate_limit(user_id)
        
        if is_limited:
            # Return 429 Too Many Requests
            return Response(
                content="Too many requests. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": "60"},
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            bool: True if rate limited, False otherwise
            
        **Validates: Requirements 10.1, 10.2**
        """
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Initialize user history if not exists
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.request_history[user_id] = [
            timestamp for timestamp in self.request_history[user_id]
            if timestamp > one_minute_ago
        ]
        
        # Check if user has exceeded limit
        if len(self.request_history[user_id]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.request_history[user_id].append(now)
        return False
