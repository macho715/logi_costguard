# HVDC Invoice Audit - 핵심 함수 및 로직 레퍼런스

**작성일**: 2025-10-15
**프로젝트**: HVDC Invoice Audit System
**버전**: v4.1-PATCHED

---

## Executive Summary

HVDC Invoice Audit System의 핵심 함수와 알고리즘을 정리한 기술 레퍼런스입니다. 8개 Phase + logic_patch.md 적용을 거쳐 구현된 주요 컴포넌트의 함수 시그니처, 핵심 로직, 사용 예시를 포함합니다.

**v4.1-PATCHED 주요 개선사항**:
- Configuration 기반 COST-GUARD 밴드 판정
- 공용 유틸리티 통합 (cost_guard, portal_fee, rate_service)
- PDF 매핑 개선 (rglob 전체 스캔)
- At-Cost 판정 완충 (REVIEW_NEEDED)
- Hybrid 회로 차단 자동 복구

---

## 1. MasterData Validator (masterdata_validator.py)

### 1.1 validate_all()

**함수 시그니처**:
```python
def validate_all(self) -> pd.DataFrame:
```

**설명**: 102개 Invoice 항목의 전체 검증을 수행하고 결과를 DataFrame으로 반환

**핵심 로직**:
```python
def validate_all(self) -> pd.DataFrame:
    """전체 MasterData 검증 수행"""
    results = []

    for idx, row in self.df.iterrows():
        # 1. PDF 라인 아이템 추출 (At Cost 항목)
        pdf_line_item = self._extract_pdf_line_item(row)

        # 2. 계약 요율 조회
        ref_rate = self.find_contract_ref_rate(row)

        # 3. 검증 상태 결정
        validation_status = self._determine_validation_status(row, ref_rate, pdf_line_item)

        # 4. 결과 저장
        results.append({
            'row_index': idx,
            'order_ref': row['Order Ref. Number'],
            'description': row['DESCRIPTION'],
            'validation_status': validation_status,
            'pdf_amount': pdf_line_item.get('amount') if pdf_line_item else None,
            'pdf_qty': pdf_line_item.get('qty') if pdf_line_item else None,
            'pdf_unit_rate': pdf_line_item.get('unit_rate') if pdf_line_item else None,
            'validation_notes': self._generate_notes(row, ref_rate, pdf_line_item)
        })

    return pd.DataFrame(results)
```

**사용 예시**:
```python
validator = MasterDataValidator("invoice.xlsm")
results_df = validator.validate_all()
print(f"PASS: {len(results_df[results_df['validation_status'] == 'PASS'])}")
```

**파일 위치**: `01_DSV_SHPT/Core_Systems/masterdata_validator.py:45-89`

### 1.2 _extract_pdf_line_item()

**함수 시그니처**:
```python
def _extract_pdf_line_item(self, row: pd.Series) -> Optional[Dict]:
```

**설명**: At Cost 항목의 PDF에서 실제 청구 금액/수량을 추출

**핵심 로직**:
```python
def _extract_pdf_line_item(self, row: pd.Series) -> Optional[Dict]:
    """PDF에서 특정 Category의 실제 청구 라인 아이템 추출"""
    if "AT COST" not in str(row.get("RATE SOURCE", "")):
        return None

    # PDF 파일 경로 구성
    order_ref = row['Order Ref. Number']
    pdf_filename = f"{order_ref}_CarrierInvoice.pdf"
    pdf_path = self.pdf_dir / pdf_filename

    if not pdf_path.exists():
        return None

    try:
        # Hybrid Client로 PDF 파싱
        unified_ir = self.hybrid_client.parse_invoice(str(pdf_path))

        # Unified IR Adapter로 라인 아이템 추출
        category = row['DESCRIPTION']
        line_item = self.unified_ir_adapter.extract_invoice_line_item(unified_ir, category)

        return line_item
    except Exception as e:
        logger.error(f"PDF parsing failed for {pdf_filename}: {e}")
        return None
```

