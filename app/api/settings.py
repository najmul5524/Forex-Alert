from fastapi import APIRouter, Body
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("")
async def get_settings():
    return {
        "smtp_host": settings.SMTP_HOST or "",
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or "",
        "has_smtp_password": bool(settings.SMTP_PASSWORD),
        "smtp_use_tls": settings.SMTP_USE_TLS,
        "discord_webhook_url": settings.DISCORD_WEBHOOK_URL or "",
        "telegram_bot_token": settings.TELEGRAM_BOT_TOKEN or "",
        "telegram_chat_id": settings.TELEGRAM_CHAT_ID or "",
        "twelve_data_api_key": settings.TWELVE_DATA_API_KEY or "",
        "finnhub_api_key": settings.FINNHUB_API_KEY or "",
        "vapid_public_key": settings.VAPID_PUBLIC_KEY or ""
    }

@router.post("")
async def update_settings(payload: dict = Body(...)):
    if "smtp_host" in payload:
        settings.SMTP_HOST = payload["smtp_host"]
    if "smtp_port" in payload:
        settings.SMTP_PORT = int(payload["smtp_port"])
    if "smtp_user" in payload:
        settings.SMTP_USER = payload["smtp_user"]
    if "smtp_password" in payload and payload["smtp_password"]:
        settings.SMTP_PASSWORD = payload["smtp_password"]
    if "smtp_from_email" in payload:
        settings.SMTP_FROM_EMAIL = payload["smtp_from_email"]
    if "smtp_use_tls" in payload:
        settings.SMTP_USE_TLS = bool(payload["smtp_use_tls"])
    if "discord_webhook_url" in payload:
        settings.DISCORD_WEBHOOK_URL = payload["discord_webhook_url"]
    if "telegram_bot_token" in payload:
        settings.TELEGRAM_BOT_TOKEN = payload["telegram_bot_token"]
    if "telegram_chat_id" in payload:
        settings.TELEGRAM_CHAT_ID = payload["telegram_chat_id"]
    if "twelve_data_api_key" in payload:
        settings.TWELVE_DATA_API_KEY = payload["twelve_data_api_key"]
    if "finnhub_api_key" in payload:
        settings.FINNHUB_API_KEY = payload["finnhub_api_key"]

    return {"status": "success", "message": "Settings updated successfully"}
