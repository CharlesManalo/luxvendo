"""Application configuration."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{DB_DIR}/wifi_system.db"
)

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
API_KEY = os.getenv("API_KEY", secrets.token_hex(16))

APP_NAME = os.getenv("APP_NAME", "WiFi Voucher System")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Session settings
SESSION_COOKIE_NAME = "wifi_admin_session"
SESSION_MAX_AGE = 86400  # 24 hours

# Background tasks
SESSION_EXPIRY_CHECK_INTERVAL = 60  # seconds
