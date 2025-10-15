#!/usr/bin/env python3
"""E2E 검증 (좌표/테이블 추출 개선 후)"""
import sys
import os
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path.cwd() / "00_Shared"))
sys.path.insert(0, str(Path.cwd() / "01_DSV_SHPT" / "Core_Systems"))

# Set environment
os.environ["USE_HYBRID"] = "false"  # 기존 시스템으로 검증 (Hybrid는 선택적)

from masterdata_validator import MasterDataValidator

print("[E2E] MasterData 검증 시작...")
print(f"[E2E] USE_HYBRID={os.environ.get('USE_HYBRID')}")

validator = MasterDataValidator()
results_df = validator.validate_all()

# Summary
total = len(results_df)
pass_count = len(results_df[results_df["Validation_Status"] == "PASS"])
review_count = len(results_df[results_df["Validation_Status"] == "REVIEW_NEEDED"])
fail_count = len(results_df[results_df["Validation_Status"] == "FAIL"])

print(f"\n[RESULT] 검증 완료: {total} items")
print(f"  PASS: {pass_count} ({pass_count/total*100:.1f}%)")
print(f"  REVIEW: {review_count} ({review_count/total*100:.1f}%)")
print(f"  FAIL: {fail_count} ({fail_count/total*100:.1f}%)")

# At Cost 분석
atcost = results_df[results_df["RATE SOURCE"] == "AT COST"]
print(f"\n[AT COST] {len(atcost)} items")
if len(atcost) > 0:
    atcost_pass = len(atcost[atcost["Validation_Status"] == "PASS"])
    atcost_review = len(atcost[atcost["Validation_Status"] == "REVIEW_NEEDED"])
    atcost_fail = len(atcost[atcost["Validation_Status"] == "FAIL"])
    print(f"  PASS: {atcost_pass} ({atcost_pass/len(atcost)*100:.1f}%)")
    print(f"  REVIEW: {atcost_review} ({atcost_review/len(atcost)*100:.1f}%)")
    print(f"  FAIL: {atcost_fail} ({atcost_fail/len(atcost)*100:.1f}%)")

print(f"\n[SUCCESS] E2E 검증 완료")
