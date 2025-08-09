"""
Configuration settings for ScanIA backend
"""

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "ScanIA"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    DATABASE_URL: str = "postgresql://scania_user:scania_pass@localhost:5432/scania_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Security settings
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    
    # OWASP ZAP settings
    OWASP_ZAP_HOST: str = "localhost"
    OWASP_ZAP_PORT: int = 8080
    OWASP_ZAP_API_KEY: str = "development-zap-key"
    
    # Nmap settings
    NMAP_PATH: str = "/usr/bin/nmap"
    NMAP_TIMEOUT: int = 300
    
    # File storage settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "scania-files"
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # External API keys
    CVE_API_KEY: Optional[str] = None
    VIRUSTOTAL_API_KEY: Optional[str] = None
    SHODAN_API_KEY: Optional[str] = None
    NVD_API_KEY: Optional[str] = None
    OTX_API_KEY: Optional[str] = None
    
    # Monitoring settings
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @validator("JWT_SECRET_KEY", pre=True)
    def validate_jwt_secret(cls, v):
        if not v or v == "your-super-secret-jwt-key-change-in-production":
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("JWT_SECRET_KEY must be set for production")
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True) 
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()