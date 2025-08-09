# Sprint 3: Dashboard e Visualizações

**Duração**: 2 semanas  
**Objetivo**: Criar dashboards interativos e visualizações de dados de segurança  
**Prioridade**: 🟡 Alta  

## 🎯 Objetivos do Sprint

### Principais Entregáveis
- 📊 Dashboard principal com métricas de segurança
- 📈 Gráficos e visualizações interativas
- 🎨 Interface responsiva e profissional
- 📱 Compatibilidade mobile/tablet
- 🔍 Filtros e período de tempo
- 📋 Histórico de scans detalhado
- 🚨 Alertas visuais para vulnerabilidades críticas

### Critérios de Aceitação
- [ ] Dashboard carrega métricas em < 2 segundos
- [ ] Gráficos são interativos e responsivos
- [ ] Filtros funcionam corretamente
- [ ] Interface funciona em mobile
- [ ] Dados são atualizados em tempo real
- [ ] Export de gráficos para PNG/PDF
- [ ] Alertas visuais para riscos altos

## 🏗️ Arquitetura do Sprint

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND DASHBOARD                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   OVERVIEW      │  │   ANALYTICS     │  │   HISTORY   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Total Scans   │  │ • Trend Charts  │  │ • Scan List │ │
│  │ • Active Vulns  │  │ • Risk Matrix   │  │ • Timeline  │ │
│  │ • Risk Score    │  │ • Comparisons   │  │ • Filters   │ │
│  │ • Last Activity │  │ • Predictions   │  │ • Export    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   REAL-TIME     │  │  VULNERABILITIES│  │   REPORTS   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Live Scans    │  │ • Vuln Details  │  │ • Generated │ │
│  │ • Progress Bars │  │ • Severity Map  │  │ • Scheduled │ │
│  │ • Notifications │  │ • CVSS Scores   │  │ • Downloads │ │
│  │ • Status Feed   │  │ • Remediation   │  │ • Templates │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND ANALYTICS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   DATA AGGREG   │  │   CALCULATIONS  │  │   CACHING   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • SQL Queries   │  │ • Risk Scores   │  │ • Redis     │ │
│  │ • Data Mining   │  │ • Trends        │  │ • ETL Cache │ │
│  │ • Time Series   │  │ • Predictions   │  │ • Query Opt │ │
│  │ • Grouping      │  │ • Comparisons   │  │ • Real-time │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                           │
├─────────────────────────────────────────────────────────────┤
│ • PostgreSQL (Scans, Vulns, Users)                         │
│ • Redis (Cache, Real-time data)                            │
│ • External APIs (CVE, Threat Intel)                        │
│ • File Storage (Reports, Screenshots)                      │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Tasks Detalhadas

### Week 1: Backend Analytics e APIs

