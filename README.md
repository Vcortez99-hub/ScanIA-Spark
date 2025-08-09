# ScanIA - Sistema Inteligente de Análise de Cybersegurança

![ScanIA Banner](https://via.placeholder.com/800x200/1e293b/3b82f6?text=ScanIA+-+Sistema+Inteligente+de+Análise+de+Cybersegurança)

## 🚀 Início Rápido

### Pré-requisitos
- **Docker & Docker Compose** (para banco de dados e cache)
- **Node.js 18+** (para o frontend)
- **Python 3.9+** (para o backend)

### ⚡ Execução Automática

**Windows (PowerShell):**
```powershell
# Execute o script automatizado
.\run-dev.ps1
```

**Linux/Mac:**
```bash
# Execute o script automatizado
./run-dev.sh
```

### 📱 Execução Manual

1. **Iniciar serviços de infraestrutura:**
```bash
docker-compose up -d postgres redis minio
```

2. **Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 🌐 URLs de Acesso
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentação API:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

### 👤 Primeiro Acesso
1. Acesse http://localhost:3000
2. Clique em "Registrar" para criar sua conta
3. Faça login e explore o dashboard
4. Inicie seu primeiro scan de segurança!

## Visão Geral

O **ScanIA** é uma plataforma completa de cybersegurança que combina uma interface de chat inteligente com capacidades avançadas de análise de vulnerabilidades. Projetado para ser uma solução robusta e econômica para profissionais de segurança.

## 🎯 Objetivos Principais

- **Interface de Chat Intuitiva**: Similar ao ChatGPT/Claude com tema dark mode
- **Scanner de Vulnerabilidades**: Análise automatizada de URLs e domínios
- **Relatórios Inteligentes**: Geração automática de PDFs detalhados
- **Dashboards Dinâmicos**: Visualizações interativas em tempo real
- **Expansão Modular**: Arquitetura preparada para múltiplas funcionalidades de cybersegurança

## 🏗️ Arquitetura

### Stack Tecnológica
- **Frontend**: React + Next.js + Tailwind CSS
- **Backend**: FastAPI + Python 3.11+
- **Banco de Dados**: PostgreSQL + Redis
- **Scanners**: OWASP ZAP, Nuclei, Nmap, Custom Tools
- **Relatórios**: ReportLab + Matplotlib/Plotly
- **Deploy**: Docker + VPS/Cloud

### Princípios Arquiteturais
- **Microservices**: Componentes independentes e escaláveis
- **API-First**: Todas as funcionalidades expostas via API REST
- **Segurança em Camadas**: Múltiplos níveis de proteção
- **Observabilidade**: Logs, métricas e traces completos

## 📁 Estrutura da Documentação

### 🎯 Planejamento e Arquitetura
- [`ARQUITETURA.md`](./ARQUITETURA.md) - Arquitetura detalhada do sistema
- [`ROADMAP.md`](./ROADMAP.md) - Roadmap completo de desenvolvimento
- [`DIAGRAMAS.md`](./DIAGRAMAS.md) - Diagramas de arquitetura e fluxos

### 🏃‍♂️ Sprints de Desenvolvimento
- [`SPRINT-01.md`](./SPRINT-01.md) - MVP: Interface base e autenticação
- [`SPRINT-02.md`](./SPRINT-02.md) - Core: Scanner básico e relatórios
- [`SPRINT-03.md`](./SPRINT-03.md) - Dashboard e visualizações
- [`SPRINT-04.md`](./SPRINT-04.md) - Chat inteligente e IA
- [`SPRINT-05.md`](./SPRINT-05.md) - Análise avançada de vulnerabilidades
- [`SPRINT-06.md`](./SPRINT-06.md) - Compliance e frameworks
- [`SPRINT-07.md`](./SPRINT-07.md) - API externa e integrações
- [`SPRINT-08.md`](./SPRINT-08.md) - Monitoramento contínuo
- [`SPRINT-09.md`](./SPRINT-09.md) - Mobile e notificações
- [`SPRINT-10.md`](./SPRINT-10.md) - Enterprise e multi-tenant

### 🔧 Documentação Técnica
- [`TECNOLOGIAS.md`](./TECNOLOGIAS.md) - Detalhes das tecnologias escolhidas
- [`CONFIGURACAO.md`](./CONFIGURACAO.md) - Configurações de ambiente
- [`API-DOCS.md`](./API-DOCS.md) - Documentação completa da API
- [`SEGURANCA.md`](./SEGURANCA.md) - Políticas e implementação de segurança
- [`TESTES.md`](./TESTES.md) - Estratégias de teste e QA

### 🚀 Deploy e Operações
- [`DEPLOY.md`](./DEPLOY.md) - Guia de deploy e CI/CD
- [`MONITORAMENTO.md`](./MONITORAMENTO.md) - Observabilidade e alertas
- [`MANUTENCAO.md`](./MANUTENCAO.md) - Procedimentos de manutenção
- [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) - Solução de problemas

### 📊 Funcionalidades Futuras
- [`ROADMAP-FUTURO.md`](./ROADMAP-FUTURO.md) - Expansões a longo prazo
- [`INTELIGENCIA-ARTIFICIAL.md`](./INTELIGENCIA-ARTIFICIAL.md) - Recursos de IA avançada
- [`MARKETPLACE.md`](./MARKETPLACE.md) - Marketplace de plugins

## 🎯 Cronograma Estimado

| Sprint | Duração | Foco Principal |
|--------|---------|----------------|
| Sprint 1 | 2 semanas | MVP Base |
| Sprint 2 | 3 semanas | Scanner Core |
| Sprint 3 | 2 semanas | Dashboards |
| Sprint 4 | 3 semanas | Chat IA |
| Sprint 5 | 4 semanas | Análise Avançada |
| Sprint 6-10 | 20 semanas | Funcionalidades Enterprise |

**Total estimado**: ~6 meses para versão completa

## 💰 Estimativa de Custos

### Desenvolvimento
- **Infraestrutura**: $15-30/mês
- **Ferramentas**: $0-50/mês
- **Total mensal**: $15-80/mês

### Escalabilidade
- **100 usuários**: $50-100/mês
- **1000 usuários**: $200-500/mês
- **10000 usuários**: $1000-3000/mês

## 🚀 Como Começar

1. **Leia a arquitetura**: [`ARQUITETURA.md`](./ARQUITETURA.md)
2. **Configure o ambiente**: [`CONFIGURACAO.md`](./CONFIGURACAO.md)
3. **Execute o Sprint 1**: [`SPRINT-01.md`](./SPRINT-01.md)
4. **Siga o roadmap**: [`ROADMAP.md`](./ROADMAP.md)

## 📞 Suporte

- **Documentação**: Consulte os arquivos MD específicos
- **Issues**: Use o sistema de issues do projeto
- **Contribuições**: Siga o guia de contribuição

---

**ScanIA** - Transformando a cybersegurança através da inteligência artificial e automação.