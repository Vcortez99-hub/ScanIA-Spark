#!/usr/bin/env python3
"""
Script para testar registro de usuário diretamente
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import SecurityManager
from datetime import datetime

async def test_register():
    try:
        async with AsyncSessionLocal() as db:
            # Verificar se usuário já existe
            print("Testando criação de usuário...")
            
            # Criar usuário
            security = SecurityManager()
            user = User(
                email="test@example.com",
                password_hash=security.hash_password("TesteSenha123"),
                full_name="Usuario Teste",
                password_changed_at=datetime.utcnow()
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"✅ Usuário criado com sucesso! ID: {user.id}")
            
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_register())