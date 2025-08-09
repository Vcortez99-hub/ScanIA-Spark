"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
import json


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=1, description="Senha do usuário")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=8, description="Senha (mínimo 8 caracteres)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError('Nome completo é obrigatório')
        return v.strip()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    @classmethod
    def from_user(cls, user) -> "UserResponse":
        """Create UserResponse from User model with explicit conversion"""
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Nova senha deve ter pelo menos 8 caracteres')
        return v