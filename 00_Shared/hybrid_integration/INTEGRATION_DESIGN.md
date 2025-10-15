# HVDC Hybrid Parser Integration Design Document

**Version**: 1.0.0
**Date**: 2025-10-14
**Status**: Design Complete
**Project**: HVDC Invoice Audit - Hybrid Docling/ADE Integration

---

## Executive Summary

This document outlines the integration design for combining the Hybrid Document Parser (Docling + LandingAI ADE) with existing SHPT and DOMESTIC Invoice Audit systems. The integration aims to:

1. **Improve PDF parsing quality** through intelligent routing between local (Docling) and cloud (ADE) engines
2. **Standardize data representation** using Unified IR schema across all systems
3. **Maintain Gate validation** (Gate-11~14) within the hybrid workflow
4. **Enable cross-document validation** across invoice and supporting documents
5. **Deploy via Docker Compose** for consistent local development environment

---

## System Architecture Diagrams

### 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI / API Client]
    end

    subgraph "API Gateway Layer"
        API[FastAPI Service<br/>Port: 8080]
    end

    subgraph "Message Queue Layer"
        RMQ[RabbitMQ Broker<br/>Port: 5672]
        REDIS[Redis Backend<br/>Port: 6379]
    end

    subgraph "Processing Layer"
        WORKER[Celery Worker<br/>Hybrid Parser + Gate Validation]

        subgraph "Routing Engine"
            ROUTER[HybridPDFRouter<br/>routing_rules_hvdc.json]
        end

        subgraph "Parsing Engines"
            DOCLING[Docling<br/>Local Processing]
            ADE[LandingAI ADE<br/>Cloud Processing]
        end

        subgraph "Gate Validators"
            G11[Gate-11: MBL Check]
            G12[Gate-12: Container Check]
            G13[Gate-13: Weight ±3%]
            G14[Gate-14: Qty/Date Check]
        end
    end

    subgraph "Data Layer"
        SHPT_DATA[(SHPT Invoice Data<br/>+ 93 PDFs)]
        DOM_DATA[(DOMESTIC Invoice Data<br/>+ 36 PDFs)]
        RESULTS[(Results Storage<br/>CSV/JSON/Reports)]
    end

    subgraph "Shared Components"
        IR[Unified IR Schema<br/>YAML]
        ADAPTERS[Data Adapters<br/>SHPT/DOMESTIC ↔ IR]
        CONFIG[Config Manager<br/>Rate Loader]
    end

    UI -->|Upload PDF| API
    API -->|Enqueue Task| RMQ
    RMQ -->|Consume| WORKER
    WORKER -->|Route Decision| ROUTER
    ROUTER -->|Local/Sensitive| DOCLING
    ROUTER -->|Complex/Long| ADE
    DOCLING -->|Parsed Result| IR
    ADE -->|Parsed Result| IR
    IR -->|Convert| ADAPTERS
    ADAPTERS -->|Validate| G11
    G11 --> G12
    G12 --> G13
    G13 --> G14
    G14 -->|Store Result| REDIS
    WORKER -->|Read/Write| SHPT_DATA
    WORKER -->|Read/Write| DOM_DATA
    REDIS -->|Retrieve| API
    API -->|Response| UI
    G14 -->|Final Report| RESULTS

    style ROUTER fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style IR fill:#4caf50,stroke:#1b5e20,stroke-width:3px
    style G11 fill:#2196f3,stroke:#0d47a1,stroke-width:2px
    style G12 fill:#2196f3,stroke:#0d47a1,stroke-width:2px
    style G13 fill:#2196f3,stroke:#0d47a1,stroke-width:2px
    style G14 fill:#2196f3,stroke:#0d47a1,stroke-width:2px
