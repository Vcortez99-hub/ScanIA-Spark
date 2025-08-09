"""
Logging configuration for ScanIA
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from app.core.config import settings


def setup_logging():
    """Setup application logging configuration"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/scania.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/scania_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set specific logger levels based on environment
    if settings.ENVIRONMENT == "development":
        logging.getLogger("app").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    elif settings.ENVIRONMENT == "production":
        logging.getLogger("app").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for environment: {settings.ENVIRONMENT}")


class LoggerMixin:
    """Mixin to add logger to classes"""
    
    @property
    def logger(self):
        return logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with proper configuration"""
    return logging.getLogger(f"app.{name}")


# Security-focused logging
class SecurityLogger:
    """Security event logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("app.security")
        
        # Add security-specific handler
        security_handler = logging.FileHandler("logs/security.log")
        security_handler.setLevel(logging.INFO)
        security_formatter = logging.Formatter(
            "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
        )
        security_handler.setFormatter(security_formatter)
        self.logger.addHandler(security_handler)
    
    def log_login_attempt(self, email: str, success: bool, ip_address: str = None):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Login {status}: {email} from {ip_address or 'unknown'}")
    
    def log_logout(self, email: str, ip_address: str = None):
        """Log logout"""
        self.logger.info(f"Logout: {email} from {ip_address or 'unknown'}")
    
    def log_password_change(self, email: str, ip_address: str = None):
        """Log password change"""
        self.logger.info(f"Password changed: {email} from {ip_address or 'unknown'}")
    
    def log_failed_authorization(self, email: str, resource: str, ip_address: str = None):
        """Log failed authorization attempt"""
        self.logger.warning(f"Authorization failed: {email} tried to access {resource} from {ip_address or 'unknown'}")
    
    def log_suspicious_activity(self, description: str, email: str = None, ip_address: str = None):
        """Log suspicious activity"""
        self.logger.warning(f"Suspicious activity: {description} - User: {email or 'unknown'} - IP: {ip_address or 'unknown'}")
    
    def log_security_event(self, event_type: str, description: str, metadata: Dict[str, Any] = None):
        """Log general security event"""
        metadata_str = f" - Metadata: {metadata}" if metadata else ""
        self.logger.info(f"Security event [{event_type}]: {description}{metadata_str}")


# Create global security logger instance
security_logger = SecurityLogger()