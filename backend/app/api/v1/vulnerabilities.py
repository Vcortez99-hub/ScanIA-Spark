"""
Vulnerability management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from app.schemas.vulnerability import (
    VulnerabilityCreateRequest, VulnerabilityResponse, VulnerabilityListResponse,
    VulnerabilityUpdateRequest, VulnerabilityStatsResponse, VulnerabilityExportRequest,
    FalsePositiveRequest, RemediationRequest
)
from app.core.logging_simple import get_logger

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])
logger = get_logger(__name__)


class VulnerabilityService:
    """Service for vulnerability management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_vulnerability(self, user: User, request: VulnerabilityCreateRequest) -> Vulnerability:
        """Create a new vulnerability"""
        # Verify scan belongs to user
        result = await self.db.execute(
            select(Scan).where(
                and_(
                    Scan.id == request.scan_id,
                    Scan.user_id == user.id
                )
            )
        )
        scan = result.scalar_one_or_none()
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan não encontrado"
            )
        
        # Create vulnerability
        vulnerability = Vulnerability(
            scan_id=request.scan_id,
            vulnerability_id=request.vulnerability_id,
            cve_id=request.cve_id,
            severity=request.severity,
            cvss_score=request.cvss_score,
            cvss_vector=request.cvss_vector,
            title=request.title,
            description=request.description,
            solution=request.solution,
            references=request.references,
            affected_url=request.affected_url,
            affected_component=request.affected_component,
            affected_parameter=request.affected_parameter,
            vulnerability_type=request.vulnerability_type,
            attack_vector=request.attack_vector,
            attack_complexity=request.attack_complexity,
            evidence=request.evidence,
            proof_of_concept=request.proof_of_concept
        )
        
        self.db.add(vulnerability)
        await self.db.commit()
        await self.db.refresh(vulnerability)
        
        logger.info(f"Vulnerability created: {vulnerability.id} for scan {request.scan_id}")
        return vulnerability
    
    async def get_vulnerability(self, vuln_id: str, user: User) -> Optional[Vulnerability]:
        """Get vulnerability by ID"""
        result = await self.db.execute(
            select(Vulnerability)
            .options(selectinload(Vulnerability.scan))
            .where(Vulnerability.id == vuln_id)
        )
        vulnerability = result.scalar_one_or_none()
        
        # Verify user owns the scan
        if vulnerability and vulnerability.scan.user_id != user.id:
            return None
        
        return vulnerability
    
    async def list_vulnerabilities(
        self,
        user: User,
        page: int = 1,
        per_page: int = 20,
        scan_id: Optional[str] = None,
        severity_filter: Optional[List[VulnerabilitySeverity]] = None,
        status_filter: Optional[List[VulnerabilityStatus]] = None,
        search: Optional[str] = None
    ) -> dict:
        """List vulnerabilities with filters and pagination"""
        
        # Base query - join with scans to filter by user
        query = select(Vulnerability).join(Scan).where(Scan.user_id == user.id)
        
        # Apply filters
        if scan_id:
            query = query.where(Vulnerability.scan_id == scan_id)
        
        if severity_filter:
            query = query.where(Vulnerability.severity.in_(severity_filter))
        
        if status_filter:
            query = query.where(Vulnerability.status.in_(status_filter))
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Vulnerability.title.ilike(search_term),
                    Vulnerability.description.ilike(search_term),
                    Vulnerability.affected_url.ilike(search_term),
                    Vulnerability.cve_id.ilike(search_term)
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(desc(Vulnerability.created_at)).offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        vulnerabilities = result.scalars().all()
        
        # Get aggregation counts
        severity_counts = {}
        status_counts = {}
        type_counts = {}
        
        # Count by severity
        result = await self.db.execute(
            select(
                Vulnerability.severity,
                func.count(Vulnerability.id)
            )
            .join(Scan)
            .where(Scan.user_id == user.id)
            .group_by(Vulnerability.severity)
        )
        for severity, count in result:
            severity_counts[severity.value] = count
        
        # Count by status
        result = await self.db.execute(
            select(
                Vulnerability.status,
                func.count(Vulnerability.id)
            )
            .join(Scan)
            .where(Scan.user_id == user.id)
            .group_by(Vulnerability.status)
        )
        for status_val, count in result:
            status_counts[status_val.value] = count
        
        return {
            "vulnerabilities": vulnerabilities,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1,
            "severity_counts": severity_counts,
            "status_counts": status_counts,
            "type_counts": type_counts
        }
    
    async def update_vulnerability(
        self, 
        vuln_id: str, 
        user: User, 
        request: VulnerabilityUpdateRequest
    ) -> Optional[Vulnerability]:
        """Update vulnerability"""
        vulnerability = await self.get_vulnerability(vuln_id, user)
        if not vulnerability:
            return None
        
        if request.status is not None:
            vulnerability.status = request.status
        
        if request.remediation_notes is not None:
            vulnerability.remediation_notes = request.remediation_notes
        
        if request.remediation_priority is not None:
            vulnerability.remediation_priority = request.remediation_priority
        
        if request.assigned_to is not None:
            vulnerability.assigned_to = request.assigned_to
        
        if request.due_date is not None:
            vulnerability.due_date = request.due_date
        
        if request.is_false_positive is not None:
            vulnerability.is_false_positive = request.is_false_positive
        
        if request.user_feedback is not None:
            vulnerability.user_feedback = request.user_feedback
        
        await self.db.commit()
        await self.db.refresh(vulnerability)
        
        return vulnerability
    
    async def mark_false_positive(
        self, 
        vuln_id: str, 
        user: User, 
        request: FalsePositiveRequest
    ) -> Optional[Vulnerability]:
        """Mark vulnerability as false positive"""
        vulnerability = await self.get_vulnerability(vuln_id, user)
        if not vulnerability:
            return None
        
        vulnerability.mark_as_false_positive(request.reason)
        await self.db.commit()
        await self.db.refresh(vulnerability)
        
        logger.info(f"Vulnerability {vuln_id} marked as false positive by {user.email}")
        return vulnerability
    
    async def mark_remediated(
        self, 
        vuln_id: str, 
        user: User, 
        request: RemediationRequest
    ) -> Optional[Vulnerability]:
        """Mark vulnerability as remediated"""
        vulnerability = await self.get_vulnerability(vuln_id, user)
        if not vulnerability:
            return None
        
        vulnerability.mark_as_fixed(request.notes)
        await self.db.commit()
        await self.db.refresh(vulnerability)
        
        logger.info(f"Vulnerability {vuln_id} marked as fixed by {user.email}")
        return vulnerability
    
    async def get_vulnerability_stats(self, user: User) -> dict:
        """Get vulnerability statistics for user"""
        # Basic counts
        result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan)
            .where(Scan.user_id == user.id)
        )
        total_vulnerabilities = result.scalar() or 0
        
        # By severity
        result = await self.db.execute(
            select(
                Vulnerability.severity,
                func.count(Vulnerability.id)
            )
            .join(Scan)
            .where(Scan.user_id == user.id)
            .group_by(Vulnerability.severity)
        )
        by_severity = {row[0].value: row[1] for row in result}
        
        # By status
        result = await self.db.execute(
            select(
                Vulnerability.status,
                func.count(Vulnerability.id)
            )
            .join(Scan)
            .where(Scan.user_id == user.id)
            .group_by(Vulnerability.status)
        )
        by_status = {row[0].value: row[1] for row in result}
        
        # Critical and high open
        result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan)
            .where(
                and_(
                    Scan.user_id == user.id,
                    Vulnerability.severity == VulnerabilitySeverity.CRITICAL,
                    Vulnerability.status == VulnerabilityStatus.OPEN
                )
            )
        )
        critical_open = result.scalar() or 0
        
        result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan)
            .where(
                and_(
                    Scan.user_id == user.id,
                    Vulnerability.severity == VulnerabilitySeverity.HIGH,
                    Vulnerability.status == VulnerabilityStatus.OPEN
                )
            )
        )
        high_open = result.scalar() or 0
        
        # Average CVSS score
        result = await self.db.execute(
            select(func.avg(Vulnerability.cvss_score))
            .join(Scan)
            .where(
                and_(
                    Scan.user_id == user.id,
                    Vulnerability.cvss_score.isnot(None)
                )
            )
        )
        avg_cvss = float(result.scalar() or 0)
        
        # Exploitable count
        result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan)
            .where(
                and_(
                    Scan.user_id == user.id,
                    Vulnerability.exploit_available == True,
                    Vulnerability.network_accessible == True
                )
            )
        )
        exploitable_count = result.scalar() or 0
        
        # False positive rate
        result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan)
            .where(
                and_(
                    Scan.user_id == user.id,
                    Vulnerability.is_false_positive == True
                )
            )
        )
        false_positives = result.scalar() or 0
        false_positive_rate = (false_positives / total_vulnerabilities * 100) if total_vulnerabilities > 0 else 0
        
        return {
            "total_vulnerabilities": total_vulnerabilities,
            "by_severity": by_severity,
            "by_status": by_status,
            "by_type": {},  # Will be populated when we have more data
            "critical_open": critical_open,
            "high_open": high_open,
            "avg_cvss_score": avg_cvss,
            "exploitable_count": exploitable_count,
            "false_positive_rate": false_positive_rate,
            "remediation_stats": {
                "fixed": by_status.get("fixed", 0),
                "in_progress": by_status.get("in_progress", 0),
                "open": by_status.get("open", 0)
            }
        }


