# Sprint 4: Chat Inteligente e IA

**Duração**: 3 semanas  
**Objetivo**: Implementar sistema de chat inteligente com IA especializada em cybersegurança  
**Prioridade**: 🔥 Crítica  

## 🎯 Objetivos do Sprint

### Principais Entregáveis
- 🤖 Chat bot especializado em cybersegurança
- 💬 Interface de chat similar ao ChatGPT/Claude
- 🧠 Processamento de linguagem natural (NLP)
- 📊 Análise contextual de vulnerabilidades
- 🔍 Consultas inteligentes sobre dados de scan
- 💡 Recomendações automatizadas de segurança
- 📝 Geração de relatórios via conversação

### Critérios de Aceitação
- [ ] Chat responde perguntas sobre cybersegurança
- [ ] Interface é intuitiva e responsiva
- [ ] Análise contextual dos dados do usuário
- [ ] Recomendações personalizadas
- [ ] Histórico de conversas salvo
- [ ] Integração com dados de scans
- [ ] Suporte a comandos especiais

## 🏗️ Arquitetura do Sprint

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND CHAT UI                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  CHAT INTERFACE │  │   MESSAGE FLOW  │  │  CONTEXT UI │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Input Field   │  │ • Real-time WS  │  │ • Scan Data │ │
│  │ • Message List  │  │ • Typing Indicator│ │ • Filters   │ │
│  │ • Attachments   │  │ • Auto-scroll   │  │ • Quick Cmds│ │
│  │ • Commands      │  │ • Message Status│  │ • Shortcuts │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CHAT API LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  CHAT SERVICE   │  │ WEBSOCKET MGR   │  │ CONTEXT MGR │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Message CRUD  │  │ • Real-time     │  │ • User Data │ │
│  │ • Conversation  │  │ • Broadcasting  │  │ • Scan Info │ │
│  │ • History Mgmt  │  │ • Connection    │  │ • Security  │ │
│  │ • User Context  │  │ • Status Track  │  │ • Analytics │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI ENGINE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   NLP PROCESSOR │  │  KNOWLEDGE BASE │  │ REASONING   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Intent Recog  │  │ • CVE Database  │  │ • Logic Eng │ │
│  │ • Entity Extract│  │ • Security KB   │  │ • Inference │ │
│  │ • Sentiment     │  │ • Best Practices│  │ • Decision  │ │
│  │ • Classification│  │ • Threat Intel  │  │ • Learning  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ RESPONSE GEN    │  │  EXTERNAL APIs  │  │ MONITORING  │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Template Eng  │  │ • OpenAI/GPT    │  │ • Usage     │ │
│  │ • Content Gen   │  │ • Security APIs │  │ • Performance│ │
│  │ • Personalize   │  │ • Research APIs │  │ • Quality   │ │
│  │ • Format        │  │ • Update Feeds  │  │ • Accuracy  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Tasks Detalhadas

### Week 1: AI Engine e NLP

#### 🎯 Task 1.1: Arquitetura da IA (Day 1-3)
**Responsável**: AI/ML Engineer  
**Estimativa**: 24h  

