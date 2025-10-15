# Quick Start Guide - 5분 완성 가이드

**대상**: DOMESTIC 인보이스 검증 시스템 첫 사용자
**목표**: 5분 내 시스템 이해 및 실행
**난이도**: ⭐☆☆☆☆ (매우 쉬움)

---

## 1분: 시스템 이해

### 무엇을 하는 시스템인가?

```
📊 Invoice Excel (44건) + 🗺️ ApprovedLaneMap (124 레인) + 📄 DN PDF (36개)
                              ↓
            🔍 자동 매칭 + 검증 (95.5% 성공률)
                              ↓
        📈 검증 완료 Excel + 📊 상세 분석 리포트
```

**핵심 기능**:
1. Enhanced Lane Matching (4-level fallback)
2. Hybrid PDF Parsing (Docling/ADE intelligent routing)
3. Cross-Document Validation (1:1 greedy matching)

**최종 성과**: 95.5% 자동 매칭, FAIL 0%, Destination 유사도 0.971

---

## 2분: 환경 설정

### 필수 패키지

```bash
pip install pandas openpyxl
```

### 선택 패키지 (성능 향상)

```bash
pip install PyMuPDF  # PDF 처리 15-35배 가속
```

---

## 1분: 실행

### 기본 실행

```bash
cd 02_DSV_DOMESTIC
python validate_domestic_with_pdf.py
```

### 고급 실행 (권장)

```bash
# DN Capacity 자동 증가 활성화
export DN_AUTO_CAPACITY_BUMP=true
export DN_MAX_CAPACITY=16

python validate_domestic_with_pdf.py
```

**실행 시간**: 약 8분 (44개 인보이스 처리)

---

## 1분: 결과 확인

### Excel 파일

```
Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx
```

**주요 시트**:
- `items`: 44개 인보이스 검증 결과 (25+ columns)
- `ApprovedLaneMap`: 124개 레인 (하이퍼링크 대상)
- `DN_Validation`: 상세 검증 내역

**핵심 컬럼**:
- `ref_adj`: 매칭된 요율 (하이퍼링크 클릭 가능!)
- `dn_matched`: Yes/No
- `dn_validation_status`: PASS/WARN/FAIL
- `dn_dest_similarity`: Destination 유사도
- `hybrid_engine`: Docling or ADE (NEW)
- `hybrid_confidence`: Parsing 신뢰도 (NEW)

### 리포트

```
Results/Sept_2025/Reports/SEPT_2025_COMPLETE_VALIDATION_REPORT.md
```

**포함 내용**:
- 전체 통계
- 매칭 결과
- 미매칭 분석
- 권장 조치

---

## 보너스: 주요 설정

### DN Capacity 관리

```bash
DN_AUTO_CAPACITY_BUMP=true   # 자동 용량 증가 (권장!)
DN_MAX_CAPACITY=16           # 최대 용량 (기본 16)
DN_CAPACITY_DEFAULT=1        # 기본 용량
```

### 유사도 임계값

```bash
DN_ORIGIN_THR=0.27    # Origin 유사도 (유연)
DN_DEST_THR=0.50      # Destination 유사도 (중간)
DN_VEH_THR=0.30       # Vehicle 유사도 (유연)
DN_MIN_SCORE=0.40     # 최소 매칭 점수
```

### PDF 추출 우선순위

```bash
DN_USE_PDF_FIELDS_FIRST=true  # PDF 본문 우선 (권장!)
```

---

## 문제 해결

### PDF 파싱 실패 시

```bash
# PyMuPDF 설치 확인
pip install PyMuPDF

# 실행 재시도
python validate_domestic_with_pdf.py
```

### 매칭률이 낮을 때

```bash
# DN Capacity 증가
export DN_MAX_CAPACITY=20

# 재실행
python validate_domestic_with_pdf.py
```

### Hybrid Integration 비활성화

```python
# validate_domestic_with_pdf.py Line ~62
HYBRID_INTEGRATION_AVAILABLE = False  # Force disable
```

---

## 다음 단계

### 상세 가이드
- [USER_GUIDE.md](../02_GUIDES/USER_GUIDE.md) - 전체 사용자 가이드
- [DEVELOPMENT_GUIDE.md](../02_GUIDES/DEVELOPMENT_GUIDE.md) - 개발자 가이드

### 시스템 이해
- [SYSTEM_ARCHITECTURE.md](../01_ARCHITECTURE/SYSTEM_ARCHITECTURE.md) - 아키텍처
- [SYSTEM_ARCHITECTURE_DIAGRAM.md](../01_ARCHITECTURE/SYSTEM_ARCHITECTURE_DIAGRAM.md) - 다이어그램

### Hybrid Integration
- [HYBRID_INTEGRATION_ARCHITECTURE.md](../01_ARCHITECTURE/HYBRID_INTEGRATION_ARCHITECTURE.md) - Hybrid 상세 아키텍처
- [INTEGRATION_COMPLETE.md](../../INTEGRATION_COMPLETE.md) - 통합 완료 보고서

---

**작성일**: 2025-10-14
**버전**: v1.0
**난이도**: ⭐☆☆☆☆
**예상 시간**: 5분

