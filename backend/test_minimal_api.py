#!/usr/bin/env python3
"""
Teste da API mínima
"""

import requests
import json

def test_minimal_register():
    url = "http://localhost:8001/test-register"
    data = {
        "email": "minimal_test@example.com",
        "password": "MinimalTest123@",
        "full_name": "Minimal Test User"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        print("Testando API mínima...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCESSO: API mínima funcionou!")
        else:
            print("ERRO: API mínima falhou")
            
    except requests.exceptions.ConnectionError:
        print("ERRO: Não conseguiu conectar na API teste (porta 8001)")
    except Exception as e:
        print(f"ERRO: {str(e)}")

def test_main_register():
    url = "http://localhost:8000/api/v1/auth/register"
    data = {
        "email": "comparison_test@example.com",
        "password": "ComparisonTest123@",
        "full_name": "Comparison Test User"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        print("\nTestando API principal...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test_minimal_register()
    test_main_register()