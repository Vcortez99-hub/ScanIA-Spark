# Sprint 1: MVP Base

**Duração**: 2 semanas  
**Objetivo**: Criar fundação sólida do ScanIA com autenticação, interface básica e deploy funcional  
**Prioridade**: 🔥 Crítica  

## 🎯 Objetivos do Sprint

### Principais Entregáveis
- ✅ Estrutura completa do projeto (frontend + backend)
- ✅ Sistema de autenticação seguro (JWT + OAuth2)
- ✅ Interface web com dark mode
- ✅ Base de dados configurada
- ✅ Deploy automatizado em produção
- ✅ Documentação técnica inicial

### Critérios de Aceitação
- [ ] Usuário pode se registrar com email/senha
- [ ] Usuário pode fazer login e logout
- [ ] Interface carrega em dark mode por padrão
- [ ] Dashboard básico exibe informações do usuário
- [ ] Sistema roda em produção com SSL
- [ ] Testes unitários básicos funcionando
- [ ] CI/CD pipeline configurado

## 🏗️ Arquitetura do Sprint

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│   API Gateway   │────│   Backend       │
│   (Next.js)     │    │   (Nginx)       │    │   (FastAPI)     │
│                 │    │                 │    │                 │
│ • Auth Pages    │    │ • Rate Limit    │    │ • Auth API      │
│ • Dashboard     │    │ • SSL Term      │    │ • User CRUD     │
│ • Dark Theme    │    │ • Load Balance  │    │ • JWT Manager   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌───────────────┐
                                               │  PostgreSQL   │
                                               │               │
                                               │ • Users       │
                                               │ • Sessions    │
                                               │ • Audit Logs  │
                                               └───────────────┘
```

## 📋 Tasks Detalhadas

### Week 1: Setup e Backend

#### 🎯 Task 1.1: Setup do Projeto (Day 1-2)
**Responsável**: DevOps  
**Estimativa**: 16h  

**Atividades**:
1. **Estrutura de Diretórios**
   ```
   scania/
   ├── frontend/          # Next.js app
   ├── backend/           # FastAPI app
   ├── scanner/           # Scanner engine
   ├── docker/            # Docker configs
   ├── docs/              # Documentation
   ├── scripts/           # Utility scripts
   └── docker-compose.yml # Local development
   ```

2. **Configuração de Desenvolvimento**
   - Docker compose para ambiente local
   - Makefile com comandos úteis
   - .env templates
   - Git hooks (pre-commit, pre-push)

3. **CI/CD Pipeline**
   - GitHub Actions workflows
   - Automated testing
   - Docker build & push
   - Deploy scripts

**Deliverables**:
- [ ] Repositório estruturado
- [ ] Docker compose funcional
- [ ] CI/CD configurado

---

#### 🎯 Task 1.2: Backend Core (Day 2-4)
**Responsável**: Backend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **FastAPI Setup**
   ```python
   # app/main.py
   from fastapi import FastAPI, Depends, HTTPException
   from fastapi.middleware.cors import CORSMiddleware
   from fastapi.middleware.trustedhost import TrustedHostMiddleware
   
   app = FastAPI(
       title="ScanIA API",
       description="Sistema de Cybersegurança Inteligente",
       version="1.0.0"
   )
   
   # Security middlewares
   app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
   app.add_middleware(CORSMiddleware, allow_origins=["*"])
   ```

2. **Database Models**
   ```python
   # app/models/user.py
   from sqlalchemy import Column, String, Boolean, DateTime
   from sqlalchemy.dialects.postgresql import UUID
   from app.core.database import Base
   
   class User(Base):
       __tablename__ = "users"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
       email = Column(String(255), unique=True, nullable=False)
       password_hash = Column(String(255), nullable=False)
       full_name = Column(String(255), nullable=False)
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

3. **Authentication System**
   - JWT token generation
   - Password hashing (bcrypt)
   - OAuth2 flows
   - Session management

**Deliverables**:
- [ ] FastAPI app estruturada
- [ ] Database models criados
- [ ] Sistema de auth funcional
- [ ] API docs geradas automaticamente

---

#### 🎯 Task 1.3: Database Setup (Day 3-4)
**Responsável**: Backend Dev  
**Estimativa**: 16h  

**Atividades**:
1. **PostgreSQL Configuration**
   ```yaml
   # docker-compose.yml
   postgres:
     image: postgres:15
     environment:
       POSTGRES_DB: scania_db
       POSTGRES_USER: scania_user
       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
     volumes:
       - postgres_data:/var/lib/postgresql/data
       - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
   ```

2. **Migration System**
   - Alembic configuration
   - Initial migrations
   - Seed data scripts

3. **Database Security**
   - Connection pooling
   - Query optimization
   - Backup strategy

**Deliverables**:
- [ ] PostgreSQL containerizado
- [ ] Migrations funcionando
- [ ] Dados de teste criados

### Week 2: Frontend e Integração

