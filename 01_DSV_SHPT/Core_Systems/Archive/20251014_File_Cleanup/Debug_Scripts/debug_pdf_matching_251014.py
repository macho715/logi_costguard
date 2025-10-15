#!/usr/bin/env python3
"""
PDF 매칭 디버깅 - 미매칭 25개 항목 상세 분석
"""

import pandas as pd
from pathlib import Path


def normalize(text):
    """정규화"""
    return text.replace(" ", "").replace(",", "").lower()


def main():
    # 최신 검증 결과
    result_csv = Path(
        r"C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\01_DSV_SHPT\Core_Systems\out\masterdata_validated_20251014_202550.csv"
    )
    df = pd.read_csv(result_csv)

    # Supporting Docs
    pdf_dir = Path(
        r"C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\01_DSV_SHPT\Data\DSV 202509\SCNT Import (Sept 2025) - Supporting Documents"
    )

    # 미매칭 항목
    no_pdf = df[df["PDF_Count"] == 0]
    no_pdf_refs = no_pdf["Order Ref. Number"].unique()

    print("=" * 80)
    print("PDF Matching Debug - Unmatched Items")
    print("=" * 80)

    print(
        f"\n[Unmatched Items]: {len(no_pdf)} items, {len(no_pdf_refs)} unique shipments"
    )

    # 각 미매칭 Shipment에 대해 디렉토리 찾기 시도
    for ref in sorted(no_pdf_refs):
        print(f"\n{ref}:")
        print(f"  Normalized: '{normalize(ref)}'")

        # 디렉토리 검색
        found = False
        for subdir in pdf_dir.iterdir():
            if subdir.is_dir():
                # 정확한 매칭
                if ref in subdir.name:
                    print(f"  EXACT MATCH: {subdir.name}")
                    found = True
                    break

                # 정규화 매칭
                if normalize(ref) in normalize(subdir.name):
                    print(f"  NORMALIZED MATCH: {subdir.name}")
                    found = True
                    break

        if not found:
            print(f"  NO MATCH")
            # 유사한 디렉토리 찾기
            ref_core = (
                ref.split("-")[-1] if "-" in ref else ref
            )  # "HE-0499(LOT1)" → "0499(LOT1)"
            print(f"  Searching for similar (core: '{ref_core}')...")
            for subdir in pdf_dir.iterdir():
                if subdir.is_dir() and ref_core[:8] in subdir.name:
                    print(f"    SIMILAR: {subdir.name}")

    # 모든 디렉토리 목록 (참고용)
    print(f"\n[All Directories in Supporting Docs]")
    dirs = sorted([d.name for d in pdf_dir.iterdir() if d.is_dir()])
    for d in dirs:
        print(f"  {d}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
