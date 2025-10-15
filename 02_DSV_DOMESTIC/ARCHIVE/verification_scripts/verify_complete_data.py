#!/usr/bin/env python3
"""Complete data verification - Check all validation results"""
import pandas as pd

excel_file = "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_20251014_202923.xlsx"

print("=" * 80)
print("COMPLETE DATA VERIFICATION - All Columns Analysis")
print("=" * 80)

# Load all sheets
items_df = pd.read_excel(excel_file, sheet_name="items")
dn_val_df = pd.read_excel(excel_file, sheet_name="DN_Validation")

print(f"\n[SHEET 1] items: {items_df.shape[0]} rows x {items_df.shape[1]} columns")
print("\nColumn Categories:")
print("  - BASE (Invoice data): 12 columns")
print("  - DN (PDF validation): 13 columns")
print("  - HYBRID (Routing info): 5 columns")
print("  Total: 30 columns")

print(
    f"\n[SHEET 2] DN_Validation: {dn_val_df.shape[0]} rows x {dn_val_df.shape[1]} columns"
)

print("\n" + "=" * 80)
print("INVOICE VALIDATION RESULTS (verdict_adj column)")
print("=" * 80)
print(items_df["verdict_adj"].value_counts())
verified_count = len(items_df[items_df["verdict_adj"] == "VERIFIED"])
print(f"\nSummary: {verified_count}/44 VERIFIED ({verified_count/44*100:.1f}%)")

print("\n" + "=" * 80)
print("DN MATCHING RESULTS (dn_matched column)")
print("=" * 80)
print(items_df["dn_matched"].value_counts())
dn_yes = len(items_df[items_df["dn_matched"] == "Yes"])
print(f"\nSummary: {dn_yes}/44 matched ({dn_yes/44*100:.1f}%)")

print("\n" + "=" * 80)
print("HYBRID ROUTING RESULTS (hybrid_engine column)")
print("=" * 80)
print(items_df["hybrid_engine"].value_counts(dropna=False))
hybrid_count = items_df["hybrid_engine"].notna().sum()
print(f"\nSummary: {hybrid_count}/44 processed by Hybrid ({hybrid_count/44*100:.1f}%)")

print("\n" + "=" * 80)
print("SAMPLE ROW - All Validation Data (Row 0)")
print("=" * 80)
row = items_df.iloc[0]
print(f"Invoice Data:")
print(f'  origin: {row["origin"]}')
print(f'  destination: {row["destination"]}')
print(f'  vehicle: {row["vehicle"]}')
print(f'  draft_usd: {row["draft_usd"]}')
print(f'  verdict_adj: {row["verdict_adj"]}')
print(f"\nDN Validation:")
print(f'  dn_matched: {row["dn_matched"]}')
print(f'  dn_validation_status: {row["dn_validation_status"]}')
print(f'  dn_origin_similarity: {row["dn_origin_similarity"]}')
print(f'  dn_dest_similarity: {row["dn_dest_similarity"]}')
print(f"\nHybrid Routing:")
print(f'  hybrid_engine: {row["hybrid_engine"]}')
print(f'  hybrid_rule: {row["hybrid_rule"]}')
print(f'  hybrid_confidence: {row["hybrid_confidence"]}')
print(f'  hybrid_validation: {row["hybrid_validation"]}')

print("\n" + "=" * 80)
print("CRITICAL CHECK: Null value counts")
print("=" * 80)
print(f'verdict_adj null: {items_df["verdict_adj"].isnull().sum()}')
print(f'dn_matched null: {items_df["dn_matched"].isnull().sum()}')
print(f'hybrid_engine null: {items_df["hybrid_engine"].isnull().sum()}')

print("\n" + "=" * 80)
print("DATA COMPLETENESS CHECK")
print("=" * 80)

# Check if all key columns exist
required_cols = [
    "origin",
    "destination",
    "vehicle",
    "draft_usd",
    "verdict_adj",
    "dn_matched",
    "dn_validation_status",
    "hybrid_engine",
    "hybrid_rule",
    "hybrid_confidence",
]

missing_cols = [col for col in required_cols if col not in items_df.columns]
if missing_cols:
    print(f"[ERROR] Missing columns: {missing_cols}")
else:
    print("[OK] All required columns present")

# Check data completeness
print("\nData completeness per column:")
for col in required_cols:
    non_null = items_df[col].notna().sum()
    print(f"  {col:25s}: {non_null:2d}/44 ({non_null/44*100:5.1f}%)")

print("\n" + "=" * 80)
print("LOGIC VERIFICATION")
print("=" * 80)

# Verify: If dn_matched == "Yes", then hybrid_engine should not be null
matched_rows = items_df[items_df["dn_matched"] == "Yes"]
matched_with_hybrid = matched_rows[matched_rows["hybrid_engine"].notna()]

print(f"\nDN matched rows: {len(matched_rows)}")
print(f"  - With hybrid data: {len(matched_with_hybrid)}")
print(f"  - Without hybrid data: {len(matched_rows) - len(matched_with_hybrid)}")

if len(matched_rows) == len(matched_with_hybrid):
    print("[OK] All DN-matched rows have hybrid data")
else:
    print("[WARNING] Some DN-matched rows missing hybrid data")
    missing_hybrid = matched_rows[matched_rows["hybrid_engine"].isna()]
    print(f"\nRows with DN matched but no hybrid data:")
    print(
        missing_hybrid[["origin", "destination", "dn_matched", "hybrid_engine"]].head()
    )

print("\n[VERIFICATION COMPLETE]")
