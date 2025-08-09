@echo off
cd /d "%~dp0\backend"
set DATABASE_URL=postgresql://scania_user:scania_pass@localhost:5433/scania_db
set REDIS_URL=redis://localhost:6381/0
set JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
set OWASP_ZAP_HOST=localhost
set OWASP_ZAP_PORT=8080
set OWASP_ZAP_API_KEY=development-zap-key
set ENVIRONMENT=development
set DEBUG=true

echo 🚀 Iniciando ScanIA Backend...
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload