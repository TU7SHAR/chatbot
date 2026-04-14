import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def send_invite_email(target_email, user_name, plain_password):
    subject = "You've been invited to chat.bot"
    body = f"Hi {user_name},\n\nYou have been invited to join the team dashboard.\n\nLogin Email: {target_email}\nTemporary Password: {plain_password}\n\nPlease log in and change your password immediately."
    
    try:
        return True
    except Exception:
        return False

def generate_otp():
    """Generates a random 6-digit OTP string."""
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp_code):
    """Sends the OTP email via SMTP."""

    html_content = f"""
    <div style="font-family: sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; background: #fff; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #111827;">Your Verification Code</h2>
        <p style="color: #4b5563; font-size: 16px;">Please use the following 6-digit code to verify your chat.bot account:</p>
        <div style="background: #f9fafb; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <strong style="font-size: 32px; letter-spacing: 4px; color: #E8722A;">{otp_code}</strong>
        </div>
        <p style="color: #9ca3af; font-size: 13px;">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "chat.bot - Your Verification Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

        return True

    except Exception as e:
        print(f"SMTP Email Error: {e}")
        return False