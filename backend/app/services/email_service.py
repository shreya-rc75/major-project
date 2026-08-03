import os
import smtplib
import logging
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Minimal SMTP email service wrapper.

    Reads SMTP configuration from environment variables:
      - SMTP_HOST
      - SMTP_PORT
      - SMTP_USERNAME
      - SMTP_PASSWORD
      - SMTP_USE_TLS (true/false)
      - EMAIL_FROM

    This is intentionally simple; for production you may swap for a more
    robust provider SDK (SendGrid, SES, etc.).
    """

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "localhost")
        self.port = int(os.getenv("SMTP_PORT", "25"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "false").lower() in ["1", "true", "yes"]
        self.email_from = os.getenv("EMAIL_FROM", "noreply@cervicare.local")

    def send_email(self, to_address: str, subject: str, html_body: str, plain_body: Optional[str] = None) -> None:
        msg = EmailMessage()
        msg["From"] = self.email_from
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(plain_body or "This message requires an HTML-capable client.")
        msg.add_alternative(html_body, subtype="html")

        logger.info("Sending email to %s via %s:%s", to_address, self.host, self.port)
        try:
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
            logger.info("Email successfully sent to %s", to_address)
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_address, exc)
            raise
