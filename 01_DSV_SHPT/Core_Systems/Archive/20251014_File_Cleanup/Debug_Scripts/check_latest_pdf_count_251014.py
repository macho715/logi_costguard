#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

# 최신 CSV 파일 자동 선택
out_dir = Path(__file__).parent / "out"
csv_files = sorted(out_dir.glob("masterdata_validated_*.csv"))
csv_file = csv_files[-1] if csv_files else None

if not csv_file:
    print("[ERROR] No CSV files found")
    exit(1)

print(f"Analyzing: {csv_file.name}\n")
df = pd.read_csv(csv_file)

print("PDF_Count Statistics:")
print(f"  Total with PDFs: {len(df[df['PDF_Count'] > 0])}")
print(f"  Total without PDFs: {len(df[df['PDF_Count'] == 0])}")
print(f"  Average: {df['PDF_Count'].mean():.2f}")
print(f"  Max: {df['PDF_Count'].max():.0f}")
print(f"  Min: {df['PDF_Count'].min():.0f}")

print(f"\nShipments with PDFs:")
for _, row in df[df["PDF_Count"] > 0].head(15).iterrows():
    print(
        f"  {row['Order Ref. Number']}: {row['PDF_Count']:.0f} PDFs - {row['DESCRIPTION'][:35]}"
    )

if len(df[df["PDF_Count"] > 0]) == 0:
    print("  [WARNING] No PDFs found for any item!")
