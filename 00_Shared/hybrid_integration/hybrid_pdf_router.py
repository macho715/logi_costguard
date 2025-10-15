#!/usr/bin/env python3
"""
Hybrid PDF Router for HVDC Integration

Routes PDF documents to optimal parsing engine (Docling or ADE) based on:
- Document characteristics (type, pages, tables, skew, etc.)
- Budget constraints
- Sensitivity requirements
- Routing rules (routing_rules_hvdc.json)
"""

from typing import Dict, List, Optional, Tuple
import json
import logging
from pathlib import Path
from datetime import datetime, date
import hashlib


class HybridPDFRouter:
    """
    Intelligent routing engine for hybrid Docling/ADE parsing

    Features:
    - Rule-based routing from routing_rules_hvdc.json
    - Budget tracking for ADE usage
    - Automatic fallback on engine failure
    - Document type detection
    - Routing decision logging
    """

    def __init__(self, config_path: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize router

        Args:
            config_path: Path to routing_rules_hvdc.json
            log_level: Logging level
        """
        self.logger = self._setup_logger(log_level)

        # Load routing rules
        if not config_path:
            config_path = str(Path(__file__).parent / "routing_rules_hvdc.json")

        self.rules = self._load_rules(config_path)
        self.default_engine = self.rules.get("default_engine", "docling")
        self.daily_budget = self.rules.get("daily_ade_budget_usd", 50.0)
        self.sensitivity_list = self.rules.get("sensitivity_force_local", [])

        # Budget tracking (resets daily)
        self.budget_date = date.today()
        self.budget_used = 0.0

        # Routing metrics
        self.routing_history = []

        self.logger.info(
            f"HybridPDFRouter initialized with {len(self.rules.get('rules', []))} rules"
        )

    def _setup_logger(self, level: str) -> logging.Logger:
        logger = logging.getLogger("HybridPDFRouter")
        logger.setLevel(getattr(logging, level))
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _load_rules(self, config_path: str) -> Dict:
        """Load routing rules from JSON file"""
        try:
            with open(config_path, "r") as f:
                rules = json.load(f)
            self.logger.info(f"Loaded routing rules from {config_path}")
            return rules
        except FileNotFoundError:
            self.logger.error(f"Routing rules file not found: {config_path}")
            return {"default_engine": "docling", "rules": []}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in routing rules: {e}")
            return {"default_engine": "docling", "rules": []}

    def decide_route(
        self,
        file_path: str,
        doc_characteristics: Optional[Dict] = None,
        force_engine: Optional[str] = None,
    ) -> Dict:
        """
        Make routing decision for a document

        Args:
            file_path: Path to PDF file
            doc_characteristics: Optional pre-analyzed characteristics
            force_engine: Force specific engine (for testing)

        Returns:
            Routing decision dict with:
                - engine_choice: "docling" or "ade"
                - rule_matched: Name of matched rule
                - reason: Human-readable reason
                - confidence: Expected parsing confidence
                - fallback_used: Whether fallback was triggered
                - latency_ms: Expected latency (estimated)
                - ade_cost_usd: Estimated ADE cost (if applicable)
        """
        # Reset budget if new day
        self._check_budget_reset()

        # Force engine if specified (for testing)
        if force_engine:
            return self._create_decision(
                engine=force_engine,
                rule_name="forced",
                reason=f"Forced to {force_engine} by caller",
            )

        # Analyze document if characteristics not provided
        if not doc_characteristics:
            doc_characteristics = self._analyze_document(file_path)

        # Check budget constraint first (highest priority after sensitive)
        if self._is_budget_exceeded():
            return self._create_decision(
                engine="docling",
                rule_name="ade_budget_guard",
                reason=f"ADE budget exceeded (${self.budget_used:.2f}/${self.daily_budget})",
            )

        # Check sensitivity (critical priority)
        if self._is_sensitive_document(doc_characteristics):
            return self._create_decision(
                engine="docling",
                rule_name="sensitive_force_local",
                reason="Sensitive document - local processing only",
            )

        # Match against rules
        matched_rule = self._match_rules(doc_characteristics)

        if matched_rule:
            engine = matched_rule["action"]["engine"]

            # Handle "swap" action for fallback scenarios
            if engine == "swap":
                engine = self._get_swap_engine(doc_characteristics)

            decision = self._create_decision(
                engine=engine,
                rule_name=matched_rule["name"],
                reason=matched_rule["action"]["reason"],
                doc_characteristics=doc_characteristics,
            )
        else:
            # No rule matched - use default
            decision = self._create_decision(
                engine=self.default_engine,
                rule_name="default",
                reason=f"No specific rule matched - using default ({self.default_engine})",
                doc_characteristics=doc_characteristics,
            )

        # Update budget if using ADE
        if decision["engine_choice"] == "ade":
            self.budget_used += decision.get("ade_cost_usd", 0.0)

        # Log decision
        self.routing_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "decision": decision,
            }
        )

        self.logger.info(
            f"Routed {Path(file_path).name} to {decision['engine_choice']} "
            f"(rule: {decision['rule_matched']}, confidence: {decision['confidence']:.2f})"
        )

        return decision

    def _analyze_document(self, file_path: str) -> Dict:
        """
        Analyze document characteristics

        Returns:
            Dict with:
                - doc_type: Detected type (BOE/DO/DN/CarrierInvoice/Other)
                - pages: Number of pages
                - table_density: Estimated table density (0-1)
                - skew_deg: Estimated skew in degrees
                - dpi: Estimated DPI
                - file_size_mb: File size in MB
                - visual_relations: List of detected visual elements
        """
        characteristics = {
            "doc_type": self._detect_doc_type(file_path),
            "pages": self._estimate_pages(file_path),
            "table_density": 0.0,  # Would need actual analysis
            "skew_deg": 0.0,
            "dpi": 300,  # Assume reasonable DPI
            "file_size_mb": self._get_file_size(file_path),
            "visual_relations": [],
            "container_count": 0,
            "hs_code_count": 0,
            "line_item_count": 0,
            "multi_stop_detected": False,
        }

        self.logger.debug(f"Analyzed {Path(file_path).name}: {characteristics}")
        return characteristics

    def _detect_doc_type(self, file_path: str) -> str:
        """Detect document type from filename"""
        filename = Path(file_path).name.upper()

        if "BOE" in filename:
            return "BOE"
        elif "DO" in filename and "DN" not in filename:
            return "DO"
        elif "DN" in filename:
            return "DN"
        elif "CARRIER" in filename or "INVOICE" in filename:
            return "CarrierInvoice"
        else:
            return "Other"

    def _estimate_pages(self, file_path: str) -> int:
        """Estimate page count (simplified - would need actual PDF reading)"""
        try:
            # Rough estimate based on file size
            file_size_mb = self._get_file_size(file_path)
            # Assume ~100KB per page average
            estimated_pages = max(1, int(file_size_mb * 10))
            return estimated_pages
        except:
            return 1

    def _get_file_size(self, file_path: str) -> float:
        """Get file size in MB"""
        try:
            size_bytes = Path(file_path).stat().st_size
            return size_bytes / (1024 * 1024)
        except:
            return 0.0

    def _is_budget_exceeded(self) -> bool:
        """Check if daily ADE budget is exceeded"""
        return self.budget_used >= self.daily_budget

    def _is_sensitive_document(self, characteristics: Dict) -> bool:
        """Check if document is marked as sensitive"""
        doc_type = characteristics.get("doc_type", "").lower()
        # Check against sensitivity list
        return any(sensitive in doc_type for sensitive in self.sensitivity_list)

    def _match_rules(self, characteristics: Dict) -> Optional[Dict]:
        """
        Match document characteristics against rules

        Returns matched rule or None
        """
        doc_type = characteristics.get("doc_type")

        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(
            self.rules.get("rules", []),
            key=lambda r: r.get("priority", 0),
            reverse=True,
        )

        for rule in sorted_rules:
            # Check if rule applies to this doc type
            rule_doc_types = rule.get("doc_types", [])
            if rule_doc_types and doc_type not in rule_doc_types:
                continue

            # Check rule conditions
            when = rule.get("when", {})
            if self._check_conditions(when, characteristics):
                return rule

        return None

    def _check_conditions(self, when: Dict, characteristics: Dict) -> bool:
        """Check if all conditions in 'when' clause are met"""
        for condition, value in when.items():
            if condition == "default":
                return True
            elif condition == "pages_gt":
                if characteristics.get("pages", 0) <= value:
                    return False
            elif condition == "pages_gte":
                if characteristics.get("pages", 0) < value:
                    return False
            elif condition == "table_density_gte":
                if characteristics.get("table_density", 0) < value:
                    return False
            elif condition == "skew_deg_gte":
                if characteristics.get("skew_deg", 0) < value:
                    return False
            elif condition == "dpi_lt":
                if characteristics.get("dpi", 300) >= value:
                    return False
            elif condition == "container_count_gte":
                if characteristics.get("container_count", 0) < value:
                    return False
            elif condition == "hs_code_count_gte":
                if characteristics.get("hs_code_count", 0) < value:
                    return False
            elif condition == "line_item_count_gte":
                if characteristics.get("line_item_count", 0) < value:
                    return False
            elif condition == "multi_stop_detected":
                if not characteristics.get("multi_stop_detected", False):
                    return False
            elif condition == "visual_relations":
                doc_relations = characteristics.get("visual_relations", [])
                required_relations = value
                if not any(rel in doc_relations for rel in required_relations):
                    return False
            elif condition == "sensitivity_in":
                # Already handled separately
                pass
            elif condition == "ade_budget_exceeded":
                if value != self._is_budget_exceeded():
                    return False
            elif condition == "engine_failed":
                # Would be set by caller in retry scenarios
                if not characteristics.get("engine_failed", False):
                    return False

        return True

    def _get_swap_engine(self, characteristics: Dict) -> str:
        """Determine swap engine for fallback scenarios"""
        failed_engine = characteristics.get("failed_engine")

        if failed_engine == "ade":
            return "docling"
        elif failed_engine == "docling":
            # Only swap to ADE if budget allows
            return "ade" if not self._is_budget_exceeded() else "docling"
        else:
            return self.default_engine

    def _create_decision(
        self,
        engine: str,
        rule_name: str,
        reason: str,
        doc_characteristics: Optional[Dict] = None,
    ) -> Dict:
        """Create routing decision dictionary"""
        decision = {
            "rule_matched": rule_name,
            "reason": reason,
            "engine_choice": engine,
            "confidence": 0.90,  # Base confidence
            "fallback_used": "fallback" in rule_name.lower(),
            "latency_ms": 0,  # Will be filled by actual parsing
            "ade_cost_usd": 0.0,
        }

        # Estimate ADE cost if using ADE
        if engine == "ade" and doc_characteristics:
            pages = doc_characteristics.get("pages", 1)
            cost_per_page = self.rules.get("cost_management", {}).get(
                "ade_cost_per_page_usd", 0.01
            )
            decision["ade_cost_usd"] = pages * cost_per_page

        # Adjust confidence based on engine and doc type
        if doc_characteristics:
            doc_type = doc_characteristics.get("doc_type", "Other")
            if engine == "ade":
                # ADE generally has higher confidence for complex docs
                if doc_characteristics.get("table_density", 0) > 0.3:
                    decision["confidence"] = 0.95
                elif doc_characteristics.get("pages", 1) > 10:
                    decision["confidence"] = 0.93
                else:
                    decision["confidence"] = 0.92
            else:
                # Docling confidence
                decision["confidence"] = 0.90

        return decision

    def _check_budget_reset(self):
        """Reset budget tracking if new day"""
        today = date.today()
        if today != self.budget_date:
            self.logger.info(
                f"Resetting ADE budget (used ${self.budget_used:.2f} on {self.budget_date})"
            )
            self.budget_date = today
            self.budget_used = 0.0

    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        return {
            "date": self.budget_date.isoformat(),
            "daily_limit_usd": self.daily_budget,
            "used_usd": self.budget_used,
            "remaining_usd": self.daily_budget - self.budget_used,
            "usage_pct": (
                (self.budget_used / self.daily_budget * 100)
                if self.daily_budget > 0
                else 0
            ),
        }

    def get_routing_metrics(self) -> Dict:
        """Get routing metrics and statistics"""
        if not self.routing_history:
            return {"total_routes": 0}

        total = len(self.routing_history)
        ade_count = sum(
            1 for r in self.routing_history if r["decision"]["engine_choice"] == "ade"
        )
        docling_count = total - ade_count

        total_ade_cost = sum(
            r["decision"].get("ade_cost_usd", 0)
            for r in self.routing_history
            if r["decision"]["engine_choice"] == "ade"
        )

        return {
            "total_routes": total,
            "ade_routes": ade_count,
            "docling_routes": docling_count,
            "ade_percentage": (ade_count / total * 100) if total > 0 else 0,
            "total_ade_cost_usd": total_ade_cost,
            "budget_status": self.get_budget_status(),
        }


if __name__ == "__main__":
    # Example usage
    print("HVDC Hybrid PDF Router - Test Module\n")

    router = HybridPDFRouter()

    # Test routing decisions
    test_files = [
        "/data/HVDC-ADOPT-SCT-0126_BOE.pdf",
        "/data/HVDC-ADOPT-SCT-0127_DO.pdf",
        "/data/HVDC-ADOPT-SCT-0128_DN.pdf",
    ]

    for file_path in test_files:
        decision = router.decide_route(file_path)
        print(f"\nFile: {Path(file_path).name}")
        print(f"  Engine: {decision['engine_choice']}")
        print(f"  Rule: {decision['rule_matched']}")
        print(f"  Reason: {decision['reason']}")
        print(f"  Confidence: {decision['confidence']:.2f}")
        if decision.get("ade_cost_usd", 0) > 0:
            print(f"  Est. Cost: ${decision['ade_cost_usd']:.4f}")

    # Print metrics
    print("\n" + "=" * 60)
    print("ROUTING METRICS:")
    metrics = router.get_routing_metrics()
    print(f"  Total Routes: {metrics['total_routes']}")
    print(f"  ADE Routes: {metrics['ade_routes']} ({metrics['ade_percentage']:.1f}%)")
    print(f"  Docling Routes: {metrics['docling_routes']}")
    print(f"  Total ADE Cost: ${metrics['total_ade_cost_usd']:.2f}")

    budget = metrics["budget_status"]
    print(f"\nBudget Status:")
    print(f"  Daily Limit: ${budget['daily_limit_usd']:.2f}")
    print(f"  Used: ${budget['used_usd']:.2f}")
    print(f"  Remaining: ${budget['remaining_usd']:.2f}")
    print(f"  Usage: {budget['usage_pct']:.1f}%")
