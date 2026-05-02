"""
네이버 광고 리포트 분석기 – 메인 진입점
PROJECT_RULES.txt 섹션 26 기준

실행 방법:
  python app/main.py                                  # GUI 모드 (Step 15 이후)
  python app/main.py --init-db                        # DB 초기화
  python app/main.py --test-file <파일경로>            # 파일 로드 테스트
  python app/main.py --test-analyze <파일경로>         # 지표 계산 + action_list 테스트
  python app/main.py --input <파일> --advertiser-name <광고주명> [--date YYYY-MM-DD] [--overwrite]
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


def _load_and_standardize(file_path: str):
    """공통: 파일 로드 → 컬럼 매핑 → 검증 → 숫자 정리."""
    from app.core.file_loader import load_file
    from app.core.column_mapper import map_columns
    from app.core.validator import validate_columns
    from app.core.formatter import format_numeric_columns

    path = Path(file_path)
    result = load_file(path)
    if not result["success"]:
        print(f"[실패] 파일 로드 오류: {result['error']}")
        sys.exit(1)

    df = result["df"]
    df = map_columns(df)["df"]

    validation = validate_columns(df)
    if not validation["valid"]:
        print(f"[중단] 필수 컬럼 누락: {validation['missing_required']}")
        sys.exit(1)

    warnings: list[str] = []
    df = format_numeric_columns(df, warnings=warnings)
    return df, validation


def cmd_test_file(file_path: str) -> None:
    """--test-file: 파일 로드 → 컬럼 매핑 → 검증 → 숫자 정리 결과 출력."""
    from app.core.file_loader import load_file
    from app.core.column_mapper import map_columns
    from app.core.validator import validate_columns
    from app.core.formatter import format_numeric_columns

    path = Path(file_path)
    print(f"\n{'='*60}")
    print(f"[테스트] 파일: {path.name}")
    print(f"{'='*60}")

    result = load_file(path)
    if not result["success"]:
        print(f"[실패] {result['error']}")
        sys.exit(1)

    df = result["df"]
    print(f"\n[1] 파일 로드 완료")
    print(f"    행 수: {len(df)}, 컬럼 수: {len(df.columns)}")
    print(f"    원본 컬럼: {list(df.columns)}")

    mapped = map_columns(df)
    df = mapped["df"]
    print(f"\n[2] 컬럼 매핑 완료")
    print(f"    매핑: {mapped['mapped']}")
    if mapped["unmapped"]:
        print(f"    미매핑: {mapped['unmapped']}")
    print(f"    표준화된 컬럼: {list(df.columns)}")

    validation = validate_columns(df)
    print(f"\n[3] 컬럼 검증")
    print(f"    분석 가능: {validation['valid']}")
    for w in validation["warnings"]:
        print(f"    ⚠ {w}")
    if validation["skip_analysis"]:
        print(f"    건너뜀: {validation['skip_analysis']}")
    if not validation["valid"]:
        sys.exit(1)

    fmt_warnings: list[str] = []
    df = format_numeric_columns(df, warnings=fmt_warnings)
    print(f"\n[4] 숫자 정리 완료")
    for w in fmt_warnings:
        print(f"    ⚠ {w}")

    numeric_cols = [c for c in ["impressions", "clicks", "cost",
                                 "purchase_conversions", "purchase_revenue"] if c in df.columns]
    preview_cols = (["date"] if "date" in df.columns else []) + numeric_cols
    print(f"\n[5] 데이터 미리보기 (상위 5행)")
    print(df[preview_cols].head(5).to_string(index=False))

    print(f"\n{'='*60}")
    print(f"[완료] 표준화 성공. 총 {len(df)}행 처리.")
    print(f"{'='*60}\n")


def cmd_test_analyze(file_path: str) -> None:
    """--test-analyze: 지표 계산 + action_list 분석 결과 출력."""
    from app.core.metrics import add_metrics_columns, aggregate_metrics
    from app.core.analyzer import build_action_list, print_action_list

    path = Path(file_path)
    print(f"\n{'='*60}")
    print(f"[분석] 파일: {path.name}")
    print(f"{'='*60}")

    df, validation = _load_and_standardize(file_path)
    df = add_metrics_columns(df)
    print(f"\n[1] 지표 계산 완료")

    summary = aggregate_metrics(df)
    print(f"\n[2] 전체 요약")
    print(f"    노출수:   {summary['impressions']:,.0f}")
    print(f"    클릭수:   {summary['clicks']:,.0f}")
    print(f"    총비용:   {summary['cost']:,.0f}원")
    print(f"    CTR:      {summary['ctr']*100:.2f}%")
    print(f"    CPC:      {summary['cpc']:,.0f}원")
    print(f"    구매전환: {summary['purchase_conversions']:,.0f}")
    print(f"    구매매출: {summary['purchase_revenue']:,.0f}원")
    print(f"    구매CVR:  {summary['purchase_cvr']*100:.2f}%")
    print(f"    구매CPA:  {summary['purchase_cpa']:,.0f}원")
    print(f"    구매ROAS: {summary['purchase_roas']*100:.0f}%")

    metric_cols = [c for c in ["date", "search_term", "keyword", "campaign",
                                "impressions", "clicks", "cost",
                                "ctr", "cpc", "purchase_roas"] if c in df.columns]
    print(f"\n[3] 행별 지표 미리보기 (상위 5행)")
    preview = df[metric_cols].head(5).copy()
    if "ctr" in preview.columns:
        preview["ctr"] = preview["ctr"].apply(lambda x: f"{x*100:.2f}%")
    if "cpc" in preview.columns:
        preview["cpc"] = preview["cpc"].apply(lambda x: f"{x:,.0f}원")
    if "purchase_roas" in preview.columns:
        preview["purchase_roas"] = preview["purchase_roas"].apply(lambda x: f"{x*100:.0f}%")
    print(preview.to_string(index=False))

    action_list = build_action_list(df)
    print(f"\n[4] action_list ({len(action_list)}개)")
    print_action_list(action_list)

    print(f"\n{'='*60}")
    print(f"[완료] 분석 완료. 총 {len(df)}행 처리.")
    print(f"{'='*60}\n")


def cmd_upload(
    file_path: str,
    advertiser_name: str,
    selected_date: str | None,
    overwrite: bool,
) -> None:
    """--input: 단일 파일 CLI 업로드."""
    from app.services.upload_service import upload_file

    ensure_app_data_dirs()
    conn = init_db(DB_PATH)

    try:
        result = upload_file(
            conn,
            advertiser_name=advertiser_name,
            file_path=file_path,
            selected_date=selected_date,
            overwrite=overwrite,
        )

        if result["success"]:
            print(f"\n[완료] 업로드 성공")
            print(f"  광고주: {result['advertiser_name']} (id={result['advertiser_id']})")
            print(f"  upload_id: {result['upload_id']}")
            print(f"  저장 행수: {result['row_count']}")
            print(f"  날짜: {result['dates']}")
            if result.get("skipped_dates"):
                print(f"  건너뜀(중복): {result['skipped_dates']}")
        else:
            print(f"\n[실패] {result.get('error')}")
            if result.get("skipped_dates"):
                print(f"  건너뜀(중복): {result['skipped_dates']}")
    finally:
        close_connection(conn)



def cmd_compare(advertiser_id: int, selected_date: str) -> None:
    """--compare: 전일 대비 비교 결과 출력."""
    from app.services.comparison_service import compare, COMPARE_METRICS

    ensure_app_data_dirs()
    conn = init_db(DB_PATH)

    METRIC_LABELS = {
        "impressions":          "노출수",
        "clicks":               "클릭수",
        "cost":                 "총비용(원)",
        "ctr":                  "CTR",
        "cpc":                  "CPC(원)",
        "purchase_conversions": "구매전환",
        "purchase_revenue":     "구매매출(원)",
        "purchase_cpa":         "구매CPA(원)",
        "purchase_roas":        "구매ROAS",
    }
    PCT_METRICS  = {"ctr", "purchase_roas"}
    RATE_METRICS = {"ctr", "cpc", "purchase_cpa", "purchase_roas"}

    try:
        result = compare(conn, advertiser_id, selected_date)

        print(f"\n{'='*65}")
        print(f"[전일 비교] 광고주 id={advertiser_id} | {result['yesterday_date']} → {result['selected_date']}")
        print(f"{'='*65}")

        if not result["success"]:
            print(f"\n[실패] {result['message']}\n")
            return

        if not result["has_yesterday"]:
            print(f"\n⚠  {result['message']}\n")
            today = result["today"]
            print(f"  오늘({result['selected_date']}) 데이터만 표시합니다.")
            for m in COMPARE_METRICS:
                val = float(today.get(m, 0) or 0)
                label = METRIC_LABELS.get(m, m)
                if m in PCT_METRICS:
                    print(f"  {label:<18} {val*100:>10.2f}%")
                else:
                    print(f"  {label:<18} {val:>12,.0f}")
            print()
            return

        # 비교 테이블 출력
        print(f"  {'지표':<18} {'전일':>12} {'오늘':>12} {'증감':>12} {'증감률':>10}")
        print(f"  {'-'*66}")

        for m in COMPARE_METRICS:
            c      = result["comparison"][m]
            label  = METRIC_LABELS.get(m, m)
            is_pct = m in PCT_METRICS

            if is_pct:
                t_str  = f"{c['today']*100:.2f}%"
                y_str  = f"{c['yesterday']*100:.2f}%"
                d_str  = f"{c['diff']*100:+.2f}%"
            else:
                t_str  = f"{c['today']:,.0f}"
                y_str  = f"{c['yesterday']:,.0f}"
                d_str  = f"{c['diff']:+,.0f}"

            if c["change_rate"] is None:
                r_str = "-"
            else:
                r_str = f"{c['change_rate']*100:+.1f}%"

            print(f"  {label:<18} {y_str:>12} {t_str:>12} {d_str:>12} {r_str:>10}")

        print(f"{'='*65}\n")
    finally:
        close_connection(conn)

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
    parser.add_argument("--test-analyze", metavar="FILE", help="지표 계산 + action_list 테스트")
    parser.add_argument("--input", metavar="FILE", help="업로드할 파일 경로")
    parser.add_argument("--advertiser-name", metavar="NAME", help="광고주명 (--input 필수)")
    parser.add_argument("--date", metavar="DATE", help="기준일 YYYY-MM-DD (date 컬럼 없을 때)")
    parser.add_argument("--overwrite", action="store_true", help="기존 데이터 덮어쓰기")
    parser.add_argument("--compare", action="store_true", help="전일 대비 비교")
    parser.add_argument("--advertiser-id", metavar="ID", type=int, help="광고주 ID (--compare 사용 시)")
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

    if args.test_analyze:
        cmd_test_analyze(args.test_analyze)
        sys.exit(0)

    if args.compare:
        if not args.advertiser_id or not args.date:
            print("[오류] --compare 사용 시 --advertiser-id 와 --date 를 함께 지정해야 합니다.")
            sys.exit(1)
        cmd_compare(args.advertiser_id, args.date)
        sys.exit(0)

    if args.input:
        if not args.advertiser_name:
            print("[오류] --input 사용 시 --advertiser-name 을 함께 지정해야 합니다.")
            sys.exit(1)
        cmd_upload(
            file_path=args.input,
            advertiser_name=args.advertiser_name,
            selected_date=args.date,
            overwrite=args.overwrite,
        )
        sys.exit(0)

    run_gui()


if __name__ == "__main__":
    main()
