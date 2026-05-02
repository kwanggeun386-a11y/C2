"""
기본 분석 action_list 생성
PROJECT_RULES.txt 섹션 14 기준
"""
import logging

import pandas as pd

from app.config import (
    HIGH_COST_NO_CONVERSION_COST,
    CLICK_WASTE_CLICKS,
    HIGH_EFFICIENCY_ROAS,
    HIGH_EFFICIENCY_PURCHASE_CONVERSIONS,
    LOW_CTR_IMPRESSIONS,
    LOW_CTR_THRESHOLD,
    HIGH_CPC_THRESHOLD,
)

logger = logging.getLogger(__name__)

# action_list 유형 정의
ACTION_TYPES = {
    "고비용_무전환": {
        "label": "고비용 무전환",
        "judgment": "위험",
        "action": "비용은 발생했지만 구매완료 전환이 없어 제외, 입찰 조정 또는 검색 의도 점검 필요",
    },
    "클릭_낭비": {
        "label": "클릭 낭비",
        "judgment": "점검",
        "action": "클릭은 충분히 발생했지만 구매완료 전환이 없어 검색어 적합성, 랜딩페이지, 상품 경쟁력 점검 필요",
    },
    "고효율_검색어": {
        "label": "고효율 검색어",
        "judgment": "우수",
        "action": "구매 성과가 우수하므로 노출 유지, 예산 확대, 관련 키워드 확장 검토",
    },
    "저CTR": {
        "label": "저CTR",
        "judgment": "CTR 낮음",
        "action": "노출 대비 클릭률이 낮아 광고문안, 상품명, 검색어 적합성 점검 필요",
    },
    "고CPC": {
        "label": "고CPC",
        "judgment": "CPC 높음",
        "action": "클릭당 비용이 높아 입찰가, 경쟁 키워드 여부, 전환 효율 점검 필요",
    },
}


def _get_label_col(df: pd.DataFrame) -> str:
    """행을 식별할 대표 컬럼 선택 (search_term > keyword > ad_group > campaign > 인덱스)."""
    for col in ["search_term", "keyword", "ad_group", "campaign"]:
        if col in df.columns:
            return col
    return None


def build_action_list(df: pd.DataFrame) -> list[dict]:
    """
    지표가 계산된 DataFrame을 받아 action_list를 반환.

    필요 컬럼: metrics.add_metrics_columns() 결과 DataFrame
    반환: [
        {
            "action_type": str,
            "label": str,
            "judgment": str,
            "action": str,
            "term": str,       # 식별 값 (검색어 / 키워드 / 광고그룹 등)
            "impressions": float,
            "clicks": float,
            "cost": float,
            "purchase_conversions": float,
            "purchase_revenue": float,
            "ctr": float,
            "cpc": float,
            "purchase_roas": float,
        },
        ...
    ]
    """
    action_list: list[dict] = []
    label_col = _get_label_col(df)

    has_purchase = "purchase_conversions" in df.columns
    has_total    = "total_conversions" in df.columns

    for _, row in df.iterrows():
        term = str(row[label_col]) if label_col else f"행{_}"

        impressions          = float(row.get("impressions", 0) or 0)
        clicks               = float(row.get("clicks", 0) or 0)
        cost                 = float(row.get("cost", 0) or 0)
        purchase_conversions = float(row.get("purchase_conversions", 0) or 0) if has_purchase else 0.0
        total_conversions    = float(row.get("total_conversions", 0) or 0) if has_total else 0.0
        purchase_revenue     = float(row.get("purchase_revenue", 0) or 0)
        ctr                  = float(row.get("ctr", 0) or 0)
        cpc                  = float(row.get("cpc", 0) or 0)
        purchase_roas        = float(row.get("purchase_roas", 0) or 0)

        # 전환 기준: purchase_conversions 우선, 없으면 total_conversions
        conv_val = purchase_conversions if has_purchase else total_conversions

        def _base(action_type: str) -> dict:
            info = ACTION_TYPES[action_type]
            return {
                "action_type":          action_type,
                "label":                info["label"],
                "judgment":             info["judgment"],
                "action":               info["action"],
                "term":                 term,
                "impressions":          impressions,
                "clicks":               clicks,
                "cost":                 cost,
                "purchase_conversions": purchase_conversions,
                "purchase_revenue":     purchase_revenue,
                "ctr":                  ctr,
                "cpc":                  cpc,
                "purchase_roas":        purchase_roas,
            }

        # 1. 고비용 무전환
        if cost >= HIGH_COST_NO_CONVERSION_COST and conv_val == 0:
            action_list.append(_base("고비용_무전환"))

        # 2. 클릭 낭비
        if clicks >= CLICK_WASTE_CLICKS and conv_val == 0:
            action_list.append(_base("클릭_낭비"))

        # 3. 고효율 검색어
        if (purchase_roas >= HIGH_EFFICIENCY_ROAS
                and purchase_conversions >= HIGH_EFFICIENCY_PURCHASE_CONVERSIONS):
            action_list.append(_base("고효율_검색어"))

        # 4. 저CTR
        if impressions >= LOW_CTR_IMPRESSIONS and ctr < LOW_CTR_THRESHOLD:
            action_list.append(_base("저CTR"))

        # 5. 고CPC
        if cpc >= HIGH_CPC_THRESHOLD and clicks >= 5:
            action_list.append(_base("고CPC"))

    logger.info(f"action_list 생성 완료: {len(action_list)}개 항목")
    return action_list


def print_action_list(action_list: list[dict]) -> None:
    """action_list를 터미널에 출력."""
    if not action_list:
        print("  action_list: 해당 항목 없음")
        return

    for i, item in enumerate(action_list, 1):
        print(f"\n  [{i}] {item['label']} ({item['judgment']})")
        print(f"      대상: {item['term']}")
        print(f"      비용: {item['cost']:,.0f}원  클릭: {item['clicks']:.0f}  "
              f"CTR: {item['ctr']*100:.2f}%  CPC: {item['cpc']:,.0f}원")
        print(f"      구매전환: {item['purchase_conversions']:.0f}  "
              f"구매매출: {item['purchase_revenue']:,.0f}원  "
              f"ROAS: {item['purchase_roas']*100:.0f}%")
        print(f"      → {item['action']}")
