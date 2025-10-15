# HVDC Hybrid Integration Module

**Version**: 1.0.0
**Status**: Production Ready
**Project**: HVDC Invoice Audit - Docling/ADE Hybrid Parser Integration

## Overview

This module provides intelligent routing and integration between local (Docling) and cloud (LandingAI ADE) PDF parsing engines for the HVDC Invoice Audit System (SHPT and DOMESTIC).

### Key Features

- ✅ **Intelligent Routing**: Routes documents to optimal engine based on characteristics
- ✅ **Budget Control**: Daily ADE budget cap with automatic Docling fallback
- ✅ **Unified IR Schema**: Standardized document representation across systems
- ✅ **Data Adapters**: Seamless conversion between SHPT/DOMESTIC and Unified IR
- ✅ **Schema Validation**: Comprehensive validation with confidence thresholds
- ✅ **Gate Validation Ready**: Prepares documents for Gate-11~14 validation

## Architecture

```
hybrid_integration/
├── __init__.py                      # Package initialization
├── README.md                         # This file
├── INTEGRATION_DESIGN.md             # Detailed architecture design
│
├── hybrid_pdf_router.py              # Routing engine
├── data_adapters.py                  # Format conversion
├── schema_validator.py               # Document validation
│
├── routing_rules_hvdc.json           # HVDC-specific routing rules
└── unified_ir_schema_hvdc.yaml       # Extended Unified IR schema
```

## Quick Start

### 1. Installation

```python
# Add to your Python path
import sys
sys.path.insert(0, '/path/to/HVDC_Invoice_Audit/00_Shared')

# Import module
from hybrid_integration import HybridPDFRouter, create_adapter, SchemaValidator
```

### 2. Basic Usage

```python
# Initialize router
router = HybridPDFRouter()

# Route a document
decision = router.decide_route("/data/HVDC-ADOPT-SCT-0126_BOE.pdf")
print(f"Engine: {decision['engine_choice']}")  # "docling" or "ade"
print(f"Reason: {decision['reason']}")
print(f"Confidence: {decision['confidence']}")

# Check budget status
budget = router.get_budget_status()
print(f"ADE Budget: ${budget['used_usd']:.2f} / ${budget['daily_limit_usd']:.2f}")
```

### 3. Data Conversion

```python
# Convert SHPT to Unified IR
shpt_adapter = create_adapter("shpt_to_ir")
unified_doc = shpt_adapter.convert(shpt_parsed_data, routing_decision=decision)

# Convert DOMESTIC to Unified IR
domestic_adapter = create_adapter("domestic_to_ir")
unified_doc = domestic_adapter.convert(domestic_parsed_data, routing_decision=decision)

# Convert back to SHPT (for Gate validation)
shpt_adapter_back = create_adapter("ir_to_shpt")
shpt_doc = shpt_adapter_back.convert(unified_doc)
```

### 4. Validation

```python
# Validate document
validator = SchemaValidator(min_confidence=0.90)
is_valid, errors = validator.validate(unified_doc)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Check Gate validation readiness
gate_ready, gate_errors = validator.validate_for_gate(unified_doc)
print(f"Gate Validation Ready: {gate_ready}")
```

## Routing Rules

### Rule Priority

Rules are evaluated in priority order (highest first):

1. **Priority 1000**: Sensitive documents (contracts, price-sensitive) → Docling
2. **Priority 200**: Engine fallback scenarios
3. **Priority 100**: Budget exceeded → Docling
4. **Priority 8**: Visual relationships → ADE
5. **Priority 7**: Poor scan quality → ADE
6. **Priority 6**: Complex documents → ADE
7. **Priority 5**: Table-dense/multi-page → ADE
8. **Priority 1**: Default → Docling

### Document Type Routing

**BOE (Bill of Entry)**:
- Table density ≥ 30% → ADE
- Pages > 12 → ADE
- HS code count ≥ 5 → ADE
- Otherwise → Docling

