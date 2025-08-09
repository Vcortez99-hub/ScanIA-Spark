"""
Nmap Port Scanner Integration

Integrates with Nmap for network port scanning and service detection.
Provides comprehensive port scanning capabilities and service enumeration.
"""

import asyncio
import json
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urlparse
import tempfile
import os
import re

from .base_scanner import BaseScanner, ScanResult, ScanType, VulnerabilityData, VulnerabilitySeverity
from app.core.logging_simple import get_logger

logger = get_logger(__name__)


class NmapScanner(BaseScanner):
    """
    Nmap Scanner implementation.
    
    This scanner integrates with Nmap to perform network reconnaissance including:
    - Port scanning (TCP/UDP)
    - Service detection and version identification  
    - OS detection
    - Script scanning for vulnerability detection
    - Stealth scanning techniques
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(ScanType.NMAP_PORT, config)
        
        # Nmap configuration
        self.nmap_executable = self.config.get("nmap_executable", "nmap")
        self.max_scan_duration = self.config.get("max_scan_duration", 600)  # 10 minutes
        self.default_ports = self.config.get("default_ports", "1-1000")
        self.scan_techniques = self.config.get("scan_techniques", ["tcp_syn"])
        
        # Scan options
        self.enable_service_detection = self.config.get("enable_service_detection", True)
        self.enable_os_detection = self.config.get("enable_os_detection", False)
        self.enable_scripts = self.config.get("enable_scripts", True)
        self.enable_version_detection = self.config.get("enable_version_detection", True)
        self.timing_template = self.config.get("timing_template", 4)  # T4 aggressive
        
        # Script categories to run
        self.script_categories = self.config.get("script_categories", ["default", "safe", "vuln"])
        
        # Output format
        self.output_format = self.config.get("output_format", "xml")
    
    async def configure(self, options: Dict[str, Any]) -> bool:
        """Configure Nmap scanner with specific options"""
        try:
            # Update timing
            if "timing_template" in options:
                timing = options["timing_template"]
                if 0 <= timing <= 5:
                    self.timing_template = timing
            
            # Update ports
            if "ports" in options:
                self.default_ports = options["ports"]
                
            # Update scan techniques
            if "scan_techniques" in options:
                valid_techniques = ["tcp_syn", "tcp_connect", "udp", "tcp_ack", "tcp_fin"]
                techniques = options["scan_techniques"]
                if isinstance(techniques, list) and all(t in valid_techniques for t in techniques):
                    self.scan_techniques = techniques
            
            # Update detection options
            if "enable_service_detection" in options:
                self.enable_service_detection = options["enable_service_detection"]
                
            if "enable_os_detection" in options:
                self.enable_os_detection = options["enable_os_detection"]
                
            if "enable_scripts" in options:
                self.enable_scripts = options["enable_scripts"]
                
            if "enable_version_detection" in options:
                self.enable_version_detection = options["enable_version_detection"]
            
            # Update script categories
            if "script_categories" in options:
                self.script_categories = options["script_categories"]
            
            logger.info("Nmap scanner configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring Nmap scanner: {str(e)}")
            return False
    
    async def validate_target(self, target_url: str) -> bool:
        """Validate if target is suitable for Nmap scanning"""
        try:
            # Extract hostname/IP from URL
            if "://" in target_url:
                parsed = urlparse(target_url)
                target_host = parsed.netloc.split(':')[0]  # Remove port if present
            else:
                target_host = target_url.split(':')[0]  # Handle plain hostname/IP
            
            # Basic validation - check if it looks like a hostname or IP
            if not target_host or len(target_host) < 1:
                logger.error("Invalid target hostname/IP")
                return False
            
            # Check if target is reachable with a simple ping test
            try:
                # Try to resolve hostname or ping IP
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "3", target_host] if os.name != 'nt' else ["ping", "-n", "1", "-w", "3000", target_host],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"Target {target_host} is reachable")
                else:
                    logger.warning(f"Target {target_host} may not be reachable, but continuing scan")
                    
            except subprocess.TimeoutExpired:
                logger.warning("Ping timeout, but continuing with scan")
            
            logger.info(f"Target validated for Nmap scan: {target_host}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating target: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Nmap is installed and accessible"""
        try:
            # Check if nmap is available
            result = subprocess.run(
                [self.nmap_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                logger.info(f"Nmap health check passed - {version_info}")
                return True
            else:
                logger.error(f"Nmap health check failed - return code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            logger.error("Nmap executable not found")
            return False
        except Exception as e:
            logger.error(f"Nmap health check error: {str(e)}")
            return False
    
    async def scan(self, target_url: str, options: Dict[str, Any] = None) -> ScanResult:
        """Perform Nmap port scan"""
        start_time = datetime.utcnow()
        scan_result = ScanResult(
            scan_type=self.scan_type,
            target_url=target_url,
            status="running",
            start_time=start_time,
            metadata={"nmap_version": await self._get_nmap_version()}
        )
        
        try:
            self.is_running = True
            self.update_progress(0, "Initializing Nmap scan")
            
            # Health check
            if not await self.health_check():
                raise Exception("Nmap is not accessible")
            
            # Configure scan options
            if options:
                await self.configure(options)
            
            # Validate and extract target
            if not await self.validate_target(target_url):
                raise Exception("Target validation failed")
            
            target_host = self._extract_host_from_url(target_url)
            
            self.update_progress(10, f"Starting port scan of {target_host}")
            
            # Build and execute Nmap command
            nmap_command = self._build_nmap_command(target_host, options or {})
            
            self.update_progress(20, "Executing Nmap scan...")
            
            # Execute scan
            scan_output = await self._execute_nmap_scan(nmap_command)
            
            self.update_progress(80, "Parsing scan results...")
            
            # Parse results
            parsed_results = await self._parse_nmap_output(scan_output, target_host)
            vulnerabilities = self._convert_to_vulnerabilities(parsed_results, target_host)
            
            # Update scan result
            end_time = datetime.utcnow()
            scan_result.end_time = end_time
            scan_result.duration_seconds = (end_time - start_time).total_seconds()
            scan_result.status = "completed"
            scan_result.vulnerabilities = vulnerabilities
            scan_result.raw_output = scan_output
            scan_result.metadata.update({
                "target_host": target_host,
                "ports_scanned": self.default_ports,
                "scan_techniques": self.scan_techniques,
                "open_ports": len([v for v in vulnerabilities if "open port" in v.title.lower()]),
                "services_detected": len([v for v in vulnerabilities if "service detected" in v.title.lower()])
            })
            
            self.update_progress(100, f"Scan completed - {len(vulnerabilities)} findings")
            
        except Exception as e:
            logger.error(f"Nmap scan error: {str(e)}")
            scan_result.status = "failed"
            scan_result.error_message = str(e)
            scan_result.end_time = datetime.utcnow()
            if scan_result.start_time:
                scan_result.duration_seconds = (scan_result.end_time - scan_result.start_time).total_seconds()
        
        finally:
            self.is_running = False
            
        return scan_result
    
    def _extract_host_from_url(self, target_url: str) -> str:
        """Extract hostname/IP from URL"""
        if "://" in target_url:
            parsed = urlparse(target_url)
            return parsed.netloc.split(':')[0]
        else:
            return target_url.split(':')[0]
    
    def _build_nmap_command(self, target_host: str, options: Dict[str, Any]) -> List[str]:
        """Build Nmap command with appropriate options"""
        command = [self.nmap_executable]
        
        # Timing template
        command.extend([f"-T{self.timing_template}"])
        
        # Scan techniques
        for technique in self.scan_techniques:
            if technique == "tcp_syn":
                command.append("-sS")
            elif technique == "tcp_connect":
                command.append("-sT") 
            elif technique == "udp":
                command.append("-sU")
            elif technique == "tcp_ack":
                command.append("-sA")
            elif technique == "tcp_fin":
                command.append("-sF")
        
        # Port specification
        ports = options.get("ports", self.default_ports)
        command.extend(["-p", ports])
        
        # Service detection
        if self.enable_service_detection:
            command.append("-sV")
        
        # Version detection
        if self.enable_version_detection:
            command.append("-sC")
        
        # OS detection
        if self.enable_os_detection:
            command.append("-O")
        
        # Scripts
        if self.enable_scripts and self.script_categories:
            script_args = ",".join(self.script_categories)
            command.extend(["--script", script_args])
        
        # Output format
        if self.output_format == "xml":
            command.append("-oX")
            command.append("-")  # Output to stdout
        
        # Disable DNS resolution for faster scanning
        command.append("-n")
        
        # Disable ping
        command.append("-Pn")
        
        # Target
        command.append(target_host)
        
        logger.info(f"Nmap command: {' '.join(command)}")
        return command
    
    async def _execute_nmap_scan(self, command: List[str]) -> str:
        """Execute Nmap scan command asynchronously"""
        try:
            # Start process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.max_scan_duration
                )
            except asyncio.TimeoutError:
                # Kill process if timeout
                process.terminate()
                await process.wait()
                raise Exception("Nmap scan timeout")
            
            if process.returncode != 0 and stderr:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.warning(f"Nmap stderr: {error_msg}")
            
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output.strip():
                raise Exception("Nmap produced no output")
            
            return output
            
        except Exception as e:
            logger.error(f"Error executing Nmap scan: {str(e)}")
            raise
    
    async def _parse_nmap_output(self, output: str, target_host: str) -> Dict[str, Any]:
        """Parse Nmap XML output"""
        results = {
            "host": target_host,
            "ports": [],
            "services": [],
            "scripts": [],
            "os_detection": None
        }
        
        try:
            # Parse XML
            root = ET.fromstring(output)
            
            # Find host information
            host_elem = root.find(".//host")
            if host_elem is None:
                logger.warning("No host information found in Nmap output")
                return results
            
            # Parse ports
            ports_elem = host_elem.find("ports")
            if ports_elem is not None:
                for port_elem in ports_elem.findall("port"):
                    port_info = {
                        "port": port_elem.get("portid"),
                        "protocol": port_elem.get("protocol"),
                        "state": None,
                        "service": None,
                        "version": None,
                        "scripts": []
                    }
                    
                    # Port state
                    state_elem = port_elem.find("state")
                    if state_elem is not None:
                        port_info["state"] = state_elem.get("state")
                    
                    # Service information
                    service_elem = port_elem.find("service")
                    if service_elem is not None:
                        port_info["service"] = {
                            "name": service_elem.get("name"),
                            "product": service_elem.get("product"),
                            "version": service_elem.get("version"),
                            "extrainfo": service_elem.get("extrainfo")
                        }
                    
                    # Script results
                    for script_elem in port_elem.findall("script"):
                        script_info = {
                            "id": script_elem.get("id"),
                            "output": script_elem.get("output")
                        }
                        port_info["scripts"].append(script_info)
                    
                    results["ports"].append(port_info)
            
            # Parse OS detection
            os_elem = host_elem.find("os")
            if os_elem is not None:
                osmatch_elem = os_elem.find("osmatch")
                if osmatch_elem is not None:
                    results["os_detection"] = {
                        "name": osmatch_elem.get("name"),
                        "accuracy": osmatch_elem.get("accuracy")
                    }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing Nmap XML output: {str(e)}")
            # Try to parse as text output
            results["raw_text"] = output
        except Exception as e:
            logger.error(f"Error processing Nmap output: {str(e)}")
            results["raw_text"] = output
        
        return results
    
    def _convert_to_vulnerabilities(self, parsed_results: Dict[str, Any], target_host: str) -> List[VulnerabilityData]:
        """Convert parsed Nmap results to vulnerability data"""
        vulnerabilities = []
        
        try:
            # Process open ports
            for port_info in parsed_results.get("ports", []):
                if port_info.get("state") == "open":
                    port_num = port_info.get("port")
                    protocol = port_info.get("protocol", "tcp")
                    service_info = port_info.get("service", {})
                    
                    # Create vulnerability for open port
                    title = f"Open Port {port_num}/{protocol.upper()}"
                    description = f"Port {port_num} is open on {target_host}"
                    
                    if service_info and service_info.get("name"):
                        service_name = service_info.get("name")
                        title += f" - {service_name}"
                        description += f" running {service_name}"
                        
                        if service_info.get("product"):
                            product = service_info.get("product")
                            description += f" ({product}"
                            
                            if service_info.get("version"):
                                version = service_info.get("version")
                                description += f" {version}"
                            
                            description += ")"
                    
                    # Determine severity based on port and service
                    severity = self._assess_port_severity(port_num, service_info)
                    
                    vuln = VulnerabilityData(
                        vulnerability_id=f"nmap_port_{target_host}_{port_num}_{protocol}",
                        title=title,
                        description=description,
                        severity=severity,
                        solution=self._get_port_remediation(port_num, service_info),
                        affected_url=f"{target_host}:{port_num}",
                        evidence={"port_info": port_info, "service": service_info},
                        tags=["port-scan", "network", protocol]
                    )
                    
                    vulnerabilities.append(vuln)
                    
                    # Process script results for this port
                    for script_info in port_info.get("scripts", []):
                        script_vuln = self._process_script_result(
                            script_info, target_host, port_num, protocol
                        )
                        if script_vuln:
                            vulnerabilities.append(script_vuln)
            
            # Process OS detection
            if parsed_results.get("os_detection"):
                os_info = parsed_results["os_detection"]
                vuln = VulnerabilityData(
                    vulnerability_id=f"nmap_os_{target_host}",
                    title=f"OS Detection: {os_info.get('name', 'Unknown')}",
                    description=f"Operating system detected as: {os_info.get('name', 'Unknown')} (Accuracy: {os_info.get('accuracy', 'N/A')}%)",
                    severity=VulnerabilitySeverity.INFO,
                    solution="This is informational only. Review system configuration if OS disclosure is a concern.",
                    affected_url=target_host,
                    evidence={"os_info": os_info},
                    tags=["os-detection", "fingerprinting"]
                )
                vulnerabilities.append(vuln)
            
        except Exception as e:
            logger.error(f"Error converting Nmap results to vulnerabilities: {str(e)}")
        
        return vulnerabilities
    
    def _assess_port_severity(self, port: str, service_info: Dict[str, Any]) -> VulnerabilitySeverity:
        """Assess severity of open port based on port number and service"""
        port_num = int(port)
        service_name = service_info.get("name", "").lower()
        
        # High-risk ports
        high_risk_ports = [21, 23, 25, 53, 135, 139, 445, 1433, 1521, 3306, 3389, 5432]
        
        # Medium-risk ports  
        medium_risk_ports = [22, 80, 110, 143, 443, 993, 995]
        
        # Check for dangerous services
        dangerous_services = ["telnet", "ftp", "rsh", "rlogin", "netbios", "smb"]
        
        if port_num in high_risk_ports or any(svc in service_name for svc in dangerous_services):
            return VulnerabilitySeverity.HIGH
        elif port_num in medium_risk_ports:
            return VulnerabilitySeverity.MEDIUM
        else:
            return VulnerabilitySeverity.LOW
    
    def _get_port_remediation(self, port: str, service_info: Dict[str, Any]) -> str:
        """Get remediation advice for open port"""
        port_num = int(port)
        service_name = service_info.get("name", "").lower()
        
        remediation_map = {
            21: "Replace FTP with SFTP or FTPS for secure file transfer",
            22: "SSH is relatively secure, ensure strong authentication and latest version",
            23: "Replace Telnet with SSH for secure remote access",
            25: "Secure SMTP configuration and prevent open relay",
            53: "Secure DNS server configuration and restrict zone transfers",
            80: "Consider using HTTPS instead of HTTP for web traffic",
            110: "Use secure POP3S or IMAP over TLS instead of plain POP3",
            135: "Windows RPC - restrict access and apply latest security patches",
            139: "NetBIOS - disable if not needed, restrict network access",
            143: "Use IMAP over TLS instead of plain IMAP",
            443: "HTTPS is secure, ensure proper TLS configuration",
            445: "SMB - ensure latest patches and restrict network access",
            993: "IMAPS - secure, verify TLS configuration",
            995: "POP3S - secure, verify TLS configuration",
            1433: "MSSQL - restrict network access and use SQL authentication",
            1521: "Oracle DB - restrict network access and secure configuration",
            3306: "MySQL - restrict network access and secure configuration",
            3389: "RDP - use strong authentication and restrict network access",
            5432: "PostgreSQL - restrict network access and secure configuration"
        }
        
        if port_num in remediation_map:
            return remediation_map[port_num]
        elif "telnet" in service_name:
            return "Replace Telnet with SSH for secure remote access"
        elif "ftp" in service_name:
            return "Replace FTP with SFTP or FTPS for secure file transfer"
        elif any(db in service_name for db in ["mysql", "postgres", "oracle", "mssql"]):
            return "Restrict database access to authorized networks only"
        else:
            return f"Review necessity of {service_name} service and restrict network access if possible"
    
    def _process_script_result(self, script_info: Dict[str, Any], target_host: str, port: str, protocol: str) -> Optional[VulnerabilityData]:
        """Process Nmap script results and convert to vulnerabilities"""
        script_id = script_info.get("id", "")
        script_output = script_info.get("output", "")
        
        if not script_output:
            return None
        
        # Map script IDs to vulnerability types
        vuln_scripts = {
            "http-sql-injection": VulnerabilitySeverity.HIGH,
            "http-xssed": VulnerabilitySeverity.HIGH,
            "http-csrf": VulnerabilitySeverity.MEDIUM,
            "http-slowloris-check": VulnerabilitySeverity.MEDIUM,
            "smb-vuln-ms17-010": VulnerabilitySeverity.CRITICAL,
            "smb-vuln-ms08-067": VulnerabilitySeverity.CRITICAL,
            "ssl-poodle": VulnerabilitySeverity.MEDIUM,
            "ssl-heartbleed": VulnerabilitySeverity.HIGH
        }
        
        severity = vuln_scripts.get(script_id, VulnerabilitySeverity.INFO)
        
        # Only create vulnerabilities for actual issues found
        if any(keyword in script_output.lower() for keyword in ["vulnerable", "found", "detected", "exposed"]):
            severity = vuln_scripts.get(script_id, VulnerabilitySeverity.MEDIUM)
        else:
            severity = VulnerabilitySeverity.INFO
        
        return VulnerabilityData(
            vulnerability_id=f"nmap_script_{target_host}_{port}_{script_id}",
            title=f"Script Detection: {script_id}",
            description=f"Nmap script {script_id} found: {script_output[:200]}...",
            severity=severity,
            solution=f"Review and remediate issues identified by Nmap script {script_id}",
            affected_url=f"{target_host}:{port}",
            evidence={"script_output": script_output, "script_id": script_id},
            tags=["script-scan", "nmap", script_id],
            confidence="Medium"
        )
    
    async def _get_nmap_version(self) -> str:
        """Get Nmap version information"""
        try:
            result = subprocess.run(
                [self.nmap_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from first line
                version_line = result.stdout.split('\n')[0]
                match = re.search(r'(\d+\.\d+)', version_line)
                if match:
                    return match.group(1)
                return version_line.strip()
        except:
            pass
        return "unknown"
    
    def get_supported_options(self) -> List[str]:
        """Get list of supported configuration options"""
        return [
            "ports",
            "scan_techniques",
            "timing_template",
            "enable_service_detection",
            "enable_os_detection", 
            "enable_scripts",
            "enable_version_detection",
            "script_categories",
            "max_scan_duration"
        ]