#### 🎯 Task 1.1: Analytics Service (Day 1-3)
**Responsável**: Backend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **Dashboard Analytics Service**
   ```python
   # services/analytics_service.py
   from typing import Dict, List, Optional, Any
   from datetime import datetime, timedelta
   from sqlalchemy import func, and_, or_
   from app.models import Scan, Vulnerability, User
   from app.core.database import get_db_session
   import pandas as pd
   
   class AnalyticsService:
       def __init__(self):
           self.db = get_db_session()
       
       async def get_dashboard_overview(
           self, 
           user_id: str, 
           days: int = 30
       ) -> Dict[str, Any]:
           """Métricas gerais do dashboard"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           # Total scans
           total_scans = await self.db.execute(
               "SELECT COUNT(*) FROM scans WHERE user_id = %s AND created_at >= %s",
               (user_id, start_date)
           )
           
           # Active vulnerabilities
           active_vulns = await self.db.execute(
               """
               SELECT COUNT(*) FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s 
               AND v.status = 'open'
               AND s.created_at >= %s
               """,
               (user_id, start_date)
           )
           
           # Risk score calculation
           risk_score = await self.calculate_risk_score(user_id, days)
           
           # Recent activity
           recent_scans = await self.get_recent_scans(user_id, limit=5)
           
           # Vulnerability breakdown
           vuln_breakdown = await self.get_vulnerability_breakdown(user_id, days)
           
           # Trend data
           scan_trend = await self.get_scan_trend(user_id, days)
           vulnerability_trend = await self.get_vulnerability_trend(user_id, days)
           
           return {
               'overview': {
                   'total_scans': total_scans,
                   'active_vulnerabilities': active_vulns,
                   'risk_score': risk_score,
                   'period_days': days,
                   'last_scan': recent_scans[0] if recent_scans else None,
                   'improvement_percentage': await self.calculate_improvement(user_id, days)
               },
               'vulnerability_breakdown': vuln_breakdown,
               'recent_activity': recent_scans,
               'trends': {
                   'scans': scan_trend,
                   'vulnerabilities': vulnerability_trend
               }
           }
       
       async def calculate_risk_score(self, user_id: str, days: int) -> float:
           """Calcular score de risco baseado em vulnerabilidades"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           # Peso por severidade
           severity_weights = {
               'critical': 10.0,
               'high': 7.5,
               'medium': 5.0,
               'low': 2.5,
               'info': 1.0
           }
           
           query = """
               SELECT v.severity, COUNT(*) as count
               FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s 
               AND s.created_at >= %s
               AND v.status = 'open'
               GROUP BY v.severity
           """
           
           results = await self.db.execute(query, (user_id, start_date))
           
           total_score = 0
           total_vulns = 0
           
           for row in results:
               severity = row['severity']
               count = row['count']
               weight = severity_weights.get(severity, 1.0)
               total_score += count * weight
               total_vulns += count
           
           if total_vulns == 0:
               return 0.0
           
           # Normalizar para 0-100
           avg_score = total_score / total_vulns
           normalized_score = min(100, (avg_score / 10.0) * 100)
           
           return round(normalized_score, 1)
       
       async def get_vulnerability_breakdown(self, user_id: str, days: int) -> Dict[str, int]:
           """Breakdown de vulnerabilidades por severidade"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           query = """
               SELECT v.severity, COUNT(*) as count
               FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s 
               AND s.created_at >= %s
               GROUP BY v.severity
           """
           
           results = await self.db.execute(query, (user_id, start_date))
           
           breakdown = {
               'critical': 0,
               'high': 0,
               'medium': 0,
               'low': 0,
               'info': 0
           }
           
           for row in results:
               breakdown[row['severity']] = row['count']
           
           return breakdown
       
       async def get_scan_trend(self, user_id: str, days: int) -> List[Dict[str, Any]]:
           """Tendência de scans ao longo do tempo"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           # Gerar intervalos de tempo (por dia se <= 30 dias, por semana se > 30)
           interval = 'day' if days <= 30 else 'week'
           
           query = f"""
               SELECT 
                   DATE_TRUNC('{interval}', created_at) as period,
                   COUNT(*) as scan_count,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                   COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
               FROM scans 
               WHERE user_id = %s 
               AND created_at >= %s
               GROUP BY DATE_TRUNC('{interval}', created_at)
               ORDER BY period
           """
           
           results = await self.db.execute(query, (user_id, start_date))
           
           trend_data = []
           for row in results:
               trend_data.append({
                   'period': row['period'].isoformat(),
                   'total_scans': row['scan_count'],
                   'completed_scans': row['completed_count'],
                   'failed_scans': row['failed_count'],
                   'success_rate': (row['completed_count'] / row['scan_count'] * 100) if row['scan_count'] > 0 else 0
               })
           
           return trend_data
       
       async def get_vulnerability_trend(self, user_id: str, days: int) -> List[Dict[str, Any]]:
           """Tendência de vulnerabilidades ao longo do tempo"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           interval = 'day' if days <= 30 else 'week'
           
           query = f"""
               SELECT 
                   DATE_TRUNC('{interval}', s.created_at) as period,
                   v.severity,
                   COUNT(*) as vuln_count
               FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s 
               AND s.created_at >= %s
               GROUP BY DATE_TRUNC('{interval}', s.created_at), v.severity
               ORDER BY period, v.severity
           """
           
           results = await self.db.execute(query, (user_id, start_date))
           
           # Organizar dados por período
           trend_data = {}
           for row in results:
               period = row['period'].isoformat()
               if period not in trend_data:
                   trend_data[period] = {
                       'period': period,
                       'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0,
                       'total': 0
                   }
               
               severity = row['severity']
               count = row['vuln_count']
               trend_data[period][severity] = count
               trend_data[period]['total'] += count
           
           return list(trend_data.values())
       
       async def get_top_vulnerabilities(
           self, 
           user_id: str, 
           days: int = 30, 
           limit: int = 10
       ) -> List[Dict[str, Any]]:
           """Top vulnerabilidades mais comuns"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           query = """
               SELECT 
                   v.title,
                   v.severity,
                   COUNT(*) as occurrence_count,
                   AVG(v.cvss_score) as avg_cvss,
                   COUNT(DISTINCT s.target_url) as affected_targets
               FROM vulnerabilities v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.user_id = %s 
               AND s.created_at >= %s
               GROUP BY v.title, v.severity
               ORDER BY occurrence_count DESC, avg_cvss DESC
               LIMIT %s
           """
           
           results = await self.db.execute(query, (user_id, start_date, limit))
           
           top_vulns = []
           for row in results:
               top_vulns.append({
                   'title': row['title'],
                   'severity': row['severity'],
                   'occurrence_count': row['occurrence_count'],
                   'average_cvss': round(row['avg_cvss'] or 0, 1),
                   'affected_targets': row['affected_targets']
               })
           
           return top_vulns
       
       async def get_target_risk_matrix(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
           """Matriz de risco por target"""
           end_date = datetime.utcnow()
           start_date = end_date - timedelta(days=days)
           
           query = """
               SELECT 
                   s.target_url,
                   COUNT(*) as total_scans,
                   COUNT(CASE WHEN v.severity = 'critical' THEN 1 END) as critical_count,
                   COUNT(CASE WHEN v.severity = 'high' THEN 1 END) as high_count,
                   COUNT(CASE WHEN v.severity = 'medium' THEN 1 END) as medium_count,
                   COUNT(CASE WHEN v.severity = 'low' THEN 1 END) as low_count,
                   AVG(v.cvss_score) as avg_cvss,
                   MAX(s.created_at) as last_scan
               FROM scans s
               LEFT JOIN vulnerabilities v ON s.id = v.scan_id
               WHERE s.user_id = %s 
               AND s.created_at >= %s
               GROUP BY s.target_url
               ORDER BY critical_count DESC, high_count DESC, avg_cvss DESC
           """
           
           results = await self.db.execute(query, (user_id, start_date))
           
           risk_matrix = []
           for row in results:
               # Calcular risk score para este target
               risk_score = (
                   (row['critical_count'] or 0) * 10 +
                   (row['high_count'] or 0) * 7.5 +
                   (row['medium_count'] or 0) * 5 +
                   (row['low_count'] or 0) * 2.5
               )
               
               risk_matrix.append({
                   'target_url': row['target_url'],
                   'total_scans': row['total_scans'],
                   'vulnerabilities': {
                       'critical': row['critical_count'] or 0,
                       'high': row['high_count'] or 0,
                       'medium': row['medium_count'] or 0,
                       'low': row['low_count'] or 0
                   },
                   'risk_score': round(risk_score, 1),
                   'average_cvss': round(row['avg_cvss'] or 0, 1),
                   'last_scan': row['last_scan'].isoformat() if row['last_scan'] else None
               })
           
           return risk_matrix
   ```

