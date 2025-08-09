"""
Base Scanner Class

Abstract base class for all security scanners in the ScanIA system.
Defines the common interface and functionality for security scanners.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ScanType(str, Enum):
    """Supported scan types"""
    OWASP_ZAP = "owasp_zap"
    NMAP_PORT = "nmap_port"
    SSL_TLS = "ssl_tls"
    DIRECTORY_BRUTEFORCE = "directory_bruteforce"
    SUBDOMAIN_ENUM = "subdomain_enum"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class VulnerabilityData:
    """Data class for vulnerability information"""
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    url: Optional[str] = None
    parameter: Optional[str] = None
    evidence: Optional[str] = None
    solution: Optional[str] = None
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: Optional[str] = None
    risk_description: Optional[str] = None


@dataclass
class ScanResult:
    """Data class for scan results"""
    scan_type: ScanType
    target_url: str
    status: str
    vulnerabilities: List[VulnerabilityData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    raw_output: Optional[str] = None


class BaseScanner(ABC):
    """
    Abstract base class for all security scanners.
    
    This class defines the common interface that all scanners must implement,
    including configuration, execution, and result processing.
    """
    
    def __init__(self, scan_type: ScanType, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base scanner.
        
        Args:
            scan_type: The type of scan this scanner performs
            config: Optional configuration dictionary
        """
        self.scan_type = scan_type
        self.config = config or {}
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.is_running = False
        self.should_stop = False
        
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set callback function for progress updates"""
        self.progress_callback = callback
    
    def update_progress(self, progress: float, message: str):
        """Update scan progress"""
        if self.progress_callback:
            self.progress_callback(progress, message)
        logger.info(f"[{self.scan_type}] Progress: {progress:.1f}% - {message}")
    
    def stop(self):
        """Signal the scanner to stop"""
        self.should_stop = True
        logger.info(f"[{self.scan_type}] Stop signal received")
    
    @abstractmethod
    async def configure(self, options: Dict[str, Any]) -> bool:
        """
        Configure the scanner with specific options.
        
        Args:
            options: Scanner-specific configuration options
            
        Returns:
            bool: True if configuration was successful
        """
        pass
    
    @abstractmethod
    async def validate_target(self, target_url: str) -> bool:
        """
        Validate if the target URL is suitable for this scanner.
        
        Args:
            target_url: The target URL to validate
            
        Returns:
            bool: True if target is valid for this scanner
        """
        pass
    
    @abstractmethod
    async def scan(self, target_url: str, options: Dict[str, Any] = None) -> ScanResult:
        """
        Perform the security scan.
        
        Args:
            target_url: The target URL to scan
            options: Optional scan-specific options
            
        Returns:
            ScanResult: The results of the scan
        """
        pass
    
    async def pre_scan_hook(self, target_url: str) -> bool:
        """
        Hook called before scan execution.
        Can be overridden by specific scanners for setup tasks.
        
        Args:
            target_url: The target URL to be scanned
            
        Returns:
            bool: True if pre-scan setup was successful
        """
        return True
    
    async def post_scan_hook(self, result: ScanResult) -> ScanResult:
        """
        Hook called after scan execution.
        Can be overridden by specific scanners for cleanup tasks.
        
        Args:
            result: The scan result
            
        Returns:
            ScanResult: The potentially modified scan result
        """
        return result
    
    def get_scanner_info(self) -> Dict[str, Any]:
        """Get information about this scanner"""
        return {
            "name": self.__class__.__name__,
            "scan_type": self.scan_type.value,
            "version": "1.0.0",
            "description": self.__doc__ or "Security scanner",
            "supported_options": self.get_supported_options()
        }
    
    def get_supported_options(self) -> List[str]:
        """Get list of supported configuration options"""
        return []
    
    async def health_check(self) -> bool:
        """
        Check if the scanner is healthy and ready to run.
        
        Returns:
            bool: True if scanner is healthy
        """
        return True