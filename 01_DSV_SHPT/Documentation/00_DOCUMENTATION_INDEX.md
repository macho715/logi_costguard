# HVDC Invoice Audit - 문서 인덱스

**프로젝트**: HVDC Invoice Audit System
**최종 업데이트**: 2025-10-15 02:40 AM

---

## 📚 핵심 문서

### 1. 시작하기
- **[마스터 보고서](../HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md)** ⭐
  - 전체 시스템 개요 및 8개 Phase 상세 설명
  - Executive Summary, KPI, 아키텍처

- **[개발 타임라인](../DEVELOPMENT_TIMELINE.md)** 📅
  - 2025-10-12 ~ 2025-10-15 (4일간) 개발 일지
  - 날짜별 주요 작업 및 성과

- **[README](../README.md)** 📖
  - 시스템 사용 방법 및 주요 기능
  - Quick Start 가이드

- **[QUICK_START](../../QUICK_START.md)** ⚡
  - 3단계 빠른 시작 가이드

---

## 📊 Phase별 개선 보고서 (시간순)

### Phase 1: Contract Validation (2025-10-13)
- 계약 요율 검증 로직 통합
- Configuration 외부화 시작

### Phase 2: Configuration Management (2025-10-14)
- **[하드코딩 제거 완료](../HARDCODING_REMOVAL_COMPLETE_251014.md)**
  - 206개 항목 중 175개 외부화 (85%)

- **[시스템 재사용성 평가](../SYSTEM_REUSABILITY_ASSESSMENT_251014.md)**
  - 재사용성 점수: 20% → 90%

### Phase 3: PDF Integration (2025-10-14)
- **[파일 정리 완료](../FILE_CLEANUP_COMPLETE_REPORT_251014.md)**
  - 69개 파일 Archive 이동

- **[파일 이름 표준화](../FILE_NAMING_STANDARDIZATION_COMPLETE.md)**
  - 8개 파일 이름 변경

- **[중복 분석 완료](../DUPLICATION_ANALYSIS_COMPLETE_251014.md)**
  - 구버전 시스템 제거

### Phase 4: Category Normalization (2025-10-14)
- **[Configuration 정규화 완료](../CONFIGURATION_NORMALIZATION_COMPLETE_REPORT.md)**
  - Synonym Dictionary 20개 카테고리
  - Category Normalizer 구현

### Phase 5: At Cost Validation (2025-10-14)
- **[At Cost 검증 강화](../AT_COST_VALIDATION_ENHANCEMENT_REPORT.md)**
  - PDF 실제 청구 금액 추출
  - AED → USD 자동 변환
  - FAIL 100% → 41.2% (-58.8%p)

- **[종합 개선 최종 보고서](../COMPREHENSIVE_IMPROVEMENT_FINAL_REPORT.md)**
  - Phase 1-5 통합 성과

### Phase 6: PDF Summary Extraction (2025-10-15)
- **[PDF Summary 추출 최종](../PDF_SUMMARY_EXTRACTION_FINAL_REPORT.md)**
  - 3가지 레이아웃 지원
  - Summary Row 필터링
  - 정확도: 85% → 92%

### Phase 7: Hybrid System Integration (2025-10-15)
- **[Hybrid System Setup 최종](../../HYBRID_SYSTEM_SETUP_FINAL_REPORT.md)**
  - FastAPI + Celery + Redis 아키텍처
  - No-Docker 런타임 (WSL2)

- **[Hybrid Artifacts v1 통합](../HYBRID_ARTIFACTS_V1_INTEGRATION_REPORT.md)**
  - 고급 라우팅 규칙 통합
  - pdfplumber bbox 기반 추출

- **[E2E 통합 테스트](../E2E_HYBRID_INTEGRATION_TEST_REPORT.md)**
  - 102 items, 52.0% PASS

- **[최종 통합 요약](../../FINAL_INTEGRATION_SUMMARY.md)**
  - Phase 7 완료 종합

### Phase 8: Coordinate/Table Extraction (2025-10-15)
- **[좌표/테이블 추출 완료](../COORDINATE_TABLE_EXTRACTION_COMPLETE_REPORT.md)**
  - 좌표 검색 범위 확대 (200px → 600px)
  - 테이블 기반 추출 추가
  - Multi-strategy Fallback

- **[좌표/테이블 최종 실행](../COORDINATE_TABLE_FINAL_EXECUTION_REPORT.md)**
  - E2E 검증 완료
  - +111 lines 코드 추가

---

## 🔧 기술 문서

### Setup & Configuration
- **[WSL2 Setup](../../README_WSL2_SETUP.md)**
  - Windows에서 WSL2 설치 및 설정

- **[Redis 설치 가이드](../../REDIS_INSTALLATION_GUIDE.md)**
  - Redis 설치 및 테스트