**사용 예시**:
```python
pdf_data = validator._extract_pdf_line_item(row)
if pdf_data:
    print(f"PDF Amount: ${pdf_data['amount']:.2f}")
```

**파일 위치**: `01_DSV_SHPT/Core_Systems/masterdata_validator.py:120-145`

---

## 2. Unified IR Adapter (unified_ir_adapter.py)

### 2.1 extract_invoice_data()

**함수 시그니처**:
```python
def extract_invoice_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
```

**설명**: Unified IR에서 Invoice 데이터(Total Amount, Items)를 추출

**핵심 로직**:
```python
def extract_invoice_data(self, unified_ir: Dict[str, Any]) -> Dict[str, Any]:
    """Unified IR에서 Invoice 데이터 추출"""
    extracted = {
        "total_amount": 0.0,
        "currency": "USD",
        "items": [],
        "extraction_method": "unknown"
    }

    blocks = unified_ir.get("blocks", [])

    # 1. Summary 블록에서 Total Amount 추출 (우선순위 1)
    summary = self._extract_summary_section(blocks)
    if summary.get("total"):
        extracted["total_amount"] = summary["total"]
        extracted["currency"] = summary.get("currency", "USD")
        extracted["extraction_method"] = "summary"

    # 2. Summary 블록 Fallback (좌표 기반, 우선순위 2)
    for block in blocks:
        if block.get("type") == "summary" and block.get("total_amount"):
            extracted["total_amount"] = block["total_amount"]
            extracted["currency"] = block["currency"]
            extracted["extraction_method"] = block["extraction_method"]
            break

    # 3. Items 추출
    for block in blocks:
        if block.get("type") == "table":
            items = self._extract_items_from_table(block["rows"])
            extracted["items"].extend(items)
        elif block.get("type") == "text":
            items = self._extract_items_from_text(block["text"])
            extracted["items"].extend(items)

    return extracted
```

**사용 예시**:
```python
invoice_data = adapter.extract_invoice_data(unified_ir)
print(f"Total: ${invoice_data['total_amount']:.2f} {invoice_data['currency']}")
```

**파일 위치**: `00_Shared/unified_ir_adapter.py:45-89`

### 2.2 extract_invoice_line_item()

**함수 시그니처**:
```python
def extract_invoice_line_item(self, unified_ir: Dict, category: str) -> Optional[Dict]:
```

**설명**: 4단계 Fuzzy 매칭으로 특정 카테고리의 라인 아이템을 추출

**핵심 로직**:
```python
def extract_invoice_line_item(self, unified_ir: Dict, category: str) -> Optional[Dict]:
    """4단계 Fuzzy 매칭으로 라인 아이템 추출"""
    blocks = unified_ir.get("blocks", [])
    all_items = []

    # 모든 블록에서 아이템 수집
    for block in blocks:
        if block.get("type") == "table":
            items = self._extract_items_from_table(block["rows"])
            all_items.extend(items)
        elif block.get("type") == "text":
            items = self._extract_items_from_text(block["text"])
            all_items.extend(items)

    # 4단계 매칭 전략
    for item in all_items:
        description = item.get("description", "").upper()
        category_upper = category.upper()

        # 1. Exact Match
        if description == category_upper:
            return self._convert_to_usd_if_needed(item)

        # 2. Contains Match
        if category_upper in description or description in category_upper:
            return self._convert_to_usd_if_needed(item)

        # 3. Keyword Match (Jaccard similarity > 0.7)
        if self._calculate_jaccard_similarity(category_upper, description) > 0.7:
            return self._convert_to_usd_if_needed(item)

        # 4. Fuzzy Match (SequenceMatcher ratio > 0.6)
        if self._calculate_fuzzy_ratio(category_upper, description) > 0.6:
            return self._convert_to_usd_if_needed(item)

    return None
```

**사용 예시**:
```python
line_item = adapter.extract_invoice_line_item(unified_ir, "CARRIER CONTAINER RETURN SERVICE FEE")
if line_item:
    print(f"Amount: ${line_item['amount']:.2f}, Qty: {line_item['qty']}")
```

