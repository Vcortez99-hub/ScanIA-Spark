"""
Scanner Engine - Core scanning functionality
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import requests
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import Scan, ScanStatus
from app.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from app.core.config import settings
from app.core.logging_simple import get_logger

logger = get_logger(__name__)


class ScannerEngine:
    """Main scanner engine that orchestrates different scanning tools"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.zap_api_url = f"http://{settings.OWASP_ZAP_HOST}:{settings.OWASP_ZAP_PORT}"
        self.zap_api_key = settings.OWASP_ZAP_API_KEY
    
    async def execute_scan(self, scan: Scan) -> bool:
        """Execute a security scan"""
        try:
            logger.info(f"Starting scan execution: {scan.id}")
            
            # Update scan status
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Execute scan types
            vulnerabilities = []
            
            if "owasp_zap" in scan.scan_types:
                zap_vulns = await self._execute_zap_scan(scan)
                vulnerabilities.extend(zap_vulns)
            
            if "nmap" in scan.scan_types:
                nmap_vulns = await self._execute_nmap_scan(scan)
                vulnerabilities.extend(nmap_vulns)
            
            if "nikto" in scan.scan_types:
                nikto_vulns = await self._execute_nikto_scan(scan)
                vulnerabilities.extend(nikto_vulns)
            
            # Save vulnerabilities to database
            for vuln_data in vulnerabilities:
                vulnerability = Vulnerability(**vuln_data)
                self.db.add(vulnerability)
            
            # Update scan completion
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            
            if scan.started_at:
                duration = scan.completed_at - scan.started_at
                scan.duration_seconds = int(duration.total_seconds())
            
            await self.db.commit()
            
            logger.info(f"Scan completed: {scan.id} with {len(vulnerabilities)} vulnerabilities")
            return True
            
        except Exception as e:
            logger.error(f"Scan execution failed: {scan.id} - {str(e)}")
            
            # Update scan status to failed
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            await self.db.commit()
            
            return False
    
    async def _execute_zap_scan(self, scan: Scan) -> List[Dict[str, Any]]:
        """Execute OWASP ZAP scan"""
        logger.info(f"Executing ZAP scan for: {scan.target_url}")
        
        try:
            # Start ZAP session
            session_name = f"scan_{scan.id}"
            
            # Create new session
            response = requests.get(
                f"{self.zap_api_url}/JSON/core/action/newSession/",
                params={
                    "apikey": self.zap_api_key,
                    "name": session_name,
                    "overwrite": "true"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create ZAP session: {response.text}")
            
            # Spider the target
            await self._zap_spider(scan.target_url)
            
            # Active scan
            await self._zap_active_scan(scan.target_url)
            
            # Get alerts (vulnerabilities)
            alerts_response = requests.get(
                f"{self.zap_api_url}/JSON/core/view/alerts/",
                params={
                    "apikey": self.zap_api_key,
                    "baseurl": scan.target_url
                }
            )
            
            if alerts_response.status_code != 200:
                raise Exception(f"Failed to get ZAP alerts: {alerts_response.text}")
            
            alerts_data = alerts_response.json()
            vulnerabilities = []
            
            for alert in alerts_data.get("alerts", []):
                vulnerability = self._parse_zap_alert(alert, scan.id)
                vulnerabilities.append(vulnerability)
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"ZAP scan failed: {str(e)}")
            return []
    
    async def _zap_spider(self, target_url: str) -> None:
        """Run ZAP spider"""
        logger.info(f"Starting ZAP spider for: {target_url}")
        
        # Start spider
        response = requests.get(
            f"{self.zap_api_url}/JSON/spider/action/scan/",
            params={
                "apikey": self.zap_api_key,
                "url": target_url,
                "maxChildren": "10",
                "recurse": "true"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to start spider: {response.text}")
        
        scan_id = response.json().get("scan")
        
        # Wait for spider to complete
        while True:
            status_response = requests.get(
                f"{self.zap_api_url}/JSON/spider/view/status/",
                params={
                    "apikey": self.zap_api_key,
                    "scanId": scan_id
                }
            )
            
            if status_response.status_code == 200:
                status = int(status_response.json().get("status", 0))
                if status >= 100:
                    break
            
            await asyncio.sleep(2)
        
        logger.info("ZAP spider completed")
    
    async def _zap_active_scan(self, target_url: str) -> None:
        """Run ZAP active scan"""
        logger.info(f"Starting ZAP active scan for: {target_url}")
        
        # Start active scan
        response = requests.get(
            f"{self.zap_api_url}/JSON/ascan/action/scan/",
            params={
                "apikey": self.zap_api_key,
                "url": target_url,
                "recurse": "true",
                "inScopeOnly": "false"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to start active scan: {response.text}")
        
        scan_id = response.json().get("scan")
        
        # Wait for active scan to complete
        while True:
            status_response = requests.get(
                f"{self.zap_api_url}/JSON/ascan/view/status/",
                params={
                    "apikey": self.zap_api_key,
                    "scanId": scan_id
                }
            )
            
            if status_response.status_code == 200:
                status = int(status_response.json().get("status", 0))
                if status >= 100:
                    break
            
            await asyncio.sleep(5)
        
        logger.info("ZAP active scan completed")
    
    def _parse_zap_alert(self, alert: Dict[str, Any], scan_id: str) -> Dict[str, Any]:
        """Parse ZAP alert into vulnerability format"""
        
        # Map ZAP risk to severity
        risk_mapping = {
            "High": VulnerabilitySeverity.HIGH,
            "Medium": VulnerabilitySeverity.MEDIUM,
            "Low": VulnerabilitySeverity.LOW,
            "Informational": VulnerabilitySeverity.INFO
        }
        
        severity = risk_mapping.get(alert.get("risk", "Low"), VulnerabilitySeverity.LOW)
        
        return {
            "scan_id": scan_id,
            "vulnerability_id": f"zap_{alert.get('pluginId', uuid.uuid4())}",
            "severity": severity,
            "title": alert.get("alert", "Unknown Vulnerability"),
            "description": alert.get("desc", ""),
            "solution": alert.get("solution", ""),
            "references": alert.get("reference", "").split("\n") if alert.get("reference") else [],
            "affected_url": alert.get("url", ""),
            "affected_parameter": alert.get("param", ""),
            "vulnerability_type": alert.get("cweid", ""),
            "evidence": {
                "attack": alert.get("attack", ""),
                "evidence": alert.get("evidence", ""),
                "other": alert.get("other", "")
            },
            "status": VulnerabilityStatus.OPEN,
            "network_accessible": True,
            "internet_facing": True
        }
    
    async def _execute_nmap_scan(self, scan: Scan) -> List[Dict[str, Any]]:
        """Execute Nmap scan"""
        logger.info(f"Executing Nmap scan for: {scan.target_url}")
        
        # Extract domain from URL
        parsed_url = urlparse(scan.target_url)
        target_host = parsed_url.netloc
        
        try:
            # This is a simplified implementation
            # In production, you would use python-nmap library
            vulnerabilities = []
            
            # Simulate some common findings
            if parsed_url.scheme == "http":
                vulnerabilities.append({
                    "scan_id": str(scan.id),
                    "vulnerability_id": f"nmap_http_unencrypted",
                    "severity": VulnerabilitySeverity.MEDIUM,
                    "title": "Unencrypted HTTP Traffic",
                    "description": "The application is accessible over unencrypted HTTP protocol",
                    "solution": "Implement HTTPS with proper TLS configuration",
                    "affected_url": scan.target_url,
                    "vulnerability_type": "Information Disclosure",
                    "status": VulnerabilityStatus.OPEN,
                    "network_accessible": True,
                    "internet_facing": True
                })
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Nmap scan failed: {str(e)}")
            return []
    
    async def _execute_nikto_scan(self, scan: Scan) -> List[Dict[str, Any]]:
        """Execute Nikto scan"""
        logger.info(f"Executing Nikto scan for: {scan.target_url}")
        
        try:
            # This is a simplified implementation
            # In production, you would integrate with actual Nikto
            vulnerabilities = []
            
            # Simulate some common web server findings
            vulnerabilities.append({
                "scan_id": str(scan.id),
                "vulnerability_id": f"nikto_server_info",
                "severity": VulnerabilitySeverity.INFO,
                "title": "Server Information Disclosure",
                "description": "Web server reveals version information",
                "solution": "Configure server to hide version information",
                "affected_url": scan.target_url,
                "vulnerability_type": "Information Disclosure",
                "status": VulnerabilityStatus.OPEN,
                "network_accessible": True,
                "internet_facing": True
            })
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Nikto scan failed: {str(e)}")
            return []


class ScanJobManager:
    """Manages scan job execution"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scanner_engine = ScannerEngine(db)
    
    async def start_scan_job(self, scan_id: str) -> bool:
        """Start a scan job"""
        try:
            # Get scan from database
            from sqlalchemy import select
            result = await self.db.execute(
                select(Scan).where(Scan.id == scan_id)
            )
            scan = result.scalar_one_or_none()
            
            if not scan:
                logger.error(f"Scan not found: {scan_id}")
                return False
            
            # Execute scan
            success = await self.scanner_engine.execute_scan(scan)
            return success
            
        except Exception as e:
            logger.error(f"Failed to start scan job: {scan_id} - {str(e)}")
            return False