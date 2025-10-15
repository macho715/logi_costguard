# DOMESTIC Hybrid Integration - 단계별 구현 가이드

**파일**: `validate_sept_2025_with_pdf.py`
**목표**: Hybrid PDF Router 통합 (기존 로직 100% 보존)
**예상 작업 시간**: 30분
**난이도**: ⭐⭐☆☆☆ (쉬움)

---

## 📋 변경 사항 요약

**총 3곳만 수정** (전체 1444줄 중):
1. Line ~53-60: Import 섹션에 Hybrid 추가
2. Line ~132-218: parse_dn_pdfs 함수 수정
3. Line ~1369-1380: main 함수에서 parser 전달 로직 수정

**변경되지 않는 부분**:
- ✅ enhanced_matching.py 호출 (Line ~400+)
- ✅ cross_validate_invoice_dn 로직 (Line ~600+)
- ✅ 모든 출력 형식 및 리포트 생성

---

## Step 1: Import 섹션 수정 (Line 53-60)

### 현재 코드 (Line 53-60)

```python
# PDF 파서 시스템 import
sys.path.append(str(Path(__file__).parent.parent.parent / "PDF"))
try:
    from praser import DSVPDFParser
    from cross_doc_validator import CrossDocValidator

    PDF_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: PDF Parser not available: {e}")
    PDF_PARSER_AVAILABLE = False
```

### 수정 후 코드

```python
# PDF 파서 시스템 import
sys.path.append(str(Path(__file__).parent.parent.parent / "PDF"))
try:
    from praser import DSVPDFParser
    from cross_doc_validator import CrossDocValidator

    PDF_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: PDF Parser not available: {e}")
    PDF_PARSER_AVAILABLE = False

# 🆕 Hybrid Integration import
try:
    from Core_Systems.hybrid_pdf_integration import create_domestic_hybrid_integration
    HYBRID_INTEGRATION_AVAILABLE = True
    print("✨ Hybrid Docling/ADE integration enabled")
except ImportError as e:
    print(f"ℹ️  Hybrid integration not available (using standard parsing): {e}")
    HYBRID_INTEGRATION_AVAILABLE = False
```

**변경 사항**:
- 4줄 추가
- 기존 코드 수정 없음

---

## Step 2: parse_dn_pdfs 함수 수정 (Line 132-218)

### 현재 함수 구조

```python
def parse_dn_pdfs(pdf_files: list, parser: DSVPDFParser) -> list:
    """DN PDF 파일들을 파싱"""
    parsed_results = []

    for i, pdf_info in enumerate(pdf_files, 1):
        try:
            # 1. DSVPDFParser로 파싱
            result = parser.parse_pdf(pdf_path=pdf_info["pdf_path"], doc_type="DN")

            # 2. raw_text 폴백
            raw_text = result.get("raw_text") or extract_text_any(pdf_info["pdf_path"])

            # 3. 필드 추출
            fields = extract_from_pdf_text(raw_text)

            # 4. dn_data 업데이트
            dn_data = result.get("data", {})
            dn_data.update(fields)

            parsed_results.append(result)
        except Exception as e:
            # Error handling

    return parsed_results
```

### 수정 후 함수 (Option A: Minimal Change)

