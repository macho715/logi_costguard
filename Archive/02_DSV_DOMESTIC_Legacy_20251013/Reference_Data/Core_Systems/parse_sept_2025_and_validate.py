#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
9월 2025 DOMESTIC 인보이스 파싱 후 패치된 validator로 검증
"""

import pandas as pd
import sys
from pathlib import Path
from domestic_validator_patched import validate_domestic_invoices

def parse_sept_2025_invoice(excel_path):
    """9월 2025 인보이스 Excel 파싱"""
    print(f"인보이스 파싱 중: {excel_path}")
    
    # Excel 파일 읽기 (header=None, 인보이스 형식)
    raw_df = pd.read_excel(excel_path, sheet_name=0, header=None)
    
    # S/N 헤더 행 찾기
    header_row = None
    for idx, row in raw_df.iterrows():
        row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
        if 'S/N' in row_str or 'S/No' in row_str or 'S/NO' in row_str.upper():
            header_row = idx
            print(f"✓ 헤더 행 발견: {idx}행")
            break
    
    if header_row is None:
        raise ValueError("헤더 행(S/N)을 찾을 수 없습니다")
    
    # 헤더 설정 및 데이터 추출
    raw_df.columns = raw_df.iloc[header_row]
    data_df = raw_df[header_row + 1:].reset_index(drop=True)
    
    # 인보이스 항목 추출
    items = []
    for idx, row in data_df.iterrows():
        try:
            s_no = str(row.get('S/N', row.get('S/No', row.get('S/NO', '')))).strip()
            
            # 빈 행이나 TOTAL 행 스킵
            if not s_no or s_no == 'nan' or 'TOTAL' in s_no.upper():
                continue
            
            # Shipment Reference
            shipment_ref = str(row.get('Shipment Reference#', row.get('REF', row.get('REFERENCE', '')))).strip()
            
            # Origin/Destination (실제 컬럼명 사용)
            origin = str(row.get('Place of Loading', row.get('ORIGIN', ''))).strip()
            destination = str(row.get('Place of Delivery', row.get('DESTINATION', ''))).strip()
            
            # 빈 경우 스킵
            if (not origin or origin == 'nan') and (not destination or destination == 'nan'):
                continue
            
            # Vehicle Type
            vehicle = str(row.get('Vehicle Type', row.get('VEHICLE', 'FLATBED'))).strip().upper()
            if vehicle == 'nan' or not vehicle:
                vehicle = 'FLATBED'
            
            # Rate
            rate_usd = 0.0
            for rate_col_name in ['Rate (USD)', 'RATE', 'Rate', 'UNIT RATE', 'Unit Rate']:
                if rate_col_name in row.index:
                    rate_val = row.get(rate_col_name)
                    if pd.notna(rate_val):
                        try:
                            rate_usd = float(str(rate_val).replace(',', ''))
                            if rate_usd > 0:
                                break
                        except:
                            pass
            
            # Quantity (# Trips)
            qty_col = row.get('# Trips', row.get("Q'TY", row.get('QTY', 1)))
            quantity = float(str(qty_col).replace(',', '')) if pd.notna(qty_col) else 1
            
            # Distance (기본값 0)
            distance_km = 0
            
            items.append({
                'Shipment Reference': shipment_ref if shipment_ref and shipment_ref != 'nan' else f"DOM-{s_no}",
                'Place of Loading': origin if origin and origin != 'nan' else "UNKNOWN",
                'Place of Delivery': destination if destination and destination != 'nan' else "UNKNOWN",
                'Vehicle Type': vehicle,
                'Q/TY': quantity,
                'Rate (USD)': rate_usd,
                'Distance(km)': distance_km,
            })
            
        except Exception as e:
            print(f"경고: 행 {idx} 파싱 실패: {e}")
            continue
    
    if not items:
        raise ValueError("추출된 항목이 없습니다")
    
    df = pd.DataFrame(items)
    print(f"✓ {len(df)}개 항목 파싱 완료")
    return df


def main():
    """메인 실행"""
    
    # 파일 경로
    excel_file = Path("../Data/DSV 202509/SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025.xlsx")
    temp_csv = Path("../Results/Sept_2025/sept_2025_parsed.csv")
    output_xlsx = Path("../Results/Sept_2025/domestic_sept_2025_patched_report.xlsx")
    output_json = Path("../Results/Sept_2025/domestic_sept_2025_patched_artifact.json")
    
    print("="*60)
    print("9월 2025 DOMESTIC 인보이스 검증 (패치 버전)")
    print("="*60)
    
    # 1. 인보이스 파싱
    df = parse_sept_2025_invoice(excel_file)
    
    # 2. 임시 CSV 저장
    temp_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(temp_csv, index=False)
    print(f"✓ 파싱된 데이터 저장: {temp_csv}")
    
    # 3. 패치된 validator로 검증
    print("\n패치된 validator로 검증 시작...")
    items, summary_band, summary_ver, artifact, recap = validate_domestic_invoices(
        str(temp_csv), str(output_xlsx), str(output_json)
    )
    
    # 4. 결과 출력
    print("\n" + "="*60)
    print("=== PRISM Recap Card ===")
    print(recap)
    print("="*60)
    
    print(f"\n✅ 검증 완료!")
    print(f"총 항목: {len(items)}")
    print(f"\n검증 결과:")
    for record in summary_ver.to_dict('records'):
        print(f"  {record['verification']:20s} {record['count']:4d}개")
    
    print(f"\nCOST-GUARD 밴드:")
    for record in summary_band.to_dict('records'):
        print(f"  {record['cg_band']:20s} {record['count']:4d}개")
    
    print(f"\n결과 파일:")
    print(f"  - {output_xlsx}")
    print(f"  - {output_json}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