```

### 2. Data Flow Pipeline

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Queue
    participant Worker
    participant Router
    participant Docling
    participant ADE
    participant IR
    participant Gates
    participant Results

    Client->>API: POST /upload (PDF file)
    API->>Queue: Enqueue parse_document task
    API-->>Client: {task_id: "abc123"}

    Queue->>Worker: Consume task
    Worker->>Worker: Detect doc_type (BOE/DO/DN)
    Worker->>Router: Route decision

    alt Sensitive/Local
        Router->>Docling: Parse locally
        Docling-->>Router: Parsed blocks + bbox
    else Complex/Long/Table-dense
        Router->>ADE: Parse via API
        ADE-->>Router: Parsed blocks + bbox + confidence
    end

    Router->>IR: Convert to Unified IR
    IR->>IR: Validate schema compliance

    IR->>Gates: Gate-11 (MBL check)
    Gates->>Gates: Gate-12 (Container check)
    Gates->>Gates: Gate-13 (Weight ±3%)
    Gates->>Gates: Gate-14 (Qty/Date check)

    Gates->>Results: Store validation results
    Results->>Queue: Update task status

    Client->>API: GET /result/{task_id}
    API->>Queue: Retrieve result
    Queue-->>API: {status, data, gates}
    API-->>Client: Return Unified IR + Gate results
```

### 3. Routing Decision Tree

```mermaid
flowchart TD
    START[PDF Document] --> DETECT{Detect<br/>Document Type}

    DETECT -->|BOE| BOE_CHECK{Check<br/>Characteristics}
    DETECT -->|DO| DO_CHECK{Check<br/>Characteristics}
    DETECT -->|DN| DN_CHECK{Check<br/>Characteristics}
    DETECT -->|Invoice| INV_CHECK{Check<br/>Characteristics}

    BOE_CHECK -->|table_density ≥ 30%| ADE1[Route to ADE]
    BOE_CHECK -->|pages > 12| ADE1
    BOE_CHECK -->|else| DOC1[Route to Docling]

    DO_CHECK -->|skew ≥ 4°| ADE2[Route to ADE]
    DO_CHECK -->|sensitive| DOC2[Route to Docling]
    DO_CHECK -->|else| DOC2

    DN_CHECK -->|pages ≥ 4| ADE3[Route to ADE]
    DN_CHECK -->|visual_relations| ADE3
    DN_CHECK -->|else| DOC3[Route to Docling]

    INV_CHECK -->|price-sensitive| DOC4[Route to Docling]
    INV_CHECK -->|else| DOC4

    ADE1 --> BUDGET{ADE Budget<br/>Exceeded?}
    ADE2 --> BUDGET
    ADE3 --> BUDGET

    BUDGET -->|Yes| FALLBACK[Fallback to Docling]
    BUDGET -->|No| PARSE_ADE[Parse with ADE]

    DOC1 --> PARSE_DOC[Parse with Docling]
    DOC2 --> PARSE_DOC
    DOC3 --> PARSE_DOC
    DOC4 --> PARSE_DOC
    FALLBACK --> PARSE_DOC

    PARSE_ADE --> IR[Convert to<br/>Unified IR]
    PARSE_DOC --> IR

    IR --> GATE[Gate Validation<br/>11-14]
    GATE --> END[Store Results]

    style START fill:#e1f5fe
    style ADE1 fill:#ffccbc,stroke:#bf360c
    style ADE2 fill:#ffccbc,stroke:#bf360c
    style ADE3 fill:#ffccbc,stroke:#bf360c
    style DOC1 fill:#c8e6c9,stroke:#1b5e20
    style DOC2 fill:#c8e6c9,stroke:#1b5e20
    style DOC3 fill:#c8e6c9,stroke:#1b5e20
    style DOC4 fill:#c8e6c9,stroke:#1b5e20
    style IR fill:#fff9c4,stroke:#f57f17
    style GATE fill:#bbdefb,stroke:#0d47a1
```