**Atividades**:
1. **Core AI Service Architecture**
   ```python
   # services/ai_service.py
   from typing import Dict, List, Optional, Any
   from dataclasses import dataclass
   from enum import Enum
   import openai
   import spacy
   from transformers import pipeline
   import json
   
   class IntentType(Enum):
       QUESTION = "question"
       SCAN_REQUEST = "scan_request"
       REPORT_REQUEST = "report_request"
       ANALYSIS_REQUEST = "analysis_request"
       GENERAL_SECURITY = "general_security"
       HELP_REQUEST = "help_request"
       COMPLAINT_REPORT = "complaint_report"
   
   @dataclass
   class AIMessage:
       content: str
       intent: IntentType
       entities: Dict[str, Any]
       confidence: float
       context: Dict[str, Any]
       suggested_actions: List[str]
   
   @dataclass
   class AIResponse:
       message: str
       intent: IntentType
       confidence: float
       entities: Dict[str, Any]
       actions: List[Dict[str, Any]]
       context_updates: Dict[str, Any]
       follow_up_questions: List[str]
   
   class CyberSecurityAI:
       def __init__(self):
           # Initialize NLP models
           self.nlp = spacy.load("pt_core_news_lg")  # Portuguese model
           self.intent_classifier = pipeline(
               "text-classification",
               model="microsoft/DialoGPT-medium",
               return_all_scores=True
           )
           
           # Initialize knowledge base
           self.knowledge_base = CyberSecurityKnowledgeBase()
           self.context_manager = ConversationContextManager()
           
           # OpenAI configuration
           openai.api_key = settings.OPENAI_API_KEY
       
       async def process_message(
           self, 
           message: str, 
           user_id: str, 
           conversation_id: str,
           user_context: Dict[str, Any] = None
       ) -> AIResponse:
           """Processar mensagem do usuário e gerar resposta inteligente"""
           
           # 1. Pré-processamento e limpeza
           cleaned_message = self._preprocess_message(message)
           
           # 2. Análise de intenção
           intent = await self._classify_intent(cleaned_message)
           
           # 3. Extração de entidades
           entities = self._extract_entities(cleaned_message)
           
           # 4. Recuperar contexto da conversa
           context = await self.context_manager.get_context(
               user_id, conversation_id
           )
           
           # 5. Adicionar contexto do usuário (scans, vulnerabilidades, etc.)
           if user_context:
               context.update(user_context)
           
           # 6. Gerar resposta baseada na intenção
           response = await self._generate_response(
               message=cleaned_message,
               intent=intent,
               entities=entities,
               context=context
           )
           
           # 7. Atualizar contexto da conversa
           await self.context_manager.update_context(
               user_id, conversation_id, response.context_updates
           )
           
           return response
       
       def _preprocess_message(self, message: str) -> str:
           """Limpar e normalizar mensagem"""
           # Remove caracteres especiais, normaliza espaços, etc.
           cleaned = message.strip().lower()
           
           # Remove stopwords específicas de chat
           stopwords = ["por favor", "obrigado", "olá", "oi"]
           words = cleaned.split()
           filtered_words = [w for w in words if w not in stopwords]
           
           return " ".join(filtered_words)
       
       async def _classify_intent(self, message: str) -> IntentType:
           """Classificar intenção da mensagem"""
           
           # Padrões simples para início
           patterns = {
               IntentType.SCAN_REQUEST: [
                   "scan", "escanear", "analisar", "verificar segurança",
                   "testar vulnerabilidade", "audit"
               ],
               IntentType.REPORT_REQUEST: [
                   "relatório", "report", "gerar documento", "pdf",
                   "exportar", "resumo"
               ],
               IntentType.ANALYSIS_REQUEST: [
                   "analisar", "explicar", "o que significa", "como corrigir",
                   "vulnerabilidade", "CVE"
               ],
               IntentType.GENERAL_SECURITY: [
                   "segurança", "proteção", "best practice", "recomendação",
                   "como proteger", "firewall", "ssl"
               ],
               IntentType.HELP_REQUEST: [
                   "ajuda", "help", "como", "tutorial", "não entendo",
                   "explicação"
               ]
           }
           
           message_lower = message.lower()
           
           for intent, keywords in patterns.items():
               if any(keyword in message_lower for keyword in keywords):
                   return intent
           
           # Fallback para classificação mais sofisticada usando ML
           try:
               result = self.intent_classifier(message)
               # Process ML result and return appropriate intent
               return IntentType.QUESTION  # Default
           except:
               return IntentType.QUESTION
       
       def _extract_entities(self, message: str) -> Dict[str, Any]:
           """Extrair entidades da mensagem"""
           doc = self.nlp(message)
           
           entities = {
               "urls": [],
               "ips": [],
               "cve_ids": [],
               "tech_terms": [],
               "severity_levels": []
           }
           
           # Extract URLs
           import re
           url_pattern = r'https?://[^\s]+'
           entities["urls"] = re.findall(url_pattern, message)
           
           # Extract IP addresses
           ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
           entities["ips"] = re.findall(ip_pattern, message)
           
           # Extract CVE IDs
           cve_pattern = r'CVE-\d{4}-\d{4,}'
           entities["cve_ids"] = re.findall(cve_pattern, message, re.IGNORECASE)
           
           # Extract technical terms
           tech_terms = ["xss", "sql injection", "csrf", "rce", "lfi", "rfi", 
                        "dos", "ddos", "mitm", "ssl", "tls", "https"]
           for term in tech_terms:
               if term in message.lower():
                   entities["tech_terms"].append(term)
           
           # Extract severity levels
           severity_terms = ["crítica", "alta", "média", "baixa", "critical", 
                           "high", "medium", "low"]
           for severity in severity_terms:
               if severity in message.lower():
                   entities["severity_levels"].append(severity)
           
           # Extract named entities from spaCy
           for ent in doc.ents:
               if ent.label_ not in entities:
                   entities[ent.label_] = []
               entities[ent.label_].append(ent.text)
           
           return entities
       
       async def _generate_response(
           self,
           message: str,
           intent: IntentType,
           entities: Dict[str, Any],
           context: Dict[str, Any]
       ) -> AIResponse:
           """Gerar resposta baseada na intenção e contexto"""
           
           if intent == IntentType.SCAN_REQUEST:
               return await self._handle_scan_request(message, entities, context)
           elif intent == IntentType.REPORT_REQUEST:
               return await self._handle_report_request(message, entities, context)
           elif intent == IntentType.ANALYSIS_REQUEST:
               return await self._handle_analysis_request(message, entities, context)
           elif intent == IntentType.GENERAL_SECURITY:
               return await self._handle_security_question(message, entities, context)
           elif intent == IntentType.HELP_REQUEST:
               return await self._handle_help_request(message, entities, context)
           else:
               return await self._handle_general_question(message, entities, context)
       
       async def _handle_scan_request(
           self, message: str, entities: Dict[str, Any], context: Dict[str, Any]
       ) -> AIResponse:
           """Lidar com solicitações de scan"""
           
           urls = entities.get("urls", [])
           if not urls:
               return AIResponse(
                   message="Para iniciar um scan, preciso de uma URL. Você pode fornecer a URL do site que deseja analisar?",
                   intent=IntentType.SCAN_REQUEST,
                   confidence=0.9,
                   entities=entities,
                   actions=[
                       {
                           "type": "request_url",
                           "message": "Solicitar URL para scan"
                       }
                   ],
                   context_updates={"awaiting_url": True},
                   follow_up_questions=[
                       "Que tipo de scan você gostaria de executar?",
                       "Há alguma configuração específica para este scan?"
                   ]
               )
           
           # Se há URLs, preparar para iniciar scan
           target_url = urls[0]
           scan_types = self._determine_scan_types(message, entities)
           
           return AIResponse(
               message=f"Perfeito! Vou iniciar um scan de segurança em {target_url}. "
                      f"Tipos de scan selecionados: {', '.join(scan_types)}. "
                      f"O scan pode levar alguns minutos. Você será notificado quando completar.",
               intent=IntentType.SCAN_REQUEST,
               confidence=0.95,
               entities=entities,
               actions=[
                   {
                       "type": "start_scan",
                       "target_url": target_url,
                       "scan_types": scan_types
                   }
               ],
               context_updates={
                   "last_scan_url": target_url,
                   "scan_in_progress": True
               },
               follow_up_questions=[
                   "Gostaria de receber notificações por email?",
                   "Quer configurar scans recorrentes para este site?"
               ]
           )
   
       def _determine_scan_types(self, message: str, entities: Dict[str, Any]) -> List[str]:
           """Determinar tipos de scan baseado na mensagem"""
           scan_types = ["owasp_zap"]  # Default
           
           message_lower = message.lower()
           
           if any(term in message_lower for term in ["porta", "port", "nmap"]):
               scan_types.append("nmap")
           
           if any(term in message_lower for term in ["ssl", "tls", "certificado"]):
               scan_types.append("ssl_checker")
           
           if any(term in message_lower for term in ["crawler", "estrutura", "links"]):
               scan_types.append("web_crawler")
           
           return scan_types
   ```

