"""
Authentication endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.database import get_async_db
from app.core.security import security
from app.core.logging_simple import security_logger
from app.models.user import User, UserSession
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, UserResponse,
    TokenRefreshRequest, PasswordChangeRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security_scheme = HTTPBearer()

# Explicit OPTIONS handler for CORS preflight
@router.options("/register")
async def register_options():
    """Handle CORS preflight for register endpoint"""
    return {"status": "ok"}


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        # Get user by email
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Verify password
        if not security.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create_user(self, email: str, password: str, full_name: str) -> User:
        """Create new user"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        is_strong, message = security.is_strong_password(password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Create user
        user = User(
            email=email,
            password_hash=security.hash_password(password),
            full_name=full_name,
            password_changed_at=datetime.utcnow()
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def create_session(self, user: User, ip_address: str = None, user_agent: str = None) -> str:
        """Create user session and return JWT token"""
        # Create JWT token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "session_id": security.generate_session_id()
        }
        
        access_token = security.create_access_token(data=token_data)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=token_data["session_id"],
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=1440)  # 24 hours
        )
        
        self.db.add(session)
        
        # Update user last login
        user.last_login = datetime.utcnow()
        
        await self.db.commit()
        
        return access_token
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        # Decode token
        payload = security.verify_token(token)
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify session is still valid
        if session_id:
            result = await self.db.execute(
                select(UserSession).where(
                    UserSession.session_token == session_id,
                    UserSession.user_id == user.id,
                    UserSession.is_active == True
                )
            )
            session = result.scalar_one_or_none()
            
            if not session or not session.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return user


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Dependency to get current authenticated user"""
    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials.credentials)


# Dependency to get current admin user
async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/register-debug")
async def register_debug(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Super simplified register endpoint for debugging"""
    try:
        # Step 1: Create user with minimal logic
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        # Step 2: Return simple dict (no Pydantic response model)
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": str(user.id),
            "email": user.email
        }
        
    except HTTPException as he:
        return {"success": False, "error": f"HTTPException: {he.detail}"}
    except Exception as e:
        import traceback
        return {
            "success": False, 
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db),
    http_request: Request = None
):
    """Register new user"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== REGISTER ENDPOINT START ===")
    logger.info(f"Request data: email={request.email}, full_name={request.full_name}")
    
    auth_service = AuthService(db)
    
    try:
        logger.info("=== STEP 1: Starting user creation ===")
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        logger.info("=== STEP 1: User creation completed ===")
        
        logger.info("=== STEP 2: Logging user details ===")
        logger.info(f"User created successfully: {user.id}")
        logger.info(f"User details: email={user.email}, role={user.role}, active={user.is_active}")
        logger.info("=== STEP 2: User details logged ===")
        
        logger.info("=== STEP 3: Creating UserResponse ===")
        logger.info(f"Converting UUID {user.id} (type: {type(user.id)}) to string")
        user_response = UserResponse.from_user(user)
        logger.info("=== STEP 3: UserResponse created successfully ===")
        
        logger.info("=== STEP 4: Preparing to return response ===")
        logger.info(f"UserResponse ID: {user_response.id}")
        logger.info(f"UserResponse type: {type(user_response)}")
        logger.info("=== STEP 4: About to return user_response ===")
        
        # Try different response strategies
        logger.info("=== TRYING MANUAL RESPONSE CREATION ===")
        
        # Create response manually as dict first
        response_dict = {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        logger.info(f"Response dict created: {response_dict}")
        
        # Create UserResponse from dict
        final_user_response = UserResponse(**response_dict)
        logger.info(f"Final UserResponse created: {final_user_response.id}")
        
        return final_user_response
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in register: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR in register endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        security_logger.log_security_event(
            "REGISTRATION_ERROR",
            f"Registration failed for {request.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DEBUG ERROR: {str(e)} | Type: {type(e).__name__} | Args: {e.args}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_db),
    http_request: Request = None
):
    """Authenticate user and return access token"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== LOGIN ENDPOINT START ===")
    logger.info(f"Login attempt for: {request.email}")
    
    auth_service = AuthService(db)
    ip_address = http_request.client.host if http_request else None
    user_agent = http_request.headers.get("user-agent") if http_request else None
    
    try:
        logger.info("=== STEP 1: Authenticating user ===")
        # Authenticate user
        user = await auth_service.authenticate_user(request.email, request.password)
        
        if not user:
            logger.warning(f"Authentication failed for: {request.email}")
            security_logger.log_login_attempt(request.email, False, ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"=== STEP 2: User authenticated successfully: {user.id} ===")
        
        logger.info("=== STEP 3: Creating session and token ===")
        # Create session and token
        access_token = await auth_service.create_session(user, ip_address, user_agent)
        logger.info("=== STEP 3: Session created successfully ===")
        
        logger.info("=== STEP 4: Creating UserResponse ===")
        user_response = UserResponse.from_user(user)
        logger.info("=== STEP 4: UserResponse created successfully ===")
        
        logger.info("=== STEP 5: Creating LoginResponse ===")
        login_response = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1440 * 60,  # 24 hours in seconds
            user=user_response
        )
        logger.info("=== STEP 5: LoginResponse created successfully ===")
        
        # Log successful login
        security_logger.log_login_attempt(request.email, True, ip_address)
        
        logger.info("=== LOGIN ENDPOINT SUCCESS ===")
        return login_response
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in login: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR in login endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        security_logger.log_security_event(
            "LOGIN_ERROR",
            f"Login error for {request.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DEBUG LOGIN ERROR: {str(e)} | Type: {type(e).__name__}"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    http_request: Request = None
):
    """Logout user and revoke session"""
    try:
        # Get session token from authorization header
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = security.verify_token(token)
            session_id = payload.get("session_id")
            
            if session_id:
                # Revoke session
                result = await db.execute(
                    select(UserSession).where(
                        UserSession.session_token == session_id,
                        UserSession.user_id == current_user.id
                    )
                )
                session = result.scalar_one_or_none()
                
                if session:
                    session.revoke("logout")
                    await db.commit()
        
        # Log logout
        ip_address = http_request.client.host if http_request else None
        security_logger.log_logout(current_user.email, ip_address)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        security_logger.log_security_event(
            "LOGOUT_ERROR",
            f"Logout error for {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_user(current_user)


@router.post("/register-simple")
async def register_simple(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Simplified register endpoint for debugging"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Simple register called for: {request.email}")
        
        # Step 1: Create user directly
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        logger.info(f"User created with ID: {user.id}")
        
        # Step 2: Return simple dict (no Pydantic model)
        return {
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
        
    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    http_request: Request = None
):
    """Change user password"""
    try:
        # Verify current password
        if not security.verify_password(request.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        is_strong, message = security.is_strong_password(request.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Update password
        current_user.password_hash = security.hash_password(request.new_password)
        current_user.password_changed_at = datetime.utcnow()
        
        await db.commit()
        
        # Log password change
        ip_address = http_request.client.host if http_request else None
        security_logger.log_password_change(current_user.email, ip_address)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        security_logger.log_security_event(
            "PASSWORD_CHANGE_ERROR",
            f"Password change error for {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )