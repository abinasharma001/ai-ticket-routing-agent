import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

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
        message["Subject"] = f"Ticket Escalation: {category} Issue"
        message["From"] = sender_email
        message["To"] = receiver_email

        text = f"""\
Ticket Escalation Request

Category: {category}
Department: {department}

Issue Description:
{issue}
"""
        html = f"""\
<html>
  <body>
    <h2>Ticket Escalation Request</h2>
    <p><b>Category:</b> {category}</p>
    <p><b>Department:</b> {department}</p>
    <br>
    <p><b>Issue Description:</b></p>
    <p>{issue}</p>
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
