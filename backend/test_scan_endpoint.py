#!/usr/bin/env python3
"""
Teste específico para o endpoint de criação de scan
"""

import requests
import json

def test_create_scan():
    """Teste do endpoint POST /api/v1/scans"""
    
    # Primeiro fazer login para obter token
    login_url = "http://localhost:8000/api/v1/auth/login"
    scan_url = "http://localhost:8000/api/v1/scans"
    
    # Credenciais de um usuário existente
    login_data = {
        "email": "login_test_user@example.com",
        "password": "LoginTest123@"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("=== STEP 1: FAZENDO LOGIN ===")
        
        login_response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Erro no login: {login_response.text}")
            return
        
        # Extrair token
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        print(f"Token obtido: {access_token[:50]}...")
        
        print("\n=== STEP 2: CRIANDO SCAN ===")
        
        # Headers com token
        scan_headers = headers.copy()
        scan_headers["Authorization"] = f"Bearer {access_token}"
        
        # Dados do scan
        scan_data = {
            "target_url": "https://example.com",
            "scan_types": ["owasp_zap"],
            "environment_type": "testing",
            "options": {}
        }
        
        print(f"Dados do scan: {json.dumps(scan_data, indent=2)}")
        
        scan_response = requests.post(scan_url, json=scan_data, headers=scan_headers, timeout=30)
        
        print(f"Scan Status Code: {scan_response.status_code}")
        print(f"Scan Response Headers: {dict(scan_response.headers)}")
        print(f"Scan Response Body: {scan_response.text}")
        
        if scan_response.status_code == 201:
            print("SUCESSO: Scan criado com sucesso!")
            result = scan_response.json()
            print(f"Scan ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
        elif scan_response.status_code == 401:
            print("ERRO 401: Token inválido ou expirado")
        elif scan_response.status_code == 403:
            print("ERRO 403: Usuário sem permissão ou limite atingido")
        elif scan_response.status_code == 422:
            print("ERRO 422: Dados inválidos")
            try:
                error_detail = scan_response.json()
                print(f"Detalhes do erro: {json.dumps(error_detail, indent=2)}")
            except:
                pass
        elif scan_response.status_code == 500:
            print("ERRO 500: Erro interno do servidor")
            try:
                error_detail = scan_response.json().get('detail', 'No detail')
                print(f"Error detail: {error_detail}")
            except:
                pass
        else:
            print(f"ERRO HTTP: Status {scan_response.status_code}")
            
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test_create_scan()