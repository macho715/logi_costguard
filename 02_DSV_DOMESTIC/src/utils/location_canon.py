# -*- coding: utf-8 -*-
# location_canon.py — structural
import re
from .utils_normalize import normalize_location

# 약어/변형 → 표준 지명 매핑 (필요시 항목 추가)
_LOCATION_MAP = {
    r"^DSV$": "DSV MUSSAFAH",
    r"^MOSB$": "SAMSUNG MOSB",
    r"^(MIR|MIRFA)$": "MIRFA PMO SAMSUNG",
    r"^PRE$": "AGILITY M44 WAREHOUSE",
    r"^MARKAZ$": "DSV MARKAZ",
    r"^(SKM|SAMSUNG)$": "SAMSUNG",
    r"^(SHU|SHUWEIHAT)$": "SHUWEIHAT",
    r"^HE$": "HAULER",
    r"^HAU$": "HAULER",
    r"^SAS$": "SAS WAREHOUSE",
    r"^FP$": "FALCON PACK",
    r"^DAS$": "DASMAL",
    r"^AGI$": "AGILITY",
    r"^TEC$": "TECHNO ELECTRIC",
    r"^TRO$": "TRONOX",
    r"^MDAS$": "MOSB DASMAL",
}


def expand_location_abbrev(s: str) -> str:
    """
    파일명 약어/짧은 토큰을 표준 지명으로 확장.
    입력이 이미 정규화된 전체명이라면 그대로 반환.

    Args:
        s: 약어 또는 전체 지명

    Returns:
        확장된 표준 지명
    """
    if not s:
        return ""

    s_norm = normalize_location(s)

    for pat, canon in _LOCATION_MAP.items():
        if re.match(pat, s_norm):
            return canon

    return s_norm