2. **Knowledge Base Implementation**
   ```python
   # services/knowledge_base.py
   from typing import Dict, List, Optional
   import json
   import sqlite3
   from pathlib import Path
   
   class CyberSecurityKnowledgeBase:
       def __init__(self):
           self.db_path = Path("data/cybersec_kb.db")
           self._initialize_database()
           self._load_knowledge()
       
       def _initialize_database(self):
           """Inicializar base de conhecimento SQLite"""
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           
           # Tabela de vulnerabilidades conhecidas
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS vulnerabilities (
                   id INTEGER PRIMARY KEY,
                   cve_id TEXT UNIQUE,
                   title TEXT,
                   description TEXT,
                   severity TEXT,
                   cvss_score REAL,
                   solution TEXT,
                   references TEXT,
                   tags TEXT
               )
           """)
           
           # Tabela de best practices
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS best_practices (
                   id INTEGER PRIMARY KEY,
                   category TEXT,
                   title TEXT,
                   description TEXT,
                   implementation TEXT,
                   difficulty TEXT,
                   impact TEXT
               )
           """)
           
           # Tabela de threat intelligence
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS threat_intel (
                   id INTEGER PRIMARY KEY,
                   threat_type TEXT,
                   iocs TEXT,
                   description TEXT,
                   mitigation TEXT,
                   last_updated TIMESTAMP
               )
           """)
           
           conn.commit()
           conn.close()
       
       def _load_knowledge(self):
           """Carregar conhecimento inicial"""
           # Carregar CVEs mais comuns
           common_cves = [
               {
                   "cve_id": "CVE-2021-44228",
                   "title": "Log4j Remote Code Execution",
                   "description": "Vulnerabilidade crítica no Apache Log4j que permite execução remota de código",
                   "severity": "critical",
                   "cvss_score": 10.0,
                   "solution": "Atualizar Log4j para versão 2.17.0 ou superior",
                   "references": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-44228"
               },
               # Adicionar mais CVEs...
           ]
           
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           
           for cve in common_cves:
               cursor.execute("""
                   INSERT OR REPLACE INTO vulnerabilities 
                   (cve_id, title, description, severity, cvss_score, solution, references)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
               """, (
                   cve["cve_id"], cve["title"], cve["description"],
                   cve["severity"], cve["cvss_score"], cve["solution"], cve["references"]
               ))
           
           conn.commit()
           conn.close()
       
       async def search_vulnerability(self, query: str) -> List[Dict[str, Any]]:
           """Buscar vulnerabilidades na base de conhecimento"""
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           
           cursor.execute("""
               SELECT * FROM vulnerabilities 
               WHERE title LIKE ? OR description LIKE ? OR cve_id LIKE ?
               ORDER BY cvss_score DESC
               LIMIT 10
           """, (f"%{query}%", f"%{query}%", f"%{query}%"))
           
           results = cursor.fetchall()
           conn.close()
           
           return [
               {
                   "cve_id": row[1],
                   "title": row[2],
                   "description": row[3],
                   "severity": row[4],
                   "cvss_score": row[5],
                   "solution": row[6],
                   "references": row[7]
               }
               for row in results
           ]
       
       async def get_best_practices(self, category: str = None) -> List[Dict[str, Any]]:
           """Obter melhores práticas de segurança"""
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           
           if category:
               cursor.execute("""
                   SELECT * FROM best_practices WHERE category = ?
               """, (category,))
           else:
               cursor.execute("SELECT * FROM best_practices")
           
           results = cursor.fetchall()
           conn.close()
           
           return [
               {
                   "category": row[1],
                   "title": row[2],
                   "description": row[3],
                   "implementation": row[4],
                   "difficulty": row[5],
                   "impact": row[6]
               }
               for row in results
           ]
   ```

**Deliverables**:
- [ ] Core AI service architecture
- [ ] NLP processing pipeline
- [ ] Knowledge base implementation
- [ ] Intent classification system

---

#### 🎯 Task 1.2: Context Management (Day 3-5)
**Responsável**: Backend Dev  
**Estimativa**: 20h  

