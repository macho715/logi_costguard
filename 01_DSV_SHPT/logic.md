# ExecSummary

* 목표: **청구서 라인별 단가·수량·통화·증빙**을 계약/AT-COST/레퍼런스 요율로 교차검증하고 Δ%를 **COST-GUARD 밴드**로 판정(PASS/WARN/HIGH/CRITICAL).
* 기준 데이터: 카테고리별 참조요율(항공/컨테이너/벌크), 고정환율 **1 USD=3.6725 AED**, 계약 허용오차 **±3%**, Auto-Fail **>15%**.
* 조인 키: **Category+Port+Destination+Unit** + O/D Canonical 매핑(ApprovedLaneMap·NormalizationMap) → 레인 중앙값/표준요율을 ref로 사용.
* 판정 규칙: **Δ≤2% PASS / ≤5% WARN / ≤10% HIGH / >10% CRITICAL**(COST-GUARD), 증빙 불충분/단위불일치/통화불일치 시 별도 플래그.

---

## Data Flow (End-to-End)

### Legacy Mode
```
Excel Invoice → masterdata_validator.py
                    ↓ (USE_HYBRID=false)
                    ↓ validate_all() [line 832-867]
                    ↓ validate_row() [line 668-754]
                    ↓ classify_charge_group()
                    ↓ find_contract_ref_rate() [line 226-350]
                    ↓   → config_manager.get_rate()
                    ↓   → normalizer.normalize()
                    ↓ calculate_delta_percent() [line 542-550]
                    ↓ get_cost_guard_band() [line 552-568]
                    ↓ calculate_gate_score() [line 570-620]
                    ↓ (Legacy PDF Integration)
                    ↓ pdf_integration.extract_line_item()
                    ↓
CSV/Excel Output
```

### Hybrid Mode
```
Excel Invoice → masterdata_validator.py
                    ↓ (USE_HYBRID=true)
                    ↓ validate_all() [line 832-867]
                    ↓ validate_row() [line 668-754]
                    ↓ classify_charge_group()
                    ↓ _extract_pdf_line_item() [line 350-450]
                    ↓   → hybrid_client.parse_pdf(pdf_path)
                    ↓   → FastAPI (:8080) → Celery Worker
                    ↓   → pdfplumber (coordinate extraction)
                    ↓   → 3-Stage Fallback:
                    ↓     - Priority 1: Regex patterns
                    ↓     - Priority 2: Coordinate-based (x: 200-600px, y: ±10px)
                    ↓     - Priority 3: Table-based (TOTAL keyword)
                    ↓   → Unified IR
                    ↓   → ir_adapter.extract_invoice_line_item()
                    ↓   → AED → USD conversion (/3.6725)
                    ↓ calculate_delta_percent() [line 542-550]
                    ↓ get_cost_guard_band() [line 552-568]
                    ↓ calculate_gate_score() [line 570-620]
                    ↓
CSV/Excel Output (with PDF data)
```

### System Components
- **FastAPI Server** (`:8080`): PDF upload/status endpoints
- **Celery Worker**: Async PDF parsing with pdfplumber
- **Redis Broker**: Task queue management
- **UnifiedIRAdapter**: IR → HVDC data transformation
- **HybridDocClient**: API client for PDF parsing requests
- **ConfigManager**: Rate lookup and configuration management
- **CategoryNormalizer**: Description normalization and fuzzy matching

---

## Core Logic (라인 단위 알고리즘)

1. **문서 흡수 · 분류**

   * PDF/엑셀/스캔 → 페이지 타입 감지(인보이스/DO/BOE/Port/Carrier).
   * 파일 메타+해시 저장(감사 추적).

2. **OCR/Parse → 정규화(Normalizer)**

   * 숫자/통화/단위 강제 2-dec, 통화는 원화 금지·USD/AED만 허용(고정환율 적용).
   * 지명·장소 **NormalizationMap**으로 Canonical화(예: Mussafah 군집→“DSV Mussafah Yard”, Mirfa→“MIRFA SITE”).

