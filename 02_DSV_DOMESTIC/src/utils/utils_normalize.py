# -*- coding: utf-8 -*-
# utils_normalize.py — structural
import re
from typing import Set

# DN 문서 접두/기관 표기 등 비교에 불필요한 토큰
STOPWORDS: Set[str] = {"CICPA", "PMO"}


def _squash(s: str) -> str:
    """다중 공백을 단일 공백으로 축소"""
    return re.sub(r"\s+", " ", s).strip()


def normalize_location(s: str) -> str:
    """
    지명/시설명을 비교 가능한 표준 문자열로 정규화:
      - 대문자화
      - 영숫자/공백만 유지
      - 다중 공백 축소
      - STOPWORDS 제거
    """
    if not s:
        return ""
    s = s.upper()
    s = re.sub(r"[^A-Z0-9\s]", " ", s)
    s = _squash(s)
    toks = [t for t in s.split() if t and t not in STOPWORDS]
    return " ".join(toks)


def token_set_jaccard(a: str, b: str) -> float:
    """
    간단·견고한 토큰 세트 자카드 유사도.

    Args:
        a: 첫 번째 문자열
        b: 두 번째 문자열

    Returns:
        0.0 ~ 1.0 사이의 자카드 유사도
    """
    A, B = set(a.split()), set(b.split())
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)