#### 🎯 Task 2.1: Frontend Base (Day 5-7)
**Responsável**: Frontend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **Next.js Setup**
   ```typescript
   // next.config.js
   /** @type {import('next').NextConfig} */
   const nextConfig = {
     experimental: {
       appDir: true,
     },
     env: {
       API_URL: process.env.API_URL,
     },
   }
   
   module.exports = nextConfig
   ```

2. **Tailwind + Dark Mode**
   ```typescript
   // tailwind.config.js
   module.exports = {
     darkMode: 'class',
     content: ['./src/**/*.{js,ts,jsx,tsx}'],
     theme: {
       extend: {
         colors: {
           primary: {
             50: '#eff6ff',
             900: '#1e3a8a',
           },
           dark: {
             bg: '#0f172a',
             card: '#1e293b',
             text: '#f1f5f9',
           }
         }
       }
     }
   }
   ```

3. **Component Library**
   ```typescript
   // components/ui/Button.tsx
   interface ButtonProps {
     variant: 'primary' | 'secondary' | 'danger';
     size: 'sm' | 'md' | 'lg';
     children: React.ReactNode;
     onClick?: () => void;
   }
   
   export const Button: React.FC<ButtonProps> = ({
     variant, size, children, onClick
   }) => {
     // Implementation with Tailwind classes
   }
   ```

**Deliverables**:
- [ ] Next.js app configurada
- [ ] Dark mode implementado
- [ ] Componentes base criados

---

#### 🎯 Task 2.2: Authentication UI (Day 7-9)
**Responsável**: Frontend Dev  
**Estimativa**: 20h  

**Atividades**:
1. **Login/Register Pages**
   ```typescript
   // pages/auth/login.tsx
   export default function LoginPage() {
     const [email, setEmail] = useState('');
     const [password, setPassword] = useState('');
     const { login, isLoading } = useAuth();
   
     const handleLogin = async (e: FormEvent) => {
       e.preventDefault();
       await login(email, password);
     };
   
     return (
       <div className="min-h-screen bg-dark-bg flex items-center justify-center">
         <Card className="w-full max-w-md">
           <form onSubmit={handleLogin}>
             {/* Form fields */}
           </form>
         </Card>
       </div>
     );
   }
   ```

2. **Authentication Context**
   ```typescript
   // contexts/AuthContext.tsx
   interface AuthContextType {
     user: User | null;
     login: (email: string, password: string) => Promise<void>;
     logout: () => void;
     isLoading: boolean;
   }
   
   export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
     // Implementation
   };
   ```

3. **Protected Routes**
   ```typescript
   // components/ProtectedRoute.tsx
   export const ProtectedRoute: React.FC<{ children: ReactNode }> = ({ children }) => {
     const { user, isLoading } = useAuth();
     
     if (isLoading) return <LoadingSpinner />;
     if (!user) return <Navigate to="/auth/login" />;
     
     return <>{children}</>;
   };
   ```

**Deliverables**:
- [ ] Páginas de auth criadas
- [ ] Context de autenticação funcional
- [ ] Rotas protegidas implementadas

---

#### 🎯 Task 2.3: Dashboard Básico (Day 8-10)
**Responsável**: Frontend Dev  
**Estimativa**: 16h  

**Atividades**:
1. **Layout Principal**
   ```typescript
   // components/Layout/DashboardLayout.tsx
   export const DashboardLayout: React.FC<{ children: ReactNode }> = ({ children }) => {
     return (
       <div className="min-h-screen bg-dark-bg">
         <Sidebar />
         <Header />
         <main className="ml-64 p-8">
           {children}
         </main>
       </div>
     );
   };
   ```

2. **Dashboard Home**
   ```typescript
   // pages/dashboard/index.tsx
   export default function DashboardPage() {
     const { user } = useAuth();
     
     return (
       <DashboardLayout>
         <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <StatsCard title="Scans Realizados" value="0" />
           <StatsCard title="Vulnerabilidades" value="0" />
           <StatsCard title="Relatórios" value="0" />
         </div>
         
         <div className="mt-8">
           <RecentActivity />
         </div>
       </DashboardLayout>
     );
   }
   ```

3. **Sidebar Navigation**
   ```typescript
   // components/Sidebar.tsx
   const navigationItems = [
     { label: 'Dashboard', href: '/dashboard', icon: HomeIcon },
     { label: 'Scanner', href: '/scanner', icon: SearchIcon },
     { label: 'Relatórios', href: '/reports', icon: DocumentIcon },
     { label: 'Chat', href: '/chat', icon: ChatIcon },
   ];
   ```

**Deliverables**:
- [ ] Layout responsivo criado
- [ ] Dashboard com métricas básicas
- [ ] Navegação funcional

#### 🎯 Task 2.4: Deploy e Testes (Day 9-10)
**Responsável**: DevOps + QA  
**Estimativa**: 16h  

**Atividades**:
1. **Docker Configuration**
   ```dockerfile
   # Dockerfile.frontend
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build
   
   FROM node:18-alpine AS runner
   WORKDIR /app
   COPY --from=builder /app/.next ./.next
   COPY --from=builder /app/node_modules ./node_modules
   COPY --from=builder /app/package.json ./package.json
   
   EXPOSE 3000
   CMD ["npm", "start"]
   ```

