"""
네이버 광고센터 한글 컬럼 → 내부 표준 컬럼 매핑
PROJECT_RULES.txt 섹션 10 기준
"""
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# 표준 컬럼명 : 허용 alias 목록
COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["일별", "날짜", "일자", "보고일"],
    "campaign_type": ["캠페인유형", "캠페인 유형", "광고유형", "광고 유형"],
    "campaign": ["캠페인", "캠페인명", "캠페인 이름"],
    "ad_group": ["광고그룹", "광고그룹명", "광고 그룹", "광고 그룹명"],
    "media": ["매체이름", "매체", "게재지면", "노출매체"],
    "search_term": ["검색어", "검색어명", "검색 질의", "실제 검색어"],
    "keyword": ["키워드", "키워드명", "등록키워드", "등록 키워드"],
    "impressions": ["노출수", "노출", "총노출수"],
    "clicks": ["클릭수", "클릭", "총클릭수"],
    "cost": ["총비용", "비용", "광고비", "총 비용", "총 광고비"],
    "total_conversions": ["총 전환수", "전환수", "전체 전환수"],
    "total_revenue": ["총 전환매출액(원)", "총 전환매출액", "전환매출액", "전체 전환매출액"],
    "purchase_conversions": ["구매완료 전환수", "구매 전환수", "구매완료수", "구매수"],
    "purchase_revenue": [
        "구매완료 전환매출액(원)",
        "구매완료 전환매출액",
        "구매완료 매출액",
        "구매 전환매출액",
        "구매매출",
    ],
}

# alias → 표준 컬럼명 역방향 맵 (빠른 조회용)
_ALIAS_TO_STANDARD: dict[str, str] = {}
for _std, _aliases in COLUMN_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_STANDARD[_alias.strip()] = _std


def map_columns(df: pd.DataFrame) -> dict:
    """
    DataFrame의 컬럼명을 표준 컬럼명으로 변환.

    반환:
        {
            "df": pd.DataFrame,          # 표준 컬럼명으로 rename된 DataFrame
            "mapped": dict,              # {원본컬럼: 표준컬럼}
            "unmapped": list[str],       # 매핑되지 않은 컬럼
        }
    """
    df = df.copy()
    rename_map: dict[str, str] = {}
    unmapped: list[str] = []

    for col in df.columns:
        col_stripped = str(col).strip()
        if col_stripped in _ALIAS_TO_STANDARD:
            standard = _ALIAS_TO_STANDARD[col_stripped]
            rename_map[col] = standard
        else:
            unmapped.append(col)

    df = df.rename(columns=rename_map)

    logger.info(f"컬럼 매핑: {len(rename_map)}개 성공, {len(unmapped)}개 미매핑")
    if unmapped:
        logger.debug(f"미매핑 컬럼: {unmapped}")

    return {"df": df, "mapped": rename_map, "unmapped": unmapped}


def get_standard_columns() -> list[str]:
    """표준 컬럼명 목록 반환."""
    return list(COLUMN_ALIASES.keys())
