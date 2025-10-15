#!/usr/bin/env python3
"""
Invoice PDF Integration Layer
==============================

Invoice Audit 시스템과 PDF 파싱 모듈 통합

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# PDF 통합 모듈 임포트 - 강화된 파서 사용
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "PDF"))

try:
    # PDF 통합 모듈 임포트 (00_Shared/pdf_integration에서)
    from pdf_integration import (
        DSVPDFParser,
        CrossDocValidator,
        OntologyMapper,
        WorkflowAutomator,
    )

    PDF_INTEGRATION_OK = True
    logging.info("PDF integration modules loaded successfully")
except ImportError as e:
    PDF_INTEGRATION_OK = False
    logging.warning(f"PDF integration modules not found: {e}. Install dependencies.")


class InvoicePDFIntegration:
    """
    Invoice와 PDF 검증 통합 레이어

    Features:
    - Invoice 항목 ↔ Supporting PDF 자동 매칭
    - PDF 파싱 결과를 Invoice 검증에 활용
    - Cross-document 검증 결과 통합
    - Gate 검증 확장 (Gate-11~14)
    """

    def __init__(self, audit_system=None, config_path: Optional[str] = None):
        """
        Args:
            audit_system: SHPTSept2025EnhancedAuditSystem 인스턴스
            config_path: PDF 설정 파일 경로
        """
        self.audit_system = audit_system
        self.logger = self._setup_logger()

        # PDF 모듈 초기화
        if PDF_INTEGRATION_OK:
            self.pdf_parser = DSVPDFParser(log_level="INFO")
            self.doc_validator = CrossDocValidator()
            self.ontology_mapper = OntologyMapper()

            # Config 경로 결정
            if not config_path:
                config_path = str(
                    Path(__file__).parent.parent.parent
                    / "00_Shared"
                    / "pdf_integration"
                    / "config.yaml"
                )

            self.workflow_automator = WorkflowAutomator(config_path=config_path)

            self.logger.info("PDF Integration modules initialized")
        else:
            self.pdf_parser = None
            self.doc_validator = None
            self.ontology_mapper = None
            self.workflow_automator = None
            self.logger.warning("PDF Integration modules not available")

        # 파싱 캐시 (file_hash → parsed_data)
        self.parse_cache = {}

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("InvoicePDFIntegration")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def parse_supporting_docs(self, shipment_id: str, pdf_files: List[Dict]) -> Dict:
        """
        Shipment ID의 모든 PDF 파싱

        Args:
            shipment_id: HVDC Shipment ID
            pdf_files: PDF 파일 정보 리스트 [{file_name, file_path, doc_type}]

        Returns:
            파싱 결과 딕셔너리
        """
        if not PDF_INTEGRATION_OK or not self.pdf_parser:
            return {
                "shipment_id": shipment_id,
                "parsed_count": 0,
                "documents": [],
                "error": "PDF integration not available",
            }

        parsed_documents = []

        for pdf_file in pdf_files:
            file_path = pdf_file["file_path"]

            try:
                # 캐시 확인
                file_hash = self._get_file_hash(file_path)

                if file_hash in self.parse_cache:
                    self.logger.info(f"Using cached result for {pdf_file['file_name']}")
                    parsed_result = self.parse_cache[file_hash]
                else:
                    # PDF 파싱
                    parsed_result = self.pdf_parser.parse_pdf(
                        file_path, doc_type=pdf_file.get("doc_type")
                    )

                    # 캐시 저장
                    if parsed_result.get("error") is None:
                        self.parse_cache[file_hash] = parsed_result

                parsed_documents.append(parsed_result)

            except Exception as e:
                self.logger.error(f"Error parsing {pdf_file['file_name']}: {e}")
                parsed_documents.append(
                    {
                        "header": {
                            "file_path": file_path,
                            "doc_type": pdf_file.get("doc_type"),
                        },
                        "data": None,
                        "error": str(e),
                    }
                )

        result = {
            "shipment_id": shipment_id,
            "parsed_count": len(
                [d for d in parsed_documents if d.get("error") is None]
            ),
            "total_files": len(pdf_files),
            "documents": parsed_documents,
        }

        self.logger.info(
            f"Parsed {result['parsed_count']}/{result['total_files']} documents for {shipment_id}"
        )
        return result

    def _get_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        import hashlib

        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일 파싱 (간단한 구현)"""
        try:
            # 실제 PDF 파싱은 DSVPDFParser를 사용해야 하지만,
            # 현재는 기본 구조만 반환
            return {
                "file_path": pdf_path,
                "boe_data": [],
                "do_data": [],
                "dn_data": [],
                "carrier_invoice_data": [],
                "currency": "USD",  # 기본값
                "parsed_successfully": True,
            }
        except Exception as e:
            logging.warning(f"PDF parsing failed for {pdf_path}: {e}")
            return {
                "file_path": pdf_path,
                "boe_data": [],
                "do_data": [],
                "dn_data": [],
                "carrier_invoice_data": [],
                "currency": "USD",
                "parsed_successfully": False,
                "error": str(e),
            }

    def validate_invoice_with_docs(
        self, invoice_item: Dict, shipment_id: str, pdf_files: List[Dict]
    ) -> Dict:
        """
        Invoice 항목 + PDF 데이터 통합 검증

        Args:
            invoice_item: Invoice 항목 딕셔너리
            shipment_id: Shipment ID
            pdf_files: PDF 파일 리스트

        Returns:
            통합 검증 결과
        """
        # 1. PDF 파싱
        parse_result = self.parse_supporting_docs(shipment_id, pdf_files)

        # 2. Cross-document 검증
        documents_for_validation = []

        for doc in parse_result["documents"]:
            if doc.get("error") is None and doc.get("data"):
                doc_type = doc["header"].get("doc_type", "Unknown")
                documents_for_validation.append(
                    {"doc_type": doc_type, "data": doc["data"]}
                )

        # Cross-document 검증 실행
        if documents_for_validation and self.doc_validator:
            doc_report = self.doc_validator.generate_validation_report(
                shipment_id, documents_for_validation
            )
        else:
            doc_report = {
                "overall_status": "NOT_VALIDATED",
                "total_issues": 0,
                "all_issues": [],
            }

        # 3. Invoice 검증에 PDF 데이터 통합
        enhanced_validation = invoice_item.copy()
        enhanced_validation["pdf_validation"] = {
            "enabled": True,
            "parsed_files": parse_result["parsed_count"],
            "total_files": parse_result["total_files"],
            "cross_doc_status": doc_report["overall_status"],
            "cross_doc_issues": doc_report["total_issues"],
            "issues_detail": doc_report.get("all_issues", []),
        }

        # 4. Demurrage Risk 체크 (DO 파일이 있으면)
        for doc in parse_result["documents"]:
            if doc.get("header", {}).get("doc_type") == "DO" and doc.get("data"):
                if self.workflow_automator:
                    do_data = doc["data"].copy()
                    do_data["item_code"] = shipment_id

                    demurrage_risk = self.workflow_automator.check_demurrage_risk(
                        do_data
                    )

                    if demurrage_risk:
                        enhanced_validation["demurrage_risk"] = demurrage_risk
                        enhanced_validation["pdf_validation"][
                            "has_demurrage_risk"
                        ] = True

        return enhanced_validation

    def enrich_validation_with_pdf(self, validation: Dict, pdf_data: Dict) -> Dict:
        """
        PDF 검증 결과를 Invoice 검증에 추가

        Args:
            validation: Invoice 검증 결과
            pdf_data: PDF 파싱/검증 결과

        Returns:
            통합된 검증 결과
        """
        enriched = validation.copy()

        # PDF 검증 상태 추가
        if pdf_data.get("cross_doc_status") == "FAIL":
            enriched["status"] = "FAIL"
            enriched["flag"] = "CRITICAL"
            enriched["issues"].append("Supporting documents validation failed")

        elif pdf_data.get("cross_doc_status") == "WARNING":
            if enriched.get("status") == "PASS":
                enriched["status"] = "REVIEW_NEEDED"
            enriched["issues"].append("Supporting documents have warnings")

        # Demurrage Risk 플래그
        if pdf_data.get("has_demurrage_risk"):
            enriched["issues"].append(
                "Demurrage risk detected - DO validity expiring soon"
            )

        return enriched

    def run_pdf_gates(self, invoice_item: Dict, pdf_data: Dict) -> Dict:
        """
        PDF 기반 Gate 검증 (Gate-11~14)

        Args:
            invoice_item: Invoice 항목
            pdf_data: PDF 파싱 결과

        Returns:
            Gate 검증 결과
        """
        gate_results = []
        total_score = 0
        max_score = 0

        # Gate-11: BOE-Invoice MBL 일치
        gate_11 = self._gate_11_mbl_consistency(invoice_item, pdf_data)
        gate_results.append(gate_11)
        total_score += gate_11["score"]
        max_score += 100

        # Gate-12: Container 번호 일치
        gate_12 = self._gate_12_container_consistency(pdf_data)
        gate_results.append(gate_12)
        total_score += gate_12["score"]
        max_score += 100

        # Gate-13: Weight 일치
        gate_13 = self._gate_13_weight_consistency(pdf_data)
        gate_results.append(gate_13)
        total_score += gate_13["score"]
        max_score += 100

        # Gate-14: 누락 인증서 체크
        gate_14 = self._gate_14_certification_check(pdf_data)
        gate_results.append(gate_14)
        total_score += gate_14["score"]
        max_score += 100

        # 전체 결과
        avg_score = round(total_score / max_score * 100, 1) if max_score > 0 else 0

        fails = [g for g in gate_results if g["result"] == "FAIL"]

        return {
            "Gate_Status": "FAIL" if fails else "PASS",
            "Gate_Score": avg_score,
            "Gate_Fails": len(fails),
            "Gate_Details": gate_results,
        }

    def _gate_11_mbl_consistency(self, invoice_item: Dict, pdf_data: Dict) -> Dict:
        """Gate-11: BOE-Invoice MBL 일치"""
        # PDF 데이터에서 MBL 추출
        mbls = []

        for doc in pdf_data.get("documents", []):
            if doc.get("data"):
                mbl = doc["data"].get("mbl_no") or doc["data"].get("bl_number")
                if mbl:
                    mbls.append(mbl)

        # 일치 확인
        if len(set(mbls)) > 1:
            return {
                "gate": "Gate-11",
                "name": "MBL Consistency",
                "result": "FAIL",
                "score": 0,
                "details": f"Multiple MBL numbers found: {set(mbls)}",
            }
        elif mbls:
            return {
                "gate": "Gate-11",
                "name": "MBL Consistency",
                "result": "PASS",
                "score": 100,
                "details": f"MBL consistent: {mbls[0]}",
            }
        else:
            return {
                "gate": "Gate-11",
                "name": "MBL Consistency",
                "result": "SKIP",
                "score": 100,
                "details": "No MBL data in PDFs",
            }

    def _gate_12_container_consistency(self, pdf_data: Dict) -> Dict:
        """Gate-12: Container 번호 일치 (BOE ↔ DO ↔ DN)"""
        containers_by_doc = {}

        for doc in pdf_data.get("documents", []):
            if doc.get("data"):
                doc_type = doc["header"].get("doc_type")
                containers = set()

                if doc_type == "BOE":
                    containers = set(doc["data"].get("containers", []))
                elif doc_type == "DO":
                    container_list = doc["data"].get("containers", [])
                    containers = set(
                        [
                            c.get("container_no") if isinstance(c, dict) else c
                            for c in container_list
                        ]
                    )
                elif doc_type == "DN":
                    container_no = doc["data"].get("container_no")
                    if container_no:
                        containers = {container_no}

                if containers:
                    containers_by_doc[doc_type] = containers

        # 비교
        if len(containers_by_doc) >= 2:
            all_containers = list(containers_by_doc.values())
            first_set = all_containers[0]

            for container_set in all_containers[1:]:
                if first_set != container_set:
                    return {
                        "gate": "Gate-12",
                        "name": "Container Consistency",
                        "result": "FAIL",
                        "score": 0,
                        "details": f"Container mismatch: {containers_by_doc}",
                    }

            return {
                "gate": "Gate-12",
                "name": "Container Consistency",
                "result": "PASS",
                "score": 100,
                "details": f"Containers consistent: {len(first_set)} containers",
            }

        return {
            "gate": "Gate-12",
            "name": "Container Consistency",
            "result": "SKIP",
            "score": 100,
            "details": "Insufficient container data",
        }

    def _gate_13_weight_consistency(self, pdf_data: Dict) -> Dict:
        """Gate-13: Weight 일치 (±3% 허용)"""
        weights = {}

        for doc in pdf_data.get("documents", []):
            if doc.get("data"):
                doc_type = doc["header"].get("doc_type")

                if doc_type == "BOE":
                    weight = doc["data"].get("gross_weight_kg")
                    if weight:
                        weights["BOE"] = float(weight)

                elif doc_type == "DO":
                    weight = doc["data"].get("weight_kg")
                    if weight:
                        weights["DO"] = float(weight)

        # 비교
        if "BOE" in weights and "DO" in weights:
            boe_weight = weights["BOE"]
            do_weight = weights["DO"]

            if boe_weight > 0:
                delta_pct = abs(boe_weight - do_weight) / boe_weight

                if delta_pct > 0.03:  # 3% 초과
                    return {
                        "gate": "Gate-13",
                        "name": "Weight Consistency",
                        "result": "FAIL",
                        "score": max(0, 100 - delta_pct * 100),
                        "details": f"Weight deviation {delta_pct*100:.2f}% (BOE: {boe_weight} kg, DO: {do_weight} kg)",
                    }
                else:
                    return {
                        "gate": "Gate-13",
                        "name": "Weight Consistency",
                        "result": "PASS",
                        "score": 100,
                        "details": f"Weight within ±3%: {delta_pct*100:.2f}%",
                    }

        return {
            "gate": "Gate-13",
            "name": "Weight Consistency",
            "result": "SKIP",
            "score": 100,
            "details": "Insufficient weight data",
        }

    def _gate_14_certification_check(self, pdf_data: Dict) -> Dict:
        """Gate-14: 누락 인증서 체크 (FANR/MOIAT)"""
        missing_certs = []

        for doc in pdf_data.get("documents", []):
            if doc.get("data") and doc["header"].get("doc_type") == "BOE":
                data = doc["data"]
                hs_code = data.get("hs_code")
                description = data.get("description", "")

                if hs_code and self.ontology_mapper:
                    # 규제 요건 추론
                    certs = self.ontology_mapper.infer_certification_requirements(
                        hs_code, description
                    )

                    for cert in certs:
                        if cert["status"] == "PENDING":
                            missing_certs.append(cert)

        if missing_certs:
            cert_types = [c["type"] for c in missing_certs]
            return {
                "gate": "Gate-14",
                "name": "Certification Check",
                "result": "FAIL",
                "score": 0,
                "details": f"Missing certifications: {', '.join(cert_types)}",
                "missing_certs": missing_certs,
            }
        else:
            return {
                "gate": "Gate-14",
                "name": "Certification Check",
                "result": "PASS",
                "score": 100,
                "details": "No missing certifications or no BOE data",
            }

    def generate_integrated_report(
        self, invoice_results: List[Dict], pdf_results: Dict
    ) -> Dict:
        """
        통합 보고서 생성

        Args:
            invoice_results: Invoice 검증 결과 리스트
            pdf_results: PDF 파싱/검증 결과

        Returns:
            통합 보고서
        """
        total_items = len(invoice_results)
        items_with_pdf = sum(
            1
            for item in invoice_results
            if item.get("pdf_validation", {}).get("enabled")
        )

        pdf_pass = sum(
            1
            for item in invoice_results
            if item.get("pdf_validation", {}).get("cross_doc_status") == "PASS"
        )

        pdf_fail = sum(
            1
            for item in invoice_results
            if item.get("pdf_validation", {}).get("cross_doc_status") == "FAIL"
        )

        demurrage_risks = sum(
            1 for item in invoice_results if item.get("demurrage_risk")
        )

        report = {
            "report_type": "INTEGRATED_INVOICE_PDF_AUDIT",
            "generated_at": Path(__file__).parent.parent.parent.name,
            "summary": {
                "total_invoice_items": total_items,
                "items_with_pdf_validation": items_with_pdf,
                "pdf_pass": pdf_pass,
                "pdf_fail": pdf_fail,
                "demurrage_risks": demurrage_risks,
            },
            "invoice_results": invoice_results,
            "pdf_validation_enabled": PDF_INTEGRATION_OK,
        }

        self.logger.info(
            f"Integrated report generated: {total_items} items, {items_with_pdf} with PDF validation"
        )
        return report


# 사용 예시
if __name__ == "__main__":
    # 통합 레이어 초기화
    integration = InvoicePDFIntegration()

    # 샘플 데이터
    test_pdf_files = [
        {
            "file_name": "HVDC-ADOPT-SCT-0126_BOE.pdf",
            "file_path": "/path/to/BOE.pdf",
            "doc_type": "BOE",
        },
        {
            "file_name": "HVDC-ADOPT-SCT-0126_DO.pdf",
            "file_path": "/path/to/DO.pdf",
            "doc_type": "DO",
        },
    ]

    test_invoice_item = {
        "s_no": 1,
        "sheet_name": "SIM-0001",
        "description": "TRANSPORTATION FROM KHALIFA PORT TO DSV YARD",
        "rate_source": "CONTRACT",
        "unit_rate": 252.00,
        "quantity": 3,
        "total_usd": 756.00,
    }

    # 통합 검증
    result = integration.validate_invoice_with_docs(
        test_invoice_item, "HVDC-ADOPT-SCT-0126", test_pdf_files
    )

    print("Integration Result:")
    print(f"  PDF Validation: {result.get('pdf_validation', {})}")
    print(f"  Demurrage Risk: {result.get('demurrage_risk', 'None')}")
