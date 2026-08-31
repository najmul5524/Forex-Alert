import logging
from email.message import EmailMessage
import aiosmtplib
from app.config import settings

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
  .container { max-width: 580px; margin: 0 auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }
  .header { background: linear-gradient(135deg, #2563eb, #3b82f6); padding: 24px; text-align: center; }
  .header h1 { margin: 0; font-size: 22px; color: #ffffff; letter-spacing: 0.5px; }
  .content { padding: 24px; }
  .badge { display: inline-block; padding: 4px 12px; border-radius: 9999px; background: rgba(59, 130, 246, 0.2); color: #60a5fa; font-weight: bold; font-size: 13px; margin-bottom: 16px; border: 1px solid rgba(59, 130, 246, 0.4); }
  .metric-card { background: #0f172a; border-radius: 8px; padding: 18px; margin: 16px 0; border: 1px solid #334155; }
  .metric-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }
  .metric-row:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  .label { color: #94a3b8; }
  .value { font-weight: 600; color: #f1f5f9; }
  .highlight-price { font-size: 24px; font-weight: 700; color: #38bdf8; text-align: center; margin: 12px 0; }
  .footer { background: #0f172a; padding: 16px 24px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; }
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚡ Live Market Alert Triggered</h1>
    </div>
    <div class="content">
      <div style="text-align: center;">
        <span class="badge">{{ symbol }} • {{ timeframe }}</span>
      </div>
      <div class="highlight-price">{{ trigger_price }}</div>
      <div class="metric-card">
        <div class="metric-row"><span class="label">Condition:</span> <span class="value">{{ summary }}</span></div>
        <div class="metric-row"><span class="label">Instrument:</span> <span class="value">{{ symbol }}</span></div>
        <div class="metric-row"><span class="label">Timeframe:</span> <span class="value">{{ timeframe }}</span></div>
        <div class="metric-row"><span class="label">Triggered At:</span> <span class="value">{{ timestamp }} UTC</span></div>
      </div>
    </div>
    <div class="footer">
      Sent by Live Forex & Market Alert Engine
    </div>
  </div>
</body>
</html>
"""

async def send_email_alert(to_email: str, subject: str, data: dict) -> bool:
    if not to_email:
        return False

    smtp_host = settings.SMTP_HOST
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASSWORD
    from_email = settings.SMTP_FROM_EMAIL or smtp_user

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.warning("SMTP configuration is incomplete. Skipping email alert.")
        return False

    try:
        html_content = HTML_TEMPLATE
        for k, v in data.items():
            html_content = html_content.replace(f"{{{{ {k} }}}}", str(v))

        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(f"Alert: {data.get('summary', '')} at {data.get('trigger_price', '')}")
        message.add_alternative(html_content, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=settings.SMTP_PORT,
            start_tls=settings.SMTP_USE_TLS,
            username=smtp_user,
            password=smtp_pass,
            timeout=10
        )
        logger.info(f"Email alert sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert to {to_email}: {e}")
        return False