3. **라인 분류(Line Classifier)**

   * `RATE SOURCE == CONTRACT` → 계약/참조표 조인.
   * `RATE SOURCE == AT COST` → 증빙금액(AED) 추출→ **AED÷3.6725** 로 USD 환산(2-dec).

4. **참조요율 조인(4단계 우선순위)**

   ### Stage 1: Fixed Fee Lookup
   ```python
   # config_manager.py:get_fixed_fee_by_keywords()
   fixed_fee = self.config_manager.get_fixed_fee_by_keywords(description, keywords)
   # Examples: "DO FEE", "CUSTOMS CLEARANCE FEE", "PORTAL FEE"
   ```

   ### Stage 2: Lane Map Lookup
   ```python
   # masterdata_validator.py:226-350 (find_contract_ref_rate)
   normalized_desc = self.normalizer.normalize(description)
   lane_rate = self.config_manager.get_inland_transportation_rate(
       origin, destination, normalized_desc
   )
   # Examples: DSV→MIRFA 420, DSV→SHU 600
   ```

   ### Stage 3: Keyword Match
   ```python
   # config_manager.py:keyword_based_lookup()
   if "AIRPORT" in desc and "MOSB" in desc:
       return lane_map["AUH_DSV_MUSSAFAH"]["rate"]
   elif "PORT" in desc and "JEBEL" in desc:
       return lane_map["JEBEL_ALI_DSV"]["rate"]
   ```

   ### Stage 4: Fuzzy Match (Fallback)
   ```python
   # category_normalizer.py:3-stage matching
   from fuzzywuzzy import fuzz

   # Stage 1: Exact Match
   exact_match = synonyms.get(description)
   if exact_match:
       return exact_match

   # Stage 2: Contains Match
   for key, value in synonyms.items():
       if key in description or description in key:
           return value

   # Stage 3: Fuzzy Match
   best_match = max(synonyms.keys(), key=lambda s: fuzz.ratio(desc, s))
   if fuzz.ratio(desc, best_match) >= 60:  # threshold
       return synonyms[best_match]
   ```

   * **허용오차**: ±3% (Contract), ±0.5% (Portal Fee)
   * **Auto-Fail**: >15% (Contract), >5% (Portal Fee)
   * **미스매치**: `REF_MISSING`, `OUTLIER`로 표기

5. **계산 규칙(Calculator)**

   * `LineTotal = Rate × Qty` (수식이 있으면 재계산·반올림 통일 2-dec).
   * `Δ% = (DraftRate − RefRate)/RefRate × 100`.
   * **Auto-Fail:** |Δ%| > **15%** → FAIL. **Tolerance:** |Δ%| ≤ **3%** → 계약 일치.

6. **COST-GUARD 밴딩 & 스코어**

   * 밴드: **PASS/WARN/HIGH/CRITICAL**(2/5/10/>10%), 알림: HIGH↑ TG 핑.
   * O/D 유사도 스코어(원/목 0.35씩 + 차량 0.10 + 거리 0.10 + 요율 0.10, 임계 0.60)로 **대체 레인 제안**.

7. **AT-COST 로직**

   * 증빙(Port/Carrier/공항청구)에서 **AED 원가** 추출 → **USD 환산(÷3.6725)** → 청구표와 일치성 검사. (예: 공항 Appointment 27 AED → 7.35 USD).
   * VAT/세금은 원가에서 제외하고 세금계정 분개(보고서 주석).

8. **Cross-Document Consistency**

   * 수량/컨테이너/중량: DO·BOE·DN·Carrier 인보이스의 ID·수량·CW/CTR 매칭.
   * Port/레인: `ApprovedLaneMap`의 Canonical 목적지로 역추적(레인 오조인 방지).

9. **출력 & 증명(Report + Artifact)**

   * 라인별 표(Δ%, 밴드, 근거문서, 판정로직) + 총계.
   * **PRISM.KERNEL** 방식의 `proof.artifact(JSON)` 생성(해시 포함, 재현성·감사용).

---

## Hybrid Mode Architecture (v4.0+)

