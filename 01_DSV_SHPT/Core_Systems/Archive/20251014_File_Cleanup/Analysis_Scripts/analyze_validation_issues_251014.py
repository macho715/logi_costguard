#!/usr/bin/env python3
"""
REVIEW_NEEDED 및 FAIL 항목 상세 분석
"""

import pandas as pd
from pathlib import Path
from collections import Counter

# CSV 로드
csv_path = Path(__file__).parent / "out" / "masterdata_validated_20251014_205430.csv"
df = pd.read_csv(csv_path)

print("=" * 100)
print("REVIEW_NEEDED 및 FAIL 상세 분석")
print("=" * 100)

# 1. REVIEW_NEEDED 분석 (50건)
print("\n" + "=" * 100)
print("1. REVIEW_NEEDED 상세 분석 (50건)")
print("=" * 100)

review_needed = df[df["Validation_Status"] == "REVIEW_NEEDED"]
print(f"\nTotal REVIEW_NEEDED: {len(review_needed)}건")

# Delta 분포
print("\n[Delta % 분포]")
review_with_delta = review_needed[review_needed["Python_Delta"].notna()]
print(f"Delta 값 있음: {len(review_with_delta)}건")

if len(review_with_delta) > 0:
    deltas = review_with_delta["Python_Delta"].abs()
    minor = (deltas <= 5).sum()
    moderate = ((deltas > 5) & (deltas <= 15)).sum()
    high = ((deltas > 15) & (deltas <= 30)).sum()
    critical = (deltas > 30).sum()

    print(f"  - Minor (0-5%): {minor}건 ({minor/len(review_with_delta)*100:.1f}%)")
    print(
        f"  - Moderate (5-15%): {moderate}건 ({moderate/len(review_with_delta)*100:.1f}%)"
    )
    print(f"  - High (15-30%): {high}건 ({high/len(review_with_delta)*100:.1f}%)")
    print(
        f"  - Critical (>30%): {critical}건 ({critical/len(review_with_delta)*100:.1f}%)"
    )

# Charge Group 분포
print("\n[Charge Group 분포]")
charge_group_counts = review_needed["Charge_Group"].value_counts()
for group, count in charge_group_counts.items():
    print(f"  - {group}: {count}건 ({count/len(review_needed)*100:.1f}%)")

# Ref Rate 소스 분석
print("\n[Ref Rate 소스 분석]")
has_ref_rate = review_needed["Ref_Rate_USD"].notna().sum()
no_ref_rate = review_needed["Ref_Rate_USD"].isna().sum()
print(
    f"  - Ref Rate 있음: {has_ref_rate}건 ({has_ref_rate/len(review_needed)*100:.1f}%)"
)
print(
    f"  - Ref Rate 없음 (At Cost 등): {no_ref_rate}건 ({no_ref_rate/len(review_needed)*100:.1f}%)"
)

# Notes에서 소스 파악
notes_with_config = review_needed[
    review_needed["Validation_Notes"].str.contains("Config", na=False, case=False)
]
notes_with_pdf = review_needed[
    review_needed["Validation_Notes"].str.contains("PDF", na=False, case=False)
]
print(f"  - Config 소스: {len(notes_with_config)}건")
print(f"  - PDF 소스: {len(notes_with_pdf)}건")

# DESCRIPTION 카테고리 분석
print("\n[DESCRIPTION 카테고리 분석 - Top 10]")
desc_counts = review_needed["DESCRIPTION"].value_counts().head(10)
for i, (desc, count) in enumerate(desc_counts.items(), 1):
    print(f"  {i}. {desc[:60]}: {count}건")

# Top 10 REVIEW_NEEDED 항목 (Delta 큰 순)
print("\n[Top 10 REVIEW_NEEDED 항목 (Delta 큰 순서)]")
print("-" * 100)
review_with_delta_sorted = review_with_delta.sort_values(
    "Python_Delta", key=abs, ascending=False
).head(10)
for idx, row in review_with_delta_sorted.iterrows():
    print(f"\nOrder Ref: {row['Order Ref. Number']}")
    print(f"  DESCRIPTION: {row['DESCRIPTION']}")
    print(
        f"  RATE: {row['RATE']:.2f} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')} | Delta: {row['Python_Delta']:.2f}%"
    )
    print(
        f"  Charge Group: {row['Charge_Group']} | CG_Band: {row.get('CG_Band', 'N/A')}"
    )
    print(f"  Notes: {row['Validation_Notes'][:100]}")

