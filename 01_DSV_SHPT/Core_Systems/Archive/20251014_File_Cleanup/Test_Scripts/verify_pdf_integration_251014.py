#!/usr/bin/env python3
"""
PDF 검증 통합 확인
최종 보고서의 PDF_Count 및 검증 결과 확인
"""

import pandas as pd
from pathlib import Path


def main():
    print("=" * 80)
    print("PDF Validation Integration Verification")
    print("=" * 80)

    # 최신 검증 결과 로드
    result_file = Path(
        rPath(__file__).parent.parent / "Results"
    )

    df = pd.read_excel(result_file, sheet_name="MasterData_Validated")

    print(f"\n[PDF Integration Status]")
    print(f"Total items: {len(df)}")

    # PDF_Count 분석
    pdf_stats = df["PDF_Count"].describe()
    print(f"\nPDF_Count Statistics:")
    print(f"  Total with PDFs: {len(df[df['PDF_Count'] > 0])}")
    print(f"  Total without PDFs: {len(df[df['PDF_Count'] == 0])}")
    print(f"  Max PDFs per item: {df['PDF_Count'].max():.0f}")
    print(f"  Average PDFs: {df['PDF_Count'].mean():.2f}")

    # Shipment별 PDF 개수
    print(f"\n[PDF Count by Shipment]")
    shipment_pdf = (
        df.groupby("Order Ref. Number")["PDF_Count"]
        .first()
        .sort_values(ascending=False)
    )
    for shipment, count in list(shipment_pdf.items())[:10]:
        print(f"  {shipment}: {count:.0f} PDFs")

    # Gate Score 분석 (PDF 영향)
    print(f"\n[Gate Score Analysis]")
    print(f"  Average Gate Score: {df['Gate_Score'].mean():.1f}/100")
    print(f"  Gate PASS: {len(df[df['Gate_Status'] == 'PASS'])}/{len(df)}")

    # PDF가 있는 항목 vs 없는 항목 비교
    with_pdf = df[df["PDF_Count"] > 0]
    without_pdf = df[df["PDF_Count"] == 0]

    print(f"\n[PDF Impact on Gate Score]")
    if len(with_pdf) > 0:
        print(f"  With PDF ({len(with_pdf)} items):")
        print(f"    Avg Gate Score: {with_pdf['Gate_Score'].mean():.1f}")
        print(
            f"    Gate PASS: {len(with_pdf[with_pdf['Gate_Status'] == 'PASS'])}/{len(with_pdf)}"
        )

    if len(without_pdf) > 0:
        print(f"  Without PDF ({len(without_pdf)} items):")
        print(f"    Avg Gate Score: {without_pdf['Gate_Score'].mean():.1f}")
        print(
            f"    Gate PASS: {len(without_pdf[without_pdf['Gate_Status'] == 'PASS'])}/{len(without_pdf)}"
        )

    # Validation Notes에 PDF 정보 포함 확인
    print(f"\n[Validation Notes (PDF 관련)]")
    pdf_notes = df[df["Validation_Notes"].str.contains("PDF", na=False)]
    print(f"  Items with PDF in notes: {len(pdf_notes)}")

    if len(pdf_notes) > 0:
        print(f"\n  Sample notes:")
        for _, row in pdf_notes.head(5).iterrows():
            print(f"    - {row['DESCRIPTION'][:30]}: {row['Validation_Notes']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
