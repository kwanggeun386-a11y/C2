"""
daily_performance / daily_summary 테이블 repository
PROJECT_RULES.txt 섹션 7.3, 7.4 기준
SQL은 이 파일에서만 작성한다.
"""
import logging
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)


# ── daily_performance ─────────────────────────────────────

def has_performance(conn: sqlite3.Connection, advertiser_id: int, date: str) -> bool:
    """해당 광고주 + 날짜 데이터 존재 여부 확인."""
    row = conn.execute(
        "SELECT 1 FROM daily_performance WHERE advertiser_id = ? AND date = ? LIMIT 1",
        (advertiser_id, date),
    ).fetchone()
    return row is not None


def has_performance_any_date(conn: sqlite3.Connection, advertiser_id: int, dates: list[str]) -> list[str]:
    """날짜 목록 중 이미 데이터가 있는 날짜 반환."""
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"""
        SELECT DISTINCT date FROM daily_performance
        WHERE advertiser_id = ? AND date IN ({placeholders})
        """,
        (advertiser_id, *dates),
    ).fetchall()
    return [r["date"] for r in rows]


def delete_performance(conn: sqlite3.Connection, advertiser_id: int, date: str) -> int:
    """해당 광고주 + 날짜의 daily_performance 전체 삭제. 삭제 행 수 반환."""
    cursor = conn.execute(
        "DELETE FROM daily_performance WHERE advertiser_id = ? AND date = ?",
        (advertiser_id, date),
    )
    conn.commit()
    logger.info(f"daily_performance 삭제: advertiser_id={advertiser_id}, date={date}, {cursor.rowcount}행")
    return cursor.rowcount


def insert_performance_rows(
    conn: sqlite3.Connection,
    advertiser_id: int,
    upload_id: int,
    df: pd.DataFrame,
) -> int:
    """
    DataFrame 행을 daily_performance에 batch insert.
    date 컬럼이 없으면 RuntimeError.
    반환: 삽입 행 수
    """
    if "date" not in df.columns:
        raise RuntimeError("date 컬럼이 없습니다. 삽입 불가.")

    cols = [
        "campaign_type", "campaign", "ad_group", "media",
        "search_term", "keyword",
        "impressions", "clicks", "cost",
        "total_conversions", "total_revenue",
        "purchase_conversions", "purchase_revenue",
    ]

    rows = []
    for _, row in df.iterrows():
        rows.append((
            advertiser_id,
            upload_id,
            str(row["date"]),
            row.get("campaign_type"),
            row.get("campaign"),
            row.get("ad_group"),
            row.get("media"),
            row.get("search_term"),
            row.get("keyword"),
            float(row.get("impressions", 0) or 0),
            float(row.get("clicks", 0) or 0),
            float(row.get("cost", 0) or 0),
            float(row.get("total_conversions", 0) or 0),
            float(row.get("total_revenue", 0) or 0),
            float(row.get("purchase_conversions", 0) or 0),
            float(row.get("purchase_revenue", 0) or 0),
        ))

    conn.executemany(
        """
        INSERT INTO daily_performance (
            advertiser_id, upload_id, date,
            campaign_type, campaign, ad_group, media,
            search_term, keyword,
            impressions, clicks, cost,
            total_conversions, total_revenue,
            purchase_conversions, purchase_revenue
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    logger.info(f"daily_performance 삽입: {len(rows)}행 (advertiser_id={advertiser_id})")
    return len(rows)


def get_performance_by_date(
    conn: sqlite3.Connection, advertiser_id: int, date: str
) -> pd.DataFrame:
    """해당 광고주 + 날짜의 daily_performance를 DataFrame으로 반환."""
    rows = conn.execute(
        """
        SELECT * FROM daily_performance
        WHERE advertiser_id = ? AND date = ?
        """,
        (advertiser_id, date),
    ).fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


# ── daily_summary ─────────────────────────────────────────

def upsert_daily_summary(
    conn: sqlite3.Connection,
    advertiser_id: int,
    date: str,
    summary: dict,
) -> None:
    """
    daily_summary upsert (INSERT OR REPLACE).
    summary dict: aggregate_metrics() 반환값
    """
    conn.execute(
        """
        INSERT INTO daily_summary (
            advertiser_id, date,
            impressions, clicks, cost,
            ctr, cpc,
            total_conversions, total_revenue,
            total_cvr, total_cpa, total_roas,
            purchase_conversions, purchase_revenue,
            purchase_cvr, purchase_cpa, purchase_roas,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(advertiser_id, date) DO UPDATE SET
            impressions          = excluded.impressions,
            clicks               = excluded.clicks,
            cost                 = excluded.cost,
            ctr                  = excluded.ctr,
            cpc                  = excluded.cpc,
            total_conversions    = excluded.total_conversions,
            total_revenue        = excluded.total_revenue,
            total_cvr            = excluded.total_cvr,
            total_cpa            = excluded.total_cpa,
            total_roas           = excluded.total_roas,
            purchase_conversions = excluded.purchase_conversions,
            purchase_revenue     = excluded.purchase_revenue,
            purchase_cvr         = excluded.purchase_cvr,
            purchase_cpa         = excluded.purchase_cpa,
            purchase_roas        = excluded.purchase_roas,
            updated_at           = datetime('now','localtime')
        """,
        (
            advertiser_id, date,
            summary.get("impressions", 0),
            summary.get("clicks", 0),
            summary.get("cost", 0),
            summary.get("ctr", 0),
            summary.get("cpc", 0),
            summary.get("total_conversions", 0),
            summary.get("total_revenue", 0),
            summary.get("total_cvr", 0),
            summary.get("total_cpa", 0),
            summary.get("total_roas", 0),
            summary.get("purchase_conversions", 0),
            summary.get("purchase_revenue", 0),
            summary.get("purchase_cvr", 0),
            summary.get("purchase_cpa", 0),
            summary.get("purchase_roas", 0),
        ),
    )
    conn.commit()
    logger.info(f"daily_summary upsert 완료: advertiser_id={advertiser_id}, date={date}")


def get_daily_summary(
    conn: sqlite3.Connection, advertiser_id: int, date: str
) -> dict | None:
    """해당 광고주 + 날짜의 daily_summary 반환. 없으면 None."""
    row = conn.execute(
        "SELECT * FROM daily_summary WHERE advertiser_id = ? AND date = ?",
        (advertiser_id, date),
    ).fetchone()
    return dict(row) if row else None
