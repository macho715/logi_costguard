#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Lane Matching Algorithm Module
========================================
고급 레인 매칭 알고리즘: 정규화, 유사도, 다단계 매칭
"""

import pandas as pd
import re
from typing import Optional, Dict, List, Tuple


# ============================================================================
# 1. NORMALIZATION: 확장된 정규화 로직
# ============================================================================

# 약어 및 시노님 매핑
LOCATION_SYNONYMS = {
    # 철자 변형
    "MUSSAFAH": ["MUSAFAH", "MUSAFFAH", "MUSSAFFAH"],
    "MUSAFFAH": ["MUSSAFAH", "MUSAFAH", "MUSSAFFAH"],
    
    # 약어
    "WAREHOUSE": ["WH", "W/H", "WHEREHOUSE"],
    "PORT": ["MINA", "HARBOUR", "HARBOR"],
    "MINA": ["PORT"],
    
    # 지역명
    "JEBEL ALI": ["JEBEL", "J.ALI", "JABEL ALI"],
    "ABU DHABI": ["ABUDHABI", "AD", "A.D"],
    "DUBAI": ["DXB", "DB"],
    
    # 시설명
    "YARD": ["YRD", "STORAGE"],
    "SITE": ["LOCATION", "LOC"],
    "FACTORY": ["PLANT", "FACTY"],
    
    # 회사명
    "SAMSUNG": ["SAMSNG", "SAMSG"],
    "MASAOOD": ["MASOOD", "MASOUD", "MOSB"],
}

VEHICLE_SYNONYMS = {
    "FLATBED": ["FLAT BED", "FLAT-BED", "FLAT_BED", "FB"],
    "FLAT BED": ["FLATBED", "FLAT-BED", "FLAT_BED"],
    "TRUCK": ["LORRY", "VEHICLE"],
    "LORRY": ["TRUCK"],
    "TRAILER": ["TRAILOR", "TRALER"],
    "CRANE": ["MOBILE CRANE", "MCR"],
}


def normalize_text(text: str, synonym_map: Dict[str, List[str]]) -> str:
    """
    텍스트를 정규화하고 시노님을 표준화
    
    Args:
        text: 원본 텍스트
        synonym_map: 시노님 매핑 딕셔너리
    
    Returns:
        정규화된 텍스트
    """
    if pd.isna(text):
        return ""
    
    text = str(text).upper().strip()
    
    # 특수문자 정리 (but keep spaces)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 시노님 매핑
    for standard, variants in synonym_map.items():
        for variant in variants:
            if variant in text:
                text = text.replace(variant, standard)
    
    return text


def normalize_location(location: str) -> str:
    """
    향상된 위치명 정규화
    
    기존 하드코딩 규칙 + 시노님 매핑 통합
    """
    if pd.isna(location):
        return ""
    
    # 기본 정규화
    loc = normalize_text(location, LOCATION_SYNONYMS)
    
    # 기존 하드코딩 규칙 (우선순위 높음)
    # DSV 관련
    if "DSV" in loc and "MUSSAFAH" in loc:
        return "DSV MUSSAFAH YARD"
    
    if "DSV" in loc and "M44" in loc:
        return "M44 WAREHOUSE"
    
    if "DSV" in loc and "MARKAZ" in loc:
        return "AL MARKAZ WAREHOUSE"
    
    # MIRFA 관련
    if any(k in loc for k in ["MIRFA", "PMO"]) and "SAMSUNG" in loc:
        return "MIRFA SITE"
    
    # SHUWEIHAT 관련  
    if any(k in loc for k in ["SHUWEIHAT", "POWER"]):
        return "SHUWEIHAT SITE"
    
    # MOSB/MASAOOD 관련
    if any(k in loc for k in ["MOSB", "MASAOOD"]):
        if "SAMSUNG" in loc:
            return "SAMSUNG MOSB YARD"
        else:
            return "AL MASAOOD (MOSB)"
    
    # MINA/PORT 관련
    if any(k in loc for k in ["MINA", "ZAYED", "PORT", "FREEPORT"]):
        if "JEBEL" in loc:
            return "JEBEL ALI PORT"
        else:
            return "MINA ZAYED PORT"
    
    # M44 관련
    if "M44" in loc:
        return "M44 WAREHOUSE"
    
    # ICAD 관련
    if "ICAD" in loc:
        return "ICAD WAREHOUSE"
    
    # MARKAZ 관련
    if "MARKAZ" in loc:
        return "AL MARKAZ WAREHOUSE"
    
    # 기타 특수 케이스
    if "TROJAN" in loc:
        return "TROJAN MUSSAFAH"
        
    if "SURTI" in loc and "JEBEL" in loc:
        return "SURTI INDUSTRIES LLC (JEBEL ALI)"
    
    return loc


def normalize_vehicle(vehicle: str) -> str:
    """차량 타입 정규화"""
    if pd.isna(vehicle):
        return ""
    
    return normalize_text(vehicle, VEHICLE_SYNONYMS)


# ============================================================================
# 2. SIMILARITY: 하이브리드 유사도 알고리즘
# ============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Levenshtein Distance (편집거리) 계산
    
    Args:
        s1, s2: 비교할 두 문자열
    
    Returns:
        편집거리 (삽입/삭제/치환 최소 횟수)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 삽입, 삭제, 치환 비용
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Levenshtein 유사도 (0~1)
    
    Returns:
        1.0 - (distance / max_length)
    """
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    s1, s2 = str(s1).upper(), str(s2).upper()
    
    if s1 == s2:
        return 1.0
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    
    return 1.0 - (distance / max_len) if max_len > 0 else 0.0


