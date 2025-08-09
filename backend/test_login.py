#!/usr/bin/env python3
"""
Teste específico para o endpoint de login
"""

import requests
import json

def test_login_with_existing_user():
    """Teste de login usando credenciais de um usuário que foi criado"""
    
    # Primeiro, vamos criar um usuário para fazer login
    register_url = "http://localhost:8000/api/v1/auth/register"
    login_url = "http://localhost:8000/api/v1/auth/login"
    
    # Dados do usuário
    email = "login_test_user@example.com"
    password = "LoginTest123@"
    full_name = "Login Test User"
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("=== STEP 1: CRIANDO USUARIO PARA LOGIN ===")
        
        # Criar usuário primeiro (pode já existir)
        register_data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        
        register_response = requests.post(register_url, json=register_data, headers=headers, timeout=10)
        print(f"Register Status: {register_response.status_code}")
        
        if register_response.status_code == 201:
            print("Usuario criado com sucesso")
        elif register_response.status_code == 400:
            print("Usuario já existe (ok para o teste)")
        else:
            print(f"Erro inesperado no registro: {register_response.text}")
        
        print("\n=== STEP 2: TESTANDO LOGIN ===")
        
        # Tentar fazer login
        login_data = {
            "email": email,
            "password": password
        }
        
        login_response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        
        print(f"Login Status Code: {login_response.status_code}")
        print(f"Login Response Headers: {dict(login_response.headers)}")
        print(f"Login Response Body: {login_response.text}")
        
        if login_response.status_code == 200:
            print("SUCESSO: Login funcionou!")
            result = login_response.json()
            print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"User ID: {result.get('user', {}).get('id')}")
        elif login_response.status_code == 401:
            print("ERRO 401: Credenciais incorretas")
        elif login_response.status_code == 500:
            print("ERRO 500: Erro interno do servidor")
            try:
                error_detail = login_response.json().get('detail', 'No detail')
                print(f"Error detail: {error_detail}")
            except:
                pass
        else:
            print(f"ERRO HTTP: Status {login_response.status_code}")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test_login_with_existing_user()