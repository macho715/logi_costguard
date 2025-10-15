# HVDC Invoice Audit - 최종 파일 구조

**프로젝트**: HVDC Invoice Audit System
**생성일**: 2025-10-15 02:50 AM
**버전**: v4.0-COMPLETE

---

## 프로젝트 구조 개요

```
HVDC_Invoice_Audit/
├── 00_Shared/                  (공유 라이브러리 및 Configuration)
├── 01_DSV_SHPT/                (DSV Shipment 시스템)
├── 02_DSV_DOMESTIC/            (DSV Domestic 시스템)
├── Archive/                    (보관 파일)
├── hybrid_doc_system/          (Hybrid PDF 파싱 시스템)
├── ML/                         (머신러닝 모듈)
├── PDF/                        (PDF 파서 실험)
├── Rate/                       (요율 Configuration)
└── [Root Files]                (설정 및 실행 파일)
```

---

## 00_Shared/ - 공유 라이브러리

### 핵심 모듈 (5개)

| 파일 | Lines | 목적 |
|------|-------|------|
| `config_manager.py` | 400 | Configuration 통합 관리 |
| `unified_ir_adapter.py` | 600 | PDF 데이터 변환 |
| `category_normalizer.py` | 178 | 카테고리 정규화 |
| `rate_loader.py` | 250 | 요율 파일 로더 |
| `validate_rate_json.py` | 150 | 요율 검증 |

### 하위 디렉토리

#### hybrid_integration/ (Hybrid System 클라이언트)
```
- hybrid_client.py          (200 lines) - FastAPI 클라이언트
- __init__.py
- routing_config.json
```

#### pdf_integration/ (PDF 파싱 통합)
```
- pdf_parser.py             (400 lines) - Unified PDF 파서
- cross_doc_validator.py    (250 lines) - 문서 간 검증
- ontology_mapper.py         (180 lines) - Ontology 매핑
- workflow_automator.py      (220 lines) - 워크플로우 자동화
```

---

## 01_DSV_SHPT/ - Shipment 시스템 (주 시스템)

### Core_Systems/ - 핵심 시스템 파일

#### 실행 파일 (3개)
| 파일 | 목적 | 실행 명령 |
|------|------|-----------|
| `masterdata_validator.py` | 주 검증 엔진 (900 lines) | `python masterdata_validator.py` |
| `report_generator.py` | Excel 보고서 생성 (500 lines) | (자동 호출) |
| `run_audit.py` | 전체 감사 실행 (200 lines) | `python run_audit.py` |

#### Archive/ - 보관 파일
```
Archive/
├── Obsolete_Systems/        (구버전 시스템 2개)
├── Analysis_Scripts/        (분석 스크립트 25개)
├── Test_Scripts/            (테스트 스크립트 5개)
└── Debug_Scripts/           (디버그 스크립트 6개) ← 새로 정리
```

### Data/ - Invoice 및 PDF
```
Data/
└── DSV 202509/
    ├── SCNT Import (Sept 2025) - Supporting Documents/
    │   ├── 01. HVDC-ADOPT-SCT-0126/
    │   │   ├── HVDC-ADOPT-SCT-0126_CarrierInvoice.pdf
    │   │   └── ...pdf (57개 PDF 파일)
    │   └── ...
    └── SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm
```

### Results/ - 검증 결과
```
Results/
└── Final_Validation_Report_20251015_HHMMSS.xlsx
```

### Documentation/ - 문서

#### 핵심 문서 (4개)
- **00_DOCUMENTATION_INDEX.md** ⭐ - 전체 문서 인덱스
- **01_USER_GUIDE.md** - 사용자 매뉴얼
- **02_CONFIGURATION_GUIDE.md** - 설정 가이드
- **03_TROUBLESHOOTING_GUIDE.md** - 문제 해결

