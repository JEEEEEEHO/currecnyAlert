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
import pandas as pd # Alpha Vantage 응답 처리를 위해 필요
# from alpha_vantage.foreignexchange import ForeignExchange # Alpha Vantage 클라이언트 (더 이상 사용 안함)
import logging # 로깅 추가

from ..core.config import settings
from ..models.notification import NotificationSetting
from ..models.user import User
import smtplib
from email.mime.text import MIMEText

# 로거 설정
logger = logging.getLogger(__name__)

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
    # exchangerate-api.com 엔드포인트 사용
    url = f"{settings.CURRENCY_API_BASE}/{settings.CURRENCY_API_KEY}/latest/{base}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return float(data["conversion_rates"][target])

def _api_timeseries_avg_3y(base: str, target: str) -> float:
    # exchangerate.host API를 사용하여 3년치 시계열 데이터를 가져오고 평균을 계산합니다.
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=3 * 365) # 3년치 데이터

        # exchangerate.host timeseries 엔드포인트 사용
        # 예: https://api.exchangerate.host/timeseries?start_date=2021-01-01&end_date=2024-01-01&base=USD&symbols=KRW
        url = (
            f"https://api.exchangerate.host/timeseries?"
            f"start_date={start_date.strftime('%Y-%m-%d')}&"
            f"end_date={end_date.strftime('%Y-%m-%d')}&"
            f"base={base}&symbols={target}"
        )
        
        print(f"[exchangerate.host] Calling timeseries API: {url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status() # HTTP 에러 발생 시 예외 발생
        data = resp.json()

        # API 응답에서 환율 데이터 추출
        # data['rates']는 {'YYYY-MM-DD': {'SYMBOL': RATE}} 형태입니다.
        rates = []
        for date_str, rate_data in data.get('rates', {}).items():
            if target in rate_data:
                rates.append(rate_data[target])
        
        if not rates:
            print(f"[exchangerate.host] No historical data received for {base}/{target}. Check API response or query parameters.")
            return 1250.0
        
        df = pd.DataFrame(rates, columns=['rate'])
        avg_rate = df['rate'].astype(float).mean()

        print(f"[exchangerate.host]: Successfully fetched historical data for {base}/{target}. Average: {avg_rate:.4f}")
        return avg_rate

    except requests.exceptions.RequestException as e:
        # requests 라이브러리 관련 예외 처리 (네트워크 오류, HTTP 오류 등)
        logger.error(f"[exchangerate.host]: Network or HTTP error fetching data for {base}/{target}. Message: {e}", exc_info=True)
        return 1250.0
    except Exception as e:
        # 그 외 모든 예외 처리
        logger.error(f"[exchangerate.host]: Error fetching or processing data for {base}/{target}. Message: {e}", exc_info=True)
        return 1250.0

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
    # 최근 저장된 통계를 우선 반환하고, 없거나 오래되었으면 즉시 계산 (API 호출)
    latest = await RateStat.find({"base": base, "target": target}).sort(-RateStat.calculated_at).first_or_none()

    # 캐시 유효 기간 (예: 1시간) 설정 - 환경 변수에서 가져옴
    # NOTE: CACHE_TTL_SECONDS는 나중에 config.py에 추가될 것입니다.
    cache_ttl_seconds = settings.CACHE_TTL_SECONDS # 초 단위

    if latest:
        # 캐시 데이터가 유효한지 확인
        # calculated_at은 UTC로 저장되므로, 현재 시간도 UTC로 비교해야 합니다.
        time_since_last_update = (datetime.utcnow() - latest.calculated_at).total_seconds()
        if time_since_last_update < cache_ttl_seconds:
            print(f"[CurrencyService] Returning cached stat for {base}/{target}. Last updated {time_since_last_update:.0f} seconds ago.")
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
    print(f"[CurrencyService] No latest stat in DB. Calling _api_latest and _api_timeseries_avg_3y...")
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
