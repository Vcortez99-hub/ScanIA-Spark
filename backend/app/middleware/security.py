"""
Security middleware for ScanIA
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware to add security headers and perform basic security checks"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Security headers
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # CORS preflight requests (OPTIONS) should always be allowed
        if request.method == "OPTIONS":
            logger.info("CORS preflight request - allowing without security checks")
            response = await call_next(request)
        else:
            # Basic security checks for non-OPTIONS requests
            if self._is_suspicious_request(request):
                logger.warning(f"Suspicious request detected: {request.url}")
                return JSONResponse(
                    status_code=403,
                    content={"message": "Request blocked for security reasons"}
                )
            
            # Process request
            response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https: *"
        
        # Log response time
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Basic suspicious request detection - relaxed for development"""
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Don't block requests without user agent in development
        # if not user_agent:
        #     return True
        
        # Only block really dangerous scanners
        dangerous_agents = [
            "sqlmap", "nikto", "masscan"
        ]
        
        for agent in dangerous_agents:
            if agent in user_agent:
                return True
        
        # Only check for really dangerous paths
        path = str(request.url.path).lower()
        dangerous_paths = [
            "wp-admin", "phpmyadmin", ".env", "config.php"
        ]
        
        for danger_path in dangerous_paths:
            if danger_path in path:
                return True
        
        return False