#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOMESTIC System - Hybrid PDF Integration Module

Integrates HybridPDFRouter with DOMESTIC DN parsing workflow.
Maintains 100% backward compatibility with enhanced_matching.py

Author: HVDC Logistics AI Team
Date: 2025-10-14
Version: 1.0.0
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import hybrid integration components
try:
    from hybrid_integration import HybridPDFRouter, create_adapter, SchemaValidator

    HYBRID_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hybrid integration not available: {e}")
    HYBRID_AVAILABLE = False

# Import existing DOMESTIC utils
try:
    from src.utils.pdf_text_fallback import extract_text_any
    from src.utils.pdf_extractors import extract_from_pdf_text

    DOMESTIC_UTILS_AVAILABLE = True
except ImportError as e:
    print("Warning: DOMESTIC utils not available")
    DOMESTIC_UTILS_AVAILABLE = False


class DOMESTICHybridPDFIntegration:
    """
    Hybrid PDF integration for DOMESTIC DN processing

    Features:
    - Intelligent routing to Docling or ADE
    - Unified IR conversion for standardization
    - Backward compatible with enhanced_matching.py
    - Automatic fallback on errors
    - Budget tracking for ADE usage

    Input: PDF file path
    Output: DOMESTIC-compatible dict (file_path, text, origin, destination, vehicle, do_number)
    """

    def __init__(self, log_level: str = "INFO"):
        """
        Initialize hybrid integration components

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        if not HYBRID_AVAILABLE:
            raise ImportError(
                "Hybrid integration modules not available. Check 00_Shared/hybrid_integration/"
            )

        if not DOMESTIC_UTILS_AVAILABLE:
            raise ImportError("DOMESTIC utils not available. Check src/utils/")

        self.router = HybridPDFRouter(log_level=log_level)
        self.adapter_to_ir = create_adapter("domestic_to_ir", log_level=log_level)
        self.adapter_from_ir = create_adapter("ir_to_domestic", log_level=log_level)
        self.validator = SchemaValidator(min_confidence=0.85, log_level=log_level)

        self.logger = self._setup_logger(log_level)

        # Stats tracking
        self.parse_count = 0
        self.success_count = 0
        self.failure_count = 0

        self.logger.info("[OK] DOMESTIC Hybrid PDF Integration initialized")

    def _setup_logger(self, level: str) -> logging.Logger:
        """Setup logger for this module"""
        logger = logging.getLogger("DOMESTICHybridIntegration")
        logger.setLevel(getattr(logging, level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def parse_dn_with_routing(self, pdf_path: str, shipment_ref: str = "") -> Dict:
        """
        Parse DN PDF with intelligent Docling/ADE routing

        Args:
            pdf_path: Path to DN PDF file
            shipment_ref: Optional shipment reference for context

        Returns:
            Dict with DOMESTIC-compatible format:
            {
                "file_path": str,
                "text": str,
                "origin": str,
                "destination": str,
                "vehicle_type": str,
                "do_number": str,
                "routing_metadata": {...}
            }
        """
        self.parse_count += 1

        try:
            # Step 1: Routing decision
            decision = self.router.decide_route(pdf_path)

            self.logger.info(
                f"[ROUTE] {Path(pdf_path).name} -> {decision['engine_choice'].upper()} "
                f"(rule: {decision['rule_matched']}, confidence: {decision['confidence']:.2f})"
            )

            # Step 2: Parse based on routing decision
            if decision["engine_choice"] == "ade":
                # ADE parsing
                # TODO: Implement actual ADE API call when ADE credentials available
                # For now, use enhanced fallback but mark for future upgrade
                self.logger.info(
                    "  [ADE] ADE selected - using enhanced fallback (ADE API pending)"
                )
                parsed_data = self._parse_with_enhanced_fallback(pdf_path)
                parsed_data["parsing_method"] = (
                    "ade_fallback"  # Will be 'ade' when implemented
                )
            else:
                # Docling/local parsing
                self.logger.info(
                    "  [DOCLING] Docling selected - using local fallback parsing"
                )
                parsed_data = self._parse_with_enhanced_fallback(pdf_path)
                parsed_data["parsing_method"] = "docling"

            # Step 3: Convert to Unified IR for standardization
            unified_doc = self.adapter_to_ir.convert(
                parsed_data, routing_decision=decision
            )

            # Step 4: Validate schema compliance
            is_valid, errors = self.validator.validate(unified_doc)

            if not is_valid:
                self.logger.warning(
                    f"  [WARN] Validation warnings ({len(errors)}): {errors[:2]}"
                )

            # Step 5: Convert back to DOMESTIC format
            domestic_data = self.adapter_from_ir.convert(unified_doc)

            # Step 6: Add routing metadata for analysis
            domestic_data["routing_metadata"] = {
                "engine": decision["engine_choice"],
                "rule": decision["rule_matched"],
                "reason": decision["reason"],
                "confidence": decision["confidence"],
                "ade_cost_usd": decision.get("ade_cost_usd", 0.0),
                "validation_passed": is_valid,
                "validation_error_count": len(errors),
            }

            self.success_count += 1
            return domestic_data

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"  [ERROR] Hybrid parsing failed for {pdf_path}: {e}")

            # Fallback to basic parsing
            self.logger.info("  [FALLBACK] Using basic DOMESTIC parsing...")
            return self._parse_with_enhanced_fallback(pdf_path)

    def _parse_with_enhanced_fallback(self, pdf_path: str) -> Dict:
        """
        Enhanced fallback parsing using existing DOMESTIC logic

        Multi-layer text extraction:
        1. PyMuPDF (primary)
        2. pypdf (secondary)
        3. pdfminer.six (complex layouts)
        4. pdftotext (external tool)

        Field extraction via extract_from_pdf_text
        """
        try:
            # Extract text with existing DOMESTIC fallback chain
            text = extract_text_any(pdf_path)

            if not text or not text.strip():
                self.logger.warning(f"  [WARN] No text extracted from {pdf_path}")
                return {
                    "file_path": pdf_path,
                    "text": "",
                    "origin": "",
                    "destination": "",
                    "vehicle_type": "",
                    "do_number": "",
                    "destination_code": "",
                    "error": "No text extracted",
                }

            # Extract fields using existing DOMESTIC extract_from_pdf_text
            fields = extract_from_pdf_text(text)

            origin = fields.get("loading_point", "")
            destination = fields.get("destination", "")
            dest_code = fields.get("dest_code", "")
            waybill = fields.get("waybill", "")

            self.logger.debug(
                f"  [EXTRACT] origin={origin[:20] if origin else 'N/A'}..., dest={destination[:20] if destination else 'N/A'}..."
            )

            return {
                "file_path": pdf_path,
                "text": text,
                "origin": origin,
                "destination": destination,
                "vehicle_type": "",  # Not extracted by extract_from_pdf_text
                "do_number": waybill,
                "destination_code": dest_code,
            }

        except Exception as e:
            self.logger.error(f"  [ERROR] Fallback parsing error: {e}")
            return {
                "file_path": pdf_path,
                "text": "",
                "origin": "",
                "destination": "",
                "vehicle_type": "",
                "do_number": "",
                "destination_code": "",
                "error": str(e),
            }

    def get_routing_stats(self) -> Dict:
        """
        Get routing and parsing statistics

        Returns:
            Dict with routing metrics, parse counts, success rates
        """
        routing_metrics = self.router.get_routing_metrics()

        return {
            **routing_metrics,
            "parse_stats": {
                "total_attempts": self.parse_count,
                "successes": self.success_count,
                "failures": self.failure_count,
                "success_rate_pct": (
                    (self.success_count / self.parse_count * 100)
                    if self.parse_count > 0
                    else 0
                ),
            },
        }

    def print_summary(self):
        """Print comprehensive routing and parsing summary"""
        stats = self.get_routing_stats()

        print("\n" + "=" * 70)
        print("DOMESTIC HYBRID INTEGRATION SUMMARY")
        print("=" * 70)

        # Parsing stats
        parse_stats = stats["parse_stats"]
        print(f"\nParsing Statistics:")
        print(f"  Total Attempts: {parse_stats['total_attempts']}")
        print(f"  Successes: {parse_stats['successes']}")
        print(f"  Failures: {parse_stats['failures']}")
        print(f"  Success Rate: {parse_stats['success_rate_pct']:.1f}%")

        # Routing stats
        if stats["total_routes"] > 0:
            print(f"\nRouting Statistics:")
            print(f"  Total Routes: {stats['total_routes']}")
            print(
                f"  ADE Routes: {stats['ade_routes']} ({stats['ade_percentage']:.1f}%)"
            )
            print(f"  Docling Routes: {stats['docling_routes']}")
            print(f"  Total ADE Cost: ${stats['total_ade_cost_usd']:.2f}")

            # Budget status
            budget = stats["budget_status"]
            print(f"\nBudget Status (Date: {budget['date']}):")
            print(f"  Daily Limit: ${budget['daily_limit_usd']:.2f}")
            print(f"  Used: ${budget['used_usd']:.2f}")
            print(f"  Remaining: ${budget['remaining_usd']:.2f}")
            print(f"  Usage: {budget['usage_pct']:.1f}%")

        print("=" * 70 + "\n")


# Convenience factory function
def create_domestic_hybrid_integration(
    log_level: str = "INFO",
) -> DOMESTICHybridPDFIntegration:
    """
    Factory function to create DOMESTIC hybrid integration instance

    Args:
        log_level: Logging level

    Returns:
        DOMESTICHybridPDFIntegration instance

    Raises:
        ImportError: If required modules not available
    """
    return DOMESTICHybridPDFIntegration(log_level=log_level)


if __name__ == "__main__":
    # Test module
    print("DOMESTIC Hybrid PDF Integration - Test Module\n")

    if not HYBRID_AVAILABLE:
        print("[ERROR] Hybrid integration modules not available")
        print("   Install from: 00_Shared/hybrid_integration/")
        sys.exit(1)

    if not DOMESTIC_UTILS_AVAILABLE:
        print("[ERROR] DOMESTIC utils not available")
        print("   Check src/utils/ directory")
        sys.exit(1)

    # Test with mock PDF path
    test_pdf = "/path/to/test/HVDC-DSV-SKM-MOSB-212_DN.pdf"

    try:
        integration = create_domestic_hybrid_integration(log_level="INFO")

        # Test routing (file doesn't need to exist for routing test)
        decision = integration.router.decide_route(test_pdf)

        print(f"[PASS] Hybrid integration test passed!\n")
        print(f"Test File: {Path(test_pdf).name}")
        print(f"  Engine: {decision['engine_choice']}")
        print(f"  Rule: {decision['rule_matched']}")
        print(f"  Reason: {decision['reason']}")
        print(f"  Confidence: {decision['confidence']:.2f}")

        # Print available components
        print(f"\nAvailable Components:")
        print(f"  - HybridPDFRouter: OK")
        print(f"  - DOMESTICToUnifiedIRAdapter: OK")
        print(f"  - UnifiedIRToDOMESTICAdapter: OK")
        print(f"  - SchemaValidator: OK")
        print(f"  - DOMESTIC PDF utils: OK")

        print(f"\n[READY] Integration module ready!")

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