2. **Dashboard API Endpoints**
   ```python
   # app/api/v1/dashboard.py
   from fastapi import APIRouter, Depends, Query
   from typing import Optional
   from app.services.analytics_service import AnalyticsService
   from app.core.auth import get_current_user
   
   router = APIRouter(prefix="/dashboard", tags=["dashboard"])
   
   @router.get("/overview")
   async def get_dashboard_overview(
       days: int = Query(30, ge=1, le=365, description="Período em dias"),
       current_user: User = Depends(get_current_user),
       analytics: AnalyticsService = Depends()
   ):
       """Obter dados gerais do dashboard"""
       return await analytics.get_dashboard_overview(
           user_id=current_user.id,
           days=days
       )
   
   @router.get("/vulnerabilities/top")
   async def get_top_vulnerabilities(
       days: int = Query(30, ge=1, le=365),
       limit: int = Query(10, ge=1, le=50),
       current_user: User = Depends(get_current_user),
       analytics: AnalyticsService = Depends()
   ):
       """Top vulnerabilidades mais comuns"""
       return await analytics.get_top_vulnerabilities(
           user_id=current_user.id,
           days=days,
           limit=limit
       )
   
   @router.get("/targets/risk-matrix")
   async def get_target_risk_matrix(
       days: int = Query(30, ge=1, le=365),
       current_user: User = Depends(get_current_user),
       analytics: AnalyticsService = Depends()
   ):
       """Matriz de risco por target"""
       return await analytics.get_target_risk_matrix(
           user_id=current_user.id,
           days=days
       )
   
   @router.get("/real-time/stats")
   async def get_realtime_stats(
       current_user: User = Depends(get_current_user),
       analytics: AnalyticsService = Depends()
   ):
       """Estatísticas em tempo real"""
       return await analytics.get_realtime_stats(current_user.id)
   ```

**Deliverables**:
- [ ] Analytics service completo
- [ ] Dashboard API endpoints
- [ ] Cálculos de métricas de segurança
- [ ] Queries otimizadas para performance

---

#### 🎯 Task 1.2: Cache e Otimização (Day 3-4)
**Responsável**: Backend Dev  
**Estimativa**: 16h  

**Atividades**:
1. **Redis Cache Strategy**
   ```python
   # services/cache_service.py
   import redis
   import json
   from typing import Any, Optional
   from datetime import timedelta
   
   class CacheService:
       def __init__(self):
           self.redis = redis.Redis(
               host=settings.REDIS_HOST,
               port=settings.REDIS_PORT,
               db=settings.REDIS_DB,
               decode_responses=True
           )
       
       async def get_dashboard_cache(
           self, 
           user_id: str, 
           cache_key: str
       ) -> Optional[Dict[str, Any]]:
           """Obter dados em cache do dashboard"""
           try:
               cached_data = self.redis.get(f"dashboard:{user_id}:{cache_key}")
               if cached_data:
                   return json.loads(cached_data)
               return None
           except Exception as e:
               logger.error(f"Cache get error: {e}")
               return None
       
       async def set_dashboard_cache(
           self, 
           user_id: str, 
           cache_key: str, 
           data: Dict[str, Any],
           ttl_seconds: int = 300  # 5 minutes default
       ):
           """Armazenar dados em cache"""
           try:
               self.redis.setex(
                   f"dashboard:{user_id}:{cache_key}",
                   ttl_seconds,
                   json.dumps(data, default=str)
               )
           except Exception as e:
               logger.error(f"Cache set error: {e}")
       
       async def invalidate_user_cache(self, user_id: str):
           """Invalidar todo cache do usuário"""
           try:
               pattern = f"dashboard:{user_id}:*"
               keys = self.redis.keys(pattern)
               if keys:
                   self.redis.delete(*keys)
           except Exception as e:
               logger.error(f"Cache invalidation error: {e}")
       
       # Cache específico para diferentes tipos de dados
       async def cache_overview_data(self, user_id: str, data: Dict[str, Any]):
           await self.set_dashboard_cache(user_id, "overview", data, 300)  # 5 min
       
       async def cache_trends_data(self, user_id: str, data: Dict[str, Any]):
           await self.set_dashboard_cache(user_id, "trends", data, 600)  # 10 min
       
       async def cache_vulnerability_data(self, user_id: str, data: Dict[str, Any]):
           await self.set_dashboard_cache(user_id, "vulnerabilities", data, 180)  # 3 min
   ```

