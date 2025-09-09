# 설정 모듈
# - .env 값들을 한 곳에서 관리
# - 기본값을 제공하여 로컬 실행 편의성 확보

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_NAME: str = "fx-alert"
    ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGODB_URI: str = "mongodb://localhost:27017/fx_alert"

    JWT_SECRET_KEY: str = "please_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    DEFAULT_BASE_CURRENCY: str = "USD"
    DEFAULT_TARGET_CURRENCY: str = "KRW"
    CURRENCY_API_BASE: str = "https://v6.exchangerate-api.com/v6"
    CURRENCY_API_KEY: str # API 키 추가

    # ALPHA_VANTAGE_API_KEY: str 무료 제한 

    REDIS_URL: str = "redis://localhost:6379/0"
    TIMEZONE: str = "Asia/Seoul"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "FX Alert <noreply@example.com>"
    SMTP_TLS: bool = True

    # 캐시 TTL 설정 (초 단위). 기본값 1시간 (3600초)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", 3600))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
