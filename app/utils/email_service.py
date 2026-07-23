import smtplib
import os
from datetime import datetime
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger


def _priority_for_category(category: str) -> str:
  category_lower = category.strip().lower()
  if category_lower in {"security", "infrastructure", "database"}:
    return "High"
  if category_lower in {"network", "access management"}:
    return "Medium"
  return "Normal"

def send_escalation_email(issue: str, category: str, department: str) -> bool:
    """
    Send an escalation email via Gmail SMTP.
    Requires SMTP_EMAIL and SMTP_PASSWORD environment variables.
    """
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    
    # We will send the email to the sender's own email for demonstration
    receiver_email = sender_email
    
    if not sender_email or not sender_password:
        logger.warning("SMTP_EMAIL or SMTP_PASSWORD not set. Skipping actual email send.")
        raise ValueError("SMTP credentials not configured. Cannot send email.")
        
    try:
        message = MIMEMultipart("alternative")
        priority = _priority_for_category(category)
        timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        issue_html = escape(issue).replace("\n", "<br>")
        message["Subject"] = f"Ticket Escalation: {category} Issue"
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Reply-To"] = sender_email

        text = f"""\
Ticket Escalation Request

Timestamp: {timestamp}
Priority: {priority}
Category: {category}
Department: {department}

Issue Description:
{issue}
"""
        html = f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #1f2937; background: #f8fafc; padding: 24px;">
    <div style="max-width: 640px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 24px;">
      <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: #6b7280;">AI Ticket Routing Agent</div>
      <h2 style="margin: 8px 0 16px; font-size: 24px; color: #111827;">Ticket Escalation Request</h2>
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr><td style="padding: 8px 0; font-weight: 700; width: 150px;">Timestamp</td><td>{timestamp}</td></tr>
        <tr><td style="padding: 8px 0; font-weight: 700;">Priority</td><td>{priority}</td></tr>
        <tr><td style="padding: 8px 0; font-weight: 700;">Category</td><td>{escape(category)}</td></tr>
        <tr><td style="padding: 8px 0; font-weight: 700;">Department</td><td>{escape(department)}</td></tr>
        <tr><td style="padding: 8px 0; font-weight: 700;">Ticket ID</td><td>Pending escalation reference</td></tr>
      </table>
      <div style="margin-top: 18px; font-weight: 700; color: #111827;">Issue Description</div>
      <div style="margin-top: 8px; padding: 14px; background: #f9fafb; border-left: 4px solid #2563eb; border-radius: 10px; line-height: 1.6;">{issue_html}</div>
    </div>
  </body>
</html>
"""
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            
        logger.info("Escalation email sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send escalation email: {e}")
        return False