2. **Database Query Optimization**
   ```python
   # services/analytics_service.py (otimizado)
   class OptimizedAnalyticsService(AnalyticsService):
       
       async def get_dashboard_overview_cached(
           self, 
           user_id: str, 
           days: int = 30
       ) -> Dict[str, Any]:
           """Versão com cache do dashboard overview"""
           cache_key = f"overview_{days}"
           
           # Tentar obter do cache primeiro
           cached_data = await self.cache.get_dashboard_cache(user_id, cache_key)
           if cached_data:
               return cached_data
           
           # Se não estiver em cache, calcular
           data = await super().get_dashboard_overview(user_id, days)
           
           # Armazenar em cache
           await self.cache.set_dashboard_cache(user_id, cache_key, data, 300)
           
           return data
       
       async def get_aggregated_stats(self, user_id: str) -> Dict[str, Any]:
           """Usar views materializadas para performance"""
           # Criar view materializada se não existir
           await self._ensure_materialized_views()
           
           query = """
               SELECT * FROM user_security_stats_mv 
               WHERE user_id = %s
           """
           
           result = await self.db.execute(query, (user_id,))
           return result[0] if result else {}
       
       async def _ensure_materialized_views(self):
           """Criar/atualizar views materializadas"""
           create_view_sql = """
               CREATE MATERIALIZED VIEW IF NOT EXISTS user_security_stats_mv AS
               SELECT 
                   s.user_id,
                   COUNT(DISTINCT s.id) as total_scans,
                   COUNT(DISTINCT v.id) as total_vulnerabilities,
                   COUNT(DISTINCT CASE WHEN v.severity = 'critical' THEN v.id END) as critical_vulns,
                   COUNT(DISTINCT CASE WHEN v.severity = 'high' THEN v.id END) as high_vulns,
                   COUNT(DISTINCT s.target_url) as unique_targets,
                   AVG(v.cvss_score) as avg_cvss_score,
                   MAX(s.created_at) as last_scan_date
               FROM scans s
               LEFT JOIN vulnerabilities v ON s.id = v.scan_id
               WHERE s.created_at >= NOW() - INTERVAL '90 days'
               GROUP BY s.user_id;
               
               CREATE UNIQUE INDEX IF NOT EXISTS user_security_stats_mv_user_id_idx 
               ON user_security_stats_mv (user_id);
           """
           
           await self.db.execute(create_view_sql)
   ```

**Deliverables**:
- [ ] Sistema de cache implementado
- [ ] Queries otimizadas
- [ ] Views materializadas criadas
- [ ] Invalidação inteligente de cache

### Week 2: Frontend Dashboard

#### 🎯 Task 2.1: Dashboard Components (Day 5-9)
**Responsável**: Frontend Dev  
**Estimativa**: 40h  

**Atividades**:
1. **Main Dashboard Layout**
   ```typescript
   // pages/dashboard/index.tsx
   import { useState, useEffect } from 'react';
   import { useQuery } from 'react-query';
   import { dashboardApi } from '@/services/api';
   import {
     StatsOverview,
     VulnerabilityChart,
     TrendChart,
     RecentActivity,
     RiskMatrix,
     TopVulnerabilities
   } from '@/components/dashboard';
   
   interface DashboardData {
     overview: {
       total_scans: number;
       active_vulnerabilities: number;
       risk_score: number;
       last_scan: any;
       improvement_percentage: number;
     };
     vulnerability_breakdown: Record<string, number>;
     trends: {
       scans: any[];
       vulnerabilities: any[];
     };
     recent_activity: any[];
   }
   
   export default function DashboardPage() {
     const [timeRange, setTimeRange] = useState(30);
     const [refreshInterval, setRefreshInterval] = useState(30000); // 30s
   
     const { data, isLoading, error, refetch } = useQuery<DashboardData>(
       ['dashboard', timeRange],
       () => dashboardApi.getOverview(timeRange),
       {
         refetchInterval: refreshInterval,
         refetchIntervalInBackground: true,
         staleTime: 5 * 60 * 1000, // 5 minutes
       }
     );
   
     useEffect(() => {
       const interval = setInterval(() => {
         refetch();
       }, refreshInterval);
   
       return () => clearInterval(interval);
     }, [refetch, refreshInterval]);
   
     if (isLoading) {
       return <DashboardSkeleton />;
     }
   
     if (error) {
       return <ErrorState onRetry={refetch} />;
     }
   
     return (
       <DashboardLayout>
         <div className="p-6 space-y-6">
           {/* Header com filtros */}
           <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
             <div>
               <h1 className="text-3xl font-bold text-white">Dashboard de Segurança</h1>
               <p className="text-gray-400 mt-1">
                 Visão geral da sua postura de segurança
               </p>
             </div>
             
             <div className="flex items-center gap-3">
               <TimeRangeSelector
                 value={timeRange}
                 onChange={setTimeRange}
                 options={[
                   { label: '7 dias', value: 7 },
                   { label: '30 dias', value: 30 },
                   { label: '90 dias', value: 90 },
                   { label: '1 ano', value: 365 }
                 ]}
               />
               
               <RefreshButton 
                 onRefresh={refetch}
                 isRefreshing={isLoading}
               />
             </div>
           </div>
   
           {/* Stats Overview - Cards principais */}
           <StatsOverview data={data.overview} />
   
           {/* Gráficos principais */}
           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
             <VulnerabilityChart 
               data={data.vulnerability_breakdown}
               className="lg:col-span-1"
             />
             
             <TrendChart 
               data={data.trends}
               timeRange={timeRange}
               className="lg:col-span-1"
             />
           </div>
   
           {/* Seção detalhada */}
           <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
             <RecentActivity 
               data={data.recent_activity}
               className="xl:col-span-1"
             />
             
             <TopVulnerabilitiesWidget 
               userId={data.user?.id}
               timeRange={timeRange}
               className="xl:col-span-2"
             />
           </div>
   
           {/* Risk Matrix */}
           <RiskMatrixSection 
             userId={data.user?.id}
             timeRange={timeRange}
           />
         </div>
       </DashboardLayout>
     );
   }
   ```