### Mode Selection Logic
```python
# masterdata_validator.py:85-100
USE_HYBRID = os.getenv("USE_HYBRID", "false").lower() == "true"

if USE_HYBRID:
    try:
        from hybrid_client import HybridDocClient
        from unified_ir_adapter import UnifiedIRAdapter

        self.hybrid_client = HybridDocClient("http://localhost:8080")
        self.ir_adapter = UnifiedIRAdapter()
        self.pdf_integration = None  # Disable legacy
        logger.info("✅ Hybrid System enabled (Docling + ADE)")
    except Exception as e:
        logger.warning(f"Hybrid System init failed: {e}. Fallback to legacy.")
        self.use_hybrid = False
else:
    # Legacy PDF Integration
    self.pdf_integration = DSVPDFParser(supporting_docs_path)
    logger.info("✅ Legacy PDF Integration enabled")
```

### PDF Parsing Pipeline (Hybrid)
1. **Upload PDF** → FastAPI (:8080) → Celery Worker
2. **3-Stage Fallback Strategy**:
   - **Priority 1**: Regex patterns (기존 로직)
   - **Priority 2**: Coordinate-based extraction (x: 200-600px, y: ±10px)
   - **Priority 3**: Table-based extraction (TOTAL keyword search)
3. **Unified IR Generation** → `UnifiedIRAdapter`
4. **Return**: `{total_amount, currency, line_items[]}`

### AED → USD Auto-Conversion
```python
# unified_ir_adapter.py:_convert_to_usd_if_needed()
if summary['currency'] == 'AED':
    usd_amount = aed_amount / 3.6725  # Fixed FX rate
    return {"amount": usd_amount, "currency": "USD"}
```

### Hybrid System Components
- **FastAPI Server** (`:8080`): PDF upload/status endpoints
- **Celery Worker**: Async PDF parsing with pdfplumber
- **Redis Broker**: Task queue management
- **UnifiedIRAdapter**: IR → HVDC data transformation
- **HybridDocClient**: API client for PDF parsing requests

---

## System Architecture (모듈·데이터·알고리즘)

**A. 서비스 모듈**

* Ingestor(파일워처/업로드)
* OCR/Parser(문자/테이블/수식 추출)
* Normalizer(지명/단위/통화 Canonical)
* **Rate Engine**(항공/컨테이너/벌크 테이블 + Inland Trucking Table v1.1)
* **Lane Mapper**(ApprovedLaneMap/NormalizationMap, 유사도 그래프)
* **Guardrail Engine(COST-GUARD)**(Δ% 밴드·AutoFail·알림)
* Evidence Linker(DO/BOE/Port/Carrier 스냅샷 연결)
* Reporter(표·PDF·Excel) + **PRISM proof.artifact** 출력기

**B. 저장소**

* **RefRates DB**: 항공/컨/벌크 JSON, tolerance/auto-fail/FX 정책 메타 포함.
* **Lane Graph**: ApprovedLaneMap 스냅샷 + 유사도 엣지/버킷.
* **Docs Vault**: 원본 PDF·hash·PII-Mask.
* **Audit Ledger**: proof.artifact 해시 보관(변조 감시).

**C. 핵심 알고리즘(실제 구현 함수 매핑)**

