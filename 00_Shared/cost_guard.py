#!/usr/bin/env python3
"""
COST-GUARD Band Utility
단일 정책 기반 밴드 판정 유틸리티

Version: 1.0.0
Created: 2025-10-15
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

from typing import Optional, Dict


def get_cost_guard_band(delta_pct: Optional[float], bands: Dict[str, float]) -> str:
    """
    COST-GUARD 밴드 판정 (Configuration 기반)

    Args:
        delta_pct: Delta percentage (절대값 또는 원시값)
        bands: Configuration bands dictionary
               예: {"pass": 3, "warn": 5, "high": 10, "autofail": 15}

    Returns:
        str: "PASS" | "WARN" | "HIGH" | "CRITICAL" | "N/A"

    Examples:
        >>> bands = {"pass": 3, "warn": 5, "high": 10, "autofail": 15}
        >>> get_cost_guard_band(1.5, bands)
        'PASS'
        >>> get_cost_guard_band(7.2, bands)
        'HIGH'
        >>> get_cost_guard_band(16.0, bands)
        'CRITICAL'
    """
    if delta_pct is None:
        return "N/A"

    # 절대값으로 변환
    d = abs(delta_pct)

    # 밴드 판정 (pass < warn < high < autofail)
    if d <= bands.get("pass", 3):
        return "PASS"
    elif d <= bands.get("warn", 5):
        return "WARN"
    elif d <= bands.get("high", 10):
        return "HIGH"
    else:
        return "CRITICAL"


def should_auto_fail(delta_pct: Optional[float], bands: Dict[str, float]) -> bool:
    """
    Auto-Fail 여부 판정

    Args:
        delta_pct: Delta percentage
        bands: Configuration bands dictionary

    Returns:
        bool: True if delta exceeds autofail threshold
    """
    if delta_pct is None:
        return False

    autofail_threshold = bands.get("autofail", 15)
    return abs(delta_pct) > autofail_threshold


def get_band_description(band: str) -> str:
    """
    밴드 설명 반환

    Args:
        band: Band name ("PASS" | "WARN" | "HIGH" | "CRITICAL" | "N/A")

    Returns:
        str: Band description
    """
    descriptions = {
        "PASS": "Within acceptable tolerance",
        "WARN": "Minor variance - review recommended",
        "HIGH": "Significant variance - attention required",
        "CRITICAL": "Critical variance - immediate action required",
        "N/A": "Not applicable or insufficient data",
    }
    return descriptions.get(band, "Unknown band")
