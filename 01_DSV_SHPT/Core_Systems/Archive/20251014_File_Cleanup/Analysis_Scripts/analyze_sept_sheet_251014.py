#!/usr/bin/env python3
"""
SEPT 시트 구조 분석 및 활용 가능 정보 추출
"""

import pandas as pd
from pathlib import Path
import numpy as np

# Excel 파일 경로
excel_path = (
    Path(__file__).parent.parent
    / "Data"
    / "DSV 202509"
    / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
)

print("=" * 100)
print("SEPT 시트 구조 분석")
print("=" * 100)

# SEPT 시트 로드
print(f"\n파일 로드 중: {excel_path.name}")
sept_df = pd.read_excel(excel_path, sheet_name="SEPT")

# 1. 기본 정보
print("\n" + "=" * 100)
print("1. 기본 정보")
print("=" * 100)
print(f"\n행 개수: {len(sept_df)}")
print(f"열 개수: {len(sept_df.columns)}")
print(f"데이터 범위: {sept_df.shape}")

# 2. 컬럼 상세 정보
print("\n" + "=" * 100)
print("2. 컬럼 상세 정보")
print("=" * 100)
print("\n컬럼 목록 (총 {}개):".format(len(sept_df.columns)))
for i, col in enumerate(sept_df.columns, 1):
    non_null = sept_df[col].notna().sum()
    null_count = sept_df[col].isna().sum()
    dtype = sept_df[col].dtype
    print(
        f"  {i:2d}. {col:40s} - Non-null: {non_null:3d} ({non_null/len(sept_df)*100:5.1f}%) | Null: {null_count:3d} | Type: {dtype}"
    )

# 3. 샘플 데이터
print("\n" + "=" * 100)
print("3. 샘플 데이터 (처음 10행)")
print("=" * 100)
# 컬럼이 많으면 일부만 표시
important_cols = [
    col
    for col in sept_df.columns
    if col
    in [
        "No",
        "CWI Job Number",
        "Order Ref. Number",
        "S/No",
        "RATE SOURCE",
        "DESCRIPTION",
        "RATE",
        "Q'TY",
        "TOTAL (USD)",
    ]
]
if important_cols:
    print(sept_df[important_cols].head(10).to_string(index=False))
else:
    print(sept_df.head(10).to_string(index=False))

# 4. 고유 값 분석
print("\n" + "=" * 100)
print("4. 고유 값 분석")
print("=" * 100)

key_columns = ["Order Ref. Number", "DESCRIPTION", "RATE SOURCE", "CWI Job Number"]
for col in key_columns:
    if col in sept_df.columns:
        unique_count = sept_df[col].nunique()
        total_count = sept_df[col].notna().sum()
        print(f"\n[{col}]")
        print(f"  - 고유 값: {unique_count}")
        print(f"  - 전체 값: {total_count}")
        print(f"  - 상위 5개:")
        value_counts = sept_df[col].value_counts().head(5)
        for val, count in value_counts.items():
            print(f"    * {val}: {count}건")

# 5. MasterData와 비교
print("\n" + "=" * 100)
print("5. SEPT vs MasterData 컬럼 비교")
print("=" * 100)

masterdata_df = pd.read_excel(excel_path, sheet_name="MasterData")
sept_cols = set(sept_df.columns)
master_cols = set(masterdata_df.columns)

print(f"\nSEPT 컬럼 수: {len(sept_cols)}")
print(f"MasterData 컬럼 수: {len(master_cols)}")
print(f"공통 컬럼 수: {len(sept_cols & master_cols)}")

print("\n[SEPT에만 있는 컬럼]:")
sept_only = sept_cols - master_cols
if sept_only:
    for i, col in enumerate(sorted(sept_only), 1):
        print(f"  {i}. {col}")
else:
    print("  (없음)")

print("\n[MasterData에만 있는 컬럼]:")
master_only = master_cols - sept_cols
if master_only:
    for i, col in enumerate(sorted(master_only), 1):
        print(f"  {i}. {col}")
else:
    print("  (없음)")

# 6. 추가 메타데이터 추출
print("\n" + "=" * 100)
print("6. 활용 가능한 메타데이터 분석")
print("=" * 100)