```python
# masterdata_validator.py:832-867
def validate_all(self) -> pd.DataFrame:
    """MasterData 전체 검증 - 메인 진입점"""
    for idx, row in df_master.iterrows():
        validation = self.validate_row(row)  # line 668-754

# masterdata_validator.py:668-754
def validate_row(self, row: pd.Series) -> Dict:
    """MasterData 행 검증 - 핵심 로직"""

    # 1. Charge Group 분류
    charge_group = self.classify_charge_group(
        row.get("RATE SOURCE"), row.get("DESCRIPTION")
    )

    # 2. 기준 요율 조회 (4단계 우선순위)
    ref_rate = None
    if charge_group == "Contract":
        ref_rate = self.find_contract_ref_rate(
            row.get("DESCRIPTION"), row.get("RATE SOURCE"), row
        )  # line 226-350
    elif charge_group == "PortalFee":
        ref_rate = self.config_manager.get_portal_fee_rate(
            row.get("DESCRIPTION"), "USD"
        )

    # 3. Delta % 계산
    delta_pct = self.calculate_delta_percent(
        row.get("RATE"), ref_rate
    )  # line 542-550

    # 4. COST-GUARD 밴드 결정
    cg_band = self.get_cost_guard_band(delta_pct)  # line 552-568

    # 5. PDF 매핑 및 실제 데이터 추출 (Hybrid)
    pdf_info = self.map_masterdata_to_pdf(row)
    pdf_line_item = self._extract_pdf_line_item(row)  # line 350-450

    # 6. Gate 점수 계산
    gate_score = self.calculate_gate_score(
        row, ref_rate, charge_group, pdf_info["pdf_count"]
    )  # line 570-620

    # 7. Validation Status 결정 (At Cost 특별 검증)
    validation_status = self._determine_validation_status(
        row, charge_group, delta_pct, pdf_line_item
    )  # line 709-737

    return {
        "Validation_Status": validation_status,
        "Ref_Rate_USD": ref_rate,
        "Python_Delta": delta_pct,
        "CG_Band": cg_band,
        "Charge_Group": charge_group,
        "Gate_Score": gate_score,
        "PDF_Amount": pdf_line_item.get("amount") if pdf_line_item else None,
        "PDF_Qty": pdf_line_item.get("qty") if pdf_line_item else None,
        "PDF_Unit_Rate": pdf_line_item.get("unit_rate") if pdf_line_item else None,
    }
```

* `lookup_ref_rate`는 **±3% 허용오차**, **>15% Auto-Fail**를 메타로 사용.
* `banding`과 알림 임계는 **COST-GUARD 표준** 사용.

---

## Gate Validation Logic

### Gate Score Calculation
```python
# masterdata_validator.py:570-620
def calculate_gate_score(self, row, ref_rate, charge_group, pdf_count=0) -> float:
    """Gate 검증 점수 계산 (0-100)"""

    score = 0
    max_score = 100

    # Gate-01: RATE SOURCE 존재 (10점)
    if not pd.isna(row.get("RATE SOURCE")):
        score += 10

    # Gate-02: DESCRIPTION 존재 (10점)
    if not pd.isna(row.get("DESCRIPTION")):
        score += 10

    # Gate-03: RATE 유효값 (10점)
    if not pd.isna(row.get("RATE")) and row.get("RATE", 0) > 0:
        score += 10

    # Gate-04: Q'TY 유효값 (10점)
    if not pd.isna(row.get("Q'TY")) and row.get("Q'TY", 0) > 0:
        score += 10

    # Gate-05: TOTAL 계산 정확성 (20점)
    if self._verify_total_calculation(row):
        score += 20

    # Gate-06: PDF 매칭 (30점)
    if pdf_count > 0:
        score += 30  # PDF 존재
        if self._verify_pdf_amount_match(row):
            score += 10  # PDF 금액 일치

    # Gate-07: Ref Rate 존재 (10점)
    if ref_rate is not None and ref_rate > 0:
        score += 10

    return min(score, max_score)
```

### PDF Matching Rules
```python
# masterdata_validator.py:map_masterdata_to_pdf()
def map_masterdata_to_pdf(self, row) -> Dict:
    """MasterData → PDF 매핑 규칙"""

    # 1. Order Ref → PDF Folder Name (exact match)
    order_ref = row.get("ORDER REF", "")
    pdf_files = self._find_pdf_by_order_ref(order_ref)

    # 2. Category → PDF Line Items (fuzzy match, threshold 0.60)
    description = row.get("DESCRIPTION", "")
    pdf_line_items = self._extract_pdf_line_items(pdf_files)

    # 3. Amount Tolerance: ±3%
    matched_items = []
    for item in pdf_line_items:
        if self._fuzzy_match_description(description, item["description"]) >= 0.60:
            if self._verify_amount_tolerance(row.get("TOTAL (USD)", 0), item["amount"]):
                matched_items.append(item)

    return {
        "pdf_count": len(pdf_files),
        "matched_items": matched_items,
        "pdf_files": pdf_files
    }
```

