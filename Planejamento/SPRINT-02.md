# Sprint 2: Scanner Core

**Duração**: 3 semanas  
**Objetivo**: Implementar o coração do ScanIA - scanner de vulnerabilidades e geração de relatórios  
**Prioridade**: 🔥 Crítica  

## 🎯 Objetivos do Sprint

### Principais Entregáveis
- 🔍 Scanner de vulnerabilidades funcional
- 📄 Geração automática de relatórios PDF
- 🗄️ Sistema de armazenamento de resultados
- 🔗 Integração com OWASP ZAP
- 🌐 Scanner de portas com Nmap
- 📊 Interface para execução de scans
- ⚡ Sistema de filas para processamento assíncrono

### Critérios de Aceitação
- [ ] Usuário pode inserir URL e executar scan
- [ ] Sistema detecta vulnerabilidades comuns (XSS, SQLi, etc.)
- [ ] Relatório PDF é gerado automaticamente
- [ ] Resultados ficam salvos no histórico
- [ ] Scanner roda em background sem travar interface
- [ ] Progress bar mostra andamento do scan
- [ ] Notificação quando scan completa

## 🏗️ Arquitetura do Sprint

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Backend API   │────│  Scanner Engine │
│                 │    │                 │    │                 │
│ • Scan Form     │    │ • Scan API      │    │ • OWASP ZAP     │
│ • Progress UI   │    │ • Queue Manager │    │ • Nmap          │
│ • Results View  │    │ • WebSocket     │    │ • SSL Checker   │
│ • PDF Viewer    │    │ • Report API    │    │ • Custom Tools  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                        ┌───────────────┐      ┌───────────────┐
                        │   Database    │      │  File Storage │
                        │               │      │               │
                        │ • Scans       │      │ • PDF Reports │
                        │ • Results     │      │ • Screenshots │
                        │ • Vulns       │      │ • Raw Data    │
                        └───────────────┘      └───────────────┘
                                │
                        ┌───────────────┐
                        │ Redis Queue   │
                        │               │
                        │ • Scan Jobs   │
                        │ • Notifications│
                        │ • Cache       │
                        └───────────────┘
