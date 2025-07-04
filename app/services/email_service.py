import os
import smtplib
from email.message import EmailMessage
import logging

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM]):
    raise RuntimeError("SMTP credentials are not set in environment variables.")

assert SMTP_HOST is not None
assert SMTP_USER is not None
assert SMTP_PASSWORD is not None
assert EMAIL_FROM is not None

SMTP_HOST = str(SMTP_HOST)
SMTP_USER = str(SMTP_USER)
SMTP_PASSWORD = str(SMTP_PASSWORD)
EMAIL_FROM = str(EMAIL_FROM)

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your Memee OTP Verification Code"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg.set_content(f"Your OTP code is: {otp}\n\nPlease enter this code to verify your email address.")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

def send_welcome_email(to_email: str, username: str):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = os.getenv("SMTP_PORT", "587")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    if SMTP_HOST is None or SMTP_PORT is None or SMTP_USER is None or SMTP_PASSWORD is None or EMAIL_FROM is None:
        raise RuntimeError("SMTP credentials are not set or are None.")
    host = str(SMTP_HOST)
    port = int(SMTP_PORT)
    user = str(SMTP_USER)
    password = str(SMTP_PASSWORD)
    email_from = str(EMAIL_FROM)
    msg = EmailMessage()
    msg["Subject"] = f"Welcome to Memee, {username}! 🎉"
    msg["From"] = email_from
    msg["To"] = to_email
    # Plain text version
    plain_text = f"""
Hi {username},

Welcome to Memee! We're excited to have you join our meme-loving community.

You can now start exploring, sharing, and laughing with your friends.

If you have any questions, just reply to this email or contact us at support@yourdomain.com.

Best wishes,
The Memee Team
"""
    msg.set_content(plain_text)
    # HTML version
    html_content = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f7f7fa; padding: 0; margin: 0;">
        <div style="max-width: 480px; margin: 40px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden;">
          <div style="background: linear-gradient(90deg, #ff8a00 0%, #e52e71 100%); padding: 32px 0; text-align: center;">
            <h1 style="color: #fff; margin: 0; font-size: 2.2em; letter-spacing: 1px;">Welcome to <span style='color:#ffe066;'>Memee</span>!</h1>
            <p style="color: #fff; font-size: 1.1em; margin-top: 12px;">Your daily dose of memes, fun, and friends 🎉</p>
          </div>
          <div style="padding: 32px 24px 24px 24px; text-align: center;">
            <h2 style="color: #222; margin-bottom: 8px;">Hi {username} 👋</h2>
            <p style="color: #444; font-size: 1.1em;">We're thrilled to have you join the <b>Memee</b> family.<br>Start exploring, sharing, and laughing with your friends!</p>
            <a href="https://memee.com" style="display: inline-block; margin-top: 24px; padding: 12px 32px; background: linear-gradient(90deg, #ff8a00 0%, #e52e71 100%); color: #fff; border-radius: 24px; text-decoration: none; font-weight: bold; font-size: 1.1em; box-shadow: 0 2px 8px rgba(229,46,113,0.10);">Start Browsing Memes 🚀</a>
            <p style="margin-top: 24px; color: #888; font-size: 0.95em;">If you have any questions, just reply to this email or contact us at <a href='mailto:support@yourdomain.com'>support@yourdomain.com</a>.</p>
          </div>
          <div style="background: #f7f7fa; color: #aaa; font-size: 0.95em; padding: 16px 0; text-align: center; border-top: 1px solid #eee;">
            <p style="margin: 0;">Made with ❤️ by the Memee Team</p>
          </div>
        </div>
      </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")
    try:
        logging.info(f"Connecting to SMTP server {host}:{port} as {user}")
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        logging.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send welcome email to {to_email}: {e}") 