### PDF Line Item Extraction (Hybrid)
```python
# masterdata_validator.py:350-450
def _extract_pdf_line_item(self, row: pd.Series) -> Optional[Dict]:
    """PDF에서 라인 아이템 추출 (Hybrid System)"""

    if self.use_hybrid:
        # Hybrid Mode: Unified IR 사용
        pdf_path = self._get_pdf_path_by_order_ref(row.get("ORDER REF", ""))
        if pdf_path and self.hybrid_client:
            unified_ir = self.hybrid_client.parse_pdf(pdf_path, "invoice")
            if unified_ir:
                return self.ir_adapter.extract_invoice_line_item(
                    unified_ir, row.get("DESCRIPTION", "")
                )
    else:
        # Legacy Mode: 기존 PDF Integration
        if self.pdf_integration:
            return self.pdf_integration.extract_line_item(
                row.get("ORDER REF", ""), row.get("DESCRIPTION", "")
            )

    return None
```

### Gate Status Determination
```python
# Gate PASS 조건: score ≥ 80
gate_status = "PASS" if gate_score >= 80 else "FAIL"

# At Cost 항목 특별 검증
if "AT COST" in rate_source:
    if pdf_line_item:
        pdf_amount = pdf_line_item.get("amount", 0.0)
        draft_total = row.get("TOTAL (USD)", 0.0)
        amount_diff = abs(pdf_amount - draft_total)

        if amount_diff < 0.01:
            validation_status = "PASS"  # PDF 금액 일치
        elif amount_diff > draft_total * 0.03:
            validation_status = "FAIL"  # 3% 이상 차이
        else:
            validation_status = "REVIEW_NEEDED"
    else:
        validation_status = "FAIL"  # At Cost인데 PDF 없음
```

---

## Portal Fee Special Handling

### Configuration Priority
```python
# masterdata_validator.py:682-686 (validate_row)
elif charge_group == "PortalFee":
    # Portal Fee는 Configuration에서 USD로 직접 조회
    ref_rate = self.config_manager.get_portal_fee_rate(
        row.get("DESCRIPTION"), "USD"
    )

# config_manager.py:get_portal_fee_rate()
def get_portal_fee_rate(self, description: str, currency: str = "USD") -> Optional[float]:
    """Portal Fee 요율 조회 (USD 기준)"""

    # 1. Portal Fee USD 직접 조회
    portal_fee_usd = self.config.get("portal_fee_rates", {}).get(description)
    if portal_fee_usd:
        return portal_fee_usd

    # 2. AED 있으면 USD 변환 (표시만, 검증은 USD 기준)
    if 'AED' in description.upper():
        portal_fee_aed = self.config.get("portal_fee_rates_aed", {}).get(description)
        if portal_fee_aed:
            return portal_fee_aed / 3.6725  # AED → USD 변환

    return None
```

### Tolerance Override
```python
# masterdata_validator.py:732-737 (validate_row)
elif charge_group == "PortalFee" and delta_pct is not None:
    if abs(delta_pct) <= 0.5:      # Portal Fee: ±0.5% (특별 허용오차)
        validation_status = "PASS"
    elif abs(delta_pct) > 5:       # Portal Fee: >5% Auto-Fail
        validation_status = "FAIL"
    else:
        validation_status = "REVIEW_NEEDED"
```

### Portal Fee vs Contract Item 차이점
| 항목 | Portal Fee | Contract Item |
|------|------------|---------------|
| **허용오차** | ±0.5% | ±3% |
| **Auto-Fail** | >5% | >15% |
| **요율 조회** | `get_portal_fee_rate()` | `find_contract_ref_rate()` |
| **Configuration** | `portal_fee_rates` | `contract_rates` + `lane_map` |
| **검증 우선순위** | 1순위 (고정요율) | 2순위 (계약요율) |

---

## Options (개선 선택지)

1. **per RT↔per truck 변환룰 확정**(컨/벌크 혼재 방지) — Δ% 왜곡 제거.
2. **Lane 유사도 임계 0.60→0.65** 튜닝 — 잘못된 근접 매칭 감소(REF_MISSING 더 축소).
3. **Evidence OCR 템플릿화**(공항·항만 공용 포맷) — AT-COST 자동 인식률↑.