```

## 📋 Tasks Detalhadas

### Week 1: Scanner Foundation

#### 🎯 Task 1.1: Scanner Engine Architecture (Day 1-3)
**Responsável**: Backend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **Scanner Base Class**
   ```python
   # scanner/base.py
   from abc import ABC, abstractmethod
   from typing import Dict, List, Any
   from dataclasses import dataclass
   
   @dataclass
   class ScanResult:
       vulnerability_id: str
       severity: str  # critical, high, medium, low, info
       title: str
       description: str
       solution: str
       affected_url: str
       evidence: Dict[str, Any]
       cvss_score: float
       cve_id: Optional[str] = None
   
   class ScannerEngine(ABC):
       def __init__(self, target_url: str, options: Dict[str, Any]):
           self.target_url = target_url
           self.options = options
           self.results: List[ScanResult] = []
       
       @abstractmethod
       async def scan(self) -> List[ScanResult]:
           pass
       
       @abstractmethod
       def get_progress(self) -> float:
           pass
   ```

2. **OWASP ZAP Integration**
   ```python
   # scanner/engines/owasp_zap.py
   from zapv2 import ZAPv2
   import asyncio
   import logging
   
   class OWASPZapScanner(ScannerEngine):
       def __init__(self, target_url: str, options: Dict[str, Any]):
           super().__init__(target_url, options)
           self.zap = ZAPv2(
               apikey=settings.ZAP_API_KEY,
               proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
           )
       
       async def scan(self) -> List[ScanResult]:
           try:
               # Start ZAP session
               self.zap.core.new_session()
               
               # Spider the target
               spider_id = self.zap.spider.scan(self.target_url)
               await self._wait_for_spider(spider_id)
               
               # Active scan
               scan_id = self.zap.ascan.scan(self.target_url)
               await self._wait_for_scan(scan_id)
               
               # Parse results
               alerts = self.zap.core.alerts()
               return self._parse_alerts(alerts)
               
           except Exception as e:
               logging.error(f"ZAP scan failed: {str(e)}")
               raise ScannerException(f"OWASP ZAP scan failed: {str(e)}")
       
       async def _wait_for_spider(self, spider_id: str):
           while int(self.zap.spider.status(spider_id)) < 100:
               await asyncio.sleep(2)
       
       async def _wait_for_scan(self, scan_id: str):
           while int(self.zap.ascan.status(scan_id)) < 100:
               await asyncio.sleep(5)
       
       def _parse_alerts(self, alerts) -> List[ScanResult]:
           results = []
           for alert in alerts:
               result = ScanResult(
                   vulnerability_id=f"zap_{alert['alertRef']}",
                   severity=self._map_severity(alert['risk']),
                   title=alert['alert'],
                   description=alert['description'],
                   solution=alert['solution'],
                   affected_url=alert['url'],
                   evidence={
                       'param': alert.get('param', ''),
                       'attack': alert.get('attack', ''),
                       'evidence': alert.get('evidence', '')
                   },
                   cvss_score=float(alert.get('cweid', 0)),
                   cve_id=alert.get('cve', None)
               )
               results.append(result)
           return results
   ```

3. **Nmap Port Scanner**
   ```python
   # scanner/engines/nmap_scanner.py
   import nmap
   import asyncio
   from concurrent.futures import ThreadPoolExecutor
   
   class NmapScanner(ScannerEngine):
       def __init__(self, target_url: str, options: Dict[str, Any]):
           super().__init__(target_url, options)
           self.nm = nmap.PortScanner()
           self.progress = 0.0
       
       async def scan(self) -> List[ScanResult]:
           executor = ThreadPoolExecutor(max_workers=1)
           loop = asyncio.get_event_loop()
           
           # Extract hostname from URL
           from urllib.parse import urlparse
           parsed = urlparse(self.target_url)
           host = parsed.netloc
           
           # Run nmap scan in thread
           result = await loop.run_in_executor(
               executor, 
               self._run_nmap_scan, 
               host
           )
           
           return self._parse_nmap_results(result)
       
       def _run_nmap_scan(self, host: str):
           # Scan common ports + service detection
           return self.nm.scan(
               host, 
               '22,23,25,53,80,110,443,993,995,1723,3306,3389,5432,5900,8080,8443',
               '-sV -sC --script vuln'
           )
       
       def _parse_nmap_results(self, scan_result) -> List[ScanResult]:
           results = []
           
           for host in scan_result['scan']:
               for port in scan_result['scan'][host]['tcp']:
                   port_info = scan_result['scan'][host]['tcp'][port]
                   
                   # Check for vulnerabilities
                   if 'script' in port_info:
                       for script_name, script_output in port_info['script'].items():
                           if any(vuln_keyword in script_output.lower() 
                                  for vuln_keyword in ['vulnerable', 'exploit', 'cve']):
                               
                               severity = self._assess_port_severity(port, script_output)
                               
                               result = ScanResult(
                                   vulnerability_id=f"nmap_{host}_{port}_{script_name}",
                                   severity=severity,
                                   title=f"Port {port} - {script_name}",
                                   description=script_output,
                                   solution=self._get_port_solution(port, script_name),
                                   affected_url=f"{self.target_url}:{port}",
                                   evidence={
                                       'port': port,
                                       'service': port_info.get('name', 'unknown'),
                                       'version': port_info.get('version', 'unknown'),
                                       'script_output': script_output
                                   },
                                   cvss_score=self._calculate_cvss_score(severity)
                               )
                               results.append(result)
           
           return results
   ```

**Deliverables**:
- [ ] Scanner base architecture
- [ ] OWASP ZAP integration
- [ ] Nmap port scanner
- [ ] Error handling robusto

---

#### 🎯 Task 1.2: Scanner Manager (Day 3-5)
**Responsável**: Backend Dev  
**Estimativa**: 20h  

**Atividades**:
1. **Scanner Orchestrator**
   ```python
   # scanner/manager.py
   from typing import List, Dict, Any
   from celery import group
   from app.models.scan import Scan, ScanStatus
   
   class ScannerManager:
       def __init__(self):
           self.engines = {
               'owasp_zap': OWASPZapScanner,
               'nmap': NmapScanner,
               'ssl_checker': SSLScanner,
               'web_crawler': WebCrawlerScanner
           }
       
       async def start_scan(
           self, 
           user_id: str, 
           target_url: str, 
           scan_types: List[str],
           options: Dict[str, Any] = None
       ) -> str:
           # Create scan record
           scan = Scan(
               user_id=user_id,
               target_url=target_url,
               scan_types=scan_types,
               status=ScanStatus.PENDING,
               options=options or {}
           )
           await scan.save()
           
           # Queue scan job
           scan_job = group([
               run_scanner_task.s(scan.id, engine_name, target_url, options)
               for engine_name in scan_types
               if engine_name in self.engines
           ])
           
           job = scan_job.apply_async()
           scan.celery_job_id = job.id
           await scan.save()
           
           return scan.id
       
       async def get_scan_progress(self, scan_id: str) -> Dict[str, Any]:
           scan = await Scan.get(scan_id)
           if not scan:
               raise ScanNotFoundException()
           
           # Get progress from Celery
           from celery.result import GroupResult
           job = GroupResult.restore(scan.celery_job_id)
           
           if job:
               progress = {
                   'overall_progress': self._calculate_overall_progress(job),
                   'engines_progress': self._get_engines_progress(job),
                   'status': scan.status.value,
                   'started_at': scan.started_at,
                   'estimated_completion': self._estimate_completion(job)
               }
           else:
               progress = {'overall_progress': 0, 'status': 'unknown'}
           
           return progress
       
       async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
           scan = await Scan.get_with_results(scan_id)
           if not scan:
               raise ScanNotFoundException()
           
           return {
               'scan_info': {
                   'id': scan.id,
                   'target_url': scan.target_url,
                   'started_at': scan.started_at,
                   'completed_at': scan.completed_at,
                   'duration': scan.duration_seconds,
                   'status': scan.status.value
               },
               'summary': {
                   'total_vulnerabilities': len(scan.vulnerabilities),
                   'critical_count': len([v for v in scan.vulnerabilities if v.severity == 'critical']),
                   'high_count': len([v for v in scan.vulnerabilities if v.severity == 'high']),
                   'medium_count': len([v for v in scan.vulnerabilities if v.severity == 'medium']),
                   'low_count': len([v for v in scan.vulnerabilities if v.severity == 'low']),
                   'info_count': len([v for v in scan.vulnerabilities if v.severity == 'info']),
               },
               'vulnerabilities': [
                   {
                       'id': v.id,
                       'title': v.title,
                       'severity': v.severity,
                       'cvss_score': v.cvss_score,
                       'affected_url': v.affected_url,
                       'description': v.description[:200] + '...' if len(v.description) > 200 else v.description
                   }
                   for v in scan.vulnerabilities
               ]
           }
   ```

2. **Celery Tasks**
   ```python
   # scanner/tasks.py
   from celery import Celery
   from app.core.celery_app import celery_app
   import logging
   
   @celery_app.task(bind=True)
   def run_scanner_task(self, scan_id: str, engine_name: str, target_url: str, options: Dict[str, Any]):
       try:
           # Update scan status
           scan = Scan.get_sync(scan_id)
           scan.status = ScanStatus.RUNNING
           scan.save_sync()
           
           # Get scanner engine
           engine_class = ScannerManager().engines[engine_name]
           scanner = engine_class(target_url, options)
           
           # Progress callback
           def progress_callback(progress: float):
               self.update_state(
                   state='PROGRESS',
                   meta={'engine': engine_name, 'progress': progress}
               )
           
           # Run scan
           results = await scanner.scan()
           
           # Save results
           for result in results:
               vulnerability = Vulnerability(
                   scan_id=scan_id,
                   vulnerability_id=result.vulnerability_id,
                   severity=result.severity,
                   title=result.title,
                   description=result.description,
                   solution=result.solution,
                   affected_url=result.affected_url,
                   evidence=result.evidence,
                   cvss_score=result.cvss_score,
                   cve_id=result.cve_id
               )
               await vulnerability.save()
           
           return {
               'engine': engine_name,
               'vulnerabilities_found': len(results),
               'status': 'completed'
           }
           
       except Exception as e:
           logging.error(f"Scanner task failed: {str(e)}")
           scan.status = ScanStatus.FAILED
           scan.error_message = str(e)
           scan.save_sync()
           raise
   ```

**Deliverables**:
- [ ] Scanner manager funcional
- [ ] Celery tasks configuradas
- [ ] Progress tracking implementado
- [ ] Error handling completo

---

#### 🎯 Task 1.3: Database Models (Day 4-5)
**Responsável**: Backend Dev  
**Estimativa**: 16h  

**Atividades**:
1. **Scan Models**
   ```python
   # app/models/scan.py
   from sqlalchemy import Column, String, DateTime, JSON, Enum, Integer, Float, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import relationship
   from enum import Enum as PyEnum
   
   class ScanStatus(PyEnum):
       PENDING = "pending"
       RUNNING = "running"
       COMPLETED = "completed"
       FAILED = "failed"
       CANCELLED = "cancelled"
   
   class Scan(Base):
       __tablename__ = "scans"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
       user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
       target_url = Column(String(500), nullable=False)
       scan_types = Column(JSON, nullable=False)  # ['owasp_zap', 'nmap', etc.]
       status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
       options = Column(JSON, default=dict)
       
       started_at = Column(DateTime)
       completed_at = Column(DateTime)
       duration_seconds = Column(Integer)
       
       celery_job_id = Column(String(255))
       error_message = Column(Text)
       
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       
       # Relationships
       user = relationship("User", back_populates="scans")
       vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
       reports = relationship("Report", back_populates="scan", cascade="all, delete-orphan")
       
       @property
       def vulnerability_summary(self):
           summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
           for vuln in self.vulnerabilities:
               summary[vuln.severity] += 1
           return summary
   
   class Vulnerability(Base):
       __tablename__ = "vulnerabilities"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
       scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
       
       vulnerability_id = Column(String(255), nullable=False)  # Internal ID
       cve_id = Column(String(50))  # CVE identifier if available
       
       severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
       cvss_score = Column(Float)
       
       title = Column(String(500), nullable=False)
       description = Column(Text, nullable=False)
       solution = Column(Text)
       
       affected_url = Column(String(500), nullable=False)
       evidence = Column(JSON, default=dict)
       
       # Remediation status
       status = Column(String(50), default='open')  # open, fixed, false_positive, accepted_risk
       remediation_notes = Column(Text)
       
       created_at = Column(DateTime, default=datetime.utcnow)
       
       # Relationships
       scan = relationship("Scan", back_populates="vulnerabilities")
   ```

2. **Report Models**
   ```python
   # app/models/report.py
   class ReportType(PyEnum):
       EXECUTIVE_SUMMARY = "executive_summary"
       TECHNICAL_DETAILED = "technical_detailed"
       COMPLIANCE_REPORT = "compliance_report"
       VULNERABILITY_LIST = "vulnerability_list"
   
   class Report(Base):
       __tablename__ = "reports"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
       scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
       
       report_type = Column(Enum(ReportType), nullable=False)
       format = Column(String(20), nullable=False)  # pdf, html, json, xlsx
       
       title = Column(String(255), nullable=False)
       description = Column(Text)
       
       file_path = Column(String(500))  # Path to generated file
       file_size = Column(Integer)  # Size in bytes
       
       status = Column(String(50), default='generating')  # generating, completed, failed
       
       generated_at = Column(DateTime)
       expires_at = Column(DateTime)  # Auto-cleanup old reports
       
       metadata = Column(JSON, default=dict)  # Report-specific settings
       
       created_at = Column(DateTime, default=datetime.utcnow)
       
       # Relationships
       scan = relationship("Scan", back_populates="reports")
   ```

**Deliverables**:
- [ ] Database models completos
- [ ] Migrations criadas
- [ ] Relationships configuradas
- [ ] Indexes otimizados

### Week 2: API e Interface

#### 🎯 Task 2.1: Scanner API (Day 6-8)
**Responsável**: Backend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **Scan Endpoints**
   ```python
   # app/api/v1/scanner.py
   from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
   from fastapi.security import HTTPBearer
   from app.services.scanner_service import ScannerService
   from app.schemas.scan import ScanCreateRequest, ScanResponse
   
   router = APIRouter(prefix="/scanner", tags=["scanner"])
   security = HTTPBearer()
   
   @router.post("/scan", response_model=ScanResponse)
   async def start_scan(
       scan_request: ScanCreateRequest,
       current_user: User = Depends(get_current_user),
       scanner_service: ScannerService = Depends()
   ):
       """Iniciar um novo scan de vulnerabilidades"""
       try:
           # Validate URL
           if not scan_request.target_url.startswith(('http://', 'https://')):
               raise HTTPException(status_code=400, detail="URL deve começar com http:// ou https://")
           
           # Check user limits
           user_scans_today = await scanner_service.get_user_scans_count_today(current_user.id)
           if user_scans_today >= current_user.daily_scan_limit:
               raise HTTPException(status_code=429, detail="Limite diário de scans atingido")
           
           # Start scan
           scan_id = await scanner_service.start_scan(
               user_id=current_user.id,
               target_url=scan_request.target_url,
               scan_types=scan_request.scan_types,
               options=scan_request.options
           )
           
           return ScanResponse(
               scan_id=scan_id,
               status="pending",
               message="Scan iniciado com sucesso"
           )
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=f"Erro ao iniciar scan: {str(e)}")
   
   @router.get("/scan/{scan_id}/progress")
   async def get_scan_progress(
       scan_id: str,
       current_user: User = Depends(get_current_user),
       scanner_service: ScannerService = Depends()
   ):
       """Obter progresso do scan"""
       scan = await scanner_service.get_scan(scan_id)
       
       if not scan or scan.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Scan não encontrado")
       
       progress = await scanner_service.get_scan_progress(scan_id)
       return progress
   
   @router.get("/scan/{scan_id}/results")
   async def get_scan_results(
       scan_id: str,
       current_user: User = Depends(get_current_user),
       scanner_service: ScannerService = Depends()
   ):
       """Obter resultados do scan"""
       scan = await scanner_service.get_scan(scan_id)
       
       if not scan or scan.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Scan não encontrado")
       
       if scan.status != ScanStatus.COMPLETED:
           raise HTTPException(status_code=400, detail="Scan ainda não completado")
       
       results = await scanner_service.get_scan_results(scan_id)
       return results
   
   @router.get("/scans")
   async def list_user_scans(
       current_user: User = Depends(get_current_user),
       skip: int = 0,
       limit: int = 20,
       scanner_service: ScannerService = Depends()
   ):
       """Listar scans do usuário"""
       scans = await scanner_service.get_user_scans(
           user_id=current_user.id,
           skip=skip,
           limit=limit
       )
       return scans
   
   @router.delete("/scan/{scan_id}")
   async def cancel_scan(
       scan_id: str,
       current_user: User = Depends(get_current_user),
       scanner_service: ScannerService = Depends()
   ):
       """Cancelar scan em execução"""
       scan = await scanner_service.get_scan(scan_id)
       
       if not scan or scan.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Scan não encontrado")
       
       if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
           raise HTTPException(status_code=400, detail="Scan não pode ser cancelado")
       
       await scanner_service.cancel_scan(scan_id)
       return {"message": "Scan cancelado com sucesso"}
   ```

2. **WebSocket para Progress**
   ```python
   # app/api/websocket.py
   from fastapi import WebSocket, WebSocketDisconnect, Depends
   from app.core.websocket import ConnectionManager
   import json
   
   manager = ConnectionManager()
   
   @router.websocket("/scan/{scan_id}/progress")
   async def websocket_scan_progress(
       websocket: WebSocket,
       scan_id: str,
       token: str = Query(...)  # JWT token as query param
   ):
       # Authenticate user
       try:
           current_user = await get_current_user_from_token(token)
       except:
           await websocket.close(code=4001, reason="Authentication failed")
           return
       
       # Verify scan ownership
       scan = await ScannerService().get_scan(scan_id)
       if not scan or scan.user_id != current_user.id:
           await websocket.close(code=4004, reason="Scan not found")
           return
       
       await manager.connect(websocket, scan_id)
       
       try:
           while True:
               # Get current progress
               progress = await ScannerService().get_scan_progress(scan_id)
               
               # Send progress update
               await manager.send_personal_message(
                   json.dumps(progress), 
                   websocket
               )
               
               # Check if scan completed
               if progress.get('status') in ['completed', 'failed', 'cancelled']:
                   break
               
               await asyncio.sleep(2)  # Update every 2 seconds
               
       except WebSocketDisconnect:
           manager.disconnect(websocket, scan_id)
   ```

**Deliverables**:
- [ ] API endpoints completos
- [ ] WebSocket para progress
- [ ] Autenticação e autorização
- [ ] Rate limiting implementado

---

#### 🎯 Task 2.2: Scanner Frontend (Day 8-12)
**Responsável**: Frontend Dev  
**Estimativa**: 32h  

**Atividades**:
1. **Scanner Form Component**
   ```typescript
   // components/scanner/ScannerForm.tsx
   import { useState } from 'react';
   import { useRouter } from 'next/router';
   import { useMutation } from 'react-query';
   import { scannerApi } from '@/services/api';
   
   interface ScannerFormProps {
     onScanStarted: (scanId: string) => void;
   }
   
   export const ScannerForm: React.FC<ScannerFormProps> = ({ onScanStarted }) => {
     const [targetUrl, setTargetUrl] = useState('');
     const [scanTypes, setScanTypes] = useState<string[]>(['owasp_zap']);
     const [advancedOptions, setAdvancedOptions] = useState(false);
     
     const startScanMutation = useMutation(scannerApi.startScan, {
       onSuccess: (data) => {
         onScanStarted(data.scan_id);
       },
       onError: (error) => {
         console.error('Erro ao iniciar scan:', error);
       }
     });
   
     const handleSubmit = (e: React.FormEvent) => {
       e.preventDefault();
       
       if (!targetUrl) {
         alert('Por favor, insira uma URL válida');
         return;
       }
       
       startScanMutation.mutate({
         target_url: targetUrl,
         scan_types: scanTypes,
         options: {
           // Advanced options if needed
         }
       });
     };
   
     return (
       <Card className="max-w-2xl mx-auto">
         <CardHeader>
           <h2 className="text-2xl font-bold text-white">Novo Scan de Vulnerabilidades</h2>
           <p className="text-gray-400">Insira a URL do site que deseja analisar</p>
         </CardHeader>
         
         <CardContent>
           <form onSubmit={handleSubmit} className="space-y-6">
             {/* URL Input */}
             <div>
               <label className="block text-sm font-medium text-gray-300 mb-2">
                 URL do Target
               </label>
               <input
                 type="url"
                 value={targetUrl}
                 onChange={(e) => setTargetUrl(e.target.value)}
                 placeholder="https://exemplo.com"
                 className="w-full px-4 py-3 bg-dark-card border border-gray-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                 required
               />
               <p className="text-xs text-gray-500 mt-1">
                 A URL deve começar com http:// ou https://
               </p>
             </div>
   
             {/* Scan Types */}
             <div>
               <label className="block text-sm font-medium text-gray-300 mb-3">
                 Tipos de Scan
               </label>
               <div className="grid grid-cols-2 gap-3">
                 {[
                   { id: 'owasp_zap', label: 'Vulnerabilidades Web', description: 'XSS, SQLi, etc.' },
                   { id: 'nmap', label: 'Scan de Portas', description: 'Serviços expostos' },
                   { id: 'ssl_checker', label: 'Análise SSL/TLS', description: 'Certificados e criptografia' },
                   { id: 'web_crawler', label: 'Crawler Web', description: 'Estrutura do site' }
                 ].map((scanType) => (
                   <label key={scanType.id} className="flex items-start space-x-3 p-3 bg-dark-card rounded-lg cursor-pointer hover:bg-gray-700">
                     <input
                       type="checkbox"
                       checked={scanTypes.includes(scanType.id)}
                       onChange={(e) => {
                         if (e.target.checked) {
                           setScanTypes([...scanTypes, scanType.id]);
                         } else {
                           setScanTypes(scanTypes.filter(t => t !== scanType.id));
                         }
                       }}
                       className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                     />
                     <div>
                       <div className="text-sm font-medium text-white">{scanType.label}</div>
                       <div className="text-xs text-gray-400">{scanType.description}</div>
                     </div>
                   </label>
                 ))}
               </div>
             </div>
   
             {/* Advanced Options Toggle */}
             <div>
               <button
                 type="button"
                 onClick={() => setAdvancedOptions(!advancedOptions)}
                 className="text-blue-400 text-sm hover:underline"
               >
                 {advancedOptions ? 'Ocultar' : 'Mostrar'} opções avançadas
               </button>
             </div>
   
             {/* Advanced Options Panel */}
             {advancedOptions && (
               <div className="p-4 bg-gray-800 rounded-lg space-y-4">
                 <h4 className="text-white font-medium">Opções Avançadas</h4>
                 {/* Add advanced options here */}
               </div>
             )}
   
             {/* Submit Button */}
             <button
               type="submit"
               disabled={startScanMutation.isLoading || scanTypes.length === 0}
               className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-3 px-4 rounded-lg transition-colors"
             >
               {startScanMutation.isLoading ? (
                 <div className="flex items-center justify-center space-x-2">
                   <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                   <span>Iniciando Scan...</span>
                 </div>
               ) : (
                 'Iniciar Scan'
               )}
             </button>
           </form>
         </CardContent>
       </Card>
     );
   };
   ```

2. **Progress Tracking Component**
   ```typescript
   // components/scanner/ScanProgress.tsx
   import { useEffect, useState } from 'react';
   import { useWebSocket } from '@/hooks/useWebSocket';
   
   interface ScanProgressProps {
     scanId: string;
     onComplete: () => void;
   }
   
   export const ScanProgress: React.FC<ScanProgressProps> = ({ scanId, onComplete }) => {
     const [progress, setProgress] = useState(0);
     const [status, setStatus] = useState('pending');
     const [enginesProgress, setEnginesProgress] = useState<Record<string, number>>({});
     
     const { connect, disconnect, lastMessage } = useWebSocket(
       `ws://localhost:8000/api/v1/scan/${scanId}/progress`
     );
   
     useEffect(() => {
       connect();
       return () => disconnect();
     }, [scanId]);
   
     useEffect(() => {
       if (lastMessage) {
         const data = JSON.parse(lastMessage.data);
         setProgress(data.overall_progress);
         setStatus(data.status);
         setEnginesProgress(data.engines_progress || {});
         
         if (data.status === 'completed') {
           onComplete();
         }
       }
     }, [lastMessage]);
   
     const getStatusColor = (status: string) => {
       switch (status) {
         case 'pending': return 'text-yellow-400';
         case 'running': return 'text-blue-400';
         case 'completed': return 'text-green-400';
         case 'failed': return 'text-red-400';
         default: return 'text-gray-400';
       }
     };
   
     const getStatusText = (status: string) => {
       switch (status) {
         case 'pending': return 'Aguardando...';
         case 'running': return 'Executando...';
         case 'completed': return 'Concluído!';
         case 'failed': return 'Falhou';
         default: return 'Status desconhecido';
       }
     };
   
     return (
       <Card className="max-w-2xl mx-auto">
         <CardHeader>
           <div className="flex items-center justify-between">
             <h3 className="text-xl font-bold text-white">Progresso do Scan</h3>
             <span className={`text-sm font-medium ${getStatusColor(status)}`}>
               {getStatusText(status)}
             </span>
           </div>
         </CardHeader>
         
         <CardContent className="space-y-6">
           {/* Overall Progress */}
           <div>
             <div className="flex justify-between text-sm text-gray-300 mb-2">
               <span>Progresso Geral</span>
               <span>{Math.round(progress)}%</span>
             </div>
             <div className="w-full bg-gray-700 rounded-full h-3">
               <div
                 className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                 style={{ width: `${progress}%` }}
               ></div>
             </div>
           </div>
   
           {/* Engines Progress */}
           {Object.keys(enginesProgress).length > 0 && (
             <div>
               <h4 className="text-sm font-medium text-gray-300 mb-3">Detalhes por Scanner</h4>
               <div className="space-y-3">
                 {Object.entries(enginesProgress).map(([engine, engineProgress]) => (
                   <div key={engine}>
                     <div className="flex justify-between text-xs text-gray-400 mb-1">
                       <span className="capitalize">{engine.replace('_', ' ')}</span>
                       <span>{Math.round(engineProgress)}%</span>
                     </div>
                     <div className="w-full bg-gray-700 rounded-full h-2">
                       <div
                         className="bg-green-500 h-2 rounded-full transition-all duration-300"
                         style={{ width: `${engineProgress}%` }}
                       ></div>
                     </div>
                   </div>
                 ))}
               </div>
             </div>
           )}
   
           {/* Status Messages */}
           <div className="bg-dark-card p-4 rounded-lg">
             <div className="flex items-center space-x-2">
               {status === 'running' && (
                 <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
               )}
               <span className="text-sm text-gray-300">
                 {status === 'pending' && 'Preparando scanners...'}
                 {status === 'running' && 'Analisando vulnerabilidades...'}
                 {status === 'completed' && 'Scan concluído com sucesso!'}
                 {status === 'failed' && 'Ocorreu um erro durante o scan.'}
               </span>
             </div>
           </div>
         </CardContent>
       </Card>
     );
   };
   ```

**Deliverables**:
- [ ] Scanner form completo
- [ ] Progress tracking em tempo real
- [ ] WebSocket integration
- [ ] UX responsivo e intuitivo

### Week 3: Relatórios e PDF

#### 🎯 Task 3.1: PDF Report Generator (Day 13-16)
**Responsável**: Backend Dev  
**Estimativa**: 32h  

**Atividades**:
1. **PDF Generator Service**
   ```python
   # services/report_service.py
   from reportlab.lib.pagesizes import A4, letter
   from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
   from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
   from reportlab.lib.colors import HexColor
   from reportlab.lib.units import inch
   import matplotlib.pyplot as plt
   import io
   import base64
   
   class PDFReportGenerator:
       def __init__(self):
           self.styles = getSampleStyleSheet()
           self.setup_custom_styles()
       
       def setup_custom_styles(self):
           # Custom styles for ScanIA branding
           self.styles.add(ParagraphStyle(
               name='ScanIATitle',
               parent=self.styles['Title'],
               fontSize=24,
               textColor=HexColor('#2563eb'),
               spaceAfter=30,
               alignment=1  # Center
           ))
           
           self.styles.add(ParagraphStyle(
               name='VulnTitle',
               parent=self.styles['Heading2'],
               fontSize=14,
               textColor=HexColor('#dc2626'),
               spaceBefore=15,
               spaceAfter=10
           ))
       
       async def generate_executive_summary(self, scan_id: str, output_path: str) -> str:
           scan = await Scan.get_with_results(scan_id)
           if not scan:
               raise ReportException("Scan not found")
           
           doc = SimpleDocTemplate(output_path, pagesize=A4)
           story = []
           
           # Title Page
           story.append(Paragraph("ScanIA - Relatório Executivo", self.styles['ScanIATitle']))
           story.append(Spacer(1, 20))
           
           # Scan Information
           scan_info = [
               ['Target URL:', scan.target_url],
               ['Data do Scan:', scan.started_at.strftime('%d/%m/%Y %H:%M')],
               ['Duração:', f"{scan.duration_seconds}s"],
               ['Status:', scan.status.value.title()]
           ]
           
           scan_table = Table(scan_info, colWidths=[2*inch, 4*inch])
           scan_table.setStyle(TableStyle([
               ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
               ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
               ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
               ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
               ('FONTSIZE', (0, 0), (-1, -1), 10),
               ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
           ]))
           
           story.append(scan_table)
           story.append(Spacer(1, 30))
           
           # Executive Summary
           story.append(Paragraph("Resumo Executivo", self.styles['Heading1']))
           
           summary = scan.vulnerability_summary
           total_vulns = sum(summary.values())
           
           if total_vulns == 0:
               story.append(Paragraph(
                   "Parabéns! Nenhuma vulnerabilidade foi identificada durante este scan.",
                   self.styles['Normal']
               ))
           else:
               story.append(Paragraph(
                   f"Este relatório apresenta os resultados da análise de segurança realizada em {scan.target_url}. "
                   f"Foram identificadas {total_vulns} vulnerabilidades, sendo {summary['critical']} críticas, "
                   f"{summary['high']} altas, {summary['medium']} médias e {summary['low']} baixas.",
                   self.styles['Normal']
               ))
           
           story.append(Spacer(1, 20))
           
           # Vulnerability Chart
           chart_path = await self.generate_vulnerability_chart(summary)
           if chart_path:
               story.append(Image(chart_path, width=400, height=300))
               story.append(Spacer(1, 20))
           
           # Risk Assessment
           story.append(Paragraph("Avaliação de Risco", self.styles['Heading2']))
           risk_level = self.calculate_risk_level(summary)
           story.append(Paragraph(f"Nível de Risco Geral: <b>{risk_level}</b>", self.styles['Normal']))
           
           # Top Vulnerabilities
           if scan.vulnerabilities:
               story.append(Spacer(1, 20))
               story.append(Paragraph("Principais Vulnerabilidades", self.styles['Heading2']))
               
               # Sort by severity and CVSS score
               top_vulns = sorted(
                   scan.vulnerabilities, 
                   key=lambda v: (self.severity_weight(v.severity), v.cvss_score or 0), 
                   reverse=True
               )[:5]
               
               for vuln in top_vulns:
                   story.append(Paragraph(f"• {vuln.title}", self.styles['VulnTitle']))
                   story.append(Paragraph(
                       f"Severidade: {vuln.severity.title()} | "
                       f"CVSS: {vuln.cvss_score or 'N/A'} | "
                       f"URL: {vuln.affected_url}",
                       self.styles['Normal']
                   ))
                   story.append(Spacer(1, 10))
           
           # Recommendations
           story.append(Spacer(1, 20))
           story.append(Paragraph("Recomendações", self.styles['Heading2']))
           recommendations = self.generate_recommendations(summary)
           for rec in recommendations:
               story.append(Paragraph(f"• {rec}", self.styles['Normal']))
           
           # Build PDF
           doc.build(story)
           return output_path
       
       async def generate_technical_report(self, scan_id: str, output_path: str) -> str:
           scan = await Scan.get_with_results(scan_id)
           if not scan:
               raise ReportException("Scan not found")
           
           doc = SimpleDocTemplate(output_path, pagesize=A4)
           story = []
           
           # Title
           story.append(Paragraph("ScanIA - Relatório Técnico Detalhado", self.styles['ScanIATitle']))
           story.append(Spacer(1, 30))
           
           # Detailed Vulnerabilities
           for vuln in scan.vulnerabilities:
               story.append(Paragraph(vuln.title, self.styles['VulnTitle']))
               story.append(Paragraph(f"<b>Severidade:</b> {vuln.severity.title()}", self.styles['Normal']))
               story.append(Paragraph(f"<b>CVSS Score:</b> {vuln.cvss_score or 'N/A'}", self.styles['Normal']))
               story.append(Paragraph(f"<b>URL Afetada:</b> {vuln.affected_url}", self.styles['Normal']))
               
               if vuln.cve_id:
                   story.append(Paragraph(f"<b>CVE ID:</b> {vuln.cve_id}", self.styles['Normal']))
               
               story.append(Spacer(1, 10))
               story.append(Paragraph("<b>Descrição:</b>", self.styles['Normal']))
               story.append(Paragraph(vuln.description, self.styles['Normal']))
               
               story.append(Spacer(1, 10))
               story.append(Paragraph("<b>Solução:</b>", self.styles['Normal']))
               story.append(Paragraph(vuln.solution or "Solução não disponível", self.styles['Normal']))
               
               if vuln.evidence:
                   story.append(Spacer(1, 10))
                   story.append(Paragraph("<b>Evidências:</b>", self.styles['Normal']))
                   for key, value in vuln.evidence.items():
                       if value:
                           story.append(Paragraph(f"• {key}: {value}", self.styles['Normal']))
               
               story.append(Spacer(1, 30))
           
           doc.build(story)
           return output_path
       
       async def generate_vulnerability_chart(self, summary: dict) -> str:
           if sum(summary.values()) == 0:
               return None
           
           # Create pie chart
           fig, ax = plt.subplots(figsize=(8, 6))
           
           labels = []
           sizes = []
           colors = []
           
           severity_colors = {
               'critical': '#dc2626',
               'high': '#ea580c',
               'medium': '#d97706',
               'low': '#65a30d',
               'info': '#0369a1'
           }
           
           for severity, count in summary.items():
               if count > 0:
                   labels.append(f"{severity.title()} ({count})")
                   sizes.append(count)
                   colors.append(severity_colors.get(severity, '#6b7280'))
           
           ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
           ax.set_title('Distribuição de Vulnerabilidades por Severidade', fontsize=14, fontweight='bold')
           
           # Save to temporary file
           chart_path = f"/tmp/vuln_chart_{uuid4()}.png"
           plt.savefig(chart_path, dpi=300, bbox_inches='tight')
           plt.close()
           
           return chart_path
   ```

**Deliverables**:
- [ ] PDF generator completo
- [ ] Templates de relatório
- [ ] Gráficos e visualizações
- [ ] Relatórios executivo e técnico

---

#### 🎯 Task 3.2: Report API (Day 15-17)
**Responsável**: Backend Dev  
**Estimativa**: 20h  

**Atividades**:
1. **Report Endpoints**
   ```python
   # app/api/v1/reports.py
   from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
   from fastapi.responses import FileResponse
   from app.services.report_service import ReportService
   
   router = APIRouter(prefix="/reports", tags=["reports"])
   
   @router.post("/generate/{scan_id}")
   async def generate_report(
       scan_id: str,
       report_type: str,
       format: str = "pdf",
       background_tasks: BackgroundTasks,
       current_user: User = Depends(get_current_user),
       report_service: ReportService = Depends()
   ):
       """Gerar relatório para um scan"""
       # Verify scan ownership
       scan = await report_service.get_scan(scan_id)
       if not scan or scan.user_id != current_user.id:
           raise HTTPException(status_code=404, detail="Scan não encontrado")
       
       if scan.status != ScanStatus.COMPLETED:
           raise HTTPException(status_code=400, detail="Scan deve estar completo")
       
       # Generate report in background
       report_id = await report_service.create_report_job(
           scan_id=scan_id,
           report_type=report_type,
           format=format,
           user_id=current_user.id
       )
       
       background_tasks.add_task(
           report_service.generate_report_async,
           report_id
       )
       
       return {
           "report_id": report_id,
           "status": "generating",
           "message": "Relatório sendo gerado"
       }
   
   @router.get("/{report_id}/status")
   async def get_report_status(
       report_id: str,
       current_user: User = Depends(get_current_user),
       report_service: ReportService = Depends()
   ):
       """Status da geração do relatório"""
       report = await report_service.get_report(report_id)
       if not report:
           raise HTTPException(status_code=404, detail="Relatório não encontrado")
       
       # Verify ownership through scan
       scan = await report_service.get_scan(report.scan_id)
       if scan.user_id != current_user.id:
           raise HTTPException(status_code=403, detail="Acesso negado")
       
       return {
           "report_id": report_id,
           "status": report.status,
           "progress": report.progress,
           "file_size": report.file_size,
           "generated_at": report.generated_at
       }
   
   @router.get("/{report_id}/download")
   async def download_report(
       report_id: str,
       current_user: User = Depends(get_current_user),
       report_service: ReportService = Depends()
   ):
       """Download do relatório gerado"""
       report = await report_service.get_report(report_id)
       if not report:
           raise HTTPException(status_code=404, detail="Relatório não encontrado")
       
       if report.status != "completed":
           raise HTTPException(status_code=400, detail="Relatório ainda não está pronto")
       
       # Verify ownership
       scan = await report_service.get_scan(report.scan_id)
       if scan.user_id != current_user.id:
           raise HTTPException(status_code=403, detail="Acesso negado")
       
       # Return file
       return FileResponse(
           path=report.file_path,
           filename=f"scania_report_{report.scan_id}_{report.report_type}.{report.format}",
           media_type='application/pdf' if report.format == 'pdf' else 'application/octet-stream'
       )
   ```

**Deliverables**:
- [ ] API de relatórios funcional
- [ ] Download de arquivos seguro
- [ ] Background tasks para geração
- [ ] Status tracking dos relatórios

## 🧪 Testes do Sprint

### Unit Tests
```python
# tests/test_scanner.py
import pytest
from unittest.mock import Mock, patch
from scanner.engines.owasp_zap import OWASPZapScanner

