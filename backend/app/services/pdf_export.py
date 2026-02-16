"""PDF export service for coverage reports.

This module handles exporting CoverageIQ reports to PDF format
using ReportLab for HTML-to-PDF generation.
"""
import os
import io
from datetime import datetime
from typing import Dict, List, Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


class PDFExportError(Exception):
    """Raised when PDF export fails."""
    pass


class PDFExporter:
    """Export coverage reports to PDF.
    
    This class handles creating professional PDF reports with:
    - Proper formatting and styling
    - Color-coded scores and recommendations
    - Clean typography
    """
    
    def __init__(self):
        """Initialize the PDF exporter."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CoverageTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=16,
            spaceAfter=8,
            borderPadding=(0, 0, 4, 0),
            borderWidth=1,
            borderColor=colors.HexColor('#2c3e50'),
            borderDash=(5, 5)
        ))
        
        # Score badge styles
        self.styles.add(ParagraphStyle(
            name='ScoreBadgePass',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor('#e74c3c'),  # Red
            alignment=TA_CENTER,
            spaceAfter=6,
            borderPadding=(6, 6, 6, 6),
            borderRadius=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='ScoreBadgeConsider',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            backColor=colors.HexColor('#f1c40f'),  # Yellow
            alignment=TA_CENTER,
            spaceAfter=6,
            borderPadding=(6, 6, 6, 6),
            borderRadius=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='ScoreBadgeRecommend',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor('#27ae60'),  # Green
            alignment=TA_CENTER,
            spaceAfter=6,
            borderPadding=(6, 6, 6, 6),
            borderRadius=4
        ))
        
        # Evidence quote style
        self.styles.add(ParagraphStyle(
            name='EvidenceQuote',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495e'),
            leftIndent=20,
            rightIndent=20,
            spaceBefore=6,
            spaceAfter=6,
            borderPadding=(10, 10, 10, 10),
            backColor=colors.HexColor('#f8f9fa'),
            borderColor=colors.HexColor('#dee2e6'),
            borderWidth=1
        ))
        
        # Normal text with justification
        self.styles.add(ParagraphStyle(
            name='JustifiedText',
            parent=self.styles['Normal'],
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=14
        ))
        
        # List item style
        self.styles.add(ParagraphStyle(
            name='ListItem',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceBefore=3,
            spaceAfter=3
        ))
        
        # Subscore style
        self.styles.add(ParagraphStyle(
            name='SubscoreLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubscoreValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
    
    def export_coverage_report(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """Export a coverage report to PDF.
        
        Args:
            report_data: The coverage report data
            output_path: Optional path to save PDF (if None, returns bytes)
            
        Returns:
            PDF content as bytes if output_path is None
            
        Raises:
            PDFExportError: If export fails
        """
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            story = self._build_story(report_data)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Save to file if path provided
            if output_path:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
                return None
            
            return pdf_content
            
        except Exception as e:
            raise PDFExportError(f"PDF export failed: {str(e)}")
    
    def _build_story(self, report_data: Dict[str, Any]) -> List:
        """Build the PDF story (content flow).
        
        Args:
            report_data: The coverage report data
            
        Returns:
            List of flowable elements
        """
        story = []
        
        # Title
        script_title = report_data.get('script_title', 'Untitled Script')
        story.append(Paragraph(
            f'CoverageIQ Report',
            self.styles['CoverageTitle']
        ))
        story.append(Paragraph(
            f'{script_title}',
            self.styles['Heading2']
        ))
        
        # Timestamp
        timestamp = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(
            f'Generated on {timestamp}',
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Scores Section
        story.append(Paragraph('SCORES & RECOMMENDATION', self.styles['SectionHeader']))
        
        total_score = report_data.get('total_score', 0)
        recommendation = report_data.get('recommendation', 'N/A')
        
        # Score and recommendation table
        score_data = [
            [Paragraph(f'Total Score: <b>{total_score}/50</b>', self.styles['Normal'])],
            [self._get_recommendation_badge(recommendation)]
        ]
        
        score_table = Table(score_data, colWidths=[4*inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 12))
        
        # Subscores
        subscores = report_data.get('subscores', {})
        if subscores:
            story.append(Paragraph('<b>Subscores:</b>', self.styles['Normal']))
            subscore_data = []
            for category, score_data in subscores.items():
                if isinstance(score_data, dict):
                    score = score_data.get('score', 0)
                    rationale = score_data.get('rationale', '')
                else:
                    score = score_data
                    rationale = ''
                
                subscore_data.append([
                    Paragraph(f'{category.capitalize()}', self.styles['SubscoreLabel']),
                    Paragraph(f'{score}/10', self.styles['SubscoreValue'])
                ])
                if rationale:
                    subscore_data.append([
                        Paragraph(f'  {rationale}', self.styles['Normal']),
                        ''
                    ])
            
            subscore_table = Table(subscore_data, colWidths=[5*inch, 1*inch])
            subscore_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(subscore_table)
            story.append(Spacer(1, 12))
        
        # Logline
        logline = report_data.get('logline', '')
        if logline:
            story.append(Paragraph('LOGLINE', self.styles['SectionHeader']))
            story.append(Paragraph(logline, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Synopsis
        synopsis = report_data.get('synopsis', '')
        if synopsis:
            story.append(Paragraph('SYNOPSIS', self.styles['SectionHeader']))
            story.append(Paragraph(synopsis, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Overall Comments
        overall = report_data.get('overall_comments', '')
        if overall:
            story.append(Paragraph('OVERALL COMMENTS', self.styles['SectionHeader']))
            story.append(Paragraph(overall, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Strengths
        strengths = report_data.get('strengths', [])
        if strengths:
            story.append(Paragraph('STRENGTHS', self.styles['SectionHeader']))
            for strength in strengths:
                story.append(Paragraph(f'• {strength}', self.styles['ListItem']))
            story.append(Spacer(1, 12))
        
        # Weaknesses
        weaknesses = report_data.get('weaknesses', [])
        if weaknesses:
            story.append(Paragraph('WEAKNESSES', self.styles['SectionHeader']))
            for weakness in weaknesses:
                story.append(Paragraph(f'• {weakness}', self.styles['ListItem']))
            story.append(Spacer(1, 12))
        
        # Character Notes
        character_notes = report_data.get('character_notes', '')
        if character_notes:
            story.append(Paragraph('CHARACTER NOTES', self.styles['SectionHeader']))
            # Handle JSON or plain text
            if isinstance(character_notes, str) and character_notes.startswith('{'):
                try:
                    import json
                    char_data = json.loads(character_notes)
                    self._format_character_analysis(story, char_data)
                except:
                    story.append(Paragraph(character_notes, self.styles['JustifiedText']))
            else:
                story.append(Paragraph(character_notes, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Structure Analysis
        structure = report_data.get('structure_analysis', '')
        if structure:
            story.append(Paragraph('STRUCTURE ANALYSIS', self.styles['SectionHeader']))
            # Handle JSON or plain text
            if isinstance(structure, str) and structure.startswith('{'):
                try:
                    import json
                    struct_data = json.loads(structure)
                    self._format_structure_analysis(story, struct_data)
                except:
                    story.append(Paragraph(structure, self.styles['JustifiedText']))
            else:
                story.append(Paragraph(structure, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Market Positioning
        market = report_data.get('market_positioning', '')
        if market:
            story.append(Paragraph('MARKET POSITIONING', self.styles['SectionHeader']))
            # Handle JSON or plain text
            if isinstance(market, str) and market.startswith('{'):
                try:
                    import json
                    market_data = json.loads(market)
                    self._format_market_positioning(story, market_data)
                except:
                    story.append(Paragraph(market, self.styles['JustifiedText']))
            else:
                story.append(Paragraph(market, self.styles['JustifiedText']))
            story.append(Spacer(1, 12))
        
        # Evidence Quotes
        quotes = report_data.get('evidence_quotes', [])
        if quotes:
            story.append(Paragraph('EVIDENCE QUOTES', self.styles['SectionHeader']))
            for i, quote in enumerate(quotes, 1):
                quote_text = quote.get('quote', '')
                page = quote.get('page', 0)
                context = quote.get('context', '')
                
                # Quote header
                story.append(Paragraph(
                    f'<b>{i}. Page {page}</b>',
                    self.styles['Normal']
                ))
                
                # Quote text
                story.append(Paragraph(
                    f'"{quote_text}"',
                    self.styles['EvidenceQuote']
                ))
                
                # Context if available
                if context:
                    story.append(Paragraph(
                        f'<i>Context: {context}</i>',
                        self.styles['Normal']
                    ))
                
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 12))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            '— Generated by CoverageIQ —',
            self.styles['Footer']
        ))
        story.append(Paragraph(
            'AI-powered script coverage analysis',
            self.styles['Footer']
        ))
        
        return story
    
    def _get_recommendation_badge(self, recommendation: str) -> Paragraph:
        """Get the appropriate recommendation badge.
        
        Args:
            recommendation: Recommendation string
            
        Returns:
            Styled Paragraph for the badge
        """
        rec = recommendation.upper()
        if 'RECOMMEND' in rec and 'PASS' not in rec:
            return Paragraph(
                f'<b>{recommendation.upper()}</b>',
                self.styles['ScoreBadgeRecommend']
            )
        elif 'CONSIDER' in rec:
            return Paragraph(
                f'<b>{recommendation.upper()}</b>',
                self.styles['ScoreBadgeConsider']
            )
        else:
            return Paragraph(
                f'<b>{recommendation.upper()}</b>',
                self.styles['ScoreBadgePass']
            )
    
    def _format_character_analysis(self, story: List, data: Dict):
        """Format character analysis JSON data.
        
        Args:
            story: PDF story list
            data: Character analysis data
        """
        if 'protagonist' in data:
            prot = data['protagonist']
            story.append(Paragraph(
                f"<b>Protagonist:</b> {prot.get('name', 'Unknown')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                prot.get('assessment', ''),
                self.styles['JustifiedText']
            ))
            if 'series_runway' in prot:
                story.append(Paragraph(
                    f"<i>Series Runway:</i> {prot['series_runway']}",
                    self.styles['Normal']
                ))
            story.append(Spacer(1, 6))
        
        if 'supporting_cast' in data:
            story.append(Paragraph(
                '<b>Supporting Cast:</b>',
                self.styles['Normal']
            ))
            cast = data['supporting_cast']
            story.append(Paragraph(
                cast.get('assessment', ''),
                self.styles['JustifiedText']
            ))
            story.append(Spacer(1, 6))
        
        if 'character_dynamics' in data:
            story.append(Paragraph(
                '<b>Character Dynamics:</b>',
                self.styles['Normal']
            ))
            story.append(Paragraph(
                data['character_dynamics'],
                self.styles['JustifiedText']
            ))
    
    def _format_structure_analysis(self, story: List, data: Dict):
        """Format structure analysis JSON data.
        
        Args:
            story: PDF story list
            data: Structure analysis data
        """
        for key, value in data.items():
            if isinstance(value, str):
                story.append(Paragraph(
                    f'<b>{key.replace("_", " ").title()}:</b>',
                    self.styles['Normal']
                ))
                story.append(Paragraph(value, self.styles['JustifiedText']))
                story.append(Spacer(1, 4))
    
    def _format_market_positioning(self, story: List, data: Dict):
        """Format market positioning JSON data.
        
        Args:
            story: PDF story list
            data: Market positioning data
        """
        for key, value in data.items():
            if isinstance(value, str):
                story.append(Paragraph(
                    f'<b>{key.replace("_", " ").title()}:</b>',
                    self.styles['Normal']
                ))
                story.append(Paragraph(value, self.styles['JustifiedText']))
            elif isinstance(value, list):
                story.append(Paragraph(
                    f'<b>{key.replace("_", " ").title()}:</b>',
                    self.styles['Normal']
                ))
                for item in value:
                    story.append(Paragraph(f'• {item}', self.styles['ListItem']))
            story.append(Spacer(1, 4))


# Singleton instance
_exporter: Optional[PDFExporter] = None


def get_pdf_exporter() -> PDFExporter:
    """Get or create the PDF exporter singleton.
    
    Returns:
        PDFExporter instance
    """
    global _exporter
    if _exporter is None:
        _exporter = PDFExporter()
    return _exporter
