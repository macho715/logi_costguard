#!/usr/bin/env python3
"""
PDF Blocks 구조 디버그 - Summary 섹션 위치 확인

Created: 2025-10-15
"""

import sys
import json
from pathlib import Path

# Add parent directories to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))

from hybrid_client import HybridDocClient


def debug_pdf_blocks():
    """PDF blocks 구조 및 Summary 섹션 위치 확인"""

    print("\n" + "=" * 80)
    print("PDF Blocks Debug - Summary Section Analysis")
    print("=" * 80)

    # Initialize
    client = HybridDocClient("http://localhost:8080")

    # Test PDF
    pdf_path = (
        Path(__file__).parent.parent
        / "Data"
        / "DSV 202509"
        / "SCNT Import (Sept 2025) - Supporting Documents"
        / "01. HVDC-ADOPT-SCT-0126"
        / "HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf"
    )

    print(f"\nPDF: {pdf_path.name}")

    if not pdf_path.exists():
        print("PDF not found!")
        sys.exit(1)

    # Parse PDF
    print("\nParsing PDF...")
    unified_ir = client.parse_pdf(str(pdf_path), "invoice")

    if not unified_ir:
        print("PDF parsing failed!")
        sys.exit(1)

    print(f"  Engine: {unified_ir.get('engine')}")
    print(f"  Pages: {unified_ir.get('pages')}")

    blocks = unified_ir.get("blocks", [])
    print(f"  Total Blocks: {len(blocks)}")

    # 각 블록 구조 확인
    print("\n" + "=" * 80)
    print("Block Structure Analysis")
    print("=" * 80)

    for idx, block in enumerate(blocks, 1):
        block_type = block.get("type", "unknown")
        print(f"\n[Block {idx}] Type: {block_type}")

        if block_type == "text":
            text = block.get("text", "")
            print(f"  Text length: {len(text)} chars")
            # Show first 200 chars
            print(f"  Preview: {text[:200]}...")

            # TOTAL 키워드 검색
            if "TOTAL" in text.upper():
                print(f"  CONTAINS 'TOTAL' keyword")
                # TOTAL 주변 텍스트 출력
                total_pos = text.upper().find("TOTAL")
                context_start = max(0, total_pos - 50)
                context_end = min(len(text), total_pos + 100)
                print(f"  Context: ...{text[context_start:context_end]}...")

        elif block_type == "table":
            # rows 접근
            if "table" in block and isinstance(block["table"], dict):
                rows = block.get("table", {}).get("rows", [])
            else:
                rows = block.get("rows", [])

            print(f"  Rows: {len(rows)}")

            # 마지막 3행 출력 (Summary 위치)
            if rows and len(rows) > 0:
                print(f"  Last 3 rows:")
                for row_idx, row in enumerate(rows[-3:], start=len(rows) - 2):
                    print(f"    Row {row_idx}: {row}")

    # Full text 추출 및 TOTAL 검색
    print("\n" + "=" * 80)
    print("Full Text Analysis - TOTAL Keyword Search")
    print("=" * 80)

    from unified_ir_adapter import UnifiedIRAdapter

    adapter = UnifiedIRAdapter()
    full_text = adapter._extract_full_text(blocks)

    print(f"\nFull text length: {len(full_text)} chars")

    # TOTAL 키워드 위치 찾기
    import re

    total_matches = list(re.finditer(r"(TOTAL|Total)", full_text, re.IGNORECASE))
    print(f"\nFound {len(total_matches)} 'TOTAL' occurrences:")

    for i, match in enumerate(total_matches[:10], 1):  # 처음 10개만
        start = match.start()
        end = match.end()
        context_start = max(0, start - 30)
        context_end = min(len(full_text), end + 50)

        context = full_text[context_start:context_end]
        print(f"\n  [{i}] Position {start}-{end}:")
        print(f"      ...{context}...")

    print("\n" + "=" * 80)

    # Save full JSON for detailed inspection
    json_path = Path(__file__).parent / "out" / "debug_unified_ir.json"
    json_path.parent.mkdir(exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(unified_ir, f, indent=2, ensure_ascii=False)

    print(f"\nFull Unified IR saved to: {json_path.name}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        debug_pdf_blocks()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
