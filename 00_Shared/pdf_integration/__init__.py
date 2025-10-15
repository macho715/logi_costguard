"""
PDF Integration Module
======================

HVDC Invoice Audit 시스템용 PDF 파싱 및 검증 통합 모듈

Usage:
    from pdf_integration import DSVPDFParser, CrossDocValidator, OntologyMapper

Author: HVDC Logistics Team
Version: 1.0.0
"""

try:
    from .pdf_parser import (
        DSVPDFParser,
        DocumentHeader,
        BOEData,
        DOData,
        DNData,
        CarrierInvoiceData,
    )
except ImportError:
    # Fallback if dependencies not installed
    DSVPDFParser = None
    DocumentHeader = None
    BOEData = None
    DOData = None
    DNData = None
    CarrierInvoiceData = None

from .cross_doc_validator import CrossDocValidator

from .ontology_mapper import OntologyMapper

from .workflow_automator import WorkflowAutomator

__all__ = [
    # Parser
    "DSVPDFParser",
    "DocumentHeader",
    "BOEData",
    "DOData",
    "DNData",
    "CarrierInvoiceData",
    # Validator
    "CrossDocValidator",
    # Ontology
    "OntologyMapper",
    # Automation
    "WorkflowAutomator",
]

__version__ = "1.0.0"