# 2. FAIL 분석 (16건)
print("\n" + "=" * 100)
print("2. FAIL 상세 분석 (16건)")
print("=" * 100)

fail_items = df[df["Validation_Status"] == "FAIL"]
print(f"\nTotal FAIL: {len(fail_items)}건")

# 실패 원인 분류
print("\n[실패 원인 분류]")
fail_no_ref = fail_items[fail_items["Ref_Rate_USD"].isna()].shape[0]
fail_high_delta = fail_items[
    (fail_items["Ref_Rate_USD"].notna()) & (fail_items["Python_Delta"].abs() > 3)
].shape[0]
fail_other = len(fail_items) - fail_no_ref - fail_high_delta

print(
    f"  1. No Ref Rate (참조 요율 없음): {fail_no_ref}건 ({fail_no_ref/len(fail_items)*100:.1f}%)"
)
print(
    f"  2. High Delta (>3% 허용 오차 초과): {fail_high_delta}건 ({fail_high_delta/len(fail_items)*100:.1f}%)"
)
print(f"  3. Other: {fail_other}건")

# Charge Group 분포
print("\n[Charge Group 분포]")
fail_charge_group_counts = fail_items["Charge_Group"].value_counts()
for group, count in fail_charge_group_counts.items():
    print(f"  - {group}: {count}건 ({count/len(fail_items)*100:.1f}%)")

# CG_Band 분포
print("\n[CG_Band 분포]")
fail_cg_band_counts = fail_items["CG_Band"].value_counts()
for band, count in fail_cg_band_counts.items():
    print(f"  - {band}: {count}건 ({count/len(fail_items)*100:.1f}%)")

# 전체 FAIL 항목 리스트
print("\n[전체 FAIL 항목 상세 (16건)]")
print("=" * 100)
for idx, row in fail_items.iterrows():
    print(f"\n{row['No']}. Order Ref: {row['Order Ref. Number']}")
    print(f"   DESCRIPTION: {row['DESCRIPTION']}")
    print(f"   RATE: {row['RATE']:.2f} | Ref_Rate: {row.get('Ref_Rate_USD', 'N/A')}")
    if pd.notna(row.get("Python_Delta")):
        print(f"   Delta: {row['Python_Delta']:.2f}%")
    print(
        f"   Charge Group: {row['Charge_Group']} | CG_Band: {row.get('CG_Band', 'N/A')}"
    )
    print(
        f"   Gate Score: {row.get('Gate_Score', 'N/A')} | PDF Count: {row.get('PDF_Count', 0)}"
    )
    print(f"   Notes: {row['Validation_Notes']}")

# 3. 카테고리별 분류 (REVIEW_NEEDED + FAIL)
print("\n" + "=" * 100)
print("3. 카테고리별 분류 (REVIEW_NEEDED + FAIL)")
print("=" * 100)

issues = df[df["Validation_Status"].isin(["REVIEW_NEEDED", "FAIL"])]


# 키워드 기반 카테고리 분류
def categorize_description(desc):
    desc_upper = str(desc).upper()

    if any(
        kw in desc_upper
        for kw in ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]
    ):
        return "Transportation"
    elif any(kw in desc_upper for kw in ["CONTAINER", "CARRIER", "PORT CONTAINER"]):
        return "Container Fees"
    elif any(kw in desc_upper for kw in ["DOCUMENT", "DOCS", "PROCESSING FEE", "DPC"]):
        return "Documentation"
    elif any(
        kw in desc_upper for kw in ["GATE PASS", "INSPECTION", "CUSTOMS INSPECTION"]
    ):
        return "Gate/Inspection"
    elif any(kw in desc_upper for kw in ["APPOINTMENT", "TRUCK APPOINTMENT"]):
        return "Portal Fees"
    elif any(kw in desc_upper for kw in ["TERMINAL HANDLING", "THC"]):
        return "Terminal Handling"
    elif any(kw in desc_upper for kw in ["DO FEE", "DELIVERY ORDER"]):
        return "DO Fee"
    elif any(kw in desc_upper for kw in ["CUSTOMS CLEARANCE", "CLEARANCE FEE"]):
        return "Customs Clearance"
    elif any(kw in desc_upper for kw in ["OUTLAY", "DUTY"]):
        return "Duty/Outlay"
    else:
        return "Others"


