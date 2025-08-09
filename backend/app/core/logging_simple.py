"""
Simplified logging configuration for development
"""

import logging
import sys

def setup_logging():
    """Setup basic logging"""
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Setup app logger
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    
    return app_logger

def get_logger(name: str):
    """Get logger instance"""
    return logging.getLogger(name)

class SecurityLogger:
    """Simple security logger"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_login_attempt(self, email: str, success: bool, ip_address: str = None):
        if success:
            self.logger.info(f"Login successful: {email} from {ip_address}")
        else:
            self.logger.warning(f"Login failed: {email} from {ip_address}")
    
    def log_logout(self, email: str, ip_address: str = None):
        self.logger.info(f"Logout: {email} from {ip_address}")
    
    def log_password_change(self, email: str, ip_address: str = None):
        self.logger.info(f"Password changed: {email} from {ip_address}")
    
    def log_security_event(self, event_type: str, message: str, extra_data: dict = None):
        self.logger.warning(f"Security event {event_type}: {message}")

# Create global instances
security_logger = SecurityLogger()