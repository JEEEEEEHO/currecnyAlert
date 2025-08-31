# FastAPI 진입점
# - Beanie ODM 초기화 (MongoDB)
# - 라우터 라우팅
# - CORS 설정
# - Celery는 별도 프로세스로 동작 (tasks/currency_tasks.py 참고)

import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pydantic import BaseModel
import os

from .core.config import settings
from .models.user import User
from .models.notification import NotificationSetting
from .api.v1.auth import router as auth_router
from .api.v1.currency import router as currency_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="환율 알림 서비스 API",
    description="3년 평균 대비 환율 변동 알림 서비스",
    version="1.0.0"
)

# CORS 허용 도메인 세팅
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Beanie 초기화 (앱 시작 시 1회)
@app.on_event("startup")
async def app_init():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_default_database()
    await init_beanie(database=db, document_models=[User, NotificationSetting])
    # 참고: RateStat(환율 통계) Document는 services/currency_service.py 내부에 정의됨.

# 간단한 헬스체크
@app.get("/")
async def root():
    return {"ok": True, "app": "fx-alert", "time": datetime.utcnow().isoformat()}

# API v1 라우터 등록
app.include_router(auth_router, prefix="/api/v1")
app.include_router(currency_router, prefix="/api/v1")
