import io
from typing import Dict, Any, List
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    pass

def generate_solution_pdf(ticket_data: Dict[str, Any]) -> io.BytesIO:
    """Generate a PDF containing the ticket solution and details."""
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=14))
        styles.add(ParagraphStyle(name='CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor("#2C3E50")))
        styles.add(ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=11, spaceAfter=12))
        styles.add(ParagraphStyle(name='SolutionBox', parent=styles['Normal'], fontSize=12, spaceAfter=12,
                                  backColor=colors.HexColor("#E8F6F3"), textColor=colors.HexColor("#0E6251"),
                                  borderColor=colors.HexColor("#1ABC9C"), borderWidth=1, borderPadding=10))
        
        Story = []
        
        # Title
        Story.append(Paragraph("AI Ticket Resolution Report", styles["CustomTitle"]))
        Story.append(Spacer(1, 12))
        
        # Details
        Story.append(Paragraph("Ticket Details", styles["CustomHeading"]))
        Story.append(Paragraph(f"<b>Issue:</b> {ticket_data.get('input', 'N/A')}", styles["CustomNormal"]))
        Story.append(Paragraph(f"<b>Category:</b> {ticket_data.get('category', 'N/A')}", styles["CustomNormal"]))
        Story.append(Paragraph(f"<b>Department:</b> {ticket_data.get('department', 'N/A')}", styles["CustomNormal"]))
        Story.append(Paragraph(f"<b>Confidence Score:</b> {ticket_data.get('confidence', 0.0):.2f}", styles["CustomNormal"]))
        Story.append(Spacer(1, 12))
        
        # Solution
        Story.append(Paragraph("Suggested Solution", styles["CustomHeading"]))
        Story.append(Paragraph(ticket_data.get("solution", "No solution found."), styles["SolutionBox"]))
        Story.append(Spacer(1, 12))
        
        # Similar Tickets
        similar_tickets = ticket_data.get("similar_tickets", [])
        if similar_tickets:
            Story.append(Paragraph("Similar Issues Found", styles["CustomHeading"]))
            for t in similar_tickets:
                title = str(t.get('title', 'Unknown')).replace('<', '&lt;').replace('>', '&gt;')
                resolution = str(t.get('resolution', 'N/A')).replace('<', '&lt;').replace('>', '&gt;')
                score = t.get('score', 0.0)
                
                text = f"<b>[{score:.2f}] {title}</b><br/>{resolution}"
                Story.append(Paragraph(text, styles["CustomNormal"]))
        
        doc.build(Story)
    except Exception as e:
        buffer.write(f"Error generating PDF: {e}".encode("utf-8"))
        
    buffer.seek(0)
    return buffer
