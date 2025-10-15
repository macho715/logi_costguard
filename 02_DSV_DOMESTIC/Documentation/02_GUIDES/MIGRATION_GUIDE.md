# Migration Guide - 다른 월 인보이스 적용 가이드

**대상**: 10월, 11월 등 다른 월 DOMESTIC 인보이스
**소요 시간**: 약 30분
**난이도**: ⭐⭐☆☆☆ (보통)

---

## 📋 Prerequisites

### 검증 완료 사항
- ✅ 9월 2025 데이터로 95.5% 매칭률 달성
- ✅ Hybrid Integration 정상 작동 확인
- ✅ 모든 의존성 검증 완료
- ✅ ARCHIVE 시스템 작동 확인

### 시스템 요구사항
- Python 3.8+
- 필수 패키지: pandas, openpyxl
- 권장 패키지: PyMuPDF (성능 향상)
- Hybrid Integration (선택): 00_Shared/hybrid_integration/

---

## 🚀 Step-by-Step Migration

### Step 1: 데이터 준비 (10분)

#### 1.1 Invoice Excel 파일
**위치**: `Data/DSV {YYYYMM}/`
**파일명 패턴**: `SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY {MONTH} {YEAR}.xlsx`

**필수 컬럼**:
- `origin` (Loading Point)
- `destination` (Delivery Point)
- `vehicle` (Vehicle Type)
- `rate` (요율)
- `distance` (거리)

**예시**:
```
Data/DSV 202510/SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY OCTOBER 2025.xlsx
```

#### 1.2 Supporting Documents (DN PDFs)
**위치**: `Data/DSV {YYYYMM}/SCNT Domestic ({Month} {YEAR}) - Supporting Documents/`

**파일명 패턴**:
- `HVDC-{PROJECT}-{CODE}-{NUMBER}_DN.pdf`
- `HVDC-{PROJECT}-{CODE}-{NUMBER}_DAS_DN (DSV-{LOCATION}).pdf`

**예시 폴더**:
```
Data/DSV 202510/SCNT Domestic (Oct 2025) - Supporting Documents/
├── HVDC-DSV-SKM-MOSB-300_DN.pdf
├── HVDC-DSV-PRE-MIR-301_DN.pdf
└── ... (약 30-40개)
```

#### 1.3 ApprovedLaneMap JSON
**위치**: 기존 파일 재사용 가능
**파일**: `ApprovedLaneMap_ENHANCED.json`

**확인 사항**:
- 124 레인 포함 여부
- 새로운 레인 추가 필요 시 업데이트

---

### Step 2: 스크립트 파일명 변경 (5분)

#### 2.1 메인 스크립트 복사
```bash
cd 02_DSV_DOMESTIC

# 현재 스크립트 백업 (참조용)
cp validate_domestic_with_pdf.py ARCHIVE/backups/validate_domestic_with_pdf_$(date +%Y%m%d).py

# 새로운 월 적용 시에는 동일한 스크립트 사용 (범용 스크립트)
```

#### 2.2 주요 경로 수정
**파일**: `validate_oct_2025_with_pdf.py`

**Line ~1462** (Supporting Documents 경로):
```python
# Before
supporting_docs_dir = "Data/DSV 202509/SCNT Domestic (Sept 2025) - Supporting Documents"

# After
supporting_docs_dir = "Data/DSV 202510/SCNT Domestic (Oct 2025) - Supporting Documents"
```

**Line ~1464** (Input Excel):
```python
# Before
enhanced_matching_excel = "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_20251013_231013.xlsx"

# After
enhanced_matching_excel = "Results/Oct_2025/domestic_oct_2025_FINAL_WITH_PDF_VALIDATION_{latest}.xlsx"
# 또는 실제 파일명으로 교체
```

**Line ~1465** (Output Report):
```python
# Before
output_report = "Results/Sept_2025/Reports/SEPT_2025_COMPLETE_VALIDATION_REPORT.md"

# After
output_report = "Results/Oct_2025/Reports/OCT_2025_COMPLETE_VALIDATION_REPORT.md"
```