issues["Category"] = issues["DESCRIPTION"].apply(categorize_description)

print("\n[REVIEW_NEEDED 카테고리 분포]")
review_cat_counts = review_needed.copy()
review_cat_counts["Category"] = review_cat_counts["DESCRIPTION"].apply(
    categorize_description
)
review_cat_distribution = review_cat_counts["Category"].value_counts()
for cat, count in review_cat_distribution.items():
    print(f"  - {cat}: {count}건 ({count/len(review_needed)*100:.1f}%)")

print("\n[FAIL 카테고리 분포]")
fail_cat_counts = fail_items.copy()
fail_cat_counts["Category"] = fail_cat_counts["DESCRIPTION"].apply(
    categorize_description
)
fail_cat_distribution = fail_cat_counts["Category"].value_counts()
for cat, count in fail_cat_distribution.items():
    print(f"  - {cat}: {count}건 ({count/len(fail_items)*100:.1f}%)")

# 4. 개선 기회 식별
print("\n" + "=" * 100)
print("4. 개선 기회 식별")
print("=" * 100)

print("\n[즉시 개선 가능 (Priority 1)]")

# No Ref Rate 항목 중 빈도 높은 것
no_ref_items = issues[issues["Ref_Rate_USD"].isna()]
no_ref_desc_counts = no_ref_items["DESCRIPTION"].value_counts().head(5)
print("\n고빈도 Ref Rate 미매칭 항목 (추가 Configuration 필요):")
for i, (desc, count) in enumerate(no_ref_desc_counts.items(), 1):
    print(f"  {i}. {desc}: {count}건")

# High Delta 항목
high_delta_items = issues[
    (issues["Ref_Rate_USD"].notna()) & (issues["Python_Delta"].abs() > 15)
]
high_delta_desc_counts = high_delta_items["DESCRIPTION"].value_counts().head(5)
print("\nHigh Delta 항목 (요율 재검토 필요):")
for i, (desc, count) in enumerate(high_delta_desc_counts.items(), 1):
    avg_delta = high_delta_items[high_delta_items["DESCRIPTION"] == desc][
        "Python_Delta"
    ].mean()
    print(f"  {i}. {desc}: {count}건 (평균 Delta: {avg_delta:.1f}%)")

print("\n[중기 개선 (Priority 2)]")
print("  - At Cost 항목의 자동 검증 로직 개발")
print("  - PDF 파싱 정확도 향상 (현재 PDF 소스: {len(notes_with_pdf)}건)")
print("  - Transportation 요율의 Lane Map 확장")

print("\n[장기 개선 (Priority 3)]")
print("  - AI 기반 요율 예측 모델")
print("  - 과거 데이터 학습을 통한 자동 요율 업데이트")
print("  - 실시간 시장 요율 연동")

# 5. 요약 통계
print("\n" + "=" * 100)
print("5. 요약 통계")
print("=" * 100)

print(f"\n전체 검증 항목: {len(df)}건")
print(
    f"  - PASS: {(df['Validation_Status'] == 'PASS').sum()}건 ({(df['Validation_Status'] == 'PASS').sum()/len(df)*100:.1f}%)"
)
print(
    f"  - REVIEW_NEEDED: {len(review_needed)}건 ({len(review_needed)/len(df)*100:.1f}%)"
)
print(f"  - FAIL: {len(fail_items)}건 ({len(fail_items)/len(df)*100:.1f}%)")

print("\n개선 필요 항목 요약:")
print(f"  - Ref Rate 미매칭: {issues['Ref_Rate_USD'].isna().sum()}건")
print(f"  - High Delta (|Delta| > 15%): {(issues['Python_Delta'].abs() > 15).sum()}건")
print(f"  - Contract 항목 중 이슈: {(issues['Charge_Group'] == 'Contract').sum()}건")

print("\n" + "=" * 100)
print("[분석 완료]")
print("=" * 100)
