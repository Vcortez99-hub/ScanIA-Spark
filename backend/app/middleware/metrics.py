"""
Prometheus metrics middleware
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge
    
    # Metrics definitions
    REQUEST_COUNT = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code']
    )
    
    REQUEST_DURATION = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    )
    
    ACTIVE_REQUESTS = Gauge(
        'http_requests_active',
        'Number of active HTTP requests'
    )
    
    PROMETHEUS_AVAILABLE = True
    
except ImportError:
    logger.warning("Prometheus client not available. Metrics disabled.")
    PROMETHEUS_AVAILABLE = False
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    ACTIVE_REQUESTS = None


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            method = request.method
            endpoint = self._get_endpoint(request)
            status_code = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        finally:
            # Always decrement active requests
            ACTIVE_REQUESTS.dec()
    
    def _get_endpoint(self, request: Request) -> str:
        """Extract endpoint pattern from request"""
        # Simple endpoint extraction
        path = request.url.path
        
        # Replace UUIDs and numbers with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path
        )
        
        # Replace numbers
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path or "/"