**파일 위치**: `00_Shared/unified_ir_adapter.py:200-250`

### 2.3 _extract_summary_section()

**함수 시그니처**:
```python
def _extract_summary_section(self, blocks: List[Dict]) -> Dict[str, Any]:
```

**설명**: PDF Summary 섹션에서 TOTAL, VAT, SUB TOTAL을 추출

**핵심 로직**:
```python
def _extract_summary_section(self, blocks: List[Dict]) -> Dict[str, Any]:
    """Summary 섹션 추출 (TOTAL, VAT, SUB TOTAL)"""
    summary = {}

    # 정규식 패턴 (우선순위: 긴 키워드부터)
    patterns = {
        "grand_total": r"(GRAND\s*TOTAL|Grand\s*Total)\s*:?\s*([0-9,]+\.?\d*)",
        "subtotal": r"(SUB\s*TOTAL|Subtotal)\s*:?\s*([0-9,]+\.?\d*)",
        "total_net": r"(TOTAL\s*NET\s*AMOUNT[^:]*|Total\s*Net\s*Amount[^:]*)\s*:?\s*([0-9,]+\.?\d*)",
        "vat": r"(VAT|Value\s*Added\s*Tax)\s*(?:\([^)]*\))?\s*:?\s*([0-9,]+\.?\d*)",
        "total": r"(?<!SUB\s)(?<!GRAND\s)(?<!NET\s)(TOTAL|Total)(?!\s*NET)\s*:?\s*([0-9,]+\.?\d*)"
    }

    for block in blocks:
        if block.get("type") == "text":
            text = block.get("text", "")

            for key, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    amount = self._parse_number(matches[0][-1])
                    if amount > 0:
                        summary[key] = amount
                        if key == "total" and "total" not in summary:
                            summary["total"] = amount

    # 환율 추출
    for block in blocks:
        if block.get("type") == "text":
            text = block.get("text", "")
            fx_match = re.search(r"R\.O\.E\.\s*1\s*USD\s*=\s*([0-9.]+)\s*AED", text, re.IGNORECASE)
            if fx_match:
                summary["exchange_rate"] = float(fx_match.group(1))

    return summary
```

**사용 예시**:
```python
summary = adapter._extract_summary_section(blocks)
print(f"Total: ${summary.get('total', 0):.2f}")
```

**파일 위치**: `00_Shared/unified_ir_adapter.py:333-400`

---

## 3. Configuration Manager (config_manager.py)

### 3.1 get_contract_rate()

**함수 시그니처**:
```python
def get_contract_rate(self, description: str, transport_mode: str = None) -> Optional[float]:
```

**설명**: 설명과 운송 모드를 기반으로 계약 요율을 조회

**핵심 로직**:
```python
def get_contract_rate(self, description: str, transport_mode: str = None) -> Optional[float]:
    """계약 요율 조회"""
    description_upper = description.upper()

    # 1. DO Fee 조회
    if any(keyword in description_upper for keyword in ["DO FEE", "D/O FEE", "DELIVERY ORDER"]):
        return self.get_do_fee(transport_mode)

    # 2. Customs Clearance Fee
    if any(keyword in description_upper for keyword in ["CUSTOMS", "CUSTOM CLEARANCE"]):
        return self.get_customs_clearance_fee()

    # 3. Portal Fee
    if any(keyword in description_upper for keyword in ["PORTAL", "PORTAL FEE"]):
        return self.get_portal_fee_rate()

    # 4. Inland Transportation
    if any(keyword in description_upper for keyword in ["TRANSPORT", "INLAND", "DELIVERY"]):
        origin, destination = self._extract_origin_destination(description)
        if origin and destination:
            return self.get_inland_transportation_rate(origin, destination)

    # 5. 키워드 기반 고정 요율
    return self.get_fixed_fee_by_keywords(description)
```

**사용 예시**:
```python
config = ConfigurationManager()
rate = config.get_contract_rate("DO FEE", "CONTAINER")
print(f"Rate: ${rate:.2f}")
```