---

## Roadmap (P→Pi→B→O→S)

* **Prepare:** 레퍼런스 JSON/MD 최신 스냅샷 동기화(항공/컨/벌크/내륙), NormalizationMap 보강.
* **Pilot:** 최근월 인보이스 배치에 Δ% 밴드·유사도 A/B(0.60 vs 0.65). KPI: **Accuracy ≥97%, Automation ≥94%**.
* **Build:** 리포트 템플릿(COST-GUARD 표 + 증빙링크 + 논리열) + proof.artifact 내보내기.
* **Operate:** HIGH/CRITICAL 실시간 TG 알림 + 재무 분개(VAT/AT-COST 분리).
* **Scale:** `ApprovedLaneMap` 월별 스냅샷·드리프트 감시.

---

## Automation Notes

* **명령:** `/switch_mode LATTICE + /logi-master invoice-audit --deep` → OCR·정합성·조인 자동 / `/switch_mode COST-GUARD + /logi-master invoice-audit` → 밴드 판정표 생성.
* **FX/통화:** 시스템 전역 **USD 기준 + AED 보조**, 환율 고정 3.6725(변경 시 전역 경고).
* **데이터사전:** `origin,destination,vehicle,unit,ref_rate_usd,delta_pct,cg_band` 표준 필드.

---

## QA 체크리스트

* [ ] Category/Port/Destination/Unit 조인키가 전 라인에서 채워졌는가?
* [ ] 허용오차(±3%)·Auto-Fail(>15%)가 메타에서 읽혀 적용되었는가?
* [ ] AT-COST 라인의 **AED 원가→USD 환산**과 VAT 분리가 증빙과 일치하는가?
* [ ] ApprovedLaneMap 중앙값으로 보강된 레인에 **cg_band**가 부여되었는가?
* [ ] 리포트가 **PRISM proof.artifact(JSON)**를 포함하는가(해시·필드 검증)?

---

## Function Reference Table

### Core Validation Functions
| Function | File | Line | Purpose |
|----------|------|------|---------|
| `validate_all()` | masterdata_validator.py | 832-867 | MasterData 전체 검증 - 메인 진입점 |
| `validate_row()` | masterdata_validator.py | 668-754 | MasterData 행 검증 - 핵심 로직 |
| `classify_charge_group()` | masterdata_validator.py | 150-200 | Charge Group 분류 (Contract/PortalFee/AtCost) |
| `find_contract_ref_rate()` | masterdata_validator.py | 226-350 | 계약 요율 조회 (4단계 우선순위) |
| `calculate_delta_percent()` | masterdata_validator.py | 542-550 | Delta % 계산 |
| `get_cost_guard_band()` | masterdata_validator.py | 552-568 | COST-GUARD 밴드 결정 |
| `calculate_gate_score()` | masterdata_validator.py | 570-620 | Gate 검증 점수 계산 (0-100) |
| `_extract_pdf_line_item()` | masterdata_validator.py | 350-450 | PDF 라인 아이템 추출 (Hybrid/Legacy) |

### Hybrid System Functions
| Function | File | Line | Purpose |
|----------|------|------|---------|
| `parse_pdf()` | hybrid_client.py | 45-100 | PDF 파싱 요청 및 Unified IR 반환 |
| `check_service_health()` | hybrid_client.py | 150-180 | API 서비스 상태 확인 |
| `extract_invoice_line_item()` | unified_ir_adapter.py | 200-300 | Unified IR → HVDC 데이터 변환 |
| `_convert_to_usd_if_needed()` | unified_ir_adapter.py | 400-450 | AED → USD 자동 변환 |

### Configuration Functions
| Function | File | Line | Purpose |
|----------|------|------|---------|
| `get_fixed_fee_by_keywords()` | config_manager.py | 100-150 | 고정 요율 키워드 조회 |
| `get_inland_transportation_rate()` | config_manager.py | 200-250 | 내륙 운송 요율 조회 |
| `get_portal_fee_rate()` | config_manager.py | 300-350 | Portal Fee 요율 조회 |
| `get_lane_map()` | config_manager.py | 400-450 | 레인 맵 조회 |
| `normalize()` | category_normalizer.py | 50-100 | 카테고리 정규화 (3단계 매칭) |