**Line ~1509** (Final Excel):
```python
# Before
final_excel = f"Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_{timestamp_suffix}.xlsx"

# After
final_excel = f"Results/Oct_2025/domestic_oct_2025_FINAL_WITH_PDF_VALIDATION_{timestamp_suffix}.xlsx"
```

---

### Step 3: 폴더 구조 생성 (3분)

```bash
# Results 폴더 생성
mkdir -p Results/Oct_2025/Reports
mkdir -p Results/Oct_2025/Logs

# 10월 데이터 폴더 확인
ls "Data/DSV 202510/SCNT Domestic (Oct 2025) - Supporting Documents/"
# → PDF 파일들이 존재하는지 확인
```

---

### Step 4: Enhanced Lane Matching 실행 (선택, 5분)

10월 인보이스에 대해 먼저 Enhanced Lane Matching을 실행합니다:

```bash
python enhanced_matching.py  # 또는 별도 스크립트
```

**주의**: `enhanced_matching.py`는 범용적이므로 입력 파일 경로만 수정하면 됩니다.

---

### Step 5: 실행 및 검증 (10분)

#### 5.1 환경변수 설정 (권장)

```bash
# Windows PowerShell
$env:DN_AUTO_CAPACITY_BUMP="true"
$env:DN_MAX_CAPACITY="16"
$env:DN_USE_PDF_FIELDS_FIRST="true"

# Linux/Mac
export DN_AUTO_CAPACITY_BUMP=true
export DN_MAX_CAPACITY=16
export DN_USE_PDF_FIELDS_FIRST=true
```

#### 5.2 실행

```bash
python validate_oct_2025_with_pdf.py
```

**예상 출력**:
```
================================================================================
10월 2025 Domestic 인보이스 + PDF 통합 검증
================================================================================
[HYBRID] Docling/ADE integration enabled

📂 Step 1: Supporting Documents 스캔...
✅ 발견된 DN PDF: {N}개

📄 Step 2: DN PDF 파싱...
[HYBRID] Using Hybrid Docling/ADE routing for DN parsing...
  [1/{N}] ... ✅ (hybrid)
  ...

✅ 파싱 완료: {M}/{N} 성공

📊 DOMESTIC HYBRID INTEGRATION SUMMARY
  Total Attempts: {N}
  Successes: {M}
  ADE Routes: {X}
  Docling Routes: {Y}
  Total ADE Cost: ${Z}

🔍 Step 3: Cross-Document 검증...
✅ 매칭: {K}/{Total} ({%}%)

📊 Step 4: Excel에 PDF 검증 결과 통합...
✅ 생성: Results/Oct_2025/domestic_oct_2025_FINAL_WITH_PDF_VALIDATION_{timestamp}.xlsx
```

#### 5.3 결과 확인

**Excel 파일**:
```
Results/Oct_2025/domestic_oct_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx
```

**확인 항목**:
- [ ] items 시트: 모든 컬럼 정상
- [ ] ApprovedLaneMap 시트: 하이퍼링크 작동
- [ ] DN_Validation 시트: 검증 상세
- [ ] Hybrid columns: hybrid_engine, hybrid_confidence 등
- [ ] 매칭률 ≥ 90%
- [ ] FAIL 비율 ≤ 5%

---

## 🔧 Troubleshooting

### Issue 1: PDF 파일을 찾을 수 없음

**증상**:
```
📂 Step 1: Supporting Documents 스캔...
❌ 발견된 DN PDF: 0개
```

**해결**:
1. 폴더 경로 확인:
   ```bash
   ls "Data/DSV 202510/SCNT Domestic (Oct 2025) - Supporting Documents/"
   ```
2. 스크립트의 `supporting_docs_dir` 경로 재확인
3. 폴더명 정확히 일치하는지 확인 (대소문자 구분)

### Issue 2: Enhanced Matching Excel 파일 없음

