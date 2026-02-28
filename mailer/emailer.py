import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config.settings import GMAIL_SENDER, GMAIL_APP_PASSWORD


def send_report_email(recipients: list[str], report_markdown: str, gdrive_link: str = "") -> dict:
    """
    Send the competitive intelligence report via Gmail SMTP.
    
    Args:
        recipients: List of email addresses
        report_markdown: The full report in markdown
        gdrive_link: Optional Google Drive link to include
    
    Returns:
        {"success": True} or {"success": False, "error": "..."}
    """
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        return {"success": False, "error": "Gmail credentials not configured in .env"}

    subject = f"Competitive Intelligence Report — {datetime.now().strftime('%B %d, %Y')}"

    # Build HTML body from markdown (simple conversion)
    html_body = _markdown_to_html(report_markdown, gdrive_link)
    text_body = report_markdown  # plaintext fallback

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)

            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = GMAIL_SENDER
                msg["To"] = recipient

                msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))

                server.sendmail(GMAIL_SENDER, recipient, msg.as_string())

        return {"success": True}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Gmail authentication failed. Make sure you're using an App Password, not your regular password."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _markdown_to_html(markdown: str, gdrive_link: str = "") -> str:
    """Convert basic markdown to HTML for email."""
    lines = markdown.split("\n")
    html_lines = []

    for line in lines:
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2 style='color:#1a73e8;border-bottom:1px solid #eee'>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<strong>{line[2:-2]}</strong>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line == "---":
            html_lines.append("<hr>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            # Handle inline bold **text**
            formatted = line.replace("**", "<strong>", 1)
            while "**" in formatted:
                formatted = formatted.replace("**", "</strong>", 1)
            html_lines.append(f"<p>{formatted}</p>")

    drive_section = ""
    if gdrive_link:
        drive_section = f"""
        <div style='background:#f8f9fa;padding:12px;border-radius:6px;margin:16px 0'>
            📁 <a href='{gdrive_link}' style='color:#1a73e8'>View Full Report in Google Drive</a>
        </div>
        """

    return f"""
    <html>
    <body style='font-family:Arial,sans-serif;max-width:800px;margin:auto;padding:24px;color:#333'>
        {drive_section}
        {''.join(html_lines)}
        <hr>
        <p style='color:#999;font-size:12px'>
            Sent by Competitive Intelligence Agent · {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </body>
    </html>
    """
