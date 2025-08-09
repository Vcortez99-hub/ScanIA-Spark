# Script para executar ScanIA em ambiente de desenvolvimento
Write-Host "🚀 Iniciando ScanIA - Sistema Inteligente de Análise de Cybersegurança" -ForegroundColor Cyan
Write-Host ""

# Verificar se o Docker está rodando
Write-Host "📋 Verificando pré-requisitos..." -ForegroundColor Yellow

try {
    docker --version | Out-Null
    Write-Host "✅ Docker encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não encontrado. Por favor, instale o Docker Desktop." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose." -ForegroundColor Red
    exit 1
}

# Verificar se Node.js está instalado
try {
    node --version | Out-Null
    Write-Host "✅ Node.js encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js não encontrado. Por favor, instale o Node.js 18+." -ForegroundColor Red
    exit 1
}

# Verificar se Python está instalado
try {
    python --version | Out-Null
    Write-Host "✅ Python encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado. Por favor, instale o Python 3.9+." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🐳 Iniciando serviços com Docker Compose..." -ForegroundColor Yellow

# Iniciar serviços de banco de dados e cache
docker-compose up -d postgres redis minio

Write-Host ""
Write-Host "⏳ Aguardando serviços ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Instalar dependências do backend se necessário
Write-Host "📦 Instalando dependências do backend..." -ForegroundColor Yellow
Set-Location backend
if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment criado" -ForegroundColor Green
}

# Ativar virtual environment
Write-Host "🔧 Ativando virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Instalar dependências
pip install -r requirements.txt

Write-Host ""
Write-Host "📦 Instalando dependências do frontend..." -ForegroundColor Yellow
Set-Location ../frontend
npm install

Set-Location ..

Write-Host ""
Write-Host "🚀 Aplicação ScanIA está pronta!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 URLs de acesso:" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   • Banco de Dados: localhost:5432" -ForegroundColor White
Write-Host "   • Redis: localhost:6379" -ForegroundColor White
Write-Host "   • MinIO: http://localhost:9001" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Execute os comandos abaixo em terminais separados:" -ForegroundColor Yellow
Write-Host ""
Write-Host "📱 Terminal 1 - Backend:" -ForegroundColor Green
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   venv\Scripts\activate" -ForegroundColor White
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "💻 Terminal 2 - Frontend:" -ForegroundColor Green
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")