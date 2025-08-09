# Diagramas de Arquitetura - ScanIA

## 🏗️ Visão Geral da Arquitetura

### Diagrama de Alto Nível

```mermaid
graph TB
    subgraph "Cliente/Frontend"
        WEB[Web App<br/>React/Next.js]
        MOBILE[Mobile App<br/>React Native]
        CLI[CLI Tool<br/>Python]
    end
    
    subgraph "API Gateway"
        NGINX[NGINX<br/>Load Balancer]
        RATE[Rate Limiting]
        AUTH[Authentication]
    end
    
    subgraph "Aplicação Backend"
        API[FastAPI<br/>Core API]
        SCANNER[Scanner Engine<br/>Python]
        AI[AI Engine<br/>NLP/ML]
        REPORT[Report Generator<br/>PDF/HTML]
    end
    
    subgraph "Dados e Cache"
        POSTGRES[(PostgreSQL<br/>Primary DB)]
        REDIS[(Redis<br/>Cache/Queue)]
        MINIO[(MinIO<br/>File Storage)]
    end
    
    subgraph "Serviços Externos"
        ZAP[OWASP ZAP<br/>Web Scanner]
        NMAP[Nmap<br/>Port Scanner]
        CVE[CVE Database<br/>NIST/MITRE]
        THREAT[Threat Intel<br/>APIs]
    end
    
    subgraph "Monitoramento"
        PROM[Prometheus<br/>Metrics]
        GRAF[Grafana<br/>Dashboards]
        ELK[ELK Stack<br/>Logs]
    end
    
    WEB --> NGINX
    MOBILE --> NGINX
    CLI --> NGINX
    
    NGINX --> RATE
    RATE --> AUTH
    AUTH --> API
    
    API --> SCANNER
    API --> AI
    API --> REPORT
    
    SCANNER --> ZAP
    SCANNER --> NMAP
    AI --> CVE
    AI --> THREAT
    
    API --> POSTGRES
    API --> REDIS
    REPORT --> MINIO
    
    API --> PROM
    PROM --> GRAF
    API --> ELK
    
    style WEB fill:#3b82f6
    style API fill:#10b981
    style POSTGRES fill:#8b5cf6
    style REDIS fill:#ef4444
```

## 🔄 Fluxos de Processo

### 1. Fluxo de Autenticação

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Frontend as Web App
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Cache as Redis
    
    User->>Frontend: Login (email, password)
    Frontend->>Gateway: POST /auth/login
    Gateway->>Auth: Validate credentials
    Auth->>DB: Query user
    DB-->>Auth: User data
    
    alt Valid credentials
        Auth->>Auth: Generate JWT
        Auth->>Cache: Store session
        Auth-->>Gateway: JWT token
        Gateway-->>Frontend: Auth success + token
        Frontend-->>User: Redirect to dashboard
    else Invalid credentials
        Auth-->>Gateway: 401 Unauthorized
        Gateway-->>Frontend: Auth failed
        Frontend-->>User: Error message
    end
```

### 2. Fluxo de Scanner de Vulnerabilidades

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Frontend as Web App
    participant API as Core API
    participant Queue as Celery Queue
    participant Scanner as Scanner Engine
    participant ZAP as OWASP ZAP
    participant DB as PostgreSQL
    participant WS as WebSocket
    
    User->>Frontend: Start scan (URL, options)
    Frontend->>API: POST /scanner/scan
    API->>DB: Create scan record
    API->>Queue: Queue scan job
    API-->>Frontend: Scan ID + status
    
    Queue->>Scanner: Execute scan job
    Scanner->>ZAP: Initialize ZAP session
    Scanner->>ZAP: Start spider
    
    loop Spider Progress
        ZAP-->>Scanner: Progress update
        Scanner->>WS: Send progress
        WS-->>Frontend: Real-time update
    end
    
    Scanner->>ZAP: Start active scan
    
    loop Active Scan Progress
        ZAP-->>Scanner: Progress + results
        Scanner->>WS: Send progress
        WS-->>Frontend: Real-time update
    end
    
    Scanner->>ZAP: Get final results
    ZAP-->>Scanner: Vulnerability list
    Scanner->>DB: Save vulnerabilities
    Scanner->>API: Update scan status
    API->>WS: Scan completed
    WS-->>Frontend: Final notification
    Frontend-->>User: Show results
```

