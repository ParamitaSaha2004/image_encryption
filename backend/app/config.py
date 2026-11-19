"""
Application Configuration Module
Loads settings from environment variables or .env file with robust defaults and absolute storage paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "SecurePix")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "hice_db")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "hice_super_secret_jwt_key_change_in_production_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Storage Vault - Guarantees Absolute Paths
    VAULT_STORAGE_PATH: str = str((BASE_DIR / "app" / "storage" / "vault").resolve())
    SAMPLES_STORAGE_PATH: str = str((BASE_DIR / "app" / "storage" / "samples").resolve())
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

    # AI Anomaly Detection
    ANOMALY_CONTAMINATION: float = float(os.getenv("ANOMALY_CONTAMINATION", "0.05"))
    MAX_FAILED_LOGINS_THRESHOLD: int = int(os.getenv("MAX_FAILED_LOGINS_THRESHOLD", "5"))
    MAX_DECRYPTION_FAILS_THRESHOLD: int = int(os.getenv("MAX_DECRYPTION_FAILS_THRESHOLD", "3"))

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.VAULT_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.SAMPLES_STORAGE_PATH, exist_ok=True)
