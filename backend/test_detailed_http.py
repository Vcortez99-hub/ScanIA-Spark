#!/usr/bin/env python3
"""
Teste HTTP detalhado para capturar o erro exato
"""

import requests
import json
import random
import logging
import urllib3

# Habilitar logs detalhados do urllib3/requests
logging.basicConfig(level=logging.DEBUG)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.DEBUG)
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.DEBUG)

def test_detailed_register():
    """Teste com logging detalhado"""
    url = "http://localhost:8000/api/v1/auth/register"
    random_id = random.randint(10000, 99999)
    data = {
        "email": f"detailed_http_test_{random_id}@example.com",
        "password": "DetailedHttp123@",
        "full_name": "Detailed HTTP Test User"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
    
    try:
        print("=== TESTE HTTP DETALHADO ===")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print(f"Headers: {json.dumps(dict(headers), indent=2)}")
        
        print("\n--- ENVIANDO REQUEST ---")
        response = requests.post(
            url, 
            json=data, 
            headers=headers, 
            timeout=30,
            verify=False  # Disable SSL verification for local testing
        )
        
        print("\n--- RESPONSE RECEBIDO ---")
        print(f"Status Code: {response.status_code}")
        print(f"Status Text: {response.reason}")
        print(f"Response Headers:")
        for header_name, header_value in response.headers.items():
            print(f"  {header_name}: {header_value}")
        
        print(f"\nResponse Content Length: {len(response.content)} bytes")
        print(f"Response Text Length: {len(response.text)} chars")
        print(f"Response Content: {response.content}")
        print(f"Response Text: {response.text}")
        
        # Tentar parse JSON se possível
        try:
            json_response = response.json()
            print(f"Response JSON: {json.dumps(json_response, indent=2)}")
        except Exception as json_e:
            print(f"Could not parse JSON: {json_e}")
        
        # Análise do resultado
        if response.status_code == 201:
            print("\n✅ SUCESSO: Registro funcionou!")
        elif response.status_code == 400:
            print("\n❌ ERRO 400: Bad Request - possível validação ou usuário já existe")
        elif response.status_code == 500:
            print("\n❌ ERRO 500: Internal Server Error - erro no servidor")
            print("Isso confirma que há uma exception não tratada no servidor")
        else:
            print(f"\n❓ ERRO {response.status_code}: Status inesperado")
            
    except requests.exceptions.ConnectionError as conn_e:
        print(f"\n❌ ERRO DE CONEXÃO: {conn_e}")
        print("Backend não está rodando na porta 8000")
    except requests.exceptions.Timeout as timeout_e:
        print(f"\n❌ ERRO DE TIMEOUT: {timeout_e}")
        print("Request demorou mais de 30 segundos")
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {str(e)}")
        print(f"Tipo: {type(e).__name__}")

if __name__ == "__main__":
    test_detailed_register()