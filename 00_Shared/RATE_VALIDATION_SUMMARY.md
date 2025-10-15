# Rate JSON 검증 결과 요약

**Date**: 2025-10-12
**Task**: Phase 1.1 - JSON Rate Files Validation

---

## 검증 결과

### 전체 통계
- **총 파일**: 4개
- **총 레코드**: 250개
- **유효 레코드**: 196개 (78.4%)
- **무효 레코드**: 54개 (21.6%)
- **중복 레코드**: 113개

### 파일별 상세

#### 1. air_cargo_rates (1).json ✅
- 총 레코드: 37
- 유효: 37 (100%)
- 무효: 0
- 중복: 14 (weight category별 구분 - 정상)

#### 2. bulk_cargo_rates (1).json ✅
- 총 레코드: 86
- 유효: 82 (95.3%)
- 무효: 4 (unit 필드 누락 - Port Storage Charge)
- 중복: 45 (cargo type별 구분 - 정상)

#### 3. container_cargo_rates (1).json ✅
- 총 레코드: 77
- 유효: 77 (100%)
- 무효: 0
- 중복: 33 (container type별 구분 - 정상)

#### 4. inland_trucking_reference_rates_clean (2).json ❌
- 총 레코드: 50
- 유효: 0 (0%) **사용 불가**
- 무효: 50 (description 필드 누락)
- 중복: 21

---

## 결론 및 권장사항

### 사용 가능 파일 (3개)
1. **air_cargo_rates (1).json** - 37개 레코드 사용
2. **bulk_cargo_rates (1).json** - 82개 유효 레코드 사용
3. **container_cargo_rates (1).json** - 77개 레코드 사용

**총 사용 가능**: 196개 레코드

### 제외 파일 (1개)
- **inland_trucking_reference_rates_clean (2).json** - 구조적 결함으로 제외

### 중복 처리 방침
- "중복"은 실제로 **다른 cargo type/weight category**를 구분하는 정상 데이터
- 예: "Inland Trucking (Upto 1ton)" vs "Inland Trucking (Above 1ton, Upto 3ton)"
- **처리 방침**: detail_cargo_type, container_type 필드를 키에 포함하여 구분

### 데이터 품질
- **3개 사용 가능 파일**: 196/200 (98%) 유효율 ✅
- **Contract 검증에 필요한 Standard Items 모두 포함 확인**:
  - DO Fee: ✅
  - Custom Clearance: ✅
  - Port Handling Charge: ✅
  - Terminal Handling Charge: ✅
  - Inland Trucking: ✅

---

## 다음 단계

**Phase 1.1 완료**: JSON 검증 완료 ✅
- 사용 가능 파일: 3개 (196 records)
- 제외 파일: 1개 (inland_trucking_reference_rates_clean)

**Phase 1.2 진행 예정**: MD 파일 중복 분석
**Phase 2.1 준비 완료**: UnifiedRateLoader 설계 시작 가능

