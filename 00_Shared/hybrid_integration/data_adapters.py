#!/usr/bin/env python3
"""
Data Adapters for HVDC Hybrid Integration

Converts between:
- SHPT DSVPDFParser format → Unified IR
- DOMESTIC PDF parser format → Unified IR
- Unified IR → SHPT format (for Gate validation)
- Unified IR → DOMESTIC format (for enhanced matching)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import hashlib
import re


class BaseAdapter:
    """Base class for all data adapters"""

    def __init__(self, log_level: str = "INFO"):
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, level: str) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


class SHPTToUnifiedIRAdapter(BaseAdapter):
    """
    Convert SHPT DSVPDFParser output to Unified IR format

    Input format (SHPT):
    {
        "header": {"file_path": str, "doc_type": str, "shipment_id": str},
        "data": {...},
        "raw_text": str,
        "confidence": float
    }

    Output format: Unified IR (see unified_ir_schema_hvdc.yaml)
    """

    def convert(self, shpt_data: Dict, routing_decision: Optional[Dict] = None) -> Dict:
        """
        Convert SHPT format to Unified IR

        Args:
            shpt_data: Parsed data from DSVPDFParser
            routing_decision: Optional routing metadata from HybridPDFRouter

        Returns:
            Document in Unified IR format
        """
        try:
            header = shpt_data.get("header", {})
            data = shpt_data.get("data", {})
            raw_text = shpt_data.get("raw_text", "")

            # Generate doc_id from file path
            file_path = header.get("file_path", "")
            doc_id = self._generate_doc_id(file_path)

            # Build Unified IR document
            unified_doc = {
                "doc_id": doc_id,
                "engine": (
                    routing_decision.get("engine_choice", "dsvparser")
                    if routing_decision
                    else "dsvparser"
                ),
                "routing_decision": routing_decision,
                "pages": data.get("page_count", 1),
                "meta": {
                    "filename": header.get("file_name", ""),
                    "mime": "application/pdf",
                    "created_at": datetime.now().isoformat(),
                    "checksum_sha256": (
                        self._calc_file_hash(file_path) if file_path else ""
                    ),
                    "doc_type": header.get("doc_type", "Other"),
                    "shipment_id": header.get("shipment_id", ""),
                },
                "blocks": self._extract_blocks(raw_text, data),
                "hvdc_fields": self._extract_hvdc_fields(header.get("doc_type"), data),
                "gate_validation": None,  # Will be populated by gate validator
            }

            self.logger.info(f"Converted SHPT document {doc_id} to Unified IR")
            return unified_doc

        except Exception as e:
            self.logger.error(f"Error converting SHPT to Unified IR: {e}")
            raise

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique doc_id from file path"""
        if file_path:
            return hashlib.md5(file_path.encode()).hexdigest()[:16]
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:16]

    def _calc_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""

    def _extract_blocks(self, raw_text: str, data: Dict) -> List[Dict]:
        """Extract blocks from SHPT data"""
        blocks = []

        # Add text block for raw text
        if raw_text:
            blocks.append(
                {
                    "id": "text-1",
                    "type": "text",
                    "text": raw_text,
                    "bbox": None,  # SHPT doesn't provide bbox
                    "meta": {
                        "confidence": data.get("confidence", 0.9),
                        "source_engine": "dsvparser",
                        "page_idx": 0,
                    },
                }
            )

        # Add table blocks if present
        if "tables" in data:
            for idx, table in enumerate(data["tables"]):
                blocks.append(
                    {
                        "id": f"table-{idx+1}",
                        "type": "table",
                        "table": {"rows": table.get("rows", []), "header": True},
                        "bbox": None,
                        "meta": {
                            "confidence": 0.85,
                            "source_engine": "dsvparser",
                            "page_idx": table.get("page", 0),
                        },
                    }
                )

        return blocks

    def _extract_hvdc_fields(self, doc_type: str, data: Dict) -> Dict:
        """Extract HVDC-specific fields based on document type"""
        hvdc_fields = {}

        if doc_type == "BOE":
            hvdc_fields["boe_fields"] = {
                "entry_no": data.get("entry_no"),
                "customs_office": data.get("customs_office"),
                "hs_code_classifications": data.get("hs_codes", []),
                "mbl_no": data.get("mbl_no"),
                "containers": data.get("containers", []),
                "gross_weight": data.get("gross_weight"),
                "gross_weight_unit": data.get("gross_weight_unit", "KG"),
                "vessel_name": data.get("vessel_name"),
                "port_of_loading": data.get("port_of_loading"),
                "port_of_discharge": data.get("port_of_discharge"),
            }

        elif doc_type == "DO":
            hvdc_fields["do_fields"] = {
                "do_number": data.get("do_number"),
                "do_validity_date": data.get("do_validity_date"),
                "container_release_dates": data.get("container_release_dates", []),
                "demurrage_risk_level": data.get("demurrage_risk_level"),
                "estimated_demurrage_usd": data.get("estimated_demurrage_usd"),
                "free_days_remaining": data.get("free_days_remaining"),
            }

        elif doc_type == "DN":
            hvdc_fields["dn_fields"] = {
                "origin": data.get("origin"),
                "destination": data.get("destination"),
                "vehicle_type": data.get("vehicle_type"),
                "destination_code": data.get("destination_code"),
                "do_reference": data.get("do_reference"),
                "driver_info": data.get("driver_info"),
            }

        elif doc_type == "CarrierInvoice":
            hvdc_fields["carrier_invoice_fields"] = {
                "carrier_name": data.get("carrier_name"),
                "invoice_number": data.get("invoice_number"),
                "invoice_date": data.get("invoice_date"),
                "total_amount": data.get("total_amount"),
                "currency": data.get("currency", "USD"),
                "line_items": data.get("line_items", []),
            }

        # Remove None values
        hvdc_fields = {
            k: {kk: vv for kk, vv in v.items() if vv is not None}
            for k, v in hvdc_fields.items()
            if v
        }

        return hvdc_fields


