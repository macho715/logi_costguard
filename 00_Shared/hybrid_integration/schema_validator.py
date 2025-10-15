#!/usr/bin/env python3
"""
Schema Validator for Unified IR Documents

Validates parsed documents against the Unified IR schema (unified_ir_schema_hvdc.yaml).
Enforces confidence thresholds and field completeness for HVDC requirements.
"""

from typing import Dict, List, Tuple, Any, Optional
import logging
import re
from datetime import datetime


class SchemaValidator:
    """
    Validate documents against Unified IR schema

    Key validations:
    - Required fields present
    - Field types correct
    - Confidence thresholds met (≥0.95 for HVDC safety-critical)
    - HVDC-specific field completeness
    - Document type-specific requirements
    """

    def __init__(self, min_confidence: float = 0.90, log_level: str = "INFO"):
        """
        Initialize validator

        Args:
            min_confidence: Minimum confidence threshold (default: 0.90 for HVDC)
            log_level: Logging level
        """
        self.min_confidence = min_confidence
        self.logger = self._setup_logger(log_level)

        # HVDC-specific confidence thresholds by field
        self.field_confidence_thresholds = {
            "BOE": {
                "mbl_no": 0.95,
                "entry_no": 0.95,
                "containers": 0.90,
                "gross_weight": 0.85,
                "hs_code": 0.95,
            },
            "DO": {"do_number": 0.95, "do_validity_date": 0.90, "container_no": 0.95},
            "DN": {
                "origin": 0.85,
                "destination": 0.85,
                "vehicle_type": 0.80,
                "do_reference": 0.85,
            },
            "CarrierInvoice": {
                "invoice_number": 0.95,
                "total_amount": 0.95,
                "line_items": 0.85,
            },
        }

    def _setup_logger(self, level: str) -> logging.Logger:
        logger = logging.getLogger("SchemaValidator")
        logger.setLevel(getattr(logging, level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def validate(self, document: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a Unified IR document

        Args:
            document: Document in Unified IR format

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required top-level fields
        errors.extend(self._validate_required_fields(document))

        # Meta validation
        errors.extend(self._validate_meta(document.get("meta", {})))

        # Blocks validation
        errors.extend(self._validate_blocks(document.get("blocks", [])))

        # HVDC fields validation
        errors.extend(
            self._validate_hvdc_fields(
                document.get("meta", {}).get("doc_type"),
                document.get("hvdc_fields", {}),
            )
        )

        # Confidence thresholds
        errors.extend(self._validate_confidence(document))

        # Document type-specific validation
        errors.extend(self._validate_doc_type_requirements(document))

        is_valid = len(errors) == 0

        if is_valid:
            self.logger.info(
                f"Document {document.get('doc_id', 'unknown')} passed validation"
            )
        else:
            self.logger.warning(
                f"Document {document.get('doc_id', 'unknown')} failed validation: {len(errors)} errors"
            )

        return is_valid, errors

    def _validate_required_fields(self, document: Dict) -> List[str]:
        """Validate required top-level fields"""
        errors = []
        required = ["doc_id", "engine", "blocks"]

        for field in required:
            if field not in document:
                errors.append(f"Missing required field: {field}")

        return errors

    def _validate_meta(self, meta: Dict) -> List[str]:
        """Validate meta section"""
        errors = []

        # Check filename
        if not meta.get("filename"):
            errors.append("meta.filename is required")

        # Check doc_type
        doc_type = meta.get("doc_type")
        valid_types = ["BOE", "DO", "DN", "CarrierInvoice", "Invoice", "Other"]
        if doc_type not in valid_types:
            errors.append(
                f"Invalid meta.doc_type: {doc_type}. Must be one of {valid_types}"
            )

        # Check shipment_id pattern for HVDC documents
        shipment_id = meta.get("shipment_id", "")
        if shipment_id:
            pattern = r"^HVDC-[A-Z]+-[A-Z]+-\d+$"
            if not re.match(pattern, shipment_id):
                errors.append(
                    f"Invalid shipment_id format: {shipment_id}. Must match {pattern}"
                )

        # Check checksum format if present
        checksum = meta.get("checksum_sha256", "")
        if checksum:
            if not re.match(r"^[a-f0-9]{64}$", checksum):
                errors.append(f"Invalid checksum_sha256 format: {checksum}")

        return errors

    def _validate_blocks(self, blocks: List[Dict]) -> List[str]:
        """Validate blocks array"""
        errors = []

        if not blocks:
            errors.append("blocks array is empty - at least one block required")
            return errors

        valid_types = [
            "text",
            "table",
            "figure",
            "header",
            "footer",
            "field",
            "checkbox",
            "signature",
        ]

        for idx, block in enumerate(blocks):
            block_id = block.get("id", f"block-{idx}")

            # Check required fields
            if "type" not in block:
                errors.append(f"Block {block_id}: missing required 'type' field")
                continue

            # Validate type
            if block["type"] not in valid_types:
                errors.append(
                    f"Block {block_id}: invalid type '{block['type']}'. Must be one of {valid_types}"
                )

            # Validate type-specific requirements
            if block["type"] == "text" and not block.get("text"):
                errors.append(f"Block {block_id}: text blocks must have 'text' field")

            if block["type"] == "table":
                table = block.get("table", {})
                if not table.get("rows"):
                    errors.append(
                        f"Block {block_id}: table blocks must have 'rows' field"
                    )

            # Validate bbox if present
            bbox = block.get("bbox")
            if bbox:
                required_bbox_fields = ["page", "x0", "y0", "x1", "y1"]
                for field in required_bbox_fields:
                    if field not in bbox:
                        errors.append(f"Block {block_id}: bbox missing field '{field}'")

            # Validate meta
            meta = block.get("meta", {})
            if "confidence" in meta:
                conf = meta["confidence"]
                if not (0 <= conf <= 1):
                    errors.append(
                        f"Block {block_id}: confidence must be between 0 and 1, got {conf}"
                    )

        return errors

    def _validate_hvdc_fields(self, doc_type: str, hvdc_fields: Dict) -> List[str]:
        """Validate HVDC-specific fields based on document type"""
        errors = []

        if not doc_type or doc_type == "Other":
            return errors

        if doc_type == "BOE":
            boe_fields = hvdc_fields.get("boe_fields", {})
            if not boe_fields:
                errors.append("BOE document must have boe_fields")
            else:
                # Check critical BOE fields
                critical_fields = ["mbl_no", "containers", "gross_weight"]
                for field in critical_fields:
                    if not boe_fields.get(field):
                        errors.append(f"BOE missing critical field: boe_fields.{field}")

                # Validate container format
                containers = boe_fields.get("containers", [])
                if containers:
                    for container in containers:
                        if not re.match(r"^[A-Z]{4}\d{7}$", container):
                            errors.append(
                                f"Invalid container format: {container}. Must be 4 letters + 7 digits"
                            )

        elif doc_type == "DO":
            do_fields = hvdc_fields.get("do_fields", {})
            if not do_fields:
                errors.append("DO document must have do_fields")
            else:
                # Check critical DO fields
                if not do_fields.get("do_number"):
                    errors.append("DO missing critical field: do_fields.do_number")

        elif doc_type == "DN":
            dn_fields = hvdc_fields.get("dn_fields", {})
            if not dn_fields:
                errors.append("DN document must have dn_fields")
            else:
                # Check critical DN fields
                critical_fields = ["origin", "destination"]
                for field in critical_fields:
                    if not dn_fields.get(field):
                        errors.append(f"DN missing critical field: dn_fields.{field}")

        elif doc_type == "CarrierInvoice":
            carrier_fields = hvdc_fields.get("carrier_invoice_fields", {})
            if not carrier_fields:
                errors.append(
                    "CarrierInvoice document must have carrier_invoice_fields"
                )
            else:
                # Check critical fields
                critical_fields = ["invoice_number", "total_amount"]
                for field in critical_fields:
                    if not carrier_fields.get(field):
                        errors.append(
                            f"CarrierInvoice missing critical field: carrier_invoice_fields.{field}"
                        )

        return errors

    def _validate_confidence(self, document: Dict) -> List[str]:
        """Validate confidence thresholds"""
        errors = []
        doc_type = document.get("meta", {}).get("doc_type")

        if not doc_type or doc_type not in self.field_confidence_thresholds:
            return errors

        thresholds = self.field_confidence_thresholds[doc_type]
        hvdc_fields = document.get("hvdc_fields", {})

        # Get the appropriate fields dict
        if doc_type == "BOE":
            fields_dict = hvdc_fields.get("boe_fields", {})
        elif doc_type == "DO":
            fields_dict = hvdc_fields.get("do_fields", {})
        elif doc_type == "DN":
            fields_dict = hvdc_fields.get("dn_fields", {})
        elif doc_type == "CarrierInvoice":
            fields_dict = hvdc_fields.get("carrier_invoice_fields", {})
        else:
            return errors

        # Check confidence for each critical field
        for field, min_conf in thresholds.items():
            if field in fields_dict:
                # Get confidence from routing_decision or use default
                routing = document.get("routing_decision", {})
                actual_conf = routing.get("confidence", 0.9)

                if actual_conf < min_conf:
                    errors.append(
                        f"{doc_type}.{field} confidence {actual_conf:.2f} below threshold {min_conf:.2f}"
                    )

        return errors

    def _validate_doc_type_requirements(self, document: Dict) -> List[str]:
        """Validate document type-specific requirements"""
        errors = []
        doc_type = document.get("meta", {}).get("doc_type")

        if doc_type == "BOE":
            # BOE must have at least one HS code classification
            hs_codes = (
                document.get("hvdc_fields", {})
                .get("boe_fields", {})
                .get("hs_code_classifications", [])
            )
            if not hs_codes:
                errors.append("BOE must have at least one HS code classification")

        elif doc_type == "DO":
            # DO must have validity date
            validity = (
                document.get("hvdc_fields", {})
                .get("do_fields", {})
                .get("do_validity_date")
            )
            if not validity:
                errors.append(
                    "DO must have do_validity_date for demurrage risk calculation"
                )

        return errors

    def validate_for_gate(self, document: Dict) -> Tuple[bool, List[str]]:
        """
        Additional validation for Gate validation readiness

        Checks if document has all required fields for Gate-11~14 validation
        """
        errors = []
        doc_type = document.get("meta", {}).get("doc_type")

        if doc_type == "BOE":
            boe_fields = document.get("hvdc_fields", {}).get("boe_fields", {})

            # Gate-11 (MBL check)
            if not boe_fields.get("mbl_no"):
                errors.append("BOE missing mbl_no required for Gate-11")

            # Gate-12 (Container check)
            if not boe_fields.get("containers"):
                errors.append("BOE missing containers required for Gate-12")

            # Gate-13 (Weight check)
            if not boe_fields.get("gross_weight"):
                errors.append("BOE missing gross_weight required for Gate-13")

        elif doc_type == "DO":
            do_fields = document.get("hvdc_fields", {}).get("do_fields", {})

            # Gate-11 (MBL check - if DO has MBL reference)
            # Not always required for DO

            # Gate-14 (Date check)
            if not do_fields.get("do_validity_date"):
                errors.append("DO missing do_validity_date required for Gate-14")

        is_valid = len(errors) == 0
        return is_valid, errors


if __name__ == "__main__":
    # Example usage
    print("HVDC Schema Validator - Test Module")

    # Test document
    test_doc = {
        "doc_id": "test-001",
        "engine": "docling",
        "pages": 1,
        "meta": {
            "filename": "HVDC-ADOPT-SCT-0126_BOE.pdf",
            "doc_type": "BOE",
            "shipment_id": "HVDC-ADOPT-SCT-0126",
            "checksum_sha256": "a" * 64,
        },
        "blocks": [
            {
                "id": "block-1",
                "type": "text",
                "text": "Sample text",
                "meta": {"confidence": 0.95},
            }
        ],
        "hvdc_fields": {
            "boe_fields": {
                "mbl_no": "MAEU123456789",
                "containers": ["TCLU1234567"],
                "gross_weight": 15000.5,
                "hs_code_classifications": [
                    {"hs_code": "8504401000", "description": "Transformer"}
                ],
            }
        },
        "routing_decision": {"confidence": 0.97},
    }

    validator = SchemaValidator()
    is_valid, errors = validator.validate(test_doc)

    print(f"\nValidation Result: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No validation errors!")

    # Test Gate validation
    gate_valid, gate_errors = validator.validate_for_gate(test_doc)
    print(f"\nGate Validation Ready: {'YES' if gate_valid else 'NO'}")
    if gate_errors:
        print("Gate Errors:")
        for error in gate_errors:
            print(f"  - {error}")
