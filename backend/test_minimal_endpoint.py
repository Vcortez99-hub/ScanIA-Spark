#!/usr/bin/env python3
"""
Endpoint mínimo de teste para isolar o problema
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.api.v1.auth import AuthService
from app.schemas.auth import RegisterRequest

# App mínima sem middlewares complexos
app = FastAPI(title="Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.post("/test-register")
async def test_register(request: RegisterRequest):
    """Endpoint de teste minimo para registro"""
    try:
        print(f"Request recebida: {request}")
        
        async with AsyncSessionLocal() as db:
            auth_service = AuthService(db)
            
            user = await auth_service.create_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name
            )
            
            print(f"Usuario criado: {user}")
            
            return {
                "status": "success",
                "user_id": str(user.id),
                "email": user.email,
                "message": "User created successfully"
            }
            
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"Erro capturado: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/test-health")
async def test_health():
    return {"status": "ok", "message": "Test API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)