def token_set_similarity(s1: str, s2: str) -> float:
    """
    Token-Set 유사도 (교집합/합집합)
    
    Returns:
        intersection / union
    """
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    t1 = set(str(s1).upper().split())
    t2 = set(str(s2).upper().split())
    
    if not t1 or not t2:
        return 0.0
    
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    
    return intersection / union if union > 0 else 0.0


def fuzzy_token_sort_similarity(s1: str, s2: str) -> float:
    """
    Fuzzy Token Sort 유사도
    - 토큰을 정렬한 후 Levenshtein 비교
    
    Returns:
        정렬된 토큰 문자열의 Levenshtein 유사도
    """
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    # 토큰 정렬
    t1_sorted = " ".join(sorted(str(s1).upper().split()))
    t2_sorted = " ".join(sorted(str(s2).upper().split()))
    
    return levenshtein_similarity(t1_sorted, t2_sorted)


def hybrid_similarity(s1: str, s2: str, weights: Dict[str, float] = None) -> float:
    """
    하이브리드 유사도 계산
    
    Args:
        s1, s2: 비교할 문자열
        weights: 각 알고리즘의 가중치
            - token_set: Token-Set Ratio
            - levenshtein: Levenshtein Distance
            - fuzzy_sort: Fuzzy Token Sort
    
    Returns:
        가중 평균 유사도 (0~1)
    """
    if weights is None:
        weights = {
            "token_set": 0.4,
            "levenshtein": 0.3,
            "fuzzy_sort": 0.3
        }
    
    scores = {
        "token_set": token_set_similarity(s1, s2),
        "levenshtein": levenshtein_similarity(s1, s2),
        "fuzzy_sort": fuzzy_token_sort_similarity(s1, s2)
    }
    
    # 가중 평균
    total_score = sum(scores[key] * weights[key] for key in weights)
    
    return total_score


# ============================================================================
# 3. REGIONAL MATCHING: 권역별 매칭
# ============================================================================