**Atividades**:
1. **Conversation Context Manager**
   ```python
   # services/context_manager.py
   from typing import Dict, List, Optional, Any
   from datetime import datetime, timedelta
   import json
   from dataclasses import dataclass, asdict
   from app.models import Conversation, Message, Scan, Vulnerability
   
   @dataclass
   class UserContext:
       user_id: str
       recent_scans: List[Dict[str, Any]]
       active_vulnerabilities: List[Dict[str, Any]]
       security_posture: Dict[str, Any]
       preferences: Dict[str, Any]
       expertise_level: str  # beginner, intermediate, advanced
   
   @dataclass
   class ConversationContext:
       conversation_id: str
       current_topic: Optional[str]
       active_scan: Optional[str]
       pending_actions: List[Dict[str, Any]]
       user_intent_history: List[str]
       mentioned_entities: Dict[str, List[str]]
       last_updated: datetime
   
   class ConversationContextManager:
       def __init__(self):
           self.redis = redis.Redis(
               host=settings.REDIS_HOST,
               port=settings.REDIS_PORT,
               decode_responses=True
           )
           self.context_ttl = 3600 * 24  # 24 hours
       
       async def get_user_context(self, user_id: str) -> UserContext:
           """Obter contexto completo do usuário"""
           
           # Buscar dados de scans recentes
           recent_scans = await self._get_recent_scans(user_id, limit=5)
           
           # Buscar vulnerabilidades ativas
           active_vulns = await self._get_active_vulnerabilities(user_id)
           
           # Calcular postura de segurança
           security_posture = await self._calculate_security_posture(user_id)
           
           # Obter preferências do usuário
           preferences = await self._get_user_preferences(user_id)
           
           # Determinar nível de expertise
           expertise_level = await self._determine_expertise_level(user_id)
           
           return UserContext(
               user_id=user_id,
               recent_scans=recent_scans,
               active_vulnerabilities=active_vulns,
               security_posture=security_posture,
               preferences=preferences,
               expertise_level=expertise_level
           )
       
       async def get_conversation_context(
           self, 
           user_id: str, 
           conversation_id: str
       ) -> ConversationContext:
           """Obter contexto da conversa"""
           
           cache_key = f"context:{user_id}:{conversation_id}"
           cached_context = self.redis.get(cache_key)
           
           if cached_context:
               data = json.loads(cached_context)
               return ConversationContext(**data)
           
           # Criar novo contexto
           context = ConversationContext(
               conversation_id=conversation_id,
               current_topic=None,
               active_scan=None,
               pending_actions=[],
               user_intent_history=[],
               mentioned_entities={},
               last_updated=datetime.utcnow()
           )
           
           # Salvar no cache
           await self._save_context(user_id, context)
           
           return context
       
       async def update_context(
           self,
           user_id: str,
           conversation_id: str,
           updates: Dict[str, Any]
       ):
           """Atualizar contexto da conversa"""
           
           context = await self.get_conversation_context(user_id, conversation_id)
           
           # Atualizar campos
           for key, value in updates.items():
               if hasattr(context, key):
                   setattr(context, key, value)
           
           context.last_updated = datetime.utcnow()
           
           # Salvar contexto atualizado
           await self._save_context(user_id, context)
       
       async def add_intent_to_history(
           self,
           user_id: str,
           conversation_id: str,
           intent: str
       ):
           """Adicionar intenção ao histórico"""
           
           context = await self.get_conversation_context(user_id, conversation_id)
           context.user_intent_history.append(intent)
           
           # Manter apenas os últimos 10 intents
           if len(context.user_intent_history) > 10:
               context.user_intent_history = context.user_intent_history[-10:]
           
           await self._save_context(user_id, context)
       
       async def add_mentioned_entity(
           self,
           user_id: str,
           conversation_id: str,
           entity_type: str,
           entity_value: str
       ):
           """Adicionar entidade mencionada"""
           
           context = await self.get_conversation_context(user_id, conversation_id)
           
           if entity_type not in context.mentioned_entities:
               context.mentioned_entities[entity_type] = []
           
           if entity_value not in context.mentioned_entities[entity_type]:
               context.mentioned_entities[entity_type].append(entity_value)
           
           await self._save_context(user_id, context)
       
       async def _save_context(self, user_id: str, context: ConversationContext):
           """Salvar contexto no cache"""
           cache_key = f"context:{user_id}:{context.conversation_id}"
           context_data = asdict(context)
           
           # Convert datetime to string for JSON serialization
           context_data['last_updated'] = context.last_updated.isoformat()
           
           self.redis.setex(
               cache_key,
               self.context_ttl,
               json.dumps(context_data, default=str)
           )
       
       async def _get_recent_scans(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
           """Obter scans recentes do usuário"""
           from app.services.scanner_service import ScannerService
           
           scanner_service = ScannerService()
           scans = await scanner_service.get_user_scans(
               user_id, skip=0, limit=limit
           )
           
           return [
               {
                   "id": scan.id,
                   "target_url": scan.target_url,
                   "status": scan.status,
                   "created_at": scan.created_at.isoformat(),
                   "vulnerability_count": len(scan.vulnerabilities)
               }
               for scan in scans
           ]
       
       async def _get_active_vulnerabilities(self, user_id: str) -> List[Dict[str, Any]]:
           """Obter vulnerabilidades ativas do usuário"""
           
           query = """
               SELECT v.id, v.title, v.severity, v.cvss_score, s.target_url
               FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s AND v.status = 'open'
               ORDER BY v.cvss_score DESC
               LIMIT 10
           """
           
           # Execute query and return results
           # Implementation depends on your database setup
           
           return []  # Placeholder
       
       async def _calculate_security_posture(self, user_id: str) -> Dict[str, Any]:
           """Calcular postura geral de segurança"""
           
           # Implementar cálculo baseado em vulnerabilidades, scans, etc.
           return {
               "risk_score": 0.0,
               "trend": "improving",
               "critical_issues": 0,
               "last_assessment": datetime.utcnow().isoformat()
           }
       
       async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
           """Obter preferências do usuário"""
           
           # Implementar busca de preferências
           return {
               "language": "pt-BR",
               "notification_level": "normal",
               "report_format": "detailed",
               "expertise_mode": "guided"
           }
       
       async def _determine_expertise_level(self, user_id: str) -> str:
           """Determinar nível de expertise do usuário"""
           
           # Analisar histórico de uso, tipos de perguntas, etc.
           return "intermediate"  # Default
   ```

**Deliverables**:
- [ ] Context management system
- [ ] User context tracking
- [ ] Conversation state management
- [ ] Redis-based caching