@pytest.mark.asyncio
async def test_owasp_zap_scanner():
    scanner = OWASPZapScanner("https://example.com", {})
    
    with patch.object(scanner, 'zap') as mock_zap:
        mock_zap.core.alerts.return_value = [
            {
                'alertRef': '1',
                'risk': 'High',
                'alert': 'XSS Vulnerability',
                'description': 'Cross-site scripting',
                'solution': 'Sanitize input',
                'url': 'https://example.com/page',
                'param': 'input',
                'attack': '<script>alert(1)</script>',
                'evidence': 'Evidence here'
            }
        ]
        
        results = await scanner.scan()
        assert len(results) == 1
        assert results[0].severity == 'high'
        assert 'XSS' in results[0].title

def test_pdf_generation():
    from services.report_service import PDFReportGenerator
    generator = PDFReportGenerator()
    
    # Test with mock data
    mock_scan = Mock()
    mock_scan.vulnerability_summary = {'critical': 1, 'high': 2, 'medium': 3, 'low': 1, 'info': 0}
    
    # Should not raise exception
    risk_level = generator.calculate_risk_level(mock_scan.vulnerability_summary)
    assert risk_level in ['Low', 'Medium', 'High', 'Critical']
```

### Integration Tests
```python
# tests/test_scanner_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_start_scan_endpoint(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/scanner/scan",
        json={
            "target_url": "https://httpbin.org",
            "scan_types": ["owasp_zap"],
            "options": {}
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "scan_id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_scan_progress_endpoint(client: AsyncClient, auth_headers, test_scan_id):
    response = await client.get(
        f"/api/v1/scanner/scan/{test_scan_id}/progress",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overall_progress" in data
    assert "status" in data
```

## 📊 Métricas de Sucesso

### Funcionais
- [ ] **Scanner Integration**: OWASP ZAP funciona corretamente
- [ ] **Progress Tracking**: WebSocket updates em tempo real
- [ ] **PDF Generation**: Relatórios gerados sem erro
- [ ] **File Downloads**: Downloads funcionam corretamente

### Performance  
- [ ] **Scan Duration**: < 5 minutos para sites básicos
- [ ] **PDF Generation**: < 30 segundos
- [ ] **API Response**: < 500ms para endpoints
- [ ] **WebSocket Latency**: < 100ms

### Qualidade
- [ ] **Error Handling**: Falhas são tratadas elegantemente
- [ ] **Data Persistence**: Resultados salvos corretamente
- [ ] **Security**: Acesso controlado por usuário
- [ ] **Reliability**: Sistema funciona sob carga

## 🚨 Riscos Identificados

### Alto Risco
1. **OWASP ZAP Instability**
   - *Mitigação*: Fallback para outros scanners
   - *Plano B*: Implementar scanner próprio básico

2. **PDF Generation Memory**
   - *Mitigação*: Stream processing + cleanup
   - *Plano B*: HTML reports como alternativa

### Médio Risco
1. **WebSocket Connections**
   - *Mitigação*: Reconnection logic + polling fallback
   - *Plano B*: Polling API apenas

---

**Sprint 2 estabelece o core funcional do ScanIA. Sucesso aqui determina viabilidade da plataforma.**