### 3. Fluxo de Geração de Relatórios

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Frontend as Web App
    participant API as Core API
    participant ReportGen as Report Generator
    participant DB as PostgreSQL
    participant Storage as MinIO
    participant Email as Email Service
    
    User->>Frontend: Request report
    Frontend->>API: POST /reports/generate
    API->>DB: Create report record
    API->>ReportGen: Generate report (async)
    API-->>Frontend: Report ID + status
    
    ReportGen->>DB: Query scan data
    DB-->>ReportGen: Vulnerabilities + metadata
    ReportGen->>ReportGen: Generate PDF
    ReportGen->>Storage: Store PDF file
    ReportGen->>DB: Update report status
    
    opt Email notification
        ReportGen->>Email: Send notification
        Email-->>User: Report ready email
    end
    
    ReportGen-->>API: Report completed
    API-->>Frontend: Status update
    Frontend-->>User: Download available
    
    User->>Frontend: Download report
    Frontend->>API: GET /reports/{id}/download
    API->>Storage: Retrieve file
    Storage-->>API: PDF file
    API-->>Frontend: File stream
    Frontend-->>User: Download starts
```

## 🗃️ Modelo de Dados

### Diagrama Entidade-Relacionamento

```mermaid
erDiagram
    USERS ||--o{ SCANS : owns
    USERS ||--o{ CONVERSATIONS : participates
    SCANS ||--o{ VULNERABILITIES : contains
    SCANS ||--o{ REPORTS : generates
    CONVERSATIONS ||--o{ MESSAGES : contains
    USERS ||--o{ USER_SESSIONS : has
    
    USERS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string role
        boolean is_active
        jsonb preferences
        datetime created_at
        datetime updated_at
    }
    
    SCANS {
        uuid id PK
        uuid user_id FK
        string target_url
        jsonb scan_types
        string status
        jsonb options
        datetime started_at
        datetime completed_at
        integer duration_seconds
        string celery_job_id
        text error_message
        datetime created_at
    }
    
    VULNERABILITIES {
        uuid id PK
        uuid scan_id FK
        string vulnerability_id
        string cve_id
        string severity
        float cvss_score
        string title
        text description
        text solution
        string affected_url
        jsonb evidence
        string status
        text remediation_notes
        datetime created_at
    }
    
    REPORTS {
        uuid id PK
        uuid scan_id FK
        string report_type
        string format
        string title
        text description
        string file_path
        integer file_size
        string status
        datetime generated_at
        datetime expires_at
        jsonb metadata
        datetime created_at
    }
    
    CONVERSATIONS {
        uuid id PK
        uuid user_id FK
        string title
        jsonb context
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        jsonb metadata
        datetime created_at
    }
    
    USER_SESSIONS {
        uuid id PK
        uuid user_id FK
        string session_token
        string ip_address
        string user_agent
        datetime expires_at
        datetime created_at
    }
```

### Modelo Lógico Detalhado

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String passwordHash
        +String fullName
        +UserRole role
        +Boolean isActive
        +JSON preferences
        +DateTime createdAt
        +DateTime updatedAt
        +List~Scan~ scans
        +List~Conversation~ conversations
        +authenticate(password: String): Boolean
        +generateJWT(): String
        +hasPermission(action: String): Boolean
    }
    
    class Scan {
        +UUID id
        +UUID userId
        +String targetUrl
        +List~String~ scanTypes
        +ScanStatus status
        +JSON options
        +DateTime startedAt
        +DateTime completedAt
        +Integer durationSeconds
        +String celeryJobId
        +String errorMessage
        +List~Vulnerability~ vulnerabilities
        +List~Report~ reports
        +calculateRiskScore(): Float
        +getVulnerabilitySummary(): JSON
        +canUserAccess(userId: UUID): Boolean
    }
    
    class Vulnerability {
        +UUID id
        +UUID scanId
        +String vulnerabilityId
        +String cveId
        +Severity severity
        +Float cvssScore
        +String title
        +String description
        +String solution
        +String affectedUrl
        +JSON evidence
        +VulnStatus status
        +String remediationNotes
        +getSeverityWeight(): Float
        +isCritical(): Boolean
        +markAsFixed(): Void
    }
    
    class Report {
        +UUID id
        +UUID scanId
        +ReportType reportType
        +String format
        +String title
        +String description
        +String filePath
        +Integer fileSize
        +ReportStatus status
        +DateTime generatedAt
        +DateTime expiresAt
        +JSON metadata
        +generatePDF(): String
        +isExpired(): Boolean
        +getDownloadUrl(): String
    }
    
    class Conversation {
        +UUID id
        +UUID userId
        +String title
        +JSON context
        +Boolean isActive
        +List~Message~ messages
        +addMessage(role: String, content: String): Message
        +getLastMessages(limit: Integer): List~Message~
        +summarize(): String
    }
    
    class Message {
        +UUID id
        +UUID conversationId
        +MessageRole role
        +String content
        +JSON metadata
        +DateTime createdAt
        +isFromUser(): Boolean
        +isFromAssistant(): Boolean
        +extractIntent(): String
    }
    
    User ||--o{ Scan : owns
    User ||--o{ Conversation : participates
    Scan ||--o{ Vulnerability : contains
    Scan ||--o{ Report : generates
    Conversation ||--o{ Message : contains
```

## 🔧 Componentes Técnicos

### Arquitetura de Microserviços

```mermaid
graph TB
    subgraph "API Gateway Layer"
        GATEWAY[API Gateway<br/>NGINX + Kong]
        AUTH_MW[Auth Middleware]
        RATE_MW[Rate Limiting]
        CORS_MW[CORS Handler]
    end
    
    subgraph "Core Services"
        USER_SVC[User Service<br/>FastAPI]
        SCAN_SVC[Scanner Service<br/>FastAPI]
        REPORT_SVC[Report Service<br/>FastAPI]
        CHAT_SVC[Chat Service<br/>FastAPI]
    end
    
    subgraph "Processing Services"
        SCANNER_ENGINE[Scanner Engine<br/>Python + Celery]
        AI_ENGINE[AI Engine<br/>Python + ML]
        REPORT_ENGINE[Report Engine<br/>Python + ReportLab]
    end
    
    subgraph "Data Layer"
        USER_DB[(User Database<br/>PostgreSQL)]
        SCAN_DB[(Scan Database<br/>PostgreSQL)]
        CACHE[(Cache Layer<br/>Redis)]
        FILES[(File Storage<br/>MinIO)]
    end
    
    subgraph "External Integrations"
        OWASP[OWASP ZAP]
        NMAP_TOOL[Nmap]
        CVE_API[CVE APIs]
        THREAT_API[Threat Intel APIs]
    end
    
    subgraph "Infrastructure"
        QUEUE[(Message Queue<br/>Redis + Celery)]
        MONITOR[Monitoring<br/>Prometheus + Grafana]
        LOGS[Logging<br/>ELK Stack)]
    end
    
    GATEWAY --> AUTH_MW
    AUTH_MW --> RATE_MW
    RATE_MW --> CORS_MW
    
    CORS_MW --> USER_SVC
    CORS_MW --> SCAN_SVC
    CORS_MW --> REPORT_SVC
    CORS_MW --> CHAT_SVC
    
    USER_SVC --> USER_DB
    USER_SVC --> CACHE
    
    SCAN_SVC --> SCAN_DB
    SCAN_SVC --> QUEUE
    SCAN_SVC --> CACHE
    
    REPORT_SVC --> SCAN_DB
    REPORT_SVC --> FILES
    REPORT_SVC --> QUEUE
    
    CHAT_SVC --> USER_DB
    CHAT_SVC --> AI_ENGINE
    CHAT_SVC --> CACHE
    
    QUEUE --> SCANNER_ENGINE
    QUEUE --> REPORT_ENGINE
    
    SCANNER_ENGINE --> OWASP
    SCANNER_ENGINE --> NMAP_TOOL
    SCANNER_ENGINE --> SCAN_DB
    
    AI_ENGINE --> CVE_API
    AI_ENGINE --> THREAT_API
    
    REPORT_ENGINE --> FILES
    REPORT_ENGINE --> SCAN_DB
    
    USER_SVC --> MONITOR
    SCAN_SVC --> MONITOR
    REPORT_SVC --> MONITOR
    CHAT_SVC --> MONITOR
    
    USER_SVC --> LOGS
    SCAN_SVC --> LOGS
    REPORT_SVC --> LOGS
    CHAT_SVC --> LOGS
```

### Arquitetura de Deploy

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[CloudFlare<br/>CDN + DDoS Protection]
    end
    
    subgraph "Web Tier"
        NGINX1[NGINX 1<br/>Primary]
        NGINX2[NGINX 2<br/>Backup]
    end
    
    subgraph "Application Tier"
        API1[API Server 1<br/>FastAPI + Uvicorn]
        API2[API Server 2<br/>FastAPI + Uvicorn]
        API3[API Server 3<br/>FastAPI + Uvicorn]
    end
    
    subgraph "Processing Tier"
        WORKER1[Celery Worker 1<br/>Scanner Tasks]
        WORKER2[Celery Worker 2<br/>Report Tasks]
        WORKER3[Celery Worker 3<br/>AI Tasks]
    end
    
    subgraph "Data Tier"
        PG_PRIMARY[(PostgreSQL<br/>Primary)]
        PG_REPLICA[(PostgreSQL<br/>Read Replica)]
        REDIS_CLUSTER[(Redis Cluster<br/>3 Nodes)]
        MINIO_CLUSTER[(MinIO Cluster<br/>4 Nodes)]
    end
    
    subgraph "External Tools"
        ZAP_POOL[ZAP Instance Pool<br/>Docker Containers]
        NMAP_POOL[Nmap Instance Pool<br/>Docker Containers]
    end
    
    subgraph "Monitoring Stack"
        PROMETHEUS[Prometheus<br/>Metrics Collection]
        GRAFANA[Grafana<br/>Visualization]
        ELASTICSEARCH[Elasticsearch<br/>Log Storage]
        KIBANA[Kibana<br/>Log Analysis]
        ALERTMANAGER[AlertManager<br/>Notifications]
    end
    
    LB --> NGINX1
    LB --> NGINX2
    
    NGINX1 --> API1
    NGINX1 --> API2
    NGINX2 --> API3
    
    API1 --> PG_PRIMARY
    API2 --> PG_REPLICA
    API3 --> PG_PRIMARY
    
    API1 --> REDIS_CLUSTER
    API2 --> REDIS_CLUSTER
    API3 --> REDIS_CLUSTER
    
    REDIS_CLUSTER --> WORKER1
    REDIS_CLUSTER --> WORKER2
    REDIS_CLUSTER --> WORKER3
    
    WORKER1 --> ZAP_POOL
    WORKER1 --> NMAP_POOL
    WORKER2 --> MINIO_CLUSTER
    WORKER3 --> PG_PRIMARY
    
    API1 --> PROMETHEUS
    API2 --> PROMETHEUS
    API3 --> PROMETHEUS
    WORKER1 --> PROMETHEUS
    WORKER2 --> PROMETHEUS
    WORKER3 --> PROMETHEUS
    
    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTMANAGER
    
    API1 --> ELASTICSEARCH
    API2 --> ELASTICSEARCH
    API3 --> ELASTICSEARCH
    
    ELASTICSEARCH --> KIBANA
    
    style LB fill:#ff6b6b
    style PG_PRIMARY fill:#4ecdc4
    style REDIS_CLUSTER fill:#45b7d1
    style MINIO_CLUSTER fill:#f9ca24
```

## 🔒 Arquitetura de Segurança

### Camadas de Segurança

```mermaid
graph TB
    subgraph "Network Security"
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
        VPN[VPN Access]
        FIREWALL[Network Firewall]
    end
    
    subgraph "Application Security"
        JWT_AUTH[JWT Authentication]
        OAUTH[OAuth2/OIDC]
        RBAC[Role-Based Access Control]
        INPUT_VAL[Input Validation]
        XSS_PROT[XSS Protection]
        CSRF_PROT[CSRF Protection]
    end
    
    subgraph "Data Security"
        ENCRYPT_REST[Encryption at Rest]
        ENCRYPT_TRANSIT[Encryption in Transit]
        DB_ACCESS[Database Access Control]
        AUDIT_LOG[Audit Logging]
        BACKUP_ENCRYPT[Encrypted Backups]
    end
    
    subgraph "Infrastructure Security"
        CONTAINER_SEC[Container Security]
        SECRETS_MGT[Secrets Management]
        NETWORK_SEG[Network Segmentation]
        MONITORING[Security Monitoring]
    end
    
    subgraph "Compliance & Governance"
        GDPR[GDPR Compliance]
        LGPD[LGPD Compliance]
        SOC2[SOC2 Controls]
        PENTEST[Regular Pentesting]
    end
    
    WAF --> JWT_AUTH
    DDOS --> OAUTH
    VPN --> RBAC
    FIREWALL --> INPUT_VAL
    
    JWT_AUTH --> ENCRYPT_REST
    OAUTH --> ENCRYPT_TRANSIT
    RBAC --> DB_ACCESS
    INPUT_VAL --> AUDIT_LOG
    
    ENCRYPT_REST --> CONTAINER_SEC
    ENCRYPT_TRANSIT --> SECRETS_MGT
    DB_ACCESS --> NETWORK_SEG
    AUDIT_LOG --> MONITORING
    
    CONTAINER_SEC --> GDPR
    SECRETS_MGT --> LGPD
    NETWORK_SEG --> SOC2
    MONITORING --> PENTEST
```

### Fluxo de Autenticação e Autorização

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant RBAC as RBAC Engine
    participant Resource as Resource API
    participant Audit as Audit Log
    
    Client->>Gateway: Request + JWT Token
    Gateway->>Auth: Validate JWT
    
    alt JWT Valid
        Auth->>RBAC: Check permissions
        RBAC->>RBAC: Evaluate roles & policies
        
        alt Permission Granted
            RBAC-->>Auth: Access granted
            Auth-->>Gateway: Authentication OK
            Gateway->>Resource: Forward request
            Resource->>Audit: Log access
            Resource-->>Gateway: Response
            Gateway-->>Client: Success response
        else Permission Denied
            RBAC-->>Auth: Access denied
            Auth-->>Gateway: Authorization failed
            Gateway->>Audit: Log denied access
            Gateway-->>Client: 403 Forbidden
        end
    else JWT Invalid
        Auth-->>Gateway: Authentication failed
        Gateway->>Audit: Log failed auth
        Gateway-->>Client: 401 Unauthorized
    end
```

## 📊 Arquitetura de Monitoramento

### Stack de Observabilidade

```mermaid
graph TB
    subgraph "Data Sources"
        APP[Applications<br/>FastAPI, React]
        INFRA[Infrastructure<br/>Docker, K8s]
        DB[Databases<br/>PostgreSQL, Redis]
        EXT[External Services<br/>APIs, Tools]
    end
    
    subgraph "Collection Layer"
        PROM_AGENT[Prometheus Agents]
        LOG_AGENT[Log Agents<br/>Fluentd/Filebeat]
        TRACE_AGENT[Trace Agents<br/>Jaeger]
        CUSTOM[Custom Collectors]
    end
    
    subgraph "Processing Layer"
        PROMETHEUS[Prometheus<br/>Metrics Storage]
        ELASTICSEARCH[Elasticsearch<br/>Log Storage]
        JAEGER[Jaeger<br/>Trace Storage]
    end
    
    subgraph "Analysis Layer"
        GRAFANA[Grafana<br/>Dashboards]
        KIBANA[Kibana<br/>Log Analysis]
        JAEGER_UI[Jaeger UI<br/>Trace Analysis]
    end
    
    subgraph "Alerting Layer"
        ALERTMANAGER[AlertManager<br/>Alert Routing]
        SLACK[Slack<br/>Notifications]
        EMAIL[Email<br/>Notifications]
        PAGERDUTY[PagerDuty<br/>Incidents]
    end
    
    APP --> PROM_AGENT
    APP --> LOG_AGENT
    APP --> TRACE_AGENT
    
    INFRA --> PROM_AGENT
    INFRA --> LOG_AGENT
    
    DB --> PROM_AGENT
    DB --> LOG_AGENT
    
    EXT --> CUSTOM
    
    PROM_AGENT --> PROMETHEUS
    LOG_AGENT --> ELASTICSEARCH
    TRACE_AGENT --> JAEGER
    CUSTOM --> PROMETHEUS
    
    PROMETHEUS --> GRAFANA
    ELASTICSEARCH --> KIBANA
    JAEGER --> JAEGER_UI
    
    PROMETHEUS --> ALERTMANAGER
    ALERTMANAGER --> SLACK
    ALERTMANAGER --> EMAIL
    ALERTMANAGER --> PAGERDUTY
```

### Métricas e KPIs

```mermaid
graph LR
    subgraph "Business Metrics"
        USERS[Active Users]
        SCANS[Scans per Day]
        REPORTS[Reports Generated]
        VULNS[Vulnerabilities Found]
    end
    
    subgraph "Technical Metrics"
        RESPONSE[Response Time]
        THROUGHPUT[Requests/sec]
        ERRORS[Error Rate]
        UPTIME[Uptime %]
    end
    
    subgraph "Infrastructure Metrics"
        CPU[CPU Usage]
        MEMORY[Memory Usage]
        DISK[Disk Usage]
        NETWORK[Network I/O]
    end
    
    subgraph "Security Metrics"
        AUTH_FAILS[Auth Failures]
        RATE_LIMITS[Rate Limit Hits]
        SCAN_FAILS[Scan Failures]
        VULN_TRENDS[Vulnerability Trends]
    end
    
    USERS --> DASHBOARD[Executive Dashboard]
    SCANS --> DASHBOARD
    REPORTS --> DASHBOARD
    VULNS --> DASHBOARD
    
    RESPONSE --> TECH_DASH[Technical Dashboard]
    THROUGHPUT --> TECH_DASH
    ERRORS --> TECH_DASH
    UPTIME --> TECH_DASH
    
    CPU --> INFRA_DASH[Infrastructure Dashboard]
    MEMORY --> INFRA_DASH
    DISK --> INFRA_DASH
    NETWORK --> INFRA_DASH
    
    AUTH_FAILS --> SEC_DASH[Security Dashboard]
    RATE_LIMITS --> SEC_DASH
    SCAN_FAILS --> SEC_DASH
    VULN_TRENDS --> SEC_DASH
```

---

**Estes diagramas fornecem uma visão completa e técnica da arquitetura do ScanIA, servindo como guia para desenvolvimento e manutenção do sistema.**