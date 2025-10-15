#!/usr/bin/env python3
"""At Cost PDF 파싱 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hybrid_client import HybridDocClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from unified_ir_adapter import UnifiedIRAdapter

# Hybrid Client 초기화
client = HybridDocClient("http://localhost:8080")
adapter = UnifiedIRAdapter()

# 테스트할 PDF 경로
pdf_path = (
    Path(__file__).parent.parent
    / "Data"
    / "DSV 202509"
    / "SCNT Import (Sept 2025) - Supporting Documents"
    / "01. HVDC-ADOPT-SCT-0126"
    / "HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf"
)

print(f"\n{'='*80}")
print(f"At Cost PDF Parsing Test")
print(f"{'='*80}")
print(f"\nPDF: {pdf_path.name}")
print(f"Exists: {pdf_path.exists()}")

if not pdf_path.exists():
    print("PDF not found!")
    sys.exit(1)

# PDF 파싱
print(f"\n파싱 중...")
unified_ir = client.parse_pdf(str(pdf_path), "invoice")

if not unified_ir:
    print("파싱 실패!")
    sys.exit(1)

print(f"\nEngine: {unified_ir.get('engine')}")
print(f"Pages: {unified_ir.get('pages')}")
print(f"Blocks: {len(unified_ir.get('blocks', []))}")

# At Cost 항목들 추출 테스트
test_categories = [
    "CARRIER CONTAINER RETURN SERVICE FEE",
    "PORT CONTAINER ADMIN/INSPECTION FEE",
    "ISPS IMPORT FEE",
    "CARRIER CONTAINER MAINTENANCE FEE",
]

print(f"\n{'='*80}")
print(f"At Cost 항목 추출 테스트")
print(f"{'='*80}")

for category in test_categories:
    print(f"\n[Category] {category}")

    # 라인 아이템 추출
    line_item = adapter.extract_invoice_line_item(unified_ir, category)

    if line_item:
        print(f"  ✓ Found!")
        print(f"    Description: {line_item['description']}")
        print(f"    Qty: {line_item['qty']}")
        print(f"    Unit Rate: ${line_item['unit_rate']:.2f}")
        print(f"    Amount: ${line_item['amount']:.2f}")
        print(f"    Matched by: {line_item['matched_by']}")
    else:
        print(f"  ✗ Not found")

print(f"\n{'='*80}")