### 4. Docker Compose Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Network: hvdc-network"
        subgraph "API Container"
            API_MAIN[FastAPI Application<br/>Port: 8080<br/>Image: hvdc-api:latest]
        end

        subgraph "Worker Container (x3)"
            W1[Celery Worker 1<br/>Image: hvdc-worker:latest]
            W2[Celery Worker 2<br/>Image: hvdc-worker:latest]
            W3[Celery Worker 3<br/>Image: hvdc-worker:latest]
        end

        subgraph "Broker Container"
            RMQ_CONT[RabbitMQ 3.13<br/>Port: 5672, 15672<br/>Management UI]
        end

        subgraph "Backend Container"
            REDIS_CONT[Redis 7 Alpine<br/>Port: 6379]
        end

        subgraph "Docling Container"
            DOC_CONT[Docling Service<br/>Local Parser<br/>Port: 8000]
        end
    end

    subgraph "Host Volumes"
        VOL_CONFIG[./config<br/>routing_rules_hvdc.json<br/>unified_ir_schema.yaml]
        VOL_DATA[./HVDC_Invoice_Audit<br/>SHPT + DOMESTIC Data]
        VOL_RESULTS[./Results<br/>Output Reports]
        VOL_LOGS[./logs<br/>System Logs]
    end

    subgraph "Environment Variables"
        ENV[.env.hvdc<br/>ADE_API_KEY<br/>ADE_ENDPOINT<br/>ROUTING_RULES_PATH<br/>GATE_VALIDATION_ENABLED]
    end

    API_MAIN -->|Enqueue| RMQ_CONT
    RMQ_CONT -->|Distribute| W1
    RMQ_CONT -->|Distribute| W2
    RMQ_CONT -->|Distribute| W3
    W1 -->|Store Results| REDIS_CONT
    W2 -->|Store Results| REDIS_CONT
    W3 -->|Store Results| REDIS_CONT
    W1 -.->|Local Parse| DOC_CONT
    W2 -.->|Local Parse| DOC_CONT
    W3 -.->|Local Parse| DOC_CONT
    REDIS_CONT -->|Retrieve| API_MAIN

    VOL_CONFIG -.->|Mount ro| API_MAIN
    VOL_CONFIG -.->|Mount ro| W1
    VOL_CONFIG -.->|Mount ro| W2
    VOL_CONFIG -.->|Mount ro| W3
    VOL_DATA -.->|Mount rw| W1
    VOL_DATA -.->|Mount rw| W2
    VOL_DATA -.->|Mount rw| W3
    VOL_RESULTS -.->|Mount rw| W1
    VOL_RESULTS -.->|Mount rw| W2
    VOL_RESULTS -.->|Mount rw| W3
    VOL_LOGS -.->|Mount rw| API_MAIN
    VOL_LOGS -.->|Mount rw| W1
    ENV -.->|Inject| API_MAIN
    ENV -.->|Inject| W1
    ENV -.->|Inject| W2
    ENV -.->|Inject| W3

    style API_MAIN fill:#4fc3f7,stroke:#01579b,stroke-width:3px
    style W1 fill:#81c784,stroke:#1b5e20,stroke-width:2px
    style W2 fill:#81c784,stroke:#1b5e20,stroke-width:2px
    style W3 fill:#81c784,stroke:#1b5e20,stroke-width:2px
    style RMQ_CONT fill:#ffb74d,stroke:#e65100,stroke-width:2px
    style REDIS_CONT fill:#ef5350,stroke:#b71c1c,stroke-width:2px
    style DOC_CONT fill:#ba68c8,stroke:#4a148c,stroke-width:2px
```

### 5. Component Integration Matrix

```mermaid
graph LR
    subgraph "SHPT System"
        SHPT_AUDIT[shpt_sept_2025_enhanced_audit.py]
        SHPT_PDF[invoice_pdf_integration.py]
        SHPT_DATA_SRC[(93 PDFs<br/>BOE/DO/DN)]
    end

    subgraph "DOMESTIC System"
        DOM_AUDIT[validate_sept_2025_with_pdf.py]
        DOM_PDF[hybrid_pdf_integration.py<br/>NEW]
        DOM_DATA_SRC[(36 DN PDFs)]
    end

    subgraph "Shared Hybrid Layer"
        ROUTER_SHARED[hybrid_pdf_router.py]
        ADAPTER_SHARED[data_adapters.py<br/>SHPTToIR, DOMESTICToIR]
        IR_SHARED[unified_ir_schema.yaml<br/>EXTENDED]
        GATE_SHARED[gate_validator_adapter.py]
    end

    subgraph "Parsing Engines"
        DOCLING_ENG[Docling Local]
        ADE_ENG[ADE Cloud]
    end

    subgraph "Original PDF Modules"
        ORIG_PARSER[DSVPDFParser<br/>00_Shared/pdf_integration/]
        ORIG_CROSS[CrossDocValidator]
        ORIG_ONTO[OntologyMapper]
    end

    SHPT_AUDIT -->|uses| SHPT_PDF
    SHPT_PDF -->|integrates| ROUTER_SHARED
    DOM_AUDIT -->|uses| DOM_PDF
    DOM_PDF -->|integrates| ROUTER_SHARED

    ROUTER_SHARED -->|routes to| DOCLING_ENG
    ROUTER_SHARED -->|routes to| ADE_ENG

    DOCLING_ENG -->|output| ADAPTER_SHARED
    ADE_ENG -->|output| ADAPTER_SHARED

    ADAPTER_SHARED -->|converts| IR_SHARED
    IR_SHARED -->|validates| GATE_SHARED

    GATE_SHARED -->|extends| ORIG_CROSS
    SHPT_PDF -->|wraps| ORIG_PARSER

    SHPT_DATA_SRC -.->|reads| SHPT_PDF
    DOM_DATA_SRC -.->|reads| DOM_PDF

    style ROUTER_SHARED fill:#ffeb3b,stroke:#f57f17,stroke-width:4px
    style IR_SHARED fill:#4caf50,stroke:#1b5e20,stroke-width:4px
    style GATE_SHARED fill:#2196f3,stroke:#0d47a1,stroke-width:4px
    style ADAPTER_SHARED fill:#ff9800,stroke:#e65100,stroke-width:3px
