# Configuração do Ambiente - ScanIA

## 🔧 Setup Inicial

### Pré-requisitos do Sistema

#### Hardware Mínimo
- **CPU**: 4 cores / 8 threads (Intel i5 ou AMD Ryzen 5)
- **RAM**: 8GB (16GB recomendado para desenvolvimento)
- **Storage**: 50GB SSD disponível
- **Network**: Conexão banda larga estável

#### Software Base
- **OS**: Ubuntu 20.04+ / macOS 12+ / Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 15+ (ou via Docker)
- **Redis**: 7+ (ou via Docker)

### Estrutura de Diretórios

```bash
scania/
├── frontend/                 # React/Next.js application
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Next.js pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API services
│   │   ├── types/           # TypeScript types
│   │   ├── utils/           # Utility functions
│   │   └── styles/          # Global styles
│   ├── public/              # Static assets
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── core/            # Core configuration
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utility functions
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Test files
│   ├── alembic/             # Database migrations
│   ├── requirements.txt
│   └── pyproject.toml
├── scanner/                 # Scanner engine
│   ├── engines/             # Scanner implementations
│   ├── analyzers/           # Vulnerability analyzers
│   ├── databases/           # CVE and threat databases
│   ├── reporting/           # Report generators
│   └── tasks.py             # Celery tasks
├── docker/                  # Docker configurations
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   ├── Dockerfile.scanner
│   └── nginx.conf
├── scripts/                 # Utility scripts
│   ├── setup.sh             # Initial setup
│   ├── deploy.sh            # Deployment script
│   ├── backup.sh            # Backup script
│   └── migrate.sh           # Database migration
├── docs/                    # Documentation
├── .env.example             # Environment template
├── docker-compose.yml       # Local development
├── docker-compose.prod.yml  # Production
└── Makefile                 # Common commands
```

## 🐳 Docker Setup

### Docker Compose para Desenvolvimento

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Frontend Development Server
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
      target: development
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    depends_on:
      - backend
    networks:
      - scania-network

  # Backend API Server
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - scanner_data:/app/scanner_data
    environment:
      - DATABASE_URL=postgresql://scania_user:scania_pass@postgres:5432/scania_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OWASP_ZAP_API_KEY=${OWASP_ZAP_API_KEY}
      - ENVIRONMENT=development
    depends_on:
      - postgres
      - redis
    networks:
      - scania-network

  # Scanner Engine
  scanner:
    build:
      context: ./scanner
      dockerfile: ../docker/Dockerfile.scanner
    volumes:
      - scanner_data:/app/data
      - ./scanner:/app
    environment:
      - DATABASE_URL=postgresql://scania_user:scania_pass@postgres:5432/scania_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis
      - owasp-zap
    networks:
      - scania-network

  # OWASP ZAP Scanner
  owasp-zap:
    image: owasp/zap2docker-stable:latest
    command: zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=${OWASP_ZAP_API_KEY}
    ports:
      - "8080:8080"
    volumes:
      - zap_data:/zap/wrk
    networks:
      - scania-network

  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=scania_user
      - POSTGRES_PASSWORD=scania_pass
      - POSTGRES_DB=scania_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - scania-network

  # Redis Cache/Queue
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - scania-network

  # Celery Worker
  celery-worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      target: development
    command: celery -A app.core.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
      - scanner_data:/app/scanner_data
    environment:
      - DATABASE_URL=postgresql://scania_user:scania_pass@postgres:5432/scania_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis
    networks:
      - scania-network

  # MinIO File Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin123
    volumes:
      - minio_data:/data
    networks:
      - scania-network

volumes:
  postgres_data:
  redis_data:
  minio_data:
  scanner_data:
  zap_data:

networks:
  scania-network:
    driver: bridge
```

### Dockerfiles

#### Frontend Dockerfile
```dockerfile
# docker/Dockerfile.frontend
# Multi-stage build for Next.js

# Development stage
FROM node:18-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Dependencies stage
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Builder stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine AS production
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