### Week 2: Chat API e Backend

#### 🎯 Task 2.1: Chat API Development (Day 6-10)
**Responsável**: Backend Dev  
**Estimativa**: 40h  

**Atividades**:
1. **Chat API Endpoints**
   ```python
   # app/api/v1/chat.py
   from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
   from fastapi.websockets import WebSocket, WebSocketDisconnect
   from typing import List, Optional
   from app.services.ai_service import CyberSecurityAI
   from app.services.context_manager import ConversationContextManager
   from app.services.chat_service import ChatService
   from app.schemas.chat import (
       MessageCreate, MessageResponse, ConversationResponse,
       ConversationCreate, ChatContext
   )
   
   router = APIRouter(prefix="/chat", tags=["chat"])
   
   # Initialize services
   ai_service = CyberSecurityAI()
   context_manager = ConversationContextManager()
   chat_service = ChatService()
   
   @router.post("/conversations", response_model=ConversationResponse)
   async def create_conversation(
       conversation_data: ConversationCreate,
       current_user: User = Depends(get_current_user),
       chat_service: ChatService = Depends()
   ):
       """Criar nova conversa"""
       try:
           conversation = await chat_service.create_conversation(
               user_id=current_user.id,
               title=conversation_data.title or "Nova Conversa",
               context=conversation_data.context or {}
           )
           
           return ConversationResponse(
               id=conversation.id,
               title=conversation.title,
               created_at=conversation.created_at,
               updated_at=conversation.updated_at,
               message_count=0
           )
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Erro ao criar conversa: {str(e)}")
   
   @router.get("/conversations", response_model=List[ConversationResponse])
   async def list_conversations(
       skip: int = 0,
       limit: int = 20,
       current_user: User = Depends(get_current_user),
       chat_service: ChatService = Depends()
   ):
       """Listar conversas do usuário"""
       conversations = await chat_service.get_user_conversations(
           user_id=current_user.id,
           skip=skip,
           limit=limit
       )
       
       return [
           ConversationResponse(
               id=conv.id,
               title=conv.title,
               created_at=conv.created_at,
               updated_at=conv.updated_at,
               message_count=len(conv.messages)
           )
           for conv in conversations
       ]
   
   @router.get("/conversations/{conversation_id}/messages")
   async def get_conversation_messages(
       conversation_id: str,
       skip: int = 0,
       limit: int = 50,
       current_user: User = Depends(get_current_user),
       chat_service: ChatService = Depends()
   ):
       """Obter mensagens da conversa"""
       
       # Verificar se o usuário tem acesso à conversa
       conversation = await chat_service.get_conversation(conversation_id)
       if not conversation or conversation.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Conversa não encontrada")
       
       messages = await chat_service.get_conversation_messages(
           conversation_id=conversation_id,
           skip=skip,
           limit=limit
       )
       
       return [
           MessageResponse(
               id=msg.id,
               role=msg.role,
               content=msg.content,
               metadata=msg.metadata,
               created_at=msg.created_at
           )
           for msg in messages
       ]
   
   @router.post("/conversations/{conversation_id}/messages")
   async def send_message(
       conversation_id: str,
       message_data: MessageCreate,
       background_tasks: BackgroundTasks,
       current_user: User = Depends(get_current_user),
       chat_service: ChatService = Depends()
   ):
       """Enviar mensagem e obter resposta da IA"""
       
       # Verificar acesso à conversa
       conversation = await chat_service.get_conversation(conversation_id)
       if not conversation or conversation.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Conversa não encontrada")
       
       try:
           # Salvar mensagem do usuário
           user_message = await chat_service.add_message(
               conversation_id=conversation_id,
               role="user",
               content=message_data.content,
               metadata=message_data.metadata or {}
           )
           
           # Obter contexto do usuário
           user_context = await context_manager.get_user_context(current_user.id)
           
           # Processar mensagem com IA
           ai_response = await ai_service.process_message(
               message=message_data.content,
               user_id=current_user.id,
               conversation_id=conversation_id,
               user_context=user_context.__dict__
           )
           
           # Salvar resposta da IA
           ai_message = await chat_service.add_message(
               conversation_id=conversation_id,
               role="assistant",
               content=ai_response.message,
               metadata={
                   "intent": ai_response.intent.value,
                   "confidence": ai_response.confidence,
                   "entities": ai_response.entities,
                   "actions": ai_response.actions
               }
           )
           
           # Executar ações em background se necessário
           if ai_response.actions:
               background_tasks.add_task(
                   execute_ai_actions,
                   ai_response.actions,
                   current_user.id,
                   conversation_id
               )
           
           return {
               "user_message": MessageResponse(
                   id=user_message.id,
                   role=user_message.role,
                   content=user_message.content,
                   created_at=user_message.created_at
               ),
               "ai_response": MessageResponse(
                   id=ai_message.id,
                   role=ai_message.role,
                   content=ai_message.content,
                   metadata=ai_message.metadata,
                   created_at=ai_message.created_at
               ),
               "follow_up_questions": ai_response.follow_up_questions,
               "suggested_actions": [action.get("message", "") for action in ai_response.actions]
           }
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")
   
   async def execute_ai_actions(
       actions: List[Dict[str, Any]], 
       user_id: str, 
       conversation_id: str
   ):
       """Executar ações sugeridas pela IA"""
       
       for action in actions:
           action_type = action.get("type")
           
           if action_type == "start_scan":
               # Iniciar scan automaticamente
               from app.services.scanner_service import ScannerService
               scanner_service = ScannerService()
               
               await scanner_service.start_scan(
                   user_id=user_id,
                   target_url=action["target_url"],
                   scan_types=action["scan_types"]
               )
           
           elif action_type == "generate_report":
               # Gerar relatório
               from app.services.report_service import ReportService
               report_service = ReportService()
               
               await report_service.generate_report_async(
                   scan_id=action["scan_id"],
                   report_type=action.get("report_type", "technical_detailed")
               )
           
           # Adicionar mais tipos de ações conforme necessário
   
   # WebSocket endpoint para chat em tempo real
   class ConnectionManager:
       def __init__(self):
           self.active_connections: Dict[str, WebSocket] = {}
       
       async def connect(self, websocket: WebSocket, user_id: str):
           await websocket.accept()
           self.active_connections[user_id] = websocket
       
       def disconnect(self, user_id: str):
           if user_id in self.active_connections:
               del self.active_connections[user_id]
       
       async def send_message(self, user_id: str, message: dict):
           if user_id in self.active_connections:
               websocket = self.active_connections[user_id]
               await websocket.send_json(message)
   
   connection_manager = ConnectionManager()
   
   @router.websocket("/ws/{conversation_id}")
   async def websocket_chat(
       websocket: WebSocket,
       conversation_id: str,
       token: str = Query(...)
   ):
       # Authenticate user from token
       try:
           current_user = await get_current_user_from_token(token)
       except:
           await websocket.close(code=4001, reason="Authentication failed")
           return
       
       # Verify conversation access
       conversation = await chat_service.get_conversation(conversation_id)
       if not conversation or conversation.user_id != current_user.id:
           await websocket.close(code=4004, reason="Conversation not found")
           return
       
       await connection_manager.connect(websocket, current_user.id)
       
       try:
           while True:
               # Receive message from client
               data = await websocket.receive_json()
               
               # Process message with AI
               user_context = await context_manager.get_user_context(current_user.id)
               ai_response = await ai_service.process_message(
                   message=data["content"],
                   user_id=current_user.id,
                   conversation_id=conversation_id,
                   user_context=user_context.__dict__
               )
               
               # Save messages
               user_message = await chat_service.add_message(
                   conversation_id, "user", data["content"]
               )
               ai_message = await chat_service.add_message(
                   conversation_id, "assistant", ai_response.message,
                   metadata={"intent": ai_response.intent.value}
               )
               
               # Send response
               await connection_manager.send_message(current_user.id, {
                   "type": "message",
                   "user_message": {
                       "id": str(user_message.id),
                       "content": user_message.content,
                       "created_at": user_message.created_at.isoformat()
                   },
                   "ai_response": {
                       "id": str(ai_message.id),
                       "content": ai_message.content,
                       "created_at": ai_message.created_at.isoformat()
                   }
               })
               
       except WebSocketDisconnect:
           connection_manager.disconnect(current_user.id)
   ```

