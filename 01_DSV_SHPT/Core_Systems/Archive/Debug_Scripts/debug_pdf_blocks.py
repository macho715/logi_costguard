#!/usr/bin/env python3
"""
PDF 블록 구조 디버그 스크립트
"""
import sys
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent / "01_DSV_SHPT" / "Core_Systems"))

from hybrid_client import HybridDocClient
import logging

logging.basicConfig(level=logging.INFO)

# Initialize
client = HybridDocClient("http://localhost:8080")

# 테스트할 PDF
test_pdf = (
    Path(__file__).parent
    / "01_DSV_SHPT"
    / "Data"
    / "DSV 202509"
    / "SCNT Import (Sept 2025) - Supporting Documents"
    / "01. HVDC-ADOPT-SCT-0126"
    / "HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf"
)

print("=" * 80)
print(f"PDF: {test_pdf.name}")
print("=" * 80)
print()

# PDF 파싱
unified_ir = client.parse_pdf(str(test_pdf), "invoice")

if unified_ir:
    print("✅ 파싱 성공")
    print(f"   Engine: {unified_ir.get('engine')}")
    print(f"   Pages: {unified_ir.get('pages')}")
    print()

    # 블록 구조 출력
    blocks = unified_ir.get("blocks", [])
    print(f"📦 총 {len(blocks)}개 블록:")
    print()

    for i, block in enumerate(blocks, 1):
        print(f"[Block #{i}] Type: {block.get('type')}")

        if block.get("type") == "table":
            rows = block.get("rows", [])
            print(f"   Rows: {len(rows)}")
            if rows:
                print(f"   Header: {rows[0]}")
                print(f"   Sample (row 2): {rows[1] if len(rows) > 1 else 'N/A'}")

        elif block.get("type") == "text":
            text = block.get("text", "")
            lines = text.split("\n")[:5]
            print(f"   Lines: {len(text.split(chr(10)))}")
            print(f"   Sample (first 5 lines):")
            for line in lines:
                print(f"      {line[:80]}")

        print()

    # 전체 구조 JSON 출력 (파일 저장)
    output_file = Path(__file__).parent / "debug_unified_ir.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unified_ir, f, indent=2, ensure_ascii=False)

    print(f"💾 전체 구조 저장: {output_file.name}")

else:
    print("❌ 파싱 실패")

print("=" * 80)
