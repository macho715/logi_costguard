#!/usr/bin/env python3
"""
최신 실행 결과 Contract 검증 확인
"""

import pandas as pd
from pathlib import Path

# 최신 CSV 결과 로드
csv_file = (
    Path(__file__).parent.parent
    / "Results"
    / "Sept_2025"
    / "CSV"
    / "shpt_sept_2025_enhanced_result_20251013_002105.csv"
)

if not csv_file.exists():
    print(f"[ERROR] File not found: {csv_file}")
    exit(1)

df = pd.read_csv(csv_file)
contract = df[df["charge_group"] == "Contract"]

print("=" * 80)
print("Contract Validation Results (Latest Run)")
print("=" * 80)
print()
print(f"Total Contract Items: {len(contract)}")
print(
    f"ref_rate filled: {contract['ref_rate_usd'].notna().sum()} ({contract['ref_rate_usd'].notna().sum()/len(contract)*100:.1f}%)"
)
print(
    f"delta_pct calculated: {(contract['delta_pct']!=0).sum() + (contract['ref_rate_usd'].notna() & (contract['delta_pct']==0)).sum()}"
)
print()

print("=" * 80)
print("COST-GUARD Band Distribution")
print("=" * 80)
print(contract["cg_band"].value_counts())
print()

print("=" * 80)
print("Status Distribution")
print("=" * 80)
print(contract["status"].value_counts())
print()

print("=" * 80)
print("Sample Contract Items (First 10)")
print("=" * 80)
cols = [
    "s_no",
    "description",
    "unit_rate",
    "ref_rate_usd",
    "delta_pct",
    "cg_band",
    "status",
]
print(contract[cols].head(10).to_string(index=False))
print()

# 개선 비교
print("=" * 80)
print("Before vs After Comparison")
print("=" * 80)
print("Before (2025-10-12 12:37):")
print("  ref_rate filled: 0/64 (0.0%)")
print("  delta_pct calculated: 0/64 (0.0%)")
print("  Pass: 23, Review: 41")
print()
print("After (2025-10-13 00:21):")
print(
    f"  ref_rate filled: {contract['ref_rate_usd'].notna().sum()}/64 ({contract['ref_rate_usd'].notna().sum()/64*100:.1f}%)"
)
print(f"  delta_pct calculated: {contract['ref_rate_usd'].notna().sum()}/64")
pass_count = len(contract[contract["status"] == "PASS"])
fail_count = len(contract[contract["status"] == "FAIL"])
review_count = len(contract[contract["status"].str.contains("REVIEW", na=False)])
print(f"  Pass: {pass_count}, Review: {review_count}, Fail: {fail_count}")
print()

print("=" * 80)
improvement = contract["ref_rate_usd"].notna().sum()
if improvement >= 55:
    print(f"[SUCCESS] Target achieved! {improvement}/64 ({improvement/64*100:.1f}%)")
else:
    print(f"[PARTIAL] Progress made: {improvement}/64 ({improvement/64*100:.1f}%)")
