"""
필수/권장/선택 컬럼 검증
PROJECT_RULES.txt 섹션 11 기준
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# 필수 컬럼: 하나라도 없으면 분석 불가
REQUIRED_COLUMNS = ["impressions", "clicks", "cost"]

# 권장 컬럼: 없으면 경고
RECOMMENDED_COLUMNS = [
    "date",
    "campaign",
    "ad_group",
    "purchase_conversions",
    "purchase_revenue",
]

# 선택 컬럼: 없으면 해당 분석만 건너뜀
OPTIONAL_COLUMNS = [
    "campaign_type",
    "media",
    "total_conversions",
    "total_revenue",
    "keyword",
    "search_term",
]


def validate_columns(df: pd.DataFrame) -> dict:
    """
    표준 컬럼명으로 매핑된 DataFrame의 컬럼을 검증.

    반환:
        {
            "valid": bool,               # False면 분석 불가
            "missing_required": list,    # 누락된 필수 컬럼
            "missing_recommended": list, # 누락된 권장 컬럼
            "available_optional": list,  # 존재하는 선택 컬럼
            "skip_analysis": list,       # 건너뛸 분석 항목
            "warnings": list[str],       # 경고 메시지
        }
    """
    cols = set(df.columns)
    warnings: list[str] = []
    skip_analysis: list[str] = []

    # 필수 컬럼 검사
    missing_required = [c for c in REQUIRED_COLUMNS if c not in cols]
    if missing_required:
        msg = f"필수 컬럼 누락으로 분석 불가: {missing_required}"
        logger.error(msg)
        return {
            "valid": False,
            "missing_required": missing_required,
            "missing_recommended": [],
            "available_optional": [],
            "skip_analysis": ["전체"],
            "warnings": [msg],
        }

    # 권장 컬럼 검사
    missing_recommended = [c for c in RECOMMENDED_COLUMNS if c not in cols]
    for col in missing_recommended:
        if col == "date":
            msg = "date 컬럼 없음 → UI/CLI에서 선택한 기준일 사용"
            skip_analysis.append("날짜별 분석")
        elif col == "campaign":
            msg = "campaign 컬럼 없음 → 캠페인별 분석 건너뜀"
            skip_analysis.append("캠페인별 분석")
        elif col == "ad_group":
            msg = "ad_group 컬럼 없음 → 광고그룹별 분석 건너뜀"
            skip_analysis.append("광고그룹별 분석")
        elif col in ("purchase_conversions", "purchase_revenue"):
            msg = f"{col} 컬럼 없음 → 구매완료 기준 분석 건너뜀"
            skip_analysis.append("구매완료 분석")
        else:
            msg = f"권장 컬럼 없음: {col}"
        warnings.append(msg)
        logger.warning(msg)

    # search_term / keyword 둘 다 없으면
    if "search_term" not in cols and "keyword" not in cols:
        msg = "search_term, keyword 모두 없음 → 검색어/키워드 분석 건너뜀"
        warnings.append(msg)
        skip_analysis.append("검색어/키워드 분석")
        logger.warning(msg)

    # 전환 컬럼 모두 없으면
    conversion_cols = {"total_conversions", "total_revenue", "purchase_conversions", "purchase_revenue"}
    if not conversion_cols & cols:
        msg = "전환 관련 컬럼 모두 없음 → 전환 지표 계산 건너뜀"
        warnings.append(msg)
        skip_analysis.append("전환 지표")
        logger.warning(msg)

    # 존재하는 선택 컬럼
    available_optional = [c for c in OPTIONAL_COLUMNS if c in cols]

    # 중복 제거
    skip_analysis = list(dict.fromkeys(skip_analysis))

    logger.info(f"컬럼 검증 통과. 건너뜀: {skip_analysis if skip_analysis else '없음'}")

    return {
        "valid": True,
        "missing_required": [],
        "missing_recommended": missing_recommended,
        "available_optional": available_optional,
        "skip_analysis": skip_analysis,
        "warnings": warnings,
    }
