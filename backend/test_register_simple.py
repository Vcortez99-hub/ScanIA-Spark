#!/usr/bin/env python3
"""
Teste do endpoint register-simple
"""

import requests
import json
import random

def test_register_simple():
    url = "http://localhost:8000/api/v1/auth/register-simple"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"simple_reg_test_{random_id}@example.com",
        "password": "SimpleRegTest123@",
        "full_name": "Simple Reg Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("Testando endpoint register-simple...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCESSO: Endpoint register-simple funcionou!")
            result = response.json()
            print(f"User ID: {result.get('user', {}).get('id')}")
        else:
            print(f"ERRO: Endpoint falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

if __name__ == "__main__":
    test_register_simple()