#### Backend Dockerfile
```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    nmap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Development stage
FROM base AS development
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash scania
RUN chown -R scania:scania /app
USER scania

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## ⚙️ Variáveis de Ambiente

### Arquivo .env de Desenvolvimento

```bash
# .env.development

# Database Configuration
DATABASE_URL=postgresql://scania_user:scania_pass@localhost:5432/scania_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OWASP ZAP Configuration
OWASP_ZAP_HOST=localhost
OWASP_ZAP_PORT=8080
OWASP_ZAP_API_KEY=your-zap-api-key

# Nmap Configuration
NMAP_PATH=/usr/bin/nmap
NMAP_TIMEOUT=300

# File Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=scania-files

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@scania.com

# External APIs
CVE_API_KEY=your-cve-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key
SHODAN_API_KEY=your-shodan-api-key

# Application Settings
APP_NAME=ScanIA
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Arquivo .env de Produção

```bash
# .env.production

# Database Configuration
DATABASE_URL=postgresql://username:password@prod-db-host:5432/scania_prod
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Redis Configuration
REDIS_URL=redis://prod-redis-host:6379/0
REDIS_CACHE_TTL=600

# JWT Configuration
JWT_SECRET_KEY=${JWT_SECRET_KEY_FROM_SECRETS_MANAGER}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/scania.crt
SSL_KEY_PATH=/etc/ssl/private/scania.key

# CDN Configuration
CDN_URL=https://cdn.scania.com
STATIC_FILES_URL=https://static.scania.com

# Application Settings
APP_NAME=ScanIA
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Rate Limiting (more restrictive)
RATE_LIMIT_REQUESTS_PER_MINUTE=30
RATE_LIMIT_REQUESTS_PER_HOUR=500

# Security (restrictive)
ALLOWED_HOSTS=scania.com,www.scania.com,api.scania.com
CORS_ORIGINS=https://scania.com,https://www.scania.com

# Monitoring
SENTRY_DSN=${SENTRY_DSN_FROM_SECRETS}
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

## 🗄️ Configuração do Banco de Dados

### Script de Inicialização

```sql
-- scripts/init.sql
-- Database initialization script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'user', 'readonly');
CREATE TYPE scan_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE vulnerability_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info');
CREATE TYPE report_type AS ENUM ('executive_summary', 'technical_detailed', 'compliance_report', 'vulnerability_list');

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS scan_number_seq START 1000;

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_user_id_created_at ON scans(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_scan_id_severity ON vulnerabilities(scan_id, severity);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_cve_id ON vulnerabilities(cve_id) WHERE cve_id IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_scan_id_type ON reports(scan_id, report_type);

-- Create full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_title_fts ON vulnerabilities USING gin(to_tsvector('portuguese', title));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_description_fts ON vulnerabilities USING gin(to_tsvector('portuguese', description));

-- Create composite indexes for dashboard queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_user_status_created ON scans(user_id, status, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulns_scan_severity_status ON vulnerabilities(scan_id, severity, status);

-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW IF NOT EXISTS user_security_stats AS
SELECT 
    s.user_id,
    COUNT(DISTINCT s.id) as total_scans,
    COUNT(DISTINCT v.id) as total_vulnerabilities,
    COUNT(DISTINCT CASE WHEN v.severity = 'critical' THEN v.id END) as critical_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'high' THEN v.id END) as high_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'medium' THEN v.id END) as medium_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'low' THEN v.id END) as low_vulns,
    COUNT(DISTINCT s.target_url) as unique_targets,
    AVG(v.cvss_score) as avg_cvss_score,
    MAX(s.created_at) as last_scan_date
FROM scans s
LEFT JOIN vulnerabilities v ON s.id = v.scan_id
WHERE s.created_at >= NOW() - INTERVAL '90 days'
GROUP BY s.user_id;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS user_security_stats_user_id_idx ON user_security_stats (user_id);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_user_security_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_security_stats;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-refresh stats
CREATE OR REPLACE FUNCTION trigger_refresh_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Refresh stats asynchronously
    PERFORM pg_notify('refresh_stats', 'user_security_stats');
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers to relevant tables
DROP TRIGGER IF EXISTS scan_stats_refresh ON scans;
CREATE TRIGGER scan_stats_refresh
    AFTER INSERT OR UPDATE OR DELETE ON scans
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_stats();

