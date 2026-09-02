import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

BASE_DIR = Path(__file__).resolve().parent.parent

# On Render (and similar PaaS), the project dir may be read-only after build.
# Use /tmp as a writable fallback for ephemeral files.
_WRITABLE_DIR = Path("/tmp") if os.path.exists("/tmp") and not os.access(BASE_DIR, os.W_OK) else BASE_DIR


def generate_vapid_keys_if_missing():
    """Generate VAPID EC key pair, writing to disk if possible, or returning in-memory keys."""
    # Try project dir first, then /tmp as fallback
    for key_dir in [BASE_DIR, Path("/tmp")]:
        private_key_path = key_dir / "vapid_private.pem"
        public_key_path = key_dir / "vapid_public.txt"
        if private_key_path.exists() and public_key_path.exists():
            try:
                priv_key_str = private_key_path.read_text(encoding="utf-8").strip()
                pub_key_str = public_key_path.read_text(encoding="utf-8").strip()
                if priv_key_str and pub_key_str:
                    return priv_key_str, pub_key_str
            except Exception:
                pass

    # Generate new keys
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

    # Try to persist to disk (best-effort, never crash)
    for key_dir in [BASE_DIR, Path("/tmp")]:
        try:
            (key_dir / "vapid_private.pem").write_text(priv_pem, encoding="utf-8")
            (key_dir / "vapid_public.txt").write_text(pub_b64, encoding="utf-8")
            break
        except Exception:
            continue

    return priv_pem, pub_b64


def _resolve_db_url() -> str:
    """Return a SQLite DB URL using a writable path (project dir or /tmp)."""
    for candidate_dir in [BASE_DIR, Path("/tmp")]:
        try:
            test_file = candidate_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            return f"sqlite+aiosqlite:///{candidate_dir / 'alerts.db'}"
        except Exception:
            continue
    # Last resort — in-memory (alerts won't persist but app won't crash)
    return "sqlite+aiosqlite:///:memory:"


class Settings(BaseSettings):
    APP_NAME: str = "Live Market Alert Engine"
    DATABASE_URL: str = _resolve_db_url()
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
    SEED_AT_STARTUP: bool = False

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