2. **Stats Overview Component**
   ```typescript
   // components/dashboard/StatsOverview.tsx
   import { TrendingUp, TrendingDown, Shield, AlertTriangle, Activity, CheckCircle } from 'lucide-react';
   
   interface StatsOverviewProps {
     data: {
       total_scans: number;
       active_vulnerabilities: number;
       risk_score: number;
       improvement_percentage: number;
       last_scan?: any;
     };
   }
   
   export const StatsOverview: React.FC<StatsOverviewProps> = ({ data }) => {
     const stats = [
       {
         title: 'Total de Scans',
         value: data.total_scans,
         icon: Activity,
         color: 'blue',
         change: null
       },
       {
         title: 'Vulnerabilidades Ativas',
         value: data.active_vulnerabilities,
         icon: AlertTriangle,
         color: data.active_vulnerabilities > 0 ? 'red' : 'green',
         change: null
       },
       {
         title: 'Score de Risco',
         value: `${data.risk_score}/100`,
         icon: Shield,
         color: data.risk_score > 70 ? 'red' : data.risk_score > 40 ? 'yellow' : 'green',
         change: null
       },
       {
         title: 'Melhoria no Período',
         value: `${data.improvement_percentage > 0 ? '+' : ''}${data.improvement_percentage}%`,
         icon: data.improvement_percentage >= 0 ? TrendingUp : TrendingDown,
         color: data.improvement_percentage >= 0 ? 'green' : 'red',
         change: data.improvement_percentage
       }
     ];
   
     const getColorClasses = (color: string) => {
       const colors = {
         blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
         green: 'text-green-400 bg-green-500/10 border-green-500/20',
         yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
         red: 'text-red-400 bg-red-500/10 border-red-500/20'
       };
       return colors[color] || colors.blue;
     };
   
     return (
       <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
         {stats.map((stat, index) => {
           const IconComponent = stat.icon;
           const colorClasses = getColorClasses(stat.color);
           
           return (
             <Card key={index} className="p-6 bg-dark-card border-gray-700">
               <div className="flex items-center justify-between">
                 <div>
                   <p className="text-gray-400 text-sm font-medium">{stat.title}</p>
                   <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                   
                   {stat.change !== null && (
                     <div className={`flex items-center mt-2 text-sm ${
                       stat.change >= 0 ? 'text-green-400' : 'text-red-400'
                     }`}>
                       <IconComponent size={16} className="mr-1" />
                       <span>{Math.abs(stat.change)}% vs período anterior</span>
                     </div>
                   )}
                 </div>
                 
                 <div className={`p-3 rounded-lg border ${colorClasses}`}>
                   <IconComponent size={24} />
                 </div>
               </div>
             </Card>
           );
         })}
       </div>
     );
   };
   ```

