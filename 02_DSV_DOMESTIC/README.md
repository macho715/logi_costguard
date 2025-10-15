# 9월 2025 DSV Domestic Invoice 검증 시스템

**프로젝트**: HVDC Project - Samsung C&T Logistics
**기간**: 2025-10-12 ~ 2025-10-13
**최종 버전**: PATCH4 (v4.0) + Hybrid + Migration Ready
**Status**: ✅ Production Ready + Migration Ready

---

## 🎉 주요 성과

| 지표 | 최종 결과 | 목표 대비 |
|------|----------|----------|
| **매칭률** | **95.5%** (42/44) | +5.5%p 초과 🚀 |
| **PASS** | 21건 (47.7%) | 고품질 자동 검증 |
| **WARN** | 21건 (47.7%) | 중간 품질 |
| **FAIL** | 0건 (0%) | **완벽!** 🏆 |
| **Dest 유사도** | 0.971 | 거의 완벽 ⭐ |
| **자동화 시간 절감** | 약 6시간 | 수작업 대비 |

---

## 📚 문서 가이드

### 빠른 시작
- **[QUICK_START.md](Documentation/00_INDEX/QUICK_START.md)**: 5분 완성 가이드 (NEW)
- **[DOCUMENTATION_INDEX.md](Documentation/00_INDEX/DOCUMENTATION_INDEX.md)**: 전체 문서 인덱스 및 읽기 가이드

### 핵심 문서
- **[SYSTEM_ARCHITECTURE.md](Documentation/01_ARCHITECTURE/SYSTEM_ARCHITECTURE.md)**: 시스템 구조 및 컴포넌트
- **[SYSTEM_ARCHITECTURE_DIAGRAM.md](Documentation/01_ARCHITECTURE/SYSTEM_ARCHITECTURE_DIAGRAM.md)**: 시각적 아키텍처 다이어그램 📊 (10개 Mermaid)
- **[CORE_LOGIC.md](Documentation/01_ARCHITECTURE/CORE_LOGIC.md)**: 핵심 알고리즘 및 로직
- **[USER_GUIDE.md](Documentation/02_GUIDES/USER_GUIDE.md)**: 사용자 실행 가이드
- **[DEVELOPMENT_GUIDE.md](Documentation/02_GUIDES/DEVELOPMENT_GUIDE.md)**: 개발자 가이드
- **[API_REFERENCE.md](Documentation/02_GUIDES/API_REFERENCE.md)**: API 레퍼런스

### Hybrid Integration 문서
- **[HYBRID_INTEGRATION_ARCHITECTURE.md](Documentation/01_ARCHITECTURE/HYBRID_INTEGRATION_ARCHITECTURE.md)**: Hybrid 상세 아키텍처 (NEW)
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)**: Hybrid 통합 완료 보고서
- **[HYBRID_INTEGRATION_STEP_BY_STEP.md](HYBRID_INTEGRATION_STEP_BY_STEP.md)**: 단계별 통합 가이드
- **[HYBRID_INTEGRATION_FINAL_STATUS.md](HYBRID_INTEGRATION_FINAL_STATUS.md)**: 최종 상태 보고서

### 개발 이력
- **[DEVELOPMENT_TIMELINE.md](Documentation/03_HISTORY/DEVELOPMENT_TIMELINE.md)**: 3일 개발 타임라인 (NEW)
- **[PATCH_HISTORY.md](Documentation/03_HISTORY/PATCH_HISTORY.md)**: PATCH1-4 전체 이력
- **[DN_CAPACITY_EXHAUSTED_DETAILED_REPORT.md](Documentation/04_REPORTS/DN_CAPACITY_EXHAUSTED_DETAILED_REPORT.md)**: DN Capacity 분석

### Migration & Templates (다른 월 적용)
- **[MIGRATION_GUIDE.md](Documentation/02_GUIDES/MIGRATION_GUIDE.md)**: 다른 월 적용 가이드 (30분) (NEW)
- **[config_month_template.json](Templates/config_month_template.json)**: 월별 설정 템플릿 (NEW)
- **[config_oct_2025_example.json](Templates/config_oct_2025_example.json)**: 10월 예시 (NEW)

