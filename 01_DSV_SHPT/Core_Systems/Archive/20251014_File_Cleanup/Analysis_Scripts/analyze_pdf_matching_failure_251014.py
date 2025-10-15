#!/usr/bin/env python3
"""
PDF 매칭 실패 원인 분석
"""

import pandas as pd
from pathlib import Path


def main():
    print("=" * 80)
    print("PDF Matching Failure Analysis")
    print("=" * 80)

    # 1. MasterData 로드
    excel_file = Path(
        rPath(__file__).parent.parent / "Data" / "DSV 202509" / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
    )
    df = pd.read_excel(excel_file, sheet_name="MasterData")

    # 2. Supporting Docs 디렉토리
    pdf_dir = Path(
        rPath(__file__).parent.parent / "SCNT Import (Sept 2025) - Supporting Documents"
    )

    # 3. 매칭 결과 로드
    result_csv = (
        Path(__file__).parent / "out" / "masterdata_validated_20251014_202043.csv"
    )
    df_result = pd.read_csv(result_csv)

    # 4. 매칭 실패 항목 분석
    no_pdf = df_result[df_result["PDF_Count"] == 0]
    with_pdf = df_result[df_result["PDF_Count"] > 0]

    print(f"\n[Matching Results]")
    print(f"  With PDF: {len(with_pdf)} ({len(with_pdf)/len(df_result)*100:.1f}%)")
    print(f"  Without PDF: {len(no_pdf)} ({len(no_pdf)/len(df_result)*100:.1f}%)")

    # 5. 매칭 실패 항목의 Order Ref. Number 확인
    print(f"\n[Items Without PDF]")
    no_pdf_refs = no_pdf["Order Ref. Number"].unique()
    print(f"Unique Shipment IDs without PDF: {len(no_pdf_refs)}")
    for ref in sorted(no_pdf_refs):
        count = len(no_pdf[no_pdf["Order Ref. Number"] == ref])
        print(f"  {ref}: {count} items")

    # 6. 실제 디렉토리 확인
    print(f"\n[Actual Directories in Supporting Docs]")
    dirs = [d for d in pdf_dir.iterdir() if d.is_dir()]
    print(f"Total directories: {len(dirs)}")
    for d in sorted(dirs, key=lambda x: x.name)[:15]:
        pdf_count = len(list(d.glob("*.pdf")))
        print(f"  {d.name}: {pdf_count} PDFs")

    # 7. 매칭 테스트
    print(f"\n[Matching Test]")
    for ref in no_pdf_refs[:5]:
        print(f"\nTesting: '{ref}'")
        matched = False
        for subdir in pdf_dir.iterdir():
            if subdir.is_dir():
                if ref in subdir.name:
                    print(f"  MATCH: {subdir.name}")
                    matched = True
                    break
        if not matched:
            print(f"  NO MATCH - checking similar...")
            # 부분 매칭 시도
            ref_clean = ref.replace(" ", "").replace(",", "")
            for subdir in pdf_dir.iterdir():
                if subdir.is_dir():
                    dir_clean = subdir.name.replace(" ", "").replace(",", "")
                    if ref_clean in dir_clean or ref[:20] in subdir.name:
                        print(f"  SIMILAR: {subdir.name}")
                        break

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