3. **Vulnerability Chart Component**
   ```typescript
   // components/dashboard/VulnerabilityChart.tsx
   import { Doughnut, Bar } from 'react-chartjs-2';
   import {
     Chart as ChartJS,
     ArcElement,
     CategoryScale,
     LinearScale,
     BarElement,
     Title,
     Tooltip,
     Legend,
   } from 'chart.js';
   
   ChartJS.register(
     ArcElement,
     CategoryScale,
     LinearScale,
     BarElement,
     Title,
     Tooltip,
     Legend
   );
   
   interface VulnerabilityChartProps {
     data: Record<string, number>;
     className?: string;
   }
   
   export const VulnerabilityChart: React.FC<VulnerabilityChartProps> = ({ 
     data, 
     className 
   }) => {
     const [chartType, setChartType] = useState<'doughnut' | 'bar'>('doughnut');
   
     const severityColors = {
       critical: '#dc2626',
       high: '#ea580c',
       medium: '#d97706',
       low: '#65a30d',
       info: '#0369a1'
     };
   
     const chartData = {
       labels: Object.keys(data).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
       datasets: [
         {
           data: Object.values(data),
           backgroundColor: Object.keys(data).map(key => severityColors[key]),
           borderColor: Object.keys(data).map(key => severityColors[key]),
           borderWidth: 2,
         },
       ],
     };
   
     const options = {
       responsive: true,
       maintainAspectRatio: false,
       plugins: {
         legend: {
           position: 'bottom' as const,
           labels: {
             color: '#f1f5f9',
             padding: 20,
             usePointStyle: true,
           },
         },
         tooltip: {
           backgroundColor: '#1e293b',
           titleColor: '#f1f5f9',
           bodyColor: '#cbd5e1',
           borderColor: '#475569',
           borderWidth: 1,
           callbacks: {
             label: function(context: any) {
               const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
               const percentage = ((context.parsed / total) * 100).toFixed(1);
               return `${context.label}: ${context.parsed} (${percentage}%)`;
             }
           }
         },
       },
       scales: chartType === 'bar' ? {
         y: {
           beginAtZero: true,
           grid: {
             color: '#374151',
           },
           ticks: {
             color: '#9ca3af',
           },
         },
         x: {
           grid: {
             color: '#374151',
           },
           ticks: {
             color: '#9ca3af',
           },
         },
       } : undefined,
     };
   
     const total = Object.values(data).reduce((sum, count) => sum + count, 0);
   
     return (
       <Card className={`p-6 bg-dark-card border-gray-700 ${className}`}>
         <div className="flex items-center justify-between mb-6">
           <div>
             <h3 className="text-lg font-semibold text-white">
               Distribuição de Vulnerabilidades
             </h3>
             <p className="text-sm text-gray-400">
               Total: {total} vulnerabilidades encontradas
             </p>
           </div>
           
           <div className="flex items-center gap-2">
             <button
               onClick={() => setChartType('doughnut')}
               className={`p-2 rounded-lg transition-colors ${
                 chartType === 'doughnut' 
                   ? 'bg-blue-600 text-white' 
                   : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
               }`}
             >
               Rosca
             </button>
             <button
               onClick={() => setChartType('bar')}
               className={`p-2 rounded-lg transition-colors ${
                 chartType === 'bar' 
                   ? 'bg-blue-600 text-white' 
                   : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
               }`}
             >
               Barras
             </button>
           </div>
         </div>
   
         <div className="h-80">
           {total > 0 ? (
             chartType === 'doughnut' ? (
               <Doughnut data={chartData} options={options} />
             ) : (
               <Bar data={chartData} options={options} />
             )
           ) : (
             <div className="flex items-center justify-center h-full">
               <div className="text-center">
                 <CheckCircle size={48} className="text-green-400 mx-auto mb-4" />
                 <p className="text-gray-400">Nenhuma vulnerabilidade encontrada</p>
                 <p className="text-sm text-gray-500">Excelente trabalho!</p>
               </div>
             </div>
           )}
         </div>
       </Card>
     );
   };
   ```

**Deliverables**:
- [ ] Dashboard layout responsivo
- [ ] Componentes de visualização
- [ ] Gráficos interativos
- [ ] Real-time updates

---

#### 🎯 Task 2.2: Advanced Charts (Day 9-12)
**Responsável**: Frontend Dev  
**Estimativa**: 24h  