### 개선 보고서 (16개)
| 보고서 | Phase | 날짜 |
|--------|-------|------|
| **HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md** | 전체 | 2025-10-15 |
| **DEVELOPMENT_TIMELINE.md** | 전체 | 2025-10-15 |
| HARDCODING_REMOVAL_COMPLETE_251014.md | 2 | 2025-10-14 |
| SYSTEM_REUSABILITY_ASSESSMENT_251014.md | 2 | 2025-10-14 |
| FILE_CLEANUP_COMPLETE_REPORT_251014.md | 3 | 2025-10-14 |
| FILE_NAMING_STANDARDIZATION_COMPLETE.md | 3 | 2025-10-14 |
| DUPLICATION_ANALYSIS_COMPLETE_251014.md | 3 | 2025-10-14 |
| CONFIGURATION_NORMALIZATION_COMPLETE_REPORT.md | 4 | 2025-10-14 |
| AT_COST_VALIDATION_ENHANCEMENT_REPORT.md | 5 | 2025-10-14 |
| COMPREHENSIVE_IMPROVEMENT_FINAL_REPORT.md | 5 | 2025-10-14 |
| PDF_SUMMARY_EXTRACTION_FINAL_REPORT.md | 6 | 2025-10-15 |
| E2E_HYBRID_INTEGRATION_TEST_REPORT.md | 7 | 2025-10-15 |
| HYBRID_ARTIFACTS_V1_INTEGRATION_REPORT.md | 7 | 2025-10-15 |
| COORDINATE_TABLE_EXTRACTION_COMPLETE_REPORT.md | 8 | 2025-10-15 |
| COORDINATE_TABLE_FINAL_EXECUTION_REPORT.md | 8 | 2025-10-15 |
| PDF_RATE_EXTRACTION_IMPROVEMENT_REPORT.md | 보조 | 2025-10-14 |

---

## hybrid_doc_system/ - Hybrid PDF 파싱 시스템

### 구조
```
hybrid_doc_system/
├── api/
│   └── main.py              (FastAPI 서버, 300 lines)
├── worker/
│   └── celery_app.py        (Celery Worker, 550 lines)
└── config/
    └── routing_rules_hvdc.json
```

### 실행 방법
```bash
# Redis 시작
sudo service redis-server start

# Honcho 시작
honcho -f Procfile.dev start
```

---

## Rate/ - 요율 Configuration

### JSON 파일 (6개)
| 파일 | 항목 수 | 목적 |
|------|---------|------|
| `config_contract_rates.json` | 20+ | 계약 요율 (DO, Customs, Portal) |
| `config_shpt_lanes.json` | 8 | Inland Transportation 경로 |
| `config_synonyms.json` | 20 | 카테고리 Synonym |
| `air_cargo_rates.json` | 50+ | 항공 화물 요율 |
| `container_cargo_rates.json` | 100+ | 컨테이너 요율 |
| `inland_trucking_reference_rates_clean.json` | 30+ | Inland 참조 요율 |

### Markdown 문서 (5개)
- `contract_inland_trucking_charge_rates_v1.3.md`
- `Invoice_Rate_Reference_v2.1_Bulk.md`
- `Invoice_Rate_Reference_v2.1_Container.md`
- `Invoice_Rate_Reference_v2.1_full.md`
- `PRISM_KERNEL_README_HVDC_v2.md`

---

## Archive/ - 보관 파일

### 구조
```
Archive/
├── Utilities_20251015/          (8개 파일)
│   ├── analyze_legacy_files.py
│   ├── create_file_inventory.py
│   ├── identify_duplicates.py
│   ├── move_to_archive.py
│   ├── domestic_validator_v2.py
│   ├── run_domestic_audit_v2.py
│   ├── FILE_INVENTORY.xlsx
│   └── DUPLICATE_ANALYSIS.xlsx
│
├── 02_DSV_DOMESTIC_Legacy_20251013/  (131개 파일)
│   └── (구버전 Domestic 시스템 전체)
│
└── 20251013_Before_Cleanup/     (36개 파일)
    └── (정리 전 백업)
```

---

## Root Files - 설정 및 실행 파일

### 설정 파일 (6개)
| 파일 | 목적 |
|------|------|
| `Procfile.dev` | Honcho 프로세스 정의 |
| `requirements_hybrid.txt` | Python 의존성 (Hybrid) |
| `env.sample` | 환경변수 샘플 |
| `docker-compose-integrated.yaml` | Docker Compose (선택적) |
| `config_domestic_v2.json` | Domestic 설정 |
| `.gitignore` | Git 제외 파일 |

### 실행 스크립트 (3개)
| 파일 | 목적 |
|------|------|
| `start_hybrid_system.sh` | Hybrid 시작 (bash) |
| `restart_hybrid_system.sh` | Hybrid 재시작 (bash) |
| `test_redis_connection.py` | Redis 연결 테스트 |