**파일 위치**: `00_Shared/config_manager.py:45-89`

### 3.2 get_inland_transportation_rate()

**함수 시그니처**:
```python
def get_inland_transportation_rate(self, origin: str, destination: str) -> Optional[float]:
```

**설명**: 출발지와 도착지를 기반으로 내륙 운송 요율을 조회

**핵심 로직**:
```python
def get_inland_transportation_rate(self, origin: str, destination: str) -> Optional[float]:
    """내륙 운송 요율 조회"""
    # 위치 정규화
    origin_normalized = self._normalize_location(origin)
    destination_normalized = self._normalize_location(destination)

    # Lane Map 조회
    lane_map = self.get_lane_map()

    for lane in lane_map:
        if (lane["origin"].upper() == origin_normalized.upper() and
            lane["destination"].upper() == destination_normalized.upper()):
            return lane["rate"]

    # 역방향 검색
    for lane in lane_map:
        if (lane["destination"].upper() == origin_normalized.upper() and
            lane["origin"].upper() == destination_normalized.upper()):
            return lane["rate"]

    return None
```

**사용 예시**:
```python
rate = config.get_inland_transportation_rate("Khalifa Port", "DSV Mussafah Yard")
print(f"Transportation Rate: ${rate:.2f}")
```

**파일 위치**: `00_Shared/config_manager.py:120-150`

---

## 4. Category Normalizer (category_normalizer.py)

### 4.1 normalize_category()

**함수 시그니처**:
```python
def normalize_category(self, category: str) -> str:
```

**설명**: Invoice Description을 표준 카테고리로 정규화

**핵심 로직**:
```python
def normalize_category(self, category: str) -> str:
    """카테고리 정규화 (4단계 매칭)"""
    if not category:
        return ""

    category_clean = category.strip().upper()

    # 1. Exact Match
    exact_result = self._match_exact(category_clean)
    if exact_result:
        return exact_result

    # 2. Synonym Match
    synonym_result = self._match_synonym(category_clean)
    if synonym_result:
        return synonym_result

    # 3. Partial Match (threshold=0.8)
    partial_result = self._match_partial(category_clean)
    if partial_result:
        return partial_result

    # 4. Fallback (원본 반환)
    return category_clean

def _match_exact(self, category: str) -> Optional[str]:
    """정확 일치"""
    standard_categories = [
        "DO FEE", "CUSTOMS CLEARANCE", "INLAND TRANSPORTATION",
        "TERMINAL HANDLING CHARGES", "PORTAL FEE"
    ]

    for standard in standard_categories:
        if category == standard:
            return standard

    return None

def _match_synonym(self, category: str) -> Optional[str]:
    """동의어 매칭"""
    synonyms = self.load_synonyms()

    for standard, alias_list in synonyms.items():
        for alias in alias_list:
            if alias.upper() in category or category in alias.upper():
                return standard

    return None

def _match_partial(self, category: str, threshold: float = 0.8) -> Optional[str]:
    """부분 매칭 (Jaccard similarity)"""
    standard_categories = [
        "DO FEE", "CUSTOMS CLEARANCE", "INLAND TRANSPORTATION",
        "TERMINAL HANDLING CHARGES", "PORTAL FEE"
    ]

    best_match = None
    best_score = 0.0

    for standard in standard_categories:
        score = self._calculate_jaccard_similarity(category, standard)
        if score >= threshold and score > best_score:
            best_score = score
            best_match = standard

    return best_match
```

**사용 예시**:
```python
normalizer = CategoryNormalizer()
normalized = normalizer.normalize_category("D/O FEE")
print(f"Normalized: {normalized}")  # "DO FEE"
```

**파일 위치**: `00_Shared/category_normalizer.py:25-89`

---

## 5. Hybrid Client (hybrid_client.py)

### 5.1 parse_invoice()

**함수 시그니처**:
```python
def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
```

**설명**: FastAPI를 통해 PDF를 업로드하고 Celery Task로 파싱

