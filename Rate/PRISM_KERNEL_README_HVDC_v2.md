# PRISM.KERNEL.v1 — README (Cycle Template Standard)

## 📌 Background & Purpose
Modern LLM workflows often drift: outputs lose structure, rules break under recursion.  
**PRISM.KERNEL.v1** is a *law-first kernel seed* that enforces:
- **Invariant shape**: recap.card always 5 lines (P→R→I→S→M)
- **Proof artifact**: JSON with deterministic hash for audit & automation
- **Dual usability**: human-readable summary + machine-readable artifact

Think of it as the **BIOS for meaning** — it locks archetypes and prevents collapse.

---

## 🚀 Quickstart (3 Steps)
1. Copy the SEED block into your prompt (system/instruction).  
2. In user/task message, provide **I::** bindings (sources, roles, context).  
3. Ask explicitly: *"Return recap.card (5 lines) + proof.artifact (JSON)"*.

---

## 🔧 SEED Block
```
▛///▞ PRISM :: KERNEL ▞▞//▟
P:: define.actions · map.tasks · establish.goal
R:: enforce.laws · prevent.drift · validate.steps
I:: bind.inputs{sources · roles · context}
S:: sequence.flow{plan → check → persist → advance}
M:: project.outputs{artifacts · reports · states}

Support:
- invariant.shape: 5 lines only
- order.lock: P → R → I → S → M
- return both: recap.card (5 lines) + proof.artifact (JSON)
:: ∎
```

---

## 📝 Example (Invoice Audit)

**Input**
```
Task: Invoice audit cycle
I:: {sources:['OFCO.Invoice#98256059','Draft.Invoice#HLS/INV/25/0528','cost_table.v2.5'],
     roles:['auditor','validator'],
     context:{project:'HVDC-Lightning'}}
Return recap.card (5 lines) + proof.artifact(JSON).
```

**Output (recap.card)**
```
P:: invoice-audit · cost-validate · report-generate
R:: Incoterms2020 · COST-GUARD Δ≤5% · HallucinationBan
I:: {sources:['OFCO.Invoice#98256059','Draft.Invoice#HLS/INV/25/0528','cost_table.v2.5'], roles:['auditor','validator'], context:{project:'HVDC-Lightning'}}
S:: plan→check→persist→advance
M:: {risk.table, KPI, status}
```

---

## 📦 HVDC Samsung C&T Workflows — Applied Examples

### 1) Invoice Audit (OFCO · DSV · AD Ports · Others)
**Input**
```
Task: Invoice audit cycle
I:: {sources:['OFCO.Invoice','DSV.Invoice','ADPorts.Invoice','Other.Charges'],
     roles:['auditor','validator'],
     context:{project:'HVDC'}}
```

**proof.artifact excerpt**
```json
{
  "artifact_id": "InvoiceAudit-20251002-001",
  "outputs_emitted": {
    "risk.table": [
      {"vendor":"OFCO","delta_pct":2.10,"risk":"PASS"},
      {"vendor":"DSV","delta_pct":6.75,"risk":"HIGH"},
      {"vendor":"ADPorts","delta_pct":4.50,"risk":"WARN"}
    ],
    "status": "FAIL"
  }
}
```

---

### 2) CIPL·BL Pre-Arrival Guard (UAE Customs)
**Task**
Pre-arrival CIPL/BL audit & HS-permit match for UAE customs.

**Input**
```
Task: Pre-arrival CIPL/BL Guard
I:: {sources:['CIPL.PreArrival','BL.PreArrival','HS.Dict'],
     roles:['customs.agent','auditor'],
     context:{project:'HVDC','regulators':['FANR','MOIAT']}}
```

**proof.artifact excerpt**
```json
{
  "artifact_id": "PreArrival-202510",
  "outputs_emitted": {
    "CIPL.BL.match": true,
    "HS.codes": ["8544601000"],
    "permits_required": ["FANR","MOIAT"],
    "status": "BLOCK"
  }
}
```

---

### 3) Warehouse Ops (DSV Indoor, DSV Outdoor, M44, Al Markaz, Hauler)
**Input**
```
Task: Warehouse forecast cycle
I:: {sources:['WMS.DSV.Indoor','WMS.DSV.Outdoor','WMS.M44','WMS.AlMarkaz','Hauler.Logs'],
     roles:['planner','auditor'],
     context:{project:'HVDC','horizon':'12m'}}
```

**recap.card**
```
P:: forecast · optimize · reduce.contract
R:: occupancy≤85% · dwell≤30d · DEM/DET≤10%
I:: {sources:['WMS.DSV.Indoor','WMS.DSV.Outdoor','WMS.M44','WMS.AlMarkaz','Hauler.Logs'], roles:['planner','auditor'], context:{project:'HVDC','horizon':'12m'}}
S:: plan→forecast→persist→adjust
M:: {WH.utilization, KPI, status}
```

---

### 4) Stowage Simulation (LCT JPTW-71, DAS/AGI)
**Input**
```
Task: Stowage plan validation
I:: {sources:['CIPL#DAS-0057','DeckMap#JPTW71','StabilityCalc.v3'],
     roles:['nav.arch','logistics'],
     context:{voyage:61,project:'HVDC'}}
```

**proof.artifact excerpt**
```json
{
  "artifact_id": "Stowage-61",
  "outputs_emitted": {
    "deck_area_util_pct": 82.40,
    "VCG_m": 3.25,
    "COG_offset_m": 0.45,
    "status": "PASS"
  }
}
```

---

## 🛡️ Fail-Safe Rules
- If inputs missing: recap.card still 5 lines, proof.artifact.status="ZERO".  
- Artifact must list **requested fields** under `missing`.  

---

## ⚙️ Integration Tips
- **Python**: Parse proof.artifact JSON → validate sha256 hash → push to BI/DB.  
- **RPA/Sheets**: Pipe recap.card into dashboards, proof.artifact into backend.  
- **Audits**: Use proof_hash to ensure determinism & reproducibility.  

---

## ✅ Benefits
1. **Stable format** → no drift, predictable 5-line recap.  
2. **Audit trail** → every cycle has hash-bound JSON.  
3. **Dual mode** → human + machine outputs in one.  
4. **Scalable** → works across invoices, customs, warehouse, stowage.  

---

_End of README — PRISM.KERNEL.v1 HVDC Samsung C&T Standard_
