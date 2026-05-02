"""
네이버 광고 리포트 분석기 – 메인 진입점
PROJECT_RULES.txt 섹션 26 기준

실행 방법:
  python app/main.py                                # GUI 모드 (Step 15 이후)
  python app/main.py --init-db                      # DB 초기화
  python app/main.py --test-file <파일경로>          # 파일 로드 CLI 테스트
"""
import sys
import argparse
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import (
    APP_DATA_DIR, DB_DIR, DB_PATH,
    UPLOADS_DIR, EXPORTS_DIR,
    UNCLASSIFIED_UPLOADS_DIR, UNCLASSIFIED_EXPORTS_DIR,
)
from app.db.database import init_db, close_connection


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def ensure_app_data_dirs() -> None:
    dirs = [
        APP_DATA_DIR, DB_DIR, UPLOADS_DIR, EXPORTS_DIR,
        UNCLASSIFIED_UPLOADS_DIR, UNCLASSIFIED_EXPORTS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logging.getLogger(__name__).info("app_data 폴더 준비 완료")


def cmd_init_db() -> None:
    logger = logging.getLogger(__name__)
    ensure_app_data_dirs()
    conn = init_db(DB_PATH)
    close_connection(conn)
    logger.info("--init-db 완료")


def cmd_test_file(file_path: str) -> None:
    """--test-file: 파일 로드 → 컬럼 매핑 → 검증 → 숫자 정리 결과 출력"""
    from app.core.file_loader import load_file
    from app.core.column_mapper import map_columns
    from app.core.validator import validate_columns
    from app.core.formatter import format_numeric_columns

    logger = logging.getLogger(__name__)
    path = Path(file_path)

    print(f"\n{'='*60}")
    print(f"[테스트] 파일: {path.name}")
    print(f"{'='*60}")

    # 1. 파일 로드
    result = load_file(path)
    if not result["success"]:
        print(f"[실패] 파일 로드 오류: {result['error']}")
        sys.exit(1)

    df = result["df"]
    print(f"\n[1] 파일 로드 완료")
    print(f"    행 수: {len(df)}, 컬럼 수: {len(df.columns)}")
    print(f"    원본 컬럼: {list(df.columns)}")

    # 2. 컬럼 매핑
    mapped = map_columns(df)
    df = mapped["df"]
    print(f"\n[2] 컬럼 매핑 완료")
    print(f"    매핑: {mapped['mapped']}")
    if mapped["unmapped"]:
        print(f"    미매핑: {mapped['unmapped']}")
    print(f"    표준화된 컬럼: {list(df.columns)}")

    # 3. 컬럼 검증
    validation = validate_columns(df)
    print(f"\n[3] 컬럼 검증")
    print(f"    분석 가능: {validation['valid']}")
    if validation["warnings"]:
        for w in validation["warnings"]:
            print(f"    ⚠ {w}")
    if validation["skip_analysis"]:
        print(f"    건너뜀: {validation['skip_analysis']}")

    if not validation["valid"]:
        print(f"\n[중단] 필수 컬럼 누락으로 분석 불가.")
        sys.exit(1)

    # 4. 숫자 정리
    fmt_warnings: list[str] = []
    df = format_numeric_columns(df, warnings=fmt_warnings)
    print(f"\n[4] 숫자 정리 완료")
    if fmt_warnings:
        for w in fmt_warnings:
            print(f"    ⚠ {w}")

    # 5. 결과 미리보기
    numeric_cols = [c for c in ["impressions", "clicks", "cost",
                                 "purchase_conversions", "purchase_revenue"] if c in df.columns]
    print(f"\n[5] 데이터 미리보기 (상위 5행, 주요 컬럼)")
    preview_cols = (["date"] if "date" in df.columns else []) + numeric_cols
    print(df[preview_cols].head(5).to_string(index=False))

    print(f"\n{'='*60}")
    print(f"[완료] 표준화 성공. 총 {len(df)}행 처리.")
    print(f"{'='*60}\n")


def run_gui() -> None:
    logger = logging.getLogger(__name__)
    ensure_app_data_dirs()
    logger.info("GUI 모드는 Step 15(pywebview 연결)에서 구현 예정입니다.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="네이버 광고 리포트 분석기",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--init-db", action="store_true", help="DB 초기화")
    parser.add_argument("--test-file", metavar="FILE", help="파일 로드 CLI 테스트")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("앱 시작")

    args = parse_args()

    if args.init_db:
        cmd_init_db()
        logger.info("종료")
        sys.exit(0)

    if args.test_file:
        cmd_test_file(args.test_file)
        sys.exit(0)

    run_gui()


if __name__ == "__main__":
    main()
