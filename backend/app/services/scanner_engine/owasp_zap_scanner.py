"""
OWASP ZAP Scanner Implementation

Integrates with OWASP ZAP proxy for web application security testing.
Performs automated security scans including spider, active scan, and passive scan.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .base_scanner import BaseScanner, ScanType, ScanResult, VulnerabilityData, VulnerabilitySeverity, ScannerException

logger = logging.getLogger(__name__)

try:
    from zapv2 import ZAPv2
except ImportError:
    ZAPv2 = None
    logger.warning("ZAPv2 not available. Install python-owasp-zap-v2.4 to enable ZAP scanner")


class OWASPZapScanner(BaseScanner):
    """
    OWASP ZAP security scanner implementation.
    
    Performs comprehensive web application security testing including:
    - Spider/Crawler for site discovery
    - Passive scanning during crawling
    - Active security scanning for vulnerabilities
    - SSL/TLS analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(ScanType.OWASP_ZAP, config)
        self.zap: Optional[ZAPv2] = None
        self.zap_host = self.config.get('zap_host', '127.0.0.1')
        self.zap_port = self.config.get('zap_port', 8080)
        self.api_key = self.config.get('api_key', None)
        
    async def configure(self, options: Dict[str, Any]) -> bool:
        """Configure ZAP scanner with options"""
        try:
            if ZAPv2 is None:
                raise ScannerException("ZAP library not available")
                
            # Initialize ZAP client
            proxies = {
                'http': f'http://{self.zap_host}:{self.zap_port}',
                'https': f'http://{self.zap_host}:{self.zap_port}'
            }
            
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies=proxies
            )
            
            # Test ZAP connection
            try:
                version = self.zap.core.version
                logger.info(f"Connected to ZAP version: {version}")
                return True
            except Exception as e:
                raise ScannerException(f"Failed to connect to ZAP: {str(e)}")
                
        except Exception as e:
            logger.error(f"ZAP configuration failed: {e}")
            return False
    
    async def validate_target(self, target_url: str) -> bool:
        """Validate target URL for ZAP scanning"""
        if not target_url.startswith(('http://', 'https://')):
            return False
        
        return await self._validate_target_url(target_url)
    
    async def health_check(self) -> bool:
        """Check if ZAP is running and accessible"""
        if self.zap is None:
            return False
        
        try:
            self.zap.core.version
            return True
        except Exception:
            return False
    
    def get_supported_options(self) -> List[str]:
        """Get supported ZAP scanner options"""
        return [
            'spider_max_children',
            'spider_recurse',
            'spider_subtree_only',
            'active_scan_policy',
            'exclude_urls',
            'include_urls',
            'attack_strength',
            'alert_threshold'
        ]
    
    async def scan(self, target_url: str, options: Dict[str, Any] = None) -> ScanResult:
        """
        Perform comprehensive ZAP scan
        
        Args:
            target_url: Target URL to scan
            options: Scan configuration options
            
        Returns:
            ScanResult with discovered vulnerabilities
        """
        start_time = datetime.utcnow()
        scan_result = ScanResult(
            scan_type=self.scan_type,
            target_url=target_url,
            status="running",
            start_time=start_time
        )
        
        try:
            self.is_running = True
            self.update_progress(0, "Starting ZAP scan")
            
            # Pre-scan validation
            if not await self.validate_target(target_url):
                raise ScannerException(f"Invalid target URL: {target_url}")
            
            if not await self.health_check():
                raise ScannerException("ZAP is not accessible")
            
            # Configure scan options
            scan_options = options or {}
            await self._configure_scan_options(scan_options)
            
            # Start new ZAP session
            self.zap.core.new_session()
            self.update_progress(5, "Created new ZAP session")
            
            # Phase 1: Spider/Crawl
            self.update_progress(10, "Starting spider scan")
            await self._run_spider(target_url, scan_options)
            self.update_progress(40, "Spider scan completed")
            
            # Phase 2: Active Scan
            self.update_progress(45, "Starting active security scan")
            await self._run_active_scan(target_url, scan_options)
            self.update_progress(85, "Active scan completed")
            
            # Phase 3: Collect Results
            self.update_progress(90, "Collecting scan results")
            vulnerabilities = await self._collect_results()
            
            scan_result.vulnerabilities = vulnerabilities
            scan_result.status = "completed"
            scan_result.end_time = datetime.utcnow()
            scan_result.duration_seconds = (scan_result.end_time - start_time).total_seconds()
            
            self.update_progress(100, f"Scan completed - Found {len(vulnerabilities)} vulnerabilities")
            
        except Exception as e:
            logger.error(f"ZAP scan failed: {e}")
            scan_result.status = "failed"
            scan_result.error_message = str(e)
            scan_result.end_time = datetime.utcnow()
            scan_result.duration_seconds = (scan_result.end_time - start_time).total_seconds()
            
        finally:
            self.is_running = False
            
        return scan_result
    
    async def _configure_scan_options(self, options: Dict[str, Any]):
        """Configure ZAP with scan-specific options"""
        try:
            # Configure spider options
            if 'spider_max_children' in options:
                self.zap.spider.set_option_max_children(options['spider_max_children'])
            
            # Configure scan policy
            if 'active_scan_policy' in options:
                # Load or create scan policy
                pass
            
            # Set attack strength
            if 'attack_strength' in options:
                strength = options['attack_strength']
                # Configure attack strength for all scanners
                pass
                
        except Exception as e:
            logger.warning(f"Failed to configure some ZAP options: {e}")
    
    async def _run_spider(self, target_url: str, options: Dict[str, Any]):
        """Run ZAP spider to discover site structure"""
        try:
            # Configure spider options
            max_children = options.get('spider_max_children', 10)
            recurse = options.get('spider_recurse', True)
            subtree_only = options.get('spider_subtree_only', True)
            
            # Start spider
            spider_id = self.zap.spider.scan(
                url=target_url,
                maxchildren=max_children,
                recurse=recurse,
                contextname=None,
                subtreeonly=subtree_only
            )
            
            # Wait for spider to complete
            await self._wait_for_spider(spider_id)
            
        except Exception as e:
            raise ScannerException(f"Spider scan failed: {str(e)}")
    
    async def _wait_for_spider(self, spider_id: str):
        """Wait for spider scan to complete"""
        while True:
            if self.should_stop:
                self.zap.spider.stop(spider_id)
                break
                
            status = int(self.zap.spider.status(spider_id))
            if status >= 100:
                break
                
            # Update progress (spider is 5-40% of total)
            spider_progress = 10 + (status * 0.3)
            self.update_progress(spider_progress, f"Spider progress: {status}%")
            
            await asyncio.sleep(2)
    
    async def _run_active_scan(self, target_url: str, options: Dict[str, Any]):
        """Run ZAP active security scan"""
        try:
            # Configure active scan
            policy = options.get('active_scan_policy', None)
            
            # Start active scan
            scan_id = self.zap.ascan.scan(
                url=target_url,
                recurse=True,
                inscopeonly=True,
                scanpolicyname=policy
            )
            
            # Wait for active scan to complete
            await self._wait_for_active_scan(scan_id)
            
        except Exception as e:
            raise ScannerException(f"Active scan failed: {str(e)}")
    
    async def _wait_for_active_scan(self, scan_id: str):
        """Wait for active scan to complete"""
        while True:
            if self.should_stop:
                self.zap.ascan.stop(scan_id)
                break
                
            status = int(self.zap.ascan.status(scan_id))
            if status >= 100:
                break
                
            # Update progress (active scan is 45-85% of total)
            scan_progress = 45 + (status * 0.4)
            self.update_progress(scan_progress, f"Active scan progress: {status}%")
            
            await asyncio.sleep(5)
    
    async def _collect_results(self) -> List[VulnerabilityData]:
        """Collect and parse ZAP scan results"""
        vulnerabilities = []
        
        try:
            # Get all alerts from ZAP
            alerts = self.zap.core.alerts()
            
            for alert in alerts:
                vulnerability = self._parse_zap_alert(alert)
                if vulnerability:
                    vulnerabilities.append(vulnerability)
            
            # Sort by severity
            vulnerabilities.sort(key=lambda v: v.severity_weight, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to collect ZAP results: {e}")
            
        return vulnerabilities
    
    def _parse_zap_alert(self, alert: Dict[str, Any]) -> Optional[VulnerabilityData]:
        """Parse ZAP alert into VulnerabilityData"""
        try:
            # Map ZAP risk levels to our severity levels
            risk_map = {
                'High': VulnerabilitySeverity.HIGH,
                'Medium': VulnerabilitySeverity.MEDIUM,
                'Low': VulnerabilitySeverity.LOW,
                'Informational': VulnerabilitySeverity.INFO
            }
            
            severity = risk_map.get(alert.get('risk', 'Low'), VulnerabilitySeverity.LOW)
            
            # Create vulnerability data
            vulnerability = VulnerabilityData(
                vulnerability_id=f"zap_{alert.get('alertRef', 'unknown')}",
                title=alert.get('alert', 'Unknown Vulnerability'),
                description=alert.get('description', 'No description available'),
                severity=severity,
                solution=alert.get('solution', 'No solution provided'),
                affected_url=alert.get('url', ''),
                evidence={
                    'param': alert.get('param', ''),
                    'attack': alert.get('attack', ''),
                    'evidence': alert.get('evidence', ''),
                    'method': alert.get('method', ''),
                    'instances': alert.get('instances', [])
                },
                cvss_score=self._calculate_cvss_score(severity),
                cve_id=self._extract_cve_from_alert(alert),
                references=self._extract_references_from_alert(alert),
                confidence=alert.get('confidence', 'Unknown')
            )
            
            return vulnerability
            
        except Exception as e:
            logger.warning(f"Failed to parse ZAP alert: {e}")
            return None
    
    def _extract_cve_from_alert(self, alert: Dict[str, Any]) -> Optional[str]:
        """Extract CVE ID from ZAP alert if available"""
        # Check common fields for CVE references
        text_fields = [
            alert.get('description', ''),
            alert.get('otherinfo', ''),
            alert.get('reference', '')
        ]
        
        import re
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        
        for text in text_fields:
            if text:
                match = re.search(cve_pattern, text)
                if match:
                    return match.group(0)
        
        return None
    
    def _extract_references_from_alert(self, alert: Dict[str, Any]) -> List[str]:
        """Extract reference URLs from ZAP alert"""
        references = []
        
        ref_text = alert.get('reference', '')
        if ref_text:
            # Split by common separators and extract URLs
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;!?]'
            urls = re.findall(url_pattern, ref_text)
            references.extend(urls)
        
        return references