### 시스템 검증 보고서
- **[SYSTEM_HEALTH_CHECK_FINAL.md](SYSTEM_HEALTH_CHECK_FINAL.md)**: 최종 건전성 보고서 (NEW)
- **[CLEANUP_REPORT_20251014.md](CLEANUP_REPORT_20251014.md)**: 폴더 정리 보고서
- **[DOCUMENTATION_UPDATE_REPORT.md](DOCUMENTATION_UPDATE_REPORT.md)**: 문서 업데이트 보고서
- **[DOCUMENTATION_REORGANIZATION_REPORT.md](Documentation/DOCUMENTATION_REORGANIZATION_REPORT.md)**: 문서 재구성 보고서

---

## 🚀 Quick Start

### 1. 환경 설정

```bash
# 필수 패키지 설치
pip install pandas openpyxl

# 선택 패키지 (성능 향상)
pip install PyMuPDF  # PDF 추출 최적화
```

### 2. 실행

```bash
cd HVDC_Invoice_Audit/02_DSV_DOMESTIC

# 기본 실행 (PATCH4 설정)
export DN_AUTO_CAPACITY_BUMP=true
export DN_MAX_CAPACITY=16
python validate_domestic_with_pdf.py
```

### 3. 결과 확인

```
Results/Sept_2025/
├── domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx  # 최신 FINAL Excel
├── Reports/ (34개 문서)
│   ├── SEPT_2025_COMPLETE_VALIDATION_REPORT.md          # 종합 리포트
│   ├── dn_supply_demand.csv                             # 수요-공급 분석
│   ├── dn_candidate_dump.csv                            # Top-3 후보
│   ├── SYSTEM_ARCHITECTURE.md                           # 시스템 아키텍처
│   ├── CORE_LOGIC.md                                    # 핵심 로직
│   ├── PATCH_HISTORY.md                                 # 패치 이력
│   └── ... (28개 추가 문서)
└── Logs/ (13개 로그)                                     # 실행 이력
```

---

## 📂 디렉토리 구조