2. **Production Deploy**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     nginx:
       image: nginx:alpine
       ports: ["80:80", "443:443"]
       volumes:
         - ./nginx/nginx.conf:/etc/nginx/nginx.conf
         - ./nginx/ssl:/etc/nginx/ssl
     
     frontend:
       build: 
         context: ./frontend
         dockerfile: Dockerfile.prod
       environment:
         - NODE_ENV=production
         - API_URL=https://api.scania.com
     
     backend:
       build: 
         context: ./backend
         dockerfile: Dockerfile.prod
       environment:
         - DATABASE_URL=${DATABASE_URL}
         - JWT_SECRET=${JWT_SECRET}
   ```

3. **Health Checks**
   ```python
   # app/api/health.py
   @router.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "timestamp": datetime.utcnow(),
           "version": "1.0.0",
           "database": await check_database_connection(),
           "redis": await check_redis_connection()
       }
   ```

**Deliverables**:
- [ ] Containers de produção
- [ ] Deploy automatizado
- [ ] Health checks implementados
- [ ] SSL configurado

## 🧪 Testes

### Unit Tests
```python
# tests/test_auth.py
def test_user_registration():
    response = client.post("/auth/register", json={
        "email": "test@scania.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_user_login():
    # Test login functionality
    pass

def test_jwt_token_validation():
    # Test JWT validation
    pass
```

### Integration Tests
```typescript
// tests/auth.test.ts
describe('Authentication Flow', () => {
  test('User can register and login', async () => {
    // Test complete auth flow
  });
  
  test('Protected routes redirect unauthenticated users', async () => {
    // Test route protection
  });
});
```

### E2E Tests
```typescript
// e2e/auth.spec.ts
test('complete authentication flow', async ({ page }) => {
  await page.goto('/auth/register');
  await page.fill('[data-testid=email]', 'test@scania.com');
  await page.fill('[data-testid=password]', 'SecurePass123!');
  await page.click('[data-testid=register-button]');
  
  await expect(page).toHaveURL('/dashboard');
});
```

## 📊 Métricas de Sucesso

### Técnicas
- [ ] **Build Time**: < 5 minutos
- [ ] **Test Coverage**: > 80%
- [ ] **Bundle Size**: < 1MB (gzipped)
- [ ] **Lighthouse Score**: > 90

### Funcionais
- [ ] **Registration**: Funciona sem erros
- [ ] **Login/Logout**: Funciona sem erros  
- [ ] **Session Management**: JWT válido por 24h
- [ ] **Dark Mode**: Aplicado consistentemente

### Performance
- [ ] **Page Load**: < 2 segundos
- [ ] **API Response**: < 200ms
- [ ] **Database Queries**: < 50ms
- [ ] **Memory Usage**: < 512MB

## 🚨 Riscos e Mitigações

### Alto Risco
1. **Complexidade do Setup**
   - *Risco*: Configuração inicial complexa
   - *Mitigação*: Docker compose + scripts automatizados
   - *Plano B*: Setup manual documentado

2. **Problemas de Deploy**
   - *Risco*: Deploy não funcionar em produção  
   - *Mitigação*: Testes em staging environment
   - *Plano B*: Deploy manual inicial

### Médio Risco
1. **Performance do Frontend**
   - *Risco*: App lento ou pesado
   - *Mitigação*: Code splitting + lazy loading
   - *Plano B*: Otimização posterior

2. **Database Migration Issues**
   - *Risco*: Migrations falharem
   - *Mitigação*: Backup + rollback strategy
   - *Plano B*: Recriação manual

## 📚 Recursos Necessários

### Desenvolvimento
- **Frontend Developer**: 2 semanas full-time
- **Backend Developer**: 2 semanas full-time  
- **DevOps Engineer**: 0.5 semana
- **QA Tester**: 0.5 semana

### Infraestrutura
- **Development**: Local Docker
- **Staging**: VPS $10/mês
- **Production**: VPS $20/mês + CDN
- **Domain**: $15/ano
- **SSL Certificate**: Let's Encrypt (gratuito)

### Ferramentas
- **GitHub**: Gratuito (público)
- **Docker Hub**: Gratuito (limitado)
- **Monitoring**: Grafana Cloud (tier gratuito)

## ✅ Definition of Done

### Código
- [ ] Code review aprovado
- [ ] Testes unitários passando
- [ ] Testes E2E passando
- [ ] Linting sem erros
- [ ] Documentação atualizada

### Deploy
- [ ] Deploy em staging funcionando
- [ ] Deploy em production funcionando
- [ ] Health checks respondendo
- [ ] SSL/HTTPS ativo
- [ ] Monitoramento básico ativo

### Qualidade
- [ ] Performance dentro dos targets
- [ ] Segurança básica implementada
- [ ] UX responsivo em mobile/desktop
- [ ] Acessibilidade básica (WCAG 2.1 AA)

---

**Sprint 1 estabelece a fundação sólida para todo o desenvolvimento futuro do ScanIA. Foco na qualidade e arquitetura correta é fundamental.**