def vulnerability_to_response(vulnerability: Vulnerability) -> VulnerabilityResponse:
    """Convert vulnerability model to response schema"""
    return VulnerabilityResponse(
        id=str(vulnerability.id),
        scan_id=str(vulnerability.scan_id),
        vulnerability_id=vulnerability.vulnerability_id,
        cve_id=vulnerability.cve_id,
        severity=vulnerability.severity,
        cvss_score=vulnerability.cvss_score,
        cvss_base_score=vulnerability.cvss_base_score,
        cvss_temporal_score=vulnerability.cvss_temporal_score,
        cvss_environmental_score=vulnerability.cvss_environmental_score,
        cvss_vector=vulnerability.cvss_vector,
        title=vulnerability.title,
        description=vulnerability.description,
        solution=vulnerability.solution,
        references=vulnerability.references or [],
        affected_url=vulnerability.affected_url,
        affected_component=vulnerability.affected_component,
        affected_parameter=vulnerability.affected_parameter,
        vulnerability_type=vulnerability.vulnerability_type,
        attack_vector=vulnerability.attack_vector,
        attack_complexity=vulnerability.attack_complexity,
        privileges_required=vulnerability.privileges_required,
        user_interaction_required=vulnerability.user_interaction_required,
        scope_changed=vulnerability.scope_changed,
        network_accessible=vulnerability.network_accessible,
        internet_facing=vulnerability.internet_facing,
        authentication_required=vulnerability.authentication_required,
        exploit_available=vulnerability.exploit_available,
        exploit_maturity=vulnerability.exploit_maturity,
        exploit_urls=vulnerability.exploit_urls or [],
        patch_available=vulnerability.patch_available,
        patch_urls=vulnerability.patch_urls or [],
        days_since_disclosure=vulnerability.days_since_disclosure,
        days_since_patch=vulnerability.days_since_patch,
        vendor_advisory_urls=vulnerability.vendor_advisory_urls or [],
        asset_criticality=vulnerability.asset_criticality,
        business_impact=vulnerability.business_impact,
        evidence=vulnerability.evidence or {},
        proof_of_concept=vulnerability.proof_of_concept,
        status=vulnerability.status,
        remediation_notes=vulnerability.remediation_notes,
        remediation_priority=vulnerability.remediation_priority,
        assigned_to=vulnerability.assigned_to,
        due_date=vulnerability.due_date,
        is_false_positive=vulnerability.is_false_positive,
        user_feedback=vulnerability.user_feedback,
        verified_by=vulnerability.verified_by,
        verified_at=vulnerability.verified_at,
        ml_confidence=vulnerability.ml_confidence,
        ml_risk_score=vulnerability.ml_risk_score,
        severity_weight=vulnerability.severity_weight,
        is_critical=vulnerability.is_critical,
        is_exploitable=vulnerability.is_exploitable,
        risk_level=vulnerability.risk_level,
        remediation_urgency=vulnerability.get_remediation_urgency(),
        created_at=vulnerability.created_at,
        updated_at=vulnerability.updated_at
    )


