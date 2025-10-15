# Hybrid Artifacts v1 직접 실행 완료 보고서

**날짜**: 2025-10-15
**작업자**: AI Assistant
**프로젝트**: HVDC Invoice Audit - Samsung C&T Logistics

---

## 1. 요약

### 목표
- `hybrid_doc_system_artifacts_v1` 폴더의 고급 PDF 파싱 기능 통합
- At Cost 17건의 PDF Total Amount 추출률 향상
- 전체 PASS rate 개선

### 완료 상황
✅ **코드 구현 100% 완료**
- `_parse_number()` Helper 메서드
- `_extract_total_with_coordinates()` 좌표 기반 추출 (118 lines)
- `_parse_with_ade()` Fallback 통합
- `extract_invoice_data()` Summary 블록 처리

❓ **실행 테스트 일부 실패**
- 단위 테스트 (PDF 좌표 추출): **실패** (Total Amount 라벨 우측/아래에 금액 없음)
- E2E 검증 (기존 시스템): **성공** (PASS 52.0%)
- At Cost 17건 상태: **기존 Summary 추출 사용 중**

---

## 2. 구현 완료 항목

### A. celery_app.py (3개 메서드 추가)

#### 1. `_parse_number(value_str: str) -> float` (Line 267-288)
```python
def _parse_number(value_str: str) -> float:
    """
    숫자 파싱 Helper (쉼표 제거, 기본값 0.0)
    """
    try:
        cleaned = str(value_str).replace(",", "").replace(" ", "").strip()
        cleaned = cleaned.replace("$", "").replace("AED", "").replace("USD", "")

        if not cleaned or cleaned == "-" or cleaned.lower() in ["n/a", "na", "none"]:
            return 0.0

        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0
```

#### 2. `_extract_total_with_coordinates(pdf_file: Path) -> Optional[Dict]` (Line 291-408)
**전략**:
- `pdfplumber.extract_words()` 기반 bbox 좌표 추출
- "Total Amount" 라벨 찾기
- 2단계 검색:
  1. **우측 검색**: `x1 + 10~200px`, y tolerance `±5px`
  2. **아래 검색**: `y1 + 5~50px`, x tolerance `±20px`
- AED 통화 감지 (±50px 범위)
- Minimum amount: `> 10`

**코드 예시**:
```python
# 우측 영역 검색
for w in words[i+2:]:
    if w["x0"] >= x1 + 10 and w["x0"] <= x1 + 200:
        if abs(w["top"] - y0) <= 5:  # Same line
            amount = _parse_number(w["text"])
            if amount > 10:
                return {
                    "total_amount": amount,
                    "currency": currency,
                    "bbox": {...},
                    "extraction_method": "coordinate_right"
                }
```

#### 3. `_parse_with_ade()` Fallback 통합 (Line 242-253)
```python
# Coordinate-based Total Amount Fallback (NEW)
total_info = _extract_total_with_coordinates(pdf_file)
if total_info:
    unified_ir["blocks"].append({
        "type": "summary",
        "total_amount": total_info["total_amount"],
        "currency": total_info["currency"],
        "bbox": total_info["bbox"],
        "extraction_method": total_info["extraction_method"]
    })
```

### B. unified_ir_adapter.py (Summary 블록 처리)

**`extract_invoice_data()` 수정** (Line 141-153):
```python
# Fallback: Summary 블록 (우선순위 2: 좌표 기반)
for block in blocks:
    if block.get("type") == "summary" and block.get("total_amount"):
        if not summary.get("total"):
            summary["total"] = block["total_amount"]
            currency = block.get("currency", "USD")

            # AED → USD 변환
            if currency == "AED" and not any("USD" in b.get("text", "") for b in blocks):
                summary["total"] = round(summary["total"] / 3.67, 2)
```

---

## 3. 실행 테스트 결과

### 3.1 Redis 상태 확인
✅ **성공**: `redis-cli ping` → `PONG`

### 3.2 단위 테스트 (좌표 기반 Total Amount 추출)
❌ **실패**: `[FAIL] Total 추출 실패`

**원인 분석**:
- 테스트 PDF: `HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf`
- "Total Amount:" 라벨 위치: `x=312.90~381.31, y=692.51~703.51` (Word Index 298-299)
- **우측에 숫자 없음**: 라벨 우측 (x > 381.31) 영역에 단어 0개
- **아래에도 숫자 없음**: 라벨 아래 30px 영역에 숫자 형식 단어 0개

**PDF 구조 특성**:
- "Total Amount:" 라벨은 페이지 좌측에 위치
- 실제 금액은 **페이지 오른쪽 끝 (x > 500)** 또는 **별도 표 영역**에 위치
- 현재 알고리즘 (우측 10-200px, 아래 5-50px)으로는 **탐지 불가**

### 3.3 E2E 검증 (기존 시스템)
✅ **성공**:
```
Total items: 102
PASS: 53 (52.0%)
REVIEW_NEEDED: 28 (27.5%)
FAIL: 21 (20.6%)

RATE SOURCE:
- CONTRACT: 64건
- DUTY: 21건
- AT COST: 17건 (대문자)

Gate PASS: 54/102 (52.9%)
```

