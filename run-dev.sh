#!/bin/bash

# Script para executar ScanIA em ambiente de desenvolvimento
echo "🚀 Iniciando ScanIA - Sistema Inteligente de Análise de Cybersegurança"
echo ""

# Verificar se o Docker está rodando
echo "📋 Verificando pré-requisitos..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Por favor, instale o Docker."
    exit 1
fi
echo "✅ Docker encontrado"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi
echo "✅ Docker Compose encontrado"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale o Node.js 18+."
    exit 1
fi
echo "✅ Node.js encontrado"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python não encontrado. Por favor, instale o Python 3.9+."
    exit 1
fi
echo "✅ Python encontrado"

echo ""
echo "🐳 Iniciando serviços com Docker Compose..."

# Iniciar serviços de banco de dados e cache
docker-compose up -d postgres redis minio

echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Instalar dependências do backend se necessário
echo "📦 Instalando dependências do backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment criado"
fi

# Ativar virtual environment
echo "🔧 Ativando virtual environment..."
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

echo ""
echo "📦 Instalando dependências do frontend..."
cd ../frontend
npm install

cd ..

echo ""
echo "🚀 Aplicação ScanIA está pronta!"
echo ""
echo "📍 URLs de acesso:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Banco de Dados: localhost:5432"
echo "   • Redis: localhost:6379"
echo "   • MinIO: http://localhost:9001"
echo ""
echo "⚠️  IMPORTANTE: Execute os comandos abaixo em terminais separados:"
echo ""
echo "📱 Terminal 1 - Backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "💻 Terminal 2 - Frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "Pressione Enter para continuar..."
read