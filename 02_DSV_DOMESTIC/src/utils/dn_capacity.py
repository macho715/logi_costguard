# -*- coding: utf-8 -*-
"""
DN capacity 관리 시스템
- 오버라이드: 환경변수 또는 JSON 파일
- 자동 용량 상향: 수요 기반
"""
from __future__ import annotations
import json
import os
import re
from typing import Dict, List


def _safe_int(x, default=1) -> int:
    """안전한 int 변환"""
    try:
        v = int(x)
        return v if v >= 0 else default
    except Exception:
        return default


def _load_json_file(path: str) -> dict:
    """JSON 파일 로드"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_capacity_overrides() -> Dict[str, int]:
    """
    DN capacity 오버라이드 로드

    우선순위:
      1) ENV: DN_CAPACITY_MAP='{"HVDC-ADOPT-SCT-0126":2,"HVDC-DSV-SKM-MOSB-212":3}'
      2) ENV: DN_CAPACITY_FILE=/path/to/map.json

    Returns:
        Dict[pattern, capacity]: 패턴과 capacity 매핑
    """
    mapping: Dict[str, int] = {}

    # 환경변수에서 JSON 직접 로드
    env_map = os.getenv("DN_CAPACITY_MAP", "").strip()
    if env_map:
        try:
            data = json.loads(env_map)
            for k, v in data.items():
                mapping[str(k)] = _safe_int(v, 1)
        except Exception:
            pass

    # JSON 파일에서 로드
    file_path = os.getenv("DN_CAPACITY_FILE", "").strip()
    if file_path:
        data = _load_json_file(file_path)
        for k, v in data.items():
            mapping[str(k)] = _safe_int(v, 1)

    return mapping


def apply_capacity_overrides(dn_list: List[dict], mapping: Dict[str, int]) -> None:
    """
    shipment_ref/filename에 매핑 키가 '부분일치' 또는 '정규식'으로 매치되면 capacity 갱신

    Args:
        dn_list: DN 리스트
        mapping: {pattern: capacity} 매핑
    """
    for dn in dn_list:
        dn_data = dn.get("data", {}) or {}
        meta = dn.get("meta", {}) or {}

        ref = str(meta.get("shipment_ref_from_folder", "") or "")
        name = str(meta.get("filename", "") or "")

        for pat, cap in mapping.items():
            # 부분일치
            if pat in ref or pat in name:
                dn_data["capacity"] = cap
                dn["data"] = dn_data
                continue

            # 정규식 시도
            try:
                if re.search(pat, ref) or re.search(pat, name):
                    dn_data["capacity"] = cap
                    dn["data"] = dn_data
            except re.error:
                continue


def auto_capacity_bump(dn_list: List[dict], top_choice_counts: Dict[int, int]) -> None:
    """
    수요 기반 자동 용량 상향

    Args:
        dn_list: DN 리스트
        top_choice_counts: {dn_index: demand_count} 수요 카운트

    ENV:
        DN_AUTO_CAPACITY_BUMP=true (기본 false)
        DN_MAX_CAPACITY=16 (상한; 인기 DN 수요 대응)

    로직:
        - 이미 오버라이드된 DN은 건드리지 않음
        - 수요 > 1인 DN의 capacity를 수요만큼 증가 (상한까지)
    """
    if os.getenv("DN_AUTO_CAPACITY_BUMP", "false").lower() != "true":
        return

    max_cap = _safe_int(os.getenv("DN_MAX_CAPACITY", "16"), 16)

    for j, dn in enumerate(dn_list):
        dn_data = dn.get("data", {}) or {}

        # 수동 오버라이드 존중 (capacity > 1이면 건드리지 않음)
        current_cap = dn_data.get("capacity", DN_CAPACITY_DEFAULT := 1)
        if isinstance(current_cap, int) and current_cap > 1:
            continue

        # 수요 확인
        demand = int(top_choice_counts.get(j, 0))
        if demand > 1:
            dn_data["capacity"] = min(demand, max_cap)
            dn["data"] = dn_data
        else:
            # 기본 capacity 설정
            if "capacity" not in dn_data:
                dn_data["capacity"] = 1
                dn["data"] = dn_data