### 3.4 At Cost 17건 현황
- **기존 시스템**: `_extract_summary_section()` (정규식 기반) 사용 중
- **좌표 기반 Fallback**: 아직 미작동 (단위 테스트 실패로 인해 Fallback 우선순위 미도달)

---

## 4. 문제점 및 해결 방안

### 문제 1: PDF 레이아웃 다양성
**문제**: CMA CGM 인보이스는 "Total Amount:" 라벨과 금액이 **물리적으로 멀리 떨어져 있음** (라벨: 좌측, 금액: 우측 끝)

**현재 알고리즘 한계**:
```python
# 우측 검색: x1 + 10~200px (최대 200px 이내)
# 실제 거리: 300px 이상
```

**해결 방안**:
1. **검색 범위 확대**: `x1 + 10px ~ 페이지 너비` (예: 600px)
2. **Y축 허용 범위 확대**: `±10px` (현재 ±5px)
3. **페이지 전체 숫자 검색**: 우측 절반 (x > 300) 영역의 모든 숫자 중 **최대값** 선택

### 문제 2: 정규식 vs 좌표 기반 우선순위
**현황**:
- `_extract_summary_section()` (정규식) = 우선순위 1
- `Summary 블록` (좌표) = 우선순위 2

**문제**: 정규식이 이미 Total을 추출하면 좌표 기반 Fallback **실행되지 않음**

**해결 방안**:
- 정규식 실패 시에만 좌표 기반 사용 (**현재 구조 유지**)
- 또는 **두 방법 모두 실행 후 검증 로직 추가**

### 문제 3: Optional import 누락
✅ **수정 완료**: `from typing import Dict, Any, Optional`

---

## 5. 최종 상태

### 코드 상태
| 항목 | 상태 | 위치 |
|------|------|------|
| `_parse_number` | ✅ 완료 | celery_app.py:267-288 |
| `_extract_total_with_coordinates` | ✅ 완료 | celery_app.py:291-408 |
| Fallback 통합 | ✅ 완료 | celery_app.py:242-253 |
| Summary 블록 처리 | ✅ 완료 | unified_ir_adapter.py:141-153 |

### 테스트 상태
| 테스트 | 결과 | 상세 |
|--------|------|------|
| Redis | ✅ PASS | PONG 응답 |
| 단위 테스트 | ❌ FAIL | Total Amount 좌표 탐지 실패 |
| E2E 검증 | ✅ PASS | 기존 시스템 정상 (52.0%) |
| At Cost 17건 | ⏳ 대기 | 좌표 알고리즘 개선 필요 |

### 시스템 상태
- **기존 Summary 추출**: 정상 작동 (정규식 기반)
- **좌표 기반 Fallback**: 구현 완료, 단 검색 범위 확대 필요
- **At Cost 검증률**: 현재 0% (정규식 실패 시) → **목표 70-80%** (좌표 기반 개선 후)

---

## 6. 다음 단계 (권장)

### Phase 1: 좌표 검색 알고리즘 개선 (즉시)
**수정 사항**:
```python
# celery_app.py:_extract_total_with_coordinates()

# 1. 우측 검색 범위 확대 (200px → 600px)
if w["x0"] >= x1 + 10 and w["x0"] <= 600:  # 페이지 전체 너비

# 2. Y축 허용 범위 확대 (±5px → ±10px)
if abs(w["top"] - y0) <= 10:

# 3. 페이지 우측 절반 전체 스캔
right_side_numbers = [
    _parse_number(w["text"]) for w in words
    if w["x0"] > 300 and abs(w["top"] - y0) <= 15
]
if right_side_numbers:
    amount = max(right_side_numbers)
```

**예상 효과**: Total Amount 탐지율 **30-50%**

### Phase 2: 테이블 기반 추출 추가 (2-3일)
**전략**:
- `pdfplumber.extract_tables()` 사용
- 마지막 표의 마지막 행/열에서 최대 금액 추출
- 예상 효과: **+20-30%**

### Phase 3: OCR Fallback (선택적)
- `pytesseract` 또는 `EasyOCR` 통합
- 페이지 우측 하단 영역 OCR
- 예상 효과: **+10-20%**

---

## 7. 결론

### 달성한 것
✅ **코드 구현 100% 완료**: 좌표 기반 Total Amount 추출 로직 구현
✅ **Optional import 수정**: 타입 힌팅 오류 해결
✅ **E2E 검증 성공**: 기존 시스템 정상 작동 확인 (PASS 52.0%)
✅ **At Cost 17건 확인**: "AT COST" (대문자) 데이터 존재 확인

### 달성하지 못한 것
❌ **단위 테스트 실패**: PDF 레이아웃 특성상 좌표 탐지 실패
❌ **At Cost 개선 미검증**: 알고리즘 개선 전까지 효과 측정 불가

### 권장 사항
1. **좌표 검색 범위 확대** (우선순위 1)
2. **테이블 기반 추출 추가** (우선순위 2)
3. **다양한 PDF 샘플 테스트** (우선순위 3)

---

**보고서 작성**: 2025-10-15 01:58 AM
**작성자**: AI Assistant
**프로젝트**: HVDC Invoice Audit System