```
02_DSV_DOMESTIC/
├── README.md                             # 프로젝트 개요
├── config_domestic_v2.json               # 운영 설정
├── validate_domestic_with_pdf.py         # 메인 검증 스크립트
├── enhanced_matching.py                  # Enhanced Lane Matching
├── CLEANUP_REPORT_20251014.md            # 폴더 정리 보고서
├── INTEGRATION_COMPLETE.md               # Hybrid 통합 완료 보고서
├── HYBRID_INTEGRATION_STEP_BY_STEP.md    # Hybrid 통합 가이드
├── HYBRID_INTEGRATION_FINAL_STATUS.md    # Hybrid 최종 상태
│
├── Core_Systems/                         # 핵심 시스템
│   └── hybrid_pdf_integration.py         # Hybrid PDF Router 통합
│
├── src/utils/                            # 유틸리티 모듈 (6개)
│   ├── __init__.py                       # 패키지 초기화
│   ├── utils_normalize.py               # 정규화 (normalize_location, token_set_jaccard)
│   ├── location_canon.py                # 약어 확장 (16개 매핑)
│   ├── pdf_extractors.py                # PDF 필드 추출
│   ├── pdf_text_fallback.py             # PDF 텍스트 다층 폴백 (PyMuPDF 포함)
│   └── dn_capacity.py                   # DN Capacity 관리 (PATCH3)
│
├── Data/
│   └── DSV 202509/
│       └── SCNT Domestic (Sept 2025) - Supporting Documents/  # DN PDF 36개
│
├── Results/Sept_2025/                    # 검증 결과
│   ├── domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx    # 최신 FINAL (1개만)
│   └── Reports/ (34개 문서)              # 완전한 문서 세트
│
├── Templates/                            # 월별 설정 템플릿 (NEW)
│   ├── config_month_template.json        # 월별 설정 템플릿
│   └── config_example_2025_10.json       # 10월 2025 예시
│
├── Documentation/                        # 종합 문서 (14개 활성)
│   ├── 00_INDEX/ (3개)                   # 인덱스 및 시작 가이드
│   │   ├── README.md
│   │   ├── DOCUMENTATION_INDEX.md
│   │   └── QUICK_START.md (NEW)          # 5분 완성 가이드
│   ├── 01_ARCHITECTURE/ (4개)            # 시스템 아키텍처
│   │   ├── SYSTEM_ARCHITECTURE.md (Updated)
│   │   ├── SYSTEM_ARCHITECTURE_DIAGRAM.md (Updated - 10개 Mermaid)
│   │   ├── CORE_LOGIC.md
│   │   └── HYBRID_INTEGRATION_ARCHITECTURE.md (NEW)
│   ├── 02_GUIDES/ (4개)                  # 사용자/개발자 가이드
│   │   ├── USER_GUIDE.md
│   │   ├── DEVELOPMENT_GUIDE.md
│   │   ├── API_REFERENCE.md
│   │   └── MIGRATION_GUIDE.md (NEW)      # 다른 월 적용 가이드
│   ├── 03_HISTORY/ (2개) [RENAMED]       # 개발 이력
│   │   ├── PATCH_HISTORY.md
│   │   └── DEVELOPMENT_TIMELINE.md (NEW) # 3일 타임라인
│   └── 04_REPORTS/ (2개)                 # 검증 보고서
│       ├── SEPT_2025_COMPLETE_VALIDATION_REPORT.md
│       └── DN_CAPACITY_EXHAUSTED_DETAILED_REPORT.md
│
└── ARCHIVE/                              # 이력 보관 (2025-10-14 정리)
    ├── logs/                             # 로그 파일 (17개)
    │   ├── final_validation.log
    │   ├── validation_results.txt
    │   ├── validation_with_hybrid_columns.log
    │   ├── validation_hybrid_test.log
    │   └── Sept_2025_Logs/ (13개)        # 이전 실행 로그
    ├── excel_history/                    # 이전 Excel 버전 (9개)
    ├── reports_history/                  # 중복 리포트 (5개)
    ├── backups/                          # 백업 파일 (1개)
    │   └── validate_domestic_with_pdf.py.backup
    ├── temp/                             # 임시 파일 (2개)
    │   ├── dn_supply_demand.csv
    │   └── verify_final_v2.py
    └── documentation_history/            # 문서 이력 (6개)
        ├── verification_reports/ (3개)
        └── patch_reports/ (3개)
```

---

## 🔑 핵심 기능

### 1. Enhanced Lane Matching (79.5%)
**4-level Fallback System**:
- Level 1: Exact Match (100% 일치)
- Level 2: Similarity Match (≥0.65)
- Level 3: Region Match (권역별)
- Level 4: Vehicle Type Match (차량 타입)

### 2. PDF Cross-Validation (95.5%)
**Supporting Documents 검증**:
- DN PDF 파싱 (33/36 성공)
- Origin/Destination/Vehicle 추출
- 유사도 기반 검증 (Dest 0.971)
- 1:1 그리디 매칭

### 3. DN Capacity System (PATCH3-4)
**자동 용량 관리**:
- DN_MAX_CAPACITY=16 (기본값)
- Auto-Bump (수요 기반 자동 증가)
- 수요-공급 분석 (`dn_supply_demand.csv`)
- Gap=0 달성 (모든 DN)

### 4. 검증 상태 분류
- **PASS**: Origin, Dest, Vehicle 모두 임계값 충족
- **WARN**: 일부만 충족
- **FAIL**: 모두 미충족 (현재 0%)

---

## 🛠️ 환경변수

### PDF 추출
```bash
DN_USE_PDF_FIELDS_FIRST=true  # PDF 본문 우선 (기본)
```

### 유사도 임계값
```bash
DN_ORIGIN_THR=0.27   # Origin 유사도 임계값
DN_DEST_THR=0.50     # Destination 유사도 임계값
DN_VEH_THR=0.30      # Vehicle 유사도 임계값
DN_MIN_SCORE=0.40    # 최소 매칭 점수
```

### DN Capacity
```bash
DN_AUTO_CAPACITY_BUMP=true    # 자동 용량 증가 (권장)
DN_MAX_CAPACITY=16            # 최대 용량 (기본 16)
DN_CAPACITY_DEFAULT=1         # 기본 용량
```

