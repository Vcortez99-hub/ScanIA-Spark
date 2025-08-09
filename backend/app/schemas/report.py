"""
Report schemas for request/response validation
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.report import ReportFormat, ReportStatus


class ReportCreateRequest(BaseModel):
    """Request to create a new report"""
    scan_id: str = Field(..., description="ID do scan para gerar relatório")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Formato do relatório")
    report_type: str = Field(default="executive", description="Tipo de relatório (executive, technical)")
    
    class Config:
        json_encoders = {
            ReportFormat: lambda v: v.value
        }


class ReportResponse(BaseModel):
    """Report response schema"""
    id: str = Field(..., description="ID único do relatório")
    scan_id: str = Field(..., description="ID do scan")
    format: ReportFormat = Field(..., description="Formato do relatório")
    status: ReportStatus = Field(..., description="Status da geração")
    title: str = Field(..., description="Título do relatório")
    description: Optional[str] = Field(None, description="Descrição do relatório")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    created_at: datetime = Field(..., description="Data de criação")
    generated_at: Optional[datetime] = Field(None, description="Data de geração")
    download_url: Optional[str] = Field(None, description="URL para download")
    
    class Config:
        from_attributes = True
        json_encoders = {
            ReportFormat: lambda v: v.value,
            ReportStatus: lambda v: v.value
        }


class ReportListResponse(BaseModel):
    """Paginated list of reports"""
    reports: List[ReportResponse] = Field(..., description="Lista de relatórios")
    total: int = Field(..., description="Total de relatórios")
    page: int = Field(..., description="Página atual")
    per_page: int = Field(..., description="Itens por página")
    has_next: bool = Field(..., description="Tem próxima página")
    has_prev: bool = Field(..., description="Tem página anterior")


class ReportStatusResponse(BaseModel):
    """Report generation status response"""
    id: str = Field(..., description="ID do relatório")
    status: ReportStatus = Field(..., description="Status da geração")
    progress: float = Field(..., description="Progresso da geração (0-100)")
    message: str = Field(..., description="Mensagem de status")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    generated_at: Optional[datetime] = Field(None, description="Data de geração")
    
    class Config:
        json_encoders = {
            ReportStatus: lambda v: v.value
        }


class ReportStatsResponse(BaseModel):
    """Report statistics response"""
    total_reports: int = Field(..., description="Total de relatórios")
    completed_reports: int = Field(..., description="Relatórios concluídos")
    generating_reports: int = Field(..., description="Relatórios sendo gerados")
    failed_reports: int = Field(..., description="Relatórios com falha")
    total_file_size_mb: float = Field(..., description="Tamanho total dos arquivos em MB")
    total_downloads: int = Field(..., description="Total de downloads")
    reports_by_format: Dict[str, int] = Field(..., description="Relatórios por formato")
    reports_by_status: Dict[str, int] = Field(..., description="Relatórios por status")


# Report template configurations
class ReportTemplate(BaseModel):
    """Report template configuration"""
    name: str = Field(..., description="Nome do template")
    display_name: str = Field(..., description="Nome para exibição")
    description: str = Field(..., description="Descrição do template")
    supported_formats: List[ReportFormat] = Field(..., description="Formatos suportados")
    estimated_generation_time: int = Field(..., description="Tempo estimado de geração em segundos")


# Predefined report templates
REPORT_TEMPLATES = [
    ReportTemplate(
        name="executive",
        display_name="Relatório Executivo",
        description="Resumo executivo com gráficos e principais vulnerabilidades",
        supported_formats=[ReportFormat.PDF],
        estimated_generation_time=30
    ),
    ReportTemplate(
        name="technical",
        display_name="Relatório Técnico",
        description="Relatório técnico detalhado com todas as vulnerabilidades",
        supported_formats=[ReportFormat.PDF],
        estimated_generation_time=60
    ),
    ReportTemplate(
        name="compliance",
        display_name="Relatório de Compliance",
        description="Relatório focado em conformidade com padrões de segurança",
        supported_formats=[ReportFormat.PDF],
        estimated_generation_time=45
    )
]


class ReportTemplateResponse(BaseModel):
    """Report template list response"""
    templates: List[ReportTemplate] = Field(..., description="Templates disponíveis")
    
    class Config:
        json_encoders = {
            ReportFormat: lambda v: v.value
        }