**증상**:
```
FileNotFoundError: Results/Oct_2025/domestic_oct_2025_FINAL_WITH_PDF_VALIDATION...
```

**해결**:
1. Enhanced Matching 먼저 실행
2. 또는 `enhanced_matching_excel` 경로를 실제 파일로 수정

### Issue 3: 매칭률이 낮음 (< 70%)

**원인**: DN Capacity 부족

**해결**:
```bash
# MAX_CAPACITY 증가
export DN_MAX_CAPACITY=20

# 재실행
python validate_oct_2025_with_pdf.py
```

### Issue 4: Hybrid Integration 실패

**증상**:
```
[WARNING] Hybrid integration not available
```

**해결**:
1. 00_Shared/hybrid_integration/ 폴더 확인
2. Core_Systems/hybrid_pdf_integration.py 존재 확인
3. Import 오류 확인:
   ```bash
   python -c "from Core_Systems.hybrid_pdf_integration import *"
   ```

---

## 📊 예상 성능 (9월 대비)

### 유사한 성능 예상
- **매칭률**: 90-95% (DN 수에 따라 변동)
- **PDF 파싱**: 85-95%
- **FAIL 비율**: 0-5%
- **Dest 유사도**: 0.95+

### 가변 요소
- DN PDF 개수: 30-40개 예상
- Invoice 항목 수: 40-50개 예상
- 새로운 레인 출현: ApprovedLaneMap 업데이트 필요

---

## 🎯 성공 기준

### Minimum Viable (최소 성공)
- [ ] 스크립트 오류 없이 완료
- [ ] Excel 파일 생성
- [ ] 매칭률 ≥ 70%
- [ ] PDF 파싱 ≥ 80%

### Target Goal (목표)
- [ ] 매칭률 ≥ 90%
- [ ] FAIL 비율 ≤ 5%
- [ ] PDF 파싱 ≥ 90%
- [ ] Hybrid routing 작동

### Excellent (우수)
- [ ] 매칭률 ≥ 95%
- [ ] FAIL 비율 = 0%
- [ ] PDF 파싱 ≥ 95%
- [ ] Dest 유사도 ≥ 0.95

---

## 🔄 Rollback Plan

### 문제 발생 시 복구

**Option 1: 9월 스크립트로 복귀**
```bash
# 9월 데이터로 재실행하여 시스템 정상 확인
python validate_domestic_with_pdf.py
```

**Option 2: Hybrid 비활성화**
```python
# validate_oct_2025_with_pdf.py Line ~62
HYBRID_INTEGRATION_AVAILABLE = False  # Force disable
```

**Option 3: 백업에서 복원**
```bash
# 백업 파일 목록 확인
ls ARCHIVE/backups/validate_domestic_with_pdf_*.py

# 가장 최근 백업으로 복원
cp ARCHIVE/backups/validate_domestic_with_pdf_20251014.py validate_domestic_with_pdf.py
```

---

## 📈 반복 적용 (11월, 12월...)

### 자동화 스크립트 (향후 개선)

```bash
#!/bin/bash
# run_validation.sh - 월별 자동 실행 스크립트

MONTH_CODE=$1  # 예: 202511
MONTH_NAME=$2  # 예: November

python validate_domestic.py \
  --month $MONTH_CODE \
  --month-name $MONTH_NAME \
  --dn-folder "Data/DSV $MONTH_CODE/SCNT Domestic ($MONTH_NAME 2025) - Supporting Documents" \
  --output "Results/${MONTH_NAME}_2025/"
```

### 설정 파일 기반 (향후 개선)

**config_oct_2025.json**:
```json
{
  "month": "202510",
  "month_name": "Oct",
  "year": "2025",
  "paths": {
    "dn_folder": "Data/DSV 202510/SCNT Domestic (Oct 2025) - Supporting Documents",
    "output_folder": "Results/Oct_2025/"
  }
}
```

---

## ✅ Migration Checklist