DROP TRIGGER IF EXISTS vuln_stats_refresh ON vulnerabilities;
CREATE TRIGGER vuln_stats_refresh
    AFTER INSERT OR UPDATE OR DELETE ON vulnerabilities
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_stats();
```

### Configuração do Alembic

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.models.base import Base

# Alembic Config object
config = context.config

# Set database URL
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 🔧 Configuração de Desenvolvimento

### Makefile para Comandos Comuns

```makefile
# Makefile
.PHONY: help install dev build test clean deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development environment"
	@echo "  build       - Build for production"
	@echo "  test        - Run all tests"
	@echo "  clean       - Clean up containers and volumes"
	@echo "  deploy      - Deploy to production"
	@echo "  migrate     - Run database migrations"
	@echo "  seed        - Seed database with test data"

# Install dependencies
install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Setting up pre-commit hooks..."
	pre-commit install

# Start development environment
dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres redis minio owasp-zap
	@echo "Waiting for services to start..."
	sleep 10
	@echo "Running database migrations..."
	cd backend && alembic upgrade head
	@echo "Starting backend..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev &
	@echo "Starting Celery worker..."
	cd backend && celery -A app.core.celery_app worker --loglevel=info &
	@echo "Development environment started!"

# Build for production
build:
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Building Docker images..."
	docker-compose -f docker-compose.prod.yml build

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm run test
	@echo "Running E2E tests..."
	cd frontend && npm run test:e2e

# Clean up
clean:
	@echo "Stopping containers..."
	docker-compose down
	@echo "Removing volumes..."
	docker-compose down -v
	@echo "Cleaning up images..."
	docker system prune -f

# Deploy to production
deploy:
	@echo "Deploying to production..."
	./scripts/deploy.sh

# Run database migrations
migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

# Seed database
seed:
	@echo "Seeding database with test data..."
	cd backend && python scripts/seed_db.py

# Backup database
backup:
	@echo "Creating database backup..."
	./scripts/backup.sh

# Restore database
restore:
	@echo "Restoring database..."
	./scripts/restore.sh $(file)

# Update dependencies
update:
	@echo "Updating frontend dependencies..."
	cd frontend && npm update
	@echo "Updating backend dependencies..."
	cd backend && pip install --upgrade -r requirements.txt

# Code quality checks
lint:
	@echo "Running linting..."
	cd frontend && npm run lint
	cd backend && flake8 app/
	cd backend && black app/ --check
	cd backend && isort app/ --check-only

# Format code
format:
	@echo "Formatting code..."
	cd frontend && npm run lint:fix
	cd backend && black app/
	cd backend && isort app/

# Security scan
security:
	@echo "Running security scan..."
	cd frontend && npm audit
	cd backend && safety check
	cd backend && bandit -r app/
```

### Scripts de Utilitários

#### Setup Script
```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "🚀 Setting up ScanIA development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Prerequisites check passed!"

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd frontend && npm install && cd ..
cd backend && pip install -r requirements.txt && cd ..

# Setup database
echo "🗄️ Setting up database..."
docker-compose up -d postgres redis
echo "⏳ Waiting for database to start..."
sleep 10

cd backend
alembic upgrade head
python scripts/seed_db.py
cd ..

# Setup OWASP ZAP
echo "🔒 Setting up OWASP ZAP..."
docker-compose up -d owasp-zap
echo "⏳ Waiting for OWASP ZAP to start..."
sleep 15

# Generate API key for ZAP
ZAP_API_KEY=$(openssl rand -hex 16)
echo "OWASP_ZAP_API_KEY=$ZAP_API_KEY" >> .env

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make dev' to start development environment"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "🔗 Useful URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  OWASP ZAP: http://localhost:8080"
echo "  MinIO Console: http://localhost:9001"
```

---

**Esta configuração garante um ambiente de desenvolvimento completo e padronizado para o ScanIA.**