"""
지표 계산
PROJECT_RULES.txt 섹션 13 기준

내부 저장:
  CTR / CVR → 0.0244 같은 float
  ROAS      → 10.02 같은 배수 float
  CPC / CPA → 원화 float

표시 시:
  CTR / CVR → 2.44%
  ROAS      → 1002%
  비용/매출/CPC/CPA → 원화 표시  (표시는 formatter 또는 UI에서 처리)
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def _safe_div(numerator: float, denominator: float) -> float:
    """분모가 0이면 0 반환."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def calculate_metrics(row: dict) -> dict:
    """
    단일 행(dict)의 지표를 계산해 반환.
    입력 키: impressions, clicks, cost,
             total_conversions, total_revenue,
             purchase_conversions, purchase_revenue
    """
    impressions          = float(row.get("impressions", 0) or 0)
    clicks               = float(row.get("clicks", 0) or 0)
    cost                 = float(row.get("cost", 0) or 0)
    total_conversions    = float(row.get("total_conversions", 0) or 0)
    total_revenue        = float(row.get("total_revenue", 0) or 0)
    purchase_conversions = float(row.get("purchase_conversions", 0) or 0)
    purchase_revenue     = float(row.get("purchase_revenue", 0) or 0)

    return {
        "ctr":           _safe_div(clicks, impressions),
        "cpc":           _safe_div(cost, clicks),
        "total_cvr":     _safe_div(total_conversions, clicks),
        "purchase_cvr":  _safe_div(purchase_conversions, clicks),
        "total_cpa":     _safe_div(cost, total_conversions),
        "purchase_cpa":  _safe_div(cost, purchase_conversions),
        "total_roas":    _safe_div(total_revenue, cost),
        "purchase_roas": _safe_div(purchase_revenue, cost),
    }


def add_metrics_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 전체에 지표 컬럼을 추가해 반환.
    없는 컬럼은 0으로 처리.
    """
    df = df.copy()

    for col in ["impressions", "clicks", "cost",
                "total_conversions", "total_revenue",
                "purchase_conversions", "purchase_revenue"]:
        if col not in df.columns:
            df[col] = 0.0

    metrics = df.apply(lambda row: pd.Series(calculate_metrics(row.to_dict())), axis=1)
    df = pd.concat([df, metrics], axis=1)

    logger.info("지표 컬럼 추가 완료: ctr, cpc, total_cvr, purchase_cvr, "
                "total_cpa, purchase_cpa, total_roas, purchase_roas")
    return df


def aggregate_metrics(df: pd.DataFrame) -> dict:
    """
    DataFrame 전체를 합산한 뒤 지표를 재계산해 반환.
    (일간 요약용 – daily_summary 계산 시 사용)
    """
    totals = {
        "impressions":          df["impressions"].sum() if "impressions" in df.columns else 0,
        "clicks":               df["clicks"].sum() if "clicks" in df.columns else 0,
        "cost":                 df["cost"].sum() if "cost" in df.columns else 0,
        "total_conversions":    df["total_conversions"].sum() if "total_conversions" in df.columns else 0,
        "total_revenue":        df["total_revenue"].sum() if "total_revenue" in df.columns else 0,
        "purchase_conversions": df["purchase_conversions"].sum() if "purchase_conversions" in df.columns else 0,
        "purchase_revenue":     df["purchase_revenue"].sum() if "purchase_revenue" in df.columns else 0,
    }
    totals.update(calculate_metrics(totals))
    return totals
