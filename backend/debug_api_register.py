#!/usr/bin/env python3
"""
Debug específico do endpoint de registro da API
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.api.v1.auth import AuthService
from app.schemas.auth import RegisterRequest, UserResponse
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_api_register():
    """Debug exato do que acontece no endpoint register"""
    try:
        async with AsyncSessionLocal() as db:
            print("=== DEBUG API REGISTER ===")
            
            # Simular request exata
            request = RegisterRequest(
                email="api_debug_test@example.com",
                password="ApiDebugSenha123@",
                full_name="API Debug Test User"
            )
            
            print(f"Request: {request}")
            
            # Usar AuthService como no endpoint
            auth_service = AuthService(db)
            
            print("\n1. Executando create_user...")
            user = await auth_service.create_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name
            )
            
            print(f"   Usuario criado: {user}")
            print(f"   User.id: {user.id} (tipo: {type(user.id)})")
            print(f"   User.role: {user.role} (tipo: {type(user.role)})")
            
            print("\n2. Criando UserResponse...")
            
            # Tentar criar response exatamente como no endpoint
            user_response = UserResponse(
                id=str(user.id),  # Convertendo UUID para string
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            
            print(f"   UserResponse criado: {user_response}")
            print(f"   Response ID: {user_response.id}")
            
            print("\n=== SUCESSO NO DEBUG DA API ===")
            
    except Exception as e:
        print(f"\nERRO CAPTURADO NA API: {str(e)}")
        print(f"Tipo do erro: {type(e).__name__}")
        print("\nTraceback completo:")
        traceback.print_exc()

async def test_user_response_conversion():
    """Testar especificamente a conversão User -> UserResponse"""
    try:
        print("\n=== TEST USER RESPONSE CONVERSION ===")
        
        # Criar um user mockado
        from app.models.user import User, UserRole
        from datetime import datetime
        import uuid
        
        mock_user = User(
            id=uuid.uuid4(),
            email="mock@test.com", 
            full_name="Mock User",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now()
        )
        
        print(f"Mock user: {mock_user.email}")
        print(f"Mock user ID: {mock_user.id} (tipo: {type(mock_user.id)})")
        print(f"Mock user role: {mock_user.role} (tipo: {type(mock_user.role)})")
        
        # Tentar criar UserResponse
        response = UserResponse(
            id=str(mock_user.id),
            email=mock_user.email,
            full_name=mock_user.full_name,
            role=mock_user.role,
            is_active=mock_user.is_active,
            created_at=mock_user.created_at
        )
        
        print(f"Response criado: {response}")
        print("=== CONVERSAO SUCESSO ===")
        
    except Exception as e:
        print(f"ERRO NA CONVERSAO: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_response_conversion())
    asyncio.run(debug_api_register())