**Atividades**:
1. **Trend Chart Component**
   ```typescript
   // components/dashboard/TrendChart.tsx
   import { Line } from 'react-chartjs-2';
   import {
     Chart as ChartJS,
     CategoryScale,
     LinearScale,
     PointElement,
     LineElement,
     Title,
     Tooltip,
     Legend,
     Filler
   } from 'chart.js';
   
   ChartJS.register(
     CategoryScale,
     LinearScale,
     PointElement,
     LineElement,
     Title,
     Tooltip,
     Legend,
     Filler
   );
   
   interface TrendChartProps {
     data: {
       scans: Array<{
         period: string;
         total_scans: number;
         completed_scans: number;
         failed_scans: number;
         success_rate: number;
       }>;
       vulnerabilities: Array<{
         period: string;
         critical: number;
         high: number;
         medium: number;
         low: number;
         info: number;
         total: number;
       }>;
     };
     timeRange: number;
     className?: string;
   }
   
   export const TrendChart: React.FC<TrendChartProps> = ({ 
     data, 
     timeRange, 
     className 
   }) => {
     const [activeTab, setActiveTab] = useState<'scans' | 'vulnerabilities'>('scans');
   
     const formatDate = (dateString: string) => {
       const date = new Date(dateString);
       return timeRange <= 30 
         ? date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
         : date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' });
     };
   
     const scanTrendData = {
       labels: data.scans.map(item => formatDate(item.period)),
       datasets: [
         {
           label: 'Scans Realizados',
           data: data.scans.map(item => item.total_scans),
           borderColor: '#3b82f6',
           backgroundColor: 'rgba(59, 130, 246, 0.1)',
           fill: true,
           tension: 0.4,
         },
         {
           label: 'Scans Completados',
           data: data.scans.map(item => item.completed_scans),
           borderColor: '#10b981',
           backgroundColor: 'rgba(16, 185, 129, 0.1)',
           fill: false,
           tension: 0.4,
         },
         {
           label: 'Scans Falharam',
           data: data.scans.map(item => item.failed_scans),
           borderColor: '#ef4444',
           backgroundColor: 'rgba(239, 68, 68, 0.1)',
           fill: false,
           tension: 0.4,
         }
       ],
     };
   
     const vulnTrendData = {
       labels: data.vulnerabilities.map(item => formatDate(item.period)),
       datasets: [
         {
           label: 'Críticas',
           data: data.vulnerabilities.map(item => item.critical),
           borderColor: '#dc2626',
           backgroundColor: 'rgba(220, 38, 38, 0.1)',
           fill: true,
           tension: 0.4,
         },
         {
           label: 'Altas',
           data: data.vulnerabilities.map(item => item.high),
           borderColor: '#ea580c',
           backgroundColor: 'rgba(234, 88, 12, 0.1)',
           fill: true,
           tension: 0.4,
         },
         {
           label: 'Médias',
           data: data.vulnerabilities.map(item => item.medium),
           borderColor: '#d97706',
           backgroundColor: 'rgba(217, 119, 6, 0.1)',
           fill: true,
           tension: 0.4,
         }
       ],
     };
   
     const options = {
       responsive: true,
       maintainAspectRatio: false,
       interaction: {
         mode: 'index' as const,
         intersect: false,
       },
       plugins: {
         legend: {
           position: 'top' as const,
           labels: {
             color: '#f1f5f9',
             padding: 20,
             usePointStyle: true,
           },
         },
         tooltip: {
           backgroundColor: '#1e293b',
           titleColor: '#f1f5f9',
           bodyColor: '#cbd5e1',
           borderColor: '#475569',
           borderWidth: 1,
         },
       },
       scales: {
         x: {
           grid: {
             color: '#374151',
           },
           ticks: {
             color: '#9ca3af',
           },
         },
         y: {
           beginAtZero: true,
           grid: {
             color: '#374151',
           },
           ticks: {
             color: '#9ca3af',
           },
         },
       },
     };
   
     return (
       <Card className={`p-6 bg-dark-card border-gray-700 ${className}`}>
         <div className="flex items-center justify-between mb-6">
           <h3 className="text-lg font-semibold text-white">
             Tendências ao Longo do Tempo
           </h3>
           
           <div className="flex bg-gray-800 rounded-lg p-1">
             <button
               onClick={() => setActiveTab('scans')}
               className={`px-3 py-1 rounded-md text-sm transition-colors ${
                 activeTab === 'scans'
                   ? 'bg-blue-600 text-white'
                   : 'text-gray-400 hover:text-white'
               }`}
             >
               Scans
             </button>
             <button
               onClick={() => setActiveTab('vulnerabilities')}
               className={`px-3 py-1 rounded-md text-sm transition-colors ${
                 activeTab === 'vulnerabilities'
                   ? 'bg-blue-600 text-white'
                   : 'text-gray-400 hover:text-white'
               }`}
             >
               Vulnerabilidades
             </button>
           </div>
         </div>
   
         <div className="h-80">
           <Line 
             data={activeTab === 'scans' ? scanTrendData : vulnTrendData} 
             options={options} 
           />
         </div>
       </Card>
     );
   };
   ```

