# 통화 서비스 레이어
# - 외부 무료 API(exchangerate.host)에서 현재 환율과 3년 평균 계산
# - DB에 집계값 저장 (RateStat Document는 이 파일 내부에 정의)
# - 평균 대비 현재가 낮으면 구독자에게 이메일 발송

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict

import requests
from beanie import Document
from pydantic import Field
from beanie.operators import In

from ..core.config import settings
from ..models.notification import NotificationSetting
from ..models.user import User
import smtplib
from email.mime.text import MIMEText

# ---- 내부용 Document (요청된 디렉토리 구조를 유지하기 위해, 별도 models 파일을 추가하지 않고 여기 정의) ----
class RateStat(Document):
    base: str
    target: str
    current_rate: float
    avg_3y: float
    status: str  # "LOW" or "HIGH"
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "rate_stats"

# ---- 외부 API 호출 ----

def _api_latest(base: str, target: str) -> float:
    # exchangerate.host 무료 엔드포인트 사용 (API 키 불필요)
    url = f"{settings.CURRENCY_API_BASE}/latest"
    resp = requests.get(url, params={"base": base, "symbols": target}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return float(data["rates"][target])

def _api_timeseries_avg_3y(base: str, target: str) -> float:
    # 3년 기간 계산 (오늘 기준)
    end = datetime.utcnow().date()
    start = end - timedelta(days=365*3 + 5)  # 윤년/영업일 버퍼
    url = f"{settings.CURRENCY_API_BASE}/timeseries"
    resp = requests.get(url, params={"base": base, "symbols": target, "start_date": start.isoformat(), "end_date": end.isoformat()}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    rates = [float(day[target]) for day in (v["rates"] if "rates" in v else v).values()] if False else [
        float(v[target]) for _, v in sorted(data["rates"].items())
    ]
    if not rates:
        raise RuntimeError("No rates returned for timeseries")
    return sum(rates)/len(rates)

# ---- 이메일 ----

def _send_email(to_email: str, subject: str, body: str):
    # 간단한 SMTP 발송 (Gmail 등)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    try:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    finally:
        server.quit()

# ---- 퍼블릭 서비스 API ----

async def compute_and_store(base: str | None = None, target: str | None = None) -> RateStat:
    base = base or settings.DEFAULT_BASE_CURRENCY
    target = target or settings.DEFAULT_TARGET_CURRENCY

    current = _api_latest(base, target)
    avg3 = _api_timeseries_avg_3y(base, target)
    status = "LOW" if current < avg3 else "HIGH"

    stat = RateStat(base=base, target=target, current_rate=current, avg_3y=avg3, status=status)
    await stat.insert()
    return stat

async def notify_if_low(stat: RateStat):
    if stat.status != "LOW":
        return

    # 알림 구독자 조회
    subs = await NotificationSetting.find(NotificationSetting.is_active == True).to_list()
    if not subs:
        return

    # 사용자 이메일 목록 추출
    user_ids = [s.user.id for s in subs if getattr(s, "user", None)]
    if not user_ids:
        return
    users = await User.find(In(User.id, user_ids)).to_list()

    subject = f"[FX Alert] {stat.base}/{stat.target} 현재 환율이 3년 평균보다 낮습니다"
    body = (
        f"기준통화: {stat.base}\n"
        f"대상통화: {stat.target}\n"
        f"현재 환율: {stat.current_rate:.4f}\n"
        f"3년 평균: {stat.avg_3y:.4f}\n"
        f"상태: {stat.status}\n"
        f"계산 시각(UTC): {stat.calculated_at.isoformat()}"
    )

    for u in users:
        _send_email(u.email, subject, body)

async def compute_store_and_notify(base: str | None = None, target: str | None = None) -> RateStat:
    stat = await compute_and_store(base, target)
    await notify_if_low(stat)
    return stat

async def get_latest_stat_or_live(base: str, target: str) -> dict:
    # 최근 저장된 통계를 우선 반환하고, 없으면 즉시 계산 (API 호출)
    latest = await RateStat.find(RateStat.base == base, RateStat.target == target).sort(-RateStat.calculated_at).first_or_none()
    if latest:
        return {
            "base": base,
            "target": target,
            "current_rate": latest.current_rate,
            "avg_3y": latest.avg_3y,
            "status": latest.status,
            "last_updated": latest.calculated_at.isoformat(),
            "source": "db-cache"
        }
    # DB에 없으면 바로 계산
    current = _api_latest(base, target)
    avg3 = _api_timeseries_avg_3y(base, target)
    status = "LOW" if current < avg3 else "HIGH"
    return {
        "base": base,
        "target": target,
        "current_rate": current,
        "avg_3y": avg3,
        "status": status,
        "last_updated": datetime.utcnow().isoformat(),
        "source": "live"
    }