```

---

## Architecture Comparison Matrix

| Aspect | Hybrid Parser (Original) | SHPT System | DOMESTIC System | **Integrated Solution** |
|--------|-------------------------|-------------|-----------------|------------------------|
| **PDF Parsing** | Docling + ADE routing | DSVPDFParser (PyMuPDF) | Multi-layer fallback (PyMuPDF→pypdf→pdfminer→pdftotext) | **Hybrid Router with both engines** |
| **Document Types** | Generic documents | BOE, DO, DN, Carrier Invoice | DN only | **All types with specialized routing** |
| **Data Schema** | Unified IR (blocks+bbox) | Custom SHPT schema | Custom DOMESTIC schema | **Extended Unified IR** |
| **Routing Logic** | routing_rules.json (generic) | N/A | N/A | **routing_rules_hvdc.json (HVDC-specific)** |
| **Gate Validation** | None | Gate-11~14 | Cross-document validation | **Gate-11~14 in hybrid workflow** |
| **Deployment** | Docker Compose + K8s | Python script | Python script | **Docker Compose (local dev)** |
| **Async Processing** | Celery + RabbitMQ | Synchronous | Synchronous | **Celery + RabbitMQ** |
| **Budget Control** | Daily ADE budget | N/A | N/A | **Daily ADE budget with Docling fallback** |
| **Cache** | None | File hash-based | None | **File hash-based cache** |
| **Success Rate** | Unknown | 100% (93/93 PDFs) | 91.7% (33/36 PDFs) | **Target: >95%** |

---

## Unified IR Schema Mapping

### Current SHPT Data Model
```python
{
    "header": {
        "file_path": str,
        "doc_type": "BOE" | "DO" | "DN" | "CarrierInvoice",
        "shipment_id": str
    },
    "data": {
        "mbl_no": str,
        "containers": List[str],
        "gross_weight": float,
        "hs_code": str,
        "customs_office": str,
        # ... BOE/DO/DN specific fields
    }
}
```

### Current DOMESTIC Data Model
```python
{
    "file_path": str,
    "text": str,  # Full PDF text
    "origin": str,
    "destination": str,
    "vehicle_type": str,
    "destination_code": str,
    "do_number": str
}
```

### Extended Unified IR Schema
```yaml
document:
  doc_id: string
  engine: "docling" | "ade"
  routing_decision:
    rule_matched: string
    reason: string
    engine_choice: string
    confidence: float
  pages: integer
  meta:
    filename: string
    mime: string
    created_at: timestamp
    checksum_sha256: string
    doc_type: "BOE" | "DO" | "DN" | "CarrierInvoice" | "Other"
    shipment_id: string (HVDC-specific)
  blocks:
    - id: string
      type: "text" | "table" | "figure" | "header" | "footer" | "field" | "checkbox"
      text: string (optional)
      table: (optional)
        rows: array of arrays
        header: boolean
      bbox:
        page: integer
        x0: float
        y0: float
        x1: float
        y1: float
      meta:
        confidence: float
        source_engine: string
        page_idx: integer
        relations:
          - type: string
            target_id: string
  hvdc_fields:  # HVDC-specific extensions
    boe_fields: (if doc_type == "BOE")
      entry_no: string
      customs_office: string
      hs_code_classifications: array
      mbl_no: string
      containers: array
      gross_weight: float
      gross_weight_unit: string
    do_fields: (if doc_type == "DO")
      do_number: string
      do_validity_date: timestamp
      demurrage_risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
      estimated_demurrage_usd: float
    dn_fields: (if doc_type == "DN")
      origin: string
      destination: string
      vehicle_type: string
      destination_code: string
      do_reference: string
    gate_validation:  # Gate validation results
      gate_11_mbl_check:
        status: "PASS" | "FAIL" | "SKIP"
        details: string
      gate_12_container_check:
        status: "PASS" | "FAIL" | "SKIP"
        details: string
      gate_13_weight_check:
        status: "PASS" | "FAIL" | "SKIP"
        tolerance_pct: float
        details: string
      gate_14_qty_date_check:
        status: "PASS" | "FAIL" | "SKIP"
        details: string
