#!/usr/bin/env python3
"""
Script para testar API diretamente
"""

import requests
import json

def test_register():
    url = "http://localhost:8000/api/v1/auth/register"
    import random
    random_id = random.randint(1000, 9999)
    data = {
        "email": f"novo_teste_{random_id}@example.com", 
        "password": "TesteSenha123@",
        "full_name": "Usuario API Teste Novo"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Python Test Script"
    }
    
    try:
        print("Testando registro via API...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("SUCESSO: Registro funcionou!")
        else:
            print(f"ERRO: Registro falhou com código {response.status_code}")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

def test_docs():
    url = "http://localhost:8000/docs"
    
    try:
        print("Testando documentação da API...")
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content Length: {len(response.text)}")
        
        if response.status_code == 200 and "swagger" in response.text.lower():
            print("SUCESSO: Documentação está funcionando!")
        else:
            print("ERRO: Problema com a documentação")
            
    except Exception as e:
        print(f"ERRO: Erro na requisição: {str(e)}")

if __name__ == "__main__":
    test_docs()
    test_register()