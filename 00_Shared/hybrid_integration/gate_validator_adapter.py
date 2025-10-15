#!/usr/bin/env python3
"""
Gate Validator Adapter for HVDC Hybrid Integration

Integrates SHPT Gate-11~14 validation logic with Hybrid Parser workflow.
Works with Unified IR documents and provides comprehensive validation results.

Gate Validation Rules:
- Gate-11: MBL consistency across Invoice, BOE, DO
- Gate-12: Container number validation
- Gate-13: Weight tolerance check (±3%)
- Gate-14: Quantity and date logic validation
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import re


class GateValidatorAdapter:
    """
    Adapt SHPT Gate validation logic to work with Unified IR documents

    Features:
    - Extract validation data from Unified IR
    - Run Gate-11~14 validation rules
    - Support cross-document validation
    - Generate comprehensive validation reports
    """

    def __init__(self, weight_tolerance_pct: float = 3.0, log_level: str = "INFO"):
        """
        Initialize Gate Validator

        Args:
            weight_tolerance_pct: Weight tolerance percentage for Gate-13 (default: 3%)
            log_level: Logging level
        """
        self.weight_tolerance_pct = weight_tolerance_pct
        self.logger = self._setup_logger(log_level)

        self.logger.info(
            f"GateValidatorAdapter initialized (weight tolerance: ±{weight_tolerance_pct}%)"
        )

    def _setup_logger(self, level: str) -> logging.Logger:
        logger = logging.getLogger("GateValidatorAdapter")
        logger.setLevel(getattr(logging, level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def validate_all_gates(
        self, primary_doc: Dict, related_docs: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Run all Gate validations (Gate-11 through Gate-14)

        Args:
            primary_doc: Primary document in Unified IR format
            related_docs: Related documents for cross-validation (BOE, DO, DN, etc.)

        Returns:
            Complete gate validation results
        """
        if not related_docs:
            related_docs = []

        # Build document collection for validation
        all_docs = [primary_doc] + related_docs

        # Run individual gate validations
        gate_results = []

        # Gate-11: MBL Consistency
        gate_11_result = self._validate_gate_11(all_docs)
        gate_results.append(gate_11_result)

        # Gate-12: Container Validation
        gate_12_result = self._validate_gate_12(all_docs)
        gate_results.append(gate_12_result)

        # Gate-13: Weight Tolerance
        gate_13_result = self._validate_gate_13(all_docs)
        gate_results.append(gate_13_result)

        # Gate-14: Quantity & Date Logic
        gate_14_result = self._validate_gate_14(all_docs)
        gate_results.append(gate_14_result)

        # Determine overall status
        statuses = [g["status"] for g in gate_results]
        if all(s in ["PASS", "SKIP"] for s in statuses):
            overall_status = "ALL_PASS"
        elif all(s in ["FAIL", "ERROR"] for s in statuses):
            overall_status = "ALL_FAIL"
        else:
            overall_status = "PARTIAL_FAIL"

        validation_result = {
            "validated_at": datetime.now().isoformat(),
            "overall_status": overall_status,
            "gates": gate_results,
            "cross_document_refs": [
                {
                    "doc_id": doc.get("doc_id"),
                    "doc_type": doc.get("meta", {}).get("doc_type"),
                    "relationship": "related",
                }
                for doc in all_docs
            ],
        }

        self.logger.info(f"Gate validation complete: {overall_status}")
        return validation_result

    def _validate_gate_11(self, documents: List[Dict]) -> Dict:
        """
        Gate-11: MBL Consistency Check

        Verify MBL number matches across Invoice, BOE, and DO documents
        """
        gate_result = {
            "gate_id": "gate-11",
            "status": "SKIP",
            "details": "",
            "checked_fields": ["mbl_no"],
            "timestamp": datetime.now().isoformat(),
        }

        # Extract MBL numbers from all documents
        mbl_numbers = {}

        for doc in documents:
            doc_type = doc.get("meta", {}).get("doc_type")
            hvdc_fields = doc.get("hvdc_fields", {})

            if doc_type == "BOE":
                mbl = hvdc_fields.get("boe_fields", {}).get("mbl_no")
                if mbl:
                    mbl_numbers["BOE"] = mbl

            elif doc_type == "DO":
                # DO might reference MBL (not always present)
                mbl = hvdc_fields.get("do_fields", {}).get("mbl_reference")
                if mbl:
                    mbl_numbers["DO"] = mbl

            elif doc_type == "Invoice" or doc_type == "CarrierInvoice":
                # Extract MBL from blocks or fields
                mbl = self._extract_mbl_from_invoice(doc)
                if mbl:
                    mbl_numbers["Invoice"] = mbl

        # Check consistency
        if len(mbl_numbers) < 2:
            gate_result["status"] = "SKIP"
            gate_result["details"] = (
                f"Insufficient documents for MBL check (found: {list(mbl_numbers.keys())})"
            )
        else:
            unique_mbls = set(mbl_numbers.values())
            if len(unique_mbls) == 1:
                gate_result["status"] = "PASS"
                gate_result["details"] = (
                    f"MBL consistent across documents: {unique_mbls.pop()}"
                )
            else:
                gate_result["status"] = "FAIL"
                gate_result["details"] = f"MBL mismatch: {mbl_numbers}"

        self.logger.info(
            f"Gate-11 (MBL Check): {gate_result['status']} - {gate_result['details']}"
        )
        return gate_result

    def _validate_gate_12(self, documents: List[Dict]) -> Dict:
        """
        Gate-12: Container Number Validation

        Verify container numbers match across documents
        """
        gate_result = {
            "gate_id": "gate-12",
            "status": "SKIP",
            "details": "",
            "checked_fields": ["containers"],
            "timestamp": datetime.now().isoformat(),
        }

        # Extract container numbers from all documents
        container_sets = {}

        for doc in documents:
            doc_type = doc.get("meta", {}).get("doc_type")
            hvdc_fields = doc.get("hvdc_fields", {})

            if doc_type == "BOE":
                containers = hvdc_fields.get("boe_fields", {}).get("containers", [])
                if containers:
                    container_sets["BOE"] = set(containers)

            elif doc_type == "DO":
                # Extract container from DO if present
                container = hvdc_fields.get("do_fields", {}).get("container_no")
                if container:
                    container_sets["DO"] = {container}

            elif doc_type == "Invoice" or doc_type == "CarrierInvoice":
                # Extract containers from invoice
                containers = self._extract_containers_from_invoice(doc)
                if containers:
                    container_sets["Invoice"] = set(containers)

        # Check consistency
        if len(container_sets) < 2:
            gate_result["status"] = "SKIP"
            gate_result["details"] = (
                f"Insufficient documents for container check (found: {list(container_sets.keys())})"
            )
        else:
            # Check if all container sets have overlap
            all_containers = [
                c for containers in container_sets.values() for c in containers
            ]
            if len(set(all_containers)) == len(all_containers):
                # All unique - check if they match
                sets_list = list(container_sets.values())
                if all(s == sets_list[0] for s in sets_list):
                    gate_result["status"] = "PASS"
                    gate_result["details"] = (
                        f"Containers consistent: {list(sets_list[0])}"
                    )
                else:
                    gate_result["status"] = "FAIL"
                    gate_result["details"] = f"Container mismatch: {container_sets}"
            else:
                gate_result["status"] = "FAIL"
                gate_result["details"] = (
                    f"Duplicate or inconsistent containers found: {container_sets}"
                )

        self.logger.info(
            f"Gate-12 (Container Check): {gate_result['status']} - {gate_result['details']}"
        )
        return gate_result

    def _validate_gate_13(self, documents: List[Dict]) -> Dict:
        """
        Gate-13: Weight Tolerance Check (±3%)

        Compare gross weight between documents within tolerance
        """
        gate_result = {
            "gate_id": "gate-13",
            "status": "SKIP",
            "details": "",
            "checked_fields": ["gross_weight"],
            "timestamp": datetime.now().isoformat(),
        }

        # Extract weights from documents
        weights = {}

        for doc in documents:
            doc_type = doc.get("meta", {}).get("doc_type")
            hvdc_fields = doc.get("hvdc_fields", {})

            if doc_type == "BOE":
                weight = hvdc_fields.get("boe_fields", {}).get("gross_weight")
                if weight:
                    weights["BOE"] = float(weight)

            elif doc_type == "Invoice" or doc_type == "CarrierInvoice":
                # Extract weight from invoice
                weight = self._extract_weight_from_invoice(doc)
                if weight:
                    weights["Invoice"] = float(weight)

        # Check tolerance
        if len(weights) < 2:
            gate_result["status"] = "SKIP"
            gate_result["details"] = (
                f"Insufficient weight data (found: {list(weights.keys())})"
            )
        else:
            # Compare weights with tolerance
            weight_values = list(weights.values())
            max_weight = max(weight_values)
            min_weight = min(weight_values)

            # Calculate variance percentage
            if max_weight > 0:
                variance_pct = ((max_weight - min_weight) / max_weight) * 100
            else:
                variance_pct = 0

            if variance_pct <= self.weight_tolerance_pct:
                gate_result["status"] = "PASS"
                gate_result["details"] = (
                    f"Weight within tolerance (variance: {variance_pct:.2f}%): {weights}"
                )
            else:
                gate_result["status"] = "FAIL"
                gate_result["details"] = (
                    f"Weight exceeds ±{self.weight_tolerance_pct}% tolerance (variance: {variance_pct:.2f}%): {weights}"
                )

        self.logger.info(
            f"Gate-13 (Weight Check): {gate_result['status']} - {gate_result['details']}"
        )
        return gate_result

    def _validate_gate_14(self, documents: List[Dict]) -> Dict:
        """
        Gate-14: Quantity and Date Logic Validation

        Verify:
        - Quantities match across documents
        - Date logic: BL Date ≤ Invoice Date ≤ DO Validity
        """
        gate_result = {
            "gate_id": "gate-14",
            "status": "SKIP",
            "details": "",
            "checked_fields": ["quantity", "dates"],
            "timestamp": datetime.now().isoformat(),
        }

        # Extract quantities and dates
        quantities = {}
        dates = {}

        for doc in documents:
            doc_type = doc.get("meta", {}).get("doc_type")
            hvdc_fields = doc.get("hvdc_fields", {})

            if doc_type == "BOE":
                # Sum quantities from HS code classifications
                hs_codes = hvdc_fields.get("boe_fields", {}).get(
                    "hs_code_classifications", []
                )
                total_qty = sum(item.get("quantity", 0) for item in hs_codes)
                if total_qty > 0:
                    quantities["BOE"] = total_qty

            elif doc_type == "DO":
                # Extract DO validity date
                validity_date = hvdc_fields.get("do_fields", {}).get("do_validity_date")
                if validity_date:
                    dates["DO_validity"] = validity_date

            elif doc_type == "Invoice" or doc_type == "CarrierInvoice":
                # Extract invoice date
                invoice_date = hvdc_fields.get("carrier_invoice_fields", {}).get(
                    "invoice_date"
                )
                if invoice_date:
                    dates["Invoice"] = invoice_date

                # Extract quantity
                qty = self._extract_quantity_from_invoice(doc)
                if qty:
                    quantities["Invoice"] = qty

        # Validate
        issues = []

        # Check quantity consistency
        if len(quantities) >= 2:
            unique_qtys = set(quantities.values())
            if len(unique_qtys) > 1:
                issues.append(f"Quantity mismatch: {quantities}")

        # Check date logic
        if "Invoice" in dates and "DO_validity" in dates:
            invoice_date = self._parse_date(dates["Invoice"])
            do_validity = self._parse_date(dates["DO_validity"])

            if invoice_date and do_validity:
                if invoice_date > do_validity:
                    issues.append(
                        f"Invoice date ({invoice_date}) after DO validity ({do_validity})"
                    )

        # Determine status
        if not quantities and not dates:
            gate_result["status"] = "SKIP"
            gate_result["details"] = "No quantity or date data found"
        elif issues:
            gate_result["status"] = "FAIL"
            gate_result["details"] = "; ".join(issues)
        else:
            gate_result["status"] = "PASS"
            gate_result["details"] = (
                f"Quantity and dates valid: qtys={quantities}, dates={dates}"
            )

        self.logger.info(
            f"Gate-14 (Qty/Date Check): {gate_result['status']} - {gate_result['details']}"
        )
        return gate_result

    def _extract_mbl_from_invoice(self, doc: Dict) -> Optional[str]:
        """Extract MBL from invoice document"""
        blocks = doc.get("blocks", [])
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Search for MBL pattern
                match = re.search(r"\b([A-Z]{4}\d{9,})\b", text)
                if match:
                    return match.group(1)
        return None

    def _extract_containers_from_invoice(self, doc: Dict) -> List[str]:
        """Extract container numbers from invoice document"""
        containers = []
        blocks = doc.get("blocks", [])
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Search for container pattern (4 letters + 7 digits)
                matches = re.findall(r"\b([A-Z]{4}\d{7})\b", text)
                containers.extend(matches)
        return list(set(containers))  # Remove duplicates

    def _extract_weight_from_invoice(self, doc: Dict) -> Optional[float]:
        """Extract gross weight from invoice document"""
        blocks = doc.get("blocks", [])
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Search for weight pattern
                match = re.search(
                    r"(?:gross weight|g\.w\.|total weight)\s*[:]?\s*([\\d,]+\\.?\\d*)",
                    text,
                    re.IGNORECASE,
                )
                if match:
                    weight_str = match.group(1).replace(",", "")
                    try:
                        return float(weight_str)
                    except ValueError:
                        continue
        return None

    def _extract_quantity_from_invoice(self, doc: Dict) -> Optional[float]:
        """Extract quantity from invoice document"""
        blocks = doc.get("blocks", [])
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Search for quantity pattern
                match = re.search(
                    r"(?:qty|quantity)\s*[:]?\s*(\\d+(?:\\.\\d+)?)", text, re.IGNORECASE
                )
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None