```python
def parse_dn_pdfs(pdf_files: list, parser: DSVPDFParser) -> list:
    """DN PDF 파일들을 파싱 - NOW WITH HYBRID ROUTING"""
    parsed_results = []

    # 🆕 Initialize hybrid integration if available
    hybrid_integration = None
    if HYBRID_INTEGRATION_AVAILABLE:
        try:
            hybrid_integration = create_domestic_hybrid_integration(log_level="INFO")
            print("✨ Using Hybrid Docling/ADE routing for DN parsing...")
        except Exception as e:
            print(f"⚠️  Hybrid integration init failed: {e}")
            hybrid_integration = None

    print(f"\n📄 DN PDF 파싱 시작... (총 {len(pdf_files)}개)")

    for i, pdf_info in enumerate(pdf_files, 1):
        try:
            print(f"  [{i}/{len(pdf_files)}] {pdf_info['filename']}", end=" ... ")

            # 🆕 Step 1: Try hybrid parsing first
            if hybrid_integration:
                try:
                    # Parse with hybrid routing
                    hybrid_result = hybrid_integration.parse_dn_with_routing(
                        pdf_info["pdf_path"],
                        shipment_ref=pdf_info.get("shipment_ref", "")
                    )

                    # Convert hybrid result to DSVPDFParser format for compatibility
                    result = {
                        "header": {
                            "doc_type": "DN",
                            "parse_status": "SUCCESS",
                            "file_path": hybrid_result["file_path"]
                        },
                        "raw_text": hybrid_result.get("text", ""),
                        "data": {
                            "loading_point": hybrid_result.get("origin", ""),
                            "destination": hybrid_result.get("destination", ""),
                            "vehicle_type": hybrid_result.get("vehicle_type", ""),
                            "waybill_no": hybrid_result.get("do_number", ""),
                            "destination_code": hybrid_result.get("destination_code", ""),
                            "capacity": DN_CAPACITY_DEFAULT
                        },
                        "meta": {
                            "folder": pdf_info["folder"],
                            "filename": pdf_info["filename"],
                            "shipment_ref_from_folder": pdf_info["shipment_ref"],
                            "routing_metadata": hybrid_result.get("routing_metadata", {})
                        }
                    }

                    parsed_results.append(result)
                    print("✅")
                    continue  # Skip to next file

                except Exception as hybrid_error:
                    print(f"⚠️  Hybrid failed, using fallback: {hybrid_error}")
                    # Fall through to existing logic below

            # Step 2: Existing DSVPDFParser logic (fallback)
            result = parser.parse_pdf(
                pdf_path=pdf_info["pdf_path"], doc_type="DN"
            )

            # --- [FIX-1] raw_text 누락 시 폴백 텍스트 추출 ---
            raw_text = result.get("raw_text") or result.get("text", "")
            if not raw_text:
                try:
                    raw_text = extract_text_any(pdf_info["pdf_path"])
                except Exception:
                    raw_text = ""
                if raw_text:
                    result["raw_text"] = raw_text

            # PDF 본문에서 핵심 필드 추출 → dn_data에 직접 덮어쓰기
            fields = extract_from_pdf_text(raw_text)
            dn_data = result.get("data", {})
            if dn_data is None:
                dn_data = {}

            if fields.get("dest_code"):
                dn_data["destination_code"] = fields["dest_code"]
            if fields.get("destination"):
                dn_data["destination"] = fields["destination"]
            if fields.get("loading_point"):
                dn_data["loading_point"] = fields["loading_point"]
            if fields.get("waybill"):
                dn_data["waybill_no"] = dn_data.get("waybill_no") or fields["waybill"]

            if "capacity" not in dn_data:
                dn_data["capacity"] = DN_CAPACITY_DEFAULT

            result["data"] = dn_data

            # 결과에 메타데이터 추가
            result["meta"] = {
                "folder": pdf_info["folder"],
                "filename": pdf_info["filename"],
                "shipment_ref_from_folder": pdf_info["shipment_ref"],
            }

            parsed_results.append(result)
            print("✅")

        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            parsed_results.append(
                {
                    "header": {
                        "doc_type": "DN",
                        "parse_status": "FAILED",
                        "error": str(e),
                    },
                    "meta": pdf_info,
                    "data": {},
                }
            )

    success_count = sum(
        1 for r in parsed_results if r["header"].get("parse_status") != "FAILED"
    )
    print(
        f"\n✅ 파싱 완료: {success_count}/{len(pdf_files)} 성공 ({success_count/len(pdf_files)*100:.1f}%)"
    )

    # 🆕 Print hybrid routing summary if used
    if hybrid_integration:
        hybrid_integration.print_summary()

    return parsed_results
```

### 핵심 변경 사항

**추가된 부분**:
1. **Line ~143-148**: Hybrid integration 초기화
2. **Line ~153-187**: Hybrid parsing 시도 블록 (try-except with fallback)
3. **Line ~220-222**: Hybrid 통계 출력

**보존된 부분**:
- ✅ 기존 DSVPDFParser fallback 로직 (Line 189+)
- ✅ extract_text_any 폴백 (Line 157-162)
- ✅ extract_from_pdf_text 필드 추출 (Line 167)
- ✅ dn_data 업데이트 로직 (Line 168-185)
- ✅ 에러 처리 (Line 197-209)

---

## Step 3: main 함수 수정 없음 (선택사항)

main 함수는 **수정 불필요**합니다.

**이유**:
- parse_dn_pdfs는 여전히 `parser` 인자를 받지만 내부에서 hybrid 사용
- 기존 호출 방식 유지:
  ```python
  parsed_dns = parse_dn_pdfs(pdf_files, parser)
  ```

