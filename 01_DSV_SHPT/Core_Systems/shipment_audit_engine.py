#!/usr/bin/env python3
"""
Shipment Invoice Audit Engine

통합 송장 감사 시스템 - 모든 기간 지원 (logic_patch.md applied)
- Excel 직접 처리
- Portal Fee ±0.5% 검증
- 핵심 Gate 검증 (3개)
- S/No 순서 보존
- 시트별 통계
- Configuration 기반 요율 관리

Version: 2.1.0 (logic_patch.md applied)
Updated: 2025-10-15
"""

import pandas as pd
import json
import os
import re
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import logging

# UnifiedRateLoader and ConfigurationManager import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from rate_loader import UnifiedRateLoader
from config_manager import ConfigurationManager
from cost_guard import get_cost_guard_band, should_auto_fail
from portal_fee import (
    resolve_portal_fee_usd,
    is_within_portal_fee_tolerance,
    get_portal_fee_band,
)
from rate_service import RateService
from anomaly_detection import AnomalyDetectionService

# PDF Integration import
try:
    from invoice_pdf_integration import InvoicePDFIntegration

    PDF_INTEGRATION_AVAILABLE = True
except ImportError:
    PDF_INTEGRATION_AVAILABLE = False
    logging.warning(
        "PDF Integration not available. Install dependencies: pip install pdfplumber rdflib"
    )


