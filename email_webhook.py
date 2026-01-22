import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

# Load from environment variables
EMAIL = os.getenv("EMAIL_SENDER")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECIPIENTS = [r.strip() for r in os.getenv("EMAIL_RECIPIENTS", "").split(",") if r.strip()]

# Validate configuration
if not EMAIL or not APP_PASSWORD:
    raise ValueError("Email configuration missing. Please set EMAIL_SENDER and EMAIL_APP_PASSWORD in .env file")

if not RECIPIENTS:
    raise ValueError("No email recipients configured. Please set EMAIL_RECIPIENTS in .env file")


def send_email_alert(message, subject="🚨 API DOWN ALERT"):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg, to_addrs=RECIPIENTS)
