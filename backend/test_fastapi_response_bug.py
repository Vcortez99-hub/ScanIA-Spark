#!/usr/bin/env python3
"""
Teste específico para identificar problema FastAPI response
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import AsyncSessionLocal
from app.api.v1.auth import AuthService
from app.schemas.auth import RegisterRequest, UserResponse
import json
from datetime import datetime

# Criar uma app FastAPI mínima para teste
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Função para simular o que o FastAPI faz internamente
def simulate_fastapi_response_serialization(user_response: UserResponse):
    """Simular o processo de serialização de resposta do FastAPI"""
    try:
        print("=== SIMULAÇÃO SERIALIZAÇÃO FASTAPI ===")
        
        # Step 1: Pydantic model_dump (igual ao que FastAPI faz)
        print("Step 1: Pydantic model_dump...")
        response_dict = user_response.model_dump()
        print(f"model_dump() result: {response_dict}")
        
        # Step 2: JSON serialization (igual ao que FastAPI faz)
        print("Step 2: JSON serialization...")
        
        # Testar diferentes métodos de serialização JSON
        print("2a: JSON com default=str")
        json_str_1 = json.dumps(response_dict, default=str)
        print(f"Result: {json_str_1}")
        
        print("2b: JSON com ensure_ascii=False")
        json_str_2 = json.dumps(response_dict, default=str, ensure_ascii=False)
        print(f"Result: {json_str_2}")
        
        print("2c: JSON com modo Pydantic")
        json_str_3 = user_response.model_dump_json()
        print(f"Result: {json_str_3}")
        
        # Step 3: Simular parsing de volta
        print("Step 3: Parse back from JSON...")
        parsed_1 = json.loads(json_str_1)
        parsed_2 = json.loads(json_str_2) 
        parsed_3 = json.loads(json_str_3)
        print(f"Parsed 1: {parsed_1}")
        print(f"Parsed 2: {parsed_2}")
        print(f"Parsed 3: {parsed_3}")
        
        print("=== TODOS OS MÉTODOS FUNCIONARAM ===")
        return True
        
    except Exception as e:
        print(f"ERRO na simulação FastAPI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Teste principal"""
    try:
        async with AsyncSessionLocal() as db:
            print("=== TESTE FASTAPI RESPONSE BUG ===")
            
            # Criar um UserResponse usando dados reais
            request = RegisterRequest(
                email="fastapi_response_test@example.com",
                password="FastApiResponse123@",
                full_name="FastAPI Response Test User"
            )
            
            auth_service = AuthService(db)
            
            # Remover usuário se existir
            from sqlalchemy import select
            from app.models.user import User
            
            result = await db.execute(
                select(User).where(User.email == request.email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                await db.delete(existing_user)
                await db.commit()
            
            # Criar usuário
            user = await auth_service.create_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name
            )
            
            print(f"User created: {user.id}")
            
            # Criar UserResponse
            user_response = UserResponse.from_user(user)
            print(f"UserResponse created: {user_response.id}")
            
            # Testar serialização igual ao FastAPI
            success = simulate_fastapi_response_serialization(user_response)
            
            if success:
                print("=== CONCLUSÃO: PROBLEMA NÃO É NA SERIALIZAÇÃO ===")
                print("O problema deve ser em middleware ou configuração FastAPI")
            else:
                print("=== CONCLUSÃO: PROBLEMA ENCONTRADO NA SERIALIZAÇÃO ===")
                
    except Exception as e:
        print(f"ERRO GERAL: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())