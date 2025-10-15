#!/usr/bin/env python3
import pandas as pd
import json
from pathlib import Path

ref_dir = Path("reference_output")

# Lane medians
lane = pd.read_csv(ref_dir / "ref_lane_medians.csv")
print("=" * 80)
print(f"Lane Medians: {len(lane)} lanes")
print("=" * 80)
print(
    lane[
        [
            "origin_norm",
            "destination_norm",
            "vehicle_norm",
            "median_rate_usd",
            "median_distance_km",
            "samples",
        ]
    ].head(10)
)

# Region medians
region = pd.read_csv(ref_dir / "ref_region_medians.csv")
print(f"\nRegion Medians: {len(region)} regions")
print(
    region[
        ["region_o", "region_d", "vehicle_norm", "median_rate_usd", "samples"]
    ].head()
)

# Min-Fare
with open(ref_dir / "ref_min_fare.json") as f:
    minfare = json.load(f)
print(f"\nMin-Fare Table: {len(minfare)} vehicles")
for k, v in list(minfare.items())[:7]:
    print(f"  {k}: {v} USD")

# Adjusters
with open(ref_dir / "ref_adjusters.json") as f:
    adjust = json.load(f)
print(f"\nAdjusters: {adjust}")

# Special pass
sp = pd.read_csv(ref_dir / "special_pass_whitelist.csv")
print(f"\nSpecial Pass Whitelist: {len(sp)} keys")

# Summary
with open(ref_dir / "domestic_reference.json") as f:
    summary = json.load(f)
print(f"\nReference Summary:")
for k, v in summary.items():
    print(f"  {k}: {v}")
