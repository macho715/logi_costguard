#!/usr/bin/env python3
"""
Portal Fee Utility
Portal Fee 공용 로직 유틸리티

Version: 1.0.0
Created: 2025-10-15
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import re
from typing import Optional, Dict


# Portal Fee 고정값 (AED)
FIXED_PORTAL_FEES = {
    "APPOINTMENT": 27.0,
    "DPC": 35.0,
    "DOCUMENT PROCESSING": 35.0,
    "DOCUMENTATION PROCESSING": 35.0,
    "DOC PROCESSING": 35.0,
}

# Portal Fee 특별 허용오차 (±0.5%)
PORTAL_FEE_TOLERANCE = 0.005  # 0.5%


def parse_aed_from_formula(formula_text: Optional[str]) -> Optional[float]:
    """
    수식에서 AED 금액 추출

    Args:
        formula_text: Formula string (예: "=27*3.6725" or "27 AED")

    Returns:
        float: AED amount or None

    Examples:
        >>> parse_aed_from_formula("=27*3.6725")
        27.0
        >>> parse_aed_from_formula("35 AED")
        35.0
    """
    if not formula_text:
        return None

    # 수식 패턴: =숫자*환율
    formula_match = re.search(r"=\s*(\d+(?:\.\d+)?)\s*\*", str(formula_text))
    if formula_match:
        return float(formula_match.group(1))

    # 직접 AED 표기: "27 AED", "35AED"
    aed_match = re.search(r"(\d+(?:\.\d+)?)\s*AED", str(formula_text), re.IGNORECASE)
    if aed_match:
        return float(aed_match.group(1))

    return None


def find_fixed_portal_fee(description: str) -> Optional[float]:
    """
    Description에서 고정 Portal Fee 매칭

    Args:
        description: Item description

    Returns:
        float: AED amount or None

    Examples:
        >>> find_fixed_portal_fee("APPOINTMENT FEE")
        27.0
        >>> find_fixed_portal_fee("DOCUMENT PROCESSING CHARGES")
        35.0
    """
    if not description:
        return None

    desc_upper = description.upper()

    # 고정값 딕셔너리에서 키워드 매칭
    for keyword, aed_amount in FIXED_PORTAL_FEES.items():
        if keyword in desc_upper:
            return aed_amount

    return None


def resolve_portal_fee_usd(
    description: str, fx_rate: float, formula_text: Optional[str] = None
) -> Optional[float]:
    """
    Portal Fee USD 요율 해결

    Args:
        description: Item description
        fx_rate: AED to USD exchange rate (예: 3.6725)
        formula_text: Formula string (optional)

    Returns:
        float: USD amount or None

    Priority:
        1. Formula에서 AED 추출 → USD 환산
        2. Description에서 고정값 매칭 → USD 환산

    Examples:
        >>> resolve_portal_fee_usd("APPOINTMENT", 3.6725, "=27*3.6725")
        7.35
        >>> resolve_portal_fee_usd("DOCUMENT PROCESSING", 3.6725)
        9.53
    """
    # 1. Formula에서 AED 추출 시도
    aed_amount = parse_aed_from_formula(formula_text)

    # 2. 실패 시 Description에서 고정값 매칭
    if aed_amount is None:
        aed_amount = find_fixed_portal_fee(description)

    # 3. USD 환산
    if aed_amount is not None and fx_rate > 0:
        return round(aed_amount / fx_rate, 2)

    return None


def is_within_portal_fee_tolerance(
    draft_rate: float, ref_rate: float, tolerance: float = PORTAL_FEE_TOLERANCE
) -> bool:
    """
    Portal Fee 특별 허용오차 검증 (±0.5%)

    Args:
        draft_rate: Draft invoice rate
        ref_rate: Reference rate
        tolerance: Tolerance percentage (default: 0.005 = 0.5%)

    Returns:
        bool: True if within tolerance

    Examples:
        >>> is_within_portal_fee_tolerance(7.35, 7.37)
        True
        >>> is_within_portal_fee_tolerance(7.35, 7.80)
        False
    """
    if ref_rate == 0:
        return draft_rate == 0

    delta_pct = abs((draft_rate - ref_rate) / ref_rate)
    return delta_pct <= tolerance


def get_portal_fee_band(draft_rate: float, ref_rate: float) -> str:
    """
    Portal Fee 밴드 판정 (특별 규칙)

    Args:
        draft_rate: Draft invoice rate
        ref_rate: Reference rate

    Returns:
        str: "PASS" | "WARN" | "FAIL"

    Rules:
        - ±0.5% 이내: PASS
        - 0.5% ~ 5%: WARN
        - >5%: FAIL
    """
    if ref_rate == 0:
        return "PASS" if draft_rate == 0 else "FAIL"

    delta_pct = abs((draft_rate - ref_rate) / ref_rate) * 100

    if delta_pct <= 0.5:
        return "PASS"
    elif delta_pct <= 5.0:
        return "WARN"
    else:
        return "FAIL"
