#!/usr/bin/env python3
"""
Hybrid System PDF 파싱 간단 테스트
Summary 추출 로직 검증

Created: 2025-10-15
"""

import sys
from pathlib import Path

# Add parent directories to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))

from hybrid_client import HybridDocClient
from unified_ir_adapter import UnifiedIRAdapter


def test_hybrid_pdf_parsing():
    """Hybrid System PDF 파싱 및 Summary 추출 테스트"""

    print("\n" + "=" * 80)
    print("Hybrid System PDF Parsing Test")
    print("=" * 80)

    # Initialize
    client = HybridDocClient("http://localhost:8080")
    adapter = UnifiedIRAdapter()

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
    print(f"Exists: {pdf_path.exists()}")

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
    print(f"  Blocks: {len(unified_ir.get('blocks', []))}")

    # Extract Invoice Data
    print("\nExtracting Invoice Data...")
    invoice_data = adapter.extract_invoice_data(unified_ir)

    print(f"  Total Amount: ${invoice_data.get('total_amount', 0):.2f}")
    print(f"  Subtotal: ${invoice_data.get('subtotal', 0):.2f}")
    print(f"  VAT: ${invoice_data.get('vat', 0):.2f}")
    print(f"  Exchange Rate: {invoice_data.get('exchange_rate', 'N/A')}")
    print(f"  Items Count: {len(invoice_data.get('items', []))}")

    # Show first 5 items
    items = invoice_data.get("items", [])
    if items:
        print("\n  Items (first 5):")
        for i, item in enumerate(items[:5], 1):
            print(f"    {i}. {item.get('description')}: ${item.get('amount', 0):.2f}")

    # Test Summary extraction
    print("\n" + "=" * 80)
    print("Summary Section Test")
    print("=" * 80)

    summary = adapter._extract_summary_section(unified_ir.get("blocks", []))
    print(f"\nExtracted Summary: {summary}")

    if summary.get("total"):
        print(f"  SUCCESS: TOTAL = ${summary['total']:.2f}")
    else:
        print(f"  WARNING: TOTAL not extracted")

    # Test Line Item extraction for At Cost categories
    print("\n" + "=" * 80)
    print("At Cost Line Item Extraction Test")
    print("=" * 80)

    at_cost_categories = [
        "CARRIER CONTAINER RETURN SERVICE FEE",
        "PORT CONTAINER ADMIN/INSPECTION FEE",
        "ISPS IMPORT FEE",
    ]

    for category in at_cost_categories:
        print(f"\n[Category] {category}")
        line_item = adapter.extract_invoice_line_item(unified_ir, category)

        if line_item:
            print(f"  Amount: ${line_item.get('amount', 0):.2f}")
            print(f"  Qty: {line_item.get('qty', 1)}")
            print(f"  Unit Rate: ${line_item.get('unit_rate', 0):.2f}")
            print(f"  Matched by: {line_item.get('matched_by')}")
        else:
            print(f"  Not found")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_hybrid_pdf_parsing()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