### 문서 (12개)
- `README.md` - 프로젝트 개요
- `QUICK_START.md` - 빠른 시작
- `README_WSL2_SETUP.md` - WSL2 설정
- `REDIS_INSTALLATION_GUIDE.md` - Redis 설치
- `REDIS_INSTALLATION_COMPLETE_REPORT.md` - Redis 설치 완료
- `HONCHO_EXECUTION_GUIDE.md` - Honcho 실행
- `HYBRID_SYSTEM_SETUP_FINAL_REPORT.md` - Hybrid Setup 최종
- `HYBRID_SYSTEM_COMPLETE_FINAL_REPORT.md` - Hybrid 완성
- `FINAL_INTEGRATION_SUMMARY.md` - 최종 통합 요약
- `PDF_INTEGRATION_STATUS.md` - PDF 통합 상태
- `PLAN_COMPLETION_CHECKLIST.md` - 계획 체크리스트
- `FILE_STRUCTURE_FINAL.md` - 이 파일

---

## 파일 통계

### 전체 통계
```
파일 종류              수량        크기(예상)
────────────────────────────────────────
Python 스크립트       120+        ~15,000 lines
Configuration (JSON)   15+        ~2,000 lines
Markdown 문서         35+        ~350 pages
Excel 파일            45+        ~50 MB
PDF 파일             150+        ~200 MB
────────────────────────────────────────
총계                 365+        ~250 MB
```

### 주요 디렉토리별
| 디렉토리 | 파일 수 | 주요 내용 |
|----------|---------|-----------|
| **00_Shared/** | 20+ | 공유 라이브러리 |
| **01_DSV_SHPT/** | 200+ | 주 시스템 + 문서 |
| **hybrid_doc_system/** | 10+ | Hybrid System |
| **Rate/** | 15+ | Configuration |
| **Archive/** | 175+ | 보관 파일 |
| **Root** | 25+ | 설정/실행 파일 |

---

## 주요 경로 Quick Reference

### 개발자용
```bash
# 주 검증 시스템
01_DSV_SHPT/Core_Systems/masterdata_validator.py

# Configuration 관리
00_Shared/config_manager.py

# PDF 어댑터
00_Shared/unified_ir_adapter.py

# Hybrid 클라이언트
00_Shared/hybrid_integration/hybrid_client.py

# Celery Worker
hybrid_doc_system/worker/celery_app.py
```

### 사용자용
```bash
# 빠른 시작
QUICK_START.md

# 사용자 매뉴얼
01_DSV_SHPT/Documentation/01_USER_GUIDE.md

# 설정 가이드
01_DSV_SHPT/Documentation/02_CONFIGURATION_GUIDE.md

# 문제 해결
01_DSV_SHPT/Documentation/03_TROUBLESHOOTING_GUIDE.md
```

### 관리자용
```bash
# 마스터 보고서
01_DSV_SHPT/HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md

# 개발 타임라인
01_DSV_SHPT/DEVELOPMENT_TIMELINE.md

# 문서 인덱스
01_DSV_SHPT/Documentation/00_DOCUMENTATION_INDEX.md

# 파일 구조 (이 파일)
FILE_STRUCTURE_FINAL.md
```

---

## 유지보수 가이드

### 파일 추가 시
1. 적절한 디렉토리에 배치
2. 파일명 규칙 준수 (`snake_case.py`, `UPPERCASE.md`)
3. 이 문서 업데이트

### 파일 삭제 시
1. Archive로 이동 (즉시 삭제 금지)
2. 의존성 확인
3. 이 문서 업데이트

### 구조 변경 시
1. 영향 받는 import 경로 확인
2. 문서 링크 업데이트
3. README 및 이 문서 업데이트

---

## 버전 관리

### 파일 명명 규칙
```
# 날짜 포함
*_YYYYMMDD.py          예: analyze_20251014.py
*_REPORT_YYYYMMDD.md   예: VALIDATION_REPORT_20251015.md

# 버전 포함
*_v{major}.{minor}.{patch}  예: config_v2.1.3.json

# Archive 폴더
Archive/{Category}_{YYYYMMDD}/
```

### Git 관리
- `.gitignore`: 임시 파일, 민감 정보 제외
- 커밋 메시지: Conventional Commits 준수
- 브랜치: `feature/`, `bugfix/`, `release/`

---

## 결론

HVDC Invoice Audit System은 **365+ 파일**, **~250MB** 규모의 완전한 시스템으로, **체계적인 디렉토리 구조**와 **완벽한 문서화**를 갖추고 있습니다.

### 핵심 특징
- ✅ **모듈화**: 기능별 명확한 분리
- ✅ **확장성**: 새 Forwarder 추가 용이
- ✅ **유지보수성**: Configuration 외부화
- ✅ **문서화**: 35+ 문서, 완전한 추적성

---

**작성자**: AI Development Team
**최종 업데이트**: 2025-10-15 02:50 AM
**버전**: v4.0-COMPLETE