**핵심 로직**:
```python
def parse_invoice(self, pdf_path: str) -> Dict[str, Any]:
    """PDF 파싱 (FastAPI + Celery)"""
    try:
        # 1. PDF 업로드
        task_id = self._upload_pdf(pdf_path)

        # 2. 결과 폴링 (최대 30초)
        result = self._poll_result(task_id, timeout=30)

        if result.get("status") == "SUCCESS":
            return result.get("data", {})
        else:
            logger.error(f"PDF parsing failed: {result.get('error')}")
            return {}

    except Exception as e:
        logger.error(f"Hybrid client error: {e}")
        return {}

def _upload_pdf(self, pdf_path: str) -> str:
    """PDF 업로드 및 Task ID 수신"""
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(f"{self.base_url}/parse", files=files)

    if response.status_code == 200:
        return response.json()["task_id"]
    else:
        raise Exception(f"Upload failed: {response.status_code}")

def _poll_result(self, task_id: str, timeout: int = 30) -> Dict:
    """결과 폴링"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(f"{self.base_url}/result/{task_id}")

        if response.status_code == 200:
            result = response.json()
            if result["status"] in ["SUCCESS", "FAILURE"]:
                return result

        time.sleep(1)  # 1초 대기

    return {"status": "TIMEOUT", "error": "Polling timeout"}
```

**사용 예시**:
```python
client = HybridClient("http://localhost:8080")
unified_ir = client.parse_invoice("invoice.pdf")
print(f"Blocks: {len(unified_ir.get('blocks', []))}")
```

**파일 위치**: `00_Shared/hybrid_integration/hybrid_client.py:25-89`

---

## 6. Celery Worker (celery_app.py)

### 6.1 parse_invoice_task()

**함수 시그니처**:
```python
@celery_app.task
def parse_invoice_task(pdf_path: str, doc_type: str = "invoice") -> Dict[str, Any]:
```

**설명**: Celery Task로 PDF를 파싱하고 Unified IR을 생성

**핵심 로직**:
```python
@celery_app.task
def parse_invoice_task(pdf_path: str, doc_type: str = "invoice") -> Dict[str, Any]:
    """PDF 파싱 Celery Task"""
    try:
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            return {"status": "FAILURE", "error": f"File not found: {pdf_path}"}

        # ADE 엔진으로 파싱
        unified_ir = _parse_with_ade(pdf_file)

        return {
            "status": "SUCCESS",
            "data": unified_ir,
            "filename": pdf_file.name
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        return {"status": "FAILURE", "error": str(e)}

def _parse_with_ade(pdf_file: Path) -> Dict[str, Any]:
    """ADE 엔진으로 PDF 파싱"""
    # pdfplumber로 실제 파싱
    blocks = []

    with pdfplumber.open(str(pdf_file)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # 1. 테이블 추출
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if table:
                    blocks.append({
                        "type": "table",
                        "page": page_num,
                        "table_id": f"table_{page_num}_{table_idx}",
                        "rows": table,
                        "bbox": None
                    })

            # 2. 텍스트 추출
            text = page.extract_text()
            if text:
                blocks.append({
                    "type": "text",
                    "page": page_num,
                    "text": text,
                    "bbox": None
                })

    # Multi-strategy Total Amount Fallback
    total_info = _extract_total_with_coordinates(pdf_file)
    if not total_info:
        total_info = _extract_total_from_table(pdf_file)

    if total_info:
        blocks.append({
            "type": "summary",
            "total_amount": total_info["total_amount"],
            "currency": total_info["currency"],
            "bbox": total_info.get("bbox"),
            "extraction_method": total_info["extraction_method"]
        })

    return {
        "doc_id": pdf_file.name,
        "engine": "ade",
        "pages": len(pdf.pages) if 'pdf' in locals() else 1,
        "blocks": blocks,
        "meta": {
            "confidence": 0.90,
            "filename": pdf_file.name,
            "parser": "pdfplumber"
        }
    }
```