2. **Risk Matrix Component**
   ```typescript
   // components/dashboard/RiskMatrix.tsx
   import { useQuery } from 'react-query';
   import { dashboardApi } from '@/services/api';
   import { ExternalLink, AlertTriangle } from 'lucide-react';
   
   interface RiskMatrixProps {
     userId: string;
     timeRange: number;
   }
   
   export const RiskMatrixSection: React.FC<RiskMatrixProps> = ({ userId, timeRange }) => {
     const { data: riskMatrix, isLoading } = useQuery(
       ['riskMatrix', userId, timeRange],
       () => dashboardApi.getTargetRiskMatrix(timeRange),
       {
         staleTime: 5 * 60 * 1000, // 5 minutes
       }
     );
   
     const getRiskColor = (riskScore: number) => {
       if (riskScore >= 80) return 'bg-red-500';
       if (riskScore >= 60) return 'bg-orange-500';
       if (riskScore >= 40) return 'bg-yellow-500';
       if (riskScore >= 20) return 'bg-blue-500';
       return 'bg-green-500';
     };
   
     const getRiskLabel = (riskScore: number) => {
       if (riskScore >= 80) return 'Crítico';
       if (riskScore >= 60) return 'Alto';
       if (riskScore >= 40) return 'Médio';
       if (riskScore >= 20) return 'Baixo';
       return 'Mínimo';
     };
   
     if (isLoading) {
       return <div className="animate-pulse bg-dark-card h-96 rounded-lg"></div>;
     }
   
     if (!riskMatrix || riskMatrix.length === 0) {
       return (
         <Card className="p-6 bg-dark-card border-gray-700">
           <h3 className="text-lg font-semibold text-white mb-4">Matriz de Risco por Target</h3>
           <div className="text-center py-8">
             <p className="text-gray-400">Nenhum target foi analisado no período selecionado</p>
           </div>
         </Card>
       );
     }
   
     return (
       <Card className="p-6 bg-dark-card border-gray-700">
         <div className="flex items-center justify-between mb-6">
           <h3 className="text-lg font-semibold text-white">Matriz de Risco por Target</h3>
           <p className="text-sm text-gray-400">
             {riskMatrix.length} targets analisados
           </p>
         </div>
   
         <div className="overflow-x-auto">
           <table className="w-full">
             <thead>
               <tr className="border-b border-gray-700">
                 <th className="text-left py-3 px-2 text-gray-300 font-medium">Target URL</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">Risk Score</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">Críticas</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">Altas</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">Médias</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">CVSS Médio</th>
                 <th className="text-center py-3 px-2 text-gray-300 font-medium">Último Scan</th>
               </tr>
             </thead>
             <tbody>
               {riskMatrix.map((target, index) => (
                 <tr key={index} className="border-b border-gray-800 hover:bg-gray-800/50">
                   <td className="py-4 px-2">
                     <div className="flex items-center gap-2">
                       <a
                         href={target.target_url}
                         target="_blank"
                         rel="noopener noreferrer"
                         className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
                       >
                         {target.target_url.replace(/^https?:\/\//, '').substring(0, 30)}
                         {target.target_url.replace(/^https?:\/\//, '').length > 30 && '...'}
                         <ExternalLink size={12} />
                       </a>
                     </div>
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     <div className="flex items-center justify-center gap-2">
                       <div className={`w-3 h-3 rounded-full ${getRiskColor(target.risk_score)}`}></div>
                       <span className="text-white font-medium">{target.risk_score}</span>
                       <span className="text-xs text-gray-400">
                         ({getRiskLabel(target.risk_score)})
                       </span>
                     </div>
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     {target.vulnerabilities.critical > 0 ? (
                       <span className="bg-red-500/20 text-red-400 px-2 py-1 rounded text-sm font-medium">
                         {target.vulnerabilities.critical}
                       </span>
                     ) : (
                       <span className="text-gray-500">0</span>
                     )}
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     {target.vulnerabilities.high > 0 ? (
                       <span className="bg-orange-500/20 text-orange-400 px-2 py-1 rounded text-sm font-medium">
                         {target.vulnerabilities.high}
                       </span>
                     ) : (
                       <span className="text-gray-500">0</span>
                     )}
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     {target.vulnerabilities.medium > 0 ? (
                       <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded text-sm font-medium">
                         {target.vulnerabilities.medium}
                       </span>
                     ) : (
                       <span className="text-gray-500">0</span>
                     )}
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     <span className="text-white font-mono text-sm">
                       {target.average_cvss}
                     </span>
                   </td>
                   
                   <td className="py-4 px-2 text-center">
                     <span className="text-gray-400 text-sm">
                       {target.last_scan ? 
                         new Date(target.last_scan).toLocaleDateString('pt-BR') : 
                         'N/A'
                       }
                     </span>
                   </td>
                 </tr>
               ))}
             </tbody>
           </table>
         </div>
       </Card>
     );
   };
   ```

**Deliverables**:
- [ ] Gráficos de tendência avançados
- [ ] Matriz de risco interativa
- [ ] Export de dados
- [ ] Filtros e drill-down

## 🧪 Testes do Sprint

### Unit Tests
```typescript
// tests/dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { StatsOverview } from '@/components/dashboard/StatsOverview';

describe('StatsOverview', () => {
  test('renders stats correctly', () => {
    const mockData = {
      total_scans: 25,
      active_vulnerabilities: 5,
      risk_score: 65,
      improvement_percentage: -10
    };

    render(<StatsOverview data={mockData} />);

    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('65/100')).toBeInTheDocument();
    expect(screen.getByText('-10%')).toBeInTheDocument();
  });
});
```

### Performance Tests
```python
# tests/test_dashboard_performance.py
import pytest
import time
from app.services.analytics_service import AnalyticsService

@pytest.mark.asyncio
async def test_dashboard_overview_performance():
    analytics = AnalyticsService()
    
    start_time = time.time()
    result = await analytics.get_dashboard_overview("test-user-id", 30)
    end_time = time.time()
    
    # Should complete in less than 2 seconds
    assert (end_time - start_time) < 2.0
    assert result is not None
    assert 'overview' in result
```

## 📊 Métricas de Sucesso

### Performance
- [ ] **Dashboard Load**: < 2 segundos
- [ ] **Chart Rendering**: < 1 segundo
- [ ] **Real-time Updates**: < 100ms latency
- [ ] **Memory Usage**: < 100MB no frontend

### Usabilidade
- [ ] **Responsive Design**: Funciona em mobile/tablet
- [ ] **Accessibility**: WCAG 2.1 AA compliance
- [ ] **User Experience**: Navegação intuitiva
- [ ] **Data Accuracy**: Métricas corretas

### Funcionalidade
- [ ] **Real-time Data**: Atualizações automáticas
- [ ] **Interactive Charts**: Zoom, filter, export
- [ ] **Drill-down**: Detalhes por clique
- [ ] **Time Range Filters**: Períodos customizáveis

---

**Sprint 3 transforma dados brutos em insights acionáveis, estabelecendo ScanIA como ferramenta profissional de cybersegurança.**