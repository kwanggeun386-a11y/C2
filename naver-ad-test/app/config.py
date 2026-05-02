"""
앱 전역 설정 및 경로 정의
PROJECT_RULES.txt 섹션 5, 6, 14 기준
"""
from pathlib import Path

# ── 프로젝트 루트 ──────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── app_data 경로 ──────────────────────────────
APP_DATA_DIR = BASE_DIR / "app_data"
DB_DIR = APP_DATA_DIR / "database"
UPLOADS_DIR = APP_DATA_DIR / "uploads"
EXPORTS_DIR = APP_DATA_DIR / "exports"
UNCLASSIFIED_UPLOADS_DIR = UPLOADS_DIR / "_unclassified"
UNCLASSIFIED_EXPORTS_DIR = EXPORTS_DIR / "_unclassified"

# ── DB 파일 경로 ───────────────────────────────
DB_PATH = DB_DIR / "naver_ad_reports.db"

# ── action_list 기준값 (섹션 14) ───────────────
HIGH_COST_NO_CONVERSION_COST = 30000       # 고비용 무전환 기준 비용 (원)
CLICK_WASTE_CLICKS = 20                    # 클릭 낭비 기준 클릭수
HIGH_EFFICIENCY_ROAS = 5.0                 # 고효율 ROAS 기준
HIGH_EFFICIENCY_PURCHASE_CONVERSIONS = 3   # 고효율 구매완료 전환수 기준
LOW_CTR_IMPRESSIONS = 1000                 # 저CTR 기준 노출수
LOW_CTR_THRESHOLD = 0.005                  # 저CTR 기준 CTR
HIGH_CPC_THRESHOLD = 1000                  # 고CPC 기준 클릭당 비용 (원)
