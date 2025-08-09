#!/usr/bin/env python3
"""
Teste do endpoint simplificado
"""

import requests
import json

def test_simple_register():
    url = "http://localhost:8000/api/v1/test/simple-register"
    import random
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"simple_test_{random_id}@example.com",
        "password": "SimpleEndpoint123@",
        "full_name": "Simple Endpoint Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("Testando endpoint simplificado...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCESSO: Endpoint simplificado funcionou!")
            result = response.json()
            print(f"User ID: {result.get('user_id')}")
        else:
            print(f"ERRO: Endpoint falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

def test_original_register():
    url = "http://localhost:8000/api/v1/auth/register"
    import random
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"original_test_{random_id}@example.com",
        "password": "OriginalEndpoint123@",
        "full_name": "Original Endpoint Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("\nTestando endpoint original...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("SUCESSO: Endpoint original funcionou!")
        else:
            print(f"ERRO: Endpoint falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

if __name__ == "__main__":
    test_simple_register()
    test_original_register()