### 데이터 준비
- [ ] Invoice Excel 파일 준비
- [ ] DN PDF 폴더 준비 (30-40개)
- [ ] ApprovedLaneMap 확인/업데이트

### 스크립트 수정
- [ ] 메인 스크립트 파일명 변경
- [ ] Line ~1462: supporting_docs_dir 경로 수정
- [ ] Line ~1464: enhanced_matching_excel 경로 수정
- [ ] Line ~1465: output_report 경로 수정
- [ ] Line ~1509: final_excel 경로 수정

### 폴더 구조
- [ ] Results/{MONTH}_2025/ 생성
- [ ] Results/{MONTH}_2025/Reports/ 생성
- [ ] Results/{MONTH}_2025/Logs/ 생성

### 실행 및 검증
- [ ] 환경변수 설정
- [ ] 스크립트 실행
- [ ] Excel 파일 생성 확인
- [ ] 매칭률 확인 (≥90% 목표)
- [ ] Hybrid 통계 확인

### 결과 분석
- [ ] items 시트 검토
- [ ] 미매칭 항목 분석
- [ ] 필요시 DN_MAX_CAPACITY 조정

---

## 🔍 핵심 하드코딩 위치

### validate_domestic_with_pdf.py

| Line | 현재 값 | 수정 필요 | 예시 (10월) |
|------|---------|----------|------------|
| ~1462 | Data/DSV 202509/... | ✅ Yes | Data/DSV 202510/... |
| ~1464 | Results/Sept_2025/... | ✅ Yes | Results/Oct_2025/... |
| ~1465 | .../SEPT_2025_... | ✅ Yes | .../OCT_2025_... |
| ~1509 | .../sept_2025_... | ✅ Yes | .../oct_2025_... |

### 기타 파일
- `enhanced_matching.py`: ✅ 범용 (수정 불필요)
- `src/utils/*.py`: ✅ 범용 (수정 불필요)
- `Core_Systems/hybrid_pdf_integration.py`: ✅ 범용 (수정 불필요)
- `config_domestic_v2.json`: ✅ 범용 (수정 불필요)

---

## 📊 예상 결과 비교

### 9월 2025 (Actual)
- Invoice 항목: 44개
- DN PDF: 36개
- 매칭률: 95.5% (42/44)
- FAIL: 0%
- Dest 유사도: 0.971

### 10월 2025 (예상)
- Invoice 항목: 40-50개 (예상)
- DN PDF: 30-40개 (예상)
- 매칭률: 90-95% (예상)
- FAIL: 0-5% (예상)
- Dest 유사도: 0.95+ (예상)

---

## 🎯 성공 사례 (9월 2025)

### 달성한 KPI
- ✅ 매칭률: **95.5%** (목표 90%)
- ✅ FAIL: **0%** (목표 ≤5%)
- ✅ PDF 파싱: **91.7%** (목표 ≥90%)
- ✅ Dest 유사도: **0.971** (목표 ≥0.90)
- ✅ Hybrid Success: **100%** (36/36)

### 핵심 요소
1. **DN_MAX_CAPACITY=16**: 수요 집중 대응
2. **PyMuPDF 우선**: PDF 파싱 품질 향상
3. **Hybrid Routing**: Docling 77.8%, ADE 22.2%
4. **1:1 Greedy Matching**: 최적 매칭 보장

---

## 📞 Support

### 문제 발생 시
1. [TROUBLESHOOTING 섹션](#troubleshooting) 확인
2. [USER_GUIDE.md](USER_GUIDE.md) FAQ 참조
3. 9월 데이터로 재실행하여 시스템 정상 확인

### 개선 제안
- 더 나은 마이그레이션 방법
- 자동화 스크립트 요청
- 설정 파일 기반 실행

---

**가이드 버전**: 1.0
**작성일**: 2025-10-14
**기준 시스템**: PATCH4 + Hybrid Integration
**검증 데이터**: 9월 2025 (95.5% 매칭률)

