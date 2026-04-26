"""
PDF Report Generation Utilities
===============================
Generate financial reports as PDF documents.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from typing import Dict, List, Any
from datetime import date
import io


def generate_runway_report_pdf(metrics: Dict[str, Any], forecasts: List[Dict[str, Any]]) -> bytes:
    """
    Generate a PDF report for cash runway analysis.
    
    Args:
        metrics: Current financial metrics
        forecasts: Cash flow forecasts
        
    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Cash Runway Analysis Report", title_style))
    story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Current Metrics
    story.append(Paragraph("Current Financial Position", subtitle_style))
    
    current_data = [
        ["Metric", "Value"],
        ["Ending Cash", f"${metrics.get('ending_cash', 0):,.2f}"],
        ["Monthly Burn Rate", f"${metrics.get('burn_rate', 0):,.2f}"],
        ["Runway (Months)", f"{metrics.get('runway_months', 0):.1f}"],
        ["Total Revenue", f"${metrics.get('total_revenue', 0):,.2f}"],
        ["Total Expenses", f"${metrics.get('total_expenses', 0):,.2f}"],
    ]
    
    current_table = Table(current_data, colWidths=[2*inch, 2*inch])
    current_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(current_table)
    story.append(Spacer(1, 20))
    
    # Forecast Table
    if forecasts:
        story.append(Paragraph("Cash Flow Forecast", subtitle_style))
        
        forecast_data = [["Month", "Predicted Revenue", "Predicted Cash", "Confidence Range"]]
        for f in forecasts[:12]:  # Limit to 12 months
            forecast_data.append([
                f.get('forecast_date', '').strftime('%Y-%m') if f.get('forecast_date') else '',
                f"${f.get('mrr_predicted', 0):,.0f}",
                f"${f.get('cash_predicted', 0):,.0f}",
                f"${f.get('confidence_lower', 0):,.0f} - ${f.get('confidence_upper', 0):,.0f}"
            ])
        
        forecast_table = Table(forecast_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
        forecast_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(forecast_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_budget_variance_report_pdf(budget_data: Dict[str, Any]) -> bytes:
    """
    Generate a PDF report for budget vs actual analysis.
    
    Args:
        budget_data: Budget variance data
        
    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Budget vs Actual Analysis Report", title_style))
    story.append(Paragraph(f"Budget: {budget_data.get('budget_name', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Month: {budget_data.get('month', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Variance Table
    variances = budget_data.get('variances', [])
    if variances:
        variance_data = [["Category", "Budget", "Actual", "Variance", "Variance %"]]
        for v in variances:
            variance_data.append([
                v.get('category', ''),
                f"${v.get('budget', 0):,.2f}",
                f"${v.get('actual', 0):,.2f}",
                f"${v.get('variance', 0):,.2f}",
                f"{v.get('variance_pct', 0):.1f}%"
            ])
        
        variance_table = Table(variance_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        variance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(variance_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()