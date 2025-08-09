"""
Scan Job Manager

Manages the execution of security scans including:
- Background job processing
- Scanner orchestration
- Progress tracking
- Result processing and storage
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from .base_scanner import BaseScanner, ScanResult, ScanType, VulnerabilityData
from .zap_scanner import ZAPScanner
from .nmap_scanner import NmapScanner
from app.models.scan import Scan, ScanStatus
from app.models.vulnerability import Vulnerability, VulnerabilitySeverity as ModelVulnerabilitySeverity
from app.core.logging_simple import get_logger

logger = get_logger(__name__)


class ScanJobManager:
    """
    Manages scan job execution and coordination.
    
    This class orchestrates different types of security scans,
    manages their execution, tracks progress, and stores results.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize scan job manager.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Scanner registry
        self.scanners = self._initialize_scanners()
        
    def _initialize_scanners(self) -> Dict[ScanType, BaseScanner]:
        """Initialize available scanners"""
        scanners = {}
        
        try:
            # Initialize ZAP scanner
            zap_config = {
                "zap_host": "127.0.0.1",
                "zap_port": 8080,
                "auto_start_zap": False,
                "max_scan_duration": 1800,
                "enable_passive_scan": True,
                "enable_active_scan": True,
                "enable_spider": True
            }
            scanners[ScanType.OWASP_ZAP] = ZAPScanner(zap_config)
            
            # Initialize Nmap scanner
            nmap_config = {
                "nmap_executable": "nmap",
                "max_scan_duration": 600,
                "default_ports": "1-1000",
                "timing_template": 4,
                "enable_service_detection": True,
                "enable_version_detection": True,
                "enable_scripts": True
            }
            scanners[ScanType.NMAP_PORT] = NmapScanner(nmap_config)
            
            logger.info(f"Initialized {len(scanners)} scanners")
            
        except Exception as e:
            logger.error(f"Error initializing scanners: {str(e)}")
        
        return scanners
    
    async def start_scan_job(self, scan_id: str) -> bool:
        """
        Start a scan job by scan ID.
        
        Args:
            scan_id: Database scan ID
            
        Returns:
            bool: True if job started successfully
        """
        try:
            # Get scan from database
            result = await self.db.execute(
                select(Scan).where(Scan.id == scan_id)
            )
            scan = result.scalar_one_or_none()
            
            if not scan:
                logger.error(f"Scan not found: {scan_id}")
                return False
            
            # Check if already running
            if scan_id in self.active_jobs:
                logger.warning(f"Scan job already running: {scan_id}")
                return False
            
            # Update scan status to running
            await self._update_scan_status(scan_id, ScanStatus.RUNNING, {"started_at": datetime.utcnow()})
            
            # Start job in background
            job_info = {
                "scan_id": scan_id,
                "target_url": scan.target_url,
                "scan_types": scan.scan_types,
                "options": scan.options,
                "task": None
            }
            
            # Create async task
            task = asyncio.create_task(self._execute_scan_job(job_info))
            job_info["task"] = task
            
            self.active_jobs[scan_id] = job_info
            
            logger.info(f"Scan job started: {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting scan job {scan_id}: {str(e)}")
            await self._update_scan_status(scan_id, ScanStatus.FAILED, {"error_message": str(e)})
            return False
    
    async def _execute_scan_job(self, job_info: Dict[str, Any]):
        """
        Execute the scan job.
        
        Args:
            job_info: Job information dictionary
        """
        scan_id = job_info["scan_id"]
        target_url = job_info["target_url"]
        scan_types = job_info["scan_types"]
        options = job_info["options"]
        
        logger.info(f"Executing scan job {scan_id} for {target_url}")
        
        try:
            # Set up progress callback
            def progress_callback(progress: float, message: str):
                asyncio.create_task(self._update_progress(scan_id, progress, message))
            
            # Execute each scan type
            all_results = []
            total_scanners = len(scan_types)
            
            for i, scan_type_str in enumerate(scan_types):
                try:
                    # Map string to enum
                    scan_type = ScanType(scan_type_str)
                    
                    if scan_type not in self.scanners:
                        logger.warning(f"Scanner not available for type: {scan_type}")
                        continue
                    
                    scanner = self.scanners[scan_type]
                    
                    # Set progress callback
                    scanner.set_progress_callback(progress_callback)
                    
                    # Calculate progress offset for this scanner
                    base_progress = (i / total_scanners) * 90
                    
                    await self._update_progress(
                        scan_id, 
                        base_progress, 
                        f"Starting {scan_type.value} scan"
                    )
                    
                    # Execute scan
                    logger.info(f"Running {scan_type.value} scan against {target_url}")
                    result = await scanner.scan(target_url, options)
                    
                    if result.status == "completed":
                        all_results.append(result)
                        logger.info(f"{scan_type.value} scan completed with {len(result.vulnerabilities)} findings")
                    else:
                        logger.warning(f"{scan_type.value} scan failed: {result.error_message}")
                    
                except ValueError as e:
                    logger.error(f"Invalid scan type: {scan_type_str}")
                except Exception as e:
                    logger.error(f"Error executing {scan_type_str} scan: {str(e)}")
            
            # Process and store results
            await self._update_progress(scan_id, 95, "Processing scan results")
            await self._process_scan_results(scan_id, all_results)
            
            # Mark scan as completed
            await self._update_progress(scan_id, 100, "Scan completed successfully")
            await self._update_scan_status(
                scan_id, 
                ScanStatus.COMPLETED, 
                {
                    "completed_at": datetime.utcnow(),
                    "duration_seconds": None  # Will be calculated by model
                }
            )
            
            # Broadcast completion via WebSocket
            try:
                from app.api.v1.scanner_websocket import broadcast_scan_completion
                # Get vulnerability summary
                result = await self.db.execute(
                    select(Scan).options(selectinload(Scan.vulnerabilities))
                    .where(Scan.id == scan_id)
                )
                scan = result.scalar_one_or_none()
                vulnerability_summary = scan.vulnerability_summary if scan else {}
                duration = scan.duration_seconds if scan else None
                
                await broadcast_scan_completion(
                    scan_id, "completed", "Scan completed successfully", 
                    vulnerability_summary, duration
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast completion via WebSocket: {e}")
            
            logger.info(f"Scan job {scan_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Scan job {scan_id} failed: {str(e)}")
            await self._update_scan_status(
                scan_id,
                ScanStatus.FAILED,
                {
                    "error_message": str(e),
                    "completed_at": datetime.utcnow()
                }
            )
            
            # Broadcast failure via WebSocket
            try:
                from app.api.v1.scanner_websocket import broadcast_scan_completion
                await broadcast_scan_completion(
                    scan_id, "failed", f"Scan failed: {str(e)}"
                )
            except Exception as ws_error:
                logger.warning(f"Failed to broadcast failure via WebSocket: {ws_error}")
        
        finally:
            # Clean up job
            if scan_id in self.active_jobs:
                del self.active_jobs[scan_id]
    
    async def _process_scan_results(self, scan_id: str, scan_results: List[ScanResult]):
        """
        Process and store scan results in database.
        
        Args:
            scan_id: Scan ID
            scan_results: List of scan results from different scanners
        """
        try:
            # Combine all vulnerabilities
            all_vulnerabilities = []
            for result in scan_results:
                all_vulnerabilities.extend(result.vulnerabilities)
            
            # Store vulnerabilities in database
            for vuln_data in all_vulnerabilities:
                await self._store_vulnerability(scan_id, vuln_data)
            
            logger.info(f"Stored {len(all_vulnerabilities)} vulnerabilities for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Error processing scan results for {scan_id}: {str(e)}")
    
    async def _store_vulnerability(self, scan_id: str, vuln_data: VulnerabilityData):
        """
        Store a single vulnerability in the database.
        
        Args:
            scan_id: Scan ID
            vuln_data: Vulnerability data
        """
        try:
            # Map severity
            severity_mapping = {
                "critical": ModelVulnerabilitySeverity.CRITICAL,
                "high": ModelVulnerabilitySeverity.HIGH,
                "medium": ModelVulnerabilitySeverity.MEDIUM,
                "low": ModelVulnerabilitySeverity.LOW,
                "info": ModelVulnerabilitySeverity.INFO
            }
            
            model_severity = severity_mapping.get(
                vuln_data.severity.value,
                ModelVulnerabilitySeverity.MEDIUM
            )
            
            # Create vulnerability record
            vulnerability = Vulnerability(
                scan_id=scan_id,
                vulnerability_id=vuln_data.vulnerability_id,
                title=vuln_data.title,
                description=vuln_data.description,
                severity=model_severity,
                solution=vuln_data.solution,
                affected_url=vuln_data.affected_url,
                evidence=vuln_data.evidence,
                cvss_score=vuln_data.cvss_score,
                cve_id=vuln_data.cve_id,
                references=vuln_data.references,
                tags=vuln_data.tags,
                confidence=vuln_data.confidence,
                risk_description=vuln_data.risk_description
            )
            
            self.db.add(vulnerability)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing vulnerability: {str(e)}")
            await self.db.rollback()
    
    async def _update_scan_status(self, scan_id: str, status: ScanStatus, extra_data: Dict[str, Any] = None):
        """
        Update scan status in database.
        
        Args:
            scan_id: Scan ID
            status: New status
            extra_data: Additional data to update
        """
        try:
            update_data = {"status": status}
            if extra_data:
                update_data.update(extra_data)
            
            await self.db.execute(
                update(Scan)
                .where(Scan.id == scan_id)
                .values(**update_data)
            )
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating scan status: {str(e)}")
            await self.db.rollback()
    
    async def _update_progress(self, scan_id: str, progress: float, message: str):
        """
        Update scan progress with WebSocket broadcast.
        
        Args:
            scan_id: Scan ID
            progress: Progress percentage (0-100)
            message: Progress message
        """
        # Store progress update for potential WebSocket broadcast
        logger.info(f"Scan {scan_id} progress: {progress:.1f}% - {message}")
        
        # Broadcast to WebSocket clients
        try:
            from app.api.v1.scanner_websocket import broadcast_scan_progress
            await broadcast_scan_progress(scan_id, progress, message)
        except Exception as e:
            logger.warning(f"Failed to broadcast progress via WebSocket: {e}")
        
        # Call any registered progress callbacks
        if scan_id in self.progress_callbacks:
            for callback in self.progress_callbacks[scan_id]:
                try:
                    await callback(scan_id, progress, message)
                except Exception as e:
                    logger.error(f"Error in progress callback: {str(e)}")
    
    def register_progress_callback(self, scan_id: str, callback: Callable):
        """
        Register a progress callback for a scan.
        
        Args:
            scan_id: Scan ID
            callback: Async callback function(scan_id, progress, message)
        """
        if scan_id not in self.progress_callbacks:
            self.progress_callbacks[scan_id] = []
        self.progress_callbacks[scan_id].append(callback)
    
    def unregister_progress_callback(self, scan_id: str, callback: Callable):
        """
        Unregister a progress callback.
        
        Args:
            scan_id: Scan ID
            callback: Callback function to remove
        """
        if scan_id in self.progress_callbacks:
            try:
                self.progress_callbacks[scan_id].remove(callback)
            except ValueError:
                pass
    
    async def cancel_scan_job(self, scan_id: str) -> bool:
        """
        Cancel a running scan job.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            if scan_id not in self.active_jobs:
                logger.warning(f"Scan job not running: {scan_id}")
                return False
            
            job_info = self.active_jobs[scan_id]
            task = job_info.get("task")
            
            if task and not task.done():
                # Cancel the task
                task.cancel()
                
                # Stop any running scanners
                for scanner in self.scanners.values():
                    if scanner.is_running:
                        scanner.stop()
                
                # Update database
                await self._update_scan_status(
                    scan_id,
                    ScanStatus.CANCELLED,
                    {
                        "completed_at": datetime.utcnow(),
                        "error_message": "Scan cancelled by user"
                    }
                )
                
                logger.info(f"Scan job cancelled: {scan_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling scan job {scan_id}: {str(e)}")
            return False
    
    def get_active_jobs(self) -> List[str]:
        """Get list of active job IDs"""
        return list(self.active_jobs.keys())
    
    def is_job_running(self, scan_id: str) -> bool:
        """Check if a scan job is currently running"""
        return scan_id in self.active_jobs
    
    async def get_job_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a scan job.
        
        Args:
            scan_id: Scan ID
            
        Returns:
            Dict with job status information or None if not found
        """
        try:
            # Get from database
            result = await self.db.execute(
                select(Scan).where(Scan.id == scan_id)
            )
            scan = result.scalar_one_or_none()
            
            if not scan:
                return None
            
            return {
                "scan_id": str(scan.id),
                "status": scan.status.value,
                "target_url": scan.target_url,
                "scan_types": scan.scan_types,
                "started_at": scan.started_at,
                "completed_at": scan.completed_at,
                "duration_seconds": scan.duration_seconds,
                "error_message": scan.error_message,
                "is_active": scan_id in self.active_jobs
            }
            
        except Exception as e:
            logger.error(f"Error getting job status for {scan_id}: {str(e)}")
            return None
    
    async def cleanup_completed_jobs(self):
        """Clean up completed job references"""
        completed_jobs = []
        
        for scan_id, job_info in self.active_jobs.items():
            task = job_info.get("task")
            if task and task.done():
                completed_jobs.append(scan_id)
        
        for scan_id in completed_jobs:
            del self.active_jobs[scan_id]
            if scan_id in self.progress_callbacks:
                del self.progress_callbacks[scan_id]
        
        if completed_jobs:
            logger.info(f"Cleaned up {len(completed_jobs)} completed jobs")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all scanners.
        
        Returns:
            Dict with health status of each scanner
        """
        health_status = {
            "active_jobs": len(self.active_jobs),
            "scanners": {}
        }
        
        for scan_type, scanner in self.scanners.items():
            try:
                is_healthy = await scanner.health_check()
                health_status["scanners"][scan_type.value] = {
                    "healthy": is_healthy,
                    "info": scanner.get_scanner_info()
                }
            except Exception as e:
                health_status["scanners"][scan_type.value] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return health_status