**Deliverables**:
- [ ] Chat API endpoints completos
- [ ] WebSocket para tempo real
- [ ] Message persistence
- [ ] Action execution system

### Week 3: Frontend Chat Interface

#### 🎯 Task 3.1: Chat UI Components (Day 11-15)
**Responsável**: Frontend Dev  
**Estimativa**: 40h  

**Atividades**:
1. **Chat Interface Component**
   ```typescript
   // components/chat/ChatInterface.tsx
   import { useState, useEffect, useRef } from 'react';
   import { useWebSocket } from '@/hooks/useWebSocket';
   import { useMutation, useQuery } from 'react-query';
   import { chatApi } from '@/services/api';
   import { MessageBubble } from './MessageBubble';
   import { ChatInput } from './ChatInput';
   import { TypingIndicator } from './TypingIndicator';
   import { QuickActions } from './QuickActions';
   import { Send, Paperclip, Mic, Settings } from 'lucide-react';
   
   interface Message {
     id: string;
     role: 'user' | 'assistant';
     content: string;
     metadata?: any;
     created_at: string;
   }
   
   interface ChatInterfaceProps {
     conversationId: string;
     onNewConversation?: () => void;
   }
   
   export const ChatInterface: React.FC<ChatInterfaceProps> = ({
     conversationId,
     onNewConversation
   }) => {
     const [messages, setMessages] = useState<Message[]>([]);
     const [inputValue, setInputValue] = useState('');
     const [isTyping, setIsTyping] = useState(false);
     const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);
     const messagesEndRef = useRef<HTMLDivElement>(null);
   
     // WebSocket connection for real-time chat
     const { connect, disconnect, sendMessage, lastMessage } = useWebSocket(
       `ws://localhost:8000/api/v1/chat/ws/${conversationId}`
     );
   
     // Load conversation messages
     const { data: conversationMessages } = useQuery(
       ['conversationMessages', conversationId],
       () => chatApi.getConversationMessages(conversationId),
       {
         enabled: !!conversationId,
         onSuccess: (data) => {
           setMessages(data.reverse()); // Reverse to show newest at bottom
         }
       }
     );
   
     // Send message mutation
     const sendMessageMutation = useMutation(chatApi.sendMessage, {
       onMutate: (variables) => {
         // Optimistically add user message
         const userMessage: Message = {
           id: `temp-${Date.now()}`,
           role: 'user',
           content: variables.content,
           created_at: new Date().toISOString()
         };
         setMessages(prev => [...prev, userMessage]);
         setInputValue('');
         setIsTyping(true);
       },
       onSuccess: (data) => {
         // Replace optimistic message with real ones
         setMessages(prev => {
           const filtered = prev.filter(msg => !msg.id.startsWith('temp-'));
           return [
             ...filtered,
             data.user_message,
             data.ai_response
           ];
         });
         setFollowUpQuestions(data.follow_up_questions || []);
         setIsTyping(false);
       },
       onError: () => {
         setIsTyping(false);
         // Remove optimistic message on error
         setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp-')));
       }
     });
   
     // WebSocket message handler
     useEffect(() => {
       if (lastMessage) {
         const data = JSON.parse(lastMessage.data);
         if (data.type === 'message') {
           setMessages(prev => [
             ...prev,
             data.user_message,
             data.ai_response
           ]);
           setIsTyping(false);
         }
       }
     }, [lastMessage]);
   
     // Auto-scroll to bottom
     useEffect(() => {
       messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
     }, [messages]);
   
     // Connect WebSocket on mount
     useEffect(() => {
       if (conversationId) {
         connect();
         return () => disconnect();
       }
     }, [conversationId]);
   
     const handleSendMessage = async (content: string, attachments?: File[]) => {
       if (!content.trim()) return;
   
       try {
         await sendMessageMutation.mutateAsync({
           conversationId,
           content,
           metadata: {
             attachments: attachments?.map(f => f.name) || []
           }
         });
       } catch (error) {
         console.error('Error sending message:', error);
       }
     };
   
     const handleQuickAction = (action: string) => {
       setInputValue(action);
     };
   
     const handleFollowUpClick = (question: string) => {
       handleSendMessage(question);
       setFollowUpQuestions([]);
     };
   
     return (
       <div className="flex flex-col h-full bg-dark-bg">
         {/* Chat Header */}
         <div className="flex items-center justify-between p-4 border-b border-gray-700">
           <div>
             <h2 className="text-lg font-semibold text-white">
               Assistente de Cybersegurança
             </h2>
             <p className="text-sm text-gray-400">
               Especialista em análise de vulnerabilidades
             </p>
           </div>
           
           <div className="flex items-center gap-2">
             <button
               onClick={onNewConversation}
               className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700"
               title="Nova Conversa"
             >
               <Settings size={18} />
             </button>
           </div>
         </div>
   
         {/* Messages Area */}
         <div className="flex-1 overflow-y-auto p-4 space-y-4">
           {messages.length === 0 && (
             <div className="text-center py-8">
               <div className="text-gray-400 text-lg mb-4">
                 👋 Olá! Sou seu assistente de cybersegurança.
               </div>
               <div className="text-gray-500 text-sm mb-6">
                 Posso ajudar com análises de vulnerabilidades, recomendações de segurança,
                 execução de scans e muito mais!
               </div>
               
               <QuickActions onActionClick={handleQuickAction} />
             </div>
           )}
   
           {messages.map((message) => (
             <MessageBubble
               key={message.id}
               message={message}
               isUser={message.role === 'user'}
             />
           ))}
   
           {isTyping && <TypingIndicator />}
   
           {/* Follow-up Questions */}
           {followUpQuestions.length > 0 && (
             <div className="space-y-2">
               <p className="text-sm text-gray-400">Perguntas sugeridas:</p>
               <div className="flex flex-wrap gap-2">
                 {followUpQuestions.map((question, index) => (
                   <button
                     key={index}
                     onClick={() => handleFollowUpClick(question)}
                     className="px-3 py-1 text-sm bg-blue-600/20 text-blue-400 rounded-full hover:bg-blue-600/30 transition-colors"
                   >
                     {question}
                   </button>
                 ))}
               </div>
             </div>
           )}
   
           <div ref={messagesEndRef} />
         </div>
   
         {/* Chat Input */}
         <div className="p-4 border-t border-gray-700">
           <ChatInput
             value={inputValue}
             onChange={setInputValue}
             onSend={handleSendMessage}
             isLoading={sendMessageMutation.isLoading}
             placeholder="Digite sua pergunta sobre segurança..."
           />
         </div>
       </div>
     );
   };
   ```

2. **Message Bubble Component**
   ```typescript
   // components/chat/MessageBubble.tsx
   import { useState } from 'react';
   import { Copy, ThumbsUp, ThumbsDown, ExternalLink, Play } from 'lucide-react';
   import ReactMarkdown from 'react-markdown';
   import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
   import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
   
   interface MessageBubbleProps {
     message: {
       id: string;
       role: 'user' | 'assistant';
       content: string;
       metadata?: any;
       created_at: string;
     };
     isUser: boolean;
   }
   
   export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
     const [copied, setCopied] = useState(false);
     const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
   
     const handleCopy = async () => {
       await navigator.clipboard.writeText(message.content);
       setCopied(true);
       setTimeout(() => setCopied(false), 2000);
     };
   
     const handleFeedback = (type: 'up' | 'down') => {
       setFeedback(type);
       // Send feedback to API
       // chatApi.sendFeedback(message.id, type);
     };
   
     const renderContent = () => {
       if (isUser) {
         return (
           <div className="whitespace-pre-wrap break-words">
             {message.content}
           </div>
         );
       }
   
       // Assistant message with markdown support
       return (
         <ReactMarkdown
           className="prose prose-invert prose-sm max-w-none"
           components={{
             code({ node, inline, className, children, ...props }) {
               const match = /language-(\w+)/.exec(className || '');
               return !inline && match ? (
                 <SyntaxHighlighter
                   style={oneDark}
                   language={match[1]}
                   PreTag="div"
                   className="rounded-lg"
                   {...props}
                 >
                   {String(children).replace(/\n$/, '')}
                 </SyntaxHighlighter>
               ) : (
                 <code className="bg-gray-700 px-1 py-0.5 rounded text-sm" {...props}>
                   {children}
                 </code>
               );
             },
             a({ href, children }) {
               return (
                 <a
                   href={href}
                   target="_blank"
                   rel="noopener noreferrer"
                   className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
                 >
                   {children}
                   <ExternalLink size={12} />
                 </a>
               );
             }
           }}
         >
           {message.content}
         </ReactMarkdown>
       );
     };
   
     const renderMetadata = () => {
       if (!message.metadata || isUser) return null;
   
       const { intent, confidence, actions } = message.metadata;
   
       return (
         <div className="mt-3 p-3 bg-gray-800/50 rounded-lg text-xs">
           {intent && (
             <div className="flex items-center gap-2 mb-2">
               <span className="text-gray-400">Intenção:</span>
               <span className="text-blue-400 capitalize">{intent.replace('_', ' ')}</span>
               {confidence && (
                 <span className="text-gray-500">
                   ({Math.round(confidence * 100)}% confiança)
                 </span>
               )}
             </div>
           )}
           
           {actions && actions.length > 0 && (
             <div>
               <span className="text-gray-400">Ações executadas:</span>
               <ul className="mt-1 space-y-1">
                 {actions.map((action: any, index: number) => (
                   <li key={index} className="flex items-center gap-2 text-green-400">
                     <Play size={10} />
                     {action.message || action.type}
                   </li>
                 ))}
               </ul>
             </div>
           )}
         </div>
       );
     };
   
     return (
       <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
         <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
           {/* Avatar */}
           <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
             <div className={`
               w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
               ${isUser 
                 ? 'bg-blue-600 text-white' 
                 : 'bg-gradient-to-br from-purple-500 to-blue-600 text-white'
               }
             `}>
               {isUser ? 'U' : '🤖'}
             </div>
   
             {/* Message Content */}
             <div className={`
               rounded-2xl px-4 py-3 max-w-full
               ${isUser 
                 ? 'bg-blue-600 text-white rounded-br-md' 
                 : 'bg-gray-700 text-gray-100 rounded-bl-md'
               }
             `}>
               {renderContent()}
               {renderMetadata()}
               
               {/* Timestamp */}
               <div className={`
                 text-xs mt-2 opacity-70
                 ${isUser ? 'text-blue-100' : 'text-gray-400'}
               `}>
                 {new Date(message.created_at).toLocaleTimeString('pt-BR', {
                   hour: '2-digit',
                   minute: '2-digit'
                 })}
               </div>
             </div>
           </div>
   
           {/* Message Actions */}
           {!isUser && (
             <div className="flex items-center gap-2 mt-2 ml-11 opacity-0 group-hover:opacity-100 transition-opacity">
               <button
                 onClick={handleCopy}
                 className="p-1 text-gray-400 hover:text-gray-200 rounded"
                 title={copied ? 'Copiado!' : 'Copiar'}
               >
                 <Copy size={14} />
               </button>
               
               <button
                 onClick={() => handleFeedback('up')}
                 className={`p-1 rounded ${
                   feedback === 'up' 
                     ? 'text-green-400' 
                     : 'text-gray-400 hover:text-gray-200'
                 }`}
                 title="Resposta útil"
               >
                 <ThumbsUp size={14} />
               </button>
               
               <button
                 onClick={() => handleFeedback('down')}
                 className={`p-1 rounded ${
                   feedback === 'down' 
                     ? 'text-red-400' 
                     : 'text-gray-400 hover:text-gray-200'
                 }`}
                 title="Resposta não útil"
               >
                 <ThumbsDown size={14} />
               </button>
             </div>
           )}
         </div>
       </div>
     );
   };
   ```

**Deliverables**:
- [ ] Chat interface completa
- [ ] Message components
- [ ] Real-time WebSocket
- [ ] Markdown support para IA
- [ ] Feedback system

## 🧪 Testes do Sprint

### Unit Tests
```python
# tests/test_ai_service.py
import pytest
from app.services.ai_service import CyberSecurityAI, IntentType

