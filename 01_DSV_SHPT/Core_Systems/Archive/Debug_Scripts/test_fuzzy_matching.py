#!/usr/bin/env python3
"""
Fuzzy Matching 테스트
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

# Initialize
client = HybridDocClient("http://localhost:8080")
adapter = UnifiedIRAdapter()

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
print("Fuzzy Matching 테스트")
print("=" * 80)
print()

# PDF 파싱
unified_ir = client.parse_pdf(str(test_pdf), "invoice")

if unified_ir:
    # 이 PDF에 실제로 있는 항목 테스트
    test_categories = [
        "Container Return Service Charge",  # Exact
        "Container Return",  # Partial
        "Service Charge",  # Partial
        "RETURN SERVICE",  # Keyword
        "Container Charge",  # Fuzzy
    ]

    print("✅ 파싱 완료")
    print()

    for category in test_categories:
        print(f"🔍 검색: '{category}'")
        rate = adapter.extract_rate_for_category(unified_ir, category)
        if rate:
            print(f"   ✅ Found: {rate} AED")
        else:
            print(f"   ❌ Not found")
        print()

else:
    print("❌ 파싱 실패")

print("=" * 80)