### 분석 파일
```bash
DN_DUMP_TOPN=3                            # Top-N 후보 덤프 (0=비활성)
DN_DUMP_PATH=dn_candidate_dump.csv        # 후보 덤프 경로
DN_DUMP_SUPPLY=true                       # 수요-공급 분석 (권장)
DN_DUMP_SUPPLY_PATH=dn_supply_demand.csv  # 수요-공급 경로
```

---

## 📊 출력 파일

### 1. Excel 파일 (25 columns)
**domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx**

**items 시트** (44 rows):
- Enhanced Matching: 12 columns (origin, destination, vehicle, ref_adj 등)
- PDF 검증: 13 columns (dn_matched, dn_origin_similarity, dn_unmatched_reason 등)
- **하이퍼링크**: ref_adj 컬럼에서 ApprovedLaneMap으로 연결 (35개, 79.5%)

**기타 시트**:
- ApprovedLaneMap: 124 레인 (하이퍼링크 대상)
- DN_Validation: 44 rows (상세 검증)
- comparison, patterns_applied

**하이퍼링크 기능**:
- ref_adj 컬럼의 요율을 클릭하면 ApprovedLaneMap 시트의 해당 레인으로 즉시 이동
- Enhanced Matching 4-level fallback 시스템으로 자동 매칭
- 매칭률: 35/44 (79.5%)

### 2. 수요-공급 분석 CSV
**dn_supply_demand.csv**:
```csv
dn_index,shipment_ref,filename,demand_top1,capacity_final,gap
3,HVDC-ADOPT-SCT-0126,HVDC-ADOPT-SCT-0126_DAS_DN (DSV-MOSB).pdf,13,13,0
```

### 3. 종합 리포트
**SEPT_2025_COMPLETE_VALIDATION_REPORT.md**:
- Enhanced Lane Matching 결과
- PDF Cross-Validation 결과
- 주요 발견 사항
- 권장 조치

---

## 🔧 주요 스크립트

### 메인 검증
```bash
python validate_domestic_with_pdf.py
```

### 결과 검증
```bash
python verify_final_v2.py
```

### Enhanced Matching (단독)
```bash
python add_approved_lanemap_to_excel.py
```

---

## 📈 개발 이력 (PATCH1-4)

| PATCH | 핵심 기능 | 매칭률 | 날짜 |
|-------|----------|--------|------|
| **PATCH1** | 약어 확장, 정규화 | - | 2025-10-12 |
| **PATCH2** | PDF 본문 우선, 1:1 그리디 | 20/44 (45.5%) | 2025-10-13 |
| **PATCH3** | DN Capacity 시스템 | 30/44 (68.2%) | 2025-10-13 |
| **PATCH4** | PyMuPDF, MAX_CAP=16 | **42/44 (95.5%)** | 2025-10-13 |

**최종 개선**: 0% → **95.5%** (+95.5%p)

---

## 🎯 성능 지표

### 매칭 통계
- Enhanced Lane Matching: 79.5% (35/44)
- PDF Cross-Validation: 95.5% (42/44)
- PASS 비율: 47.7% (21/44)
- WARN 비율: 47.7% (21/44)
- FAIL 비율: 0% (0/44) ✅

### 유사도
- Origin: 0.473 (평균)
- Destination: 0.971 (평균) ⭐
- Vehicle: 0.985 (평균) ⭐

### 처리 성능
- PDF 파싱 성공률: 91.7% (33/36)
- 처리 시간: 약 8분 (44개 인보이스)
- 자동화율: 95.5%

---

## 🏗️ 시스템 상태

### Production 환경
- **루트 파일**: 9개 (핵심 작업 파일만)
- **폴더**: 6개 (Core_Systems, src, Data, Results, Documentation, ARCHIVE)
- **복잡도**: ⭐ (Production Ready)

### 시스템 건전성 ✅
- **의존성**: 모든 모듈 정상 로드
- **설정 파일**: v2.3.0 유효한 JSON 구조
- **입력 데이터**: 36개 DN PDF 검출 성공
- **실행 테스트**: 95.5% 매칭률 달성
- **Hybrid Integration**: Docling/ADE 라우팅 정상 작동
- **Migration Ready**: 다른 월 적용 가능 (30분)
- **System Health Check**: 건전성 검증 완료
- **상태**: Production Ready + Migration Ready