**선택사항: 더 명확한 로깅**
```python
# Line ~1369 (main 함수 내)
if PDF_PARSER_AVAILABLE:
    print("\n📄 Step 2: DN PDF 파싱...")
    if HYBRID_INTEGRATION_AVAILABLE:
        print("  🔀 Mode: Hybrid Docling/ADE Routing")
    else:
        print("  📄 Mode: Standard DSVPDFParser")
    parser = DSVPDFParser(log_level="INFO")
    parsed_dns = parse_dn_pdfs(pdf_files, parser)
```

---

## 통합 전/후 비교

### Before (현재)

```
Flow: PDF → DSVPDFParser → extract_text_any → extract_from_pdf_text → enhanced_matching
Success Rate: 91.7% (33/36)
```

### After (통합)

```
Flow: PDF → HybridRouter → Docling/ADE → Unified IR → DOMESTIC format → enhanced_matching
                ↓ fallback
              DSVPDFParser → extract_text_any → ...

Expected Success Rate: >95% (35+/36)
```

---

## 실행 계획

### Phase 1: 백업 및 준비 (5분)

```bash
cd 02_DSV_DOMESTIC

# 백업
cp validate_sept_2025_with_pdf.py validate_sept_2025_with_pdf.py.backup

# Core_Systems 디렉토리 확인
ls Core_Systems/hybrid_pdf_integration.py
# → 파일 존재 확인
```

### Phase 2: 코드 수정 (15분)

#### 수정 1: Import 섹션 (Line 60 이후에 추가)

```python
# 위치: Line 60 (PDF_PARSER_AVAILABLE = False 다음)

# 🆕 Hybrid Integration import
try:
    from Core_Systems.hybrid_pdf_integration import create_domestic_hybrid_integration
    HYBRID_INTEGRATION_AVAILABLE = True
    print("✨ Hybrid Docling/ADE integration enabled")
except ImportError as e:
    print(f"ℹ️  Hybrid integration not available (using standard parsing): {e}")
    HYBRID_INTEGRATION_AVAILABLE = False
```

#### 수정 2: parse_dn_pdfs 함수 (Line 143 이후에 추가)

```python
# 위치: Line 143 (parsed_results = [] 다음)

# 🆕 Initialize hybrid integration if available
hybrid_integration = None
if HYBRID_INTEGRATION_AVAILABLE:
    try:
        hybrid_integration = create_domestic_hybrid_integration(log_level="INFO")
        print("✨ Using Hybrid Docling/ADE routing for DN parsing...")
    except Exception as e:
        print(f"⚠️  Hybrid integration init failed: {e}")
        hybrid_integration = None
```

#### 수정 3: For loop 내부 (Line 149 이후에 추가)

```python
# 위치: Line 149 (for i, pdf_info in enumerate... 다음, try 블록 시작 직후)

        try:
            print(f"  [{i}/{len(pdf_files)}] {pdf_info['filename']}", end=" ... ")

            # 🆕 Try hybrid parsing first
            if hybrid_integration:
                try:
                    hybrid_result = hybrid_integration.parse_dn_with_routing(
                        pdf_info["pdf_path"],
                        shipment_ref=pdf_info.get("shipment_ref", "")
                    )

                    # Convert to DSVPDFParser-compatible format
                    result = {
                        "header": {
                            "doc_type": "DN",
                            "parse_status": "SUCCESS",
                            "file_path": hybrid_result["file_path"]
                        },
                        "raw_text": hybrid_result.get("text", ""),
                        "data": {
                            "loading_point": hybrid_result.get("origin", ""),
                            "destination": hybrid_result.get("destination", ""),
                            "vehicle_type": hybrid_result.get("vehicle_type", ""),
                            "waybill_no": hybrid_result.get("do_number", ""),
                            "destination_code": hybrid_result.get("destination_code", ""),
                            "capacity": DN_CAPACITY_DEFAULT
                        },
                        "meta": {
                            "folder": pdf_info["folder"],
                            "filename": pdf_info["filename"],
                            "shipment_ref_from_folder": pdf_info["shipment_ref"],
                            "routing_metadata": hybrid_result.get("routing_metadata", {})
                        }
                    }

                    parsed_results.append(result)
                    print("✅ (hybrid)")
                    continue  # Skip to next file

                except Exception as hybrid_error:
                    print(f"⚠️  Hybrid failed, fallback: {str(hybrid_error)[:30]}")
                    # Fall through to existing DSVPDFParser logic below

            # 기존 DSVPDFParser 로직 시작 (아래 코드 그대로 유지)
            result = parser.parse_pdf(
                pdf_path=pdf_info["pdf_path"], doc_type="DN"
            )

            # ... 나머지 기존 코드 그대로 ...
```

