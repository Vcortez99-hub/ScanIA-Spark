# Deploy e CI/CD - ScanIA

## 🚀 Estratégia de Deploy

### Ambientes de Deploy

```mermaid
graph LR
    DEV[Development<br/>Local Machine] --> STG[Staging<br/>Testing Environment]
    STG --> PROD[Production<br/>Live Environment]
    
    subgraph "CI/CD Pipeline"
        GHA[GitHub Actions]
        DOCKER[Docker Registry]
        DEPLOY[Deploy Scripts]
    end
    
    DEV --> GHA
    GHA --> DOCKER
    DOCKER --> STG
    STG --> PROD
```

### Infraestrutura Recomendada

#### Opção 1: VPS Básica (Custo: $20-50/mês)
- **Provider**: DigitalOcean, Linode, Vultr
- **Specs**: 4 vCPUs, 8GB RAM, 160GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Ideal para**: MVP e primeiros usuários

#### Opção 2: Cloud Escalável (Custo: $50-200/mês)
- **Provider**: AWS, GCP, Azure
- **Services**: ECS/Fargate, RDS, ElastiCache
- **Auto-scaling**: Sim
- **Ideal para**: Crescimento e produção

#### Opção 3: Kubernetes (Custo: $100-500/mês)
- **Provider**: EKS, GKE, AKS
- **Orchestration**: Full Kubernetes
- **High Availability**: Sim
- **Ideal para**: Enterprise e alta escala

## 🏗️ Configuração de Infraestrutura

### Docker Compose para Produção

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Reverse Proxy / Load Balancer
  nginx:
    image: nginx:1.24-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/var/www/static:ro
    depends_on:
      - frontend
      - backend
    networks:
      - scania-prod
    restart: unless-stopped

  # Frontend Production
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
      target: production
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.scania.com
      - NEXT_PUBLIC_WS_URL=wss://api.scania.com
    volumes:
      - static_files:/app/public
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # Backend API Production
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      target: production
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
    volumes:
      - uploads_data:/app/uploads
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Workers
  celery-worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
      target: production
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    volumes:
      - scanner_data:/app/scanner_data
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  # Scanner Engine
  scanner:
    build:
      context: ./scanner
      dockerfile: ../docker/Dockerfile.scanner
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OWASP_ZAP_HOST=owasp-zap
      - OWASP_ZAP_API_KEY=${OWASP_ZAP_API_KEY}
    volumes:
      - scanner_data:/app/data
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 3G
        reservations:
          memory: 1G

  # OWASP ZAP (Containerized)
  owasp-zap:
    image: owasp/zap2docker-stable:2.12.0
    command: zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=${OWASP_ZAP_API_KEY}
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  # PostgreSQL Primary
  postgres:
    image: postgres:15.3
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 5

  # PostgreSQL Read Replica
  postgres-replica:
    image: postgres:15.3
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_MASTER_SERVICE=postgres
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
    networks:
      - scania-prod
    restart: unless-stopped
    depends_on:
      - postgres

  # Redis Cluster
  redis-master:
    image: redis:7.0-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_master_data:/data
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  redis-replica:
    image: redis:7.0-alpine
    command: redis-server --appendonly yes --replicaof redis-master 6379
    volumes:
      - redis_replica_data:/data
    networks:
      - scania-prod
    restart: unless-stopped
    depends_on:
      - redis-master

  # MinIO Object Storage
  minio:
    image: minio/minio:RELEASE.2023-06-19T19-52-50Z
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:v2.45.0
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - scania-prod
    restart: unless-stopped

  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:10.0.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - scania-prod
    restart: unless-stopped
    depends_on:
      - prometheus

  # Log Aggregation - Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - scania-prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  # Log Visualization - Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - scania-prod
    restart: unless-stopped
    depends_on:
      - elasticsearch

