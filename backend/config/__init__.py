from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/car_hunter"
    redis_url: str = "redis://redis:6379/0"
    gemini_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "car-hunter"
    minio_secure: bool = False
    scrape_interval_minutes: int = 14
    notification_score_threshold: int = 85
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_to: str = ""

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


settings = Settings()
