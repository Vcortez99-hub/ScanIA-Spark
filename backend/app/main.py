"""
ScanIA - Sistema Inteligente de Análise de Cybersegurança
FastAPI Main Application
"""

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import settings
from app.core.logging_simple import setup_logging
from app.api.v1.router import api_router
from app.middleware.security import SecurityMiddleware
from app.middleware.metrics import PrometheusMiddleware
from app.core.database import create_tables


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("🚀 Starting ScanIA backend...")
    
    # Create database tables
    await create_tables()
    logger.info("✅ Database tables created/verified")
    
    # Initialize services
    logger.info("✅ ScanIA backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("📴 Shutting down ScanIA backend...")


# Create FastAPI application
app = FastAPI(
    title="ScanIA API",
    description="Sistema Inteligente de Análise de Cybersegurança",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS middleware (must be first for proper handling)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware (with CORS preflight support)
app.add_middleware(SecurityMiddleware)

# Trusted host middleware (temporarily disabled for debugging)
# app.add_middleware(
#     TrustedHostMiddleware, 
#     allowed_hosts=settings.ALLOWED_HOSTS
# )

# Prometheus metrics middleware
if settings.PROMETHEUS_ENABLED:
    app.add_middleware(PrometheusMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "ScanIA Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ScanIA - Sistema Inteligente de Análise de Cybersegurança",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "Contact admin for API documentation",
        "status": "running"
    }

# Global exception handler (temporarily disabled for debugging)
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     logger.error(f"Global exception: {str(exc)}", exc_info=True)
#     
#     return JSONResponse(
#         status_code=500,
#         content={
#             "message": "Internal server error",
#             "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
#         }
#     )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )