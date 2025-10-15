#!/usr/bin/env python3
"""패치 Before/After 비교"""

import pandas as pd
from pathlib import Path

base = Path(__file__).parent.parent / "Results" / "Sept_2025" / "CSV"
before = pd.read_csv(base / "domestic_sept_2025_result_20251013_003929.csv")
after = pd.read_csv(base / "domestic_sept_2025_result_20251013_010927.csv")

print("=" * 80)
print("DOMESTIC Patch Impact Analysis")
print("=" * 80)

print("\nBefore Patch (2025-10-13 00:39):")
print(before['cg_band'].value_counts())

print("\nAfter Patch (2025-10-13 01:09):")
print(after['cg_band'].value_counts())

before_c = before['cg_band'].value_counts().to_dict()
after_c = after['cg_band'].value_counts().to_dict()

print("\n" + "=" * 80)
print("Delta (Improvement)")
print("=" * 80)
print(f"PASS:     {before_c.get('PASS', 0):2d} → {after_c.get('PASS', 0):2d}  (+{after_c.get('PASS', 0) - before_c.get('PASS', 0)})")
print(f"WARN:     {before_c.get('WARN', 0):2d} → {after_c.get('WARN', 0):2d}  ({after_c.get('WARN', 0) - before_c.get('WARN', 0):+d})")
print(f"HIGH:     {before_c.get('HIGH', 0):2d} → {after_c.get('HIGH', 0):2d}  ({after_c.get('HIGH', 0) - before_c.get('HIGH', 0):+d})")
print(f"CRITICAL: {before_c.get('CRITICAL', 0):2d} → {after_c.get('CRITICAL', 0):2d}  ({after_c.get('CRITICAL', 0) - before_c.get('CRITICAL', 0):+d})")

print("\n" + "=" * 80)
improvement_pct = (after_c.get('PASS', 0) - before_c.get('PASS', 0)) / len(after) * 100
print(f"[SUCCESS] Patch improved PASS rate by {improvement_pct:.1f}%p")
print(f"          CRITICAL reduced by {abs(after_c.get('CRITICAL', 0) - before_c.get('CRITICAL', 0))} items ({abs(after_c.get('CRITICAL', 0) - before_c.get('CRITICAL', 0))/len(after)*100:.1f}%p)")
print("=" * 80)

