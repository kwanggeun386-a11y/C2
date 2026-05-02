"""
숫자 컬럼 정리 (쉼표, 원, %, 공백 제거 후 numeric 변환)
PROJECT_RULES.txt 섹션 12 기준
"""
import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# 숫자 정리 대상 컬럼
NUMERIC_COLUMNS = [
    "impressions",
    "clicks",
    "cost",
    "total_conversions",
    "total_revenue",
    "purchase_conversions",
    "purchase_revenue",
]

# 제거할 문자 패턴: 쉼표, 원, %, 공백
_STRIP_PATTERN = re.compile(r"[,원%\s]")


def _clean_value(val) -> float:
    """단일 값을 float으로 변환. 변환 불가 시 0 반환."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 0.0
    s = str(val).strip()
    if s in ("", "-", "nan", "NaN", "None"):
        return 0.0
    s = _STRIP_PATTERN.sub("", s)
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def format_numeric_columns(df: pd.DataFrame, warnings: list[str] | None = None) -> pd.DataFrame:
    """
    NUMERIC_COLUMNS 중 DataFrame에 존재하는 컬럼을 숫자로 변환.
    - 빈 값, '-', NaN → 0
    - 쉼표, 원, %, 공백 제거
    - 변환 실패 → 0
    - 음수 → 허용, warnings에 기록
    """
    if warnings is None:
        warnings = []

    df = df.copy()

    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue

        df[col] = df[col].apply(_clean_value)

        # 음수 경고
        neg_count = int((df[col] < 0).sum())
        if neg_count > 0:
            msg = f"{col}: 음수 값 {neg_count}개 발견 (허용, 점검 권장)"
            warnings.append(msg)
            logger.warning(msg)

        logger.debug(f"{col}: 숫자 변환 완료")

    logger.info(f"숫자 컬럼 정리 완료: {[c for c in NUMERIC_COLUMNS if c in df.columns]}")
    return df
