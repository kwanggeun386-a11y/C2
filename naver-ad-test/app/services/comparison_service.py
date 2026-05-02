"""
전일 대비 비교 서비스
PROJECT_RULES.txt 섹션 21 기준
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from app.db import performance_repository

logger = logging.getLogger(__name__)

# 비교 대상 지표
COMPARE_METRICS = [
    "impressions",
    "clicks",
    "cost",
    "ctr",
    "cpc",
    "purchase_conversions",
    "purchase_revenue",
    "purchase_cpa",
    "purchase_roas",
]


def _calc_diff(today_val: float, yesterday_val: float) -> dict:
    """
    diff와 change_rate 계산.
    yesterday_val이 0이면 change_rate는 None.
    """
    diff = today_val - yesterday_val
    change_rate = None if yesterday_val == 0 else diff / yesterday_val
    return {"diff": diff, "change_rate": change_rate}


def compare(
    conn: sqlite3.Connection,
    advertiser_id: int,
    selected_date: str,
) -> dict:
    """
    선택일과 전일 daily_summary를 비교해 반환.

    반환:
        {
            "success": bool,
            "has_yesterday": bool,
            "message": str or None,       # 전일 데이터 없을 때 메시지
            "selected_date": str,
            "yesterday_date": str,
            "today": dict,                # 오늘 지표
            "yesterday": dict,            # 전일 지표 (없으면 None)
            "comparison": {               # 지표별 비교 결과
                "impressions": {"today": float, "yesterday": float, "diff": float, "change_rate": float|None},
                ...
            }
        }
    """
    # 날짜 계산
    today_dt = datetime.strptime(selected_date, "%Y-%m-%d")
    yesterday_dt = today_dt - timedelta(days=1)
    yesterday_date = yesterday_dt.strftime("%Y-%m-%d")

    # 오늘 데이터 조회
    today_data = performance_repository.get_daily_summary(conn, advertiser_id, selected_date)
    if not today_data:
        return {
            "success": False,
            "has_yesterday": False,
            "message": f"선택일({selected_date}) 데이터가 없습니다.",
            "selected_date": selected_date,
            "yesterday_date": yesterday_date,
            "today": None,
            "yesterday": None,
            "comparison": {},
        }

    # 전일 데이터 조회
    yesterday_data = performance_repository.get_daily_summary(conn, advertiser_id, yesterday_date)
    if not yesterday_data:
        logger.info(f"전일 데이터 없음: advertiser_id={advertiser_id}, date={yesterday_date}")
        return {
            "success": True,
            "has_yesterday": False,
            "message": "전일 데이터가 없습니다.",
            "selected_date": selected_date,
            "yesterday_date": yesterday_date,
            "today": today_data,
            "yesterday": None,
            "comparison": {},
        }

    # 지표별 비교 계산
    comparison = {}
    for metric in COMPARE_METRICS:
        today_val     = float(today_data.get(metric, 0) or 0)
        yesterday_val = float(yesterday_data.get(metric, 0) or 0)
        comparison[metric] = {
            "today":       today_val,
            "yesterday":   yesterday_val,
            **_calc_diff(today_val, yesterday_val),
        }

    logger.info(f"전일 비교 완료: advertiser_id={advertiser_id}, {yesterday_date} → {selected_date}")

    return {
        "success": True,
        "has_yesterday": True,
        "message": None,
        "selected_date": selected_date,
        "yesterday_date": yesterday_date,
        "today": today_data,
        "yesterday": yesterday_data,
        "comparison": comparison,
    }
