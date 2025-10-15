#!/usr/bin/env python3
"""
PDF Integration 통합 테스트
===========================

Invoice Audit 시스템과 PDF 파싱 통합 기능 테스트

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

import pytest
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))

try:
    from invoice_pdf_integration import InvoicePDFIntegration
    from pdf_integration import DSVPDFParser, CrossDocValidator, OntologyMapper

    INTEGRATION_OK = True
except ImportError:
    INTEGRATION_OK = False
    print("Warning: PDF Integration modules not available")


class TestPDFIntegration:
    """PDF Integration 기능 테스트"""

    @pytest.fixture
    def integration_layer(self):
        """InvoicePDFIntegration fixture"""
        if not INTEGRATION_OK:
            pytest.skip("PDF Integration not available")
        return InvoicePDFIntegration()

    @pytest.fixture
    def sample_invoice_item(self):
        """샘플 Invoice 항목"""
        return {
            "s_no": 5,
            "sheet_name": "SCT0126",
            "description": "TRANSPORTATION CHARGES FROM KHALIFA PORT TO DSV YARD",
            "rate_source": "CONTRACT",
            "unit_rate": 252.00,
            "quantity": 3,
            "total_usd": 756.00,
            "formula_text": "",
        }

    @pytest.fixture
    def sample_pdf_files(self):
        """샘플 PDF 파일 리스트"""
        return [
            {
                "file_name": "HVDC-ADOPT-SCT-0126_BOE.pdf",
                "file_path": "test/path/BOE.pdf",
                "doc_type": "BOE",
                "file_size": 1024,
            },
            {
                "file_name": "HVDC-ADOPT-SCT-0126_DO.pdf",
                "file_path": "test/path/DO.pdf",
                "doc_type": "DO",
                "file_size": 2048,
            },
        ]

    def test_should_initialize_integration_layer(self, integration_layer):
        """통합 레이어가 초기화되어야 함"""
        assert integration_layer is not None
        assert integration_layer.pdf_parser is not None
        assert integration_layer.doc_validator is not None
        assert integration_layer.ontology_mapper is not None

    def test_should_have_pdf_gates(self, integration_layer):
        """PDF Gates (Gate-11~14)가 구현되어야 함"""
        # Mock PDF 데이터
        mock_pdf_data = {
            "shipment_id": "HVDC-ADOPT-SCT-0126",
            "parsed_count": 2,
            "documents": [
                {
                    "header": {"doc_type": "BOE"},
                    "data": {
                        "mbl_no": "CHN2595234",
                        "containers": ["CMAU2623154", "TGHU8788690"],
                        "gross_weight_kg": 53125.7,
                        "hs_code": "9405500000",
                        "description": "Luminaires",
                    },
                },
                {
                    "header": {"doc_type": "DO"},
                    "data": {
                        "mbl_no": "CHN2595234",
                        "containers": [
                            {"container_no": "CMAU2623154"},
                            {"container_no": "TGHU8788690"},
                        ],
                        "weight_kg": 53125.7,
                    },
                },
            ],
        }

        invoice_item = {}

        result = integration_layer.run_pdf_gates(invoice_item, mock_pdf_data)

        assert result is not None
        assert "Gate_Status" in result
        assert "Gate_Score" in result
        assert "Gate_Details" in result

        # Gate-11~14 확인
        gate_names = [g["gate"] for g in result["Gate_Details"]]
        assert "Gate-11" in gate_names, "Gate-11 (MBL Consistency) missing"
        assert "Gate-12" in gate_names, "Gate-12 (Container Consistency) missing"
        assert "Gate-13" in gate_names, "Gate-13 (Weight Consistency) missing"
        assert "Gate-14" in gate_names, "Gate-14 (Certification Check) missing"

    def test_gate_11_should_pass_on_consistent_mbl(self, integration_layer):
        """Gate-11: 일치하는 MBL은 PASS"""
        pdf_data = {
            "documents": [
                {"header": {"doc_type": "BOE"}, "data": {"mbl_no": "CHN2595234"}},
                {"header": {"doc_type": "DO"}, "data": {"mbl_no": "CHN2595234"}},
            ]
        }

        result = integration_layer._gate_11_mbl_consistency({}, pdf_data)

        assert result["result"] == "PASS"
        assert result["score"] == 100

    def test_gate_11_should_fail_on_mbl_mismatch(self, integration_layer):
        """Gate-11: 불일치하는 MBL은 FAIL"""
        pdf_data = {
            "documents": [
                {"header": {"doc_type": "BOE"}, "data": {"mbl_no": "CHN2595234"}},
                {
                    "header": {"doc_type": "DO"},
                    "data": {"mbl_no": "CHN9999999"},  # 불일치!
                },
            ]
        }

        result = integration_layer._gate_11_mbl_consistency({}, pdf_data)

        assert result["result"] == "FAIL"
        assert result["score"] == 0

    def test_gate_12_should_pass_on_consistent_containers(self, integration_layer):
        """Gate-12: 일치하는 Container는 PASS"""
        pdf_data = {
            "documents": [
                {
                    "header": {"doc_type": "BOE"},
                    "data": {"containers": ["CMAU2623154", "TGHU8788690"]},
                },
                {
                    "header": {"doc_type": "DO"},
                    "data": {
                        "containers": [
                            {"container_no": "CMAU2623154"},
                            {"container_no": "TGHU8788690"},
                        ]
                    },
                },
            ]
        }

        result = integration_layer._gate_12_container_consistency(pdf_data)

        assert result["result"] == "PASS"
        assert result["score"] == 100

    def test_gate_13_should_pass_within_tolerance(self, integration_layer):
        """Gate-13: ±3% 이내 Weight는 PASS"""
        pdf_data = {
            "documents": [
                {"header": {"doc_type": "BOE"}, "data": {"gross_weight_kg": 1000.0}},
                {
                    "header": {"doc_type": "DO"},
                    "data": {"weight_kg": 1025.0},  # 2.5% 차이
                },
            ]
        }

        result = integration_layer._gate_13_weight_consistency(pdf_data)

        assert result["result"] == "PASS"
        assert result["score"] == 100

    def test_gate_13_should_fail_exceeding_tolerance(self, integration_layer):
        """Gate-13: ±3% 초과 Weight는 FAIL"""
        pdf_data = {
            "documents": [
                {"header": {"doc_type": "BOE"}, "data": {"gross_weight_kg": 1000.0}},
                {
                    "header": {"doc_type": "DO"},
                    "data": {"weight_kg": 1050.0},  # 5% 차이
                },
            ]
        }

        result = integration_layer._gate_13_weight_consistency(pdf_data)

        assert result["result"] == "FAIL"
        assert result["score"] < 100

    def test_gate_14_should_detect_missing_moiat_cert(self, integration_layer):
        """Gate-14: MOIAT 인증 누락 감지"""
        pdf_data = {
            "documents": [
                {
                    "header": {"doc_type": "BOE"},
                    "data": {
                        "hs_code": "8544601000",  # Electrical - MOIAT 필요
                        "description": "High voltage power cables",
                    },
                }
            ]
        }

        result = integration_layer._gate_14_certification_check(pdf_data)

        # MOIAT 인증 누락이 감지되어야 함
        assert result["result"] == "FAIL"
        assert "missing_certs" in result

    def test_should_cache_parsed_pdfs(self, integration_layer):
        """동일 PDF는 캐시에서 로드해야 함"""
        # 캐시가 비어있음
        assert len(integration_layer.parse_cache) == 0

        # Note: 실제 파일이 없으므로 캐시 메커니즘만 테스트
        # 실제 파일로 테스트할 경우:
        # result1 = integration_layer.parse_supporting_docs(...)
        # result2 = integration_layer.parse_supporting_docs(...)  # 캐시 사용
        # assert len(integration_layer.parse_cache) > 0


class TestIntegratedAuditWorkflow:
    """통합 Audit 워크플로우 테스트"""

    @pytest.mark.skipif(not INTEGRATION_OK, reason="PDF Integration not available")
    def test_should_integrate_with_audit_system(self):
        """Audit 시스템과 통합되어야 함"""
        from shpt_sept_2025_enhanced_audit import SHPTSept2025EnhancedAuditSystem

        audit_system = SHPTSept2025EnhancedAuditSystem()

        # PDF Integration이 초기화되었는지 확인
        assert hasattr(audit_system, "pdf_integration")

    @pytest.mark.skipif(not INTEGRATION_OK, reason="PDF Integration not available")
    def test_enhanced_gates_should_include_pdf_gates(self):
        """Enhanced Gates는 PDF Gates를 포함해야 함"""
        # Mock 데이터로 테스트
        integration = InvoicePDFIntegration()

        mock_pdf_data = {
            "documents": [
                {
                    "header": {"doc_type": "BOE"},
                    "data": {"mbl_no": "CHN2595234", "containers": []},
                }
            ]
        }

        result = integration.run_pdf_gates({}, mock_pdf_data)

        # 4개 Gate가 실행되어야 함
        assert len(result["Gate_Details"]) == 4


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
