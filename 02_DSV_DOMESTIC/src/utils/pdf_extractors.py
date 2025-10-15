# -*- coding: utf-8 -*-
# pdf_extractors.py — structural
import re
from .utils_normalize import normalize_location

# Waybill 패턴 (기존 유지)
WAYBILL_RX = re.compile(r"Delivery\s*Note/Waybill#\s*:\s*([A-Za-z0-9\-]+)", re.I)


def extract_field(text: str, rx: re.Pattern, group_idx: int = 1) -> str:
    """
    정규식을 사용하여 텍스트에서 필드 추출

    Args:
        text: 검색할 텍스트
        rx: 정규식 패턴
        group_idx: 추출할 그룹 인덱스

    Returns:
        추출된 필드 값 (없으면 빈 문자열)
    """
    if not text:
        return ""
    m = rx.search(text)
    return m.group(group_idx).strip() if m else ""


def extract_destination_from_text(text: str) -> str:
    """
    DN PDF에서 Destination 추출 (필드명 이전 줄에서 값 추출)

    PDF 구조:
        Line N-1: DSV MUSSAFAH YARD    ← 실제 값
        Line N:   Destination:         ← 필드명
        Line N+1: UAE                  ← 메타데이터
    """
    if not text:
        return ""

    lines = text.split("\n")

    for i, line in enumerate(lines):
        # "Destination:" 필드명 찾기 (단독 줄)
        if re.match(r"^\s*Destination\s*:\s*$", line, re.I):
            # 이전 줄에서 값 추출
            if i > 0:
                value = lines[i - 1].strip()
                # 메타데이터/헤더 필터링
                if value and len(value) > 5:
                    value_upper = value.upper()
                    # 제외할 패턴
                    if not any(
                        skip in value_upper
                        for skip in ["CARRIER", "UAE", "CODE", "COUNTRY"]
                    ):
                        return value

    return ""


def extract_loading_point_from_text(text: str) -> str:
    """
    DN PDF에서 Loading Point (Origin) 추출

    PDF 구조:
        Line N: Loading Point
        Line N+1: Loading
        Line N+2: Country
        ...
        Line N+X: Samsung Mosb yard    ← 실제 값 (description 영역)
    """
    if not text:
        return ""

    lines = text.split("\n")

    # "Description" 섹션에서 위치 키워드 찾기 (가장 신뢰할 수 있음)
    found_description_section = False
    for i, line in enumerate(lines):
        # Description 헤더 찾기
        if re.match(r"^\s*Description\s*$", line, re.I):
            found_description_section = True
            # 이후 15줄 이내에서 위치 키워드 포함된 줄 찾기
            for j in range(i + 1, min(i + 15, len(lines))):
                candidate = lines[j].strip()
                if candidate and len(candidate) > 3:
                    # Shipment Reference 제외 (HVDC-로 시작하거나 3자 이하 코드)
                    if candidate.startswith("HVDC-") or candidate.startswith("SAMF"):
                        continue
                    if re.match(
                        r"^[A-Z]{1,3}-[A-Z]{1,4}-?$", candidate
                    ):  # SKM-MOSB-, 212 등
                        continue
                    if re.match(r"^\d+$", candidate):  # 순수 숫자
                        continue
                    # 숫자/날짜 제외
                    if re.match(r"^[\d/]+$", candidate):
                        continue
                    # UAE 제외
                    if candidate.upper() == "UAE":
                        continue

                    # 알려진 위치 키워드 (전체 단어 포함)
                    candidate_upper = candidate.upper()
                    # 더 엄격한 매칭: 실제 위치명 포함
                    if any(
                        loc in candidate_upper
                        for loc in [
                            "SAMSUNG",
                            "MOSB",
                            "MIRFA",
                            "HAULER",
                            "MARKAZ",
                            "SHUWEIHAT",
                            "PRESTIGE",
                            "AGILITY",
                            "WAREHOUSE",
                            "YARD",  # "yard" 추가
                        ]
                    ):
                        # "yard" 다음 줄 결합 (별도 줄에 있을 수 있음)
                        if "yard" in candidate.lower() and j + 1 < len(lines):
                            next_line = lines[j + 1].strip()
                            if (
                                next_line
                                and len(next_line) < 20
                                and not next_line.startswith("UAE")
                            ):
                                candidate = candidate + " " + next_line
                        # "Mosb" 또는 "Samsung" 다음 줄에 "yard"가 있는지 확인
                        elif (
                            "mosb" in candidate.lower()
                            or "samsung" in candidate.lower()
                        ) and j + 1 < len(lines):
                            next_line = lines[j + 1].strip()
                            if "yard" in next_line.lower():
                                candidate = candidate + " " + next_line
                        return candidate

    # Description 섹션을 못 찾았으면 "Loading Point" 헤더로 시도
    if not found_description_section:
        for i, line in enumerate(lines):
            if "Loading Point" in line:
                for j in range(i + 1, min(i + 15, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and len(candidate) > 5:
                        if re.match(r"^[\d/]+$", candidate):
                            continue
                        if any(
                            loc in candidate.upper()
                            for loc in [
                                "SAMSUNG",
                                "MOSB",
                                "MIRFA",
                                "HAULER",
                                "MARKAZ",
                                "SHUWEIHAT",
                                "MUSSAFAH",
                            ]
                        ):
                            return candidate

    return ""


def extract_from_pdf_text(pdf_text: str) -> dict:
    """
    DN PDF 원문 텍스트에서 고신뢰 필드 추출.

    개선된 전략:
    - Destination: 필드명 이전 줄에서 값 추출
    - Loading Point: description 섹션에서 위치 키워드 기반 추출
    - Waybill: 기존 Regex 패턴 유지

    Args:
        pdf_text: PDF 원본 텍스트

    Returns:
        dict: {
            "dest_code": str,
            "destination": str (정규화됨),
            "loading_point": str (정규화됨),
            "waybill": str
        }
    """
    if not pdf_text:
        return {
            "dest_code": "",
            "destination": "",
            "loading_point": "",
            "waybill": "",
        }

    # Destination: 필드명 이전 줄에서 추출
    destination = extract_destination_from_text(pdf_text)

    # Loading Point: description 섹션에서 추출
    loading_point = extract_loading_point_from_text(pdf_text)

    # Waybill: 기존 패턴 유지
    waybill = extract_field(pdf_text, WAYBILL_RX)

    return {
        "dest_code": "",  # DN PDF에 없음
        "destination": normalize_location(destination),
        "loading_point": normalize_location(loading_point),
        "waybill": waybill,
    }