volumes:
  postgres_data:
  postgres_replica_data:
  redis_master_data:
  redis_replica_data:
  minio_data:
  scanner_data:
  uploads_data:
  static_files:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  scania-prod:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Configuração do NGINX

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: https:; connect-src 'self' wss: https:;" always;

    # Upstream servers
    upstream frontend_servers {
        least_conn;
        server frontend:3000 max_fails=3 fail_timeout=30s;
    }

    upstream backend_servers {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
    }

    # Main server block - HTTPS
    server {
        listen 443 ssl http2;
        server_name scania.com www.scania.com;

        ssl_certificate /etc/nginx/ssl/scania.crt;
        ssl_certificate_key /etc/nginx/ssl/scania.key;

        # Frontend - Static files and SSR
        location / {
            proxy_pass http://frontend_servers;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 86400;
        }

        # API Backend
        location /api/ {
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://backend_servers;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300;
            proxy_connect_timeout 10;
            proxy_send_timeout 300;
        }

        # WebSocket connections
        location /api/v1/chat/ws/ {
            proxy_pass http://backend_servers;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/auth/ {
            limit_req zone=login burst=3 nodelay;
            
            proxy_pass http://backend_servers;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://frontend_servers;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Static-Cache "HIT";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name scania.com www.scania.com;
        return 301 https://$server_name$request_uri;
    }

    # API-only server (for mobile apps, etc.)
    server {
        listen 443 ssl http2;
        server_name api.scania.com;

        ssl_certificate /etc/nginx/ssl/scania.crt;
        ssl_certificate_key /etc/nginx/ssl/scania.key;

        location / {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend_servers;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy ScanIA

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: scania

jobs:
  # Test Job
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: scania_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Cache Python dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Cache Node dependencies
        uses: actions/cache@v3
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

      - name: Install Python dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Install Node dependencies
        run: |
          cd frontend
          npm ci

      - name: Run backend tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/scania_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Run frontend tests
        run: |
          cd frontend
          npm run test -- --coverage --watchAll=false

      - name: Run linting
        run: |
          cd backend && flake8 app/
          cd frontend && npm run lint

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml,./frontend/coverage/lcov.info

  # Security Scan
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r backend/app/ -f json -o bandit-report.json || true

  # Build and Push Docker Images
  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    strategy:
      matrix:
        service: [frontend, backend, scanner]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          file: ./docker/Dockerfile.${{ matrix.service }}
          target: production
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Deploy to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to staging
        uses: appleboy/ssh-action@v0.1.10
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/scania
            git pull origin develop
            docker-compose -f docker-compose.staging.yml pull
            docker-compose -f docker-compose.staging.yml up -d
            docker system prune -f

      - name: Run health checks
        run: |
          sleep 30
          curl -f https://staging.scania.com/health || exit 1

  # Deploy to Production
  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Create GitHub deployment
        uses: chrnorm/deployment-action@v2
        id: deployment
        with:
          token: ${{ github.token }}
          environment: production

      - name: Deploy to production
        uses: appleboy/ssh-action@v0.1.10
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_SSH_KEY }}
          script: |
            cd /opt/scania
            git pull origin main
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d --remove-orphans
            docker system prune -f

      - name: Run health checks
        run: |
          sleep 60
          curl -f https://scania.com/health || exit 1
          curl -f https://api.scania.com/health || exit 1

      - name: Update deployment status (success)
        if: success()
        uses: chrnorm/deployment-status@v2
        with:
          token: ${{ github.token }}
          deployment-id: ${{ steps.deployment.outputs.deployment_id }}
          state: success

      - name: Update deployment status (failure)
        if: failure()
        uses: chrnorm/deployment-status@v2
        with:
          token: ${{ github.token }}
          deployment-id: ${{ steps.deployment.outputs.deployment_id }}
          state: failure

      - name: Notify team
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          text: 'ScanIA deployment to production: ${{ job.status }}'
```

## 📦 Scripts de Deploy

### Script de Deploy Principal

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
BRANCH=${2:-main}
BACKUP_BEFORE_DEPLOY=${3:-true}

echo -e "${GREEN}🚀 Starting ScanIA deployment to ${ENVIRONMENT}${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    
    print_status "Prerequisites check passed ✅"
}

# Function to backup database
backup_database() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        print_status "Creating database backup..."
        
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="backups/scania_backup_${TIMESTAMP}.sql"
        
        # Create backup directory if it doesn't exist
        mkdir -p backups
        
        # Create database backup
        docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > ${BACKUP_FILE}
        
        if [ $? -eq 0 ]; then
            print_status "Database backup created: ${BACKUP_FILE} ✅"
        else
            print_error "Database backup failed"
            exit 1
        fi
        
        # Keep only last 10 backups
        ls -t backups/scania_backup_*.sql | tail -n +11 | xargs -r rm
    fi
}

# Function to update code
update_code() {
    print_status "Updating code from repository..."
    
    # Fetch latest changes
    git fetch origin
    
    # Checkout specified branch
    git checkout ${BRANCH}
    
    # Pull latest changes
    git pull origin ${BRANCH}
    
    print_status "Code updated to latest ${BRANCH} ✅"
}

# Function to build and deploy
deploy_services() {
    print_status "Building and deploying services..."
    
    # Set environment variables
    export COMPOSE_FILE=docker-compose.${ENVIRONMENT}.yml
    
    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker-compose pull
    
    # Build custom images
    print_status "Building custom images..."
    docker-compose build --no-cache
    
    # Stop services gracefully
    print_status "Stopping current services..."
    docker-compose down --timeout 30
    
    # Start services
    print_status "Starting updated services..."
    docker-compose up -d --remove-orphans
    
    print_status "Services deployed ✅"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations
    docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T backend alembic upgrade head
    
    if [ $? -eq 0 ]; then
        print_status "Database migrations completed ✅"
    else
        print_error "Database migrations failed"
        print_warning "Rolling back deployment..."
        rollback_deployment
        exit 1
    fi
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_status "Backend health check passed ✅"
            break
        else
            if [ $i -eq 10 ]; then
                print_error "Backend health check failed after 10 attempts"
                rollback_deployment
                exit 1
            fi
            print_status "Waiting for backend to be ready... (attempt $i/10)"
            sleep 10
        fi
    done
    
    # Check frontend health
    for i in {1..10}; do
        if curl -f http://localhost:3000 > /dev/null 2>&1; then
            print_status "Frontend health check passed ✅"
            break
        else
            if [ $i -eq 10 ]; then
                print_error "Frontend health check failed after 10 attempts"
                rollback_deployment
                exit 1
            fi
            print_status "Waiting for frontend to be ready... (attempt $i/10)"
            sleep 10
        fi
    done
    
    # Check database connection
    if docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres pg_isready -U ${POSTGRES_USER} > /dev/null 2>&1; then
        print_status "Database health check passed ✅"
    else
        print_error "Database health check failed"
        rollback_deployment
        exit 1
    fi
    
    print_status "All health checks passed ✅"
}

# Function to rollback deployment
rollback_deployment() {
    print_warning "Rolling back deployment..."
    
    # This would ideally restore from backup and previous version
    # For now, just restart services
    docker-compose -f docker-compose.${ENVIRONMENT}.yml restart
    
    print_warning "Rollback completed. Please check logs and fix issues."
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused volumes (be careful with this in production)
    if [ "$ENVIRONMENT" != "production" ]; then
        docker volume prune -f
    fi
    
    print_status "Cleanup completed ✅"
}

# Function to send notifications
send_notifications() {
    local status=$1
    local message="ScanIA deployment to ${ENVIRONMENT}: ${status}"
    
    # Slack notification (if webhook is configured)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${message}\"}" \
            $SLACK_WEBHOOK_URL
    fi
    
    # Discord notification (if webhook is configured)
    if [ ! -z "$DISCORD_WEBHOOK_URL" ]; then
        curl -H "Content-Type: application/json" \
            -d "{\"content\": \"${message}\"}" \
            $DISCORD_WEBHOOK_URL
    fi
    
    print_status "Notifications sent ✅"
}

# Main deployment process
main() {
    print_status "=== ScanIA Deployment Script ==="
    print_status "Environment: ${ENVIRONMENT}"
    print_status "Branch: ${BRANCH}"
    print_status "Backup: ${BACKUP_BEFORE_DEPLOY}"
    print_status "================================"
    
    # Load environment variables
    if [ -f ".env.${ENVIRONMENT}" ]; then
        source .env.${ENVIRONMENT}
    else
        print_error "Environment file .env.${ENVIRONMENT} not found"
        exit 1
    fi
    
    # Run deployment steps
    check_prerequisites
    update_code
    backup_database
    deploy_services
    run_migrations
    run_health_checks
    cleanup
    
    print_status "🎉 Deployment completed successfully!"
    send_notifications "SUCCESS"
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO. Exit code: $?"; send_notifications "FAILED"; exit 1' ERR

# Run main function
main "$@"
```

### Script de Rollback

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

ENVIRONMENT=${1:-production}
BACKUP_FILE=${2}

echo "🔄 Starting rollback for ${ENVIRONMENT} environment"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Please specify backup file"
    echo "Usage: ./rollback.sh [environment] [backup_file]"
    echo "Available backups:"
    ls -la backups/scania_backup_*.sql 2>/dev/null || echo "No backups found"
    exit 1
fi

# Stop current services
echo "🛑 Stopping current services..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml down

# Restore database
echo "🗄️ Restoring database from backup..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d postgres
sleep 10

# Drop and recreate database
docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres psql -U ${POSTGRES_USER} -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"
docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};"