**사용 예시**:
```python
# Celery Task 실행 (보통 Hybrid Client에서 호출)
result = parse_invoice_task.delay("invoice.pdf", "invoice")
unified_ir = result.get()
```

**파일 위치**: `hybrid_doc_system/worker/celery_app.py:25-89`

### 6.2 _extract_total_with_coordinates()

**함수 시그니처**:
```python
def _extract_total_with_coordinates(pdf_file: Path) -> Optional[Dict]:
```

**설명**: 좌표 기반으로 "Total Amount" 라벨 주변의 금액을 추출

**핵심 로직**:
```python
def _extract_total_with_coordinates(pdf_file: Path) -> Optional[Dict]:
    """좌표 기반 Total Amount 추출"""
    with pdfplumber.open(str(pdf_file)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words()

            # "Total Amount" 라벨 찾기
            for i, w in enumerate(words):
                if "total" in w["text"].lower() and "amount" in w["text"].lower():
                    x0, y0, x1, y1 = w["x0"], w["top"], w["x1"], w["bottom"]

                    # 1. 우측 영역 검색 (same line, ±10px y tolerance)
                    for w in words[i + 2:]:
                        if w["x0"] >= x1 + 10 and w["x0"] <= 600:  # 페이지 전체 너비
                            if abs(w["top"] - y0) <= 10:  # Same line tolerance
                                amount = _parse_number(w["text"])
                                if amount > 10:  # Minimum threshold
                                    currency = "USD"
                                    for nearby in words:
                                        if (abs(nearby["x0"] - w["x0"]) < 50 and
                                            "AED" in nearby["text"]):
                                            currency = "AED"
                                            break

                                    return {
                                        "total_amount": amount,
                                        "currency": currency,
                                        "bbox": {
                                            "page": page_num + 1,
                                            "x0": w["x0"], "y0": w["top"],
                                            "x1": w["x1"], "y1": w["bottom"]
                                        },
                                        "extraction_method": "coordinate_right"
                                    }

                    # 2. 아래 영역 검색
                    for w in words[i + 2:]:
                        if (w["top"] >= y1 + 5 and w["top"] <= y1 + 50 and
                            abs(w["x0"] - x0) <= 20):
                            amount = _parse_number(w["text"])
                            if amount > 10:
                                return {
                                    "total_amount": amount,
                                    "currency": "USD",
                                    "bbox": {
                                        "page": page_num + 1,
                                        "x0": w["x0"], "y0": w["top"],
                                        "x1": w["x1"], "y1": w["bottom"]
                                    },
                                    "extraction_method": "coordinate_below"
                                }

    return None
```

**사용 예시**:
```python
total_info = _extract_total_with_coordinates(Path("invoice.pdf"))
if total_info:
    print(f"Total: ${total_info['total_amount']:.2f} {total_info['currency']}")
```

**파일 위치**: `hybrid_doc_system/worker/celery_app.py:291-408`

---

## 7. 공용 유틸리티 (00_Shared/) - v4.1-PATCHED 신규

### 7.1 COST-GUARD 유틸리티 (cost_guard.py)

#### 7.1.1 get_cost_guard_band()

**함수 시그니처**:
```python
def get_cost_guard_band(delta_pct: Optional[float], bands: Dict[str, float]) -> str:
```

**설명**: Configuration 기반 COST-GUARD 밴드 판정

**핵심 로직**:
```python
def get_cost_guard_band(delta_pct: Optional[float], bands: Dict[str, float]) -> str:
    """COST-GUARD 밴드 판정 (Configuration 기반)"""
    if delta_pct is None:
        return "N/A"

    # 절대값으로 변환
    d = abs(delta_pct)

    # 밴드 판정 (pass < warn < high < autofail)
    if d <= bands.get("pass", 3):
        return "PASS"
    elif d <= bands.get("warn", 5):
        return "WARN"
    elif d <= bands.get("high", 10):
        return "HIGH"
    else:
        return "CRITICAL"
```

