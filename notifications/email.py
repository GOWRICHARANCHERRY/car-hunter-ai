import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from backend.config import settings


async def send_email(subject: str, body_html: str) -> bool:
    if not settings.smtp_user or not settings.smtp_password:
        return False
    msg = MIMEMultipart()
    msg["From"] = settings.smtp_user
    msg["To"] = settings.notification_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def format_deal_email(car: Dict) -> str:
    pros = "".join(f"<li>✅ {p}</li>" for p in (car.get("pros") or [])[:3])
    cons = "".join(f"<li>⚠️ {c}</li>" for c in (car.get("cons") or [])[:2])
    return f"""
    <h2 style="color:#2563eb;">🔥 Great Deal Found!</h2>
    <h3>{car['title']}</h3>
    <p><strong>Year:</strong> {car['year']} | <strong>KMs:</strong> {car.get('kms', 'N/A'):,}</p>
    <p><strong>Price:</strong> ₹{car['price']:,}</p>
    <p><strong>Score:</strong> {car['score']}/100</p>
    {'<p><strong>Fair Price:</strong> ₹' + str(car['fair_price']) + '</p>' if car.get('fair_price') else ''}
    <h4>Pros:</h4><ul>{pros}</ul>
    <h4>Cons:</h4><ul>{cons}</ul>
    {'<a href="' + car['listing_url'] + '">View Listing</a>' if car.get('listing_url') else ''}
    """
