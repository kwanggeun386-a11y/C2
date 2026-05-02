"""
단일 업로드 저장 서비스
PROJECT_RULES.txt 섹션 15 기준
"""
import hashlib
import logging
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

from app.config import UPLOADS_DIR
from app.core.column_mapper import map_columns
from app.core.file_loader import load_file
from app.core.formatter import format_numeric_columns
from app.core.validator import validate_columns
from app.db import advertiser_repository, performance_repository, upload_repository
from app.services import daily_summary_service

logger = logging.getLogger(__name__)


def _calc_file_hash(path: Path) -> str:
    """파일 MD5 해시 계산."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_to_uploads(src: Path, advertiser_name: str) -> Path:
    """원본 파일을 app_data/uploads/{광고주명}/에 복사. 저장 경로 반환."""
    dest_dir = UPLOADS_DIR / advertiser_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    # 동일 파일명 충돌 방지: 이미 있으면 덮어쓰기
    shutil.copy2(str(src), str(dest))
    logger.info(f"원본 파일 복사: {src.name} → {dest}")
    return dest


def upload_file(
    conn: sqlite3.Connection,
    advertiser_name: str,
    file_path: str,
    selected_date: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """
    단일 파일 업로드 흐름 전체를 처리.

    반환:
        {
            "success": bool,
            "advertiser_id": int,
            "advertiser_name": str,
            "upload_id": int,
            "row_count": int,
            "dates": list[str],   # 저장된 날짜 목록
            "skipped_dates": list[str],  # overwrite=False로 건너뛴 날짜
            "error": str or None,
        }
    """
    path = Path(file_path)

    # ── 1. 광고주 선택 또는 생성 ──────────────────────────
    adv, created = advertiser_repository.get_or_create(conn, advertiser_name)
    advertiser_id = adv["advertiser_id"]
    if created:
        logger.info(f"새 광고주 생성: {advertiser_name}")
    else:
        logger.info(f"기존 광고주 사용: {advertiser_name} (id={advertiser_id})")

    # ── 2. 파일 읽기 ──────────────────────────────────────
    load_result = load_file(path)
    if not load_result["success"]:
        return {"success": False, "error": load_result["error"]}

    df = load_result["df"]

    # ── 3. 컬럼 매핑 ──────────────────────────────────────
    df = map_columns(df)["df"]

    # ── 4. 필수 컬럼 검증 ─────────────────────────────────
    validation = validate_columns(df)
    if not validation["valid"]:
        return {
            "success": False,
            "error": f"필수 컬럼 누락: {validation['missing_required']}",
        }

    # ── 5. 숫자 정리 ──────────────────────────────────────
    df = format_numeric_columns(df)

    # ── 6. date 컬럼 처리 ─────────────────────────────────
    if "date" not in df.columns:
        if not selected_date:
            return {"success": False, "error": "date 컬럼 없음. --date 옵션으로 기준일을 지정해 주세요."}
        df["date"] = selected_date
        logger.info(f"date 컬럼 없음 → CLI 기준일 사용: {selected_date}")

    dates = sorted(df["date"].dropna().unique().tolist())
    report_start = dates[0] if dates else selected_date
    report_end   = dates[-1] if dates else selected_date

    # ── 7. 중복 날짜 확인 ─────────────────────────────────
    existing_dates = performance_repository.has_performance_any_date(
        conn, advertiser_id, dates
    )
    skipped_dates: list[str] = []

    if existing_dates and not overwrite:
        logger.warning(
            f"이미 데이터가 있는 날짜: {existing_dates}. "
            f"--overwrite 옵션 없이는 건너뜁니다."
        )
        skipped_dates = existing_dates
        dates_to_insert = [d for d in dates if d not in existing_dates]
        if not dates_to_insert:
            return {
                "success": False,
                "error": (
                    f"업로드할 날짜가 없습니다. "
                    f"이미 저장된 날짜: {existing_dates}. "
                    f"덮어쓰려면 --overwrite 옵션을 사용하세요."
                ),
                "skipped_dates": skipped_dates,
            }
        df = df[df["date"].isin(dates_to_insert)].copy()
        dates = dates_to_insert

    if existing_dates and overwrite:
        for d in existing_dates:
            performance_repository.delete_performance(conn, advertiser_id, d)
        logger.info(f"기존 데이터 삭제 후 재저장: {existing_dates}")

    # ── 8. 원본 파일 복사 ─────────────────────────────────
    stored_path = _copy_to_uploads(path, advertiser_name)
    file_hash   = _calc_file_hash(path)

    # ── 9. upload_files 이력 저장 ─────────────────────────
    upload_id = upload_repository.create_upload(
        conn,
        advertiser_id=advertiser_id,
        original_file_name=path.name,
        stored_file_path=str(stored_path),
        report_start_date=report_start,
        report_end_date=report_end,
        upload_type="single",
        file_hash=file_hash,
        row_count=len(df),
        status="success",
    )

    # ── 10. daily_performance 저장 ────────────────────────
    performance_repository.insert_performance_rows(conn, advertiser_id, upload_id, df)

    # ── 11. daily_summary 재계산 ──────────────────────────
    for d in dates:
        daily_summary_service.recalculate(conn, advertiser_id, d)

    logger.info(
        f"업로드 완료: {path.name} | 광고주={advertiser_name} | "
        f"날짜={dates} | {len(df)}행"
    )

    return {
        "success": True,
        "advertiser_id": advertiser_id,
        "advertiser_name": advertiser_name,
        "upload_id": upload_id,
        "row_count": len(df),
        "dates": dates,
        "skipped_dates": skipped_dates,
        "error": None,
    }