REGION_MAP = {
    # Abu Dhabi 권역
    "ABU DHABI REGION": [
        "MUSSAFAH", "MUSAFAH", "ICAD", "M44", "MARKAZ",
        "MOSB", "MASAOOD", "TROJAN", "SHUWEIHAT", "MIRFA",
        "ABU DHABI", "ABUDHABI"
    ],
    
    # Dubai 권역
    "DUBAI REGION": [
        "JEBEL ALI", "JABEL ALI", "DUBAI", "DXB",
        "SURTI"
    ],
    
    # Port 권역
    "PORT REGION": [
        "MINA ZAYED", "JEBEL ALI PORT", "PORT", "MINA"
    ],
    
    # Site 권역
    "CONSTRUCTION SITE": [
        "MIRFA SITE", "SHUWEIHAT SITE", "SITE", "PMO"
    ]
}


def get_region(location: str) -> Optional[str]:
    """
    위치명에서 권역 추출
    
    Returns:
        권역명 또는 None
    """
    loc_upper = str(location).upper()
    
    for region, keywords in REGION_MAP.items():
        if any(kw in loc_upper for kw in keywords):
            return region
    
    return None


# ============================================================================
# 4. VEHICLE TYPE MATCHING: 차량 타입별 매칭
# ============================================================================

VEHICLE_GROUPS = {
    "FLATBED_GROUP": ["FLATBED", "FLAT BED", "FLAT-BED"],
    "TRUCK_GROUP": ["TRUCK", "LORRY", "VEHICLE"],
    "TRAILER_GROUP": ["TRAILER", "TRAILOR", "LOW BED", "LOWBED"],
    "CRANE_GROUP": ["CRANE", "MOBILE CRANE", "MCR"],
}


def get_vehicle_group(vehicle: str) -> Optional[str]:
    """
    차량 타입의 그룹 추출
    
    Returns:
        차량 그룹명 또는 None
    """
    vehicle_upper = str(vehicle).upper()
    
    for group, types in VEHICLE_GROUPS.items():
        if any(vt in vehicle_upper for vt in types):
            return group
    
    return None


# ============================================================================
# 5. MULTI-LEVEL MATCHING: 4단계 매칭 시스템
# ============================================================================

