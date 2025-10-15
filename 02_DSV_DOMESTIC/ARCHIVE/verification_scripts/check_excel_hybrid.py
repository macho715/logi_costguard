#!/usr/bin/env python3
"""Check Excel Hybrid columns"""
import pandas as pd

excel_file = "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_20251014_202923.xlsx"

# Load Excel
df = pd.read_excel(excel_file, sheet_name="items")

print("=" * 80)
print(f"DOMESTIC EXCEL with HYBRID INTEGRATION")
print("=" * 80)
print(f"\nFile: {excel_file}")
print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

print(f"\n{'='*80}")
print("ALL COLUMNS (30 total):")
print("=" * 80)
for i, col in enumerate(df.columns, 1):
    prefix = (
        "[HYBRID]"
        if col.startswith("hybrid_")
        else "[DN]" if col.startswith("dn_") else "[BASE]"
    )
    print(f"{i:2d}. {prefix:10s} {col}")

print(f"\n{'='*80}")
print("HYBRID ROUTING COLUMNS (5 new columns):")
print("=" * 80)
hybrid_cols = [col for col in df.columns if col.startswith("hybrid_")]
print(hybrid_cols)

print(f"\n{'='*80}")
print("HYBRID COLUMN SAMPLE (First 10 rows):")
print("=" * 80)
print(df[hybrid_cols].head(10).to_string(index=True))

print(f"\n{'='*80}")
print("HYBRID ENGINE STATISTICS:")
print("=" * 80)
print(df["hybrid_engine"].value_counts())

print(f"\n{'='*80}")
print("HYBRID VALIDATION STATISTICS:")
print("=" * 80)
print(df["hybrid_validation"].value_counts())

print(f"\n{'='*80}")
print("HYBRID CONFIDENCE STATISTICS:")
print("=" * 80)
print(f"Mean: {df['hybrid_confidence'].mean():.3f}")
print(f"Min: {df['hybrid_confidence'].min():.3f}")
print(f"Max: {df['hybrid_confidence'].max():.3f}")

print(f"\n{'='*80}")
print("TOTAL ADE COST:")
print("=" * 80)
print(f"${df['hybrid_ade_cost'].sum():.2f} USD")

print(f"\n{'='*80}")
print("TOP ROUTING RULES USED:")
print("=" * 80)
print(df["hybrid_rule"].value_counts().head(5))

print("\n[SUCCESS] Excel verification complete!")
