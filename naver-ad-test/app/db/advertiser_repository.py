"""
advertisers 테이블 repository
PROJECT_RULES.txt 섹션 7.1 기준
SQL은 이 파일에서만 작성한다.
"""
import logging
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


def get_by_name(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    """이름으로 광고주 조회. 없으면 None."""
    row = conn.execute(
        "SELECT * FROM advertisers WHERE advertiser_name = ?",
        (name,)
    ).fetchone()
    return dict(row) if row else None


def get_by_id(conn: sqlite3.Connection, advertiser_id: int) -> Optional[dict]:
    """ID로 광고주 조회. 없으면 None."""
    row = conn.execute(
        "SELECT * FROM advertisers WHERE advertiser_id = ?",
        (advertiser_id,)
    ).fetchone()
    return dict(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[dict]:
    """전체 광고주 목록 반환."""
    rows = conn.execute(
        "SELECT * FROM advertisers ORDER BY advertiser_name"
    ).fetchall()
    return [dict(r) for r in rows]


def create(
    conn: sqlite3.Connection,
    name: str,
    industry: Optional[str] = None,
    memo: Optional[str] = None,
) -> dict:
    """광고주 생성. 생성된 광고주 dict 반환."""
    conn.execute(
        """
        INSERT INTO advertisers (advertiser_name, industry, memo)
        VALUES (?, ?, ?)
        """,
        (name, industry, memo),
    )
    conn.commit()
    adv = get_by_name(conn, name)
    logger.info(f"광고주 생성: {name} (id={adv['advertiser_id']})")
    return adv


def get_or_create(
    conn: sqlite3.Connection,
    name: str,
    industry: Optional[str] = None,
    memo: Optional[str] = None,
) -> tuple[dict, bool]:
    """
    광고주를 조회하고 없으면 생성.
    반환: (advertiser_dict, created: bool)
    """
    adv = get_by_name(conn, name)
    if adv:
        return adv, False
    adv = create(conn, name, industry, memo)
    return adv, True