**사용 예시**:
```python
bands = {"pass": 3.0, "warn": 5.0, "high": 10.0, "autofail": 15.0}
band = get_cost_guard_band(1.5, bands)  # "PASS"
band = get_cost_guard_band(7.2, bands)  # "HIGH"
```

**파일 위치**: `00_Shared/cost_guard.py:12-35`

#### 7.1.2 should_auto_fail()

**함수 시그니처**:
```python
def should_auto_fail(delta_pct: Optional[float], bands: Dict[str, float]) -> bool:
```

**설명**: Auto-Fail 여부 판정 (>15%)

**핵심 로직**:
```python
def should_auto_fail(delta_pct: Optional[float], bands: Dict[str, float]) -> bool:
    """Auto-Fail 여부 판정"""
    if delta_pct is None:
        return False

    autofail_threshold = bands.get("autofail", 15)
    return abs(delta_pct) > autofail_threshold
```

**파일 위치**: `00_Shared/cost_guard.py:38-48`

### 7.2 Portal Fee 유틸리티 (portal_fee.py)

#### 7.2.1 resolve_portal_fee_usd()

**함수 시그니처**:
```python
def resolve_portal_fee_usd(description: str, fx_rate: float, formula_text: Optional[str] = None) -> Optional[float]:
```

**설명**: Portal Fee USD 요율 해결 (AED → USD 변환)

**핵심 로직**:
```python
def resolve_portal_fee_usd(description: str, fx_rate: float, formula_text: Optional[str] = None) -> Optional[float]:
    """Portal Fee USD 요율 해결"""
    # 1. Formula에서 AED 추출 시도
    aed_amount = parse_aed_from_formula(formula_text)

    # 2. 실패 시 Description에서 고정값 매칭
    if aed_amount is None:
        aed_amount = find_fixed_portal_fee(description)

    # 3. USD 환산
    if aed_amount is not None and fx_rate > 0:
        return round(aed_amount / fx_rate, 2)

    return None
```

**사용 예시**:
```python
usd_rate = resolve_portal_fee_usd("APPOINTMENT", 3.6725, "=27*3.6725")  # 7.35
usd_rate = resolve_portal_fee_usd("DPC FEE", 3.6725)  # 9.53
```

**파일 위치**: `00_Shared/portal_fee.py:67-87`

#### 7.2.2 get_portal_fee_band()

**함수 시그니처**:
```python
def get_portal_fee_band(draft_rate: float, ref_rate: float) -> str:
```

**설명**: Portal Fee 밴드 판정 (특별 규칙: ±0.5% PASS, >5% FAIL)

**핵심 로직**:
```python
def get_portal_fee_band(draft_rate: float, ref_rate: float) -> str:
    """Portal Fee 밴드 판정 (특별 규칙)"""
    if ref_rate == 0:
        return "PASS" if draft_rate == 0 else "FAIL"

    delta_pct = abs((draft_rate - ref_rate) / ref_rate) * 100

    if delta_pct <= 0.5:
        return "PASS"
    elif delta_pct <= 5.0:
        return "WARN"
    else:
        return "FAIL"
```

**파일 위치**: `00_Shared/portal_fee.py:140-160`

### 7.3 Rate Service (rate_service.py)

#### 7.3.1 RateService.find_contract_ref_rate()

**함수 시그니처**:
```python
def find_contract_ref_rate(self, description: str, row: Optional[pd.Series] = None, transport_mode: Optional[str] = None) -> Optional[float]:
```

**설명**: 계약 참조 요율 통합 탐색 (4단계 우선순위)