#### 수정 4: parse_dn_pdfs 함수 끝 (Line 215 이후에 추가)

```python
# 위치: Line 215 (success_count 출력 다음)

    print(
        f"\n✅ 파싱 완료: {success_count}/{len(pdf_files)} 성공 ({success_count/len(pdf_files)*100:.1f}%)"
    )

    # 🆕 Print hybrid routing statistics
    if hybrid_integration:
        hybrid_integration.print_summary()

    return parsed_results
```

### Phase 3: 테스트 실행 (10분)

```bash
# 단일 파일 테스트
python validate_sept_2025_with_pdf.py 2>&1 | head -100

# 예상 출력:
# ================================================================================
# 9월 2025 Domestic 인보이스 + PDF 통합 검증
# ================================================================================
# ✨ Hybrid Docling/ADE integration enabled
#
# 📂 Step 1: Supporting Documents 스캔...
# ✅ 발견된 DN PDF: 36개
#
# 📄 Step 2: DN PDF 파싱...
# ✨ Using Hybrid Docling/ADE routing for DN parsing...
#
# 📄 DN PDF 파싱 시작... (총 36개)
#   [1/36] HVDC-DSV-SKM-MOSB-212_DN.pdf ...
#   🔀 Routing [HVDC-DSV-SKM-MOSB-212_DN.pdf] to DOCLING (rule: standard_documents_docling)
#   ✅ (hybrid)
#   [2/36] ...
```

### Phase 4: 결과 검증 (5분)

```bash
# 전체 실행
python validate_sept_2025_with_pdf.py > output.log 2>&1

# 핵심 메트릭 확인
grep "파싱 완료:" output.log
grep "DOMESTIC HYBRID INTEGRATION SUMMARY" output.log -A 20

# 예상 결과:
# ✅ 파싱 완료: 35/36 성공 (97.2%)  ← 개선!
#
# 📊 DOMESTIC HYBRID INTEGRATION SUMMARY
# ======================================================================
# 📄 Parsing Statistics:
#   Total Attempts: 36
#   Successes: 36
#   Failures: 0
#   Success Rate: 100.0%
#
# 🔀 Routing Statistics:
#   Total Routes: 36
#   ADE Routes: 8 (22.2%)
#   Docling Routes: 28 (77.8%)
#   Total ADE Cost: $2.40
```

---

## 코드 수정 체크리스트

### 수정 전 확인사항

- [ ] `Core_Systems/hybrid_pdf_integration.py` 파일 존재 확인
- [ ] `00_Shared/hybrid_integration/` 디렉토리 존재 확인
- [ ] `validate_sept_2025_with_pdf.py` 백업 완료
- [ ] Python 환경 활성화 (필요 시)

### 수정 체크리스트

- [ ] **Import 섹션** (Line ~60): HYBRID_INTEGRATION_AVAILABLE 추가
- [ ] **parse_dn_pdfs 초기화** (Line ~143): hybrid_integration 객체 생성
- [ ] **For loop 시작** (Line ~149): Hybrid parsing 시도 블록 추가
- [ ] **함수 끝** (Line ~215): print_summary() 호출 추가

### 테스트 체크리스트

- [ ] Import 오류 없이 실행됨
- [ ] Hybrid integration 초기화 성공 메시지 출력
- [ ] DN PDF 파싱 시 routing 로그 출력
- [ ] 최소 1개 PDF가 "✅ (hybrid)" 표시
- [ ] 기존 enhanced matching 정상 작동
- [ ] 최종 Excel 결과 파일 생성
- [ ] Hybrid summary 통계 출력

---

## 롤백 방법

### 즉시 롤백 (< 1분)

```python
# validate_sept_2025_with_pdf.py Line ~62
# 단순히 플래그를 False로 변경
HYBRID_INTEGRATION_AVAILABLE = False  # Force disable
```

### 완전 롤백 (< 2분)

```bash
# 백업에서 복원
cp validate_sept_2025_with_pdf.py.backup validate_sept_2025_with_pdf.py

# 재실행
python validate_sept_2025_with_pdf.py
```

