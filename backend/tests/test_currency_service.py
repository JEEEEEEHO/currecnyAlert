# 외부 API를 모킹하여 평균 계산 로직 검증
from unittest.mock import patch
import app.services.currency_service as cs

@patch("app.services.currency_service._api_latest", return_value=1300.0)
@patch("app.services.currency_service._api_timeseries_avg_3y", return_value=1350.0)
def test_get_latest_stat_or_live_low(mock_avg, mock_latest):
    import asyncio
    data = asyncio.run(cs.get_latest_stat_or_live("USD", "KRW"))
    assert data["status"] == "LOW"
    assert data["current_rate"] == 1300.0
    assert data["avg_3y"] == 1350.0

@patch("app.services.currency_service._api_latest", return_value=1400.0)
@patch("app.services.currency_service._api_timeseries_avg_3y", return_value=1350.0)
def test_get_latest_stat_or_live_high(mock_avg, mock_latest):
    import asyncio
    data = asyncio.run(cs.get_latest_stat_or_live("USD", "KRW"))
    assert data["status"] == "HIGH"
    assert data["current_rate"] == 1400.0
    assert data["avg_3y"] == 1350.0
