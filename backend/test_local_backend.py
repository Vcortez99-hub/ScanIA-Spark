#!/usr/bin/env python3
"""
Teste do backend local na porta 8002
"""

import requests
import json
import random

def test_local_simple_register():
    url = "http://localhost:8002/api/v1/test/simple-register"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"local_simple_test_{random_id}@example.com",
        "password": "LocalSimpleTest123@",
        "full_name": "Local Simple Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("Testando endpoint simplificado LOCAL...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCESSO: Endpoint simplificado LOCAL funcionou!")
            result = response.json()
            print(f"User ID: {result.get('user_id')}")
        else:
            print(f"ERRO: Endpoint LOCAL falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

def test_local_original_register():
    url = "http://localhost:8002/api/v1/auth/register"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"local_original_test_{random_id}@example.com",
        "password": "LocalOriginalTest123@",
        "full_name": "Local Original Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("\nTestando endpoint original LOCAL...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("SUCESSO: Endpoint original LOCAL funcionou!")
        else:
            print(f"ERRO: Endpoint LOCAL falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

if __name__ == "__main__":
    test_local_simple_register()
    test_local_original_register()