class DOMESTICToUnifiedIRAdapter(BaseAdapter):
    """
    Convert DOMESTIC PDF parser output to Unified IR format

    Input format (DOMESTIC):
    {
        "file_path": str,
        "text": str,
        "origin": str,
        "destination": str,
        "vehicle_type": str,
        "destination_code": str,
        "do_number": str
    }

    Output format: Unified IR (see unified_ir_schema_hvdc.yaml)
    """

    def convert(
        self, domestic_data: Dict, routing_decision: Optional[Dict] = None
    ) -> Dict:
        """
        Convert DOMESTIC format to Unified IR

        Args:
            domestic_data: Parsed DN data from DOMESTIC system
            routing_decision: Optional routing metadata

        Returns:
            Document in Unified IR format
        """
        try:
            file_path = domestic_data.get("file_path", "")
            doc_id = self._generate_doc_id(file_path)

            # Build Unified IR document
            unified_doc = {
                "doc_id": doc_id,
                "engine": (
                    routing_decision.get("engine_choice", "pymupdf")
                    if routing_decision
                    else "pymupdf"
                ),
                "routing_decision": routing_decision,
                "pages": 1,  # DOMESTIC doesn't track pages
                "meta": {
                    "filename": file_path.split("/")[-1] if file_path else "",
                    "mime": "application/pdf",
                    "created_at": datetime.now().isoformat(),
                    "checksum_sha256": (
                        self._calc_file_hash(file_path) if file_path else ""
                    ),
                    "doc_type": "DN",
                    "shipment_id": self._extract_shipment_id(file_path),
                },
                "blocks": self._extract_blocks(domestic_data),
                "hvdc_fields": {
                    "dn_fields": {
                        "origin": domestic_data.get("origin"),
                        "destination": domestic_data.get("destination"),
                        "vehicle_type": domestic_data.get("vehicle_type"),
                        "destination_code": domestic_data.get("destination_code"),
                        "do_reference": domestic_data.get("do_number"),
                    }
                },
                "gate_validation": None,
            }

            # Remove None values
            unified_doc["hvdc_fields"]["dn_fields"] = {
                k: v
                for k, v in unified_doc["hvdc_fields"]["dn_fields"].items()
                if v is not None
            }

            self.logger.info(f"Converted DOMESTIC document {doc_id} to Unified IR")
            return unified_doc

        except Exception as e:
            self.logger.error(f"Error converting DOMESTIC to Unified IR: {e}")
            raise

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique doc_id from file path"""
        if file_path:
            return hashlib.md5(file_path.encode()).hexdigest()[:16]
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:16]

    def _calc_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""

    def _extract_shipment_id(self, file_path: str) -> str:
        """Extract shipment ID from file path if present"""
        match = re.search(r"HVDC-[A-Z]+-[A-Z]+-\d+", file_path)
        return match.group(0) if match else ""

    def _extract_blocks(self, domestic_data: Dict) -> List[Dict]:
        """Extract blocks from DOMESTIC data"""
        blocks = []

        # Add text block for full text
        text = domestic_data.get("text", "")
        if text:
            blocks.append(
                {
                    "id": "text-1",
                    "type": "text",
                    "text": text,
                    "bbox": None,
                    "meta": {
                        "confidence": 0.85,
                        "source_engine": "pymupdf",
                        "page_idx": 0,
                    },
                }
            )

        return blocks


class UnifiedIRToSHPTAdapter(BaseAdapter):
    """
    Convert Unified IR back to SHPT format for Gate validation compatibility

    Input format: Unified IR
    Output format: SHPT DSVPDFParser compatible
    """

    def convert(self, unified_doc: Dict) -> Dict:
        """
        Convert Unified IR to SHPT format

        Args:
            unified_doc: Document in Unified IR format

        Returns:
            SHPT-compatible document
        """
        try:
            meta = unified_doc.get("meta", {})
            hvdc_fields = unified_doc.get("hvdc_fields", {})

            # Build SHPT format
            shpt_doc = {
                "header": {
                    "file_path": f"converted/{meta.get('filename', '')}",
                    "file_name": meta.get("filename", ""),
                    "doc_type": meta.get("doc_type", "Other"),
                    "shipment_id": meta.get("shipment_id", ""),
                },
                "data": self._extract_data(meta.get("doc_type"), hvdc_fields),
                "raw_text": self._extract_text(unified_doc.get("blocks", [])),
                "confidence": self._calc_confidence(unified_doc),
            }

            self.logger.info(
                f"Converted Unified IR {unified_doc.get('doc_id')} to SHPT format"
            )
            return shpt_doc

        except Exception as e:
            self.logger.error(f"Error converting Unified IR to SHPT: {e}")
            raise

    def _extract_data(self, doc_type: str, hvdc_fields: Dict) -> Dict:
        """Extract data based on document type"""
        if doc_type == "BOE" and "boe_fields" in hvdc_fields:
            return hvdc_fields["boe_fields"]
        elif doc_type == "DO" and "do_fields" in hvdc_fields:
            return hvdc_fields["do_fields"]
        elif doc_type == "DN" and "dn_fields" in hvdc_fields:
            return hvdc_fields["dn_fields"]
        elif doc_type == "CarrierInvoice" and "carrier_invoice_fields" in hvdc_fields:
            return hvdc_fields["carrier_invoice_fields"]
        return {}

    def _extract_text(self, blocks: List[Dict]) -> str:
        """Extract all text from blocks"""
        text_blocks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        return "\n".join(text_blocks)

    def _calc_confidence(self, unified_doc: Dict) -> float:
        """Calculate overall confidence from blocks"""
        blocks = unified_doc.get("blocks", [])
        if not blocks:
            return 0.9

        confidences = [
            b.get("meta", {}).get("confidence", 0.9) for b in blocks if b.get("meta")
        ]

        return sum(confidences) / len(confidences) if confidences else 0.9


class UnifiedIRToDOMESTICAdapter(BaseAdapter):
    """
    Convert Unified IR back to DOMESTIC format for enhanced matching compatibility

    Input format: Unified IR
    Output format: DOMESTIC PDF parser compatible
    """

    def convert(self, unified_doc: Dict) -> Dict:
        """
        Convert Unified IR to DOMESTIC format

        Args:
            unified_doc: Document in Unified IR format

        Returns:
            DOMESTIC-compatible document
        """
        try:
            meta = unified_doc.get("meta", {})
            dn_fields = unified_doc.get("hvdc_fields", {}).get("dn_fields", {})

            # Build DOMESTIC format
            domestic_doc = {
                "file_path": f"converted/{meta.get('filename', '')}",
                "text": self._extract_text(unified_doc.get("blocks", [])),
                "origin": dn_fields.get("origin"),
                "destination": dn_fields.get("destination"),
                "vehicle_type": dn_fields.get("vehicle_type"),
                "destination_code": dn_fields.get("destination_code"),
                "do_number": dn_fields.get("do_reference"),
            }

            self.logger.info(
                f"Converted Unified IR {unified_doc.get('doc_id')} to DOMESTIC format"
            )
            return domestic_doc

        except Exception as e:
            self.logger.error(f"Error converting Unified IR to DOMESTIC: {e}")
            raise

    def _extract_text(self, blocks: List[Dict]) -> str:
        """Extract all text from blocks"""
        text_blocks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        return "\n".join(text_blocks)


# Factory function for easy adapter creation
def create_adapter(adapter_type: str, log_level: str = "INFO"):
    """
    Factory function to create adapters

    Args:
        adapter_type: One of "shpt_to_ir", "domestic_to_ir", "ir_to_shpt", "ir_to_domestic"
        log_level: Logging level

    Returns:
        Adapter instance
    """
    adapters = {
        "shpt_to_ir": SHPTToUnifiedIRAdapter,
        "domestic_to_ir": DOMESTICToUnifiedIRAdapter,
        "ir_to_shpt": UnifiedIRToSHPTAdapter,
        "ir_to_domestic": UnifiedIRToDOMESTICAdapter,
    }

    if adapter_type not in adapters:
        raise ValueError(f"Unknown adapter type: {adapter_type}")

    return adapters[adapter_type](log_level=log_level)


if __name__ == "__main__":
    # Example usage
    print("HVDC Data Adapters - Test Module")

    # Test SHPT to IR
    shpt_data = {
        "header": {
            "file_path": "/data/HVDC-ADOPT-SCT-0126_BOE.pdf",
            "file_name": "HVDC-ADOPT-SCT-0126_BOE.pdf",
            "doc_type": "BOE",
            "shipment_id": "HVDC-ADOPT-SCT-0126",
        },
        "data": {
            "mbl_no": "MAEU123456789",
            "containers": ["TCLU1234567"],
            "gross_weight": 15000.5,
            "entry_no": "AUH-2025-001234",
        },
        "raw_text": "Sample BOE text...",
        "confidence": 0.95,
    }

    adapter = create_adapter("shpt_to_ir")
    unified = adapter.convert(shpt_data)
    print(f"\nConverted SHPT to Unified IR: {unified['doc_id']}")
    print(f"Doc Type: {unified['meta']['doc_type']}")
    print(f"Shipment ID: {unified['meta']['shipment_id']}")
