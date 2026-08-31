import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

BASE_DIR = Path(__file__).resolve().parent.parent

def generate_vapid_keys_if_missing():
    private_key_path = BASE_DIR / "vapid_private.pem"
    public_key_path = BASE_DIR / "vapid_public.txt"

    if private_key_path.exists() and public_key_path.exists():
        with open(private_key_path, "r", encoding="utf-8") as f:
            priv_key_str = f.read().strip()
        with open(public_key_path, "r", encoding="utf-8") as f:
            pub_key_str = f.read().strip()
        return priv_key_str, pub_key_str

    curve = ec.SECP256R1()
    private_key = ec.generate_private_key(curve)
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    pub_raw = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    pub_b64 = base64.urlsafe_b64encode(pub_raw).decode("utf-8").rstrip("=")

    with open(private_key_path, "w", encoding="utf-8") as f:
        f.write(priv_pem)
    with open(public_key_path, "w", encoding="utf-8") as f:
        f.write(pub_b64)

    return priv_pem, pub_b64

class Settings(BaseSettings):
    APP_NAME: str = "Live Market Alert Engine"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'alerts.db'}"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    SMTP_FROM_EMAIL: Optional[str] = ""
    SMTP_USE_TLS: bool = True

    VAPID_CLAIM_EMAIL: str = "mailto:alerts@liveforexalerts.local"
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_PUBLIC_KEY: Optional[str] = None

    TWELVE_DATA_API_KEY: Optional[str] = ""
    FINNHUB_API_KEY: Optional[str] = ""
    DEFAULT_FEED_SOURCE: str = "binance"

    DISCORD_WEBHOOK_URL: Optional[str] = ""
    TELEGRAM_BOT_TOKEN: Optional[str] = ""
    TELEGRAM_CHAT_ID: Optional[str] = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

settings = Settings()

if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
    try:
        priv, pub = generate_vapid_keys_if_missing()
        settings.VAPID_PRIVATE_KEY = priv
        settings.VAPID_PUBLIC_KEY = pub
    except Exception as e:
        print(f"Warning initializing VAPID keys: {e}")
