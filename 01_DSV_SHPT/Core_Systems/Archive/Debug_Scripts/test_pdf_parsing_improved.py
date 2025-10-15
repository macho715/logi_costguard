#!/usr/bin/env python3
"""
개선된 PDF 파싱 테스트 (pdfplumber + Fuzzy Matching)
"""
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent / "01_DSV_SHPT" / "Core_Systems"))

from hybrid_client import HybridDocClient
from unified_ir_adapter import UnifiedIRAdapter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize
client = HybridDocClient("http://localhost:8080")
adapter = UnifiedIRAdapter()

# 테스트할 PDF 선택
test_pdf = (
    Path(__file__).parent
    / "01_DSV_SHPT"
    / "Data"
    / "DSV 202509"
    / "SCNT Import (Sept 2025) - Supporting Documents"
    / "01. HVDC-ADOPT-SCT-0126"
    / "HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf"
)

if not test_pdf.exists():
    print(f"❌ PDF not found: {test_pdf}")
    sys.exit(1)

print("=" * 80)
print(f"테스트 PDF: {test_pdf.name}")
print("=" * 80)
print()

# 1. PDF 업로드 및 파싱
print("1️⃣ Hybrid Client로 PDF 파싱...")
unified_ir = client.parse_pdf(str(test_pdf), "invoice")

if unified_ir:
    print(f"✅ 파싱 성공")
    print(f"   Engine: {unified_ir.get('engine')}")
    print(f"   Pages: {unified_ir.get('pages')}")
    print(f"   Blocks: {len(unified_ir.get('blocks', []))}")
    print()

    # 2. Invoice 데이터 추출
    print("2️⃣ UnifiedIRAdapter로 Invoice 데이터 추출...")
    invoice_data = adapter.extract_invoice_data(unified_ir)

    print(f"   Invoice No: {invoice_data.get('invoice_no', 'N/A')}")
    print(f"   Order Ref: {invoice_data.get('order_ref', 'N/A')}")
    print(f"   Total Amount: {invoice_data.get('total_amount', 'N/A')}")
    print(f"   Currency: {invoice_data.get('currency', 'N/A')}")
    print(f"   Items: {len(invoice_data.get('items', []))}")
    print()

    # 3. Items 상세 출력
    if invoice_data.get("items"):
        print("3️⃣ 추출된 Items (상위 10개):")
        for i, item in enumerate(invoice_data["items"][:10], 1):
            print(f"   [{i}] {item.get('description', 'N/A')[:60]}")
            print(
                f"       Qty: {item.get('qty', 0)}, Rate: {item.get('unit_rate', 0)}, Amount: {item.get('amount', 0)}"
            )
        print()

    # 4. Rate 추출 테스트
    print("4️⃣ Rate 추출 테스트 (Fuzzy Matching)...")
    test_categories = [
        "TERMINAL HANDLING FEE",
        "INLAND TRUCKING",
        "DO FEE",
        "CUSTOMS CLEARANCE",
    ]

    for category in test_categories:
        rate = adapter.extract_rate_for_category(unified_ir, category)
        if rate:
            print(f"   ✅ {category}: {rate} USD")
        else:
            print(f"   ❌ {category}: Not found")
    print()

else:
    print("❌ 파싱 실패")

print("=" * 80)
