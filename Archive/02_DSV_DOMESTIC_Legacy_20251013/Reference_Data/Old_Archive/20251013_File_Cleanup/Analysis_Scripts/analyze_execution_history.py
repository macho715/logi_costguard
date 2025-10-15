#!/usr/bin/env python3
"""
Analyze DOMESTIC execution history across all validation runs
"""

import pandas as pd
from pathlib import Path
import json


def analyze_all_results():
    """모든 검증 결과 분석"""
    base_dir = Path(__file__).parent
    csv_dir = base_dir / "Results" / "Sept_2025" / "CSV"

    # Identify all result files
    result_files = sorted(csv_dir.glob("domestic_sept_2025_*.csv"))

    timeline = []

    for idx, csv_file in enumerate(result_files, 1):
        # Parse filename for timestamp
        name = csv_file.stem

        # Load data
        df = pd.read_csv(csv_file)

        # Extract metrics
        band_dist = (
            df["cg_band"].value_counts().to_dict() if "cg_band" in df.columns else {}
        )

        # Determine phase
        if "interpolated" in name:
            phase = "Distance Interpolation"
        elif "003929" in name:
            phase = "Initial (Embedded 8)"
        elif "010927" in name:
            phase = "PATCH2-1 (4 Algorithms)"
        elif "012914" in name:
            phase = "100-Lane Generation"
        elif "013624" in name:
            phase = "7-Step Quality Patch"
        elif "014944" in name:
            phase = "124-Lane Enhancement"
        else:
            phase = f"Run {idx}"

        timeline.append(
            {
                "Run": idx,
                "Phase": phase,
                "File": csv_file.name,
                "Total Items": len(df),
                "PASS": band_dist.get("PASS", 0),
                "WARN": band_dist.get("WARN", 0),
                "HIGH": band_dist.get("HIGH", 0),
                "CRITICAL": band_dist.get("CRITICAL", 0),
                "UNKNOWN": band_dist.get("UNKNOWN", 0),
                "PASS %": (
                    round(band_dist.get("PASS", 0) / len(df) * 100, 1)
                    if len(df) > 0
                    else 0
                ),
                "CRITICAL %": (
                    round(band_dist.get("CRITICAL", 0) / len(df) * 100, 1)
                    if len(df) > 0
                    else 0
                ),
            }
        )

    # Add Ref-from-Execution result
    ref_exec_file = base_dir / "domestic ref" / "verification_results" / "items.csv"
    if ref_exec_file.exists():
        df_ref = pd.read_csv(ref_exec_file)
        band_dist_ref = df_ref["cg_band"].value_counts().to_dict()

        timeline.append(
            {
                "Run": len(timeline) + 1,
                "Phase": "Reference-from-Execution",
                "File": "items.csv (domestic ref)",
                "Total Items": len(df_ref),
                "PASS": band_dist_ref.get("PASS", 0),
                "WARN": band_dist_ref.get("WARN", 0),
                "HIGH": band_dist_ref.get("HIGH", 0),
                "CRITICAL": band_dist_ref.get("CRITICAL", 0),
                "UNKNOWN": band_dist_ref.get("UNKNOWN", 0),
                "PASS %": round(band_dist_ref.get("PASS", 0) / len(df_ref) * 100, 1),
                "CRITICAL %": round(
                    band_dist_ref.get("CRITICAL", 0) / len(df_ref) * 100, 1
                ),
            }
        )

    return pd.DataFrame(timeline)


def main():
    print("=" * 80)
    print("DOMESTIC Execution History Analysis")
    print("=" * 80)

    timeline_df = analyze_all_results()

    print(f"\nTotal validation runs: {len(timeline_df)}")
    print("\nTimeline:")
    print(
        timeline_df[["Run", "Phase", "PASS", "CRITICAL", "CRITICAL %"]].to_string(
            index=False
        )
    )

    # Key milestones
    print("\n" + "=" * 80)
    print("Key Milestones")
    print("=" * 80)

    initial_critical = timeline_df.iloc[0]["CRITICAL"]
    final_critical = timeline_df.iloc[-1]["CRITICAL"]
    reduction = initial_critical - final_critical
    reduction_pct = (reduction / initial_critical * 100) if initial_critical > 0 else 0

    print(f"\nInitial CRITICAL: {initial_critical}")
    print(f"Final CRITICAL: {final_critical}")
    print(f"Reduction: -{reduction} ({reduction_pct:.1f}%)")

    # Best improvement
    timeline_df["CRITICAL_Change"] = timeline_df["CRITICAL"].diff().fillna(0)
    best_improvement = timeline_df.loc[timeline_df["CRITICAL_Change"].idxmin()]

    print(f"\nBest single improvement:")
    print(f"  Phase: {best_improvement['Phase']}")
    print(f"  CRITICAL change: {best_improvement['CRITICAL_Change']:.0f}")

    # Save
    output_excel = Path(__file__).parent / "DOMESTIC_EXECUTION_HISTORY.xlsx"
    timeline_df.to_excel(output_excel, index=False)

    print(f"\n[OK] History saved: {output_excel}")

    return timeline_df


if __name__ == "__main__":
    main()
