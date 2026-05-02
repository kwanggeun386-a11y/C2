"""
네이버 광고 리포트 분석기 – 메인 진입점
PROJECT_RULES.txt 섹션 26 기준

실행 방법:
  python app/main.py             # GUI 모드 (Step 15 이후 사용 가능)
  python app/main.py --init-db   # DB 초기화
"""
import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (직접 실행 시)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import (
    APP_DATA_DIR,
    DB_DIR,
    DB_PATH,
    UPLOADS_DIR,
    EXPORTS_DIR,
    UNCLASSIFIED_UPLOADS_DIR,
    UNCLASSIFIED_EXPORTS_DIR,
)
from app.db.database import init_db, close_connection


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def ensure_app_data_dirs() -> None:
    """app_data 폴더 구조 자동 생성 (없으면 생성, 있으면 무시)"""
    logger = logging.getLogger(__name__)
    dirs = [
        APP_DATA_DIR,
        DB_DIR,
        UPLOADS_DIR,
        EXPORTS_DIR,
        UNCLASSIFIED_UPLOADS_DIR,
        UNCLASSIFIED_EXPORTS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("app_data 폴더 준비 완료")


def cmd_init_db() -> None:
    """--init-db: app_data 폴더 생성 + SQLite DB 초기화"""
    logger = logging.getLogger(__name__)
    ensure_app_data_dirs()
    conn = init_db(DB_PATH)
    close_connection(conn)
    logger.info("--init-db 완료")


def run_gui() -> None:
    """GUI 모드 – pywebview는 Step 15에서 구현"""
    logger = logging.getLogger(__name__)
    ensure_app_data_dirs()
    logger.info("GUI 모드는 Step 15(pywebview 연결)에서 구현 예정입니다.")
    # TODO: Step 15에서 pywebview import 및 창 생성


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="네이버 광고 리포트 분석기",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="app_data 폴더 및 SQLite DB를 초기화합니다.",
    )
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

    # 인자 없으면 GUI 모드
    run_gui()


if __name__ == "__main__":
    main()
