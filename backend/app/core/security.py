"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
import secrets
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate secure reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate API key"""
        return f"sia_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, api_key_hash: str) -> bool:
        """Verify API key against hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, str]:
        """Check if password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Basic input sanitization"""
        if not input_string:
            return ""
        
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def check_rate_limit(identifier: str, limit: int, window: int) -> bool:
        """Check rate limiting (placeholder for Redis implementation)"""
        # This would be implemented with Redis in a real application
        # For now, always return True (no rate limiting)
        return True


class PasswordValidator:
    """Password validation utilities"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @classmethod
    def validate(cls, password: str) -> Dict[str, Any]:
        """Comprehensive password validation"""
        errors = []
        score = 0
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        elif len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must be no more than {cls.MAX_LENGTH} characters long")
        else:
            score += 1
        
        # Check character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if has_upper:
            score += 1
        else:
            errors.append("Password must contain at least one uppercase letter")
        
        if has_lower:
            score += 1
        else:
            errors.append("Password must contain at least one lowercase letter")
        
        if has_digit:
            score += 1
        else:
            errors.append("Password must contain at least one digit")
        
        if has_special:
            score += 1
        else:
            errors.append("Password must contain at least one special character")
        
        # Calculate strength
        if score >= 5:
            strength = "strong"
        elif score >= 3:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": score
        }


# Export security manager instance
security = SecurityManager()