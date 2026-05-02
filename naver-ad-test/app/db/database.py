"""
SQLite DB 연결 및 초기화
PROJECT_RULES.txt 섹션 6, 7 기준
"""
import sqlite3
import logging
from pathlib import Path

from app.db.schema import ALL_SCHEMAS

logger = logging.getLogger(__name__)


def get_connection(db_path: Path) -> sqlite3.Connection:
    """DB 연결 반환. row_factory는 sqlite3.Row 사용."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Path) -> sqlite3.Connection:
    """
    DB 초기화.
    - db_path 상위 폴더가 없으면 자동 생성
    - 테이블이 없으면 생성 (IF NOT EXISTS)
    - 연결 객체 반환
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)

    for sql in ALL_SCHEMAS:
        conn.execute(sql)
    conn.commit()

    logger.info(f"DB 초기화 완료: {db_path}")
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """DB 연결 종료."""
    if conn:
        conn.close()
        logger.info("DB 연결 종료")