@pytest.mark.asyncio
async def test_intent_classification():
    ai = CyberSecurityAI()
    
    # Test scan request intent
    intent = await ai._classify_intent("quero fazer um scan do site https://example.com")
    assert intent == IntentType.SCAN_REQUEST
    
    # Test report request intent
    intent = await ai._classify_intent("gerar relatório em PDF")
    assert intent == IntentType.REPORT_REQUEST
    
    # Test analysis request intent
    intent = await ai._classify_intent("o que significa CVE-2021-44228")
    assert intent == IntentType.ANALYSIS_REQUEST

def test_entity_extraction():
    ai = CyberSecurityAI()
    
    entities = ai._extract_entities("scan https://example.com para CVE-2021-44228")
    
    assert "https://example.com" in entities["urls"]
    assert "CVE-2021-44228" in entities["cve_ids"]
```

### Integration Tests
```typescript
// tests/chat.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from '@/components/chat/ChatInterface';

describe('ChatInterface', () => {
  test('sends message and displays response', async () => {
    render(<ChatInterface conversationId="test-conversation" />);
    
    const input = screen.getByPlaceholderText(/digite sua pergunta/i);
    const sendButton = screen.getByRole('button', { name: /enviar/i });
    
    fireEvent.change(input, { target: { value: 'Como fazer um scan?' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Como fazer um scan?')).toBeInTheDocument();
    });
  });
});
```

## 📊 Métricas de Sucesso

### Qualidade da IA
- [ ] **Intent Classification**: >90% accuracy
- [ ] **Response Relevance**: >85% user satisfaction
- [ ] **Context Retention**: 10+ message context
- [ ] **Entity Recognition**: >80% accuracy

### Performance
- [ ] **Response Time**: <3 segundos
- [ ] **WebSocket Latency**: <100ms
- [ ] **Message Throughput**: 100+ msg/min
- [ ] **Memory Usage**: <512MB per session

### User Experience
- [ ] **Interface Responsiveness**: Smooth scrolling
- [ ] **Real-time Updates**: No delays
- [ ] **Mobile Compatibility**: Full functionality
- [ ] **Accessibility**: WCAG 2.1 AA

---

**Sprint 4 transforma ScanIA em um assistente inteligente de cybersegurança, diferenciando-o de outras ferramentas do mercado.**