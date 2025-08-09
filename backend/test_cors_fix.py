#!/usr/bin/env python3
"""
Teste específico para verificar CORS fix
"""

import requests
import json
import random

def test_cors_preflight():
    """Teste direto da requisição OPTIONS (CORS preflight)"""
    url = "http://localhost:8000/api/v1/auth/register"
    
    # Headers típicos de uma requisição CORS preflight
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("=== TESTANDO CORS PREFLIGHT (OPTIONS) ===")
        response = requests.options(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for header_name, header_value in response.headers.items():
            if "access-control" in header_name.lower() or "cors" in header_name.lower():
                print(f"  {header_name}: {header_value}")
        
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCESSO: CORS preflight funcionando!")
        elif response.status_code == 400:
            print("❌ ERRO 400: Ainda problema com CORS preflight")
        else:
            print(f"❓ STATUS {response.status_code}: Situação inesperada")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

def test_actual_register():
    """Teste da requisição POST real de registro"""
    url = "http://localhost:8000/api/v1/auth/register"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"cors_test_{random_id}@example.com",
        "password": "CorsTest123@",
        "full_name": "CORS Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("\n=== TESTANDO REGISTRO REAL (POST) ===")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCESSO: Registro funcionando!")
        elif response.status_code == 400:
            print("❌ ERRO 400: Problema com dados ou validação")
        elif response.status_code == 500:
            print("❌ ERRO 500: Problema interno do servidor")
        else:
            print(f"❓ STATUS {response.status_code}: Situação inesperada")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test_cors_preflight()
    test_actual_register()