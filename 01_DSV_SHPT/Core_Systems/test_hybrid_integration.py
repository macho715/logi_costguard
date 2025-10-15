#!/usr/bin/env python3
"""
Hybrid Integration Unit Tests
hybrid_client.py + unified_ir_adapter.py 테스트

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))

from hybrid_client import HybridDocClient
from unified_ir_adapter import UnifiedIRAdapter


class TestUnifiedIRAdapter(unittest.TestCase):
    """UnifiedIRAdapter 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.adapter = UnifiedIRAdapter()

        # Sample Unified IR
        self.sample_ir = {
            "doc_id": "test-invoice.pdf",
            "engine": "docling",
            "pages": 2,
            "blocks": [
                {
                    "type": "text",
                    "text": "Invoice No: INV-12345\nOrder Ref: SCT-0126\nTotal Amount: 21,402.20 USD",
                },
                {
                    "type": "table",
                    "table": {
                        "rows": [
                            ["Description", "Qty", "Unit Rate", "Amount"],
                            ["INLAND TRUCKING", "1", "252.00", "252.00"],
                            ["DO FEE", "1", "150.00", "150.00"],
                            ["CUSTOMS CLEARANCE", "1", "150.00", "150.00"],
                        ]
                    },
                },
            ],
            "meta": {"confidence": 0.92, "filename": "test.pdf"},
        }

    def test_extract_invoice_no(self):
        """Invoice No 추출 테스트"""
        result = self.adapter.extract_invoice_data(self.sample_ir)

        self.assertEqual(result["invoice_no"], "INV-12345")

    def test_extract_order_ref(self):
        """Order Ref 추출 테스트"""
        result = self.adapter.extract_invoice_data(self.sample_ir)

        self.assertEqual(result["order_ref"], "SCT-0126")

    def test_extract_total_amount(self):
        """Total Amount 추출 테스트"""
        result = self.adapter.extract_invoice_data(self.sample_ir)

        self.assertEqual(result["total_amount"], 21402.20)

    def test_extract_currency(self):
        """Currency 추출 테스트"""
        result = self.adapter.extract_invoice_data(self.sample_ir)

        self.assertEqual(result["currency"], "USD")

    def test_extract_table_items(self):
        """테이블 항목 추출 테스트"""
        result = self.adapter.extract_invoice_data(self.sample_ir)

        items = result["items"]
        self.assertEqual(len(items), 3)

        # First item
        self.assertEqual(items[0]["description"], "INLAND TRUCKING")
        self.assertEqual(items[0]["qty"], 1.0)
        self.assertEqual(items[0]["unit_rate"], 252.00)
        self.assertEqual(items[0]["amount"], 252.00)

    def test_extract_rate_for_category(self):
        """Category별 요율 추출 테스트"""
        rate = self.adapter.extract_rate_for_category(self.sample_ir, "DO FEE")

        self.assertEqual(rate, 150.00)

    def test_extract_rate_for_category_not_found(self):
        """존재하지 않는 Category 테스트"""
        rate = self.adapter.extract_rate_for_category(self.sample_ir, "NONEXISTENT")

        self.assertIsNone(rate)

    def test_get_confidence_score(self):
        """신뢰도 점수 계산 테스트"""
        confidence = self.adapter.get_confidence_score(self.sample_ir)

        self.assertGreaterEqual(confidence, 0.92)
        self.assertLessEqual(confidence, 1.0)

    def test_extract_boe_data(self):
        """BOE 데이터 추출 테스트"""
        boe_ir = {
            "doc_id": "test-boe.pdf",
            "engine": "ade",
            "blocks": [
                {
                    "type": "text",
                    "text": "BOE No: BOE-67890\nCustoms Value: 10,000.00 USD\nDuty: 500.00 USD",
                }
            ],
        }

        result = self.adapter.extract_boe_data(boe_ir)

        self.assertEqual(result["doc_type"], "boe")
        self.assertEqual(result["boe_no"], "BOE-67890")
        self.assertEqual(result["customs_value"], 10000.00)
        self.assertEqual(result["duty_amount"], 500.00)

    def test_number_parsing_with_commas(self):
        """쉼표 포함 숫자 파싱 테스트"""
        self.assertEqual(self.adapter._parse_number("21,402.20"), 21402.20)
        self.assertEqual(self.adapter._parse_number("1,234"), 1234.0)
        self.assertEqual(self.adapter._parse_number("252.00"), 252.00)

    def test_number_parsing_edge_cases(self):
        """숫자 파싱 엣지 케이스 테스트"""
        self.assertEqual(self.adapter._parse_number("-"), 0.0)
        self.assertEqual(self.adapter._parse_number("N/A"), 0.0)
        self.assertEqual(self.adapter._parse_number(""), 0.0)
        self.assertEqual(self.adapter._parse_number("invalid", default=99.0), 99.0)