def find_matching_lane_enhanced(
    origin: str,
    destination: str,
    vehicle: str,
    unit: str,
    approved_lanes: List[Dict],
    verbose: bool = False
) -> Optional[Dict]:
    """
    향상된 4단계 매칭 시스템
    
    Level 1: 정확 매칭 (100% 일치)
    Level 2: 향상된 유사도 매칭 (하이브리드)
    Level 3: 권역별 매칭
    Level 4: 차량 타입별 매칭
    
    Args:
        origin: 출발지
        destination: 목적지
        vehicle: 차량 타입
        unit: 단위 (per truck, per ton 등)
        approved_lanes: ApprovedLaneMap 레인 리스트
        verbose: 상세 로그 출력
    
    Returns:
        {
            "row_index": int,
            "match_score": float,
            "match_level": str,  # "EXACT", "SIMILARITY", "REGION", "VEHICLE_TYPE"
            "lane_data": dict
        } or None
    """
    
    # 정규화
    origin_norm = normalize_location(origin)
    dest_norm = normalize_location(destination)
    vehicle_norm = normalize_vehicle(vehicle)
    
    if verbose:
        print(f"\n[MATCHING] {origin} → {destination} ({vehicle})")
        print(f"  Normalized: {origin_norm} → {dest_norm} ({vehicle_norm})")
    
    best_match = None
    best_score = 0.0
    
    # ========================================================================
    # LEVEL 1: 정확 매칭
    # ========================================================================
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        if (lane_origin == origin_norm and
            lane_dest == dest_norm and
            lane_vehicle == vehicle_norm and
            lane_unit == str(unit)):
            
            if verbose:
                print(f"  ✅ LEVEL 1 (EXACT): Lane {i} matched!")
            
            return {
                "row_index": i + 2,
                "match_score": 1.0,
                "match_level": "EXACT",
                "lane_data": lane
            }
    
    # ========================================================================
    # LEVEL 2: 향상된 유사도 매칭 (하이브리드)
    # ========================================================================
    for i, lane in enumerate(approved_lanes):
        lane_origin = lane.get("origin", "")
        lane_dest = lane.get("destination", "")
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        # 차량 및 단위는 정확히 일치해야 함
        if lane_vehicle != vehicle_norm or lane_unit != str(unit):
            continue
        
        # 하이브리드 유사도 계산
        origin_sim = hybrid_similarity(origin, lane_origin)
        dest_sim = hybrid_similarity(destination, lane_dest)
        
        # 가중 평균 (Origin 60%, Destination 40%)
        total_sim = 0.6 * origin_sim + 0.4 * dest_sim
        
        # 임계값: 0.65 이상
        if total_sim > best_score and total_sim >= 0.65:
            best_match = {
                "row_index": i + 2,
                "match_score": total_sim,
                "match_level": "SIMILARITY",
                "lane_data": lane
            }
            best_score = total_sim
    
    if best_match and verbose:
        print(f"  ✅ LEVEL 2 (SIMILARITY): Lane {best_match['row_index']-2} matched (score: {best_score:.2f})")
    
    if best_match:
        return best_match
    
    # ========================================================================
    # LEVEL 3: 권역별 매칭
    # ========================================================================
    origin_region = get_region(origin_norm)
    dest_region = get_region(dest_norm)
    
    if origin_region and dest_region:
        for i, lane in enumerate(approved_lanes):
            lane_origin = normalize_location(lane.get("origin", ""))
            lane_dest = normalize_location(lane.get("destination", ""))
            lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
            lane_unit = str(lane.get("unit", "per truck"))
            
            # 차량 및 단위 일치
            if lane_vehicle != vehicle_norm or lane_unit != str(unit):
                continue
            
            lane_origin_region = get_region(lane_origin)
            lane_dest_region = get_region(lane_dest)
            
            if lane_origin_region == origin_region and lane_dest_region == dest_region:
                # 권역 매칭 점수: 0.5 고정
                score = 0.5
                
                if score > best_score:
                    best_match = {
                        "row_index": i + 2,
                        "match_score": score,
                        "match_level": "REGION",
                        "lane_data": lane
                    }
                    best_score = score
        
        if best_match and verbose:
            print(f"  ✅ LEVEL 3 (REGION): Lane {best_match['row_index']-2} matched (region: {origin_region}→{dest_region})")
    
    if best_match:
        return best_match
    
    # ========================================================================
    # LEVEL 4: 차량 타입별 매칭
    # ========================================================================
    vehicle_group = get_vehicle_group(vehicle_norm)
    
    if vehicle_group:
        for i, lane in enumerate(approved_lanes):
            lane_origin = normalize_location(lane.get("origin", ""))
            lane_dest = normalize_location(lane.get("destination", ""))
            lane_vehicle = lane.get("vehicle", "")
            lane_unit = str(lane.get("unit", "per truck"))
            
            # 단위만 일치하면 됨
            if lane_unit != str(unit):
                continue
            
            lane_vehicle_group = get_vehicle_group(lane_vehicle)
            
            if lane_vehicle_group == vehicle_group:
                # 출발지/목적지 유사도 계산
                origin_sim = hybrid_similarity(origin, lane_origin)
                dest_sim = hybrid_similarity(destination, lane_dest)
                total_sim = 0.6 * origin_sim + 0.4 * dest_sim
                
                # 임계값: 0.4 이상
                if total_sim >= 0.4 and total_sim > best_score:
                    best_match = {
                        "row_index": i + 2,
                        "match_score": total_sim,
                        "match_level": "VEHICLE_TYPE",
                        "lane_data": lane
                    }
                    best_score = total_sim
        
        if best_match and verbose:
            print(f"  ✅ LEVEL 4 (VEHICLE_TYPE): Lane {best_match['row_index']-2} matched (group: {vehicle_group}, score: {best_score:.2f})")
    
    if best_match:
        return best_match
    
    if verbose:
        print(f"  ❌ NO MATCH")
    
    return None


# ============================================================================
# 6. UTILITY FUNCTIONS
# ============================================================================

