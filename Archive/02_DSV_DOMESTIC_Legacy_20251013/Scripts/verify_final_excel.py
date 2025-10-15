#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 Excel 파일 검증 스크립트
"""

import pandas as pd


def verify_final_excel():
    """최종 Excel 파일 구조 및 데이터 검증"""

    excel_file = "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION.xlsx"

    print("=" * 80)
    print("최종 Excel 파일 검증")
    print("=" * 80)
    print(f"\n📂 파일: {excel_file}")

    # Excel 파일 로드
    xl = pd.ExcelFile(excel_file)

    print(f"\n📋 시트 목록:")
    for i, sheet in enumerate(xl.sheet_names, 1):
        df = pd.read_excel(xl, sheet_name=sheet)
        print(f"  {i}. {sheet}: {len(df)} rows × {len(df.columns)} columns")

    # items 시트 상세
    print(f"\n" + "=" * 80)
    print("items 시트 상세")
    print("=" * 80)

    items_df = pd.read_excel(excel_file, sheet_name="items")

    print(f"\n총 행: {len(items_df)}")
    print(f"총 열: {len(items_df.columns)}")

    print(f"\n컬럼 리스트 ({len(items_df.columns)}개):")
    for i, col in enumerate(items_df.columns, 1):
        print(f"  {i:2d}. {col}")

    # PDF 검증 컬럼 확인
    pdf_columns = [col for col in items_df.columns if col.startswith("dn_")]
    print(f"\n✅ PDF 검증 컬럼 ({len(pdf_columns)}개):")
    for col in pdf_columns:
        print(f"  - {col}")

    # PDF 검증 통계
    print(f"\n📊 PDF 검증 통계:")
    if "dn_matched" in items_df.columns:
        yes_count = (items_df["dn_matched"] == "Yes").sum()
        no_count = (items_df["dn_matched"] == "No").sum()
        print(
            f"  DN 매칭 Yes: {yes_count}/{len(items_df)} ({yes_count/len(items_df)*100:.1f}%)"
        )
        print(
            f"  DN 매칭 No: {no_count}/{len(items_df)} ({no_count/len(items_df)*100:.1f}%)"
        )

        # 샘플 데이터
        print(f"\n샘플 데이터 (첫 3행):")
        sample_cols = [
            "origin",
            "destination",
            "vehicle",
            "dn_matched",
            "dn_shipment_ref",
            "dn_match_score",
        ]
        available_cols = [col for col in sample_cols if col in items_df.columns]
        print(items_df[available_cols].head(3).to_string())

    # DN_Validation 시트 확인
    print(f"\n" + "=" * 80)
    print("DN_Validation 시트 상세")
    print("=" * 80)

    dn_val_df = pd.read_excel(excel_file, sheet_name="DN_Validation")
    print(f"총 행: {len(dn_val_df)}")
    print(f"총 열: {len(dn_val_df.columns)}")
    print(f"\n컬럼 리스트:")
    for i, col in enumerate(dn_val_df.columns, 1):
        print(f"  {i}. {col}")

    print("\n" + "=" * 80)
    print("✅ 검증 완료!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        verify_final_excel()
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback

        traceback.print_exc()
