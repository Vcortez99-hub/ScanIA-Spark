"""
OWASP ZAP Scanner Integration

Integrates with OWASP ZAP (Zed Attack Proxy) for web application security scanning.
Provides comprehensive vulnerability detection including SQL injection, XSS, and more.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse
import subprocess
import requests
from requests.exceptions import RequestException, ConnectionError
import tempfile
import os

from .base_scanner import BaseScanner, ScanResult, ScanType, VulnerabilityData, VulnerabilitySeverity
from app.core.logging_simple import get_logger

logger = get_logger(__name__)


class ZAPScanner(BaseScanner):
    """
    OWASP ZAP Scanner implementation.
    
    This scanner integrates with OWASP ZAP to perform comprehensive web application
    security testing including:
    - Passive scanning
    - Active scanning  
    - Spider crawling
    - Authentication testing
    - Custom script execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(ScanType.OWASP_ZAP, config)
        
        # ZAP configuration
        self.zap_host = self.config.get("zap_host", "127.0.0.1")
        self.zap_port = self.config.get("zap_port", 8080)
        self.zap_api_key = self.config.get("zap_api_key", "")
        self.zap_proxy_url = f"http://{self.zap_host}:{self.zap_port}"
        self.zap_api_url = f"{self.zap_proxy_url}/JSON"
        
        # Scan configuration
        self.max_scan_duration = self.config.get("max_scan_duration", 1800)  # 30 minutes
        self.max_crawl_depth = self.config.get("max_crawl_depth", 5)
        self.enable_passive_scan = self.config.get("enable_passive_scan", True)
        self.enable_active_scan = self.config.get("enable_active_scan", True)
        self.enable_spider = self.config.get("enable_spider", True)
        
        # ZAP process management
        self.zap_process = None
        self.auto_start_zap = self.config.get("auto_start_zap", False)
        self.zap_executable = self.config.get("zap_executable", "zap.sh")
        
    async def configure(self, options: Dict[str, Any]) -> bool:
        """Configure ZAP scanner with specific options"""
        try:
            # Update configuration
            if "max_scan_duration" in options:
                self.max_scan_duration = options["max_scan_duration"]
            
            if "max_crawl_depth" in options:
                self.max_crawl_depth = options["max_crawl_depth"]
                
            if "enable_passive_scan" in options:
                self.enable_passive_scan = options["enable_passive_scan"]
                
            if "enable_active_scan" in options:
                self.enable_active_scan = options["enable_active_scan"]
                
            if "enable_spider" in options:
                self.enable_spider = options["enable_spider"]
            
            logger.info("ZAP scanner configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring ZAP scanner: {str(e)}")
            return False
    
    async def validate_target(self, target_url: str) -> bool:
        """Validate if target URL is suitable for ZAP scanning"""
        try:
            parsed = urlparse(target_url)
            
            # Must be HTTP or HTTPS
            if parsed.scheme not in ["http", "https"]:
                logger.error(f"Invalid URL scheme: {parsed.scheme}")
                return False
            
            # Must have a valid hostname
            if not parsed.netloc:
                logger.error("No hostname found in URL")
                return False
            
            # Check if target is reachable
            response = requests.get(target_url, timeout=10, verify=False)
            if response.status_code >= 400:
                logger.warning(f"Target returned {response.status_code}, but continuing")
            
            logger.info(f"Target URL validated: {target_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating target URL: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """Check if ZAP is running and accessible"""
        try:
            # Try to connect to ZAP API
            response = requests.get(
                f"{self.zap_api_url}/core/view/version/",
                params={"zapapiformat": "JSON"},
                timeout=5
            )
            
            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"ZAP health check passed - version: {version_info.get('version')}")
                return True
            else:
                logger.error(f"ZAP health check failed - status: {response.status_code}")
                return False
                
        except ConnectionError:
            logger.error("ZAP is not running or not accessible")
            if self.auto_start_zap:
                return await self._start_zap()
            return False
        except Exception as e:
            logger.error(f"ZAP health check error: {str(e)}")
            return False
    
    async def _start_zap(self) -> bool:
        """Start ZAP daemon if auto_start_zap is enabled"""
        try:
            logger.info("Starting ZAP daemon...")
            
            # Command to start ZAP in daemon mode
            cmd = [
                self.zap_executable,
                "-daemon",
                "-port", str(self.zap_port),
                "-host", self.zap_host,
                "-config", "api.disablekey=true",
                "-config", "api.addrs.addr.name=.*",
                "-config", "api.addrs.addr.regex=true"
            ]
            
            self.zap_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for ZAP to start
            for i in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                if await self.health_check():
                    logger.info("ZAP started successfully")
                    return True
            
            logger.error("ZAP failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Error starting ZAP: {str(e)}")
            return False
    
    async def scan(self, target_url: str, options: Dict[str, Any] = None) -> ScanResult:
        """Perform comprehensive ZAP security scan"""
        start_time = datetime.utcnow()
        scan_result = ScanResult(
            scan_type=self.scan_type,
            target_url=target_url,
            status="running",
            start_time=start_time,
            metadata={"zap_version": await self._get_zap_version()}
        )
        
        try:
            self.is_running = True
            self.update_progress(0, "Initializing ZAP scan")
            
            # Health check
            if not await self.health_check():
                raise Exception("ZAP is not accessible")
            
            # Configure scan options
            if options:
                await self.configure(options)
            
            # Validate target
            if not await self.validate_target(target_url):
                raise Exception("Target URL validation failed")
            
            self.update_progress(10, "Starting spider crawl")
            
            # Step 1: Spider the target
            spider_id = None
            if self.enable_spider:
                spider_id = await self._run_spider(target_url)
            
            self.update_progress(40, "Spider crawl completed, starting passive scan")
            
            # Step 2: Passive scan (automatic during spider)
            if self.enable_passive_scan:
                await self._wait_for_passive_scan()
            
            self.update_progress(60, "Passive scan completed, starting active scan")
            
            # Step 3: Active scan
            active_scan_id = None
            if self.enable_active_scan:
                active_scan_id = await self._run_active_scan(target_url)
            
            self.update_progress(90, "Active scan completed, collecting results")
            
            # Step 4: Collect results
            vulnerabilities = await self._collect_vulnerabilities(target_url)
            
            # Update scan result
            end_time = datetime.utcnow()
            scan_result.end_time = end_time
            scan_result.duration_seconds = (end_time - start_time).total_seconds()
            scan_result.status = "completed"
            scan_result.vulnerabilities = vulnerabilities
            scan_result.metadata.update({
                "spider_id": spider_id,
                "active_scan_id": active_scan_id,
                "total_vulnerabilities": len(vulnerabilities),
                "severity_summary": self._get_severity_summary(vulnerabilities)
            })
            
            self.update_progress(100, f"Scan completed - {len(vulnerabilities)} vulnerabilities found")
            
        except Exception as e:
            logger.error(f"ZAP scan error: {str(e)}")
            scan_result.status = "failed"
            scan_result.error_message = str(e)
            scan_result.end_time = datetime.utcnow()
            if scan_result.start_time:
                scan_result.duration_seconds = (scan_result.end_time - scan_result.start_time).total_seconds()
        
        finally:
            self.is_running = False
            
        return scan_result
    
    async def _get_zap_version(self) -> str:
        """Get ZAP version information"""
        try:
            response = requests.get(
                f"{self.zap_api_url}/core/view/version/",
                params={"zapapiformat": "JSON"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("version", "unknown")
        except:
            pass
        return "unknown"
    
    async def _run_spider(self, target_url: str) -> Optional[str]:
        """Run ZAP spider against target"""
        try:
            # Start spider
            response = requests.get(
                f"{self.zap_api_url}/spider/action/scan/",
                params={
                    "url": target_url,
                    "maxChildren": self.max_crawl_depth,
                    "zapapiformat": "JSON"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Spider start failed: {response.status_code}")
            
            spider_id = response.json().get("scan")
            logger.info(f"Spider started with ID: {spider_id}")
            
            # Wait for spider to complete
            while True:
                if self.should_stop:
                    break
                    
                status_response = requests.get(
                    f"{self.zap_api_url}/spider/view/status/",
                    params={"scanId": spider_id, "zapapiformat": "JSON"},
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    progress = int(status_response.json().get("status", 0))
                    self.update_progress(10 + (progress * 0.3), f"Spider crawling: {progress}%")
                    
                    if progress >= 100:
                        break
                
                await asyncio.sleep(2)
            
            return spider_id
            
        except Exception as e:
            logger.error(f"Spider error: {str(e)}")
            return None
    
    async def _wait_for_passive_scan(self):
        """Wait for passive scan to complete"""
        try:
            while True:
                if self.should_stop:
                    break
                    
                response = requests.get(
                    f"{self.zap_api_url}/pscan/view/recordsToScan/",
                    params={"zapapiformat": "JSON"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    records_to_scan = int(response.json().get("recordsToScan", 0))
                    if records_to_scan <= 0:
                        break
                    
                    self.update_progress(45, f"Passive scan: {records_to_scan} records remaining")
                
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Passive scan wait error: {str(e)}")
    
    async def _run_active_scan(self, target_url: str) -> Optional[str]:
        """Run ZAP active scan against target"""
        try:
            # Start active scan
            response = requests.get(
                f"{self.zap_api_url}/ascan/action/scan/",
                params={
                    "url": target_url,
                    "zapapiformat": "JSON"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Active scan start failed: {response.status_code}")
            
            scan_id = response.json().get("scan")
            logger.info(f"Active scan started with ID: {scan_id}")
            
            # Wait for active scan to complete
            start_time = time.time()
            while True:
                if self.should_stop:
                    break
                
                # Check timeout
                if time.time() - start_time > self.max_scan_duration:
                    logger.warning("Active scan timeout reached")
                    break
                    
                status_response = requests.get(
                    f"{self.zap_api_url}/ascan/view/status/",
                    params={"scanId": scan_id, "zapapiformat": "JSON"},
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    progress = int(status_response.json().get("status", 0))
                    self.update_progress(60 + (progress * 0.3), f"Active scan: {progress}%")
                    
                    if progress >= 100:
                        break
                
                await asyncio.sleep(5)
            
            return scan_id
            
        except Exception as e:
            logger.error(f"Active scan error: {str(e)}")
            return None
    
    async def _collect_vulnerabilities(self, target_url: str) -> List[VulnerabilityData]:
        """Collect vulnerabilities from ZAP"""
        vulnerabilities = []
        
        try:
            # Get alerts from ZAP
            response = requests.get(
                f"{self.zap_api_url}/core/view/alerts/",
                params={"baseurl": target_url, "zapapiformat": "JSON"},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to retrieve alerts: {response.status_code}")
                return vulnerabilities
            
            alerts = response.json().get("alerts", [])
            
            for alert in alerts:
                vuln = VulnerabilityData(
                    title=alert.get("name", "Unknown Vulnerability"),
                    description=alert.get("description", ""),
                    severity=self._map_zap_severity(alert.get("risk", "Low")),
                    cvss_score=self._calculate_cvss_from_risk(alert.get("risk", "Low")),
                    url=alert.get("url", ""),
                    parameter=alert.get("param", ""),
                    evidence=alert.get("evidence", ""),
                    solution=alert.get("solution", ""),
                    references=alert.get("reference", "").split("\n") if alert.get("reference") else [],
                    confidence=alert.get("confidence", ""),
                    risk_description=alert.get("description", "")
                )
                
                vulnerabilities.append(vuln)
            
            logger.info(f"Collected {len(vulnerabilities)} vulnerabilities from ZAP")
            
        except Exception as e:
            logger.error(f"Error collecting vulnerabilities: {str(e)}")
        
        return vulnerabilities
    
    def _map_zap_severity(self, zap_risk: str) -> VulnerabilitySeverity:
        """Map ZAP risk levels to our severity enum"""
        mapping = {
            "High": VulnerabilitySeverity.HIGH,
            "Medium": VulnerabilitySeverity.MEDIUM,
            "Low": VulnerabilitySeverity.LOW,
            "Informational": VulnerabilitySeverity.INFO
        }
        return mapping.get(zap_risk, VulnerabilitySeverity.LOW)
    
    def _calculate_cvss_from_risk(self, zap_risk: str) -> float:
        """Convert ZAP risk level to approximate CVSS score"""
        mapping = {
            "High": 8.0,
            "Medium": 5.5,
            "Low": 3.0,
            "Informational": 1.0
        }
        return mapping.get(zap_risk, 3.0)
    
    def _get_severity_summary(self, vulnerabilities: List[VulnerabilityData]) -> Dict[str, int]:
        """Get summary of vulnerabilities by severity"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in vulnerabilities:
            if vuln.severity.value in summary:
                summary[vuln.severity.value] += 1
        
        return summary
    
    def get_supported_options(self) -> List[str]:
        """Get list of supported configuration options"""
        return [
            "max_scan_duration",
            "max_crawl_depth", 
            "enable_passive_scan",
            "enable_active_scan",
            "enable_spider",
            "zap_host",
            "zap_port",
            "zap_api_key"
        ]
    
    def __del__(self):
        """Cleanup ZAP process if we started it"""
        if self.zap_process and self.zap_process.poll() is None:
            try:
                self.zap_process.terminate()
                self.zap_process.wait(timeout=10)
            except:
                pass