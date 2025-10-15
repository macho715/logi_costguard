#!/usr/bin/env python3
"""
REVIEW_NEEDED 항목 샘플링 분석 스크립트
"""
import pandas as pd
from pathlib import Path

# 최신 검증 결과 파일 로드
csv_file = Path(__file__).parent / "out" / "masterdata_validated_20251015_001208.csv"
df = pd.read_csv(csv_file)

# REVIEW_NEEDED 항목 추출
review_df = df[df["Validation_Status"] == "REVIEW_NEEDED"].copy()

print("=" * 80)
print(f"REVIEW_NEEDED 항목 샘플링 분석 (Total: {len(review_df)}건 중 10건)")
print("=" * 80)
print()

# 랜덤 샘플 10건 추출
sample = review_df.sample(min(10, len(review_df)), random_state=42)

# 상세 정보 출력
for i, (idx, row) in enumerate(sample.iterrows(), 1):
    print(f"[REVIEW #{i}] (Row {idx})")
    print(f"  Order Ref: {row['Order Ref. Number']}")
    print(f"  Description: {row['DESCRIPTION'][:60]}...")
    print(f"  Rate: {row['RATE']} USD")
    print(f"  Ref Rate: {row.get('Ref_Rate_USD', 'N/A')} USD")
    print(f"  Delta: {row.get('Delta_Percent', 'N/A')}%")
    print(f"  Charge Group: {row.get('Charge_Group', 'N/A')}")
    print(f"  Notes: {row['Validation_Notes'][:80]}...")
    print()

# 패턴 분류
print("=" * 80)
print("REVIEW_NEEDED 원인 분류")
print("=" * 80)

# Notes 키워드 분석
reason_keywords = {
    "No ref rate": 0,
    "PDF not available": 0,
    "Delta": 0,
    "AtCost": 0,
    "Other": 0,
}

for note in review_df["Validation_Notes"]:
    note_str = str(note).lower()
    if "no ref rate" in note_str:
        reason_keywords["No ref rate"] += 1
    elif "pdf not available" in note_str or "no pdf" in note_str:
        reason_keywords["PDF not available"] += 1
    elif "delta" in note_str:
        reason_keywords["Delta"] += 1
    elif "atcost" in note_str:
        reason_keywords["AtCost"] += 1
    else:
        reason_keywords["Other"] += 1

for reason, count in reason_keywords.items():
    if count > 0:
        print(f"  {count}건: {reason}")

print()
print("=" * 80)
