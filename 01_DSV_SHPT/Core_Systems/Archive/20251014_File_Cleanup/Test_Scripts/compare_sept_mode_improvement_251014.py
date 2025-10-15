#!/usr/bin/env python3
"""
SEPT Mode 통합 전후 개선 효과 비교
"""

import pandas as pd
from pathlib import Path

# 최신 검증 결과 로드
csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_211702.csv"
df = pd.read_csv(csv_path)

print("=" * 100)
print("SEPT Mode 통합 후 개선 효과 분석")
print("=" * 100)

# Before vs After 비교
print("\n[1] Validation Status 비교")
print("-" * 100)
print("\nBefore (SEPT Mode 통합 전):")
print("  - FAIL: 16건 (15.7%)")
print("  - PASS: 36건 (35.3%)")
print("  - REVIEW_NEEDED: 50건 (49.0%)")

fail_count = (df["Validation_Status"] == "FAIL").sum()
pass_count = (df["Validation_Status"] == "PASS").sum()
review_count = (df["Validation_Status"] == "REVIEW_NEEDED").sum()

print("\nAfter (SEPT Mode 통합 후):")
print(f"  - FAIL: {fail_count}건 ({fail_count/len(df)*100:.1f}%)")
print(f"  - PASS: {pass_count}건 ({pass_count/len(df)*100:.1f}%)")
print(f"  - REVIEW_NEEDED: {review_count}건 ({review_count/len(df)*100:.1f}%)")

fail_reduction = 16 - fail_count
pass_increase = pass_count - 36

print("\n[개선 효과]:")
print(f"  - FAIL 감소: {fail_reduction}건 ({fail_reduction/16*100:.1f}%)")
print(f"  - PASS 증가: {pass_increase}건 ({pass_increase/36*100:.1f}%)")

# FAIL 항목 상세
print("\n[2] 남은 FAIL 항목 상세 ({}건)".format(fail_count))
print("-" * 100)

fail_items = df[df["Validation_Status"] == "FAIL"]
for _, row in fail_items.iterrows():
    print(f"\n{int(row['No'])}. {row['Order Ref. Number']}")
    print(f"   DESCRIPTION: {row['DESCRIPTION']}")
    print(f"   RATE: {row['RATE']:.2f} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')}")
    if pd.notna(row.get("Python_Delta")):
        print(f"   Delta: {row['Python_Delta']:.2f}%")
    print(f"   CG_Band: {row.get('CG_Band', 'N/A')}")
    print(f"   Notes: {row['Validation_Notes'][:80]}")

# FAIL 항목 카테고리 분석
print("\n[3] 남은 FAIL 항목 카테고리 분석")
print("-" * 100)

fail_charge_group = fail_items["Charge_Group"].value_counts()
print("\nCharge Group 분포:")
for group, count in fail_charge_group.items():
    print(f"  - {group}: {count}건 ({count/len(fail_items)*100:.1f}%)")

# DO FEE 검증
print("\n[4] DO FEE 검증 결과")
print("-" * 100)

do_fee_items = df[df["DESCRIPTION"].str.contains("MASTER DO FEE", na=False, case=False)]
do_fee_pass = do_fee_items[do_fee_items["Validation_Status"] == "PASS"]
do_fee_fail = do_fee_items[do_fee_items["Validation_Status"] == "FAIL"]

print(f"\nTotal DO FEE: {len(do_fee_items)}건")
print(f"  - PASS: {len(do_fee_pass)}건 ({len(do_fee_pass)/len(do_fee_items)*100:.1f}%)")
print(f"  - FAIL: {len(do_fee_fail)}건 ({len(do_fee_fail)/len(do_fee_items)*100:.1f}%)")

print("\nBefore SEPT Mode 통합:")
print("  - FAIL: 12건 (48.0%) - Mode 오판")

print("\nAfter SEPT Mode 통합:")
print(f"  - FAIL: {len(do_fee_fail)}건 ({len(do_fee_fail)/len(do_fee_items)*100:.1f}%)")
print(f"  - 개선: {12 - len(do_fee_fail)}건 해결 ({(12-len(do_fee_fail))/12*100:.1f}%)")

# PASS 항목 증가 분석
print("\n[5] PASS 항목 증가 분석")
print("-" * 100)

print(f"\nBefore: PASS 36건 (35.3%)")
print(f"After:  PASS {pass_count}건 ({pass_count/len(df)*100:.1f}%)")
print(f"증가: {pass_increase}건 ({pass_increase/36*100:.1f}% 증가)")

# 새로 PASS된 항목 (DO FEE 위주)
new_pass_do_fee = len(do_fee_pass) - (25 - 12)  # 이전에는 25건 중 12건 FAIL
print(f"\n새로 PASS된 DO FEE: 약 {12 - len(do_fee_fail)}건 (Mode 오판 해결)")

# 최종 요약
print("\n" + "=" * 100)
print("최종 요약")
print("=" * 100)

print("\n[핵심 성과]")
print(f"  1. FAIL 감소: 16 -> {fail_count}건 ({fail_reduction/16*100:.1f}% 감소)")
print(f"  2. PASS 증가: 36 -> {pass_count}건 ({pass_increase/36*100:.1f}% 증가)")
print(f"  3. DO FEE FAIL 해결: 12 -> {len(do_fee_fail)}건")
print(f"  4. COST-GUARD CRITICAL: 12 -> {(fail_items['CG_Band']=='CRITICAL').sum()}건")

print("\n[남은 과제]")
if fail_count > 0:
    print(f"  - FAIL {fail_count}건 해결 (주로 Portal Fee 환율 이슈)")
print(f"  - REVIEW_NEEDED {review_count}건 개선 (Ref Rate 추가 등)")

print("\n" + "=" * 100)
print("[분석 완료]")
print("=" * 100)

