"""
Endpoint de teste simplificado
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.api.v1.auth import AuthService
from app.schemas.auth import RegisterRequest
import logging

router = APIRouter(prefix="/test", tags=["test"])
logger = logging.getLogger(__name__)

@router.post("/simple-register")
async def simple_register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Test endpoint sem UserResponse"""
    try:
        logger.info(f"Simple register called with: {request.email}")
        
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        logger.info(f"User created: {user.id}")
        
        # Retornar dict simples sem Pydantic model
        return {
            "success": True,
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple register: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))