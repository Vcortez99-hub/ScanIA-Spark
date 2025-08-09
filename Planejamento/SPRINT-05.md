# Sprint 5: Análise Avançada de Vulnerabilidades

**Duração**: 4 semanas  
**Objetivo**: Implementar análises sofisticadas de vulnerabilidades com IA e threat intelligence  
**Prioridade**: 🔥 Crítica  

## 🎯 Objetivos do Sprint

### Principais Entregáveis
- 🧠 Engine de análise avançada com Machine Learning
- 🌐 Integração com bases de threat intelligence
- 🔍 Detecção de falsos positivos automatizada
- 📊 Análise de correlação entre vulnerabilidades
- 🎯 Sistema de priorização inteligente
- 📈 Predição de tendências de segurança
- 🛡️ Recomendações automatizadas de remediação

### Critérios de Aceitação
- [ ] ML detecta falsos positivos com >85% precisão
- [ ] Correlação entre vulnerabilidades funcionando
- [ ] Threat intelligence atualizada automaticamente
- [ ] Priorização baseada em contexto real
- [ ] Recomendações específicas por vulnerabilidade
- [ ] Análise de impacto no negócio
- [ ] Integration com CVE/MITRE databases

## 🏗️ Arquitetura do Sprint

```
┌─────────────────────────────────────────────────────────────┐
│                   ADVANCED ANALYSIS ENGINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  ML ANALYZER    │  │ THREAT INTEL    │  │  CORRELATOR │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • False Pos Det │  │ • CVE Database  │  │ • Pattern   │ │
│  │ • Risk Scoring  │  │ • MITRE ATT&CK  │  │   Detection │ │
│  │ • Trend Pred    │  │ • IOCs/TTPs     │  │ • Chain     │ │
│  │ • Classification│  │ • OSINT Feeds   │  │   Analysis  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ PRIORITIZATION  │  │  REMEDIATION    │  │  BUSINESS   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Context Aware │  │ • Auto Remediate│  │ • Impact    │ │
│  │ • Business Risk │  │ • Step-by-step  │  │   Analysis  │ │
│  │ • Exploit Prob  │  │ • Code Patches  │  │ • Risk Calc │ │
│  │ • Asset Value   │  │ • Config Fix    │  │ • Cost Est  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   INTERNAL      │  │    EXTERNAL     │  │   LEARNED   │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • Scan Results  │  │ • NVD/CVE       │  │ • Models    │ │
│  │ • User Feedback │  │ • ExploitDB     │  │ • Patterns  │ │
│  │ • Asset Info    │  │ • VirusTotal    │  │ • Historical│ │
│  │ • Environment   │  │ • Security Feeds│  │ • Baselines │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Tasks Detalhadas

### Week 1: Machine Learning Foundation

#### 🎯 Task 1.1: ML Pipeline Architecture (Day 1-3)
**Responsável**: ML Engineer  
**Estimativa**: 24h  

**Atividades**:
1. **ML Pipeline Foundation**
   ```python
   # services/ml_service.py
   import pandas as pd
   import numpy as np
   from sklearn.ensemble import RandomForestClassifier, IsolationForest
   from sklearn.model_selection import train_test_split
   from sklearn.preprocessing import StandardScaler, LabelEncoder
   from sklearn.metrics import classification_report, confusion_matrix
   import joblib
   import logging
   from typing import Dict, List, Tuple, Any
   from dataclasses import dataclass
   import mlflow
   import optuna
   
   @dataclass
   class VulnerabilityFeatures:
       cvss_score: float
       severity: str
       vulnerability_type: str
       affected_component: str
       network_accessible: bool
       authentication_required: bool
       user_interaction_required: bool
       exploit_available: bool
       patch_available: bool
       asset_criticality: float
       exposure_score: float
       
   @dataclass
   class MLPrediction:
       is_false_positive: bool
       confidence: float
       risk_score: float
       priority_level: int
       recommended_actions: List[str]
       explanation: str
   
   class VulnerabilityMLService:
       def __init__(self):
           self.false_positive_model = None
           self.risk_scoring_model = None
           self.priority_model = None
           self.scaler = StandardScaler()
           self.label_encoders = {}
           
           # Initialize MLflow tracking
           mlflow.set_tracking_uri("http://localhost:5000")
           mlflow.set_experiment("vulnerability_analysis")
           
           self.logger = logging.getLogger(__name__)
       
       async def train_false_positive_detector(self, training_data: pd.DataFrame):
           """Treinar modelo para detectar falsos positivos"""
           
           with mlflow.start_run(run_name="false_positive_detector"):
               self.logger.info("Training false positive detection model...")
               
               # Feature engineering
               features = self._extract_features(training_data)
               
               # Prepare labels (0 = real vulnerability, 1 = false positive)
               labels = training_data['is_false_positive'].astype(int)
               
               # Split data
               X_train, X_test, y_train, y_test = train_test_split(
                   features, labels, test_size=0.2, random_state=42, stratify=labels
               )
               
               # Scale features
               X_train_scaled = self.scaler.fit_transform(X_train)
               X_test_scaled = self.scaler.transform(X_test)
               
               # Hyperparameter optimization with Optuna
               def objective(trial):
                   params = {
                       'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                       'max_depth': trial.suggest_int('max_depth', 3, 20),
                       'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                       'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                       'random_state': 42
                   }
                   
                   model = RandomForestClassifier(**params)
                   model.fit(X_train_scaled, y_train)
                   predictions = model.predict(X_test_scaled)
                   
                   from sklearn.metrics import f1_score
                   return f1_score(y_test, predictions)
               
               study = optuna.create_study(direction='maximize')
               study.optimize(objective, n_trials=50)
               
               # Train final model with best parameters
               best_params = study.best_params
               self.false_positive_model = RandomForestClassifier(**best_params)
               self.false_positive_model.fit(X_train_scaled, y_train)
               
               # Evaluate model
               predictions = self.false_positive_model.predict(X_test_scaled)
               probabilities = self.false_positive_model.predict_proba(X_test_scaled)
               
               # Log metrics
               from sklearn.metrics import accuracy_score, precision_score, recall_score
               
               accuracy = accuracy_score(y_test, predictions)
               precision = precision_score(y_test, predictions)
               recall = recall_score(y_test, predictions)
               
               mlflow.log_params(best_params)
               mlflow.log_metrics({
                   'accuracy': accuracy,
                   'precision': precision,
                   'recall': recall
               })
               
               # Save model
               mlflow.sklearn.log_model(
                   self.false_positive_model, 
                   "false_positive_detector"
               )
               
               self.logger.info(f"Model trained. Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
               
               return self.false_positive_model
       
       async def train_risk_scoring_model(self, training_data: pd.DataFrame):
           """Treinar modelo para scoring de risco avançado"""
           
           with mlflow.start_run(run_name="risk_scoring_model"):
               self.logger.info("Training risk scoring model...")
               
               features = self._extract_features(training_data)
               
               # Create composite risk score based on multiple factors
               risk_scores = self._calculate_composite_risk_score(training_data)
               
               X_train, X_test, y_train, y_test = train_test_split(
                   features, risk_scores, test_size=0.2, random_state=42
               )
               
               X_train_scaled = self.scaler.fit_transform(X_train)
               X_test_scaled = self.scaler.transform(X_test)
               
               # Use gradient boosting for regression
               from sklearn.ensemble import GradientBoostingRegressor
               
               def objective(trial):
                   params = {
                       'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                       'max_depth': trial.suggest_int('max_depth', 3, 10),
                       'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                       'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                       'random_state': 42
                   }
                   
                   model = GradientBoostingRegressor(**params)
                   model.fit(X_train_scaled, y_train)
                   predictions = model.predict(X_test_scaled)
                   
                   from sklearn.metrics import mean_squared_error
                   return mean_squared_error(y_test, predictions)
               
               study = optuna.create_study(direction='minimize')
               study.optimize(objective, n_trials=30)
               
               best_params = study.best_params
               self.risk_scoring_model = GradientBoostingRegressor(**best_params)
               self.risk_scoring_model.fit(X_train_scaled, y_train)
               
               # Evaluate
               predictions = self.risk_scoring_model.predict(X_test_scaled)
               
               from sklearn.metrics import mean_absolute_error, r2_score
               mae = mean_absolute_error(y_test, predictions)
               r2 = r2_score(y_test, predictions)
               
               mlflow.log_params(best_params)
               mlflow.log_metrics({'mae': mae, 'r2_score': r2})
               mlflow.sklearn.log_model(self.risk_scoring_model, "risk_scoring_model")
               
               self.logger.info(f"Risk scoring model trained. MAE: {mae:.3f}, R²: {r2:.3f}")
               
               return self.risk_scoring_model
       
       def _extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
           """Extrair features para ML"""
           
           features = pd.DataFrame()
           
           # Numerical features
           features['cvss_score'] = data['cvss_score'].fillna(0)
           features['cvss_base_score'] = data['cvss_base_score'].fillna(0)
           features['cvss_temporal_score'] = data['cvss_temporal_score'].fillna(0)
           features['cvss_environmental_score'] = data['cvss_environmental_score'].fillna(0)
           
           # Asset criticality
           features['asset_criticality'] = data['asset_criticality'].fillna(0.5)
           
           # Network exposure
           features['network_accessible'] = data['network_accessible'].astype(int)
           features['internet_facing'] = data['internet_facing'].astype(int)
           
           # Authentication and interaction
           features['auth_required'] = data['authentication_required'].astype(int)
           features['user_interaction'] = data['user_interaction_required'].astype(int)
           
           # Exploit information
           features['exploit_available'] = data['exploit_available'].astype(int)
           features['exploit_maturity'] = data['exploit_maturity'].map({
               'unproven': 0, 'proof_of_concept': 1, 'functional': 2, 'high': 3
           }).fillna(0)
           
           # Patch information
           features['patch_available'] = data['patch_available'].astype(int)
           features['days_since_disclosure'] = data['days_since_disclosure'].fillna(0)
           features['days_since_patch'] = data['days_since_patch'].fillna(999)
           
           # Categorical features (encoded)
           categorical_features = [
               'severity', 'vulnerability_type', 'affected_component', 
               'attack_vector', 'attack_complexity', 'privileges_required'
           ]
           
           for feature in categorical_features:
               if feature not in self.label_encoders:
                   self.label_encoders[feature] = LabelEncoder()
                   features[feature] = self.label_encoders[feature].fit_transform(
                       data[feature].fillna('unknown')
                   )
               else:
                   # Handle unseen categories
                   known_categories = set(self.label_encoders[feature].classes_)
                   data_categories = data[feature].fillna('unknown')
                   
                   # Map unknown categories to 'unknown'
                   mapped_categories = data_categories.apply(
                       lambda x: x if x in known_categories else 'unknown'
                   )
                   
                   features[feature] = self.label_encoders[feature].transform(mapped_categories)
           
           # Derived features
           features['risk_exposure'] = (
               features['cvss_score'] * features['network_accessible'] * 
               features['asset_criticality']
           )
           
           features['exploit_risk'] = (
               features['exploit_available'] * features['exploit_maturity'] * 
               (10 - features['auth_required'] * 5)
           )
           
           features['patch_urgency'] = np.where(
               features['patch_available'] == 1,
               np.maximum(0, 100 - features['days_since_patch']),
               features['days_since_disclosure'] * 0.5
           )
           
           return features
       
       def _calculate_composite_risk_score(self, data: pd.DataFrame) -> np.ndarray:
           """Calcular score de risco composto baseado em múltiplos fatores"""
           
           scores = []
           
           for _, row in data.iterrows():
               # Base risk from CVSS
               base_risk = row['cvss_score'] * 10  # Scale to 0-100
               
               # Asset criticality multiplier
               asset_multiplier = 0.5 + (row['asset_criticality'] * 0.5)
               
               # Exploit availability impact
               exploit_impact = 0
               if row['exploit_available']:
                   exploit_maturity_map = {
                       'unproven': 10, 'proof_of_concept': 25, 
                       'functional': 50, 'high': 80
                   }
                   exploit_impact = exploit_maturity_map.get(row['exploit_maturity'], 0)
               
               # Patch availability impact (reduces risk)
               patch_reduction = 0
               if row['patch_available']:
                   days_since_patch = row['days_since_patch']
                   if days_since_patch < 30:
                       patch_reduction = 30  # Recent patch available
                   elif days_since_patch < 90:
                       patch_reduction = 20
                   else:
                       patch_reduction = 10
               
               # Network exposure impact
               network_impact = 0
               if row['network_accessible']:
                   network_impact = 20
                   if row['internet_facing']:
                       network_impact = 40
               
               # Authentication requirement (reduces risk)
               auth_reduction = 0
               if row['authentication_required']:
                   auth_reduction = 15
               
               # Calculate final score
               final_score = (
                   (base_risk + exploit_impact + network_impact) * 
                   asset_multiplier - patch_reduction - auth_reduction
               )
               
               # Ensure score is within bounds
               final_score = max(0, min(100, final_score))
               scores.append(final_score)
           
           return np.array(scores)
       
       async def predict_vulnerability_analysis(
           self, 
           vulnerability_data: Dict[str, Any]
       ) -> MLPrediction:
           """Fazer predições avançadas sobre uma vulnerabilidade"""
           
           if not self.false_positive_model or not self.risk_scoring_model:
               raise ValueError("Models not trained. Please train models first.")
           
           # Convert to DataFrame for feature extraction
           df = pd.DataFrame([vulnerability_data])
           features = self._extract_features(df)
           features_scaled = self.scaler.transform(features)
           
           # Predict false positive probability
           fp_probability = self.false_positive_model.predict_proba(features_scaled)[0]
           is_false_positive = fp_probability[1] > 0.5
           fp_confidence = max(fp_probability)
           
           # Predict risk score
           risk_score = self.risk_scoring_model.predict(features_scaled)[0]
           
           # Determine priority level
           priority_level = self._calculate_priority_level(
               risk_score, is_false_positive, fp_confidence
           )
           
           # Generate recommendations
           recommendations = self._generate_recommendations(
               vulnerability_data, risk_score, is_false_positive
           )
           
           # Generate explanation
           explanation = self._generate_explanation(
               vulnerability_data, risk_score, is_false_positive, fp_confidence
           )
           
           return MLPrediction(
               is_false_positive=is_false_positive,
               confidence=fp_confidence,
               risk_score=risk_score,
               priority_level=priority_level,
               recommended_actions=recommendations,
               explanation=explanation
           )
       
       def _calculate_priority_level(
           self, 
           risk_score: float, 
           is_false_positive: bool, 
           confidence: float
       ) -> int:
           """Calcular nível de prioridade (1=highest, 5=lowest)"""
           
           if is_false_positive and confidence > 0.8:
               return 5  # Very low priority
           
           if risk_score >= 80:
               return 1  # Critical
           elif risk_score >= 60:
               return 2  # High
           elif risk_score >= 40:
               return 3  # Medium
           elif risk_score >= 20:
               return 4  # Low
           else:
               return 5  # Very low
       
       def _generate_recommendations(
           self, 
           vuln_data: Dict[str, Any],
           risk_score: float,
           is_false_positive: bool
       ) -> List[str]:
           """Gerar recomendações específicas"""
           
           recommendations = []
           
           if is_false_positive:
               recommendations.append("Considere marcar como falso positivo após verificação manual")
               return recommendations
           
           if risk_score >= 80:
               recommendations.append("🔥 CRÍTICO: Aplicar correção imediatamente")
               recommendations.append("Considere isolamento temporário do ativo")
           
           if vuln_data.get('patch_available'):
               days_since_patch = vuln_data.get('days_since_patch', 0)
               if days_since_patch < 7:
                   recommendations.append("✅ Patch recente disponível - aplicar com urgência")
               else:
                   recommendations.append("📦 Patch disponível - aplicar conforme janela de manutenção")
           else:
               recommendations.append("⚠️ Patch não disponível - implementar controles compensatórios")
           
           if vuln_data.get('exploit_available'):
               recommendations.append("💥 Exploit público disponível - prioridade máxima")
           
           if vuln_data.get('network_accessible'):
               recommendations.append("🌐 Acessível via rede - considere segmentação")
           
           if not vuln_data.get('authentication_required'):
               recommendations.append("🔓 Não requer autenticação - risco elevado")
           
           return recommendations
       
       def _generate_explanation(
           self,
           vuln_data: Dict[str, Any],
           risk_score: float,
           is_false_positive: bool,
           confidence: float
       ) -> str:
           """Gerar explicação detalhada da análise"""
           
           explanation = f"Análise ML da vulnerabilidade:\n\n"
           
           if is_false_positive:
               explanation += f"🎯 Provável falso positivo (confiança: {confidence:.1%})\n"
               explanation += "Recomenda-se verificação manual antes de ignorar.\n\n"
           else:
               explanation += f"✅ Vulnerabilidade válida (confiança: {confidence:.1%})\n\n"
           
           explanation += f"📊 Score de risco calculado: {risk_score:.1f}/100\n"
           
           # Explicar fatores que contribuem para o score
           factors = []
           
           cvss = vuln_data.get('cvss_score', 0)
           if cvss >= 9:
               factors.append(f"CVSS crítico ({cvss})")
           elif cvss >= 7:
               factors.append(f"CVSS alto ({cvss})")
           
           if vuln_data.get('exploit_available'):
               factors.append("Exploit público disponível")
           
           if vuln_data.get('network_accessible'):
               factors.append("Acessível via rede")
           
           if vuln_data.get('internet_facing'):
               factors.append("Exposto à internet")
           
           asset_criticality = vuln_data.get('asset_criticality', 0.5)
           if asset_criticality > 0.8:
               factors.append("Ativo de alta criticidade")
           
           if factors:
               explanation += f"\n🔍 Fatores de risco identificados:\n"
               for factor in factors:
                   explanation += f"  • {factor}\n"
           
           return explanation
   
       async def save_models(self, model_path: str = "models/"):
           """Salvar modelos treinados"""
           import os
           os.makedirs(model_path, exist_ok=True)
           
           if self.false_positive_model:
               joblib.dump(self.false_positive_model, f"{model_path}/fp_model.pkl")
           
           if self.risk_scoring_model:
               joblib.dump(self.risk_scoring_model, f"{model_path}/risk_model.pkl")
           
           joblib.dump(self.scaler, f"{model_path}/scaler.pkl")
           joblib.dump(self.label_encoders, f"{model_path}/label_encoders.pkl")
           
           self.logger.info(f"Models saved to {model_path}")
       
       async def load_models(self, model_path: str = "models/"):
           """Carregar modelos salvos"""
           
           try:
               self.false_positive_model = joblib.load(f"{model_path}/fp_model.pkl")
               self.risk_scoring_model = joblib.load(f"{model_path}/risk_model.pkl")
               self.scaler = joblib.load(f"{model_path}/scaler.pkl")
               self.label_encoders = joblib.load(f"{model_path}/label_encoders.pkl")
               
               self.logger.info(f"Models loaded from {model_path}")
           except Exception as e:
               self.logger.error(f"Error loading models: {str(e)}")
               raise
   ```

2. **Model Training Pipeline**
   ```python
   # scripts/train_models.py
   import asyncio
   import pandas as pd
   from services.ml_service import VulnerabilityMLService
   from app.models import Scan, Vulnerability
   from app.core.database import get_db_session
   
   async def prepare_training_data():
       """Preparar dados de treinamento a partir do banco"""
       
       db = get_db_session()
       
       # Query para obter dados de vulnerabilidades com feedback
       query = """
       SELECT 
           v.id,
           v.cvss_score,
           v.cvss_base_score,
           v.cvss_temporal_score,
           v.cvss_environmental_score,
           v.severity,
           v.vulnerability_type,
           v.affected_component,
           v.attack_vector,
           v.attack_complexity,
           v.privileges_required,
           v.user_interaction_required::boolean,
           v.network_accessible::boolean,
           v.internet_facing::boolean,
           v.authentication_required::boolean,
           v.exploit_available::boolean,
           v.exploit_maturity,
           v.patch_available::boolean,
           v.days_since_disclosure,
           v.days_since_patch,
           v.asset_criticality,
           v.is_false_positive::boolean,
           v.user_feedback,
           s.target_url,
           s.environment_type
       FROM vulnerabilities v
       JOIN scans s ON v.scan_id = s.id
       WHERE v.user_feedback IS NOT NULL
       """
       
       df = pd.read_sql(query, db.bind)
       
       # Feature engineering adicional
       df['days_since_disclosure'] = df['days_since_disclosure'].fillna(0)
       df['days_since_patch'] = df['days_since_patch'].fillna(999)
       df['asset_criticality'] = df['asset_criticality'].fillna(0.5)
       
       # Adicionar features derivadas
       df['is_web_app'] = df['vulnerability_type'].str.contains('web', case=False, na=False)
       df['is_infrastructure'] = df['vulnerability_type'].str.contains('infrastructure', case=False, na=False)
       df['has_cve'] = df['cve_id'].notna()
       
       return df
   
   async def main():
       """Pipeline principal de treinamento"""
       
       print("🚀 Starting ML model training pipeline...")
       
       # Preparar dados
       print("📊 Preparing training data...")
       training_data = await prepare_training_data()
       
       if len(training_data) < 100:
           print("❌ Insufficient training data. Need at least 100 labeled examples.")
           return
       
       print(f"✅ Loaded {len(training_data)} training examples")
       
       # Inicializar serviço ML
       ml_service = VulnerabilityMLService()
       
       # Treinar modelo de falsos positivos
       print("🤖 Training false positive detection model...")
       await ml_service.train_false_positive_detector(training_data)
       
       # Treinar modelo de scoring de risco
       print("📊 Training risk scoring model...")
       await ml_service.train_risk_scoring_model(training_data)
       
       # Salvar modelos
       print("💾 Saving trained models...")
       await ml_service.save_models()
       
       print("✅ ML training pipeline completed successfully!")
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

**Deliverables**:
- [ ] ML pipeline completo
- [ ] Modelos de false positive detection
- [ ] Sistema de risk scoring avançado
- [ ] Pipeline de treinamento automatizado

---

#### 🎯 Task 1.2: Threat Intelligence Integration (Day 3-5)  
**Responsável**: Security Engineer  
**Estimativa**: 20h  

**Atividades**:
1. **Threat Intelligence Service**
   ```python
   # services/threat_intelligence_service.py
   import asyncio
   import aiohttp
   import json
   from typing import Dict, List, Optional, Any
   from datetime import datetime, timedelta
   from dataclasses import dataclass
   import hashlib
   from app.core.config import settings
   from app.models import ThreatIntelligence, IOC, TTPs
   
   @dataclass
   class ThreatIndicator:
       type: str  # ip, domain, hash, cve, etc.
       value: str
       source: str
       confidence: float
       first_seen: datetime
       last_seen: datetime
       tags: List[str]
       description: str
       
   @dataclass
   class CVEIntelligence:
       cve_id: str
       cvss_score: float
       cvss_vector: str
       description: str
       published_date: datetime
       modified_date: datetime
       exploit_available: bool
       exploit_maturity: str
       patch_available: bool
       vendor_advisories: List[str]
       references: List[str]
       
   class ThreatIntelligenceService:
       def __init__(self):
           self.session = None
           self.sources = {
               'nvd': {
                   'url': 'https://services.nvd.nist.gov/rest/json/cves/2.0',
                   'api_key': settings.NVD_API_KEY
               },
               'mitre': {
                   'url': 'https://cve.mitre.org/data/downloads',
                   'api_key': None
               },
               'virustotal': {
                   'url': 'https://www.virustotal.com/api/v3',
                   'api_key': settings.VIRUSTOTAL_API_KEY
               },
               'otx': {
                   'url': 'https://otx.alienvault.com/api/v1',
                   'api_key': settings.OTX_API_KEY
               },
               'exploitdb': {
                   'url': 'https://www.exploit-db.com/api/v1',
                   'api_key': None
               }
           }
       
       async def __aenter__(self):
           self.session = aiohttp.ClientSession(
               timeout=aiohttp.ClientTimeout(total=30),
               headers={'User-Agent': 'ScanIA-ThreatIntel/1.0'}
           )
           return self
       
       async def __aexit__(self, exc_type, exc_val, exc_tb):
           if self.session:
               await self.session.close()
       
       async def enrich_vulnerability(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
           """Enriquecer dados de vulnerabilidade com threat intelligence"""
           
           enriched_data = vulnerability_data.copy()
           
           # Buscar informações por CVE ID se disponível
           cve_id = vulnerability_data.get('cve_id')
           if cve_id:
               cve_intel = await self.get_cve_intelligence(cve_id)
               if cve_intel:
                   enriched_data.update({
                       'threat_intelligence': {
                           'cve_details': cve_intel.__dict__,
                           'exploit_available': cve_intel.exploit_available,
                           'exploit_maturity': cve_intel.exploit_maturity,
                           'vendor_advisories': cve_intel.vendor_advisories
                       }
                   })
           
           # Buscar indicadores relacionados
           indicators = await self.find_related_indicators(vulnerability_data)
           if indicators:
               enriched_data['related_indicators'] = [ind.__dict__ for ind in indicators]
           
           # Buscar exploits conhecidos
           exploits = await self.search_exploits(vulnerability_data)
           if exploits:
               enriched_data['known_exploits'] = exploits
           
           # Calcular threat score baseado em intelligence
           threat_score = await self.calculate_threat_score(enriched_data)
           enriched_data['threat_score'] = threat_score
           
           return enriched_data
       
       async def get_cve_intelligence(self, cve_id: str) -> Optional[CVEIntelligence]:
           """Obter informações detalhadas sobre um CVE"""
           
           try:
               # Buscar no NVD primeiro
               nvd_data = await self._query_nvd_cve(cve_id)
               if nvd_data:
                   return self._parse_nvd_cve(nvd_data)
               
               # Fallback para MITRE
               mitre_data = await self._query_mitre_cve(cve_id)
               if mitre_data:
                   return self._parse_mitre_cve(mitre_data)
               
               return None
               
           except Exception as e:
               logger.error(f"Error fetching CVE intelligence for {cve_id}: {str(e)}")
               return None
       
       async def _query_nvd_cve(self, cve_id: str) -> Optional[Dict]:
           """Consultar NVD por CVE específico"""
           
           url = f"{self.sources['nvd']['url']}"
           params = {
               'cveId': cve_id,
               'resultsPerPage': 1
           }
           
           headers = {}
           if self.sources['nvd']['api_key']:
               headers['apiKey'] = self.sources['nvd']['api_key']
           
           async with self.session.get(url, params=params, headers=headers) as response:
               if response.status == 200:
                   data = await response.json()
                   if data.get('vulnerabilities'):
                       return data['vulnerabilities'][0]
           
           return None
       
       async def _parse_nvd_cve(self, nvd_data: Dict) -> CVEIntelligence:
           """Parsear dados do NVD"""
           
           cve = nvd_data['cve']
           
           # Extract CVSS scores
           cvss_score = 0.0
           cvss_vector = ""
           
           if 'metrics' in cve:
               metrics = cve['metrics']
               if 'cvssMetricV31' in metrics:
                   cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                   cvss_score = cvss_data['baseScore']
                   cvss_vector = cvss_data['vectorString']
               elif 'cvssMetricV30' in metrics:
                   cvss_data = metrics['cvssMetricV30'][0]['cvssData']
                   cvss_score = cvss_data['baseScore']
                   cvss_vector = cvss_data['vectorString']
           
           # Parse dates
           published_date = datetime.fromisoformat(
               cve['published'].replace('Z', '+00:00')
           )
           modified_date = datetime.fromisoformat(
               cve['lastModified'].replace('Z', '+00:00')
           )
           
           # Extract description
           description = ""
           if 'descriptions' in cve:
               for desc in cve['descriptions']:
                   if desc['lang'] == 'en':
                       description = desc['value']
                       break
           
           # Extract references
           references = []
           if 'references' in cve:
               references = [ref['url'] for ref in cve['references']]
           
           # Check for exploit availability (basic heuristic)
           exploit_available = any(
               'exploit' in ref.lower() for ref in references
           )
           
           return CVEIntelligence(
               cve_id=cve['id'],
               cvss_score=cvss_score,
               cvss_vector=cvss_vector,
               description=description,
               published_date=published_date,
               modified_date=modified_date,
               exploit_available=exploit_available,
               exploit_maturity='unknown',
               patch_available=False,  # Would need additional logic
               vendor_advisories=[],
               references=references
           )
       
       async def search_exploits(self, vulnerability_data: Dict[str, Any]) -> List[Dict[str, Any]]:
           """Buscar exploits conhecidos para a vulnerabilidade"""
           
           exploits = []
           
           # Search ExploitDB
           exploitdb_results = await self._search_exploitdb(vulnerability_data)
           exploits.extend(exploitdb_results)
           
           # Search Metasploit modules
           metasploit_results = await self._search_metasploit(vulnerability_data)
           exploits.extend(metasploit_results)
           
           # Search GitHub for PoCs
           github_results = await self._search_github_pocs(vulnerability_data)
           exploits.extend(github_results)
           
           return exploits
       
       async def _search_exploitdb(self, vuln_data: Dict[str, Any]) -> List[Dict[str, Any]]:
           """Buscar exploits no ExploitDB"""
           
           results = []
           cve_id = vuln_data.get('cve_id')
           
           if not cve_id:
               return results
           
           try:
               # ExploitDB search API
               url = f"{self.sources['exploitdb']['url']}/search"
               params = {'cve': cve_id}
               
               async with self.session.get(url, params=params) as response:
                   if response.status == 200:
                       data = await response.json()
                       for exploit in data.get('data', []):
                           results.append({
                               'source': 'ExploitDB',
                               'id': exploit.get('id'),
                               'title': exploit.get('title'),
                               'type': exploit.get('type'),
                               'platform': exploit.get('platform'),
                               'date': exploit.get('date'),
                               'url': f"https://www.exploit-db.com/exploits/{exploit.get('id')}"
                           })
           
           except Exception as e:
               logger.error(f"Error searching ExploitDB: {str(e)}")
           
           return results
       
       async def _search_metasploit(self, vuln_data: Dict[str, Any]) -> List[Dict[str, Any]]:
           """Buscar módulos do Metasploit"""
           
           results = []
           # This would require access to Metasploit database or API
           # For now, we'll use a simple heuristic based on CVE
           
           cve_id = vuln_data.get('cve_id')
           if cve_id:
               # Search for known Metasploit modules
               # This is a placeholder - in reality you'd query the actual Metasploit database
               results.append({
                   'source': 'Metasploit',
                   'module': f'exploit/multi/misc/{cve_id.lower().replace("-", "_")}',
                   'description': f'Potential Metasploit module for {cve_id}',
                   'reliability': 'estimated'
               })
           
           return results
       
       async def _search_github_pocs(self, vuln_data: Dict[str, Any]) -> List[Dict[str, Any]]:
           """Buscar proof-of-concepts no GitHub"""
           
           results = []
           cve_id = vuln_data.get('cve_id')
           
           if not cve_id:
               return results
           
           try:
               # GitHub search API
               url = "https://api.github.com/search/repositories"
               params = {
                   'q': f'{cve_id} PoC OR {cve_id} exploit',
                   'sort': 'stars',
                   'order': 'desc'
               }
               
               async with self.session.get(url, params=params) as response:
                   if response.status == 200:
                       data = await response.json()
                       for repo in data.get('items', [])[:5]:  # Limit to top 5
                           results.append({
                               'source': 'GitHub',
                               'repository': repo['full_name'],
                               'description': repo['description'],
                               'stars': repo['stargazers_count'],
                               'url': repo['html_url'],
                               'updated': repo['updated_at']
                           })
           
           except Exception as e:
               logger.error(f"Error searching GitHub: {str(e)}")
           
           return results
       
       async def find_related_indicators(self, vuln_data: Dict[str, Any]) -> List[ThreatIndicator]:
           """Buscar indicadores de ameaça relacionados"""
           
           indicators = []
           
           # Search based on affected URLs/IPs
           target_url = vuln_data.get('affected_url', '')
           if target_url:
               # Extract domain/IP
               from urllib.parse import urlparse
               parsed = urlparse(target_url)
               domain = parsed.netloc
               
               # Query threat intel sources
               otx_indicators = await self._query_otx_indicators(domain)
               indicators.extend(otx_indicators)
               
               vt_indicators = await self._query_virustotal_indicators(domain)
               indicators.extend(vt_indicators)
           
           return indicators
       
       async def _query_otx_indicators(self, domain: str) -> List[ThreatIndicator]:
           """Consultar indicadores no AlienVault OTX"""
           
           indicators = []
           
           if not self.sources['otx']['api_key']:
               return indicators
           
           try:
               url = f"{self.sources['otx']['url']}/indicators/domain/{domain}/general"
               headers = {'X-OTX-API-KEY': self.sources['otx']['api_key']}
               
               async with self.session.get(url, headers=headers) as response:
                   if response.status == 200:
                       data = await response.json()
                       
                       # Parse OTX response
                       if 'pulse_info' in data:
                           for pulse in data['pulse_info']['pulses']:
                               indicator = ThreatIndicator(
                                   type='domain',
                                   value=domain,
                                   source='AlienVault OTX',
                                   confidence=0.7,  # Default confidence
                                   first_seen=datetime.fromisoformat(pulse['created']),
                                   last_seen=datetime.fromisoformat(pulse['modified']),
                                   tags=pulse.get('tags', []),
                                   description=pulse.get('description', '')
                               )
                               indicators.append(indicator)
           
           except Exception as e:
               logger.error(f"Error querying OTX: {str(e)}")
           
           return indicators
       
       async def calculate_threat_score(self, enriched_data: Dict[str, Any]) -> float:
           """Calcular score de ameaça baseado em intelligence"""
           
           base_score = enriched_data.get('cvss_score', 0) * 10  # Scale to 0-100
           
           # Adjust based on threat intelligence
           threat_intel = enriched_data.get('threat_intelligence', {})
           
           # Exploit availability boost
           if threat_intel.get('exploit_available'):
               base_score += 20
           
           # Active exploitation in the wild
           related_indicators = enriched_data.get('related_indicators', [])
           if related_indicators:
               base_score += 15
           
           # Known exploits boost
           known_exploits = enriched_data.get('known_exploits', [])
           if known_exploits:
               base_score += len(known_exploits) * 5  # Up to 25 additional points
           
           # Age factor (newer vulnerabilities are often more dangerous)
           cve_details = threat_intel.get('cve_details', {})
           if 'published_date' in cve_details:
               published_date = datetime.fromisoformat(cve_details['published_date'])
               days_old = (datetime.now() - published_date).days
               
               if days_old < 30:
                   base_score += 10  # Very recent
               elif days_old < 90:
                   base_score += 5   # Recent
           
           # Ensure score is within bounds
           return max(0, min(100, base_score))
       
       async def update_threat_intelligence_db(self):
           """Atualizar base de dados de threat intelligence"""
           
           logger.info("Updating threat intelligence database...")
           
           # Update CVE database
           await self._update_cve_database()
           
           # Update IOCs
           await self._update_ioc_database()
           
           # Update TTPs
           await self._update_ttp_database()
           
           logger.info("Threat intelligence database updated successfully")
       
       async def _update_cve_database(self):
           """Atualizar base de CVEs"""
           
           # Get recent CVEs from NVD
           end_date = datetime.now()
           start_date = end_date - timedelta(days=30)  # Last 30 days
           
           url = f"{self.sources['nvd']['url']}"
           params = {
               'pubStartDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
               'pubEndDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
               'resultsPerPage': 100
           }
           
           headers = {}
           if self.sources['nvd']['api_key']:
               headers['apiKey'] = self.sources['nvd']['api_key']
           
           try:
               async with self.session.get(url, params=params, headers=headers) as response:
                   if response.status == 200:
                       data = await response.json()
                       
                       for vuln in data.get('vulnerabilities', []):
                           cve_intel = self._parse_nvd_cve(vuln)
                           
                           # Save to database
                           # This would save to your ThreatIntelligence model
                           pass
           
           except Exception as e:
               logger.error(f"Error updating CVE database: {str(e)}")
   ```

**Deliverables**:
- [ ] Threat intelligence service completo
- [ ] Integração com múltiplas fontes (NVD, MITRE, etc.)
- [ ] Sistema de enrichment de vulnerabilidades
- [ ] Cache e otimização de consultas

### Week 2: Correlation Engine

#### 🎯 Task 2.1: Vulnerability Correlation (Day 6-10)
**Responsável**: Security Engineer  
**Estimativa**: 40h  

**Atividades**:
1. **Correlation Engine**
   ```python
   # services/correlation_service.py
   import networkx as nx
   from typing import Dict, List, Set, Tuple, Any
   from dataclasses import dataclass
   from datetime import datetime, timedelta
   import numpy as np
   from sklearn.cluster import DBSCAN
   from sklearn.feature_extraction.text import TfidfVectorizer
   from sklearn.metrics.pairwise import cosine_similarity
   import logging
   
   @dataclass
   class VulnerabilityCluster:
       cluster_id: str
       vulnerabilities: List[str]
       attack_pattern: str
       severity_level: str
       affected_assets: List[str]
       common_root_cause: str
       remediation_approach: str
       
   @dataclass
   class AttackPath:
       path_id: str
       vulnerabilities: List[str]
       attack_steps: List[str]
       final_impact: str
       likelihood: float
       mitigation_points: List[str]
       
   class VulnerabilityCorrelationService:
       def __init__(self):
           self.vulnerability_graph = nx.Graph()
           self.logger = logging.getLogger(__name__)
           
       async def analyze_vulnerability_correlations(
           self, 
           vulnerabilities: List[Dict[str, Any]]
       ) -> Dict[str, Any]:
           """Análise principal de correlações entre vulnerabilidades"""
           
           self.logger.info(f"Analyzing correlations for {len(vulnerabilities)} vulnerabilities")
           
           # Build vulnerability graph
           self._build_vulnerability_graph(vulnerabilities)
           
           # Find vulnerability clusters
           clusters = await self._find_vulnerability_clusters(vulnerabilities)
           
           # Identify attack paths
           attack_paths = await self._identify_attack_paths(vulnerabilities)
           
           # Analyze attack patterns
           patterns = await self._analyze_attack_patterns(vulnerabilities)
           
           # Find common root causes
           root_causes = await self._find_common_root_causes(vulnerabilities)
           
           # Generate correlation insights
           insights = await self._generate_correlation_insights(
               clusters, attack_paths, patterns, root_causes
           )
           
           return {
               'clusters': [cluster.__dict__ for cluster in clusters],
               'attack_paths': [path.__dict__ for path in attack_paths],
               'patterns': patterns,
               'root_causes': root_causes,
               'insights': insights,
               'correlation_matrix': self._generate_correlation_matrix(vulnerabilities)
           }
       
       def _build_vulnerability_graph(self, vulnerabilities: List[Dict[str, Any]]):
           """Construir grafo de vulnerabilidades baseado em relacionamentos"""
           
           self.vulnerability_graph.clear()
           
           # Add nodes (vulnerabilities)
           for vuln in vulnerabilities:
               self.vulnerability_graph.add_node(
                   vuln['id'],
                   **{k: v for k, v in vuln.items() if k != 'id'}
               )
           
           # Add edges based on relationships
           for i, vuln1 in enumerate(vulnerabilities):
               for vuln2 in vulnerabilities[i+1:]:
                   relationship_strength = self._calculate_relationship_strength(vuln1, vuln2)
                   
                   if relationship_strength > 0.3:  # Threshold for connection
                       self.vulnerability_graph.add_edge(
                           vuln1['id'], 
                           vuln2['id'], 
                           weight=relationship_strength
                       )
       
       def _calculate_relationship_strength(
           self, 
           vuln1: Dict[str, Any], 
           vuln2: Dict[str, Any]
       ) -> float:
           """Calcular força do relacionamento entre duas vulnerabilidades"""
           
           strength = 0.0
           
           # Same asset/URL
           if vuln1.get('affected_url') == vuln2.get('affected_url'):
               strength += 0.4
           
           # Same vulnerability type
           if vuln1.get('vulnerability_type') == vuln2.get('vulnerability_type'):
               strength += 0.3
           
           # Same technology/component
           if vuln1.get('affected_component') == vuln2.get('affected_component'):
               strength += 0.3
           
           # Similar CVSS scores (within 1.0)
           cvss1 = vuln1.get('cvss_score', 0)
           cvss2 = vuln2.get('cvss_score', 0)
           if abs(cvss1 - cvss2) <= 1.0:
               strength += 0.2
           
           # Similar attack vectors
           av1 = vuln1.get('attack_vector', '')
           av2 = vuln2.get('attack_vector', '')
           if av1 == av2:
               strength += 0.2
           
           # Related CVEs (part of same vulnerability family)
           cve1 = vuln1.get('cve_id', '')
           cve2 = vuln2.get('cve_id', '')
           if cve1 and cve2:
               # Extract year and base number
               if cve1[:8] == cve2[:8]:  # Same year and similar ID
                   strength += 0.3
           
           # Temporal proximity (found in scans close in time)
           time1 = vuln1.get('discovered_at')
           time2 = vuln2.get('discovered_at')
           if time1 and time2:
               time_diff = abs((time1 - time2).total_seconds())
               if time_diff < 3600:  # Within 1 hour
                   strength += 0.2
               elif time_diff < 86400:  # Within 1 day
                   strength += 0.1
           
           # Description similarity (using TF-IDF)
           desc1 = vuln1.get('description', '')
           desc2 = vuln2.get('description', '')
           if len(desc1) > 10 and len(desc2) > 10:
               try:
                   vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
                   tfidf_matrix = vectorizer.fit_transform([desc1, desc2])
                   similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                   strength += similarity * 0.2
               except:
                   pass
           
           return min(1.0, strength)  # Cap at 1.0
       
       async def _find_vulnerability_clusters(
           self, 
           vulnerabilities: List[Dict[str, Any]]
       ) -> List[VulnerabilityCluster]:
           """Encontrar clusters de vulnerabilidades relacionadas"""
           
           clusters = []
           
           # Use community detection on the graph
           import networkx.algorithms.community as nx_comm
           
           try:
               communities = nx_comm.greedy_modularity_communities(self.vulnerability_graph)
               
               for i, community in enumerate(communities):
                   if len(community) > 1:  # Only clusters with multiple vulnerabilities
                       vuln_list = list(community)
                       
                       # Analyze cluster characteristics
                       cluster_vulns = [v for v in vulnerabilities if v['id'] in vuln_list]
                       
                       # Determine common patterns
                       attack_pattern = self._identify_cluster_attack_pattern(cluster_vulns)
                       severity_level = self._determine_cluster_severity(cluster_vulns)
                       affected_assets = list(set(v.get('affected_url', '') for v in cluster_vulns))
                       root_cause = self._identify_cluster_root_cause(cluster_vulns)
                       remediation = self._suggest_cluster_remediation(cluster_vulns)
                       
                       cluster = VulnerabilityCluster(
                           cluster_id=f"cluster_{i+1}",
                           vulnerabilities=vuln_list,
                           attack_pattern=attack_pattern,
                           severity_level=severity_level,
                           affected_assets=affected_assets,
                           common_root_cause=root_cause,
                           remediation_approach=remediation
                       )
                       clusters.append(cluster)
           
           except Exception as e:
               self.logger.error(f"Error in clustering: {str(e)}")
           
           return clusters
       
       def _identify_cluster_attack_pattern(self, vulnerabilities: List[Dict[str, Any]]) -> str:
           """Identificar padrão de ataque comum no cluster"""
           
           # Analyze vulnerability types
           vuln_types = [v.get('vulnerability_type', '') for v in vulnerabilities]
           type_counts = {}
           for vt in vuln_types:
               type_counts[vt] = type_counts.get(vt, 0) + 1
           
           most_common_type = max(type_counts, key=type_counts.get) if type_counts else ''
           
           # Analyze attack vectors
           attack_vectors = [v.get('attack_vector', '') for v in vulnerabilities]
           vector_counts = {}
           for av in attack_vectors:
               vector_counts[av] = vector_counts.get(av, 0) + 1
           
           most_common_vector = max(vector_counts, key=vector_counts.get) if vector_counts else ''
           
           # Generate pattern description
           if 'web' in most_common_type.lower():
               if 'network' in most_common_vector.lower():
                   return "Web Application Network Attack Chain"
               else:
                   return "Web Application Vulnerability Chain"
           elif 'infrastructure' in most_common_type.lower():
               return "Infrastructure Compromise Chain"
           elif len(set(vuln_types)) == 1:
               return f"Coordinated {most_common_type} Attack"
           else:
               return "Multi-Vector Attack Chain"
       
       async def _identify_attack_paths(
           self, 
           vulnerabilities: List[Dict[str, Any]]
       ) -> List[AttackPath]:
           """Identificar possíveis caminhos de ataque"""
           
           attack_paths = []
           
           # Find all paths in the vulnerability graph
           try:
               # Group vulnerabilities by asset
               asset_vulns = {}
               for vuln in vulnerabilities:
                   asset = vuln.get('affected_url', 'unknown')
                   if asset not in asset_vulns:
                       asset_vulns[asset] = []
                   asset_vulns[asset].append(vuln)
               
               for asset, vulns in asset_vulns.items():
                   if len(vulns) > 1:
                       # Sort by potential attack sequence
                       sorted_vulns = sorted(
                           vulns, 
                           key=lambda v: (
                               self._get_attack_complexity_score(v),
                               -v.get('cvss_score', 0)
                           )
                       )
                       
                       # Create attack path
                       path_vulns = [v['id'] for v in sorted_vulns]
                       attack_steps = self._generate_attack_steps(sorted_vulns)
                       final_impact = self._assess_final_impact(sorted_vulns)
                       likelihood = self._calculate_attack_likelihood(sorted_vulns)
                       mitigation_points = self._identify_mitigation_points(sorted_vulns)
                       
                       attack_path = AttackPath(
                           path_id=f"path_{asset}_{len(attack_paths)+1}",
                           vulnerabilities=path_vulns,
                           attack_steps=attack_steps,
                           final_impact=final_impact,
                           likelihood=likelihood,
                           mitigation_points=mitigation_points
                       )
                       attack_paths.append(attack_path)
           
           except Exception as e:
               self.logger.error(f"Error identifying attack paths: {str(e)}")
           
           return attack_paths
       
       def _get_attack_complexity_score(self, vulnerability: Dict[str, Any]) -> int:
           """Score para ordenar vulnerabilidades por complexidade de ataque"""
           
           score = 0
           
           # Network accessibility
           if vulnerability.get('network_accessible'):
               score += 1
           
           # Authentication requirement (lower score = easier)
           if not vulnerability.get('authentication_required'):
               score += 2
           
           # User interaction requirement
           if not vulnerability.get('user_interaction_required'):
               score += 1
           
           # Attack complexity
           complexity = vulnerability.get('attack_complexity', '').lower()
           if complexity == 'low':
               score += 3
           elif complexity == 'medium':
               score += 2
           else:
               score += 1
           
           return score
       
       def _generate_attack_steps(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
           """Gerar passos de ataque baseado nas vulnerabilidades"""
           
           steps = []
           
           for i, vuln in enumerate(vulnerabilities):
               step_num = i + 1
               vuln_type = vuln.get('vulnerability_type', 'unknown')
               
               if i == 0:
                   steps.append(f"Step {step_num}: Initial compromise via {vuln_type}")
               elif i == len(vulnerabilities) - 1:
                   steps.append(f"Step {step_num}: Final objective achieved through {vuln_type}")
               else:
                   steps.append(f"Step {step_num}: Lateral movement using {vuln_type}")
           
           return steps
       
       def _calculate_attack_likelihood(self, vulnerabilities: List[Dict[str, Any]]) -> float:
           """Calcular probabilidade de sucesso do caminho de ataque"""
           
           base_likelihood = 1.0
           
           for vuln in vulnerabilities:
               # Reduce likelihood based on complexity
               if vuln.get('authentication_required'):
                   base_likelihood *= 0.7
               
               if vuln.get('user_interaction_required'):
                   base_likelihood *= 0.8
               
               complexity = vuln.get('attack_complexity', 'high').lower()
               if complexity == 'low':
                   base_likelihood *= 0.9
               elif complexity == 'medium':
                   base_likelihood *= 0.7
               else:
                   base_likelihood *= 0.5
               
               # Increase likelihood if exploit is available
               if vuln.get('exploit_available'):
                   base_likelihood *= 1.3
           
           return min(1.0, base_likelihood)
       
       async def _analyze_attack_patterns(
           self, 
           vulnerabilities: List[Dict[str, Any]]
       ) -> Dict[str, Any]:
           """Analisar padrões de ataque nos dados"""
           
           patterns = {
               'temporal_patterns': self._analyze_temporal_patterns(vulnerabilities),
               'technology_patterns': self._analyze_technology_patterns(vulnerabilities),
               'severity_patterns': self._analyze_severity_patterns(vulnerabilities),
               'attack_vector_patterns': self._analyze_attack_vector_patterns(vulnerabilities)
           }
           
           return patterns
       
       def _analyze_temporal_patterns(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
           """Analisar padrões temporais de descoberta"""
           
           # Group by discovery time
           time_groups = {}
           for vuln in vulnerabilities:
               discovered_at = vuln.get('discovered_at')
               if discovered_at:
                   # Group by hour
                   hour_key = discovered_at.strftime('%Y-%m-%d %H:00:00')
                   if hour_key not in time_groups:
                       time_groups[hour_key] = []
                   time_groups[hour_key].append(vuln)
           
           # Find clusters in time
           time_clusters = []
           for time_key, vulns in time_groups.items():
               if len(vulns) > 1:
                   time_clusters.append({
                       'time': time_key,
                       'vulnerability_count': len(vulns),
                       'vulnerabilities': [v['id'] for v in vulns]
                   })
           
           return {
               'time_clusters': time_clusters,
               'total_time_span': self._calculate_time_span(vulnerabilities),
               'discovery_frequency': len(vulnerabilities) / max(1, len(time_groups))
           }
       
       def _generate_correlation_matrix(self, vulnerabilities: List[Dict[str, Any]]) -> List[List[float]]:
           """Gerar matriz de correlação entre vulnerabilidades"""
           
           n = len(vulnerabilities)
           matrix = [[0.0 for _ in range(n)] for _ in range(n)]
           
           for i in range(n):
               for j in range(n):
                   if i == j:
                       matrix[i][j] = 1.0
                   else:
                       correlation = self._calculate_relationship_strength(
                           vulnerabilities[i], vulnerabilities[j]
                       )
                       matrix[i][j] = correlation
           
           return matrix
   ```

**Deliverables**:
- [ ] Sistema de correlação avançado
- [ ] Detecção de clusters de vulnerabilidades
- [ ] Identificação de caminhos de ataque
- [ ] Análise de padrões temporais e tecnológicos

### Week 3-4: Advanced Features

#### 🎯 Task 3.1: Predictive Analytics (Day 11-20)
**Responsável**: ML Engineer  
**Estimativa**: 80h  

**Atividades**:
1. **Predictive Models**
   ```python
   # services/predictive_service.py
   import numpy as np
   import pandas as pd
   from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
   from sklearn.preprocessing import StandardScaler
   from sklearn.model_selection import train_test_split, cross_val_score
   from sklearn.metrics import mean_squared_error, classification_report
   import tensorflow as tf
   from tensorflow.keras.models import Sequential
   from tensorflow.keras.layers import LSTM, Dense, Dropout
   from datetime import datetime, timedelta
   import joblib
   from typing import Dict, List, Any, Tuple
   
   class PredictiveAnalyticsService:
       def __init__(self):
           self.vulnerability_trend_model = None
           self.exploit_prediction_model = None
           self.risk_forecast_model = None
           self.scaler = StandardScaler()
           
       async def train_vulnerability_trend_model(self, historical_data: pd.DataFrame):
           """Treinar modelo para prever tendências de vulnerabilidades"""
           
           # Prepare time series data
           time_series = self._prepare_time_series_data(historical_data)
           
           # Create sequences for LSTM
           X, y = self._create_sequences(time_series, sequence_length=30)
           
           # Split data
           X_train, X_test, y_train, y_test = train_test_split(
               X, y, test_size=0.2, random_state=42
           )
           
           # Build LSTM model
           model = Sequential([
               LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
               Dropout(0.2),
               LSTM(50, return_sequences=False),
               Dropout(0.2),
               Dense(25),
               Dense(1)
           ])
           
           model.compile(optimizer='adam', loss='mse')
           
           # Train model
           history = model.fit(
               X_train, y_train,
               batch_size=32,
               epochs=100,
               validation_data=(X_test, y_test),
               verbose=0
           )
           
           self.vulnerability_trend_model = model
           
           # Evaluate
           train_predict = model.predict(X_train)
           test_predict = model.predict(X_test)
           
           train_rmse = np.sqrt(mean_squared_error(y_train, train_predict))
           test_rmse = np.sqrt(mean_squared_error(y_test, test_predict))
           
           print(f"Vulnerability Trend Model - Train RMSE: {train_rmse:.4f}, Test RMSE: {test_rmse:.4f}")
           
           return model
       
       async def predict_future_vulnerabilities(
           self, 
           current_data: pd.DataFrame, 
           prediction_days: int = 30
       ) -> Dict[str, Any]:
           """Prever vulnerabilidades futuras"""
           
           if not self.vulnerability_trend_model:
               raise ValueError("Vulnerability trend model not trained")
           
           # Prepare current data
           recent_data = current_data.tail(30)  # Last 30 days
           time_series = self._prepare_time_series_data(recent_data)
           
           predictions = []
           current_sequence = time_series[-30:].values.reshape(1, 30, -1)
           
           # Generate predictions for each day
           for _ in range(prediction_days):
               next_pred = self.vulnerability_trend_model.predict(current_sequence, verbose=0)
               predictions.append(next_pred[0][0])
               
               # Update sequence with prediction
               current_sequence = np.roll(current_sequence, -1, axis=1)
               current_sequence[0, -1, 0] = next_pred[0][0]
           
           # Generate prediction dates
           start_date = datetime.now() + timedelta(days=1)
           prediction_dates = [
               start_date + timedelta(days=i) for i in range(prediction_days)
           ]
           
           return {
               'predictions': predictions,
               'dates': [d.isoformat() for d in prediction_dates],
               'confidence_intervals': self._calculate_confidence_intervals(predictions),
               'trend_analysis': self._analyze_trend(predictions)
           }
       
       async def train_exploit_prediction_model(self, vulnerability_data: pd.DataFrame):
           """Treinar modelo para prever probabilidade de exploit"""
           
           # Features for exploit prediction
           features = self._extract_exploit_features(vulnerability_data)
           
           # Target: whether exploit was found within 30 days
           targets = vulnerability_data['exploit_found_within_30d'].astype(int)
           
           # Split data
           X_train, X_test, y_train, y_test = train_test_split(
               features, targets, test_size=0.2, random_state=42, stratify=targets
           )
           
           # Scale features
           X_train_scaled = self.scaler.fit_transform(X_train)
           X_test_scaled = self.scaler.transform(X_test)
           
           # Train gradient boosting classifier
           model = GradientBoostingClassifier(
               n_estimators=100,
               learning_rate=0.1,
               max_depth=6,
               random_state=42
           )
           
           model.fit(X_train_scaled, y_train)
           
           # Cross-validation
           cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
           
           # Predictions
           y_pred = model.predict(X_test_scaled)
           y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
           
           print("Exploit Prediction Model Performance:")
           print(classification_report(y_test, y_pred))
           print(f"Cross-validation scores: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
           
           self.exploit_prediction_model = model
           
           return model
       
       async def predict_exploit_likelihood(
           self, 
           vulnerability: Dict[str, Any]
       ) -> Dict[str, Any]:
           """Prever probabilidade de exploit para uma vulnerabilidade"""
           
           if not self.exploit_prediction_model:
               raise ValueError("Exploit prediction model not trained")
           
           # Extract features
           df = pd.DataFrame([vulnerability])
           features = self._extract_exploit_features(df)
           features_scaled = self.scaler.transform(features)
           
           # Predict probability
           exploit_probability = self.exploit_prediction_model.predict_proba(features_scaled)[0, 1]
           
           # Get feature importance for explanation
           feature_importance = self.exploit_prediction_model.feature_importances_
           
           return {
               'exploit_probability': float(exploit_probability),
               'risk_level': self._categorize_exploit_risk(exploit_probability),
               'key_factors': self._identify_key_factors(features.iloc[0], feature_importance),
               'recommended_actions': self._generate_exploit_recommendations(vulnerability, exploit_probability)
           }
       
       def _prepare_time_series_data(self, data: pd.DataFrame) -> pd.DataFrame:
           """Preparar dados para análise de série temporal"""
           
           # Group by date and count vulnerabilities
           daily_counts = data.groupby(data['discovered_at'].dt.date).size().reset_index()
           daily_counts.columns = ['date', 'vulnerability_count']
           
           # Create date range to fill missing dates
           date_range = pd.date_range(
               start=daily_counts['date'].min(),
               end=daily_counts['date'].max(),
               freq='D'
           )
           
           # Reindex and fill missing values
           full_range = pd.DataFrame({'date': date_range.date})
           time_series = full_range.merge(daily_counts, on='date', how='left')
           time_series['vulnerability_count'] = time_series['vulnerability_count'].fillna(0)
           
           # Add additional features
           time_series['day_of_week'] = pd.to_datetime(time_series['date']).dt.dayofweek
           time_series['month'] = pd.to_datetime(time_series['date']).dt.month
           time_series['is_weekend'] = time_series['day_of_week'].isin([5, 6]).astype(int)
           
           # Rolling averages
           time_series['ma_7'] = time_series['vulnerability_count'].rolling(window=7).mean()
           time_series['ma_30'] = time_series['vulnerability_count'].rolling(window=30).mean()
           
           return time_series.fillna(0)
       
       def _create_sequences(self, data: pd.DataFrame, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
           """Criar sequências para LSTM"""
           
           # Select features for sequences
           feature_cols = ['vulnerability_count', 'day_of_week', 'month', 'is_weekend', 'ma_7', 'ma_30']
           features = data[feature_cols].values
           
           X, y = [], []
           for i in range(sequence_length, len(features)):
               X.append(features[i-sequence_length:i])
               y.append(features[i, 0])  # Predict vulnerability_count
           
           return np.array(X), np.array(y)
       
       def _extract_exploit_features(self, data: pd.DataFrame) -> pd.DataFrame:
           """Extrair features para predição de exploit"""
           
           features = pd.DataFrame()
           
           # CVSS features
           features['cvss_score'] = data['cvss_score'].fillna(0)
           features['cvss_exploitability'] = data['cvss_exploitability_score'].fillna(0)
           features['cvss_impact'] = data['cvss_impact_score'].fillna(0)
           
           # Vulnerability characteristics
           features['is_remote'] = (data['attack_vector'] == 'network').astype(int)
           features['low_complexity'] = (data['attack_complexity'] == 'low').astype(int)
           features['no_auth_required'] = (~data['authentication_required']).astype(int)
           features['no_user_interaction'] = (~data['user_interaction_required']).astype(int)
           
           # Technology factors
           features['is_web_app'] = data['vulnerability_type'].str.contains('web', case=False, na=False).astype(int)
           features['is_popular_tech'] = data['affected_component'].isin([
               'apache', 'nginx', 'mysql', 'wordpress', 'drupal', 'joomla'
           ]).astype(int)
           
           # Temporal features
           features['days_since_published'] = (
               datetime.now() - pd.to_datetime(data['published_date'])
           ).dt.days.fillna(999)
           
           features['is_recent'] = (features['days_since_published'] <= 30).astype(int)
           
           # Vendor response
           features['patch_available'] = data['patch_available'].astype(int)
           features['days_to_patch'] = data['days_to_patch'].fillna(999)
           
           # Public attention
           features['has_cve'] = data['cve_id'].notna().astype(int)
           features['in_top_vulns'] = data['in_owasp_top10'].fillna(False).astype(int)
           
           return features
       
       def _categorize_exploit_risk(self, probability: float) -> str:
           """Categorizar risco de exploit"""
           
           if probability >= 0.8:
               return "Very High"
           elif probability >= 0.6:
               return "High"
           elif probability >= 0.4:
               return "Medium"
           elif probability >= 0.2:
               return "Low"
           else:
               return "Very Low"
       
       def _identify_key_factors(self, features: pd.Series, importance: np.ndarray) -> List[str]:
           """Identificar fatores-chave para a predição"""
           
           feature_names = features.index.tolist()
           
           # Get top 3 most important features
           top_indices = np.argsort(importance)[-3:][::-1]
           
           key_factors = []
           for idx in top_indices:
               feature_name = feature_names[idx]
               feature_value = features.iloc[idx]
               importance_score = importance[idx]
               
               # Generate human-readable explanation
               factor_desc = self._explain_feature(feature_name, feature_value, importance_score)
               key_factors.append(factor_desc)
           
           return key_factors
       
       def _explain_feature(self, feature_name: str, value: Any, importance: float) -> str:
           """Explicar feature de forma legível"""
           
           explanations = {
               'cvss_score': f"CVSS Score ({value:.1f}) - {importance:.1%} importance",
               'is_remote': f"Remote exploitability ({'Yes' if value else 'No'}) - {importance:.1%} importance",
               'low_complexity': f"Low attack complexity ({'Yes' if value else 'No'}) - {importance:.1%} importance",
               'no_auth_required': f"No authentication required ({'Yes' if value else 'No'}) - {importance:.1%} importance",
               'is_recent': f"Recently published ({'Yes' if value else 'No'}) - {importance:.1%} importance",
               'is_web_app': f"Web application vulnerability ({'Yes' if value else 'No'}) - {importance:.1%} importance"
           }
           
           return explanations.get(feature_name, f"{feature_name}: {value} - {importance:.1%} importance")
       
       async def generate_security_forecast(
           self, 
           organization_data: Dict[str, Any],
           forecast_period: int = 90
       ) -> Dict[str, Any]:
           """Gerar forecast completo de segurança"""
           
           forecast = {
               'forecast_period_days': forecast_period,
               'generated_at': datetime.now().isoformat(),
               'vulnerability_trends': {},
               'risk_assessment': {},
               'recommendations': []
           }
           
           # Predict vulnerability trends
           vuln_predictions = await self.predict_future_vulnerabilities(
               organization_data['historical_vulnerabilities'],
               prediction_days=forecast_period
           )
           forecast['vulnerability_trends'] = vuln_predictions
           
           # Risk assessment
           current_vulns = organization_data.get('current_vulnerabilities', [])
           total_risk_score = 0
           high_risk_vulns = 0
           
           for vuln in current_vulns:
               exploit_analysis = await self.predict_exploit_likelihood(vuln)
               if exploit_analysis['exploit_probability'] > 0.6:
                   high_risk_vulns += 1
               total_risk_score += exploit_analysis['exploit_probability'] * vuln.get('cvss_score', 0)
           
           forecast['risk_assessment'] = {
               'current_risk_score': total_risk_score,
               'high_risk_vulnerabilities': high_risk_vulns,
               'projected_risk_trend': self._calculate_risk_trend(vuln_predictions),
               'risk_categories': self._categorize_risks(current_vulns)
           }
           
           # Generate recommendations
           forecast['recommendations'] = self._generate_forecast_recommendations(
               vuln_predictions, forecast['risk_assessment']
           )
           
           return forecast
   ```

**Deliverables**:
- [ ] Modelos preditivos para tendências
- [ ] Predição de likelihood de exploits
- [ ] Sistema de forecasting de segurança
- [ ] Análise preditiva de riscos

## 🧪 Testes do Sprint

### ML Model Tests
```python
# tests/test_ml_models.py
import pytest
import pandas as pd
import numpy as np
from services.ml_service import VulnerabilityMLService

@pytest.fixture
def sample_vulnerability_data():
    return pd.DataFrame({
        'cvss_score': [7.5, 9.8, 4.3, 6.1],
        'severity': ['high', 'critical', 'medium', 'medium'],
        'vulnerability_type': ['xss', 'rce', 'info_disclosure', 'sqli'],
        'network_accessible': [True, True, False, True],
        'exploit_available': [True, True, False, False],
        'is_false_positive': [False, False, True, False]
    })

@pytest.mark.asyncio
async def test_false_positive_detection(sample_vulnerability_data):
    ml_service = VulnerabilityMLService()
    
    # Train model
    model = await ml_service.train_false_positive_detector(sample_vulnerability_data)
    
    assert model is not None
    assert hasattr(ml_service, 'false_positive_model')

@pytest.mark.asyncio
async def test_vulnerability_analysis_prediction(sample_vulnerability_data):
    ml_service = VulnerabilityMLService()
    
    # Train models first
    await ml_service.train_false_positive_detector(sample_vulnerability_data)
    await ml_service.train_risk_scoring_model(sample_vulnerability_data)
    
    # Test prediction
    test_vuln = {
        'cvss_score': 8.5,
        'severity': 'high',
        'vulnerability_type': 'rce',
        'network_accessible': True,
        'exploit_available': True
    }
    
    prediction = await ml_service.predict_vulnerability_analysis(test_vuln)
    
    assert isinstance(prediction.is_false_positive, bool)
    assert 0 <= prediction.confidence <= 1
    assert 0 <= prediction.risk_score <= 100
    assert 1 <= prediction.priority_level <= 5
```

### Correlation Tests
```python
# tests/test_correlation.py
import pytest
from services.correlation_service import VulnerabilityCorrelationService

@pytest.mark.asyncio
async def test_vulnerability_correlation():
    correlation_service = VulnerabilityCorrelationService()
    
    vulnerabilities = [
        {
            'id': 'vuln1',
            'affected_url': 'https://example.com',
            'vulnerability_type': 'xss',
            'cvss_score': 7.5
        },
        {
            'id': 'vuln2', 
            'affected_url': 'https://example.com',
            'vulnerability_type': 'xss',
            'cvss_score': 7.2
        }
    ]
    
    analysis = await correlation_service.analyze_vulnerability_correlations(vulnerabilities)
    
    assert 'clusters' in analysis
    assert 'attack_paths' in analysis
    assert 'correlation_matrix' in analysis
```

## 📊 Métricas de Sucesso

### ML Performance
- [ ] **False Positive Detection**: >85% precision
- [ ] **Risk Scoring Accuracy**: <15% MAE
- [ ] **Exploit Prediction**: >80% AUC-ROC
- [ ] **Model Training Time**: <30 minutes

### Correlation Quality
- [ ] **Cluster Coherence**: >70% within-cluster similarity
- [ ] **Attack Path Accuracy**: >80% manual validation
- [ ] **Pattern Recognition**: >75% pattern detection rate
- [ ] **Processing Speed**: <10 seconds for 1000 vulnerabilities

### Predictive Analytics
- [ ] **Trend Prediction**: <20% MAPE
- [ ] **Forecast Horizon**: 30-90 days reliable
- [ ] **Confidence Intervals**: 95% coverage
- [ ] **Update Frequency**: Daily model updates

---

**Sprint 5 eleva ScanIA a um patamar de análise de cybersegurança com inteligência artificial de ponta, oferecendo insights preditivos únicos no mercado.**