"""
ClaimFlow PDF Generation Service
===============================
Generates professional PDF reports for insurance claims including:
- Claim assessment reports
- Agent analysis summaries
- Audit trails
- Settlement documents
"""

import io
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# PDF generation libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available - PDF generation disabled")

logger = logging.getLogger("claimflow.pdf_service")

class PDFReportGenerator:
    def __init__(self):
        """Initialize PDF generator with styles and S3 client."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not installed. Install with: pip install reportlab")
        
        # Initialize S3 client for storing PDFs
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN")
        )
        
        self.reports_bucket = os.getenv("CLAIMFLOW_S3_REPORTS_BUCKET", "claimflow-reports")
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("PDF generator initialized")

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1f4e79'),
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2e75b6'),
            borderWidth=1,
            borderColor=colors.HexColor('#2e75b6'),
            borderPadding=5
        ))
        
        # Status styles
        self.styles.add(ParagraphStyle(
            name='StatusApproved',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.green,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusRejected',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='StatusPending',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.orange,
            fontName='Helvetica-Bold'
        ))

    def _format_currency(self, amount: float) -> str:
        """Format currency in Indian Rupees."""
        if amount is None:
            return "N/A"
        return f"₹{amount:,.2f}"

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%d %B %Y, %I:%M %p")
        except:
            return date_str

    def _get_status_style(self, status: str) -> str:
        """Get appropriate style for claim status."""
        status_lower = (status or "").lower()
        if status_lower in ["approved", "auto_approve"]:
            return "StatusApproved"
        elif status_lower in ["rejected", "reject"]:
            return "StatusRejected"
        else:
            return "StatusPending"

    def generate_claim_report(self, claim_data: Dict[str, Any]) -> bytes:
        """Generate comprehensive claim assessment report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Build the document content
        story = []
        
        # Header
        story.append(Paragraph("ClaimFlow Insurance Assessment Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Claim overview section
        story.append(Paragraph("Claim Overview", self.styles['CustomSubtitle']))
        
        claim_id = claim_data.get('claim_id', 'N/A')
        claim_type = (claim_data.get('claim_type', 'N/A')).title()
        status = claim_data.get('status', 'N/A')
        created_at = self._format_date(claim_data.get('created_at'))
        
        overview_data = [
            ['Claim ID:', claim_id],
            ['Claim Type:', claim_type],
            ['Status:', status],
            ['Submitted:', created_at],
            ['User ID:', claim_data.get('user_id', 'N/A')]
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Status section with color coding
        story.append(Paragraph("Assessment Result", self.styles['CustomSubtitle']))
        
        status_style = self._get_status_style(status)
        status_text = f"Status: {status.upper()}"
        story.append(Paragraph(status_text, self.styles[status_style]))
        
        # Settlement information
        settlement = claim_data.get('settlement_amount_inr')
        if settlement:
            settlement_text = f"Settlement Amount: {self._format_currency(settlement)}"
            story.append(Paragraph(settlement_text, self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Vision Agent Analysis
        vision_result = claim_data.get('vision_result', {})
        if vision_result:
            story.append(Paragraph("Vision Agent Analysis", self.styles['CustomSubtitle']))
            
            vision_data = [
                ['Domain:', vision_result.get('domain', 'N/A').title()],
                ['Document Type:', vision_result.get('document_type', 'N/A').replace('_', ' ').title()],
                ['Damage Estimate:', self._format_currency(vision_result.get('damage_estimate_inr'))],
                ['Confidence:', f"{vision_result.get('damage_confidence', 0)*100:.1f}%"],
                ['OCR Method:', vision_result.get('ocr_source', 'N/A').title()]
            ]
            
            vision_table = Table(vision_data, colWidths=[2*inch, 4*inch])
            vision_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(vision_table)
            
            # Structured data if available
            structured_data = vision_result.get('structured_data', {})
            if structured_data:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Extracted Information:", self.styles['Heading3']))
                
                for key, value in structured_data.items():
                    if value and key != 'document_type':
                        formatted_key = key.replace('_', ' ').title()
                        story.append(Paragraph(f"• {formatted_key}: {value}", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Forensic Agent Analysis
        forensic_result = claim_data.get('forensic_result', {})
        if forensic_result:
            story.append(Paragraph("Forensic Analysis", self.styles['CustomSubtitle']))
            
            fraud_score = forensic_result.get('fraud_score', 0)
            risk_level = forensic_result.get('risk_level', 'N/A')
            claim_confidence = forensic_result.get('claim_confidence', 0)
            
            forensic_data = [
                ['Risk Score:', f"{fraud_score}/100"],
                ['Risk Level:', risk_level.title()],
                ['Claim Confidence:', f"{claim_confidence*100:.1f}%"],
                ['Suspicious Indicators:', len(forensic_result.get('suspicious_indicators', []))]
            ]
            
            forensic_table = Table(forensic_data, colWidths=[2*inch, 4*inch])
            forensic_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(forensic_table)
            
            # Damage assessment
            damage_assessment = forensic_result.get('damage_assessment', {})
            if damage_assessment:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Damage Assessment:", self.styles['Heading3']))
                
                assessment_items = [
                    f"• Severity: {damage_assessment.get('severity', 'N/A').title()}",
                    f"• Estimated Cost: {self._format_currency(damage_assessment.get('estimated_damage_cost'))}",
                    f"• Recommended Settlement: {self._format_currency(damage_assessment.get('recommended_settlement'))}",
                    f"• Inflation Risk: {damage_assessment.get('inflation_risk', 'N/A').title()}"
                ]
                
                for item in assessment_items:
                    story.append(Paragraph(item, self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Policy Compliance
        policy_result = claim_data.get('policy_result', {})
        if policy_result:
            story.append(Paragraph("Policy Compliance", self.styles['CustomSubtitle']))
            
            policy_data = [
                ['Eligible:', '✓ Yes' if policy_result.get('eligible') else '✗ No'],
                ['IRDAI Compliant:', '✓ Yes' if policy_result.get('irdai_compliant') else '✗ No'],
                ['Requires Human Review:', '✓ Yes' if policy_result.get('requires_human') else '✗ No'],
                ['Regulation Used:', policy_result.get('regulation_used', 'N/A')]
            ]
            
            policy_table = Table(policy_data, colWidths=[2*inch, 4*inch])
            policy_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(policy_table)
            story.append(Spacer(1, 20))
        
        # Audit Trail
        audit_trail = claim_data.get('audit_trail', [])
        if audit_trail:
            story.append(PageBreak())
            story.append(Paragraph("Processing Audit Trail", self.styles['CustomSubtitle']))
            
            for entry in audit_trail[-10:]:  # Last 10 entries
                timestamp = self._format_date(entry.get('timestamp', ''))
                node = entry.get('node', 'Unknown')
                message = entry.get('message', '')
                
                story.append(Paragraph(f"<b>{timestamp}</b> - {node}", self.styles['Normal']))
                story.append(Paragraph(f"   {message}", self.styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 10))
        
        footer_text = f"Generated by ClaimFlow AI System on {datetime.now(timezone.utc).strftime('%d %B %Y at %H:%M UTC')}"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        disclaimer = ("This report is generated by AI agents and may require human verification for final decisions. "
                     "All monetary amounts are estimates based on available information.")
        story.append(Paragraph(f"<i>{disclaimer}</i>", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

    async def save_report_to_s3(self, claim_id: str, pdf_bytes: bytes) -> str:
        """Save PDF report to S3 and return the URL."""
        try:
            key = f"claim-reports/{claim_id}/assessment-report.pdf"
            
            self.s3_client.put_object(
                Bucket=self.reports_bucket,
                Key=key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                Metadata={
                    'claim_id': claim_id,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Generate presigned URL (valid for 7 days)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.reports_bucket, 'Key': key},
                ExpiresIn=7*24*3600  # 7 days
            )
            
            logger.info(f"Saved PDF report for claim {claim_id} to S3")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to save PDF to S3: {e}")
            raise

    async def generate_and_save_claim_report(self, claim_data: Dict[str, Any]) -> str:
        """Generate PDF report and save to S3, returning the download URL."""
        claim_id = claim_data.get('claim_id')
        if not claim_id:
            raise ValueError("Claim ID is required")
        
        # Generate PDF
        pdf_bytes = self.generate_claim_report(claim_data)
        
        # Save to S3
        download_url = await self.save_report_to_s3(claim_id, pdf_bytes)
        
        return download_url


# Global service instance
_pdf_service = None

def get_pdf_service() -> PDFReportGenerator:
    """Get the global PDF service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFReportGenerator()
    return _pdf_service


# Convenience function
async def generate_claim_pdf(claim_data: Dict[str, Any]) -> str:
    """Generate and save claim PDF report, returning download URL."""
    return await get_pdf_service().generate_and_save_claim_report(claim_data)