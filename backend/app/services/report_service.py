"""
PDF Report Generation Service

Generates comprehensive security scan reports in PDF format with charts,
vulnerability details, and executive summaries.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import base64
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# PDF generation imports
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, colors
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. Install reportlab to enable PDF generation")

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib not available. Install matplotlib for advanced charts")

from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.report import Report, ReportFormat, ReportStatus
from app.core.logging_simple import get_logger

logger = get_logger(__name__)


class ReportGenerationException(Exception):
    """Exception raised during report generation"""
    pass


class PDFReportGenerator:
    """
    Generates PDF reports for security scan results.
    
    Features:
    - Executive summary with charts
    - Detailed vulnerability listings
    - Risk assessment and recommendations
    - Custom styling and branding
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ReportGenerationException("ReportLab library not available")
            
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Report configuration
        self.page_size = A4
        self.margin = 2*cm
        
        # Colors
        self.primary_color = HexColor('#2563eb')
        self.danger_color = HexColor('#dc2626')
        self.warning_color = HexColor('#d97706')
        self.success_color = HexColor('#16a34a')
        self.info_color = HexColor('#0891b2')
        
    def setup_custom_styles(self):
        """Set up custom paragraph styles for the report"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ScanIATitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=self.primary_color,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=self.primary_color,
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Vulnerability title style
        self.styles.add(ParagraphStyle(
            name='VulnTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.danger_color,
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Risk level styles
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            color = self._get_severity_color(severity)
            self.styles.add(ParagraphStyle(
                name=f'Risk{severity.title()}',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=color,
                fontName='Helvetica-Bold'
            ))
    
    def _get_severity_color(self, severity: str) -> HexColor:
        """Get color for severity level"""
        severity_colors = {
            'critical': HexColor('#7f1d1d'),
            'high': HexColor('#dc2626'),
            'medium': HexColor('#d97706'),
            'low': HexColor('#65a30d'),
            'info': HexColor('#0891b2')
        }
        return severity_colors.get(severity.lower(), HexColor('#6b7280'))
    
    async def generate_executive_summary(self, scan: Scan, output_path: str) -> str:
        """
        Generate executive summary PDF report
        
        Args:
            scan: Scan model with vulnerabilities
            output_path: Path to save the PDF file
            
        Returns:
            Path to generated PDF file
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page(scan))
            
            # Executive summary
            story.extend(self._create_executive_summary(scan))
            
            # Risk assessment
            story.extend(self._create_risk_assessment(scan))
            
            # Vulnerability overview
            story.extend(self._create_vulnerability_overview(scan))
            
            # Recommendations
            story.extend(self._create_recommendations(scan))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Executive summary PDF generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            raise ReportGenerationException(f"Executive summary generation failed: {str(e)}")
    
    async def generate_technical_report(self, scan: Scan, output_path: str) -> str:
        """
        Generate detailed technical PDF report
        
        Args:
            scan: Scan model with vulnerabilities
            output_path: Path to save the PDF file
            
        Returns:
            Path to generated PDF file
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page(scan, report_type="Technical"))
            
            # Scan details
            story.extend(self._create_scan_details(scan))
            
            # Detailed vulnerabilities
            story.extend(self._create_detailed_vulnerabilities(scan))
            
            # Technical appendix
            story.extend(self._create_technical_appendix(scan))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Technical report PDF generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate technical report: {e}")
            raise ReportGenerationException(f"Technical report generation failed: {str(e)}")
    
    def _create_title_page(self, scan: Scan, report_type: str = "Executive") -> List:
        """Create the title page elements"""
        elements = []
        
        # Main title
        title = f"ScanIA - Relatório {report_type}"
        elements.append(Paragraph(title, self.styles['ScanIATitle']))
        elements.append(Spacer(1, 30))
        
        # Scan information table
        scan_info = [
            ['Target URL:', scan.target_url],
            ['Data do Scan:', scan.created_at.strftime('%d/%m/%Y %H:%M')],
            ['Status:', scan.status.value.title()],
            ['Duração:', f"{scan.duration_seconds or 0}s"],
            ['Tipos de Scan:', ', '.join(scan.scan_types)],
        ]
        
        if scan.started_at:
            scan_info.append(['Iniciado em:', scan.started_at.strftime('%d/%m/%Y %H:%M')])
        
        if scan.completed_at:
            scan_info.append(['Concluído em:', scan.completed_at.strftime('%d/%m/%Y %H:%M')])
        
        table = Table(scan_info, colWidths=[3*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 40))
        
        # Page break
        elements.append(PageBreak())
        
        return elements
    
    def _create_executive_summary(self, scan: Scan) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Resumo Executivo", self.styles['SectionHeader']))
        
        summary = scan.vulnerability_summary
        total_vulns = sum(summary.values())
        
        if total_vulns == 0:
            elements.append(Paragraph(
                "Parabéns! Nenhuma vulnerabilidade foi identificada durante este scan. "
                "No entanto, recomendamos scans regulares para manter a segurança.",
                self.styles['Normal']
            ))
        else:
            # Summary paragraph
            summary_text = (
                f"Este relatório apresenta os resultados da análise de segurança realizada em "
                f"<b>{scan.target_url}</b>. Foram identificadas <b>{total_vulns}</b> vulnerabilidades, "
                f"sendo {summary.get('critical', 0)} críticas, {summary.get('high', 0)} altas, "
                f"{summary.get('medium', 0)} médias, {summary.get('low', 0)} baixas e "
                f"{summary.get('info', 0)} informativas."
            )
            
            elements.append(Paragraph(summary_text, self.styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Vulnerability chart
            chart_image = self._create_vulnerability_chart(summary)
            if chart_image:
                elements.append(chart_image)
                elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_risk_assessment(self, scan: Scan) -> List:
        """Create risk assessment section"""
        elements = []
        
        elements.append(Paragraph("Avaliação de Risco", self.styles['SectionHeader']))
        
        risk_score = scan.calculate_risk_score()
        risk_level = self._calculate_risk_level(scan.vulnerability_summary)
        
        elements.append(Paragraph(f"<b>Nível de Risco Geral:</b> {risk_level}", self.styles['Normal']))
        elements.append(Paragraph(f"<b>Score de Risco:</b> {risk_score:.1f}/100", self.styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # Risk level explanation
        risk_explanations = {
            'Low': 'Baixo risco. As vulnerabilidades encontradas são menores e não representam ameaça imediata.',
            'Medium': 'Risco médio. Recomenda-se correção das vulnerabilidades em prazo razoável.',
            'High': 'Alto risco. As vulnerabilidades devem ser corrigidas com prioridade.',
            'Critical': 'Risco crítico. Correção imediata necessária para evitar comprometimento.'
        }
        
        if risk_level in risk_explanations:
            elements.append(Paragraph(risk_explanations[risk_level], self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_vulnerability_overview(self, scan: Scan) -> List:
        """Create vulnerability overview section"""
        elements = []
        
        elements.append(Paragraph("Principais Vulnerabilidades", self.styles['SectionHeader']))
        
        if not scan.vulnerabilities:
            elements.append(Paragraph("Nenhuma vulnerabilidade encontrada.", self.styles['Normal']))
            return elements
        
        # Sort vulnerabilities by severity and CVSS score
        sorted_vulns = sorted(
            scan.vulnerabilities,
            key=lambda v: (v.severity_weight, v.cvss_score or 0),
            reverse=True
        )
        
        # Show top 10 vulnerabilities
        for i, vuln in enumerate(sorted_vulns[:10], 1):
            elements.append(Paragraph(f"{i}. {vuln.title}", self.styles['VulnTitle']))
            
            # Vulnerability details table
            vuln_data = [
                ['Severidade:', vuln.severity.value.title()],
                ['CVSS Score:', str(vuln.cvss_score or 'N/A')],
                ['URL Afetada:', vuln.affected_url],
            ]
            
            if vuln.cve_id:
                vuln_data.append(['CVE ID:', vuln.cve_id])
            
            table = Table(vuln_data, colWidths=[3*cm, 8*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 15))
        
        if len(sorted_vulns) > 10:
            remaining = len(sorted_vulns) - 10
            elements.append(Paragraph(f"... e mais {remaining} vulnerabilidades no relatório técnico.", self.styles['Normal']))
        
        return elements
    
    def _create_recommendations(self, scan: Scan) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recomendações", self.styles['SectionHeader']))
        
        summary = scan.vulnerability_summary
        recommendations = []
        
        if summary.get('critical', 0) > 0:
            recommendations.append("Corrigir imediatamente todas as vulnerabilidades críticas encontradas.")
        
        if summary.get('high', 0) > 0:
            recommendations.append("Priorizar a correção de vulnerabilidades de alto risco.")
        
        if summary.get('medium', 0) > 0:
            recommendations.append("Planejar correção de vulnerabilidades médias no próximo ciclo de manutenção.")
        
        if sum(summary.values()) > 0:
            recommendations.extend([
                "Implementar um programa regular de scans de segurança.",
                "Revisar e atualizar políticas de segurança da aplicação.",
                "Considerar implementar um Web Application Firewall (WAF).",
                "Realizar treinamento de segurança para a equipe de desenvolvimento.",
            ])
        else:
            recommendations.extend([
                "Manter as práticas atuais de segurança.",
                "Realizar scans regulares para monitoramento contínuo.",
                "Considerar testes de penetração mais avançados.",
            ])
        
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", self.styles['Normal']))
            elements.append(Spacer(1, 8))
        
        return elements
    
    def _create_scan_details(self, scan: Scan) -> List:
        """Create detailed scan information section"""
        elements = []
        
        elements.append(Paragraph("Detalhes do Scan", self.styles['SectionHeader']))
        
        # Detailed scan information
        scan_details = [
            ['ID do Scan:', str(scan.id)],
            ['Número do Scan:', str(scan.scan_number)],
            ['Target URL:', scan.target_url],
            ['Tipos de Scan:', ', '.join(scan.scan_types)],
            ['Ambiente:', scan.environment_type or 'N/A'],
            ['Status:', scan.status.value.title()],
        ]
        
        if scan.options:
            scan_details.append(['Opções:', json.dumps(scan.options, indent=2)])
        
        table = Table(scan_details, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_detailed_vulnerabilities(self, scan: Scan) -> List:
        """Create detailed vulnerability section"""
        elements = []
        
        elements.append(Paragraph("Vulnerabilidades Detalhadas", self.styles['SectionHeader']))
        
        if not scan.vulnerabilities:
            elements.append(Paragraph("Nenhuma vulnerabilidade encontrada.", self.styles['Normal']))
            return elements
        
        # Group vulnerabilities by severity
        vuln_groups = {}
        for vuln in scan.vulnerabilities:
            severity = vuln.severity.value
            if severity not in vuln_groups:
                vuln_groups[severity] = []
            vuln_groups[severity].append(vuln)
        
        # Process each severity group
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        
        for severity in severity_order:
            if severity not in vuln_groups:
                continue
                
            vulns = vuln_groups[severity]
            elements.append(Paragraph(f"Vulnerabilidades {severity.title()} ({len(vulns)})", self.styles['VulnTitle']))
            
            for i, vuln in enumerate(vulns, 1):
                elements.append(Paragraph(f"{i}. {vuln.title}", self.styles['Normal']))
                elements.append(Spacer(1, 8))
                
                # Description
                elements.append(Paragraph(f"<b>Descrição:</b>", self.styles['Normal']))
                elements.append(Paragraph(vuln.description, self.styles['Normal']))
                elements.append(Spacer(1, 8))
                
                # Solution
                if vuln.solution:
                    elements.append(Paragraph(f"<b>Solução:</b>", self.styles['Normal']))
                    elements.append(Paragraph(vuln.solution, self.styles['Normal']))
                    elements.append(Spacer(1, 8))
                
                # Technical details
                tech_details = [
                    ['URL Afetada:', vuln.affected_url],
                    ['Severidade:', vuln.severity.value.title()],
                    ['CVSS Score:', str(vuln.cvss_score or 'N/A')],
                ]
                
                if vuln.cve_id:
                    tech_details.append(['CVE ID:', vuln.cve_id])
                
                if vuln.affected_parameter:
                    tech_details.append(['Parâmetro:', vuln.affected_parameter])
                
                table = Table(tech_details, colWidths=[3*cm, 9*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#374151')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_technical_appendix(self, scan: Scan) -> List:
        """Create technical appendix section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Apêndice Técnico", self.styles['SectionHeader']))
        
        # Scan statistics
        elements.append(Paragraph("Estatísticas do Scan", self.styles['Heading2']))
        
        stats = [
            ['Total de Vulnerabilidades:', str(len(scan.vulnerabilities))],
            ['Score de Risco:', f"{scan.calculate_risk_score():.1f}/100"],
            ['Duração do Scan:', f"{scan.duration_seconds or 0} segundos"],
        ]
        
        summary = scan.vulnerability_summary
        for severity, count in summary.items():
            stats.append([f"Vulnerabilidades {severity.title()}:", str(count)])
        
        table = Table(stats, colWidths=[5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Methodology
        elements.append(Paragraph("Metodologia", self.styles['Heading2']))
        methodology_text = (
            "Este scan foi realizado utilizando ferramentas automatizadas de segurança, incluindo "
            "OWASP ZAP para vulnerabilidades de aplicações web e Nmap para análise de rede. "
            "Os resultados foram processados e classificados de acordo com o padrão CVSS (Common "
            "Vulnerability Scoring System) para priorização de correções."
        )
        elements.append(Paragraph(methodology_text, self.styles['Normal']))
        
        return elements
    
    def _create_vulnerability_chart(self, summary: Dict[str, int]):
        """Create vulnerability distribution chart"""
        if not MATPLOTLIB_AVAILABLE or sum(summary.values()) == 0:
            return None
            
        try:
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = []
            sizes = []
            colors = []
            
            severity_colors = {
                'critical': '#7f1d1d',
                'high': '#dc2626', 
                'medium': '#d97706',
                'low': '#65a30d',
                'info': '#0891b2'
            }
            
            for severity, count in summary.items():
                if count > 0:
                    labels.append(f"{severity.title()} ({count})")
                    sizes.append(count)
                    colors.append(severity_colors.get(severity, '#6b7280'))
            
            if not sizes:
                return None
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Distribuição de Vulnerabilidades por Severidade', fontsize=14, fontweight='bold')
            
            # Save to temporary file
            chart_path = f"/tmp/vuln_chart_{uuid.uuid4()}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Create ReportLab image
            img = Image(chart_path, width=12*cm, height=9*cm)
            
            # Clean up temporary file
            try:
                Path(chart_path).unlink()
            except Exception:
                pass
            
            return img
            
        except Exception as e:
            logger.warning(f"Failed to create vulnerability chart: {e}")
            return None
    
    def _calculate_risk_level(self, summary: Dict[str, int]) -> str:
        """Calculate overall risk level based on vulnerability summary"""
        if summary.get('critical', 0) > 0:
            return 'Critical'
        elif summary.get('high', 0) > 2:
            return 'Critical'
        elif summary.get('high', 0) > 0:
            return 'High'
        elif summary.get('medium', 0) > 5:
            return 'High'
        elif summary.get('medium', 0) > 0:
            return 'Medium'
        elif summary.get('low', 0) > 10:
            return 'Medium'
        elif summary.get('low', 0) > 0:
            return 'Low'
        else:
            return 'Low'


class ReportService:
    """
    Service for managing scan report generation and storage.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pdf_generator = PDFReportGenerator() if REPORTLAB_AVAILABLE else None
        
        # Report storage configuration
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_report(
        self, 
        scan_id: str, 
        report_format: ReportFormat = ReportFormat.PDF,
        report_type: str = "executive"
    ) -> str:
        """
        Generate a report for a scan
        
        Args:
            scan_id: Scan ID
            report_format: Format of the report (PDF, HTML, etc.)
            report_type: Type of report (executive, technical)
            
        Returns:
            Report ID
        """
        try:
            # Get scan with vulnerabilities
            result = await self.db.execute(
                select(Scan)
                .options(selectinload(Scan.vulnerabilities))
                .where(Scan.id == scan_id)
            )
            scan = result.scalar_one_or_none()
            
            if not scan:
                raise ReportGenerationException(f"Scan not found: {scan_id}")
            
            # Create report record
            report = Report(
                scan_id=scan_id,
                format=report_format,
                status=ReportStatus.GENERATING,
                title=f"{report_type.title()} Report - {scan.target_url}",
                description=f"Security scan report for {scan.target_url}",
                template_name=report_type
            )
            
            self.db.add(report)
            await self.db.commit()
            await self.db.refresh(report)
            
            # Generate report in background
            asyncio.create_task(self._generate_report_async(report.id, scan, report_type))
            
            return str(report.id)
            
        except Exception as e:
            logger.error(f"Failed to create report job: {e}")
            raise ReportGenerationException(f"Report creation failed: {str(e)}")
    
    async def _generate_report_async(self, report_id: str, scan: Scan, report_type: str):
        """Generate report asynchronously"""
        try:
            # Get report record
            result = await self.db.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()
            
            if not report:
                logger.error(f"Report not found: {report_id}")
                return
            
            # Generate file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_{scan.scan_number}_{report_type}_{timestamp}.pdf"
            file_path = self.reports_dir / filename
            
            # Generate PDF
            if report_type == "executive":
                await self.pdf_generator.generate_executive_summary(scan, str(file_path))
            elif report_type == "technical":
                await self.pdf_generator.generate_technical_report(scan, str(file_path))
            else:
                raise ReportGenerationException(f"Unknown report type: {report_type}")
            
            # Update report record
            file_size = file_path.stat().st_size
            
            report.status = ReportStatus.COMPLETED
            report.file_path = str(file_path)
            report.file_size = file_size
            report.mime_type = "application/pdf"
            report.generated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Report generated successfully: {report_id}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            
            # Update report status to failed
            try:
                result = await self.db.execute(
                    select(Report).where(Report.id == report_id)
                )
                report = result.scalar_one_or_none()
                
                if report:
                    report.status = ReportStatus.FAILED
                    report.error_message = str(e)
                    await self.db.commit()
                    
            except Exception as update_error:
                logger.error(f"Failed to update report status: {update_error}")
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def list_scan_reports(self, scan_id: str) -> List[Report]:
        """List all reports for a scan"""
        result = await self.db.execute(
            select(Report)
            .where(Report.scan_id == scan_id)
            .order_by(Report.created_at.desc())
        )
        return result.scalars().all()
    
    def get_report_file_path(self, report: Report) -> Optional[str]:
        """Get the file path for a completed report"""
        if report.status != ReportStatus.COMPLETED or not report.file_path:
            return None
        
        file_path = Path(report.file_path)
        if file_path.exists():
            return str(file_path)
        
        return None