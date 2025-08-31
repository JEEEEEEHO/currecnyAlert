# 환율/알림 라우터
# - GET /api/v1/currency/latest : 인증 불필요
# - POST /api/v1/notifications/subscribe : 인증 필요
# - DELETE /api/v1/notifications/unsubscribe : 인증 필요
#
# 주의: 디렉토리 구조 제약으로 notifications 라우트도 이 파일에서 처리합니다.

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ....core.config import settings
from ....core.security import get_current_user
from ....models.user import User
from ....models.notification import NotificationSetting
from ....services.currency_service import get_latest_stat_or_live

router = APIRouter(tags=["currency"])

class LatestResponse(BaseModel):
    base: str
    target: str
    current_rate: float
    avg_3y: float
    status: str
    last_updated: str
    source: str

@router.get("/currency/latest", response_model=LatestResponse, summary="현재 환율 + 3년 평균 반환")
async def currency_latest(base: str | None = None, target: str | None = None):
    base = base or settings.DEFAULT_BASE_CURRENCY
    target = target or settings.DEFAULT_TARGET_CURRENCY
    data = await get_latest_stat_or_live(base, target)
    return data

# ---- Notifications ----

noti = APIRouter(prefix="/notifications", tags=["notifications"])

@noti.post("/subscribe", summary="알림 구독 활성화 (로그인 필요)")
async def subscribe(user: User = Depends(get_current_user)):
    existing = await NotificationSetting.find_one(NotificationSetting.user.id == user.id)
    if existing:
        # 이미 있으면 활성화만 true
        if not existing.is_active:
            existing.is_active = True
            await existing.save()
        return {"ok": True, "active": True}
    # 새로 생성
    ns = NotificationSetting(user=user, is_active=True)
    await ns.insert()
    return {"ok": True, "active": True}

@noti.delete("/unsubscribe", summary="알림 구독 비활성화 (로그인 필요)")
async def unsubscribe(user: User = Depends(get_current_user)):
    existing = await NotificationSetting.find_one(NotificationSetting.user.id == user.id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    existing.is_active = False
    await existing.save()
    return {"ok": True, "active": False}

router.include_router(noti, prefix="")
