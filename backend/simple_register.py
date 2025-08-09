#!/usr/bin/env python3
"""
Teste simplificado de registro
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import SecurityManager
from datetime import datetime
from sqlalchemy import select

async def test_simple_register():
    try:
        async with AsyncSessionLocal() as db:
            print("Iniciando teste de registro simples...")
            
            email = "simpletest@example.com"
            password = "TesteSenha123@"
            full_name = "Teste Simples"
            
            # Verificar se usuário já existe
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Usuario {email} já existe, removendo...")
                await db.delete(existing_user)
                await db.commit()
            
            # Validar senha
            security = SecurityManager()
            is_strong, message = security.is_strong_password(password)
            print(f"Validação de senha: {is_strong} - {message}")
            
            if not is_strong:
                print(f"ERRO: Senha não atende critérios - {message}")
                return
            
            # Criar usuário
            user = User(
                email=email,
                password_hash=security.hash_password(password),
                full_name=full_name,
                password_changed_at=datetime.utcnow()
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"SUCESSO: Usuario criado com ID {user.id}")
            
            # Testar autenticação
            auth_user = await authenticate_user_simple(db, email, password)
            if auth_user:
                print(f"SUCESSO: Autenticação funcionou para {auth_user.email}")
            else:
                print("ERRO: Falha na autenticação")
                
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()

async def authenticate_user_simple(db, email: str, password: str):
    """Teste simples de autenticação"""
    try:
        result = await db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        security = SecurityManager()
        if not security.verify_password(password, user.password_hash):
            return None
        
        return user
    except Exception as e:
        print(f"ERRO na autenticação: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(test_simple_register())