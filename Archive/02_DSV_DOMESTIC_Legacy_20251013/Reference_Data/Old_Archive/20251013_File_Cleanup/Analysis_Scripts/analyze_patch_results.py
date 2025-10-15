#!/usr/bin/env python3
"""Analyze 7-step patch results"""

import pandas as pd
from pathlib import Path

# File paths
results_dir = Path(__file__).parent / "Results" / "Sept_2025" / "CSV"
before_csv = results_dir / "domestic_sept_2025_result_20251013_012914.csv"  # 100 lanes
after_csv = (
    results_dir / "domestic_sept_2025_result_20251013_013624.csv"
)  # 7-step patch

print("=" * 80)
print("7-Step Patch Results Analysis")
print("=" * 80)

# Load data
df_before = pd.read_csv(before_csv)
df_after = pd.read_csv(after_csv)

print(f"\nBefore (100 Lanes): {len(df_before)} items")
band_before = df_before["cg_band"].value_counts()
print(band_before)
print(
    f"  PASS: {band_before.get('PASS', 0)} ({band_before.get('PASS', 0)/len(df_before)*100:.1f}%)"
)
print(
    f"  CRITICAL: {band_before.get('CRITICAL', 0)} ({band_before.get('CRITICAL', 0)/len(df_before)*100:.1f}%)"
)

print(f"\nAfter (7-Step Patch): {len(df_after)} items")
band_after = df_after["cg_band"].value_counts()
print(band_after)
print(
    f"  PASS: {band_after.get('PASS', 0)} ({band_after.get('PASS', 0)/len(df_after)*100:.1f}%)"
)
print(
    f"  CRITICAL: {band_after.get('CRITICAL', 0)} ({band_after.get('CRITICAL', 0)/len(df_after)*100:.1f}%)"
)

# Compare
print("\n" + "=" * 80)
print("Change Summary")
print("=" * 80)
pass_change = band_after.get("PASS", 0) - band_before.get("PASS", 0)
critical_change = band_after.get("CRITICAL", 0) - band_before.get("CRITICAL", 0)
print(
    f"  PASS: {band_before.get('PASS', 0)} → {band_after.get('PASS', 0)} ({pass_change:+d})"
)
print(
    f"  CRITICAL: {band_before.get('CRITICAL', 0)} → {band_after.get('CRITICAL', 0)} ({critical_change:+d})"
)
print(f"  HIGH: {band_before.get('HIGH', 0)} → {band_after.get('HIGH', 0)}")
print(f"  WARN: {band_before.get('WARN', 0)} → {band_after.get('WARN', 0)}")

# Check decision column
if "decision" in df_after.columns:
    print("\nDecision Distribution (After):")
    decision_counts = df_after["decision"].value_counts()
    print(decision_counts)

    # Confidence gate stats
    if "confidence_gate" in df_after.columns:
        verified_count = len(df_after[df_after["decision"] == "VERIFIED"])
        print(f"\n  VERIFIED (Confidence Gate): {verified_count}")

# Flags analysis
if "flags" in df_after.columns:
    print("\nTop 10 Flags (After):")
    all_flags = []
    for flags_str in df_after["flags"].dropna():
        all_flags.extend(str(flags_str).split("|"))
    flag_counts = pd.Series(all_flags).value_counts().head(10)
    for flag, count in flag_counts.items():
        print(f"  {flag}: {count}")

print("\n" + "=" * 80)
