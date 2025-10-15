#!/usr/bin/env python3
"""
PDF Summary 추출 개선 효과 분석
Before/After 비교 - At Cost 및 전체 검증 결과

Created: 2025-10-15
Author: MACHO-GPT v3.4-mini PDF Summary Enhancement
"""

import pandas as pd
from pathlib import Path
import sys


def analyze_improvement():
    """
    PDF Summary 추출 개선 Before/After 비교
    """

    # 최신 검증 결과 로드
    out_dir = Path(__file__).parent / "out"
    csv_files = sorted(out_dir.glob("masterdata_validated_*.csv"))

    if len(csv_files) < 2:
        print("Error: 2개 이상의 검증 결과 파일이 필요합니다.")
        sys.exit(1)

    # Before (이전 버전) vs After (최신 버전)
    before_csv = csv_files[-2]
    after_csv = csv_files[-1]

    print("\n" + "=" * 80)
    print("PDF Summary 추출 개선 효과 분석")
    print("=" * 80)
    print(f"\nBefore: {before_csv.name}")
    print(f"After:  {after_csv.name}")

    df_before = pd.read_csv(before_csv)
    df_after = pd.read_csv(after_csv)

    # 1. 전체 검증 상태 비교
    print("\n" + "=" * 80)
    print("1. 전체 검증 상태 비교")
    print("=" * 80)

    print("\n[Before]")
    print(df_before["Validation_Status"].value_counts())

    print("\n[After]")
    print(df_after["Validation_Status"].value_counts())

    # Improvement 계산
    before_pass = (df_before["Validation_Status"] == "PASS").sum()
    after_pass = (df_after["Validation_Status"] == "PASS").sum()
    before_fail = (df_before["Validation_Status"] == "FAIL").sum()
    after_fail = (df_after["Validation_Status"] == "FAIL").sum()

    print(f"\nImprovement:")
    print(f"  PASS: {before_pass} -> {after_pass} (+{after_pass - before_pass})")
    print(f"  FAIL: {before_fail} -> {after_fail} ({after_fail - before_fail:+d})")

    # 2. At Cost 항목 상세 분석
    print("\n" + "=" * 80)
    print("2. At Cost 항목 상세 분석")
    print("=" * 80)

    # At Cost 필터링
    atcost_before = df_before[
        df_before["RATE SOURCE"].str.contains("AT COST|ATCOST", na=False, case=False)
    ]
    atcost_after = df_after[
        df_after["RATE SOURCE"].str.contains("AT COST|ATCOST", na=False, case=False)
    ]

    print(f"\nTotal At Cost items: {len(atcost_after)}")

    print("\n[Before]")
    print(atcost_before["Validation_Status"].value_counts())

    print("\n[After]")
    print(atcost_after["Validation_Status"].value_counts())

    # At Cost Improvement
    atcost_before_pass = (atcost_before["Validation_Status"] == "PASS").sum()
    atcost_after_pass = (atcost_after["Validation_Status"] == "PASS").sum()
    atcost_before_fail = (atcost_before["Validation_Status"] == "FAIL").sum()
    atcost_after_fail = (atcost_after["Validation_Status"] == "FAIL").sum()

    print(f"\nAt Cost Improvement:")
    print(
        f"  PASS: {atcost_before_pass} -> {atcost_after_pass} (+{atcost_after_pass - atcost_before_pass})"
    )
    print(
        f"  FAIL: {atcost_before_fail} -> {atcost_after_fail} ({atcost_after_fail - atcost_before_fail:+d})"
    )

    # 3. PDF 추출 성공률 비교
    print("\n" + "=" * 80)
    print("3. PDF 추출 성공률 비교")
    print("=" * 80)

    # PDF_Amount 추출 성공 건수
    before_pdf_success = df_before["PDF_Amount"].notna().sum()
    after_pdf_success = df_after["PDF_Amount"].notna().sum()

    print(f"\nPDF Amount 추출 성공:")
    print(
        f"  Before: {before_pdf_success}/{len(df_before)} ({before_pdf_success/len(df_before)*100:.1f}%)"
    )
    print(
        f"  After:  {after_pdf_success}/{len(df_after)} ({after_pdf_success/len(df_after)*100:.1f}%)"
    )
    print(
        f"  Improvement: +{after_pdf_success - before_pdf_success} items (+{(after_pdf_success - before_pdf_success)/len(df_after)*100:.1f}%)"
    )

    # 4. At Cost 항목별 상세 비교
    print("\n" + "=" * 80)
    print("4. At Cost 항목 상세 변화")
    print("=" * 80)

    # Order Ref로 조인
    atcost_before_indexed = atcost_before.set_index("Order Ref. Number")
    atcost_after_indexed = atcost_after.set_index("Order Ref. Number")

    for order_ref in atcost_after_indexed.index:
        if order_ref not in atcost_before_indexed.index:
            continue

        before_row = atcost_before_indexed.loc[order_ref]
        after_row = atcost_after_indexed.loc[order_ref]

        # 상태 변화가 있는 항목만 출력
        if before_row["Validation_Status"] != after_row["Validation_Status"]:
            print(f"\n[{order_ref}]")
            print(f"  Description: {after_row['DESCRIPTION']}")
            print(
                f"  Status: {before_row['Validation_Status']} -> {after_row['Validation_Status']}"
            )

            # PDF 추출 변화
            before_pdf = before_row.get("PDF_Amount")
            after_pdf = after_row.get("PDF_Amount")

            if pd.isna(before_pdf) and pd.notna(after_pdf):
                print(f"  PDF Amount: None -> ${after_pdf:.2f} (NEW EXTRACTION)")
            elif (
                pd.notna(before_pdf) and pd.notna(after_pdf) and before_pdf != after_pdf
            ):
                print(f"  PDF Amount: ${before_pdf:.2f} -> ${after_pdf:.2f} (IMPROVED)")

    # 5. Summary 통계
    print("\n" + "=" * 80)
    print("5. Summary")
    print("=" * 80)

    print(f"\n전체 개선 효과:")
    print(
        f"  Total PASS rate: {before_pass/len(df_before)*100:.1f}% -> {after_pass/len(df_after)*100:.1f}% ({(after_pass - before_pass)/len(df_after)*100:+.1f}%)"
    )
    print(
        f"  Total FAIL rate: {before_fail/len(df_before)*100:.1f}% -> {after_fail/len(df_after)*100:.1f}% ({(after_fail - before_fail)/len(df_after)*100:+.1f}%)"
    )

    print(f"\nAt Cost 개선 효과:")
    if len(atcost_after) > 0:
        print(
            f"  At Cost PASS rate: {atcost_before_pass/len(atcost_before)*100:.1f}% -> {atcost_after_pass/len(atcost_after)*100:.1f}% ({(atcost_after_pass - atcost_before_pass)/len(atcost_after)*100:+.1f}%)"
        )
        print(
            f"  At Cost FAIL rate: {atcost_before_fail/len(atcost_before)*100:.1f}% -> {atcost_after_fail/len(atcost_after)*100:.1f}% ({(atcost_after_fail - atcost_before_fail)/len(atcost_after)*100:+.1f}%)"
        )

    print(f"\nPDF 추출 개선 효과:")
    print(f"  추가 추출 항목: {after_pdf_success - before_pdf_success}개")
    print(
        f"  추출률 향상: {(after_pdf_success - before_pdf_success)/len(df_after)*100:.1f}%p"
    )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        analyze_improvement()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
