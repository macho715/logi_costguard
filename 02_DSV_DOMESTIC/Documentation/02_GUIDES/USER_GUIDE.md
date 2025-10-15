# 사용자 가이드 (User Guide)

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**대상**: 시스템 운영자, 감사자
**버전**: PATCH4 (v4.0)

---

## 🚀 Quick Start (5분 가이드)

### 1단계: 환경 설정 (1분)
```bash
cd HVDC_Invoice_Audit/02_DSV_DOMESTIC

# 환경변수 설정 (PowerShell)
$env:DN_AUTO_CAPACITY_BUMP = "true"
$env:DN_MAX_CAPACITY = "16"
```

### 2단계: 실행 (3분)
```bash
python validate_domestic_with_pdf.py
```

### 3단계: 결과 확인 (1분)
```bash
# Excel 파일 열기
start Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx

# 리포트 확인
start Results/Sept_2025/Reports/SEPT_2025_COMPLETE_VALIDATION_REPORT.md
```

---

## 📊 결과 파일 해석

### 1. Excel 파일 (25 columns)

**items 시트**:
- `dn_matched`: Yes/No (DN 매칭 여부)
- `dn_validation_status`: PASS/WARN/FAIL
- `dn_origin_similarity`: Origin 유사도 (0.27 이상 권장)
- `dn_dest_similarity`: Destination 유사도 (0.50 이상 권장)
- `dn_vehicle_similarity`: Vehicle 유사도 (0.30 이상 권장)
- `dn_unmatched_reason`: 미매칭 사유 (DN_CAPACITY_EXHAUSTED 등)

**해석 예시**:
```
Row 1:
- dn_matched: Yes ✅
- dn_validation_status: PASS ✅
- dn_dest_similarity: 1.000 (완벽!) ⭐
→ 고품질 자동 검증 완료
```

### 2. 수요-공급 분석 (dn_supply_demand.csv)

**컬럼 설명**:
- `demand_top1`: 해당 DN을 최우선 선택한 인보이스 수
- `capacity_final`: Auto-bump 후 최종 capacity
- `gap`: 미충족 수요 (demand - capacity)

**해석**:
```csv
dn_index,shipment_ref,demand_top1,capacity_final,gap
3,HVDC-ADOPT-SCT-0126,13,13,0  ✅ 완벽
```
- gap=0: 수요 완전 충족
- gap>0: capacity 부족 → DN_MAX_CAPACITY 증가 필요

---

## ⚙️ 환경변수 가이드

### 필수 설정 (권장)
```bash
DN_AUTO_CAPACITY_BUMP=true  # 자동 용량 증가
DN_MAX_CAPACITY=16          # 최대 용량
```

### 선택 설정
```bash
# 유사도 임계값 조정 (기본값 권장)
DN_ORIGIN_THR=0.27
DN_DEST_THR=0.50
DN_VEH_THR=0.30
DN_MIN_SCORE=0.40

# 분석 파일 생성
DN_DUMP_TOPN=3              # Top-3 후보 덤프
DN_DUMP_SUPPLY=true         # 수요-공급 분석
```

### 고급 설정 (수동 오버라이드)
```bash
# 특정 DN의 capacity 수동 설정
export DN_CAPACITY_MAP='{
  "HVDC-ADOPT-SCT-0126": 20,
  "HVDC-DSV-PRE-MIR-SHU-230": 10
}'
```

---

## 🔍 검증 상태 이해하기

### PASS (47.7%)
- **의미**: 모든 필드가 임계값 충족
- **조치**: 검증 완료, 추가 확인 불필요
- **예시**: Origin 0.50, Dest 1.00, Vehicle 0.80

### WARN (47.7%)
- **의미**: 일부 필드만 충족
- **조치**: 수작업 확인 권장 (선택)
- **예시**: Origin 0.20, Dest 0.95, Vehicle 0.70
- **대부분 Destination이 높으면 신뢰 가능**

### FAIL (0%)
- **의미**: 모든 필드 미충족
- **조치**: 필수 수작업 검토
- **현재**: FAIL 0% (없음!) ✅

---

## 📝 미매칭 항목 처리

### DN_CAPACITY_EXHAUSTED (현재 0건)
- **원인**: DN capacity 소진
- **해결**: `DN_MAX_CAPACITY` 증가 또는 DN 추가 확보

### BELOW_MIN_SCORE (2건)
- **원인**: 유사도 점수 < 0.40
- **해결**: 수작업 검토 또는 임계값 하향 조정
- **주의**: 임계값 하향 시 품질 저하 가능

---

## 🛠️ 문제 해결 (Troubleshooting)

### Q1: "No text extracted" 경고
**원인**: PDF가 스캔 이미지 (텍스트 없음)
**해결**: OCR 필요 (pytesseract) 또는 수작업

### Q2: 매칭률이 낮음 (<90%)
**원인**: DN_MAX_CAPACITY 부족
**해결**:
```bash
export DN_MAX_CAPACITY=20  # 증가
```

### Q3: PyMuPDF import 오류
**원인**: 미설치
**해결**:
```bash
pip install PyMuPDF
```

### Q4: Excel 파일이 너무 큼
**원인**: DN_Validation 시트
**해결**: 정상 (44 rows만 포함)

---

## 📞 FAQ

**Q: 매칭률 95.5%는 어떻게 달성했나요?**
A: PATCH4에서 DN_MAX_CAPACITY를 16으로 증가하여 모든 DN의 수요를 충족했습니다.

**Q: PASS와 WARN의 차이는?**
A: PASS는 모든 필드 충족, WARN은 일부만 충족합니다. 대부분 Destination이 높으면 신뢰 가능합니다.

**Q: 미매칭 2건은 어떻게 처리하나요?**
A: BELOW_MIN_SCORE 사유이므로 수작업 검토 권장합니다.

**Q: 다른 월 인보이스에도 사용 가능한가요?**
A: 네, 동일한 방법으로 실행 가능합니다.

**Q: DN을 추가하려면?**
A: `Data/DSV 202509/SCNT Domestic (Sept 2025) - Supporting Documents/` 폴더에 PDF 추가 후 재실행.

---

## 📚 추가 문서

- **시스템 구조**: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- **핵심 로직**: [CORE_LOGIC.md](CORE_LOGIC.md)
- **개발 가이드**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- **패치 이력**: [PATCH_HISTORY.md](PATCH_HISTORY.md)

---

**문서 버전**: 1.0
**작성일**: 2025-10-13 22:50:00
**문의**: 시스템 관리자