**핵심 로직**:
```python
def find_contract_ref_rate(self, description: str, row: Optional[pd.Series] = None, transport_mode: Optional[str] = None) -> Optional[float]:
    """계약 참조 요율 통합 탐색"""
    if not description or pd.isna(description):
        return None

    desc_upper = str(description).upper()

    # Priority 1: 고빈도 고정 요율
    fixed_rate = self._get_fixed_fee_rate(desc_upper, transport_mode)
    if fixed_rate is not None:
        return fixed_rate

    # Priority 2: 키워드 기반 고정 요율 조회
    keyword_fee = self.config_manager.get_fixed_fee_by_keywords(description)
    if keyword_fee:
        # Transport mode 검증 로직...
        return keyword_fee["rate"]

    # Priority 3: Inland Transportation (FROM..TO)
    if any(kw in desc_upper for kw in ["TRANSPORTATION", "TRUCKING", "INLAND", "FROM", "TO"]):
        inland_rate = self._find_inland_transportation_rate(description)
        if inland_rate is not None:
            return inland_rate

    # Priority 4: General contract rate
    contract_rate = self.config_manager.get_contract_rate(description)
    if contract_rate is not None:
        return contract_rate

    return None
```

**파일 위치**: `00_Shared/rate_service.py:25-65`

---

## 8. 핵심 알고리즘

### 8.1 4-Stage Fuzzy Matching

**알고리즘**:
```
1. Exact Match (정확 일치)
   - description == category (100% 일치)

2. Contains Match (포함 관계)
   - category in description OR description in category

3. Keyword Match (키워드 유사도)
   - Jaccard similarity > 0.7
   - Stop words 필터링 후 비교

4. Fuzzy Match (문자열 유사도)
   - SequenceMatcher ratio > 0.6
   - 최종 fallback
```

### 7.2 Multi-Strategy Total Amount Fallback

**우선순위**:
```
1. 정규식 (_extract_summary_section) - 90%+ 성공률
   ↓
2. 좌표 기반 (우측 600px, 우측 절반 MAX)
   ↓
3. 테이블 기반 (TOTAL 키워드 행)
   ↓
4. 기본값 (0.0)
```

### 7.3 AED to USD Conversion

**환율**: 1 USD = 3.67 AED

```python
def _convert_to_usd_if_needed(amount: float, unit_rate: float, description: str) -> Tuple[float, float]:
    """AED → USD 변환"""
    if "AED" in description.upper() and "USD" not in description.upper():
        fx_rate = 3.67
        amount_usd = round(amount / fx_rate, 2)
        unit_rate_usd = round(unit_rate / fx_rate, 2)
        return (amount_usd, unit_rate_usd)
    return (amount, unit_rate)
```

---

## 8. 데이터 흐름

### 8.1 검증 워크플로우
```
MasterData Row → PDF Line Item 추출 → 계약 요율 조회 → 검증 상태 결정 → 결과 저장
```

### 8.2 PDF 파싱 워크플로우
```
PDF 파일 → Hybrid Client → FastAPI → Celery Task → pdfplumber → Unified IR → Adapter → 검증 결과
```

### 8.3 Configuration 조회 워크플로우
```
Description → Category Normalizer → Configuration Manager → JSON 파일 → 요율 반환
```

---

## Quick Reference

| Module | Function | Purpose | Input | Output |
|--------|----------|---------|-------|--------|
| masterdata_validator | validate_all() | 전체 검증 | DataFrame | List[Dict] |
| masterdata_validator | _extract_pdf_line_item() | At Cost PDF 추출 | pd.Series | Dict |
| unified_ir_adapter | extract_invoice_data() | Invoice 데이터 추출 | Dict | Dict |
| unified_ir_adapter | extract_invoice_line_item() | 라인 아이템 추출 | Dict, str | Dict |
| config_manager | get_contract_rate() | 계약 요율 조회 | str, str | float |
| config_manager | get_inland_transportation_rate() | 내륙 운송 요율 | str, str | float |
| category_normalizer | normalize_category() | 카테고리 정규화 | str | str |
| hybrid_client | parse_invoice() | PDF 파싱 | str | Dict |
| celery_app | parse_invoice_task() | Celery Task | str, str | Dict |
| celery_app | _extract_total_with_coordinates() | 좌표 기반 추출 | Path | Dict |

---

**작성자**: AI Development Team
**프로젝트**: HVDC Invoice Audit System
**버전**: v4.0-COMPLETE
**최종 업데이트**: 2025-10-15