class TestHybridDocClient(unittest.TestCase):
    """HybridDocClient 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.client = HybridDocClient(
            api_url="http://localhost:8080", timeout=30, enable_cache=True
        )

    @patch("hybrid_client.requests.post")
    def test_upload_pdf_success(self, mock_post):
        """PDF 업로드 성공 테스트"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"task_id": "test-task-123"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create temporary test file
        test_file = Path("test_sample.pdf")
        test_file.write_text("dummy pdf content")

        try:
            task_id = self.client._upload_pdf(test_file, "invoice")
            self.assertEqual(task_id, "test-task-123")
        finally:
            if test_file.exists():
                test_file.unlink()

    @patch("hybrid_client.requests.get")
    def test_poll_result_completed(self, mock_get):
        """폴링 완료 테스트"""
        # Mock completed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "completed",
            "result": {
                "doc_id": "test.pdf",
                "engine": "docling",
                "blocks": [],
            },
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.client._poll_result("test-task-123")

        self.assertEqual(result["doc_id"], "test.pdf")
        self.assertEqual(result["engine"], "docling")

    @patch("hybrid_client.requests.get")
    def test_poll_result_failed(self, mock_get):
        """폴링 실패 테스트"""
        # Mock failed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "failed",
            "error": "PDF corrupted",
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.client._poll_result("test-task-123")

        self.assertIn("Parsing failed", str(context.exception))

    @patch("hybrid_client.requests.get")
    def test_check_service_health_success(self, mock_get):
        """서비스 헬스 체크 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_healthy = self.client.check_service_health()

        self.assertTrue(is_healthy)

    @patch("hybrid_client.requests.get")
    def test_check_service_health_failure(self, mock_get):
        """서비스 헬스 체크 실패 테스트"""
        mock_get.side_effect = Exception("Connection refused")

        is_healthy = self.client.check_service_health()

        self.assertFalse(is_healthy)

    def test_cache_functionality(self):
        """캐싱 기능 테스트"""
        # Add to cache
        cache_key = "test.pdf_invoice"
        test_ir = {"doc_id": "test.pdf", "blocks": []}

        self.client.cache[cache_key] = test_ir

        # Check cache size
        self.assertEqual(len(self.client.cache), 1)
        self.assertEqual(self.client.cache[cache_key]["doc_id"], "test.pdf")


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def setUp(self):
        """통합 테스트 초기화"""
        self.client = HybridDocClient(api_url="http://localhost:8080")
        self.adapter = UnifiedIRAdapter()

    def test_end_to_end_flow(self):
        """End-to-End 플로우 테스트 (Mock)"""

        # Mock Unified IR from Hybrid API
        mock_unified_ir = {
            "doc_id": "SCT-0126-Invoice.pdf",
            "engine": "ade",
            "pages": 3,
            "blocks": [
                {
                    "type": "text",
                    "text": "Invoice No: DSV-2025-09-001\nOrder Ref: SCT-0126",
                },
                {
                    "type": "table",
                    "table": {
                        "rows": [
                            ["Description", "Qty", "Unit Rate", "Amount"],
                            [
                                "INLAND TRUCKING FROM KP TO DSV YARD",
                                "1",
                                "252.00",
                                "252.00",
                            ],
                        ]
                    },
                },
            ],
            "meta": {"confidence": 0.95},
        }

        # Extract HVDC data
        hvdc_data = self.adapter.extract_invoice_data(mock_unified_ir)

        # Assertions
        self.assertEqual(hvdc_data["invoice_no"], "DSV-2025-09-001")
        self.assertEqual(hvdc_data["order_ref"], "SCT-0126")
        self.assertEqual(len(hvdc_data["items"]), 1)
        self.assertEqual(hvdc_data["items"][0]["unit_rate"], 252.00)
        self.assertEqual(hvdc_data["engine_used"], "ade")
        self.assertGreaterEqual(hvdc_data["confidence"], 0.95)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
