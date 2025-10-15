# HVDC Invoice Audit - Hybrid System 기술 문서

최신 Hybrid System 관련 기술 문서 모음입니다.

**작성일**: 2025-10-15
**프로젝트**: HVDC Invoice Audit System
**버전**: v4.1-PATCHED

---

## 핵심 문서

1. **`HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md`** - 전체 시스템 마스터 보고서
   - 8개 Phase 전체 개선 과정
   - 최종 성과 및 KPI
   - 시스템 아키텍처

2. **`CORE_FUNCTIONS_AND_LOGIC_REFERENCE.md`** - 핵심 함수 레퍼런스
   - 6개 모듈의 주요 함수 (시그니처 + 로직)
   - 알고리즘 설명
   - Quick Reference 테이블

3. **`DEVELOPMENT_TIMELINE.md`** - 개발 타임라인 (4일간)
   - 일별 작업 내용
   - 주요 성과
   - 의사결정 기록

4. **`LOGIC_PATCH_REPORT.md`** - logic_patch.md 적용 보고서
   - 7개 핵심 이슈 해결
   - 6개 주요 패치 적용
   - 시스템 안정성 향상

5. **`PATCHED_VALIDATION_COMPARISON.md`** - 패치 전후 검증 비교
   - Legacy vs Hybrid Mode 성능 분석
   - KPI 달성도 평가
   - 최종 검증 결과

---

## Phase별 기술 보고서

- **`AT_COST_VALIDATION_ENHANCEMENT_REPORT.md`** - Phase 5 (At Cost 검증)
  - PDF 실제 청구 금액 추출
  - 4단계 Fuzzy 매칭
  - AED → USD 변환

- **`PDF_RATE_EXTRACTION_IMPROVEMENT_REPORT.md`** - Phase 3 (PDF 파싱)
  - pdfplumber 통합
  - Fuzzy Matching 알고리즘
  - 테이블/텍스트 추출

- **`PDF_SUMMARY_EXTRACTION_FINAL_REPORT.md`** - Phase 6 (Summary 추출)
  - 3가지 패턴 지원 (Same line, Next line, Table)
  - Summary 행 필터링
  - 환율 추출 (R.O.E.)

- **`E2E_HYBRID_INTEGRATION_TEST_REPORT.md`** - Phase 7 (E2E 테스트)
  - FastAPI + Celery + Redis 통합
  - Health Check 검증
  - 102개 항목 검증 결과

- **Phase 8 (System Optimization)**: logic_patch.md 적용
  - **Configuration 기반 정책 관리**: COST-GUARD 밴드 판정 외부 설정
  - **공용 유틸리티 통합**: cost_guard, portal_fee, rate_service
  - **PDF 매핑 개선**: rglob 전체 스캔으로 누락 방지
  - **Hybrid 회로 차단**: 자동 Legacy 전환 + 5분 복구

---

## 시스템 가이드

- **`WSL2_Redis _Honcho Hybrid System.md`** - Hybrid 시스템 설정 가이드
  - WSL2 환경 설정
  - Redis 설치 및 설정
  - Honcho 프로세스 관리

---

## 문서 사용법

### 개발자 온보딩
1. `../README.md` - **메인 시스템 문서** (Legacy vs Hybrid 모드 설명)
2. `HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md` - 전체 시스템 이해
3. `CORE_FUNCTIONS_AND_LOGIC_REFERENCE.md` - 핵심 함수 파악
4. `DEVELOPMENT_TIMELINE.md` - 개발 과정 파악

### 특정 기능 이해
- PDF 파싱: `PDF_RATE_EXTRACTION_IMPROVEMENT_REPORT.md`
- At Cost 검증: `AT_COST_VALIDATION_ENHANCEMENT_REPORT.md`
- Summary 추출: `PDF_SUMMARY_EXTRACTION_FINAL_REPORT.md`

### 시스템 설정
- `WSL2_Redis _Honcho Hybrid System.md` - 환경 구축
- `E2E_HYBRID_INTEGRATION_TEST_REPORT.md` - 테스트 방법

### 빠른 시작
```bash
# Legacy Mode (간단)
cd ../Core_Systems
export USE_HYBRID=false
python masterdata_validator.py

# Hybrid Mode (고급)
# Terminal 1: bash ../../start_hybrid_system.sh
# Terminal 2: export USE_HYBRID=true && python masterdata_validator.py
```

---

## 관련 폴더

- **`../Documentation/`** - 사용자 가이드 (USER_GUIDE.md, CONFIGURATION_GUIDE.md)
- **`../Archive/Technical_Reports_20251015/`** - 구버전 기술 보고서
- **`../Core_Systems/`** - 실제 구현 코드

---

**작성자**: AI Development Team
**프로젝트**: HVDC Invoice Audit System
**최종 업데이트**: 2025-10-16 (logic_patch.md 적용 완료)
