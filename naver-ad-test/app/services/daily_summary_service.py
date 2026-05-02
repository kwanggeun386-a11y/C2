"""
daily_summary 재계산 서비스
PROJECT_RULES.txt 섹션 20 기준
"""
import logging
import sqlite3

from app.core.metrics import aggregate_metrics
from app.db import performance_repository

logger = logging.getLogger(__name__)


def recalculate(conn: sqlite3.Connection, advertiser_id: int, date: str) -> dict:
    """
    해당 광고주 + 날짜의 daily_performance를 집계해
    daily_summary를 upsert한다.
    반환: 집계된 summary dict
    """
    df = performance_repository.get_performance_by_date(conn, advertiser_id, date)

    if df.empty:
        logger.warning(f"daily_summary 재계산: 데이터 없음 (advertiser_id={advertiser_id}, date={date})")
        return {}

    summary = aggregate_metrics(df)
    performance_repository.upsert_daily_summary(conn, advertiser_id, date, summary)
    logger.info(f"daily_summary 재계산 완료: advertiser_id={advertiser_id}, date={date}")
    return summary