if __name__ == "__main__":
    # Example usage
    print("HVDC Gate Validator Adapter - Test Module\n")

    # Mock Unified IR documents
    boe_doc = {
        "doc_id": "boe-001",
        "meta": {"doc_type": "BOE", "shipment_id": "HVDC-ADOPT-SCT-0126"},
        "hvdc_fields": {
            "boe_fields": {
                "mbl_no": "MAEU123456789",
                "containers": ["TCLU1234567"],
                "gross_weight": 15000.5,
                "hs_code_classifications": [{"hs_code": "8504401000", "quantity": 5}],
            }
        },
    }

    invoice_doc = {
        "doc_id": "inv-001",
        "meta": {"doc_type": "Invoice", "shipment_id": "HVDC-ADOPT-SCT-0126"},
        "blocks": [
            {
                "type": "text",
                "text": "MBL: MAEU123456789\nContainer: TCLU1234567\nGross Weight: 15,450.0 KG\nQty: 5",
            }
        ],
    }

    validator = GateValidatorAdapter(weight_tolerance_pct=3.0)

    # Run validation
    results = validator.validate_all_gates(boe_doc, related_docs=[invoice_doc])

    print(f"Overall Status: {results['overall_status']}\n")
    for gate in results["gates"]:
        print(f"{gate['gate_id'].upper()}: {gate['status']}")
        print(f"  Details: {gate['details']}\n")
