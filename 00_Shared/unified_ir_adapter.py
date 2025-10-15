#!/usr/bin/env python3
"""
Unified IR to HVDC Data Adapter
Unified IR (Docling/ADE) → HVDC Invoice/BOE/DO/DN 데이터 변환

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Integration
"""

import re
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedIRAdapter:
    """
    Unified IR → HVDC 데이터 변환 어댑터
    """

    def __init__(self, ir_schema_path: Optional[str] = None):
        """
        Args:
            ir_schema_path: unified_ir_schema.yaml 경로
        """
        self.schema = None
        self.invoice_selectors = {}

        if ir_schema_path:
            self._load_schema(ir_schema_path)
        else:
            # Default selectors (embedded)
            self.invoice_selectors = self._get_default_selectors()

        logger.info("UnifiedIRAdapter initialized")

    def _load_schema(self, schema_path: str):
        """YAML 스키마 로드"""
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = yaml.safe_load(f)

            # Extract invoice selectors
            if self.schema and "mapping" in self.schema:
                mapping = self.schema.get("mapping", {})
                invoice_mapping = mapping.get("invoice", {})
                self.invoice_selectors = invoice_mapping.get("selectors", {})

            logger.info(
                f"Schema loaded: {len(self.invoice_selectors)} invoice selectors"
            )

        except Exception as e:
            logger.warning(f"Schema load failed: {e}. Using default selectors.")
            self.invoice_selectors = self._get_default_selectors()

    def _get_default_selectors(self) -> Dict[str, Any]:
        """기본 Invoice 셀렉터 (embedded)"""
        return {
            "invoice_no": {
                "any": [
                    {
                        "regex": r"(Invoice No\.?|INV\.? No\.?)\s*[:#]?\s*([A-Za-z0-9\-_/]+)",
                        "group": 2,
                    }
                ]
            },
            "bl_no": {
                "any": [
                    {
                        "regex": r"(B\/L|BL|Bill of Lading)\s*(No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-_/]+)",
                        "group": 3,
                    }
                ]
            },
            "order_ref": {
                "any": [
                    {
                        "regex": r"(Order Ref\.?|Job No\.?)\s*[:#]?\s*([A-Z]+-\d+)",
                        "group": 2,
                    }
                ]
            },
            "total_amount": {
                "any": [
                    {
                        "regex": r"(Grand\s*Total|Total\s*Amount)\s*[:]?\s*([0-9,]+\.?\d*)",
                        "group": 2,
                    }
                ]
            },
            "currency": {"any": [{"regex": r"\b(USD|AED|EUR|GBP)\b", "group": 1}]},
        }

    def extract_invoice_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified IR에서 Invoice 필드 추출

        Args:
            unified_ir: Unified IR (Docling/ADE output)

        Returns:
            {
                "invoice_no": "INV-12345",
                "bl_no": "BL-67890",
                "order_ref": "SCT-0126",
                "items": [
                    {"description": "INLAND TRUCKING", "unit_rate": 252.00, "qty": 1, "amount": 252.00},
                    ...
                ],
                "total_amount": 21402.20,
                "currency": "USD",
                "engine_used": "ade" or "docling",
                "confidence": 0.95
            }
        """
        extracted = {
            "engine_used": unified_ir.get("engine", "unknown"),
            "pages": unified_ir.get("pages", 0),
            "confidence": unified_ir.get("meta", {}).get("confidence", 0.0),
        }

        blocks = unified_ir.get("blocks", [])

        # Extract full text from all blocks
        full_text = self._extract_full_text(blocks)

        # Extract fields using selectors
        for field_name, selector_config in self.invoice_selectors.items():
            value = self._apply_selectors(full_text, selector_config)
            if value:
                extracted[field_name] = value

        # Extract Summary section (TOTAL, VAT, Subtotal) - NEW
        summary = self._extract_summary_section(blocks)

        # Fallback: Summary 블록 (우선순위 2: 좌표 기반)
        for block in blocks:
            if block.get("type") == "summary" and block.get("total_amount"):
                if not summary.get("total"):
                    summary["total"] = block["total_amount"]
                    currency = block.get("currency", "USD")

                    # AED → USD 변환
                    if currency == "AED" and not any(
                        "USD" in b.get("text", "") for b in blocks
                    ):
                        summary["total"] = round(summary["total"] / 3.67, 2)
                        logger.info(
                            f"[SUMMARY BLOCK] Converted AED ${block['total_amount']:.2f} → USD ${summary['total']:.2f}"
                        )
                    else:
                        logger.info(
                            f"[SUMMARY BLOCK] Using coordinate-based total: ${summary['total']:.2f} {currency}"
                        )

        # Extract table data (invoice line items) - 테이블과 텍스트 모두 파싱
        extracted["items"] = self._extract_table_items(blocks)

        # If no items from tables, try parsing from text
        if not extracted["items"]:
            extracted["items"] = self._extract_items_from_text(full_text)

        # Use Summary total_amount if available (우선순위)
        if summary.get("total"):
            extracted["total_amount"] = summary["total"]
            logger.info(f"[INVOICE] Using Summary total: ${summary['total']:.2f}")

        # Store additional summary info
        if summary.get("subtotal"):
            extracted["subtotal"] = summary["subtotal"]
        if summary.get("vat"):
            extracted["vat"] = summary["vat"]
        if summary.get("exchange_rate"):
            extracted["exchange_rate"] = summary["exchange_rate"]

        # Post-processing
        extracted = self._post_process_extracted_data(extracted)

        logger.info(
            f"Extracted {len(extracted.get('items', []))} items from {extracted.get('engine_used')} output"
        )

        return extracted

    def _extract_full_text(self, blocks: List[Dict]) -> str:
        """모든 블록에서 텍스트 추출"""
        text_parts = []

        for block in blocks:
            block_type = block.get("type")

            if block_type == "text":
                text_parts.append(block.get("text", ""))
            elif block_type == "header":
                text_parts.append(block.get("text", ""))
            elif block_type == "footer":
                text_parts.append(block.get("text", ""))

        return "\n".join(text_parts)

    def _apply_selectors(self, text: str, selector_config: Dict) -> Optional[str]:
        """셀렉터 적용하여 필드 추출"""
        for selector in selector_config.get("any", []):
            pattern = selector.get("regex")
            group = selector.get("group", 0)

            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(group).strip()

        return None

    def _extract_table_items(self, blocks: List[Dict]) -> List[Dict]:
        """
        Invoice line items 추출 (테이블 블록에서)

        Returns:
            [
                {"description": "...", "qty": 1.0, "unit_rate": 252.00, "amount": 252.00},
                ...
            ]
        """
        items = []

        for block in blocks:
            if block.get("type") == "table":
                # Support both formats:
                # 1. {"table": {"rows": [...]}}  (original)
                # 2. {"rows": [...]}  (direct from celery_app)
                if "table" in block:
                    rows = block.get("table", {}).get("rows", [])
                else:
                    rows = block.get("rows", [])

                # Skip if no rows
                if not rows or len(rows) < 2:
                    continue

                # Skip header row (assume first row is header)
                for row_idx, row in enumerate(rows[1:], start=1):
                    if not row or len(row) < 2:
                        continue  # Too few columns

                    # Flexible parsing based on column count
                    item = self._parse_table_row(row, row_idx)
                    if item and item.get("description"):
                        items.append(item)

        return items

    def _parse_table_row(self, row: List[str], row_idx: int) -> Optional[Dict]:
        """
        테이블 행 파싱 (Improved)

        Flexible parsing:
        - Find first non-empty cell as description
        - Find last non-empty numeric cell as amount
        - Extract rate from description if embedded (e.g., "DO FEE AED 150.00")
        """
        try:
            # Clean row data (convert None to empty string)
            row_cleaned = [str(cell).strip() if cell else "" for cell in row]

            # Filter non-empty cells
            non_empty = [
                (i, cell)
                for i, cell in enumerate(row_cleaned)
                if cell and cell.lower() != "none"
            ]

            if not non_empty:
                return None

            # First non-empty cell = description
            desc_idx, description = non_empty[0]

            # Skip Summary rows (NEW)
            desc_upper = description.upper()
            summary_keywords = [
                "SUB TOTAL",
                "SUBTOTAL",
                "SUB-TOTAL",
                "VAT",
                "VALUE ADDED TAX",
                "TAX",
                "TOTAL NET",
                "TOTAL NET AMOUNT",
                "NET TOTAL",
                "GRAND TOTAL",
                "TOTAL",
                "OVERALL TOTAL",
            ]

            # Check if this is a summary row
            for keyword in summary_keywords:
                if keyword in desc_upper:
                    # Strict check: not part of a larger description
                    if (
                        desc_upper.strip() == keyword
                        or desc_upper.startswith(keyword + " ")
                        or desc_upper.endswith(" " + keyword)
                    ):
                        logger.debug(f"[SKIP] Summary row: {description}")
                        return None

            # Last non-empty cell = try as amount
            last_idx, last_cell = non_empty[-1]
            amount = self._parse_number(last_cell, default=0.0)

            # If last cell is not numeric, try to extract amount from description
            if amount == 0.0:
                # Pattern: "Description AED/USD amount"
                import re

                match = re.search(r"(AED|USD)\s+([0-9,]+\.?\d*)", description)
                if match:
                    amount = self._parse_number(match.group(2))

            # Skip if no valid data
            if not description or (amount == 0.0 and len(description) < 10):
                return None

            return {
                "description": description,
                "qty": 1.0,
                "unit_rate": amount if amount > 0 else 0.0,
                "amount": amount if amount > 0 else 0.0,
            }

        except Exception as e:
            logger.warning(f"Row parsing failed: {e}")
            return None

    def _parse_number(self, value_str: str, default: float = 0.0) -> float:
        """숫자 파싱 (쉼표 제거, 기본값 처리)"""
        try:
            # Remove commas and whitespace
            cleaned = str(value_str).replace(",", "").replace(" ", "").strip()

            if not cleaned or cleaned == "-" or cleaned.lower() == "n/a":
                return default

            return float(cleaned)

        except:
            return default

    def _extract_items_from_text(self, text: str) -> List[Dict]:
        """
        텍스트에서 키-값 쌍 추출 (테이블이 없을 경우 Fallback)

        Pattern: "Description AED/USD amount"

        Returns:
            List of items
        """
        items = []

        # Pattern: "Description ... AED/USD ... amount"
        # Example: "Container Return Service Charge AED 535.00"
        pattern = r"([A-Za-z\s\(\)]+?)\s+(AED|USD)\s+([0-9,]+\.?\d*)"

        matches = re.finditer(pattern, text, re.MULTILINE)

        for match in matches:
            description = match.group(1).strip()
            currency = match.group(2)
            amount_str = match.group(3)

            # Skip headers/labels and summary keywords (EXPANDED)
            skip_keywords = [
                "TOTAL",
                "SUBTOTAL",
                "SUB TOTAL",
                "SUB-TOTAL",
                "VAT (",
                "VALUE ADDED TAX",
                "GRAND TOTAL",
                "OVERALL TOTAL",
                "TOTAL NET",
                "TOTAL NET AMOUNT",
                "NET TOTAL",
                "CURRENCY",
                "INVOICE",
                "BILL",
                "SUMMARY",
            ]
            if any(skip in description.upper() for skip in skip_keywords):
                continue

            amount = self._parse_number(amount_str)

            if amount > 0 and len(description) > 5:
                items.append(
                    {
                        "description": description,
                        "qty": 1.0,
                        "unit_rate": amount,
                        "amount": amount,
                        "currency": currency,
                    }
                )

        logger.info(f"Extracted {len(items)} items from text (fallback)")
        return items

    def _extract_summary_section(self, blocks: List[Dict]) -> Dict[str, float]:
        """
        PDF Summary 섹션에서 SUB TOTAL, VAT, TOTAL 추출

        Patterns:
        1. "TOTAL" 우측 (같은 줄): "TOTAL    556.50"
        2. "TOTAL" 아래 줄: 라벨과 금액이 별도 행
        3. "Total Net Amount Inclusive of Tax:    556.50"

        Returns:
            {
                "subtotal": 530.00,
                "vat": 26.50,
                "total": 556.50,
                "exchange_rate": 3.6725  # Optional: R.O.E. 환율
            }
        """
        summary = {}

        # 전체 텍스트 추출
        full_text = self._extract_full_text(blocks)

        # Pattern 1: 같은 줄에 라벨과 금액 (우측)
        # "SUB TOTAL    530.00" or "TOTAL:    556.50"
        # CRITICAL: 순서 중요! 긴 키워드부터 매칭 (SUB TOTAL before TOTAL)
        summary_patterns = {
            "grand_total": r"(GRAND\s*TOTAL|Grand\s*Total)\s*:?\s*([0-9,]+\.?\d*)",
            "subtotal": r"(SUB\s*TOTAL|Subtotal)\s*:?\s*([0-9,]+\.?\d*)",
            "total_net": r"(TOTAL\s*NET\s*AMOUNT[^:]*|Total\s*Net\s*Amount[^:]*)\s*:?\s*([0-9,]+\.?\d*)",
            "vat": r"(VAT|Value\s*Added\s*Tax)\s*(?:\([^)]*\))?\s*:?\s*([0-9,]+\.?\d*)",
            "total": r"(?<!SUB\s)(?<!GRAND\s)(?<!NET\s)(TOTAL|Total)(?!\s*NET)\s*:?\s*([0-9,]+\.?\d*)",
        }

        for key, pattern in summary_patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                # 마지막 그룹이 금액
                amount_str = match.group(match.lastindex).strip()
                amount = self._parse_number(amount_str)

                if amount > 0:
                    # Grand Total이 있으면 Total 대신 사용
                    if key == "grand_total":
                        summary["total"] = amount
                        logger.debug(f"[SUMMARY] Grand Total: {amount}")
                    elif key == "total_net":
                        summary["total"] = amount
                        logger.debug(f"[SUMMARY] Total Net Amount: {amount}")
                    elif key == "total" and "total" not in summary:
                        summary["total"] = amount
                        logger.debug(f"[SUMMARY] Total: {amount}")
                    elif key == "subtotal":
                        summary["subtotal"] = amount
                        logger.debug(f"[SUMMARY] Subtotal: {amount}")
                    elif key == "vat":
                        summary["vat"] = amount
                        logger.debug(f"[SUMMARY] VAT: {amount}")

        # Pattern 2: 테이블 블록의 마지막 행들에서 Summary 추출
        # (라벨과 금액이 별도 열에 있는 경우)
        for block in blocks:
            if block.get("type") != "table":
                continue

            # rows 접근 (구조 차이 처리)
            if "table" in block and isinstance(block["table"], dict):
                rows = block.get("table", {}).get("rows", [])
            else:
                rows = block.get("rows", [])

            if not rows or len(rows) < 2:
                continue

            # 마지막 5행만 검사 (Summary는 보통 테이블 하단)
            last_rows = rows[-5:] if len(rows) > 5 else rows

            for row in last_rows:
                if not row or len(row) < 2:
                    continue

                # 각 셀 텍스트 정규화
                row_text = [str(cell).strip().upper() if cell else "" for cell in row]

                # Summary 키워드 찾기
                for idx, cell_text in enumerate(row_text):
                    if any(kw in cell_text for kw in ["SUB TOTAL", "SUBTOTAL"]):
                        # 우측 셀들에서 금액 찾기
                        for amount_cell in row_text[idx + 1 :]:
                            amount = self._parse_number(amount_cell)
                            if amount > 0 and "subtotal" not in summary:
                                summary["subtotal"] = amount
                                logger.debug(f"[SUMMARY TABLE] Subtotal: {amount}")
                                break

                    elif "VAT" in cell_text and "TOTAL" not in cell_text:
                        # 우측 셀들에서 금액 찾기
                        for amount_cell in row_text[idx + 1 :]:
                            amount = self._parse_number(amount_cell)
                            if amount > 0 and "vat" not in summary:
                                summary["vat"] = amount
                                logger.debug(f"[SUMMARY TABLE] VAT: {amount}")
                                break

                    elif (
                        any(kw in cell_text for kw in ["TOTAL", "TOTAL NET"])
                        and "SUB" not in cell_text
                        and "GRAND" not in cell_text
                    ):
                        # 우측 셀들에서 금액 찾기
                        for amount_cell in row_text[idx + 1 :]:
                            amount = self._parse_number(amount_cell)
                            if amount > 0 and "total" not in summary:
                                summary["total"] = amount
                                logger.debug(f"[SUMMARY TABLE] Total: {amount}")
                                break

                    elif "GRAND TOTAL" in cell_text:
                        # 우측 셀들에서 금액 찾기
                        for amount_cell in row_text[idx + 1 :]:
                            amount = self._parse_number(amount_cell)
                            if amount > 0:
                                summary["total"] = amount  # Grand Total이 최종
                                logger.debug(f"[SUMMARY TABLE] Grand Total: {amount}")
                                break

        # Pattern 3: 다음 줄에 금액 (라벨과 금액이 별도 행)
        # "TOTAL\n556.50" 패턴
        lines = full_text.split("\n")
        for i in range(len(lines) - 1):
            line = lines[i].strip().upper()
            next_line = lines[i + 1].strip()

            # TOTAL 라벨 찾기
            if line in ["TOTAL", "SUB TOTAL", "SUBTOTAL", "VAT", "GRAND TOTAL"]:
                # 다음 줄에서 금액 추출
                amount = self._parse_number(next_line)
                if amount > 0:
                    if "GRAND" in line and "total" not in summary:
                        summary["total"] = amount
                        logger.debug(f"[SUMMARY NEXTLINE] Grand Total: {amount}")
                    elif line == "TOTAL" and "total" not in summary:
                        summary["total"] = amount
                        logger.debug(f"[SUMMARY NEXTLINE] Total: {amount}")
                    elif "SUB" in line and "subtotal" not in summary:
                        summary["subtotal"] = amount
                        logger.debug(f"[SUMMARY NEXTLINE] Subtotal: {amount}")
                    elif line == "VAT" and "vat" not in summary:
                        summary["vat"] = amount
                        logger.debug(f"[SUMMARY NEXTLINE] VAT: {amount}")

        # 환율 추출 (Optional)
        # Pattern: "R.O.E. 1 USD = 3.6725000 AED"
        fx_pattern = r"R\.O\.E\.\s*1\s*USD\s*=\s*([0-9.]+)\s*AED"
        fx_match = re.search(fx_pattern, full_text, re.IGNORECASE)
        if fx_match:
            exchange_rate = self._parse_number(fx_match.group(1))
            if exchange_rate > 0:
                summary["exchange_rate"] = exchange_rate
                logger.debug(f"[SUMMARY] Exchange Rate: 1 USD = {exchange_rate} AED")

        # 로그 출력
        if summary:
            logger.info(f"[SUMMARY] Extracted summary: {summary}")
        else:
            logger.warning("[SUMMARY] No summary section found in PDF")

        return summary

    def _post_process_extracted_data(self, extracted: Dict) -> Dict:
        """추출된 데이터 후처리"""

        # Total amount 파싱
        if "total_amount" in extracted and isinstance(extracted["total_amount"], str):
            extracted["total_amount"] = self._parse_number(
                extracted["total_amount"], default=0.0
            )

        # Currency 기본값
        if "currency" not in extracted:
            extracted["currency"] = "USD"

        # Items validation
        if not extracted.get("items"):
            extracted["items"] = []

        return extracted

    def extract_boe_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
        """
        BOE (Bill of Entry) 데이터 추출

        Returns:
            {
                "boe_no": "BOE-12345",
                "customs_value": 10000.00,
                "duty_amount": 500.00,
                "vat_amount": 500.00,
                "items": [...]
            }
        """
        extracted = {"doc_type": "boe"}

        blocks = unified_ir.get("blocks", [])
        full_text = self._extract_full_text(blocks)

        # BOE-specific patterns
        boe_patterns = {
            "boe_no": r"(BOE|B\.O\.E\.|Entry)\s*(No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-_/]+)",
            "customs_value": r"(Customs\s*Value|CIF\s*Value)\s*[:]?\s*([0-9,]+\.?\d*)",
            "duty_amount": r"(Duty|Customs\s*Duty)\s*[:]?\s*([0-9,]+\.?\d*)",
            "vat_amount": r"(VAT|Value Added Tax)\s*[:]?\s*([0-9,]+\.?\d*)",
        }

        for field_name, pattern in boe_patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                value = match.group(match.lastindex).strip()
                extracted[field_name] = (
                    self._parse_number(value) if "amount" in field_name else value
                )

        # Extract items
        extracted["items"] = self._extract_table_items(blocks)

        return extracted

    def extract_do_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
        """
        DO (Delivery Order) 데이터 추출

        Returns:
            {
                "do_no": "DO-12345",
                "container_no": "ABCD1234567",
                "delivery_location": "Storage Yard"
            }
        """
        extracted = {"doc_type": "do"}

        blocks = unified_ir.get("blocks", [])
        full_text = self._extract_full_text(blocks)

        # DO-specific patterns
        do_patterns = {
            "do_no": r"(D\/O|DO|Delivery Order)\s*(No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-_/]+)",
            "container_no": r"(Container|CNTR)\s*(No\.?|#)\s*[:#]?\s*([A-Z]{4}\d{7})",
            "delivery_location": r"(Delivery\s*to|Deliver\s*to)\s*[:]?\s*([A-Za-z\s]+)",
        }

        for field_name, pattern in do_patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted[field_name] = match.group(match.lastindex).strip()

        return extracted

    def extract_dn_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
        """
        DN (Debit Note) 데이터 추출

        Returns:
            {
                "dn_no": "DN-12345",
                "charges": [
                    {"description": "Storage", "amount": 100.00},
                    ...
                ]
            }
        """
        extracted = {"doc_type": "dn"}

        blocks = unified_ir.get("blocks", [])
        full_text = self._extract_full_text(blocks)

        # DN-specific patterns
        dn_pattern = r"(D\/N|DN|Debit Note)\s*(No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-_/]+)"
        match = re.search(dn_pattern, full_text, re.IGNORECASE)
        if match:
            extracted["dn_no"] = match.group(3).strip()

        # Extract charges from table
        charges = []
        for block in blocks:
            if block.get("type") == "table":
                table_data = block.get("table", {})
                rows = table_data.get("rows", [])

                for row in rows[1:]:  # Skip header
                    if len(row) >= 2:
                        charges.append(
                            {
                                "description": row[0],
                                "amount": self._parse_number(row[-1], default=0.0),
                            }
                        )

        extracted["charges"] = charges

        return extracted

    def _convert_to_usd_if_needed(
        self, amount: float, unit_rate: float, description: str
    ) -> tuple:
        """
        AED → USD 통화 변환 (필요 시)

        Args:
            amount: 금액
            unit_rate: 단가
            description: 설명 (AED 키워드 확인용)

        Returns:
            (amount_usd, unit_rate_usd)
        """
        # AED 키워드 확인
        desc_upper = description.upper()
        if "AED" in desc_upper and "USD" not in desc_upper:
            # AED → USD 변환 (1 USD = 3.67 AED)
            fx_rate = 3.67
            amount_usd = round(amount / fx_rate, 2)
            unit_rate_usd = round(unit_rate / fx_rate, 2)
            logger.debug(f"[CURRENCY] AED ${amount:.2f} → USD ${amount_usd:.2f}")
            return (amount_usd, unit_rate_usd)

        return (amount, unit_rate)

    def extract_invoice_line_item(
        self, unified_ir: Dict[str, Any], category: str
    ) -> Optional[Dict[str, Any]]:
        """
        PDF에서 특정 Category의 실제 청구 라인 아이템 추출

        Args:
            unified_ir: Unified IR 데이터
            category: 검색할 카테고리 (예: "TERMINAL HANDLING FEE")

        Returns:
            {
                "description": str,  # 실제 PDF 설명
                "qty": float,        # 수량
                "unit_rate": float,  # 단가
                "amount": float,     # 총액
                "matched_by": str    # 매칭 방식
            } or None
        """
        # Extract invoice data using existing method
        invoice_data = self.extract_invoice_data(unified_ir)
        items = invoice_data.get("items", [])

        logger.info(f"Extracted {len(items)} line items from PDF")

        if not items:
            logger.warning(f"No line items found in PDF for category '{category}'")
            return None

        # 4-stage matching strategy
        category_upper = category.upper().strip()

        # Stage 1: Exact match
        for item in items:
            if item["description"].upper() == category_upper:
                # Currency conversion check (AED → USD)
                amount_usd, unit_rate_usd = self._convert_to_usd_if_needed(
                    item.get("amount", 0.0),
                    item.get("unit_rate", item.get("amount", 0.0)),
                    item["description"],
                )

                logger.info(
                    f"[EXACT MATCH] '{category}' → ${amount_usd:.2f} USD (qty: {item['qty']}, unit_rate: ${unit_rate_usd:.2f})"
                )
                return {
                    "description": item["description"],
                    "qty": item.get("qty", 1.0),
                    "unit_rate": unit_rate_usd,
                    "amount": amount_usd,
                    "matched_by": "exact",
                }

        # Stage 2: Contains match
        for item in items:
            if category_upper in item["description"].upper():
                amount_usd, unit_rate_usd = self._convert_to_usd_if_needed(
                    item.get("amount", 0.0),
                    item.get("unit_rate", item.get("amount", 0.0)),
                    item["description"],
                )

                logger.info(
                    f"[CONTAINS MATCH] '{category}' → ${amount_usd:.2f} USD (qty: {item['qty']}, unit_rate: ${unit_rate_usd:.2f})"
                )
                return {
                    "description": item["description"],
                    "qty": item.get("qty", 1.0),
                    "unit_rate": unit_rate_usd,
                    "amount": amount_usd,
                    "matched_by": "contains",
                }

        # Stage 3: Keyword-based (Jaccard similarity)
        stop_words = {
            "THE",
            "AND",
            "FOR",
            "X",
            "OF",
            "TO",
            "FROM",
            "A",
            "AN",
            "IN",
            "ON",
        }
        category_keywords = set(
            w
            for w in re.split(r"\W+", category_upper)
            if w and w not in stop_words and not w.isdigit()
        )

        best_match = None
        best_score = 0.0

        for item in items:
            desc_keywords = set(
                w
                for w in re.split(r"\W+", item["description"].upper())
                if w and w not in stop_words and not w.isdigit()
            )

            if not desc_keywords:
                continue

            # Jaccard similarity
            intersection = category_keywords & desc_keywords
            union = category_keywords | desc_keywords
            score = len(intersection) / len(union) if union else 0.0

            if score >= 0.20 and score > best_score:  # 20% threshold
                best_score = score
                best_match = item

        if best_match:
            amount_usd, unit_rate_usd = self._convert_to_usd_if_needed(
                best_match.get("amount", 0.0),
                best_match.get("unit_rate", best_match.get("amount", 0.0)),
                best_match["description"],
            )

            logger.info(
                f"[KEYWORD MATCH] '{category}' → ${amount_usd:.2f} USD (score: {best_score:.2f}, qty: {best_match['qty']}, unit_rate: ${unit_rate_usd:.2f})"
            )
            return {
                "description": best_match["description"],
                "qty": best_match.get("qty", 1.0),
                "unit_rate": unit_rate_usd,
                "amount": amount_usd,
                "matched_by": "keyword",
            }

        # Stage 4: Fuzzy matching (SequenceMatcher)
        from difflib import SequenceMatcher

        best_match = None
        best_ratio = 0.0

        for item in items:
            ratio = SequenceMatcher(
                None, category_upper, item["description"].upper()
            ).ratio()

            if ratio >= 0.40 and ratio > best_ratio:  # 40% threshold
                best_ratio = ratio
                best_match = item

        if best_match:
            amount_usd, unit_rate_usd = self._convert_to_usd_if_needed(
                best_match.get("amount", 0.0),
                best_match.get("unit_rate", best_match.get("amount", 0.0)),
                best_match["description"],
            )

            logger.info(
                f"[FUZZY MATCH] '{category}' → ${amount_usd:.2f} USD (ratio: {best_ratio:.2f}, qty: {best_match['qty']}, unit_rate: ${unit_rate_usd:.2f})"
            )
            return {
                "description": best_match["description"],
                "qty": best_match.get("qty", 1.0),
                "unit_rate": unit_rate_usd,
                "amount": amount_usd,
                "matched_by": "fuzzy",
            }

        logger.warning(
            f"No match found for category '{category}' (searched {len(items)} items)"
        )
        return None

    def extract_rate_for_category(
        self, unified_ir: Dict[str, Any], category: str
    ) -> Optional[float]:
        """
        특정 Category의 요율 추출 (Fuzzy Matching + 키워드 기반)

        Args:
            unified_ir: Unified IR
            category: 찾을 카테고리 (예: "INLAND TRUCKING", "DO FEE")

        Returns:
            요율 (float) 또는 None
        """
        from difflib import SequenceMatcher

        # Extract invoice data
        invoice_data = self.extract_invoice_data(unified_ir)
        items = invoice_data.get("items", [])

        if not items:
            logger.warning(f"No items found in PDF for category '{category}'")
            return None

        # 1. 정확한 매칭 (Exact match)
        category_upper = category.upper()
        for item in items:
            desc = str(item.get("description", "")).upper()
            if category_upper == desc:
                unit_rate = item.get("unit_rate", 0.0)
                if unit_rate > 0:
                    logger.info(f"[EXACT] Found rate for '{category}': {unit_rate}")
                    return unit_rate

        # 2. 포함 매칭 (Contains)
        for item in items:
            desc = str(item.get("description", "")).upper()
            if category_upper in desc:
                unit_rate = item.get("unit_rate", 0.0)
                if unit_rate > 0:
                    logger.info(
                        f"[CONTAINS] Found rate for '{category}': {unit_rate} (from '{item['description']}')"
                    )
                    return unit_rate

        # 3. 키워드 매칭 (Keyword-based) - Improved
        category_keywords = set(category_upper.split())

        # Filter out common words for better matching
        stop_words = {
            "THE",
            "A",
            "AN",
            "AND",
            "OR",
            "OF",
            "TO",
            "FROM",
            "FOR",
            "IN",
            "ON",
            "AT",
            "BY",
            "WITH",
            "X",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
        }
        category_keywords_filtered = {
            w for w in category_keywords if w not in stop_words and len(w) > 2
        }

        best_match = None
        best_score = 0.0

        for item in items:
            desc = str(item.get("description", "")).upper()
            desc_keywords = set(desc.split())
            desc_keywords_filtered = {
                w for w in desc_keywords if w not in stop_words and len(w) > 2
            }

            # Jaccard similarity (filtered keywords only)
            intersection = category_keywords_filtered & desc_keywords_filtered
            union = category_keywords_filtered | desc_keywords_filtered
            jaccard = len(intersection) / len(union) if union else 0.0

            # Lower threshold for better recall
            if (
                jaccard > best_score and jaccard >= 0.2
            ):  # 20% threshold (lowered from 30%)
                unit_rate = item.get("unit_rate", 0.0)
                if unit_rate > 0:
                    best_score = jaccard
                    best_match = (item, jaccard)

        if best_match:
            item, score = best_match
            unit_rate = item.get("unit_rate", 0.0)
            logger.info(
                f"[KEYWORD] Found rate for '{category}': {unit_rate} (similarity: {score:.2f}, from '{item['description']}')"
            )
            return unit_rate

        # 4. Fuzzy 매칭 (SequenceMatcher) - Lowered threshold
        best_fuzzy_match = None
        best_fuzzy_score = 0.0

        for item in items:
            desc = str(item.get("description", "")).upper()
            similarity = SequenceMatcher(None, category_upper, desc).ratio()

            # Lower threshold for better recall
            if (
                similarity > best_fuzzy_score and similarity >= 0.4
            ):  # 40% threshold (lowered from 60%)
                unit_rate = item.get("unit_rate", 0.0)
                if unit_rate > 0:
                    best_fuzzy_score = similarity
                    best_fuzzy_match = (item, similarity)

        if best_fuzzy_match:
            item, score = best_fuzzy_match
            unit_rate = item.get("unit_rate", 0.0)
            logger.info(
                f"[FUZZY] Found rate for '{category}': {unit_rate} (similarity: {score:.2f}, from '{item['description']}')"
            )
            return unit_rate

        logger.warning(
            f"No rate found for category '{category}' (searched {len(items)} items)"
        )
        return None

    def convert_to_hvdc_format(
        self, unified_ir: Dict[str, Any], doc_type: str = "invoice"
    ) -> Dict[str, Any]:
        """
        Unified IR → HVDC 표준 포맷 변환

        Args:
            unified_ir: Unified IR
            doc_type: invoice, boe, do, dn

        Returns:
            HVDC 표준 포맷
        """
        if doc_type == "invoice":
            return self.extract_invoice_data(unified_ir)
        elif doc_type == "boe":
            return self.extract_boe_data(unified_ir)
        elif doc_type == "do":
            return self.extract_do_data(unified_ir)
        elif doc_type == "dn":
            return self.extract_dn_data(unified_ir)
        else:
            logger.warning(f"Unknown doc_type: {doc_type}. Defaulting to invoice.")
            return self.extract_invoice_data(unified_ir)

    def get_confidence_score(self, unified_ir: Dict[str, Any]) -> float:
        """
        Unified IR의 전체 신뢰도 점수

        Returns:
            0.0 ~ 1.0
        """
        meta = unified_ir.get("meta", {})
        confidence = meta.get("confidence", 0.0)

        # Additional heuristics
        blocks = unified_ir.get("blocks", [])
        if len(blocks) == 0:
            return 0.0

        # Table blocks increase confidence
        table_count = sum(1 for b in blocks if b.get("type") == "table")
        if table_count > 0:
            confidence = min(1.0, confidence + 0.05)

        return round(confidence, 2)


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with sample Unified IR
    sample_ir = {
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
                    ]
                },
            },
        ],
        "meta": {"confidence": 0.92},
    }

    adapter = UnifiedIRAdapter()

    # Test invoice extraction
    invoice_data = adapter.extract_invoice_data(sample_ir)

    print("\n✅ Unified IR Adapter Test")
    print(f"   Invoice No: {invoice_data.get('invoice_no')}")
    print(f"   Order Ref: {invoice_data.get('order_ref')}")
    print(f"   Total Amount: {invoice_data.get('total_amount')}")
    print(f"   Currency: {invoice_data.get('currency')}")
    print(f"   Items: {len(invoice_data.get('items', []))}")
    print(f"   Confidence: {adapter.get_confidence_score(sample_ir)}")

    # Test rate extraction
    rate = adapter.extract_rate_for_category(sample_ir, "DO FEE")
    print(f"\n   DO FEE rate: {rate}")