if "DESCRIPTION" in sept_df.columns:
    # Transportation 항목
    print("\n[Transportation 항목 분석]")
    transportation_items = sept_df[
        sept_df["DESCRIPTION"].str.contains(
            "TRANSPORTATION|TRUCKING|FROM|TO", na=False, case=False
        )
    ]
    print(f"Transportation 관련 항목: {len(transportation_items)}건")

    if len(transportation_items) > 0:
        print("\n샘플 Transportation 항목 (처음 5건):")
        trans_cols = (
            ["Order Ref. Number", "DESCRIPTION", "RATE", "Q'TY"]
            if "Q'TY" in sept_df.columns
            else ["Order Ref. Number", "DESCRIPTION", "RATE"]
        )
        trans_cols = [col for col in trans_cols if col in sept_df.columns]
        print(transportation_items[trans_cols].head(5).to_string(index=False))

        # 경로 패턴 분석
        print("\n경로 패턴 추출:")
        for idx, row in transportation_items.head(5).iterrows():
            desc = str(row.get("DESCRIPTION", ""))
            if "FROM" in desc.upper() and "TO" in desc.upper():
                print(f"  - {desc}")

    # Container 항목
    print("\n[Container Fees 분석]")
    container_items = sept_df[
        sept_df["DESCRIPTION"].str.contains(
            "CONTAINER|20DC|40HC|40DC|20FT|40FT", na=False, case=False
        )
    ]
    print(f"Container 관련 항목: {len(container_items)}건")

    if len(container_items) > 0:
        print("\n샘플 Container 항목 (처음 5건):")
        cont_cols = [col for col in trans_cols if col in sept_df.columns]
        print(container_items[cont_cols].head(5).to_string(index=False))

    # Terminal Handling
    print("\n[Terminal Handling 분석]")
    thc_items = sept_df[
        sept_df["DESCRIPTION"].str.contains(
            "TERMINAL HANDLING|THC", na=False, case=False
        )
    ]
    print(f"Terminal Handling 관련 항목: {len(thc_items)}건")

    if len(thc_items) > 0:
        print("\n샘플 THC 항목:")
        thc_cols = [col for col in trans_cols if col in sept_df.columns]
        print(thc_items[thc_cols].head(5).to_string(index=False))

    # DO FEE
    print("\n[DO FEE 분석]")
    do_fee_items = sept_df[
        sept_df["DESCRIPTION"].str.contains(
            "DO FEE|DELIVERY ORDER", na=False, case=False
        )
    ]
    print(f"DO FEE 관련 항목: {len(do_fee_items)}건")

    if len(do_fee_items) > 0:
        print("\n샘플 DO FEE 항목:")
        do_cols = [col for col in trans_cols if col in sept_df.columns]
        print(do_fee_items[do_cols].head(5).to_string(index=False))

        # AIR vs CONTAINER 구분
        if "Order Ref. Number" in sept_df.columns:
            air_do = do_fee_items[
                do_fee_items["Order Ref. Number"].str.contains("HE", na=False)
            ]
            container_do = do_fee_items[
                do_fee_items["Order Ref. Number"].str.contains("SCT", na=False)
            ]
            print(f"\n  AIR (HE) DO FEE: {len(air_do)}건")
            print(f"  CONTAINER (SCT) DO FEE: {len(container_do)}건")

# 7. RATE SOURCE 분석
if "RATE SOURCE" in sept_df.columns:
    print("\n" + "=" * 100)
    print("7. RATE SOURCE 분포")
    print("=" * 100)

    rate_source_counts = sept_df["RATE SOURCE"].value_counts()
    print(f"\n총 {len(rate_source_counts)}개 유형:")
    for source, count in rate_source_counts.items():
        print(f"  - {source}: {count}건 ({count/len(sept_df)*100:.1f}%)")

# 8. 데이터 품질 확인
print("\n" + "=" * 100)
print("8. 데이터 품질 확인")
print("=" * 100)

# Null 값이 많은 컬럼
print("\nNull 값이 많은 컬럼 (>10%):")
for col in sept_df.columns:
    null_pct = sept_df[col].isna().sum() / len(sept_df) * 100
    if null_pct > 10:
        print(f"  - {col}: {null_pct:.1f}%")

# 중복 행
if "Order Ref. Number" in sept_df.columns and "DESCRIPTION" in sept_df.columns:
    duplicates = sept_df.duplicated(subset=["Order Ref. Number", "DESCRIPTION"]).sum()
    print(f"\n중복 행 (Order Ref + DESCRIPTION 기준): {duplicates}건")

# 9. MasterData와 데이터 일치 여부
print("\n" + "=" * 100)
print("9. MasterData와 데이터 일치 여부")
print("=" * 100)

print(f"\nSEPT 행 개수: {len(sept_df)}")
print(f"MasterData 행 개수: {len(masterdata_df)}")
print(f"차이: {abs(len(sept_df) - len(masterdata_df))}건")

# 공통 컬럼에 대한 값 일치 확인
common_cols = ["Order Ref. Number", "DESCRIPTION", "RATE"]
common_cols = [col for col in common_cols if col in sept_cols and col in master_cols]

if common_cols:
    print("\n공통 컬럼 값 일치 확인:")
    for col in common_cols:
        # 동일 행 수만큼만 비교
        min_rows = min(len(sept_df), len(masterdata_df))
        matches = (
            sept_df[col].iloc[:min_rows] == masterdata_df[col].iloc[:min_rows]
        ).sum()
        print(f"  - {col}: {matches}/{min_rows} ({matches/min_rows*100:.1f}%) 일치")

print("\n" + "=" * 100)
print("[분석 완료]")
print("=" * 100)

# 10. 활용 가능 정보 요약
print("\n" + "=" * 100)
print("10. 활용 가능 정보 요약")
print("=" * 100)

print("\n[OK] 발견된 활용 가능 정보:")
print(
    "  1. Shipment별 요금 요약 (MASTER DO, CUSTOMS CLEARANCE, PORT HANDLING, TRANSPORTATION)"
)
print("  2. POL/POD (Port of Loading/Discharge) - Lane Map 확장 가능")
print("  3. Mode (AIR/SEA) - Transport Mode 자동 식별")
print("  4. Container 수량 (No. Of CNTR) - 검증 로직에 활용")
print("  5. Trips 수 - Transportation 요금 검증")
print("  6. BOE (Bill of Entry) 정보 - Customs 관련 검증")

print("\n[WARN] 개선 필요 사항:")
if sept_only:
    print(f"  - SEPT 시트에만 있는 {len(sept_only)}개 컬럼 활용 검토")
if master_only:
    print(f"  - MasterData 시트에만 있는 {len(master_only)}개 컬럼의 출처 확인")

print("\n[INFO] 권장 사항:")
print("  1. SEPT 시트는 Shipment별 요약 정보 - MasterData는 상세 Line Item")
print("  2. Shpt Ref로 SEPT와 MasterData 연결 가능")
print("  3. SEPT의 요금 합계와 MasterData 합계 비교 검증 추가")
print("  4. POL/POD 정보로 Lane Map 자동 확장")
print("  5. Mode 정보로 AIR/SEA 자동 구분")
