#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 파일에 ApprovedLaneMap 시트 추가 및 하이퍼링크 생성
Enhanced with multi-level matching algorithm
"""

import pandas as pd
import json
import xlsxwriter
from pathlib import Path
import re
from enhanced_matching import find_matching_lane_enhanced

def token_set_similarity(s1: str, s2: str) -> float:
    """Token-Set 유사도 계산"""
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    t1 = set(str(s1).upper().split())
    t2 = set(str(s2).upper().split())
    
    if not t1 or not t2:
        return 0.0
    
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    
    return intersection / union if union > 0 else 0.0

def normalize_location(location: str) -> str:
    """향상된 위치명 정규화"""
    if pd.isna(location):
        return ""
    
    loc = str(location).upper().strip()
    
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

def find_matching_lane(origin, destination, vehicle, unit, approved_lanes):
    """
    ApprovedLaneMap에서 매칭되는 레인 찾기
    
    Returns:
        dict: {"row_index": int, "match_score": float, "lane_data": dict} or None
    """
    
    best_match = None
    best_score = 0.0
    
    # 정규화
    origin_norm = normalize_location(origin)
    dest_norm = normalize_location(destination)
    
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = str(lane.get("vehicle", "")).upper()
        lane_unit = str(lane.get("unit", "per truck"))
        
        # 1. 정확 매칭 (최우선)
        if (lane_origin == origin_norm and
            lane_dest == dest_norm and
            lane_vehicle == str(vehicle).upper() and
            lane_unit == str(unit)):
            return {
                "row_index": i + 2,  # Excel 행 번호 (헤더 고려)
                "match_score": 1.0,
                "lane_data": lane
            }
        
        # 2. 유사도 매칭 (차선) - 더 관대한 매칭
        if lane_vehicle == str(vehicle).upper() and lane_unit == str(unit):
            origin_sim = token_set_similarity(origin, lane.get("origin", ""))
            dest_sim = token_set_similarity(destination, lane.get("destination", ""))
            
            # 전체 유사도 (Origin 60%, Destination 40%)
            total_sim = 0.6 * origin_sim + 0.4 * dest_sim
            
            # 임계값을 0.7에서 0.5로 낮춤 (더 많은 매칭 허용)
            if total_sim > best_score and total_sim >= 0.5:  # 50% 이상 유사도
                best_match = {
                    "row_index": i + 2,
                    "match_score": total_sim,
                    "lane_data": lane
                }
                best_score = total_sim
    
    return best_match

def add_approved_lanemap_to_excel(
    excel_file="Results/Sept_2025/domestic_sept_2025_advanced_v3_NO_LEAK.xlsx",
    approved_json="Results/Sept_2025/Reports/ApprovedLaneMap_ENHANCED.json",
    output_file=None
):
    """
    Excel 파일에 ApprovedLaneMap 시트 추가 및 하이퍼링크 생성
    """
    
    excel_path = Path(excel_file)
    json_path = Path(approved_json)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    print("=" * 80)
    print("📊 Excel ApprovedLaneMap 통합 시작")
    print("=" * 80)
    
    # 1. 기존 Excel 파일 로드
    print(f"📂 Loading Excel: {excel_path.name}")
    items_df = pd.read_excel(excel_file, sheet_name="items")
    comparison_df = pd.read_excel(excel_file, sheet_name="comparison") 
    patterns_df = pd.read_excel(excel_file, sheet_name="patterns_applied")
    
    print(f"  ✅ items: {len(items_df)} records")
    print(f"  ✅ comparison: {len(comparison_df)} records")
    print(f"  ✅ patterns_applied: {len(patterns_df)} records")
    
    # 2. ApprovedLaneMap JSON 로드
    print(f"\n📂 Loading ApprovedLaneMap: {json_path.name}")
    with open(json_path, 'r', encoding='utf-8') as f:
        approved_data = json.load(f)
    
    approved_lanes = approved_data["data"]["Sheet1"]
    print(f"  ✅ ApprovedLanes: {len(approved_lanes)} lanes")
    
    # 3. ApprovedLaneMap DataFrame 생성
    approved_df = pd.DataFrame(approved_lanes)
    
    # 컬럼 순서 정리
    columns_order = [
        "lane_id", "origin", "destination", "vehicle", "unit",
        "median_rate_usd", "mean_rate_usd", "samples",
        "median_distance_km", "mean_distance_km", "std_rate_usd", "notes", "key"
    ]
    
    approved_df = approved_df[[col for col in columns_order if col in approved_df.columns]]
    
    # 4. 매칭 및 하이퍼링크 정보 생성 (ENHANCED)
    print(f"\n🔗 하이퍼링크 매칭 중... (Enhanced Multi-Level Matching)")
    
    hyperlink_info = []
    match_stats = {
        "exact": 0,
        "similarity": 0,
        "region": 0,
        "vehicle_type": 0,
        "no_match": 0
    }
    
    for i, row in items_df.iterrows():
        origin = row.get("origin", "")
        destination = row.get("destination", "")
        vehicle = row.get("vehicle", "")
        unit = row.get("unit", "per truck")
        
        # Enhanced 매칭 사용
        match_result = find_matching_lane_enhanced(
            origin, destination, vehicle, unit, approved_lanes, verbose=False
        )
        
        if match_result:
            match_level = match_result.get("match_level", "SIMILARITY")
            
            hyperlink_info.append({
                "item_row": i + 2,  # Excel row (헤더 고려)
                "target_row": match_result["row_index"],
                "match_score": match_result["match_score"],
                "match_level": match_level,
                "approved_rate": match_result["lane_data"].get("median_rate_usd", 0),
                "lane_id": match_result["lane_data"].get("lane_id", "")
            })
            
            # 통계 업데이트
            if match_level == "EXACT":
                match_stats["exact"] += 1
            elif match_level == "SIMILARITY":
                match_stats["similarity"] += 1
            elif match_level == "REGION":
                match_stats["region"] += 1
            elif match_level == "VEHICLE_TYPE":
                match_stats["vehicle_type"] += 1
        else:
            match_stats["no_match"] += 1
            hyperlink_info.append({
                "item_row": i + 2,
                "target_row": None,
                "match_score": 0.0,
                "match_level": None,
                "approved_rate": None,
                "lane_id": None
            })
    
    print(f"  ✅ 매칭 결과 (Enhanced):")
    print(f"    Level 1 - 정확 매칭: {match_stats['exact']}건")
    print(f"    Level 2 - 유사도 매칭: {match_stats['similarity']}건")
    print(f"    Level 3 - 권역 매칭: {match_stats['region']}건")
    print(f"    Level 4 - 차량타입 매칭: {match_stats['vehicle_type']}건")
    print(f"    매칭 실패: {match_stats['no_match']}건")
    
    total_matched = match_stats['exact'] + match_stats['similarity'] + match_stats['region'] + match_stats['vehicle_type']
    match_rate = (total_matched / len(items_df) * 100) if len(items_df) > 0 else 0
    print(f"    📊 총 매칭률: {match_rate:.1f}% ({total_matched}/{len(items_df)})")
    
    # 5. 출력 파일 경로
    if output_file is None:
        output_file = excel_path.parent / f"{excel_path.stem}_WITH_LANEMAP.xlsx"
    
    output_path = Path(output_file)
    
    # 6. 새 Excel 파일 생성 (xlsxwriter 사용)
    print(f"\n📝 새 Excel 파일 생성: {output_path.name}")
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # 하이퍼링크 포맷 정의
        hyperlink_format = workbook.add_format({
            'font_color': 'blue',
            'underline': 1,
            'num_format': '"$"#,##0.00'
        })
        
        normal_format = workbook.add_format({
            'num_format': '"$"#,##0.00'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1
        })
        
        # Sheet 1: items (하이퍼링크 포함)
        items_df.to_excel(writer, sheet_name="items", index=False)
        worksheet_items = writer.sheets["items"]
        
        # 헤더 포맷팅
        for col_num, value in enumerate(items_df.columns.values):
            worksheet_items.write(0, col_num, value, header_format)
        
        # ref_rate_usd 컬럼에 하이퍼링크 추가
        ref_rate_col_index = None
        if "ref_adj" in items_df.columns:
            ref_rate_col_index = list(items_df.columns).index("ref_adj")
        elif "ref_base" in items_df.columns:
            ref_rate_col_index = list(items_df.columns).index("ref_base")
        
        if ref_rate_col_index is not None:
            print(f"  🔗 Adding hyperlinks to column: {items_df.columns[ref_rate_col_index]}")
            
            for link_info in hyperlink_info:
                item_row = link_info["item_row"]
                target_row = link_info["target_row"]
                
                # 실제 요율 값
                rate_value = items_df.iloc[item_row - 2].iloc[ref_rate_col_index]
                
                if pd.notna(rate_value) and target_row:
                    # 하이퍼링크 생성
                    hyperlink_url = f"internal:ApprovedLaneMap!A{target_row}"
                    worksheet_items.write_url(
                        item_row - 1, ref_rate_col_index,  # Excel 0-based index
                        hyperlink_url,
                        hyperlink_format,
                        string=f"${float(rate_value):,.2f}"
                    )
                elif pd.notna(rate_value):
                    # 매칭 없는 경우 일반 숫자
                    worksheet_items.write(
                        item_row - 1, ref_rate_col_index,
                        float(rate_value),
                        normal_format
                    )
        
        # Sheet 2: comparison
        comparison_df.to_excel(writer, sheet_name="comparison", index=False)
        worksheet_comp = writer.sheets["comparison"]
        for col_num, value in enumerate(comparison_df.columns.values):
            worksheet_comp.write(0, col_num, value, header_format)
        
        # Sheet 3: patterns_applied
        patterns_df.to_excel(writer, sheet_name="patterns_applied", index=False)
        worksheet_pat = writer.sheets["patterns_applied"]
        for col_num, value in enumerate(patterns_df.columns.values):
            worksheet_pat.write(0, col_num, value, header_format)
        
        # Sheet 4: ApprovedLaneMap (신규)
        print(f"  📋 Adding ApprovedLaneMap sheet...")
        approved_df.to_excel(writer, sheet_name="ApprovedLaneMap", index=False)
        worksheet_approved = writer.sheets["ApprovedLaneMap"]
        
        # ApprovedLaneMap 헤더 포맷팅
        for col_num, value in enumerate(approved_df.columns.values):
            worksheet_approved.write(0, col_num, value, header_format)
        
        # ApprovedLaneMap 컬럼 너비 조정
        worksheet_approved.set_column('A:A', 8)   # lane_id
        worksheet_approved.set_column('B:B', 20)  # origin
        worksheet_approved.set_column('C:C', 25)  # destination
        worksheet_approved.set_column('D:D', 15)  # vehicle
        worksheet_approved.set_column('E:E', 12)  # unit
        worksheet_approved.set_column('F:F', 15)  # median_rate_usd
        worksheet_approved.set_column('G:G', 15)  # mean_rate_usd
        worksheet_approved.set_column('H:H', 10)  # samples
        
        # items 시트 컬럼 너비 조정
        worksheet_items.set_column('A:A', 20)  # origin
        worksheet_items.set_column('B:B', 25)  # destination
        worksheet_items.set_column('C:C', 15)  # vehicle
        
    print(f"✅ Excel 파일 저장 완료: {output_path}")
    
    # 결과 요약
    print(f"\n📊 작업 요약:")
    print(f"  총 항목: {len(items_df)}")
    print(f"  ApprovedLanes: {len(approved_df)}")
    print(f"  하이퍼링크: {match_stats['exact'] + match_stats['similarity']}개")
    print(f"  매칭률: {((match_stats['exact'] + match_stats['similarity']) / len(items_df)) * 100:.1f}%")
    
    total_matched = match_stats['exact'] + match_stats['similarity'] + match_stats['region'] + match_stats['vehicle_type']
    
    return {
        "output_file": str(output_path),
        "total_items": len(items_df),
        "total_approved_lanes": len(approved_df),
        "hyperlinks_created": total_matched,
        "match_rate_percent": (total_matched / len(items_df) * 100) if len(items_df) > 0 else 0,
        "match_stats": match_stats
    }

def main():
    """메인 실행 함수"""
    
    excel_file = "Results/Sept_2025/domestic_sept_2025_advanced_v3_NO_LEAK.xlsx"
    approved_json = "Results/Sept_2025/Reports/ApprovedLaneMap_ENHANCED.json"
    output_file = "Results/Sept_2025/domestic_sept_2025_advanced_v3_NO_LEAK_WITH_LANEMAP_ENHANCED.xlsx"
    
    try:
        result = add_approved_lanemap_to_excel(excel_file, approved_json, output_file)
        
        print(f"\n{'='*80}")
        print(f"🎉 작업 완료! (Enhanced Multi-Level Matching)")
        print(f"{'='*80}")
        print(f"📄 출력 파일: {result['output_file']}")
        print(f"🔗 하이퍼링크: {result['hyperlinks_created']}/{result['total_items']}개")
        print(f"📊 매칭률: {result['match_rate_percent']:.1f}%")
        print(f"\n📈 매칭 상세:")
        print(f"  - Level 1 (정확): {result['match_stats']['exact']}건")
        print(f"  - Level 2 (유사도): {result['match_stats']['similarity']}건")
        print(f"  - Level 3 (권역): {result['match_stats']['region']}건")
        print(f"  - Level 4 (차량타입): {result['match_stats']['vehicle_type']}건")
        print(f"  - 매칭 실패: {result['match_stats']['no_match']}건")
        
        return True
        
    except Exception as e:
        print(f"❌ 작업 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ ApprovedLaneMap 통합 및 하이퍼링크 생성 완료!")
    else:
        print("\n💥 작업 실패!")
