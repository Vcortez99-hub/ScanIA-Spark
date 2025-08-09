#!/usr/bin/env python3
"""
Teste específico para encontrar o bug no UserResponse
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
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_exact_endpoint_logic():
    """Reproduzir exatamente o que acontece no endpoint"""
    try:
        async with AsyncSessionLocal() as db:
            print("=== TESTE EXACT ENDPOINT LOGIC ===")
            
            # Exatos mesmo dados e lógica do endpoint
            request = RegisterRequest(
                email="exact_endpoint_test@example.com",
                password="ExactEndpoint123@",
                full_name="Exact Endpoint Test User"
            )
            
            print(f"Request: {request}")
            
            auth_service = AuthService(db)
            
            # Apagar usuário se existir
            from sqlalchemy import select
            from app.models.user import User
            
            result = await db.execute(
                select(User).where(User.email == request.email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                await db.delete(existing_user)
                await db.commit()
            
            print("Step 1: Creating user via AuthService")
            user = await auth_service.create_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name
            )
            
            print(f"Step 2: User created successfully: {user.id}")
            print(f"User details: email={user.email}, role={user.role}, active={user.is_active}")
            
            print("Step 3: Creating UserResponse")
            print(f"Converting UUID {user.id} (type: {type(user.id)}) to string")
            
            # Testar ambos os métodos
            print("=== TESTE MÉTODO ANTIGO ===")
            try:
                user_response_old = UserResponse(
                    id=str(user.id),
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at
                )
                print(f"Método antigo SUCESSO: {user_response_old.id}")
                
                # Testar serialização JSON
                json_data = user_response_old.model_dump()
                print(f"JSON serialization: {json_data}")
                json_str = json.dumps(json_data, default=str)
                print(f"JSON string: {json_str}")
                
            except Exception as e:
                print(f"Método antigo FALHOU: {str(e)}")
                traceback.print_exc()
            
            print("=== TESTE MÉTODO NOVO ===")
            try:
                user_response_new = UserResponse.from_user(user)
                print(f"Método novo SUCESSO: {user_response_new.id}")
                
                # Testar serialização JSON
                json_data = user_response_new.model_dump()
                print(f"JSON serialization: {json_data}")
                json_str = json.dumps(json_data, default=str)
                print(f"JSON string: {json_str}")
                
            except Exception as e:
                print(f"Método novo FALHOU: {str(e)}")
                traceback.print_exc()
            
            print("=== SUCESSO COMPLETO ===")
            
    except Exception as e:
        print(f"\nERRO CAPTURADO: {str(e)}")
        print(f"Tipo do erro: {type(e).__name__}")
        print("Traceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_exact_endpoint_logic())