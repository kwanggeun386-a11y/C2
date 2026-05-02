"""
upload_files 테이블 repository
PROJECT_RULES.txt 섹션 7.2 기준
SQL은 이 파일에서만 작성한다.
"""
import logging
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


def create_upload(
    conn: sqlite3.Connection,
    advertiser_id: int,
    original_file_name: str,
    stored_file_path: str,
    report_start_date: Optional[str],
    report_end_date: Optional[str],
    upload_type: str,
    file_hash: Optional[str],
    row_count: int,
    status: str = "success",
) -> int:
    """업로드 이력 저장. 생성된 upload_id 반환."""
    cursor = conn.execute(
        """
        INSERT INTO upload_files (
            advertiser_id, original_file_name, stored_file_path,
            report_start_date, report_end_date,
            upload_type, file_hash, row_count, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            advertiser_id,
            original_file_name,
            stored_file_path,
            report_start_date,
            report_end_date,
            upload_type,
            file_hash,
            row_count,
            status,
        ),
    )
    conn.commit()
    upload_id = cursor.lastrowid
    logger.info(f"업로드 이력 저장: upload_id={upload_id}, file={original_file_name}")
    return upload_id


def update_status(conn: sqlite3.Connection, upload_id: int, status: str) -> None:
    """업로드 상태 갱신."""
    conn.execute(
        "UPDATE upload_files SET status = ? WHERE upload_id = ?",
        (status, upload_id),
    )
    conn.commit()
    logger.info(f"업로드 상태 갱신: upload_id={upload_id}, status={status}")
