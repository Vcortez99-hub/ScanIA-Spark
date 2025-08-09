#!/usr/bin/env python3
"""
Debug script para investigar erro de registro
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.api.v1.auth import AuthService
from app.schemas.auth import RegisterRequest
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_register():
    """Debug registration process step by step"""
    try:
        async with AsyncSessionLocal() as db:
            print("=== DEBUG REGISTRO ===")
            
            # Dados de teste
            email = "debug_test@example.com"
            password = "DebugSenha123@"
            full_name = "Debug Test User"
            
            print(f"Email: {email}")
            print(f"Senha: {password}")
            print(f"Nome: {full_name}")
            
            # Criar serviço de autenticação
            auth_service = AuthService(db)
            
            # Tentar criar usuário passo a passo
            print("\n1. Verificando se usuário já existe...")
            from sqlalchemy import select
            from app.models.user import User
            
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"   Usuario {email} já existe, removendo...")
                await db.delete(existing_user)
                await db.commit()
                print("   Usuario removido!")
            else:
                print("   Usuario não existe - OK")
            
            print("\n2. Validando senha...")
            from app.core.security import security
            is_strong, message = security.is_strong_password(password)
            print(f"   Validação: {is_strong} - {message}")
            
            if not is_strong:
                print(f"   ERRO: Senha inválida")
                return
            
            print("\n3. Criando hash da senha...")
            password_hash = security.hash_password(password)
            print(f"   Hash gerado: {password_hash[:20]}...")
            
            print("\n4. Criando objeto User...")
            from datetime import datetime
            from app.models.user import UserRole
            
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                role=UserRole.USER,
                password_changed_at=datetime.utcnow()
            )
            
            print(f"   Usuario criado: {user.email}, Role: {user.role}")
            
            print("\n5. Salvando no banco...")
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"   SUCESSO! Usuario salvo com ID: {user.id}")
            
            # Testar se o usuário foi mesmo criado
            print("\n6. Verificando se foi salvo...")
            result = await db.execute(
                select(User).where(User.id == user.id)
            )
            saved_user = result.scalar_one_or_none()
            
            if saved_user:
                print(f"   CONFIRMADO: Usuario {saved_user.email} existe no banco")
            else:
                print("   ERRO: Usuario não foi encontrado no banco!")
            
            print("\n=== SUCESSO TOTAL ===")
            
    except Exception as e:
        print(f"\nERRO CAPTURADO: {str(e)}")
        print("\nTraceback completo:")
        traceback.print_exc()
        
        # Tentar identificar o tipo específico do erro
        print(f"\nTipo do erro: {type(e).__name__}")
        print(f"Args do erro: {e.args}")

if __name__ == "__main__":
    asyncio.run(debug_register())