def compare_matching_results(
    items_df: pd.DataFrame,
    approved_lanes: List[Dict],
    old_matching_func,
    new_matching_func
) -> Dict:
    """
    기존 매칭 vs 새 매칭 결과 비교
    
    Returns:
        {
            "old_stats": {...},
            "new_stats": {...},
            "improvements": [...]
        }
    """
    old_matches = []
    new_matches = []
    
    for i, row in items_df.iterrows():
        origin = row.get("origin", "")
        destination = row.get("destination", "")
        vehicle = row.get("vehicle", "")
        unit = row.get("unit", "per truck")
        
        # 기존 매칭
        old_result = old_matching_func(origin, destination, vehicle, unit, approved_lanes)
        old_matches.append(old_result)
        
        # 새 매칭
        new_result = new_matching_func(origin, destination, vehicle, unit, approved_lanes)
        new_matches.append(new_result)
    
    # 통계 계산
    old_stats = {
        "exact": sum(1 for m in old_matches if m and m.get("match_score") == 1.0),
        "similarity": sum(1 for m in old_matches if m and 0 < m.get("match_score", 0) < 1.0),
        "no_match": sum(1 for m in old_matches if m is None),
        "total": len(old_matches)
    }
    
    new_stats = {
        "exact": sum(1 for m in new_matches if m and m.get("match_level") == "EXACT"),
        "similarity": sum(1 for m in new_matches if m and m.get("match_level") == "SIMILARITY"),
        "region": sum(1 for m in new_matches if m and m.get("match_level") == "REGION"),
        "vehicle_type": sum(1 for m in new_matches if m and m.get("match_level") == "VEHICLE_TYPE"),
        "no_match": sum(1 for m in new_matches if m is None),
        "total": len(new_matches)
    }
    
    # 개선 사항
    improvements = []
    for i, (old, new) in enumerate(zip(old_matches, new_matches)):
        if old is None and new is not None:
            improvements.append({
                "item_index": i,
                "origin": items_df.iloc[i].get("origin", ""),
                "destination": items_df.iloc[i].get("destination", ""),
                "vehicle": items_df.iloc[i].get("vehicle", ""),
                "new_match_level": new.get("match_level"),
                "new_match_score": new.get("match_score")
            })
    
    return {
        "old_stats": old_stats,
        "new_stats": new_stats,
        "improvements": improvements
    }


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 80)
    print("Enhanced Matching Module - Test")
    print("=" * 80)
    
    # 테스트 1: 정규화
    print("\n[TEST 1] Normalization")
    print(f"  normalize_location('DSV Musafah Yard') = {normalize_location('DSV Musafah Yard')}")
    print(f"  normalize_vehicle('FLAT BED') = {normalize_vehicle('FLAT BED')}")
    
    # 테스트 2: 유사도
    print("\n[TEST 2] Similarity")
    s1, s2 = "MUSSAFAH YARD", "MUSAFAH YRD"
    print(f"  token_set_similarity('{s1}', '{s2}') = {token_set_similarity(s1, s2):.3f}")
    print(f"  levenshtein_similarity('{s1}', '{s2}') = {levenshtein_similarity(s1, s2):.3f}")
    print(f"  hybrid_similarity('{s1}', '{s2}') = {hybrid_similarity(s1, s2):.3f}")
    
    # 테스트 3: 권역
    print("\n[TEST 3] Region")
    print(f"  get_region('DSV MUSSAFAH') = {get_region('DSV MUSSAFAH')}")
    print(f"  get_region('JEBEL ALI PORT') = {get_region('JEBEL ALI PORT')}")
    
    # 테스트 4: 차량 그룹
    print("\n[TEST 4] Vehicle Group")
    print(f"  get_vehicle_group('FLATBED') = {get_vehicle_group('FLATBED')}")
    print(f"  get_vehicle_group('FLAT BED') = {get_vehicle_group('FLAT BED')}")
    
    print("\n✅ Module test completed!")