### PDF Integration Functions
| Function | File | Line | Purpose |
|----------|------|------|---------|
| `extract_line_item()` | pdf_integration.py | 200-300 | Legacy PDF 라인 아이템 추출 |
| `map_masterdata_to_pdf()` | masterdata_validator.py | 500-600 | MasterData → PDF 매핑 |
| `_find_pdf_by_order_ref()` | masterdata_validator.py | 700-750 | Order Ref로 PDF 파일 검색 |
| `_fuzzy_match_description()` | masterdata_validator.py | 800-850 | Description 퍼지 매칭 |

### Utility Functions
| Function | File | Line | Purpose |
|----------|------|------|---------|
| `_generate_notes()` | masterdata_validator.py | 756-850 | 검증 노트 생성 |
| `_print_statistics()` | masterdata_validator.py | 869-920 | 검증 통계 출력 |
| `_verify_total_calculation()` | masterdata_validator.py | 600-650 | TOTAL 계산 정확성 검증 |
| `_verify_pdf_amount_match()` | masterdata_validator.py | 650-700 | PDF 금액 일치 검증 |

---

## Configuration Files Structure

### Core Configuration Files
| File | Path | Purpose | Structure |
|------|------|---------|-----------|
| `config_contract_rates.json` | `00_Shared/` | 계약 요율 테이블 | `{category: {origin: {destination: rate}}}` |
| `config_shpt_lanes.json` | `00_Shared/` | 레인 맵 (운송 구간) | `{lane_id: {origin, destination, rate, unit}}` |
| `config_metadata.json` | `00_Shared/` | 메타데이터 (허용오차, Auto-Fail) | `{tolerance: 3.0, auto_fail: 15.0, fx_rate: 3.6725}` |
| `config_template.json` | `00_Shared/` | 템플릿 설정 | `{excel_schema, validation_rules}` |
| `config_synonyms.json` | `00_Shared/` | 카테고리 동의어 사전 | `{synonyms: {key: normalized_value}}` |

### Configuration Structure Examples
```json
// config_contract_rates.json
{
  "air_cargo": {
    "AUH": {"DSV_MUSSAFAH": 420, "MIRFA_SITE": 600},
    "DXB": {"DSV_MUSSAFAH": 380, "JEBEL_ALI": 450}
  },
  "container_cargo": {
    "JEBEL_ALI": {"DSV_MUSSAFAH": 250, "MIRFA_SITE": 520},
    "KHOR_FAKKAN": {"DSV_MUSSAFAH": 180}
  }
}

// config_shpt_lanes.json
{
  "lanes": {
    "AUH_DSV_MUSSAFAH": {
      "origin": "AUH",
      "destination": "DSV_MUSSAFAH",
      "rate": 420,
      "unit": "USD",
      "category": "air_cargo"
    }
  }
}

// config_metadata.json
{
  "tolerance_percent": 3.0,
  "auto_fail_percent": 15.0,
  "portal_fee_tolerance": 0.5,
  "portal_fee_auto_fail": 5.0,
  "fx_rate_usd_aed": 3.6725,
  "gate_score_threshold": 80
}

// config_synonyms.json
{
  "synonyms": {
    "DSV MUSSFAH YARD": "DSV_MUSSAFAH",
    "MIRFA SITE": "MIRFA_SITE",
    "JEBEL ALI PORT": "JEBEL_ALI"
  }
}
```

### Environment Configuration
| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_HYBRID` | `false` | Hybrid Mode 활성화 여부 |
| `HYBRID_API_URL` | `http://localhost:8080` | Hybrid API 서버 URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis 브로커 URL |
| `LOG_LEVEL` | `INFO` | 로깅 레벨 |

필요하면 위 로직을 바로 돌리는 **샘플 입력→산출 JSON/표 템플릿**도 뽑아줄게.