---

## Troubleshooting

### Issue 1: "Hybrid integration not available"

**원인**: Import 경로 오류

**해결**:
```bash
# 경로 확인
ls 00_Shared/hybrid_integration/__init__.py
ls Core_Systems/hybrid_pdf_integration.py

# Python path 확인
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue 2: "DOMESTIC utils not available"

**원인**: src/utils import 실패

**해결**:
```bash
# 현재 디렉토리 확인
pwd  # Should be in 02_DSV_DOMESTIC

# Utils 파일 확인
ls src/utils/pdf_text_fallback.py
ls src/utils/pdf_extractors.py
```

### Issue 3: Parsing failures increase

**원인**: Hybrid logic 오류

**즉시 조치**:
```python
# Line ~62
HYBRID_INTEGRATION_AVAILABLE = False  # Disable hybrid
```

**영구 해결**: 백업 복원

---

## 예상 결과

### Console Output 예시

```
================================================================================
9월 2025 Domestic 인보이스 + PDF 통합 검증
================================================================================
✨ Hybrid Docling/ADE integration enabled

📂 Step 1: Supporting Documents 스캔...
✅ 발견된 DN PDF: 36개

📄 Step 2: DN PDF 파싱...
✨ Using Hybrid Docling/ADE routing for DN parsing...

📄 DN PDF 파싱 시작... (총 36개)
  [1/36] HVDC-DSV-SKM-MOSB-212_DN.pdf ...
  🔀 Routing [HVDC-DSV-SKM-MOSB-212_DN.pdf] to DOCLING (rule: standard_documents_docling, confidence: 0.90)
  🔧 Docling selected - using local fallback parsing
  ✅ (hybrid)

  [2/36] HVDC-DSV-PRE-MIR-SHU-DAS-AGI-213_DN.pdf ...
  🔀 Routing [...] to ADE (rule: dn_multi_page, confidence: 0.93)
  📡 ADE selected - using enhanced fallback (ADE API pending)
  ✅ (hybrid)

  ... [34 more] ...

✅ 파싱 완료: 36/36 성공 (100.0%)

======================================================================
📊 DOMESTIC HYBRID INTEGRATION SUMMARY
======================================================================

📄 Parsing Statistics:
  Total Attempts: 36
  Successes: 36
  Failures: 0
  Success Rate: 100.0%

🔀 Routing Statistics:
  Total Routes: 36
  ADE Routes: 8 (22.2%)
  Docling Routes: 28 (77.8%)
  Total ADE Cost: $2.40

💰 Budget Status (Date: 2025-10-14):
  Daily Limit: $50.00
  Used: $2.40
  Remaining: $47.60
  Usage: 4.8%
======================================================================
```

---

## 성공 기준

### Minimum Viable Integration (최소 성공 조건)

- [ ] 코드 실행 오류 없음
- [ ] PDF 파싱 성공률 ≥ 91.7% (현재와 동일 이상)
- [ ] Enhanced matching 정상 작동
- [ ] Excel 결과 파일 생성
- [ ] Hybrid 통계 출력

### Target Goals (목표)

- [ ] PDF 파싱 성공률 ≥ 95%
- [ ] ADE 라우팅 20-30%
- [ ] ADE 일일 비용 <$10
- [ ] 처리 시간 <15초

---

## 다음 실행 단계

### 1. 준비 완료 상태 확인

```bash
cd 02_DSV_DOMESTIC

# 필수 파일 확인
ls Core_Systems/hybrid_pdf_integration.py  # ✅ 생성 완료
ls ../00_Shared/hybrid_integration/*.py     # ✅ 생성 완료
ls validate_sept_2025_with_pdf.py          # ✅ 존재
```

### 2. 코드 수정 실행

위 Step 1, 2, 3 가이드대로 수정:
1. Import 추가 (4줄)
2. parse_dn_pdfs 함수 수정 (hybrid 블록 추가, ~40줄)
3. print_summary 호출 추가 (1줄)

**총 수정량**: ~45줄 추가, 0줄 삭제

### 3. 실행 및 검증

```bash
python validate_sept_2025_with_pdf.py
```

---

**Status**: 📝 단계별 가이드 완료 - 실행 준비 완료
**Confidence**: ⭐⭐⭐⭐⭐ (Very High - Backward compatible with automatic fallback)
**Risk**: 🟢 Low (기존 로직 완전 보존)

