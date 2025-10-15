#!/usr/bin/env python3
"""좌표 + 테이블 추출 개선 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "hybrid_doc_system"))
from worker.celery_app import _extract_total_with_coordinates, _extract_total_from_table

# Test PDF
test_pdf = Path(
    "01_DSV_SHPT/Data/DSV 202509/SCNT Import (Sept 2025) - Supporting Documents/01. HVDC-ADOPT-SCT-0126/HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf"
)

print("[TEST 1] 좌표 기반 추출 (개선)")
result_coord = _extract_total_with_coordinates(test_pdf)
if result_coord:
    print(
        f"  [OK] ${result_coord['total_amount']:.2f} {result_coord['currency']} via {result_coord['extraction_method']}"
    )
else:
    print(f"  [FAIL] 추출 실패")

print("\n[TEST 2] 테이블 기반 추출 (신규)")
result_table = _extract_total_from_table(test_pdf)
if result_table:
    print(
        f"  [OK] ${result_table['total_amount']:.2f} {result_table['currency']} via {result_table['extraction_method']}"
    )
else:
    print(f"  [FAIL] 추출 실패")