@router.post("", response_model=VulnerabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_vulnerability(
    request: VulnerabilityCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new vulnerability"""
    service = VulnerabilityService(db)
    vulnerability = await service.create_vulnerability(current_user, request)
    return vulnerability_to_response(vulnerability)


@router.get("", response_model=VulnerabilityListResponse)
async def list_vulnerabilities(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    scan_id: Optional[str] = Query(None, description="Filtrar por scan"),
    severity: Optional[List[VulnerabilitySeverity]] = Query(None, description="Filtrar por severidade"),
    status: Optional[List[VulnerabilityStatus]] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Buscar por texto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List vulnerabilities with filters"""
    service = VulnerabilityService(db)
    
    result = await service.list_vulnerabilities(
        current_user,
        page=page,
        per_page=per_page,
        scan_id=scan_id,
        severity_filter=severity,
        status_filter=status,
        search=search
    )
    
    vulnerability_responses = [
        vulnerability_to_response(vuln) for vuln in result["vulnerabilities"]
    ]
    
    return VulnerabilityListResponse(
        vulnerabilities=vulnerability_responses,
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        has_next=result["has_next"],
        has_prev=result["has_prev"],
        severity_counts=result["severity_counts"],
        status_counts=result["status_counts"],
        type_counts=result["type_counts"]
    )


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vulnerability_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get vulnerability details"""
    service = VulnerabilityService(db)
    vulnerability = await service.get_vulnerability(vulnerability_id, current_user)
    
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerabilidade não encontrada"
        )
    
    return vulnerability_to_response(vulnerability)


@router.put("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vulnerability_id: str,
    request: VulnerabilityUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update vulnerability"""
    service = VulnerabilityService(db)
    vulnerability = await service.update_vulnerability(vulnerability_id, current_user, request)
    
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerabilidade não encontrada"
        )
    
    return vulnerability_to_response(vulnerability)


@router.post("/{vulnerability_id}/false-positive", response_model=VulnerabilityResponse)
async def mark_false_positive(
    vulnerability_id: str,
    request: FalsePositiveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark vulnerability as false positive"""
    service = VulnerabilityService(db)
    vulnerability = await service.mark_false_positive(vulnerability_id, current_user, request)
    
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerabilidade não encontrada"
        )
    
    return vulnerability_to_response(vulnerability)


@router.post("/{vulnerability_id}/remediate", response_model=VulnerabilityResponse)
async def mark_remediated(
    vulnerability_id: str,
    request: RemediationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark vulnerability as remediated"""
    service = VulnerabilityService(db)
    vulnerability = await service.mark_remediated(vulnerability_id, current_user, request)
    
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerabilidade não encontrada"
        )
    
    return vulnerability_to_response(vulnerability)


@router.get("/stats/summary", response_model=VulnerabilityStatsResponse)
async def get_vulnerability_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get vulnerability statistics"""
    service = VulnerabilityService(db)
    stats = await service.get_vulnerability_stats(current_user)
    
    return VulnerabilityStatsResponse(**stats)