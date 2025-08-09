"""
Scan management endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.scan import Scan, ScanStatus
from app.models.vulnerability import Vulnerability
from app.schemas.scan import (
    ScanCreateRequest, ScanResponse, ScanListResponse, 
    ScanUpdateRequest, ScanStatusResponse, ScanStatsResponse
)
from app.core.logging_simple import get_logger

router = APIRouter(prefix="/scans", tags=["scans"])
logger = get_logger(__name__)


class ScanService:
    """Service for scan management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_scan(self, user: User, request: ScanCreateRequest) -> Scan:
        """Create a new scan"""
        # Check user scan limits
        if not user.can_perform_scan():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Limite de scans atingido ou conta bloqueada"
            )
        
        # Get next scan number
        result = await self.db.execute(
            select(func.max(Scan.scan_number)).where(Scan.user_id == user.id)
        )
        max_scan_number = result.scalar() or 0
        
        # Create scan
        scan = Scan(
            user_id=user.id,
            target_url=str(request.target_url),
            scan_types=[scan_type.value for scan_type in request.scan_types],
            options=request.options,
            environment_type=request.environment_type,
            scan_number=max_scan_number + 1
        )
        
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)
        
        logger.info(f"Scan created: {scan.id} for user {user.email}")
        return scan
    
    async def get_scan(self, scan_id: str, user: User) -> Optional[Scan]:
        """Get scan by ID"""
        result = await self.db.execute(
            select(Scan)
            .options(selectinload(Scan.vulnerabilities))
            .where(
                and_(
                    Scan.id == scan_id,
                    Scan.user_id == user.id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_scans(
        self, 
        user: User, 
        page: int = 1, 
        per_page: int = 20,
        status_filter: Optional[ScanStatus] = None,
        target_filter: Optional[str] = None
    ) -> dict:
        """List user scans with pagination and filters"""
        
        # Build query
        query = select(Scan).where(Scan.user_id == user.id)
        
        if status_filter:
            query = query.where(Scan.status == status_filter)
        
        if target_filter:
            query = query.where(Scan.target_url.ilike(f"%{target_filter}%"))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(desc(Scan.created_at)).offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        scans = result.scalars().all()
        
        return {
            "scans": scans,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1
        }
    
    async def update_scan(self, scan_id: str, user: User, request: ScanUpdateRequest) -> Optional[Scan]:
        """Update scan"""
        scan = await self.get_scan(scan_id, user)
        if not scan:
            return None
        
        if request.status is not None:
            scan.status = request.status
            
            if request.status == ScanStatus.RUNNING and not scan.started_at:
                scan.started_at = datetime.utcnow()
            elif request.status == ScanStatus.COMPLETED:
                scan.completed_at = datetime.utcnow()
                if scan.started_at:
                    duration = scan.completed_at - scan.started_at
                    scan.duration_seconds = int(duration.total_seconds())
        
        if request.options is not None:
            scan.options.update(request.options)
        
        if request.error_message is not None:
            scan.error_message = request.error_message
        
        await self.db.commit()
        await self.db.refresh(scan)
        
        return scan
    
    async def delete_scan(self, scan_id: str, user: User) -> bool:
        """Delete scan and associated vulnerabilities"""
        scan = await self.get_scan(scan_id, user)
        if not scan:
            return False
        
        # Can only delete non-running scans
        if scan.status == ScanStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete running scan"
            )
        
        await self.db.delete(scan)
        await self.db.commit()
        
        logger.info(f"Scan deleted: {scan_id} by user {user.email}")
        return True
    
    async def get_scan_stats(self, user: User) -> dict:
        """Get user scan statistics"""
        # Basic counts
        result = await self.db.execute(
            select(
                func.count(Scan.id).label('total'),
                func.count().filter(Scan.status == ScanStatus.RUNNING).label('running'),
                func.count().filter(Scan.status == ScanStatus.COMPLETED).label('completed'),
                func.count().filter(Scan.status == ScanStatus.FAILED).label('failed'),
                func.avg(Scan.duration_seconds).label('avg_duration')
            ).where(Scan.user_id == user.id)
        )
        stats = result.first()
        
        # Scans by day (last 30 days)
        from datetime import date, timedelta
        thirty_days_ago = date.today() - timedelta(days=30)
        
        result = await self.db.execute(
            select(
                func.date(Scan.created_at).label('scan_date'),
                func.count(Scan.id).label('count')
            )
            .where(
                and_(
                    Scan.user_id == user.id,
                    func.date(Scan.created_at) >= thirty_days_ago
                )
            )
            .group_by(func.date(Scan.created_at))
            .order_by(func.date(Scan.created_at))
        )
        
        scans_by_day = {str(row.scan_date): row.count for row in result}
        
        return {
            "total_scans": stats.total or 0,
            "running_scans": stats.running or 0,
            "completed_scans": stats.completed or 0,
            "failed_scans": stats.failed or 0,
            "avg_duration_minutes": (stats.avg_duration or 0) / 60.0,
            "scans_by_day": scans_by_day,
            "vulnerability_trends": {}  # Will be populated when we have vulnerability data
        }


async def start_scan_job(scan: Scan, db: AsyncSession):
    """Start scan background job"""
    from app.services.scanner_engine import ScanJobManager
    
    # Create scan job manager
    job_manager = ScanJobManager(db)
    
    # Start scan execution in background
    # In production, this would be handled by Celery
    import asyncio
    asyncio.create_task(job_manager.start_scan_job(str(scan.id)))
    
    logger.info(f"Scan job started: {scan.id}")


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    request: ScanCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new security scan"""
    logger.info(f"=== CREATE SCAN ENDPOINT START ===")
    logger.info(f"User: {current_user.email}")
    logger.info(f"Request: target_url={request.target_url}, scan_types={request.scan_types}")
    
    service = ScanService(db)
    
    try:
        logger.info("=== STEP 1: Creating scan via ScanService ===")
        scan = await service.create_scan(current_user, request)
        logger.info(f"=== STEP 1: Scan created successfully: {scan.id} ===")
        
        logger.info("=== STEP 2: Adding background task ===")
        # Start scan in background
        background_tasks.add_task(start_scan_job, scan, db)
        logger.info("=== STEP 2: Background task added ===")
        
        logger.info("=== STEP 3: Creating ScanResponse ===")
        scan_response = ScanResponse(
            id=str(scan.id),
            target_url=scan.target_url,
            scan_types=scan.scan_types,
            status=scan.status,
            options=scan.options,
            environment_type=scan.environment_type,
            scan_number=scan.scan_number,
            created_at=scan.created_at,
            updated_at=scan.updated_at,
            vulnerability_summary={},  # Empty for new scan
            total_vulnerabilities=0,   # Zero for new scan
            risk_score=0.0            # Zero for new scan
        )
        logger.info("=== STEP 3: ScanResponse created successfully ===")
        
        logger.info("=== CREATE SCAN ENDPOINT SUCCESS ===")
        return scan_response
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in create_scan: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR in create_scan endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DEBUG SCAN ERROR: {str(e)} | Type: {type(e).__name__}"
        )


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    status: Optional[ScanStatus] = Query(None, description="Filtrar por status"),
    target: Optional[str] = Query(None, description="Filtrar por URL alvo"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List user scans"""
    service = ScanService(db)
    
    result = await service.list_scans(
        current_user, 
        page=page, 
        per_page=per_page,
        status_filter=status,
        target_filter=target
    )
    
    scan_responses = []
    for scan in result["scans"]:
        scan_responses.append(ScanResponse(
            id=str(scan.id),
            target_url=scan.target_url,
            scan_types=scan.scan_types,
            status=scan.status,
            options=scan.options,
            environment_type=scan.environment_type,
            scan_number=scan.scan_number,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            duration_seconds=scan.duration_seconds,
            celery_job_id=scan.celery_job_id,
            error_message=scan.error_message,
            created_at=scan.created_at,
            updated_at=scan.updated_at,
            vulnerability_summary=scan.vulnerability_summary,
            total_vulnerabilities=scan.total_vulnerabilities,
            risk_score=scan.calculate_risk_score()
        ))
    
    return ScanListResponse(
        scans=scan_responses,
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        has_next=result["has_next"],
        has_prev=result["has_prev"]
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get scan details"""
    service = ScanService(db)
    scan = await service.get_scan(scan_id, current_user)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan não encontrado"
        )
    
    return ScanResponse(
        id=str(scan.id),
        target_url=scan.target_url,
        scan_types=scan.scan_types,
        status=scan.status,
        options=scan.options,
        environment_type=scan.environment_type,
        scan_number=scan.scan_number,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.duration_seconds,
        celery_job_id=scan.celery_job_id,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        vulnerability_summary=scan.vulnerability_summary,
        total_vulnerabilities=scan.total_vulnerabilities,
        risk_score=scan.calculate_risk_score()
    )


@router.put("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: str,
    request: ScanUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update scan"""
    service = ScanService(db)
    scan = await service.update_scan(scan_id, current_user, request)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan não encontrado"
        )
    
    return ScanResponse(
        id=str(scan.id),
        target_url=scan.target_url,
        scan_types=scan.scan_types,
        status=scan.status,
        options=scan.options,
        environment_type=scan.environment_type,
        scan_number=scan.scan_number,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.duration_seconds,
        celery_job_id=scan.celery_job_id,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        vulnerability_summary=scan.vulnerability_summary,
        total_vulnerabilities=scan.total_vulnerabilities,
        risk_score=scan.calculate_risk_score()
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete scan"""
    service = ScanService(db)
    deleted = await service.delete_scan(scan_id, current_user)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan não encontrado"
        )


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get real-time scan status"""
    service = ScanService(db)
    scan = await service.get_scan(scan_id, current_user)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan não encontrado"
        )
    
    # Calculate progress based on status
    progress = 0.0
    message = "Aguardando início"
    
    if scan.status == ScanStatus.RUNNING:
        progress = 50.0  # Simplified progress calculation
        message = "Executando scan..."
    elif scan.status == ScanStatus.COMPLETED:
        progress = 100.0
        message = "Scan concluído"
    elif scan.status == ScanStatus.FAILED:
        progress = 0.0
        message = f"Falha no scan: {scan.error_message or 'Erro desconhecido'}"
    elif scan.status == ScanStatus.CANCELLED:
        progress = 0.0
        message = "Scan cancelado"
    
    return ScanStatusResponse(
        id=str(scan.id),
        status=scan.status,
        progress=progress,
        message=message,
        started_at=scan.started_at
    )


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel running scan"""
    service = ScanService(db)
    scan = await service.get_scan(scan_id, current_user)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan não encontrado"
        )
    
    if scan.status != ScanStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas scans em execução podem ser cancelados"
        )
    
    # Update scan status
    update_request = ScanUpdateRequest(status=ScanStatus.CANCELLED)
    await service.update_scan(scan_id, current_user, update_request)
    
    return {"message": "Scan cancelado com sucesso"}


@router.get("/stats/summary", response_model=ScanStatsResponse)
async def get_scan_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user scan statistics"""
    service = ScanService(db)
    stats = await service.get_scan_stats(current_user)
    
    return ScanStatsResponse(**stats)