class ShipmentAuditEngine:
    """통합 송장 감사 엔진 - 모든 기간 지원"""

    def __init__(self):
        self.root = Path(
            __file__
        ).parent.parent  # Core_Systems의 상위 폴더 (01_DSV_SHPT)
        self.out_dir = self.root / "Results" / "Sept_2025"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # 9월 2025 파일 경로 (_FINAL 버전 사용)
        self.excel_file = (
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
        )
        self.supporting_docs_paths = [
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT Import (Sept 2025) - Supporting Documents",
            self.root
            / "Data"
            / "DSV 202509"
            / "SCNT Domestic (Sept 2025) - Supporting Documents",
        ]

        # SHPT 설정
        self.system_type = "SHPT_ENHANCED"
        self.scope = (
            "Shipment Invoice Processing (Sea + Air) + Portal Fee + Gate Validation"
        )

        # UnifiedRateLoader 초기화
        rate_dir = self.root.parent / "Rate"
        self.rate_loader = UnifiedRateLoader(rate_dir)
        self.rate_loader.load_all_rates()

        # ConfigurationManager 초기화 (새로운 설정 관리)
        self.config_manager = ConfigurationManager(rate_dir)
        self.config_manager.load_all_configs()
        logging.info(
            f"✅ Configuration Manager loaded: {self.config_manager.get_config_summary()['lanes_loaded']} lanes"
        )

        # PDF Integration 초기화
        if PDF_INTEGRATION_AVAILABLE:
            try:
                self.pdf_integration = InvoicePDFIntegration(
                    audit_system=self, config_path=None  # 기본 경로 사용
                )
                logging.info("✅ PDF Integration enabled")
            except Exception as e:
                self.pdf_integration = None
                logging.warning(f"⚠️ PDF Integration disabled: {e}")
        else:
            self.pdf_integration = None
            logging.warning("⚠️ PDF Integration not available")

        # Lane Map (ConfigurationManager에서 로드)
        self.lane_map = self.config_manager.get_lane_map()

        # Normalization Map (ConfigurationManager에서 로드)
        self.normalization_map = self.config_manager.get_normalization_aliases()

        # COST-GUARD 밴드 (ConfigurationManager에서 로드)
        self.cost_guard_bands = self.config_manager.get_cost_guard_bands()

        # FX 환율 (ConfigurationManager에서 로드)
        self.fx_rate = self.config_manager.get_fx_rate("USD", "AED")

        # Risk-based review 설정 및 서비스 초기화
        self.risk_based_review_config = (
            self.config_manager.get_risk_based_review_config()
        )
        # AnomalyDetectionService는 config 딕셔너리를 받음
        anomaly_config = self.config_manager.get_anomaly_detection_config()
        self.anomaly_service = AnomalyDetectionService(anomaly_config)

        # Rate Service 초기화 (Issue #4 패치: 중복 로직 통합)
        self.rate_service = RateService(self.config_manager)
        logging.info("Rate Service initialized for ShipmentAuditEngine")

        # Anomaly Detection 초기화
        self.anomaly_base_config = self.config_manager.get_anomaly_detection_config()
        self.anomaly_detectors: Dict[
            Optional[str], Optional[AnomalyDetectionService]
        ] = {}
        self.anomaly_disabled_lanes: Set[str] = set()
        self.anomaly_detectors[None] = self._create_anomaly_detector(
            self.anomaly_base_config
        )
        if self.anomaly_detectors[None] is None and not self.anomaly_base_config.get(
            "enabled", False
        ):
            logging.info("Anomaly detection disabled globally")

        # Portal Fee 설정 (Enhanced 기능) - portal_fee.py로 마이그레이션 예정
        self.portal_fee_keywords = [
            "MAQTA",
            "APPOINTMENT",
            "APPT",
            "DPC",
            "DOCUMENT PROCESSING",
            "MANIFEST",
        ]
        self.portal_fee_tolerance = (
            0.005  # ±0.5% (portal_fee.PORTAL_FEE_TOLERANCE와 동일)
        )
        self.portal_fee_fixed_rates = {
            "APPOINTMENT": {"AED": 27.00, "USD": 7.35},
            "DPC": {"AED": 35.00, "USD": 9.53},
            "DOCUMENT PROCESSING": {"AED": 35.00, "USD": 9.53},
        }

        # 로깅 설정
        log_file = self.out_dir / "shpt_sept_2025_enhanced_audit.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

        logging.info(f"SHPT Enhanced 시스템 초기화 완료")
        logging.info(f"송장 파일: {self.excel_file}")

    # ==================== Portal Fee 검증 메서드 (Enhanced) ====================

    def is_portal_fee(self, rate_source: str, description: str) -> bool:
        """Portal Fee 여부 판별"""
        rs = (rate_source or "").upper()
        desc = (description or "").upper()
        return any(
            keyword in rs or keyword in desc for keyword in self.portal_fee_keywords
        )

    def parse_aed_from_formula(self, formula: str) -> Optional[float]:
        """수식에서 AED 금액 추출 (=27/3.6725 형식)"""
        if not formula:
            return None

        pattern = r"=\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*3\.6725"
        match = re.search(pattern, formula.replace(",", ""))
        return float(match.group(1)) if match else None

    def get_portal_fee_fixed_rate(self, description: str) -> Optional[Dict[str, float]]:
        """Portal Fee 고정값 조회"""
        desc_upper = (description or "").upper()

        for keyword, rates in self.portal_fee_fixed_rates.items():
            if keyword in desc_upper:
                return rates

        return None

    def portal_fee_band(self, delta_abs: float) -> str:
        """Portal Fee 전용 COST-GUARD 밴드 (±0.5% 기준)"""
        if delta_abs <= 0.005:  # ≤0.5%
            return "PASS"
        elif delta_abs <= 0.05:  # 0.5-5%
            return "WARN"
        elif delta_abs <= 0.10:  # 5-10%
            return "HIGH"
        else:
            return "CRITICAL"

    # ==================== Gate 검증 메서드 (핵심 3개) ====================

    def validate_gate_01_document_set(
        self, supporting_docs: List[Dict]
    ) -> Dict[str, Any]:
        """Gate-01: 문서세트 존재 검증"""
        required_docs = ["BOE", "DO", "DN"]
        found_docs = [doc.get("doc_type", "") for doc in supporting_docs]

        missing_docs = [doc for doc in required_docs if doc not in found_docs]

        return {
            "status": "PASS" if not missing_docs else "FAIL",
            "missing_docs": missing_docs,
            "score": max(0, 100 - len(missing_docs) * 25),
        }

    def validate_gate_07_total_consistency(self, item: Dict) -> Dict[str, Any]:
        """Gate-07: 합계 정합 검증"""
        rate = item.get("unit_rate", 0)
        quantity = item.get("quantity", 0)
        total = item.get("total_usd", 0)

        calculated_total = rate * quantity
        delta = abs(total - calculated_total)

        return {
            "status": "PASS" if delta < 0.01 else "FAIL",
            "calculated": calculated_total,
            "actual": total,
            "delta": delta,
            "score": max(0, 100 - delta * 100),
        }

    def run_key_gates(
        self, item: Dict, supporting_docs: List[Dict], pdf_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """핵심 Gate 검증 실행 (기존 + PDF Gates)"""
        gates = {
            "Gate_01": self.validate_gate_01_document_set(supporting_docs),
            "Gate_07": self.validate_gate_07_total_consistency(item),
        }

        # PDF Integration Gates 추가 (활성화 시)
        if pdf_data and self.pdf_integration:
            pdf_gates = self.pdf_integration.run_pdf_gates(item, pdf_data)

            # PDF Gate 결과를 기존 gates에 통합
            for gate_detail in pdf_gates.get("Gate_Details", []):
                gate_name = gate_detail["gate"]
                gates[gate_name] = {
                    "status": gate_detail["result"],
                    "score": gate_detail["score"],
                    "details": gate_detail["details"],
                }

        failed_gates = [
            name for name, result in gates.items() if result["status"] == "FAIL"
        ]
        total_score = sum(result["score"] for result in gates.values()) / len(gates)

        return {
            "Gate_Status": "PASS" if not failed_gates else "FAIL",
            "Gate_Fails": ",".join(failed_gates) if failed_gates else "",
            "Gate_Score": round(total_score, 1),
            "gates": gates,
        }

    def _apply_risk_based_review(self, validation: Dict[str, Any]) -> None:
        """Risk 기반 리뷰 적용/Apply risk-based review decision."""

        if not self.risk_based_review_config.get("enabled", False):
            return

        anomaly_indicator = 0.0

        if validation.get("issues"):
            anomaly_indicator = max(anomaly_indicator, 0.5)

        if validation.get("gate_status") == "FAIL":
            anomaly_indicator = max(anomaly_indicator, 1.0)

        pdf_status = None
        if isinstance(validation.get("pdf_validation"), dict):
            pdf_status = validation["pdf_validation"].get("cross_doc_status")

        if pdf_status == "FAIL":
            anomaly_indicator = max(anomaly_indicator, 1.0)
        elif pdf_status == "WARNING":
            anomaly_indicator = max(anomaly_indicator, 0.5)

        if validation.get("demurrage_risk"):
            anomaly_indicator = max(anomaly_indicator, 1.0)

        gates = validation.get("gates", {}) or {}
        certification_missing = any(
            "CERT" in gate_name.upper() and gate.get("status") == "FAIL"
            for gate_name, gate in gates.items()
        )
        signature_risk = any(
            "SIGNATURE" in gate_name.upper() and gate.get("status") == "FAIL"
            for gate_name, gate in gates.items()
        )

        risk = self.anomaly_service.compute_risk_score(
            delta_pct=validation.get("delta_pct"),
            anomaly_indicator=anomaly_indicator,
            certification_missing=certification_missing,
            signature_risk=signature_risk,
        )

        validation["risk_score"] = risk.score
        validation["risk_components"] = risk.components
        validation["risk_triggered"] = risk.triggered

        if risk.triggered and validation.get("status") not in ("FAIL", "ERROR"):
            if validation.get("status") == "PASS":
                validation["status"] = "REVIEW_NEEDED"

            if validation.get("flag") == "OK":
                validation["flag"] = "RISK"

            message = (
                f"Risk-based review triggered (score {risk.score:.2f} >= "
                f"threshold {self.anomaly_service.trigger_threshold:.2f})"
            )
            if message not in validation["issues"]:
                validation["issues"].append(message)

    # ==================== Excel 처리 메서드 ====================

    def load_invoice_sheets(self):
        """Excel 파일의 모든 시트 로드"""
        try:
            logging.info(f"📂 송장 파일 로드 중: {self.excel_file.name}")

            if not self.excel_file.exists():
                logging.error(f"[ERROR] File not found: {self.excel_file}")
                return None

            excel_file = pd.ExcelFile(self.excel_file, engine="openpyxl")

            logging.info(f"[OK] File loaded successfully")
            logging.info(f"📊 총 시트 수: {len(excel_file.sheet_names)}")

            return excel_file

        except Exception as e:
            logging.error(f"[ERROR] File load error: {e}")
            return None

    def extract_invoice_items(self, df, sheet_name):
        """시트에서 송장 항목 추출 (run_sept_2025_audit.py 검증된 로직 사용)"""
        items = []

        try:
            # S/No 컬럼 찾기
            header_row = None
            for idx, row in df.iterrows():
                row_str = " ".join([str(cell) for cell in row if pd.notna(cell)])
                if "S/No" in row_str or "S/NO" in row_str.upper():
                    header_row = idx
                    break

            if header_row is None:
                return items

            # 헤더 설정
            df.columns = df.iloc[header_row]
            df = df[header_row + 1 :].reset_index(drop=True)

            # 데이터 추출
            for idx, row in df.iterrows():
                try:
                    s_no = str(row.get("S/No", row.get("S/NO", ""))).strip()

                    if not s_no or s_no == "nan":
                        continue

                    if "TOTAL" in s_no.upper():
                        break

                    description = str(
                        row.get("DESCRIPTION", row.get("Description", ""))
                    ).strip()
                    if not description or description == "nan":
                        continue

                    rate_source = str(
                        row.get("RATE SOURCE", row.get("Rate Source", ""))
                    ).strip()

                    rate_col = row.get("RATE", row.get("Rate", row.get("UNIT RATE", 0)))
                    rate = (
                        float(str(rate_col).replace(",", ""))
                        if pd.notna(rate_col)
                        else 0
                    )

                    qty_col = row.get(
                        "Q'TY", row.get("QTY", row.get("Qty", row.get("QUANTITY", 1)))
                    )
                    qty = (
                        float(str(qty_col).replace(",", "")) if pd.notna(qty_col) else 1
                    )

                    total_col = row.get(
                        "TOTAL (USD)", row.get("Total (USD)", row.get("AMOUNT", 0))
                    )
                    total = (
                        float(str(total_col).replace(",", ""))
                        if pd.notna(total_col)
                        else 0
                    )

                    formula_col = row.get("FORMULA", row.get("Formula", ""))
                    formula = str(formula_col).strip() if pd.notna(formula_col) else ""

                    remark = str(row.get("REMARK", row.get("Remark", ""))).strip()

                    item = {
                        "sheet_name": sheet_name,
                        "s_no": s_no,
                        "description": description,
                        "rate_source": rate_source,
                        "unit_rate": rate,
                        "quantity": qty,
                        "total_usd": total,
                        "formula_text": formula,
                        "remark": remark,
                    }

                    items.append(item)

                except Exception as e:
                    logging.debug(f"행 추출 오류 ({sheet_name}, 행 {idx}): {e}")
                    continue

            logging.info(f"  [OK] {sheet_name}: {len(items)} items extracted")

        except Exception as e:
            logging.error(f"  [ERROR] {sheet_name} extraction error: {e}")

        return items

    def validate_enhanced_item(self, item: Dict, supporting_docs: List[Dict]) -> Dict:
        """Enhanced 송장 항목 검증 (Portal Fee + Gate 포함)"""
        validation = {
            "s_no": item["s_no"],
            "sheet_name": item["sheet_name"],
            "description": item["description"],
            "rate_source": item["rate_source"],
            "unit_rate": item["unit_rate"],
            "quantity": item["quantity"],
            "total_usd": item["total_usd"],
            "status": "PASS",
            "flag": "OK",
            "delta_pct": 0.0,
            "cg_band": "PASS",
            "charge_group": "Other",
            "issues": [],
            "tolerance": 0.03,  # 기본 3%
            "ref_rate_usd": None,
            "doc_aed": None,
            "gates": {},
            "risk_score": 0.0,
            "risk_components": {
                "delta": 0.0,
                "anomaly": 0.0,
                "certification": 0.0,
                "signature": 0.0,
            },
            "risk_triggered": False,
        }

        try:
            # 1. 금액 계산 검증
            expected_total = round(item["unit_rate"] * item["quantity"], 2)
            if abs(expected_total - item["total_usd"]) > 0.01:
                validation["issues"].append(
                    f"금액 불일치: 예상 {expected_total}, 실제 {item['total_usd']}"
                )
                validation["flag"] = "WARN"

            # 2. Rate Source 분류
            rate_source_upper = item["rate_source"].upper()
            desc_upper = item["description"].upper()

            # Portal Fee 판별 (Enhanced)
            if self.is_portal_fee(item["rate_source"], item["description"]):
                validation["charge_group"] = "PortalFee"
                validation["tolerance"] = self.portal_fee_tolerance  # ±0.5%

                # AED 수식 파싱
                doc_aed = self.parse_aed_from_formula(item["formula_text"])

                # 고정값 테이블 조회
                if doc_aed is None:
                    fixed_rate = self.get_portal_fee_fixed_rate(item["description"])
                    if fixed_rate:
                        doc_aed = fixed_rate["AED"]

                # AED → USD 환산
                if doc_aed is not None:
                    validation["doc_aed"] = doc_aed
                    validation["ref_rate_usd"] = round(doc_aed / self.fx_rate, 2)

                    # Delta % 계산 (Portal Fee)
                    if validation["ref_rate_usd"] > 0:
                        delta_pct = (
                            (item["unit_rate"] - validation["ref_rate_usd"])
                            / validation["ref_rate_usd"]
                        ) * 100
                        validation["delta_pct"] = round(delta_pct, 2)
                        validation["cg_band"] = self.portal_fee_band(
                            abs(delta_pct / 100)
                        )

                        # Status 결정 (±0.5% 기준)
                        if abs(delta_pct) <= 0.5:
                            validation["status"] = "PASS"
                            validation["flag"] = "OK"
                        elif abs(delta_pct) <= 5.0:
                            validation["status"] = "REVIEW"
                            validation["flag"] = "WARN"
                        else:
                            validation["status"] = "FAIL"
                            validation["flag"] = "CRITICAL"

            elif "CONTRACT" in rate_source_upper:
                validation["charge_group"] = "Contract"

                # Contract 항목 ref_rate 조회
                ref_rate = self._find_contract_ref_rate(item)
                if ref_rate is not None:
                    validation["ref_rate_usd"] = ref_rate

                    # Delta % 계산
                    delta_pct = self.rate_loader.calculate_delta_percent(
                        item["unit_rate"], ref_rate
                    )
                    validation["delta_pct"] = delta_pct

                    # COST-GUARD 밴드 결정 (Issue #1 패치: config 기반)
                    cg_band = get_cost_guard_band(delta_pct, self.cost_guard_bands)
                    validation["cg_band"] = cg_band

                    # Issue #7 패치: "Δ>5% FAIL" 고정 분기 제거, 밴드 기반 판정
                    if cg_band == "CRITICAL":
                        validation["status"] = "FAIL"
                        validation["flag"] = "CRITICAL"
                        validation["issues"].append(
                            f"Contract 과다/과소 청구 (CRITICAL): Delta {delta_pct:.2f}% (Ref: ${ref_rate})"
                        )
                    elif cg_band == "HIGH":
                        validation["status"] = "REVIEW_NEEDED"
                        validation["flag"] = "HIGH"
                        validation["issues"].append(
                            f"Contract 청구 주의 필요 (HIGH): Delta {delta_pct:.2f}% (Ref: ${ref_rate})"
                        )
                    elif cg_band == "WARN":
                        validation["status"] = "REVIEW_NEEDED"
                        validation["flag"] = "WARN"

            elif "AT COST" in rate_source_upper or "AT-COST" in rate_source_upper:
                validation["charge_group"] = "AtCost"
            else:
                validation["charge_group"] = "Other"

            # 3. Gate 검증 실행
            gate_result = self.run_key_gates(item, supporting_docs)
            validation["gate_status"] = gate_result["Gate_Status"]
            validation["gate_score"] = gate_result["Gate_Score"]
            validation["gate_fails"] = gate_result["Gate_Fails"]
            validation["gates"] = gate_result.get("gates", {})

            lane_metadata = self._resolve_lane_metadata(item) or {}
            lane_id = lane_metadata.get("lane_id")
            lane_rate = (
                validation.get("ref_rate_usd")
                or lane_metadata.get("rate")
                or item.get("unit_rate")
                or 0.0
            )

            anomaly_features: Dict[str, Any] = {
                "unit_rate": float(item.get("unit_rate", 0.0)),
                "quantity": float(item.get("quantity", 0.0)),
                "total_usd": float(item.get("total_usd", 0.0)),
                "lane_rate": float(lane_rate or 0.0),
                "delta_pct": float(validation.get("delta_pct", 0.0)),
            }

            if lane_metadata:
                anomaly_features.update(
                    {
                        "lane_id": lane_id,
                        "lane_category": lane_metadata.get("category"),
                        "lane_port": lane_metadata.get("port"),
                        "lane_destination": lane_metadata.get("destination"),
                    }
                )

            anomaly_features["charge_group"] = validation.get("charge_group")
            anomaly_features["sheet_name"] = item.get("sheet_name")
            anomaly_features["s_no"] = item.get("s_no")

            detector = self._get_anomaly_detector(lane_id)
            anomaly_payload: Dict[str, Any] = {
                "lane_id": lane_id,
                "lane_metadata": lane_metadata,
                "features": self._format_anomaly_features(anomaly_features),
            }

            if detector and detector.enabled:
                anomaly_result = detector.score_item(anomaly_features)
                anomaly_payload.update(asdict(anomaly_result))

                if anomaly_result.flagged:
                    issue_msg = (
                        "Anomaly detection risk "
                        f"{anomaly_result.risk_level}"
                        f" (score {anomaly_result.score:.2f})"
                    )
                    validation["issues"].append(issue_msg)

                    if anomaly_result.risk_level == "HIGH":
                        validation["status"] = "FAIL"
                        validation["flag"] = "CRITICAL"
                    elif anomaly_result.risk_level == "MEDIUM":
                        if validation["status"] != "FAIL":
                            validation["status"] = "REVIEW_NEEDED"
                        if validation["flag"] not in ["CRITICAL", "HIGH"]:
                            validation["flag"] = "HIGH"
                    elif anomaly_result.risk_level == "LOW":
                        if validation["status"] != "FAIL":
                            validation["status"] = "REVIEW_NEEDED"
                        if validation["flag"] == "OK":
                            validation["flag"] = "WARN"
            else:
                disabled_reason = (
                    "lane_disabled"
                    if lane_id in self.anomaly_disabled_lanes
                    else "disabled"
                )
                anomaly_payload.update(
                    {
                        "enabled": False,
                        "score": 0.0,
                        "risk_level": "DISABLED",
                        "flagged": False,
                        "model": self.anomaly_base_config.get("model", {}).get(
                            "type", "none"
                        ),
                        "details": {"reason": disabled_reason},
                    }
                )

            validation["anomaly_detection"] = anomaly_payload

            # 4. 최종 상태 결정
            if not validation["issues"] and validation["gate_status"] == "PASS":
                validation["status"] = "PASS"
            elif validation["issues"] or validation["gate_status"] == "FAIL":
                if validation["status"] != "FAIL":
                    validation["status"] = "REVIEW_NEEDED"

            # 5. Risk 기반 리뷰 적용
            self._apply_risk_based_review(validation)

        except Exception as e:
            validation["status"] = "ERROR"
            validation["flag"] = "ERROR"
            validation["issues"].append(f"검증 오류: {e}")

        return validation

    def _find_contract_ref_rate(self, item: Dict) -> Optional[float]:
        """
        Contract 항목의 참조 요율 조회 (SHPT 시스템 통합 버전)

        Args:
            item: Invoice 항목

        Returns:
            참조 요율 (USD) 또는 None
        """
        description = item.get("description", "").strip()
        desc_upper = description.upper()

        # 1. ConfigurationManager로 고정 요율 조회 먼저 시도
        # MASTER DO FEE, CUSTOMS CLEARANCE 등
        contract_rate = self.config_manager.get_contract_rate(description)
        if contract_rate is not None:
            return contract_rate

        # 2. Standard Items 키워드 기반 조회
        standard_keywords = [
            ("DO FEE", "DO Fee"),
            ("MASTER DO", "DO Fee"),
            ("CUSTOMS CLEARANCE", "Custom Clearance"),
            ("CUSTOM CLEARANCE", "Custom Clearance"),
            ("TERMINAL HANDLING FEE", "Terminal Handling Charge"),
            ("TERMINAL HANDLING CHARGE", "Terminal Handling Charge"),
            ("TERMINAL HANDLING", "Terminal Handling Charge"),
            ("PORT HANDLING", "Port Handling Charge"),
            ("THC", "Terminal Handling Charge"),
        ]

        for keyword_match, keyword_lookup in standard_keywords:
            if keyword_match in desc_upper:
                # Port 추출 시도
                port = self._extract_port_from_description(description)
                if not port:
                    port = "Khalifa Port"  # 기본값

                # Terminal Handling의 경우 container type에 따라 다름
                if "TERMINAL HANDLING" in keyword_match or keyword_match == "THC":
                    # Container type 추출
                    if "20DC" in desc_upper or "20FT" in desc_upper:
                        return 280.00  # THC_20FT from config
                    elif "40HC" in desc_upper or "40FT" in desc_upper:
                        return 420.00  # THC_40FT from config
                    elif "KG" in desc_upper or "CW:" in desc_upper:
                        return 0.55  # Abu Dhabi Airport per KG

                # Rate Loader로 조회
                ref_rate = self.rate_loader.get_standard_rate(keyword_lookup, port)
                if ref_rate is not None:
                    return ref_rate

        # 3. Inland Trucking (Transportation) 조회 - SHPT 통합 로직
        if (
            "TRANSPORTATION" in desc_upper
            or "TRUCKING" in desc_upper
            or "INLAND" in desc_upper
        ):
            # Description에서 Port와 Destination 파싱
            port, destination = self._parse_transportation_route(description)

            if port and destination:
                # ConfigurationManager로 Lane rate 조회 (SHPT 로직)
                ref_rate = self.config_manager.get_lane_rate(
                    port, destination, "per truck"
                )
                if ref_rate is not None:
                    return ref_rate

                # Lane Map 직접 조회 (SHPT get_standard_rate 방식)
                ref_rate = self.get_standard_rate_shpt_style(
                    port, destination, "per truck"
                )
                if ref_rate is not None:
                    return ref_rate

            # 파싱 실패 시 Lane Map 폴백 (기존 로직 유지)
            if "KHALIFA PORT" in desc_upper and (
                "STORAGE" in desc_upper or "DSV" in desc_upper or "YARD" in desc_upper
            ):
                return 252.00
            elif (
                "DSV" in desc_upper and "KHALIFA" in desc_upper
            ):  # DSV → KHALIFA (EMPTY RETURN)
                return 252.00
            elif "AUH AIRPORT" in desc_upper and "MOSB" in desc_upper:
                if "3 TON PU" in desc_upper or "3T" in desc_upper:
                    return 100.00  # AUH → MOSB (3T PU)
                else:
                    return 200.00  # AUH → MOSB (FB)
            elif "MIRFA" in desc_upper:
                return 420.00
            elif "SHUWEIHAT" in desc_upper or "SHU" in desc_upper:
                return 600.00

        return None

    def get_standard_rate_shpt_style(
        self, port: str, destination: str, unit: str
    ) -> Optional[float]:
        """
        SHPT 시스템의 get_standard_rate 로직 통합
        Lane Map 기반 표준 요율 조회 (정규화 포함)

        Args:
            port: Port 이름
            destination: Destination 이름
            unit: 단위 (예: "per truck")

        Returns:
            표준 요율 (USD) 또는 None
        """
        # Lane Map에서 직접 조회
        lane_key = f"{port}_{destination}".replace(" ", "_").upper()
        if lane_key in self.lane_map:
            return self.lane_map[lane_key].get("rate")

        # 정규화 후 재시도
        normalized_port = port
        normalized_dest = destination

        if self.normalization_map:
            port_aliases = self.normalization_map.get("ports", {})
            dest_aliases = self.normalization_map.get("destinations", {})

            # Port 정규화
            for alias, canonical in port_aliases.items():
                if alias.upper() in port.upper():
                    normalized_port = canonical
                    break

            # Destination 정규화
            for alias, canonical in dest_aliases.items():
                if alias.upper() in destination.upper():
                    normalized_dest = canonical
                    break

        # 정규화된 키로 재조회
        lane_key = f"{normalized_port}_{normalized_dest}".replace(" ", "_").upper()
        if lane_key in self.lane_map:
            return self.lane_map[lane_key].get("rate")

        return None

    def _extract_port_from_description(self, description: str) -> Optional[str]:
        """Description에서 Port 이름 추출 (정규화 별칭 사용)"""
        desc_upper = description.upper()

        # ConfigurationManager 별칭 사용
        if self.normalization_map:
            port_aliases = self.normalization_map.get("ports", {})
            for alias, canonical in port_aliases.items():
                if alias.upper() in desc_upper:
                    return canonical

        # 폴백: 기존 로직
        if "KHALIFA" in desc_upper or "KP" in desc_upper:
            return "Khalifa Port"
        elif "JEBEL ALI" in desc_upper or "JAP" in desc_upper:
            return "Jebel Ali Port"
        elif "ABU DHABI AIRPORT" in desc_upper or "AUH" in desc_upper:
            return "Abu Dhabi Airport"
        elif "DUBAI AIRPORT" in desc_upper or "DXB" in desc_upper:
            return "Dubai Airport"
        elif "MUSSAFAH" in desc_upper or "MOSB" in desc_upper:
            return "Musaffah Port"

        return None

    def _parse_transportation_route(
        self, description: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Transportation description에서 Port와 Destination 파싱

        예: "TRANSPORTATION FROM KHALIFA PORT TO STORAGE YARD"

        Returns:
            (port, destination) 튜플
        """
        desc_upper = description.upper()

        # FROM ... TO ... 패턴
        import re

        match = re.search(r"FROM\s+(.+?)\s+TO\s+(.+)", desc_upper)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()

            # 정규화
            port = self._extract_port_from_description(origin)
            dest = self._normalize_destination(destination)

            return (port, dest)

        return (None, None)

    def _normalize_destination(self, destination: str) -> Optional[str]:
        """Destination 정규화 (ConfigurationManager 별칭 사용)"""
        dest_upper = destination.upper()

        # ConfigurationManager 별칭 사용
        if self.normalization_map:
            dest_aliases = self.normalization_map.get("destinations", {})
            for alias, canonical in dest_aliases.items():
                if alias.upper() in dest_upper:
                    return canonical

        # 폴백: 기존 로직
        if "MIRFA" in dest_upper:
            return "MIRFA SITE"
        elif "SHUWEIHAT" in dest_upper or "SHU" in dest_upper:
            return "SHUWEIHAT Site"
        elif "STORAGE" in dest_upper or "YARD" in dest_upper or "DSV" in dest_upper:
            return "Storage Yard"

        return destination

    def map_supporting_documents(self) -> Dict[str, List[Dict]]:
        """증빙문서 매핑 생성"""
        supporting_docs = {}

        for docs_path in self.supporting_docs_paths:
            if not docs_path.exists():
                logging.warning(f"⚠️ 증빙문서 폴더 없음: {docs_path}")
                continue

            try:
                pdf_files = list(docs_path.rglob("*.pdf"))
                logging.info(f"[DOCS] {docs_path.name}: {len(pdf_files)} PDFs found")

                for pdf_file in pdf_files:
                    # 파일명에서 Shipment ID 추출
                    shipment_id = self.extract_shipment_id(pdf_file.name)

                    if shipment_id:
                        if shipment_id not in supporting_docs:
                            supporting_docs[shipment_id] = []

                        doc_type = self.extract_doc_type(pdf_file.name)

                        supporting_docs[shipment_id].append(
                            {
                                "file_name": pdf_file.name,
                                "file_path": str(pdf_file),
                                "doc_type": doc_type,
                                "file_size": pdf_file.stat().st_size,
                            }
                        )

            except Exception as e:
                logging.error(f"증빙문서 매핑 오류: {e}")

        logging.info(
            f"[OK] Total {len(supporting_docs)} shipment supporting documents mapped"
        )
        return supporting_docs

    def _create_anomaly_detector(
        self, config: Dict[str, Any]
    ) -> Optional[AnomalyDetectionService]:
        """이상 탐지기 생성 / Create anomaly detector from config."""

        if not config.get("enabled", False):
            return None

        try:
            detector = AnomalyDetectionService(config)
        except Exception as exc:
            logging.error(f"⚠️ Anomaly detector initialization failed: {exc}")
            return None

        if not detector.enabled:
            return None

        logging.info(
            "Anomaly detection enabled: model=%s",
            config.get("model", {}).get("type", "unknown"),
        )
        return detector

    def _get_anomaly_detector(
        self, lane_id: Optional[str]
    ) -> Optional[AnomalyDetectionService]:
        """Lane별 이상 탐지기 조회 / Resolve detector for lane."""

        if lane_id and lane_id in self.anomaly_disabled_lanes:
            return None

        if lane_id not in self.anomaly_detectors:
            lane_config = self.config_manager.get_anomaly_detection_config(lane_id)
            if not lane_config.get("enabled", False):
                if lane_id:
                    self.anomaly_disabled_lanes.add(lane_id)
                self.anomaly_detectors[lane_id] = None
            else:
                self.anomaly_detectors[lane_id] = self._create_anomaly_detector(
                    lane_config
                )

        if lane_id is None:
            return self.anomaly_detectors.get(None)

        return self.anomaly_detectors.get(lane_id)

    def _resolve_lane_metadata(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lane 메타데이터 계산 / Resolve lane metadata for item."""

        description = item.get("description", "")
        port, destination = self._parse_transportation_route(description)
        if port and destination:
            return self.config_manager.get_lane_metadata(port, destination) or None
        return None

    @staticmethod
    def _format_anomaly_features(features: Dict[str, Any]) -> Dict[str, Any]:
        """이상 탐지 피처 정규화 / Normalise anomaly features for storage."""

        formatted: Dict[str, Any] = {}
        for key, value in features.items():
            if isinstance(value, float):
                formatted[key] = round(value, 2)
            else:
                formatted[key] = value
        return formatted

    def _summarize_anomalies(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이상 탐지 집계 / Summarise anomaly results across items."""

        base_enabled = bool(self.anomaly_base_config.get("enabled", False))
        summary = {
            "enabled": base_enabled,
            "model": self.anomaly_base_config.get("model", {}).get("type", "none"),
            "total_scored": 0,
            "flagged_items": 0,
            "average_score": 0.0,
            "risk_counts": {},
        }

        lane_feature_map: Dict[Optional[str], List[Dict[str, Any]]] = {}
        for item in items:
            anomaly_data = item.get("anomaly_detection")
            if not anomaly_data or not anomaly_data.get("features"):
                continue

            lane_id = anomaly_data.get("lane_id")
            if lane_id in self.anomaly_disabled_lanes:
                continue

            lane_feature_map.setdefault(lane_id, []).append(anomaly_data["features"])

        combined_scores: List[float] = []
        for lane_id, feature_list in lane_feature_map.items():
            detector = self._get_anomaly_detector(lane_id)
            if not detector or not detector.enabled:
                continue

            batch_result = detector.score_batch(feature_list)
            summary["total_scored"] += batch_result.get("total_scored", 0)
            summary["flagged_items"] += batch_result.get("flagged_items", 0)
            for risk_level, count in batch_result.get("risk_counts", {}).items():
                summary["risk_counts"][risk_level] = (
                    summary["risk_counts"].get(risk_level, 0) + count
                )
            combined_scores.append(
                batch_result.get("average_score", 0.0)
                * batch_result.get("total_scored", 0)
            )

        if summary["total_scored"] > 0 and combined_scores:
            summary["average_score"] = round(
                sum(combined_scores) / summary["total_scored"],
                2,
            )

        return summary

    def extract_shipment_id(self, filename: str) -> Optional[str]:
        """파일명에서 Shipment ID 추출 (개선)"""
        if "HVDC-ADOPT-" in filename:
            # HVDC-ADOPT-SCT-0126_BOE.pdf 형식
            parts = filename.split("_")
            if parts:
                # 첫 번째 부분이 Shipment ID
                shipment_id = parts[0]
                # 추가 정제: .pdf 제거 등
                shipment_id = shipment_id.replace(".pdf", "")
                return shipment_id
        elif "HVDC-" in filename:
            parts = filename.split("_")
            return parts[0] if parts else None
        return None

    def extract_doc_type(self, filename: str) -> str:
        """파일명에서 문서 타입 추출"""
        fn_upper = filename.upper()
        if "BOE" in fn_upper:
            return "BOE"
        elif "DO" in fn_upper and "DN" not in fn_upper:
            return "DO"
        elif "DN" in fn_upper:
            return "DN"
        elif "CARRIER" in fn_upper or "INVOICE" in fn_upper:
            return "CarrierInvoice"
        else:
            return "Other"

    # ==================== 메인 감사 실행 ====================

    def run_full_enhanced_audit(self):
        """전체 Enhanced 감사 실행"""
        try:
            logging.info("=" * 80)
            logging.info("[START] SHPT Enhanced Sept 2025 full audit")
            logging.info("=" * 80)

            # 1. Excel 파일 로드
            excel_file = self.load_invoice_sheets()
            if excel_file is None:
                return None

            # 2. 증빙문서 매핑
            supporting_docs = self.map_supporting_documents()

            # 3. 모든 시트 처리
            all_items = []
            sheet_summary = []

            logging.info("\n📋 시트별 송장 항목 추출 및 검증 중...\n")

            for sheet_name in excel_file.sheet_names:
                if sheet_name.startswith("_") or sheet_name in [
                    "Summary",
                    "Template",
                    "SEPT",
                    "MasterData",  # VBA 출력물이므로 skip
                ]:
                    continue

                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    items = self.extract_invoice_items(df, sheet_name)

                    if items:
                        # 각 항목 검증 - 시트명에서 Shipment ID 올바르게 추출
                        if sheet_name.startswith("SCT"):
                            shipment_id = f"HVDC-ADOPT-SCT-{sheet_name[3:]}"  # SCT0126 → HVDC-ADOPT-SCT-0126
                        elif sheet_name.startswith("HE"):
                            shipment_id = f"HVDC-ADOPT-HE-{sheet_name[2:]}"  # HE0471 → HVDC-ADOPT-HE-0471
                        elif sheet_name.startswith("SIM"):
                            shipment_id = f"HVDC-ADOPT-SIM-{sheet_name[3:]}"  # SIM0092 → HVDC-ADOPT-SIM-0092
                        else:
                            shipment_id = f"HVDC-ADOPT-{sheet_name}"

                        sheet_docs = supporting_docs.get(shipment_id, [])

                        # PDF 파싱 및 검증 (통합 활성화 시)
                        pdf_validation_data = None
                        if self.pdf_integration and sheet_docs:
                            try:
                                pdf_parse_result = (
                                    self.pdf_integration.parse_supporting_docs(
                                        shipment_id, sheet_docs
                                    )
                                )
                                pdf_validation_data = pdf_parse_result
                                logging.debug(
                                    f"  [PDF] {shipment_id}: Parsed {pdf_parse_result['parsed_count']} docs"
                                )
                            except Exception as e:
                                logging.warning(
                                    f"  [PDF] {shipment_id} parsing failed: {e}"
                                )

                        for item in items:
                            validation = self.validate_enhanced_item(item, sheet_docs)

                            # PDF 검증 통합
                            if pdf_validation_data and self.pdf_integration:
                                try:
                                    enriched = (
                                        self.pdf_integration.validate_invoice_with_docs(
                                            item, shipment_id, sheet_docs
                                        )
                                    )

                                    # PDF 검증 정보 병합
                                    validation["pdf_validation"] = enriched.get(
                                        "pdf_validation", {}
                                    )
                                    validation["demurrage_risk"] = enriched.get(
                                        "demurrage_risk"
                                    )

                                    # PDF Gates 실행 (Gate-11~14)
                                    pdf_gates_result = (
                                        self.pdf_integration.run_pdf_gates(
                                            item, pdf_validation_data
                                        )
                                    )

                                    # Gate 점수 업데이트 (기존 Gate + PDF Gates 통합)
                                    if pdf_gates_result:
                                        existing_gates = validation.get("gates", {})

                                        # PDF Gates 추가
                                        for gate_detail in pdf_gates_result.get(
                                            "Gate_Details", []
                                        ):
                                            gate_name = gate_detail["gate"]
                                            existing_gates[gate_name] = {
                                                "status": gate_detail["result"],
                                                "score": gate_detail["score"],
                                                "details": gate_detail["details"],
                                            }

                                        # 전체 Gate 점수 재계산
                                        all_gates = list(existing_gates.values())
                                        avg_score = (
                                            sum(g["score"] for g in all_gates)
                                            / len(all_gates)
                                            if all_gates
                                            else 0
                                        )
                                        fails = [
                                            name
                                            for name, g in existing_gates.items()
                                            if g["status"] == "FAIL"
                                        ]

                                        validation["gate_score"] = round(avg_score, 1)
                                        validation["gate_status"] = (
                                            "FAIL" if fails else "PASS"
                                        )
                                        validation["gate_fails"] = ",".join(fails)
                                        validation["gates"] = existing_gates

                                except Exception as e:
                                    logging.warning(
                                        f"  [PDF] PDF validation failed for item {item.get('s_no')}: {e}"
                                    )

                            # 증빙문서 정보 추가
                            validation["supporting_docs_list"] = sheet_docs
                            validation["evidence_count"] = len(sheet_docs)
                            validation["evidence_types"] = list(
                                set(doc["doc_type"] for doc in sheet_docs)
                            )
                            all_items.append(validation)

                        sheet_summary.append(
                            {
                                "sheet_name": sheet_name,
                                "item_count": len(items),
                                "supporting_docs": len(sheet_docs),
                                "shipment_id": shipment_id,
                            }
                        )

                except Exception as e:
                    logging.error(f"  [ERROR] {sheet_name} processing error: {e}")

            logging.info(
                f"\n[OK] Total {len(all_items)} items extracted and validated from {len(sheet_summary)} sheets"
            )

            # 4. 통계 계산
            total_items = len(all_items)
            pass_items = len([item for item in all_items if item["status"] == "PASS"])
            review_items = len(
                [
                    item
                    for item in all_items
                    if item["status"] == "REVIEW_NEEDED" or item["status"] == "REVIEW"
                ]
            )
            error_items = len([item for item in all_items if item["status"] == "ERROR"])
            fail_items = len([item for item in all_items if item["status"] == "FAIL"])

            portal_fee_items = len(
                [item for item in all_items if item["charge_group"] == "PortalFee"]
            )
            contract_items = len(
                [item for item in all_items if item["charge_group"] == "Contract"]
            )
            at_cost_items = len(
                [item for item in all_items if item["charge_group"] == "AtCost"]
            )

            total_amount = sum(item["total_usd"] for item in all_items)

            gate_pass_items = len(
                [item for item in all_items if item.get("gate_status") == "PASS"]
            )
            avg_gate_score = (
                sum(item.get("gate_score", 0) for item in all_items) / total_items
                if total_items > 0
                else 0
            )

            anomaly_summary = self._summarize_anomalies(all_items)

            # 5. 결과 생성
            audit_result = {
                "audit_info": {
                    "invoice_file": self.excel_file.name,
                    "audit_date": datetime.now().isoformat(),
                    "system_type": self.system_type,
                    "scope": self.scope,
                    "supporting_docs_paths": [
                        str(p) for p in self.supporting_docs_paths
                    ],
                    "total_supporting_docs": sum(
                        len(pdfs) for pdfs in supporting_docs.values()
                    ),
                },
                "statistics": {
                    "total_sheets": len(sheet_summary),
                    "total_items": total_items,
                    "pass_items": pass_items,
                    "review_items": review_items,
                    "fail_items": fail_items,
                    "error_items": error_items,
                    "pass_rate": (
                        f"{(pass_items/total_items*100):.1f}%"
                        if total_items > 0
                        else "0%"
                    ),
                    "total_amount_usd": total_amount,
                    "charge_group_breakdown": {
                        "Contract": contract_items,
                        "AtCost": at_cost_items,
                        "PortalFee": portal_fee_items,
                        "Other": total_items
                        - contract_items
                        - at_cost_items
                        - portal_fee_items,
                    },
                    "gate_validation": {
                        "gate_pass_items": gate_pass_items,
                        "gate_pass_rate": (
                            f"{(gate_pass_items/total_items*100):.1f}%"
                            if total_items > 0
                            else "0%"
                        ),
                        "avg_gate_score": round(avg_gate_score, 1),
                    },
                    "anomaly_detection": anomaly_summary,
                },
                "supporting_docs": supporting_docs,
                "sheet_summary": sheet_summary,
                "items": all_items,
                "anomaly_detection": anomaly_summary,
            }

            # 6. 결과 저장
            self.save_enhanced_results(audit_result)

            # 7. 결과 출력
            self.print_enhanced_summary(audit_result)

            return audit_result

        except Exception as e:
            logging.error(f"[ERROR] Full audit error: {e}")
            import traceback

            logging.error(traceback.format_exc())
            return None

    def save_enhanced_results(self, audit_result):
        """Enhanced 감사 결과 저장 (Excel 출력 추가)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # JSON 파일 저장 (새 폴더 구조)
            json_file = (
                self.out_dir
                / "JSON"
                / f"shpt_sept_2025_enhanced_result_{timestamp}.json"
            )
            json_file.parent.mkdir(parents=True, exist_ok=True)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False)

            logging.info(f"\n💾 JSON 결과 저장: {json_file}")

            # CSV 파일 저장 (새 폴더 구조)
            csv_file = (
                self.out_dir / "CSV" / f"shpt_sept_2025_enhanced_result_{timestamp}.csv"
            )
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            items_df = pd.DataFrame(audit_result["items"])
            items_df.to_csv(csv_file, index=False, encoding="utf-8-sig")

            logging.info(f"💾 CSV 결과 저장: {csv_file}")

            # Excel 보고서 생성 (새로 추가)
            try:
                from create_enhanced_excel_report import EnhancedExcelReportGenerator

                excel_generator = EnhancedExcelReportGenerator()
                excel_results = excel_generator.create_comprehensive_report(
                    csv_path=str(csv_file),
                    json_path=str(json_file),
                    output_dir=str(self.out_dir / "Reports"),
                )

                if "integrated_report" in excel_results:
                    logging.info(
                        f"📊 Excel 통합 보고서 생성: {excel_results['integrated_report']}"
                    )
                else:
                    logging.warning(
                        f"Excel 보고서 생성 실패: {excel_results.get('error', 'Unknown error')}"
                    )

            except ImportError as e:
                logging.warning(f"Excel 보고서 생성기 모듈을 찾을 수 없습니다: {e}")
            except Exception as e:
                logging.error(f"Excel 보고서 생성 중 오류 발생: {e}")

            # 요약 리포트 저장 (새 폴더 구조)
            summary_file = (
                self.out_dir
                / "Reports"
                / f"shpt_sept_2025_enhanced_summary_{timestamp}.txt"
            )
            summary_file.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("SHPT Enhanced 9월 2025 Invoice Audit 결과\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"감사 일시: {audit_result['audit_info']['audit_date']}\n")
                f.write(f"파일: {audit_result['audit_info']['invoice_file']}\n")
                f.write(f"시스템: {audit_result['audit_info']['system_type']}\n\n")

                f.write("📊 통계\n")
                f.write("-" * 80 + "\n")
                stats = audit_result["statistics"]
                f.write(f"총 시트 수: {stats['total_sheets']}\n")
                f.write(f"총 항목 수: {stats['total_items']}\n")
                f.write(f"PASS: {stats['pass_items']} ({stats['pass_rate']})\n")
                f.write(f"검토 필요: {stats['review_items']}\n")
                f.write(f"FAIL: {stats['fail_items']}\n")
                f.write(f"오류: {stats['error_items']}\n")
                f.write(f"총 금액: ${stats['total_amount_usd']:,.2f} USD\n\n")

                f.write("📋 Charge Group 분석 (Enhanced)\n")
                f.write("-" * 80 + "\n")
                cg = stats["charge_group_breakdown"]
                f.write(f"Contract: {cg['Contract']}개\n")
                f.write(f"AtCost: {cg['AtCost']}개\n")
                f.write(f"PortalFee: {cg['PortalFee']}개 ← Enhanced 기능\n")
                f.write(f"Other: {cg['Other']}개\n\n")

                f.write("🚪 Gate 검증 결과 (Enhanced)\n")
                f.write("-" * 80 + "\n")
                gate = stats["gate_validation"]
                f.write(
                    f"Gate PASS: {gate['gate_pass_items']}개 ({gate['gate_pass_rate']})\n"
                )
                f.write(f"평균 Gate Score: {gate['avg_gate_score']}\n\n")

                f.write("📋 시트별 요약\n")
                f.write("-" * 80 + "\n")
                for sheet in audit_result["sheet_summary"]:
                    f.write(
                        f"  - {sheet['sheet_name']}: {sheet['item_count']}개 항목 (증빙 {sheet['supporting_docs']}개)\n"
                    )

            logging.info(f"💾 요약 리포트 저장: {summary_file}")

        except Exception as e:
            logging.error(f"[ERROR] Result save error: {e}")

    def print_enhanced_summary(self, audit_result):
        """Enhanced 결과 요약 출력"""
        logging.info("\n" + "=" * 80)
        logging.info("📊 SHPT Enhanced 감사 결과 요약")
        logging.info("=" * 80)

        stats = audit_result["statistics"]
        logging.info(f"\n총 시트 수: {stats['total_sheets']}")
        logging.info(f"총 항목 수: {stats['total_items']}")
        logging.info(f"PASS: {stats['pass_items']} ({stats['pass_rate']})")
        logging.info(f"검토 필요: {stats['review_items']}")
        logging.info(f"FAIL: {stats['fail_items']}")
        logging.info(f"총 금액: ${stats['total_amount_usd']:,.2f} USD")

        logging.info("\n📋 Charge Group 분석:")
        cg = stats["charge_group_breakdown"]
        logging.info(f"  - Contract: {cg['Contract']}개")
        logging.info(f"  - AtCost: {cg['AtCost']}개")
        logging.info(f"  - PortalFee: {cg['PortalFee']}개 ← Enhanced 기능")
        logging.info(f"  - Other: {cg['Other']}개")

        logging.info("\n🚪 Gate 검증 결과:")
        gate = stats["gate_validation"]
        logging.info(
            f"  - Gate PASS: {gate['gate_pass_items']}개 ({gate['gate_pass_rate']})"
        )
        logging.info(f"  - 평균 Gate Score: {gate['avg_gate_score']}")

        logging.info("\n📋 시트별 항목 수:")
        for sheet in audit_result["sheet_summary"]:
            logging.info(f"  - {sheet['sheet_name']}: {sheet['item_count']}개")

        logging.info("\n" + "=" * 80)
        logging.info("[COMPLETE] SHPT Enhanced audit finished!")
        logging.info("=" * 80)


def main():
    """메인 실행 함수"""
    print("[Shipment Audit Engine] Invoice Audit System")
    print("=" * 80)

    auditor = ShipmentAuditEngine()
    result = auditor.run_full_enhanced_audit()

    if result:
        logging.info("\n[SUCCESS] Enhanced audit completed successfully.")
        logging.info(f"[SAVED] Results saved to Results/Sept_2025 directory.")

        # Portal Fee 항목 상세 출력
        portal_fee_items = [
            item for item in result["items"] if item["charge_group"] == "PortalFee"
        ]
        if portal_fee_items:
            logging.info(f"\n[PORTAL FEE] {len(portal_fee_items)} items:")
            for pf_item in portal_fee_items[:5]:  # 최대 5개만 출력
                logging.info(f"  - {pf_item['description']}")
                logging.info(f"    Draft: ${pf_item['unit_rate']:.2f}")
                if pf_item["doc_aed"]:
                    logging.info(f"    Doc AED: {pf_item['doc_aed']}")
                    logging.info(f"    Ref USD: ${pf_item['ref_rate_usd']:.2f}")
                logging.info(f"    Delta: {pf_item['delta_pct']:.2f}%")
                logging.info(f"    Tolerance: +/-{pf_item['tolerance']*100}%")
                logging.info(f"    Status: {pf_item['status']}")
    else:
        logging.error("\n[ERROR] Enhanced audit failed")


if __name__ == "__main__":
    main()