**DO (Delivery Order)**:
- Skew ≥ 4° → ADE
- Multi-container (≥3) → ADE
- Otherwise → Docling

**DN (Delivery Note)**:
- Pages ≥ 4 → ADE
- Multi-stop detected → ADE
- Otherwise → Docling

**Carrier Invoice**:
- Line items ≥ 10 → ADE
- Otherwise → Docling

## Unified IR Schema

### Core Structure

```yaml
document:
  doc_id: unique_identifier
  engine: "docling" | "ade"
  routing_decision:
    rule_matched: rule_name
    reason: explanation
    engine_choice: chosen_engine
    confidence: 0.0-1.0
  meta:
    filename: string
    doc_type: BOE | DO | DN | CarrierInvoice
    shipment_id: HVDC-XXX-YYY-NNNN
  blocks:
    - id: block_id
      type: text | table | figure | ...
      text: content
      bbox: {page, x0, y0, x1, y1}
  hvdc_fields:
    boe_fields: {...}
    do_fields: {...}
    dn_fields: {...}
    carrier_invoice_fields: {...}
  gate_validation:
    gates: [...]
```

### HVDC-Specific Fields

**BOE Fields**:
- `entry_no`: Customs entry number
- `mbl_no`: Master Bill of Lading
- `containers`: Array of container numbers
- `gross_weight`: Total weight
- `hs_code_classifications`: HS code items

**DO Fields**:
- `do_number`: Delivery Order number
- `do_validity_date`: Expiry date
- `demurrage_risk_level`: LOW/MEDIUM/HIGH/CRITICAL
- `estimated_demurrage_usd`: Cost estimate

**DN Fields**:
- `origin`: Loading point
- `destination`: Delivery destination
- `vehicle_type`: Transport vehicle
- `destination_code`: For lane matching

## Budget Management

### Daily Budget Control

```python
# Configure in routing_rules_hvdc.json
{
  "daily_ade_budget_usd": 50.0,
  "cost_management": {
    "ade_cost_per_page_usd": 0.01,
    "budget_alert_threshold_pct": 0.80
  }
}
```

### Automatic Fallback

When budget is exceeded:
1. All new documents route to Docling
2. Budget resets at midnight
3. Routing history preserved

### Budget Monitoring

```python
budget = router.get_budget_status()
print(f"Daily Limit: ${budget['daily_limit_usd']}")
print(f"Used: ${budget['used_usd']} ({budget['usage_pct']:.1f}%)")
print(f"Remaining: ${budget['remaining_usd']}")
```

## Confidence Thresholds

### HVDC Safety-Critical Requirements

Field-level confidence thresholds (from `routing_rules_hvdc.json`):

```json
{
  "confidence_thresholds": {
    "boe": {
      "mbl_no": 0.95,
      "entry_no": 0.95,
      "containers": 0.90,
      "hs_code": 0.95
    },
    "do": {
      "do_number": 0.95,
      "do_validity_date": 0.90
    },
    "dn": {
      "origin": 0.85,
      "destination": 0.85
    }
  }
}
```

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Parsing Success Rate** | >95% | TBD |
| **Processing Latency** | <10s | TBD |
| **Gate Validation Accuracy** | >98% | TBD |
| **ADE Daily Budget** | ≤$50 | Tracked |
| **Cache Hit Rate** | >40% | TBD |

## Integration Points

### SHPT System

```python
# In invoice_pdf_integration.py
from hybrid_integration import HybridPDFRouter, create_adapter

router = HybridPDFRouter()
adapter = create_adapter("shpt_to_ir")

# Parse with routing
decision = router.decide_route(pdf_path)
# ... parse with chosen engine ...
unified_doc = adapter.convert(parsed_data, routing_decision=decision)
```

### DOMESTIC System

