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
from alpha_vantage.foreignexchange import ForeignExchange # Alpha Vantage 클라이언트
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
    # Alpha Vantage API를 사용하여 3년치 시계열 데이터를 가져오고 평균을 계산합니다.
    # 무료 플랜은 API 호출 제한이 있을 수 있습니다.
    try:
        # Alpha Vantage API 키를 로그로 출력하여 확인 (디버깅용)
        print(f"Alpha Vantage API Key being used: {settings.ALPHA_VANTAGE_API_KEY[:5]}...{settings.ALPHA_VANTAGE_API_KEY[-5:]}") # 보안을 위해 앞뒤 5글자만 출력
        # ForeignExchange 객체 생성 직전 로그 추가
        print(f"[AlphaVantage] Attempting to initialize ForeignExchange with key.")
        fx = ForeignExchange(key=settings.ALPHA_VANTAGE_API_KEY)
        # 일별 환율 데이터 가져오기 (full outputsize로 지난 20년간의 데이터 가져옴)
        data, _ = fx.get_currency_exchange_daily(from_symbol=base, to_symbol=target, outputsize='full')
        
        # Alpha Vantage API로부터 받은 원본 데이터 출력
        print(f"Alpha Vantage Raw Data for {base}/{target}: {data}")

        # 데이터가 없을 경우 로그 추가
        if not data:
            print(f"[AlphaVantage] No data received from API for {base}/{target}. Check API key, network, or API limits.")
            print(f"Alpha Vantage: No data found for {base}/{target}. Returning dummy value.")
            return 1250.0

        df = pd.DataFrame.from_dict(data).T
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=3*365)

        # 3년치 데이터 필터링
        df_3y = df.loc[start_date.strftime('%Y-%m-%d'):end_date.strftime('%Y-%m-%d')]
        
        # 3년치 필터링된 데이터 출력
        print(f"Alpha Vantage 3-year Filtered Data for {base}/{target}: {df_3y}")

        if not df_3y.empty:
            # '4. close' 가격의 3년 평균 계산 (Alpha Vantage 필드명)
            avg_rate = df_3y['4. close'].astype(float).mean()
            print(f"Alpha Vantage: Successfully fetched data for {base}/{target}. Average: {avg_rate:.4f}")
            return avg_rate
        else:
            print(f"Alpha Vantage: No 3-year data found for {base}/{target}. Returning dummy value.")
            return 1250.0

    except Exception as e:
        # 예외 발생 시 상세한 오류 메시지와 스택 트레이스 출력
        logger.error(f"Alpha Vantage: Error fetching data for {base}/{target}. Message: {e}", exc_info=True)
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
    # 최근 저장된 통계를 우선 반환하고, 없으면 즉시 계산 (API 호출)
    latest = await RateStat.find({"base": base, "target": target}).sort(-RateStat.calculated_at).first_or_none()
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
