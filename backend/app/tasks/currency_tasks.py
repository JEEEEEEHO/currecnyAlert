# Celery 작업 & 스케줄
# - 평일 오전 9시, 오후 12시에 실행 (Asia/Seoul)
# - 현재 환율 vs 3년 평균 계산 후, 평균보다 낮으면 이메일 발송

import os
from celery import Celery
from celery.schedules import crontab
import asyncio

from ..core.config import settings
from ..services.currency_service import compute_store_and_notify
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ..models.user import User
from ..models.notification import NotificationSetting

# Celery 앱 초기화
celery_app = Celery("currency_tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# 비동기 Beanie 초기화 유틸
async def _init_beanie():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_default_database()
    # RateStat 모델은 currency_service 내부 정의 -> 런타임 import
    from ..services.currency_service import RateStat  # noqa: WPS433 (runtime import by design)
    await init_beanie(database=db, document_models=[User, NotificationSetting, RateStat])

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 평일 오전 9시, 오후 12시 (KST) 실행
    sender.add_periodic_task(
        crontab(hour=9, minute=0, day_of_week="1-5", timezone=settings.TIMEZONE),
        run_scheduled.s(),
        name="compute_and_maybe_notify_9am_kst",
    )
    sender.add_periodic_task(
        crontab(hour=12, minute=0, day_of_week="1-5", timezone=settings.TIMEZONE),
        run_scheduled.s(),
        name="compute_and_maybe_notify_12pm_kst",
    )

@celery_app.task
def run_scheduled():
    # Celery는 동기 함수이므로, 내부에서 asyncio 루프 실행
    async def _run():
        await _init_beanie()
        await compute_store_and_notify()
    asyncio.run(_run())