```python
# In hybrid_pdf_integration.py (new file)
from hybrid_integration import HybridPDFRouter, create_adapter

router = HybridPDFRouter()
adapter = create_adapter("domestic_to_ir")

# Parse DN
decision = router.decide_route(dn_path)
# ... parse with chosen engine ...
unified_doc = adapter.convert(parsed_data, routing_decision=decision)
```

## Configuration

### Routing Rules (`routing_rules_hvdc.json`)

Key configuration options:

```json
{
  "version": "1.0-hvdc",
  "default_engine": "docling",
  "daily_ade_budget_usd": 50.0,
  "sensitivity_force_local": [
    "contract", "passport", "price-sensitive", "portal-fee"
  ],
  "performance_targets": {
    "max_latency_ms": 10000,
    "min_success_rate": 0.95,
    "min_confidence": 0.90
  }
}
```

### Schema Configuration (`unified_ir_schema_hvdc.yaml`)

Extends original Unified IR with HVDC fields. See file for complete specification.

## Error Handling

### Validation Errors

```python
validator = SchemaValidator()
is_valid, errors = validator.validate(document)

if not is_valid:
    for error in errors:
        # Handle specific errors
        if "confidence" in error:
            # Low confidence handling
        elif "missing" in error:
            # Missing field handling
```

### Engine Failures

Automatic fallback is configured in routing rules:

```json
{
  "name": "engine_fallback_ade_to_docling",
  "priority": 200,
  "when": {"engine_failed": true, "failed_engine": "ade"},
  "action": {"engine": "docling", "reason": "ADE failed - fallback"}
}
```

## Testing

### Unit Tests

```bash
# Test router
python hybrid_pdf_router.py

# Test adapters
python data_adapters.py

# Test validator
python schema_validator.py
```

### Integration Tests

```python
# Test complete workflow
from hybrid_integration import *

router = HybridPDFRouter()
adapter = create_adapter("shpt_to_ir")
validator = SchemaValidator()

# Route
decision = router.decide_route("/test/file.pdf")

# Parse (mock)
parsed_data = {...}

# Convert
unified_doc = adapter.convert(parsed_data, routing_decision=decision)

# Validate
is_valid, errors = validator.validate(unified_doc)

assert is_valid, f"Validation failed: {errors}"
```

## Troubleshooting

### Common Issues

**Issue**: "Routing rules file not found"
```python
# Solution: Specify explicit path
router = HybridPDFRouter(config_path="/path/to/routing_rules_hvdc.json")
```

**Issue**: "Budget exceeded unexpectedly"
```python
# Check budget status
budget = router.get_budget_status()
print(f"Used: ${budget['used_usd']} on {budget['date']}")

# Reset manually if needed (for testing)
router.budget_used = 0.0
```

**Issue**: "Validation errors for Gate readiness"
```python
# Check specific errors
gate_ready, errors = validator.validate_for_gate(document)
for error in errors:
    print(f"Gate Error: {error}")
```

## API Reference

See individual module docstrings for detailed API documentation:

- `HybridPDFRouter`: Routing engine
- `create_adapter()`: Adapter factory
- `SchemaValidator`: Document validator

## Version History

### v1.0.0 (2025-10-14)
- Initial release
- Hybrid routing engine
- Data adapters for SHPT/DOMESTIC
- Schema validation
- Budget tracking
- HVDC-specific rules and schema

## Contributing

When adding new features:

1. Update routing rules in `routing_rules_hvdc.json`
2. Extend schema in `unified_ir_schema_hvdc.yaml`
3. Add corresponding adapter logic
4. Update validation rules
5. Add tests
6. Update this README

## License

Internal use - HVDC Project only

## Support

For issues or questions:
- Check `INTEGRATION_DESIGN.md` for architectural details
- Review test modules for usage examples
- Contact HVDC Logistics AI Team

---

**Last Updated**: 2025-10-14
**Status**: ✅ Production Ready

