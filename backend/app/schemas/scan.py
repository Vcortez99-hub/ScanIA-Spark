"""
Scan schemas
"""

from pydantic import BaseModel, HttpUrl, validator, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.scan import ScanStatus


class ScanTypeEnum(str, Enum):
    OWASP_ZAP = "owasp_zap"
    NMAP = "nmap"
    NIKTO = "nikto"
    SQLMAP = "sqlmap"
    XSS_HUNTER = "xss_hunter"
    CUSTOM = "custom"


class ScanCreateRequest(BaseModel):
    target_url: HttpUrl = Field(..., description="URL alvo para o scan")
    scan_types: List[ScanTypeEnum] = Field(..., description="Tipos de scan a serem executados")
    options: Dict[str, Any] = Field(default_factory=dict, description="Opções específicas do scan")
    environment_type: str = Field(default="production", description="Tipo de ambiente")
    
    @validator('target_url')
    def validate_target_url(cls, v):
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL deve começar com http:// ou https://')
        return v
    
    @validator('scan_types')
    def validate_scan_types(cls, v):
        if not v:
            raise ValueError('Pelo menos um tipo de scan deve ser selecionado')
        return v


class ScanResponse(BaseModel):
    id: str
    target_url: str
    scan_types: List[str]
    status: ScanStatus
    options: Dict[str, Any]
    environment_type: str
    scan_number: Optional[int] = None
    
    # Execution details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    # Job tracking
    celery_job_id: Optional[str] = None
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Vulnerability summary
    vulnerability_summary: Dict[str, int] = Field(default_factory=dict)
    total_vulnerabilities: int = 0
    risk_score: float = 0.0
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ScanUpdateRequest(BaseModel):
    status: Optional[ScanStatus] = None
    options: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ScanStatusResponse(BaseModel):
    id: str
    status: ScanStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    message: str = ""
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ScanStatsResponse(BaseModel):
    total_scans: int
    running_scans: int
    completed_scans: int
    failed_scans: int
    avg_duration_minutes: float
    scans_by_day: Dict[str, int]
    vulnerability_trends: Dict[str, Dict[str, int]]