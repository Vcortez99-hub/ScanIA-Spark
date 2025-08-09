#!/usr/bin/env python3
"""
Teste do endpoint debug simplificado
"""

import requests
import json
import random

def test_register_debug():
    """Teste do endpoint debug que retorna erro real"""
    url = "http://localhost:8000/api/v1/auth/register-debug"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"debug_endpoint_test_{random_id}@example.com",
        "password": "DebugEndpoint123@",
        "full_name": "Debug Endpoint Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("=== TESTANDO ENDPOINT DEBUG ===")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("SUCESSO: Endpoint debug funcionou!")
                print(f"User ID: {result.get('user_id')}")
            else:
                print("ERRO: Endpoint debug falhou:")
                print(f"Error: {result.get('error')}")
                print(f"Error Type: {result.get('error_type')}")
                if result.get('traceback'):
                    print("Traceback:")
                    print(result.get('traceback'))
        else:
            print(f"ERRO HTTP: Status {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test_register_debug()