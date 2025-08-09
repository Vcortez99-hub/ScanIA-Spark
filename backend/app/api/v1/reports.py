"""
Report generation and management endpoints
"""

import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_async_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.scan import Scan, ScanStatus
from app.models.report import Report, ReportFormat, ReportStatus
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportCreateRequest, ReportResponse, ReportListResponse,
    ReportStatusResponse, ReportStatsResponse
)
from app.core.logging_simple import get_logger

router = APIRouter(prefix="/reports", tags=["reports"])
logger = get_logger(__name__)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate a new report for a completed scan"""
    logger.info(f"Creating report for scan {request.scan_id} by user {current_user.email}")
    
    try:
        # Verify scan exists and belongs to user
        result = await db.execute(
            select(Scan).where(
                and_(
                    Scan.id == request.scan_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        scan = result.scalar_one_or_none()
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan não encontrado"
            )
        
        # Check if scan is completed
        if scan.status != ScanStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan deve estar completo para gerar relatório"
            )
        
        # Check if user has reached report limit
        # This could be implemented based on user plan
        
        # Create report service
        report_service = ReportService(db)
        
        # Generate report
        report_id = await report_service.generate_report(
            scan_id=request.scan_id,
            report_format=request.format,
            report_type=request.report_type
        )
        
        # Get the created report
        report = await report_service.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar relatório"
            )
        
        logger.info(f"Report {report_id} created successfully")
        
        return ReportResponse(
            id=str(report.id),
            scan_id=str(report.scan_id),
            format=report.format,
            status=report.status,
            title=report.title,
            description=report.description,
            file_size=report.file_size,
            created_at=report.created_at,
            generated_at=report.generated_at,
            download_url=f"/api/v1/reports/{report.id}/download" if report.status == ReportStatus.COMPLETED else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    scan_id: Optional[str] = Query(None, description="Filtrar por ID do scan"),
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List user reports with pagination and filtering"""
    
    try:
        # Build query - only reports for scans owned by the user
        query = select(Report).join(Scan).where(Scan.user_id == current_user.id)
        
        # Filter by scan ID if provided
        if scan_id:
            query = query.where(Report.scan_id == scan_id)
        
        # Count total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(Report.created_at.desc()).offset(offset).limit(per_page)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        # Convert to response format
        report_responses = []
        for report in reports:
            report_responses.append(ReportResponse(
                id=str(report.id),
                scan_id=str(report.scan_id),
                format=report.format,
                status=report.status,
                title=report.title,
                description=report.description,
                file_size=report.file_size,
                created_at=report.created_at,
                generated_at=report.generated_at,
                download_url=f"/api/v1/reports/{report.id}/download" if report.status == ReportStatus.COMPLETED else None
            ))
        
        return ReportListResponse(
            reports=report_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar relatórios"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get report details"""
    
    try:
        # Get report and verify ownership
        result = await db.execute(
            select(Report)
            .join(Scan)
            .where(
                and_(
                    Report.id == report_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        return ReportResponse(
            id=str(report.id),
            scan_id=str(report.scan_id),
            format=report.format,
            status=report.status,
            title=report.title,
            description=report.description,
            file_size=report.file_size,
            created_at=report.created_at,
            generated_at=report.generated_at,
            download_url=f"/api/v1/reports/{report.id}/download" if report.status == ReportStatus.COMPLETED else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter relatório"
        )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get report generation status"""
    
    try:
        # Get report and verify ownership
        result = await db.execute(
            select(Report)
            .join(Scan)
            .where(
                and_(
                    Report.id == report_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Calculate progress based on status
        progress = 0.0
        message = "Pendente"
        
        if report.status == ReportStatus.GENERATING:
            progress = 50.0
            message = "Gerando relatório..."
        elif report.status == ReportStatus.COMPLETED:
            progress = 100.0
            message = "Relatório concluído"
        elif report.status == ReportStatus.FAILED:
            progress = 0.0
            message = f"Falha na geração: {report.error_message or 'Erro desconhecido'}"
        
        return ReportStatusResponse(
            id=str(report.id),
            status=report.status,
            progress=progress,
            message=message,
            file_size=report.file_size,
            generated_at=report.generated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter status do relatório"
        )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Download a completed report"""
    
    try:
        # Get report and verify ownership
        result = await db.execute(
            select(Report)
            .join(Scan)
            .where(
                and_(
                    Report.id == report_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Check if report is completed and file exists
        if report.status != ReportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relatório ainda não está pronto para download"
            )
        
        if not report.file_path or not Path(report.file_path).exists():
            logger.error(f"Report file not found: {report.file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo do relatório não encontrado"
            )
        
        # Update download count
        report.download_count += 1
        await db.commit()
        
        # Determine filename
        filename = f"scania_report_{report.scan.scan_number}_{report.template_name}.{report.format.value}"
        
        # Return file
        return FileResponse(
            path=report.file_path,
            filename=filename,
            media_type=report.mime_type or 'application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao fazer download do relatório"
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a report"""
    
    try:
        # Get report and verify ownership
        result = await db.execute(
            select(Report)
            .join(Scan)
            .where(
                and_(
                    Report.id == report_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Delete file if exists
        if report.file_path and Path(report.file_path).exists():
            try:
                os.remove(report.file_path)
                logger.info(f"Deleted report file: {report.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete report file: {e}")
        
        # Delete database record
        await db.delete(report)
        await db.commit()
        
        logger.info(f"Report deleted: {report_id} by user {current_user.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar relatório"
        )


@router.get("/scan/{scan_id}", response_model=List[ReportResponse])
async def list_scan_reports(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List all reports for a specific scan"""
    
    try:
        # Verify scan ownership
        result = await db.execute(
            select(Scan).where(
                and_(
                    Scan.id == scan_id,
                    Scan.user_id == current_user.id
                )
            )
        )
        scan = result.scalar_one_or_none()
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan não encontrado"
            )
        
        # Get scan reports
        result = await db.execute(
            select(Report)
            .where(Report.scan_id == scan_id)
            .order_by(Report.created_at.desc())
        )
        reports = result.scalars().all()
        
        # Convert to response format
        report_responses = []
        for report in reports:
            report_responses.append(ReportResponse(
                id=str(report.id),
                scan_id=str(report.scan_id),
                format=report.format,
                status=report.status,
                title=report.title,
                description=report.description,
                file_size=report.file_size,
                created_at=report.created_at,
                generated_at=report.generated_at,
                download_url=f"/api/v1/reports/{report.id}/download" if report.status == ReportStatus.COMPLETED else None
            ))
        
        return report_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing scan reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar relatórios do scan"
        )


@router.get("/stats/summary", response_model=ReportStatsResponse)
async def get_report_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user report statistics"""
    
    try:
        from sqlalchemy import func
        
        # Basic report counts
        result = await db.execute(
            select(
                func.count(Report.id).label('total'),
                func.count().filter(Report.status == ReportStatus.COMPLETED).label('completed'),
                func.count().filter(Report.status == ReportStatus.GENERATING).label('generating'),
                func.count().filter(Report.status == ReportStatus.FAILED).label('failed'),
                func.sum(Report.file_size).label('total_size'),
                func.sum(Report.download_count).label('total_downloads')
            )
            .join(Scan)
            .where(Scan.user_id == current_user.id)
        )
        stats = result.first()
        
        # Reports by format
        result = await db.execute(
            select(Report.format, func.count(Report.id))
            .join(Scan)
            .where(Scan.user_id == current_user.id)
            .group_by(Report.format)
        )
        format_counts = {format.value: count for format, count in result}
        
        # Reports by status
        result = await db.execute(
            select(Report.status, func.count(Report.id))
            .join(Scan)
            .where(Scan.user_id == current_user.id)
            .group_by(Report.status)
        )
        status_counts = {status.value: count for status, count in result}
        
        return ReportStatsResponse(
            total_reports=stats.total or 0,
            completed_reports=stats.completed or 0,
            generating_reports=stats.generating or 0,
            failed_reports=stats.failed or 0,
            total_file_size_mb=(stats.total_size or 0) / (1024 * 1024),
            total_downloads=stats.total_downloads or 0,
            reports_by_format=format_counts,
            reports_by_status=status_counts
        )
        
    except Exception as e:
        logger.error(f"Error getting report stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter estatísticas de relatórios"
        )