### 폴더 정리 완료 ✅ (2025-10-14)
- **루트 파일 정리**: 25개 → 9개 (64% 감소)
- **로그 파일**: 17개 ARCHIVE로 이동
- **Excel 버전 관리**: 10개 → 1개 (최신만 유지, 9개 ARCHIVE)
- **중복 문서**: 11개 ARCHIVE로 이동 (reports_history, documentation_history)
- **백업/임시 파일**: 3개 ARCHIVE로 정리
- **최신 FINAL**: 1개만 유지 (깔끔한 Production)
- **문서**: 14개 활성 (Documentation) + 34개 (Reports)
- **ARCHIVE 구조**: `ARCHIVE/` (logs, excel_history, reports_history, backups, temp, documentation_history)
- **정리 보고서**: [CLEANUP_REPORT_20251014.md](CLEANUP_REPORT_20251014.md)

### Documentation 재구성 완료 ✅ (2025-10-14)
- **03_PATCH_HISTORY → 03_HISTORY**: 폴더명 변경
- **신규 문서 추가**: QUICK_START.md, HYBRID_INTEGRATION_ARCHITECTURE.md, MIGRATION_GUIDE.md, DEVELOPMENT_TIMELINE.md
- **Templates 폴더 생성**: 월별 설정 템플릿 및 예시
- **문서 이력 보관**: 6개 문서 ARCHIVE/documentation_history로 이동
- **재구성 보고서**: [DOCUMENTATION_REORGANIZATION_REPORT.md](Documentation/DOCUMENTATION_REORGANIZATION_REPORT.md)

---

## 🤝 기여

### 개발팀
- **AI System**: MACHO-GPT v3.4-mini
- **Project**: HVDC Samsung C&T Logistics
- **Partnership**: ADNOC·DSV

### 기술 스택
- **Language**: Python 3.8+
- **Core Libraries**: pandas, openpyxl
- **PDF Processing**: PyMuPDF, pypdf, pdfminer.six, pdftotext
- **Matching**: Token-Set Jaccard, Levenshtein, Fuzzy

---

## 📞 문의

### 빠른 시작
- **5분 가이드**: [QUICK_START.md](Documentation/00_INDEX/QUICK_START.md)
- **다른 월 적용**: [MIGRATION_GUIDE.md](Documentation/02_GUIDES/MIGRATION_GUIDE.md) (30분)
- **설정 템플릿**: [config_month_template.json](Templates/config_month_template.json)

### 문서
- 시스템 구조: [SYSTEM_ARCHITECTURE.md](Documentation/01_ARCHITECTURE/SYSTEM_ARCHITECTURE.md)
- 사용 방법: [USER_GUIDE.md](Documentation/02_GUIDES/USER_GUIDE.md)
- 개발 가이드: [DEVELOPMENT_GUIDE.md](Documentation/02_GUIDES/DEVELOPMENT_GUIDE.md)
- Hybrid 아키텍처: [HYBRID_INTEGRATION_ARCHITECTURE.md](Documentation/01_ARCHITECTURE/HYBRID_INTEGRATION_ARCHITECTURE.md)
- 시스템 건전성: [SYSTEM_HEALTH_CHECK_FINAL.md](SYSTEM_HEALTH_CHECK_FINAL.md)

### 이슈
- DN 미매칭: [DN_CAPACITY_EXHAUSTED_DETAILED_REPORT.md](Documentation/04_REPORTS/DN_CAPACITY_EXHAUSTED_DETAILED_REPORT.md)
- Capacity 문제: `DN_MAX_CAPACITY` 증가 권장
- 구조 검증: [FINAL_STRUCTURE_VERIFICATION.md](Documentation/00_INDEX/FINAL_STRUCTURE_VERIFICATION.md)

---

## 📄 라이선스

Samsung C&T HVDC Project - Internal Use Only
**Confidential**: NDA·PII 보호 필수

---

**Last Updated**: 2025-10-14 10:00:00
**Version**: PATCH4 (v4.0) + Hybrid + Cleanup + Migration Ready
**Status**: ✅ Production Ready + Migration Ready (다른 월 적용 가능)
