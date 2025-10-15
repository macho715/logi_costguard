"""
HVDC Hybrid Integration Package

Provides hybrid Docling/ADE PDF parsing integration for SHPT and DOMESTIC systems.

Main Components:
- HybridPDFRouter: Route documents to optimal parsing engine
- Data Adapters: Convert between SHPT/DOMESTIC and Unified IR formats
- SchemaValidator: Validate documents against Unified IR schema
- Routing Rules: HVDC-specific routing configuration
- Unified IR Schema: Standardized document representation

Usage:
    from hybrid_integration import HybridPDFRouter, create_adapter, SchemaValidator

    # Create router
    router = HybridPDFRouter()

    # Route document
    decision = router.decide_route("/path/to/document.pdf")

    # Convert SHPT to Unified IR
    adapter = create_adapter("shpt_to_ir")
    unified_doc = adapter.convert(shpt_data, routing_decision=decision)

    # Validate
    validator = SchemaValidator()
    is_valid, errors = validator.validate(unified_doc)
"""

__version__ = "1.0.0"
__author__ = "HVDC Logistics AI Team"

from .hybrid_pdf_router import HybridPDFRouter
from .data_adapters import (
    SHPTToUnifiedIRAdapter,
    DOMESTICToUnifiedIRAdapter,
    UnifiedIRToSHPTAdapter,
    UnifiedIRToDOMESTICAdapter,
    create_adapter,
)
from .schema_validator import SchemaValidator

__all__ = [
    # Router
    "HybridPDFRouter",
    # Adapters
    "SHPTToUnifiedIRAdapter",
    "DOMESTICToUnifiedIRAdapter",
    "UnifiedIRToSHPTAdapter",
    "UnifiedIRToDOMESTICAdapter",
    "create_adapter",
    # Validator
    "SchemaValidator",
    # Version
    "__version__",
]