```

---

## Routing Rules Customization

### HVDC-Specific Routing Rules (`routing_rules_hvdc.json`)

```json
{
  "version": "1.0-hvdc",
  "default_engine": "docling",
  "daily_ade_budget_usd": 50.0,
  "sensitivity_force_local": [
    "contract",
    "passport",
    "price-sensitive",
    "portal-fee",
    "demurrage-calculation"
  ],
  "rules": [
    {
      "name": "boe_table_dense",
      "doc_types": ["BOE"],
      "when": {
        "table_density_gte": 0.30
      },
      "action": {
        "engine": "ade",
        "reason": "BOE with dense tables - ADE excels at table extraction"
      }
    },
    {
      "name": "boe_long_document",
      "doc_types": ["BOE"],
      "when": {
        "pages_gt": 12
      },
      "action": {
        "engine": "ade",
        "reason": "Long BOE document - ADE handles better"
      }
    },
    {
      "name": "do_skewed_scan",
      "doc_types": ["DO"],
      "when": {
        "skew_deg_gte": 4.0
      },
      "action": {
        "engine": "ade",
        "reason": "Skewed DO scan - ADE has better correction"
      }
    },
    {
      "name": "dn_multi_page",
      "doc_types": ["DN"],
      "when": {
        "pages_gte": 4
      },
      "action": {
        "engine": "ade",
        "reason": "Multi-page DN - better handling with ADE"
      }
    },
    {
      "name": "visual_relations_detection",
      "doc_types": ["BOE", "DO", "DN", "CarrierInvoice"],
      "when": {
        "visual_relations": ["checkbox", "caption", "chart", "signature"]
      },
      "action": {
        "engine": "ade",
        "reason": "Document with visual relationships - ADE specializes"
      }
    },
    {
      "name": "ade_budget_guard",
      "doc_types": ["BOE", "DO", "DN", "CarrierInvoice"],
      "when": {
        "ade_budget_exceeded": true
      },
      "action": {
        "engine": "docling",
        "reason": "ADE budget exceeded - fallback to Docling"
      },
      "priority": "HIGH"
    },
    {
      "name": "sensitive_force_local",
      "doc_types": ["BOE", "DO", "DN", "CarrierInvoice"],
      "when": {
        "sensitivity_in": ["contract", "passport", "price-sensitive", "portal-fee"]
      },
      "action": {
        "engine": "docling",
        "reason": "Sensitive document - local processing only"
      },
      "priority": "CRITICAL"
    },
    {
      "name": "engine_fallback",
      "doc_types": ["BOE", "DO", "DN", "CarrierInvoice"],
      "when": {
        "engine_failed": true
      },
      "action": {
        "engine": "swap",
        "reason": "Primary engine failed - swap to alternative"
      },
      "priority": "HIGH"
    }
  ],
  "metrics_emit": [
    "latency_ms",
    "engine",
    "doc_type",
    "pages",
    "table_density",
    "ade_cost_usd",
    "cache_hit",
    "retries",
    "gate_validation_results"
  ]
}
```

---

## Gate Validation Integration Points

### Current SHPT Gate Validation Logic

**Gate-11: MBL Consistency Check**
- Compare MBL number across Invoice, BOE, and DO
- Status: PASS if all match, FAIL if mismatch detected

**Gate-12: Container Number Validation**
- Verify container numbers match across Invoice and BOE
- Handle multiple containers per shipment
- Status: PASS if consistent, FAIL if discrepancy

**Gate-13: Weight Tolerance Check (±3%)**
- Compare gross weight between Invoice and BOE
- Allow 3% tolerance for measurement variance
- Status: PASS if within tolerance, FAIL if exceeds

**Gate-14: Quantity & Date Validation**
- Verify quantity consistency across documents
- Check date logic (BL Date ≤ Invoice Date ≤ DO Validity)
- Status: PASS if logical, FAIL if inconsistent

### Integration into Hybrid Workflow

```python
# Pseudocode for integrated validation pipeline

