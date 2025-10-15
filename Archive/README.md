# Archive 디렉토리

**목적**: 개발 과정에서 생성된 임시 파일, 분석 스크립트, 구버전 시스템 보관
**최종 업데이트**: 2025-10-15 02:45 AM

---

## 디렉토리 구조

```
Archive/
├── Utilities_20251015/          (분석 및 정리 스크립트)
├── 02_DSV_DOMESTIC_Legacy_20251013/  (구버전 Domestic 시스템)
└── 20251013_Before_Cleanup/     (정리 전 백업)
```

---

## Utilities_20251015/ (8개 파일)

### 분석 스크립트 (4개)
| 파일 | 목적 | 작성일 |
|------|------|--------|
| `analyze_legacy_files.py` | 레거시 파일 분석 | 2025-10-13 |
| `create_file_inventory.py` | 파일 목록 생성 | 2025-10-14 |
| `identify_duplicates.py` | 중복 파일 식별 | 2025-10-14 |
| `move_to_archive.py` | 파일 Archive 이동 | 2025-10-14 |

### 정리 도구 (2개)
| 파일 | 목적 | 작성일 |
|------|------|--------|
| `domestic_validator_v2.py` | Domestic 검증 v2 (구버전) | 2025-10-13 |
| `run_domestic_audit_v2.py` | Domestic 감사 실행 | 2025-10-13 |

### 분석 결과 (2개)
| 파일 | 내용 | 크기 |
|------|------|------|
| `FILE_INVENTORY.xlsx` | 전체 파일 목록 | ~500 rows |
| `DUPLICATE_ANALYSIS.xlsx` | 중복 파일 분석 | ~100 rows |

---

## 02_DSV_DOMESTIC_Legacy_20251013/ (131개 파일)

### 개요
- **보관일**: 2025-10-13
- **목적**: Domestic 시스템 구버전 보관
- **사유**: Shipment 시스템으로 통합

### 주요 파일
- `domestic_audit_system.py`: 구버전 감사 시스템
- `domestic_pdf_parser.py`: 구버전 PDF 파서
- 37개 Excel 파일: 중간 결과물
- 33개 Python 스크립트: 분석 도구
- 20개 JSON/CSV: Configuration 파일

---

## 20251013_Before_Cleanup/ (36개 파일)

### 개요
- **백업일**: 2025-10-13
- **목적**: 대규모 정리 전 백업
- **복원**: 필요시 원본 파일 복원 가능

### 주요 파일
- 13개 Excel: 검증 보고서
- 8개 CSV: 중간 데이터
- 8개 JSON: 설정 파일
- 7개 Python: 분석 스크립트

---

## Archive 정책

### 보관 기간
| 유형 | 기간 | 사유 |
|------|------|------|
| 분석 스크립트 | 6개월 | 향후 참조 가능성 |
| 구버전 시스템 | 1년 | 복원 필요시 대비 |
| 백업 파일 | 3개월 | 단기 복원용 |

### 삭제 조건
- ✅ 프로젝트 종료 후 보관 기간 경과
- ✅ 더 이상 참조되지 않음
- ✅ 최신 시스템으로 완전 대체

### 주의사항
- ⚠️ Archive 파일 직접 수정 금지
- ⚠️ 복원 시 최신 시스템과 호환성 확인
- ⚠️ 삭제 전 담당자 승인 필요

---

## Archive 통계

### 파일 수
```
Utilities_20251015/           8개
02_DSV_DOMESTIC_Legacy/     131개
20251013_Before_Cleanup/     36개
─────────────────────────────────
총계                        175개
```

### 디스크 사용량 (예상)
```
Utilities_20251015/          ~15 MB
02_DSV_DOMESTIC_Legacy/     ~120 MB
20251013_Before_Cleanup/     ~45 MB
─────────────────────────────────
총계                        ~180 MB
```

---

## 복원 가이드

### 분석 스크립트 복원
```bash
# 원본 위치로 복사
cp Archive/Utilities_20251015/analyze_legacy_files.py .
```

### 구버전 시스템 참조
```bash
# 특정 파일 열람
cd Archive/02_DSV_DOMESTIC_Legacy_20251013/
python -c "import sys; sys.path.insert(0, '.'); import domestic_audit_system; help(domestic_audit_system)"
```

---

## 문의

### Archive 관련 질문
- 담당자: AI Development Team
- 이메일: (프로젝트 담당자)

### 파일 복원 요청
1. 복원 필요 파일 목록 제공
2. 복원 사유 명시
3. 담당자 승인 대기

---

**작성자**: AI Development Team
**최종 업데이트**: 2025-10-15 02:45 AM


