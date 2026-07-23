from __future__ import annotations

import io
from datetime import datetime
from html import escape
from typing import Any, Dict
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
except ImportError:
    letter = colors = SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = None  # type: ignore[assignment]
    getSampleStyleSheet = ParagraphStyle = None  # type: ignore[assignment]
    inch = None  # type: ignore[assignment]


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(document.leftMargin, 0.45 * inch, "AI Ticket Routing & Resolution Agent")
    canvas.drawRightString(document.pagesize[0] - document.rightMargin, 0.45 * inch, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _format_similarity(score: Any) -> str:
    try:
        similarity = float(score)
    except (TypeError, ValueError):
        similarity = 0.0
    if similarity <= 1.0:
        similarity *= 100
    return f"{similarity:.0f}%"

def generate_solution_pdf(ticket_data: Dict[str, Any]) -> io.BytesIO:
    """Generate a PDF containing the ticket solution and details."""
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=42)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CustomTitle", parent=styles["Heading1"], fontSize=20, spaceAfter=14, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="CustomHeading", parent=styles["Heading2"], fontSize=13, spaceAfter=8, textColor=colors.HexColor("#1F2937")))
        styles.add(ParagraphStyle(name="CustomNormal", parent=styles["Normal"], fontSize=10.5, leading=14, spaceAfter=8))
        styles.add(ParagraphStyle(name="Muted", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#6B7280")))
        styles.add(ParagraphStyle(name="SolutionBox", parent=styles["Normal"], fontSize=11, leading=15, spaceAfter=12,
                                  backColor=colors.HexColor("#EFF6FF"), textColor=colors.HexColor("#0F172A"),
                                  borderColor=colors.HexColor("#3B82F6"), borderWidth=1, borderPadding=10))
        
        story = []
        timestamp = ticket_data.get("timestamp") or datetime.utcnow().isoformat(timespec="seconds") + "Z"
        confidence = float(ticket_data.get("confidence", 0.0) or 0.0)
        
        story.append(Paragraph("AI Ticket Resolution Report", styles["CustomTitle"]))
        story.append(Paragraph("Generated from the current routing, retrieval, and resolution pipeline.", styles["Muted"]))
        story.append(Spacer(1, 10))

        header_table = Table(
            [
                [Paragraph("Company Logo", styles["CustomNormal"]), Paragraph("Ticket ID", styles["CustomNormal"]), Paragraph("Timestamp", styles["CustomNormal"])],
                [Paragraph("Logo placeholder", styles["Muted"]), Paragraph(str(ticket_data.get("ticket_id", "N/A")), styles["CustomNormal"]), Paragraph(timestamp, styles["CustomNormal"])],
            ],
            colWidths=[1.8 * inch, 2.0 * inch, 2.4 * inch],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BFDBFE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 14))
        
        story.append(Paragraph("Ticket Details", styles["CustomHeading"]))
        details_table = Table(
            [
                ["Category", escape(str(ticket_data.get("category", "N/A")))],
                ["Department", escape(str(ticket_data.get("department", "N/A")))],
                ["Confidence", f"{confidence:.0%}"],
                ["Issue", escape(str(ticket_data.get("input", "N/A"))).replace("\n", "<br/>")],
            ],
            colWidths=[1.25 * inch, 4.95 * inch],
        )
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#111827")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(details_table)
        story.append(Spacer(1, 14))
        
        story.append(Paragraph("Suggested Solution", styles["CustomHeading"]))
        story.append(Paragraph(escape(str(ticket_data.get("solution", "No solution found."))).replace("\n", "<br/>"), styles["SolutionBox"]))
        story.append(Spacer(1, 10))
        
        similar_tickets = ticket_data.get("similar_tickets", [])
        if similar_tickets:
            story.append(Paragraph("Similar Issues Found", styles["CustomHeading"]))
            rows = [["Ticket ID", "Category", "Department", "Problem", "Suggested Solution", "Similarity"]]
            for ticket in similar_tickets:
                rows.append(
                    [
                        str(ticket.get("id", "N/A")),
                        escape(str(ticket.get("category", "N/A"))),
                        escape(str(ticket.get("department", "N/A"))),
                        escape(str(ticket.get("title", ticket.get("ticket_text", "N/A"))))[:160],
                        escape(str(ticket.get("resolution", "N/A")))[:180],
                        _format_similarity(ticket.get("score", 0.0)),
                    ]
                )

            similar_table = Table(rows, colWidths=[0.8 * inch, 1.0 * inch, 1.0 * inch, 2.0 * inch, 1.6 * inch, 0.9 * inch], repeatRows=1)
            similar_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(similar_table)

        story.append(Spacer(1, 14))
        story.append(Paragraph("Footer", styles["CustomHeading"]))
        story.append(Paragraph("This report was generated automatically from the AI Ticket Routing & Resolution Agent.", styles["Muted"]))

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    except Exception as e:
        buffer.write(f"Error generating PDF: {e}".encode("utf-8"))
        
    buffer.seek(0)
    return buffer