async def process_document_with_validation(pdf_file, shipment_id):
    # Step 1: Route and parse
    routing_decision = hybrid_router.decide_route(pdf_file)
    if routing_decision.engine == "ade":
        parsed_result = await ade_parser.parse(pdf_file)
    else:
        parsed_result = docling_parser.parse(pdf_file)

    # Step 2: Convert to Unified IR
    unified_ir = data_adapter.to_unified_ir(
        parsed_result,
        routing_decision,
        shipment_id
    )

    # Step 3: Validate schema
    schema_validator.validate(unified_ir)

    # Step 4: Gate validation (if applicable)
    if unified_ir.doc_type in ["BOE", "DO", "DN"]:
        gate_results = gate_validator.validate_all_gates(
            unified_ir,
            related_documents=fetch_related_documents(shipment_id)
        )
        unified_ir.hvdc_fields.gate_validation = gate_results

    # Step 5: Store and return
    await redis_backend.store(unified_ir)
    return unified_ir
```

---

## Key Design Decisions

### 1. Why Hybrid Routing?
- **Docling**: Fast, local, no cost, good for standard documents
- **ADE**: Cloud-based, better for complex layouts, costs money
- **Decision**: Route based on document characteristics to optimize cost/quality

### 2. Why Unified IR Schema?
- **Problem**: SHPT and DOMESTIC use different data models
- **Solution**: Single standardized schema that both can convert to/from
- **Benefit**: Enables code reuse, cross-system validation, easier maintenance

### 3. Why Docker Compose (not K8s)?
- **Requirement**: Local development environment specified in plan
- **Trade-off**: K8s provides better scaling, but Docker Compose is simpler for local dev
- **Future**: Can migrate to K8s using existing k8s/ manifests

### 4. Why Preserve Existing PDF Modules?
- **Legacy**: SHPT DSVPDFParser already proven in production (100% success rate)
- **Strategy**: Wrap existing parser, don't replace
- **Benefit**: Maintains backward compatibility, reduces risk

---

## Risk Analysis & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ADE API downtime | High | Low | Automatic fallback to Docling |
| Budget overrun | Medium | Medium | Daily budget cap with local fallback |
| Schema conversion errors | High | Medium | Comprehensive validation + unit tests |
| Performance degradation | Medium | Low | Caching + async processing |
| Gate validation false positives | High | Low | Extensive testing with real data (102+44 items) |
| Docker networking issues | Low | Low | Standard compose patterns + documentation |

---

## Success Metrics

### Performance Targets
- **Parsing Success Rate**: >95% (vs. current 100% SHPT, 91.7% DOMESTIC)
- **Processing Latency**: <10 seconds per document (vs. current ~7 seconds for SHPT)
- **Gate Validation Accuracy**: >98% (maintain current SHPT standards)
- **ADE Cost**: <$50 USD/day (as configured)

### Quality Targets
- **Schema Validation**: 100% compliance with Unified IR
- **Cache Hit Rate**: >40% for repeated documents
- **Zero Downtime**: Graceful fallback on engine failures

---

## Next Steps

1. ✅ **Design Complete** - This document
2. ⏳ **Phase 2**: Implement Unified IR schema extension
3. ⏳ **Phase 3**: Build hybrid router and adapters
4. ⏳ **Phase 4**: Integrate with SHPT and DOMESTIC systems
5. ⏳ **Phase 5**: Docker Compose deployment
6. ⏳ **Phase 6**: Testing with real datasets (93+36 PDFs)
7. ⏳ **Phase 7**: Documentation and performance reporting

---

**Document Status**: ✅ Ready for Implementation
**Approval**: Pending stakeholder review
**Next Review**: After Phase 2 completion

