# Makefile para ScanIA
.PHONY: help install dev build test clean deploy

# Default target
help:
	@echo "ScanIA - Sistema de Cybersegurança"
	@echo "Comandos disponíveis:"
	@echo "  install     - Instalar dependências"
	@echo "  dev         - Iniciar ambiente de desenvolvimento"
	@echo "  build       - Build para produção"
	@echo "  test        - Executar todos os testes"
	@echo "  clean       - Limpar containers e volumes"
	@echo "  deploy      - Deploy para produção"
	@echo "  migrate     - Executar migrações do banco"
	@echo "  seed        - Popular banco com dados de teste"

# Instalar dependências
install:
	@echo "🔧 Instalando dependências do frontend..."
	cd frontend && npm install
	@echo "🔧 Instalando dependências do backend..."
	cd backend && pip install -r requirements.txt
	@echo "🔧 Configurando pre-commit hooks..."
	pre-commit install

# Iniciar ambiente de desenvolvimento
dev:
	@echo "🚀 Iniciando ambiente de desenvolvimento..."
	docker-compose up -d postgres redis minio owasp-zap
	@echo "⏳ Aguardando serviços iniciarem..."
	sleep 10
	@echo "🗄️ Executando migrações do banco..."
	cd backend && alembic upgrade head
	@echo "🎯 Iniciando backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "⚡ Iniciando frontend..."
	cd frontend && npm run dev &
	@echo "🔄 Iniciando Celery worker..."
	cd backend && celery -A app.core.celery_app worker --loglevel=info &
	@echo "✅ Ambiente de desenvolvimento iniciado!"
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔗 Backend API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"

# Build para produção
build:
	@echo "🏗️ Building frontend..."
	cd frontend && npm run build
	@echo "🐳 Building Docker images..."
	docker-compose -f docker-compose.prod.yml build

# Executar testes
test:
	@echo "🧪 Executando testes do backend..."
	cd backend && pytest tests/ -v --cov=app --cov-report=xml
	@echo "🧪 Executando testes do frontend..."
	cd frontend && npm run test
	@echo "🧪 Executando testes E2E..."
	cd frontend && npm run test:e2e

# Limpar ambiente
clean:
	@echo "🧹 Parando containers..."
	docker-compose down
	@echo "🗑️ Removendo volumes..."
	docker-compose down -v
	@echo "🧹 Limpando imagens..."
	docker system prune -f

# Deploy para produção
deploy:
	@echo "🚀 Fazendo deploy para produção..."
	./scripts/deploy.sh

# Executar migrações
migrate:
	@echo "🗄️ Executando migrações do banco..."
	cd backend && alembic upgrade head

# Popular banco com dados de teste
seed:
	@echo "🌱 Populando banco com dados de teste..."
	cd backend && python scripts/seed_db.py

# Backup do banco
backup:
	@echo "💾 Criando backup do banco..."
	./scripts/backup.sh

# Atualizar dependências
update:
	@echo "⬆️ Atualizando dependências do frontend..."
	cd frontend && npm update
	@echo "⬆️ Atualizando dependências do backend..."
	cd backend && pip install --upgrade -r requirements.txt

# Verificação de qualidade do código
lint:
	@echo "🔍 Executando linting..."
	cd frontend && npm run lint
	cd backend && flake8 app/
	cd backend && black app/ --check
	cd backend && isort app/ --check-only

# Formatação do código
format:
	@echo "✨ Formatando código..."
	cd frontend && npm run lint:fix
	cd backend && black app/
	cd backend && isort app/

# Scan de segurança
security:
	@echo "🔒 Executando scan de segurança..."
	cd frontend && npm audit
	cd backend && safety check
	cd backend && bandit -r app/