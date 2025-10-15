# 좌표/테이블 추출 개선 완료 보고서

**날짜**: 2025-10-15
**프로젝트**: HVDC Invoice Audit - Samsung C&T Logistics

---

## 1. 구현 완료 요약

### Phase 1: 좌표 검색 알고리즘 개선 (완료)

#### 1.1 우측 검색 범위 확대
- **Before**: `x1 + 10px ~ x1 + 200px`
- **After**: `x1 + 10px ~ 600px` (페이지 전체 너비)
- **파일**: `celery_app.py` Line 366

#### 1.2 Y축 허용 범위 확대
- **Before**: `±5px`
- **After**: `±10px`
- **파일**: `celery_app.py` Line 367

#### 1.3 페이지 우측 절반 전체 스캔 추가
- **전략**: "Total Amount" 라벨과 같은 y축 (±15px)에서 x > 300인 모든 숫자 검색
- **로직**: 최대값 선택 (보통 Total Amount가 가장 큼)
- **파일**: `celery_app.py` Line 396-430 (35 lines)

### Phase 2: 테이블 기반 추출 추가 (완료)

#### 2.1 `_extract_total_from_table()` 메서드
- **전략**:
  1. `extract_tables()` 모든 테이블 추출
  2. 각 테이블의 모든 행 검사
  3. "TOTAL AMOUNT", "TOTAL VAT", "GRAND TOTAL" 등 키워드 포함 행 찾기
  4. 해당 행의 모든 셀에서 숫자 추출, 최대값 선택
- **파일**: `celery_app.py` Line 472-547 (76 lines)

#### 2.2 Fallback 전략 통합
- **우선순위**:
  1. Coordinate-based (우측 검색 + 우측 절반 스캔)
  2. Table-based (표 Summary 행 검색)
  3. 기존 정규식 (unified_ir_adapter.py)
- **파일**: `celery_app.py` Line 242-260

---

## 2. 테스트 결과

### 단위 테스트 (SCT-0126 PDF)
- **좌표 기반**: FAIL (y축 ±15px 내 숫자 없음)
- **테이블 기반**: FAIL (멀티라인 셀 구조)

### PDF 구조 분석
**HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf**:
```
Line 48: Total Amount:
Line 57: For Reference ( AED ) Total VAT:
Line 58: Total Amount:
```

**특성**:
- "Total Amount:" 라벨만 존재, 금액은 **별도 위치**
- Table 0, Row 6: `535.00` (line item, Total 아님)
- Table 1: 멀티라인 셀 구조, 파싱 복잡

**결론**: 이 PDF는 **정규식 기반 `_extract_summary_section()`에 의존**해야 함

---

## 3. 코드 변경 요약

### celery_app.py 수정 사항

| 항목 | Line | 변경 내용 |
|------|------|-----------|
| 우측 검색 범위 | 366 | 200px → 600px |
| Y축 허용 범위 | 367 | ±5px → ±10px |
| 우측 절반 스캔 | 396-430 | 신규 추가 (35 lines) |
| 테이블 추출 메서드 | 472-547 | `_extract_total_from_table()` (76 lines) |
| Fallback 전략 | 242-260 | 좌표 → 테이블 순서 통합 |

**총 변경**: +111 lines

---

## 4. 시스템 동작 흐름

### PDF Total Amount 추출 우선순위

```
1. [REGEX] _extract_summary_section() (unified_ir_adapter.py)
   ↓ 실패 시
2. [COORDINATE] _extract_total_with_coordinates()
   2-1. 우측 검색 (x1+10~600px, y ±10px)
   2-2. 우측 절반 스캔 (x>300, y ±15px, MAX)
   2-3. 아래 검색 (y1+5~50px, x ±20px)
   ↓ 실패 시
3. [TABLE] _extract_total_from_table()
   3-1. 모든 테이블의 모든 행 검사
   3-2. TOTAL 키워드 포함 행 찾기
   3-3. 해당 행의 최대 숫자 추출
   ↓ 실패 시
4. [DEFAULT] 0.0 또는 None
```

---

## 5. 예상 vs 실제

| 항목 | 예상 | 실제 (SCT-0126) | 비고 |
|------|------|-----------------|------|
| 좌표 기반 탐지 | 50-60% | 0% (실패) | 금액이 y축 ±15px 밖 |
| 테이블 기반 탐지 | 20-30% | 0% (실패) | 멀티라인 셀 복잡도 |
| 정규식 기반 | 기존 | 정상 작동 | 주 추출 방법 |

---

## 6. 한계 및 권장 사항

### 한계점
1. **CMA CGM 인보이스 레이아웃**: 라벨과 금액이 **y축으로도 멀리 떨어져 있음** (50px 이상)
2. **멀티라인 테이블 셀**: pdfplumber의 표 파싱이 복잡한 셀 병합 처리 미흡
3. **정규식 의존도**: 대부분의 PDF는 **정규식 기반 추출로 충분**

### 권장 사항
1. **정규식 기반 유지**: 현재 `_extract_summary_section()`이 가장 안정적
2. **좌표/테이블 Fallback**: 정규식 실패 시에만 사용 (현재 구조 유지)
3. **다양한 PDF 샘플 테스트**: At Cost 17건 중 다른 PDF로 검증 필요
4. **Y축 범위 추가 확대**: ±15px → ±30px 또는 페이지 전체 (선택적)

---

## 7. 다음 단계

### 즉시 실행 가능
1. **E2E 검증**: `masterdata_validator.py` 실행 (102 items)
2. **At Cost 17건 분석**: 실제 개선 효과 측정
3. **다른 PDF 샘플 테스트**: SCT-0127, SCT-0122 등

### 선택적 개선
1. **Y축 범위 확대**: ±30px 또는 ±50px (매우 공격적)
2. **OCR Fallback**: pytesseract 통합 (최후 수단)
3. **ML 기반 추출**: Layout Analysis 모델 (장기 과제)

---

## 8. 결론

✅ **코드 구현 100% 완료**:
- 좌표 검색 범위 확대 (200px → 600px, ±5px → ±10px)
- 페이지 우측 절반 스캔 추가
- 테이블 기반 추출 메서드 추가
- Multi-strategy Fallback 통합

⚠️ **SCT-0126 PDF 한계**:
- 특수한 레이아웃으로 인해 좌표/테이블 추출 실패
- 정규식 기반 추출로 정상 처리 중

🎯 **권장**: 다른 At Cost PDF 샘플로 추가 검증 필요

---

**작성**: 2025-10-15 02:05 AM
**작성자**: AI Assistant

