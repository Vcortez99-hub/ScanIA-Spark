"""
API v1 Router - Centralized routing configuration
"""

from fastapi import APIRouter

from app.api.v1 import auth, scans, vulnerabilities, test_simple

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router)

# Include scan management routes
api_router.include_router(scans.router)

# Include vulnerability management routes
api_router.include_router(vulnerabilities.router)

# Include test routes
api_router.include_router(test_simple.router)