- **[Redis 설치 완료](../../REDIS_INSTALLATION_COMPLETE_REPORT.md)**
  - 설치 결과 및 검증

- **[Honcho 실행 가이드](../../HONCHO_EXECUTION_GUIDE.md)**
  - Honcho 기반 프로세스 관리

- **[WSL2 Redis Honcho 통합](../WSL2_Redis _Honcho Hybrid System.md)**
  - 전체 시스템 통합 가이드

### System Architecture
- **[Hybrid System 완성](../../HYBRID_SYSTEM_COMPLETE_FINAL_REPORT.md)**
  - 전체 Hybrid System 아키텍처

- **[PDF 통합 상태](../../PDF_INTEGRATION_STATUS.md)**
  - PDF 파싱 통합 현황

- **[Hybrid 통합 상태](../../HYBRID_INTEGRATION_STATUS.md)**
  - Hybrid System 통합 상태

### User Guides
- **[User Guide](01_USER_GUIDE.md)**
  - 사용자 매뉴얼

- **[Configuration Guide](02_CONFIGURATION_GUIDE.md)**
  - 설정 파일 가이드

- **[Troubleshooting Guide](03_TROUBLESHOOTING_GUIDE.md)**
  - 문제 해결 가이드

---

## 📦 Archive

### Obsolete Reports (구버전 보고서)
- **[Legacy/](../Legacy/)**
  - 구버전 시스템 파일
  - 이전 분석 스크립트

### Debug Scripts (디버그 스크립트)
- **[Core_Systems/Archive/Debug_Scripts/](../Core_Systems/Archive/Debug_Scripts/)**
  - PDF 디버그 스크립트 (6개)
  - Fuzzy 매칭 테스트
  - E2E 검증 스크립트

### Utilities (유틸리티)
- **[Archive/Utilities_20251015/](../../Archive/Utilities_20251015/)**
  - 분석 스크립트 (8개)
  - 파일 정리 도구
  - Excel 분석 파일

---

## 📈 통계 요약

### 문서 통계
| 카테고리 | 수량 | 페이지 수 (예상) |
|----------|------|-------------------|
| 핵심 문서 | 4개 | ~40 pages |
| Phase 보고서 | 16개 | ~200 pages |
| 기술 문서 | 9개 | ~100 pages |
| **총계** | **29개** | **~340 pages** |

### 코드 통계
| 항목 | 수량 |
|------|------|
| 신규 파일 | 15개 |
| 수정 파일 | 8개 |
| Configuration 파일 | 6개 |
| 신규 코드 | ~1,900 lines |
| 총 코드 증가 | ~2,200 lines |

---

## 🔍 문서 검색 가이드

### 주제별 검색

#### "Configuration 설정하기"
1. [Configuration Guide](02_CONFIGURATION_GUIDE.md)
2. [Configuration 정규화](../CONFIGURATION_NORMALIZATION_COMPLETE_REPORT.md)

#### "PDF 파싱 문제"
1. [PDF Summary 추출](../PDF_SUMMARY_EXTRACTION_FINAL_REPORT.md)
2. [Hybrid System Setup](../../HYBRID_SYSTEM_SETUP_FINAL_REPORT.md)
3. [Troubleshooting Guide](03_TROUBLESHOOTING_GUIDE.md)

#### "At Cost 검증"
1. [At Cost 검증 강화](../AT_COST_VALIDATION_ENHANCEMENT_REPORT.md)
2. [종합 개선 보고서](../COMPREHENSIVE_IMPROVEMENT_FINAL_REPORT.md)

#### "시스템 확장하기"
1. [시스템 재사용성 평가](../SYSTEM_REUSABILITY_ASSESSMENT_251014.md)
2. [마스터 보고서 - 향후 개선](../HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md#향후-개선-방안)

---

## 📞 문서 관련 문의

### 문서 오류 발견 시
1. 해당 문서의 "작성일" 확인
2. 최신 버전인지 확인
3. GitHub Issue 생성 또는 담당자 문의

### 문서 업데이트 요청
1. 필요한 내용 명시
2. 관련 문서 링크 제공
3. 담당자에게 요청

---

## 🎯 빠른 참조

### 시작하기
```
1. README.md 읽기
2. QUICK_START.md 따라하기
3. User Guide 참조
```

### 문제 해결
```
1. Troubleshooting Guide 확인
2. 관련 Phase 보고서 참조
3. 담당자 문의
```

### 시스템 확장
```
1. 마스터 보고서 읽기
2. Configuration Guide 참조
3. 재사용성 평가 검토
```

---

**작성자**: AI Development Team
**관리자**: Samsung C&T Logistics
**최종 업데이트**: 2025-10-15 02:40 AM