# Restore from backup
docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ${BACKUP_FILE}

# Restart all services
echo "🚀 Restarting all services..."
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

echo "✅ Rollback completed successfully!"
```

## 🔍 Monitoramento de Deploy

### Health Check Endpoints

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
import redis
import subprocess
import psutil
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Could measure actual response time
        }
    except Exception as e:
        checks["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"
    
    # Redis check
    try:
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        r.ping()
        checks["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"
    
    # System resources
    checks["checks"]["system"] = {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
    
    # Scanner engines
    try:
        # Check if OWASP ZAP is accessible
        import requests
        response = requests.get(f"http://{settings.OWASP_ZAP_HOST}:8080", timeout=5)
        checks["checks"]["owasp_zap"] = {"status": "healthy"}
    except:
        checks["checks"]["owasp_zap"] = {"status": "unhealthy"}
    
    return checks

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
```

### Métricas Prometheus

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Application metrics
ACTIVE_SCANS = Gauge('active_scans_total', 'Number of active scans')
VULNERABILITIES_FOUND = Counter('vulnerabilities_found_total', 'Total vulnerabilities found')
USERS_ACTIVE = Gauge('users_active_total', 'Number of active users')

class PrometheusMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Get request info
            method = scope["method"]
            path = scope["path"]
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
            
        else:
            await self.app(scope, receive, send)
```

---

**Esta configuração de deploy garante uma implantação robusta, escalável e monitorada do ScanIA em produção.**