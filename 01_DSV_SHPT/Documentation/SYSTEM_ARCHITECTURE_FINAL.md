# 🏗️ 최종 시스템 아키텍처 - SHPT vs DOMESTIC 분리

## 📋 시스템 분리 완료 상태

### ✅ SHPT 전용 시스템 (현재 프로젝트)
```
invoice-audit/
├── shpt_audit_system.py              # SHPT 전용 메인 시스템
├── audit_runner_enhanced.py          # SHPT 감사 실행 엔진
├── joiners_enhanced.py               # SHPT 데이터 조인 및 분류
├── rules_enhanced.py                 # SHPT 검증 규칙 및 밴드
├── test_portal_fee_system.py         # SHPT 테스트 스크립트
└── 기타 SHPT 관련 파일들...
```

### ❌ DOMESTIC 시스템 (별도 프로젝트 필요)
```
domestic-invoice-audit/               # 별도 프로젝트 디렉토리
├── domestic_audit_system.py          # DOMESTIC 전용 메인 시스템
├── domestic_joiners.py               # DOMESTIC 데이터 조인
├── domestic_rules.py                 # DOMESTIC 검증 규칙
└── 기타 DOMESTIC 관련 파일들...
```

## 🔧 시스템별 특징 비교

| 구분 | SHPT 시스템 | DOMESTIC 시스템 |
|------|-------------|-----------------|
| **범위** | Shipment Invoice Processing | Inland Transportation |
| **계약번호** | HVDC-SHPT-2025-001 | HVDC-ITC-2025-001 |
| **Incoterm** | FOB (assumed) | DDP (assumed) |
| **포트** | Khalifa Port, Jebel Ali Port | Khalifa Port, Abu Dhabi Airport |
| **목적지** | MIRFA, SHUWEIHAT, DSV Yard | MIRFA, SHUWEIHAT, DSV Yard |
| **단위** | per truck, per cntr, per BL | per truck, per RT |
| **검증규칙** | 8개 규칙 (R-001~R-008) | 5개 규칙 (R-001~R-005) |
| **예외처리** | 3개 예외 (EX-001~EX-003) | 2개 예외 (EX-001~EX-002) |

## 🎯 핵심 차이점

### 1. **시스템 유형**
- **SHPT**: `system_type = "SHPT"`
- **DOMESTIC**: `system_type = "DOMESTIC_INVOICE"`

### 2. **계약 정보**
- **SHPT**: `contract_no = "HVDC-SHPT-2025-001"`
- **DOMESTIC**: `contract_no = "HVDC-ITC-2025-001"`

### 3. **Incoterm**
- **SHPT**: `incoterm = "FOB (assumed)"`
- **DOMESTIC**: `incoterm = "DDP (assumed)"`

### 4. **포트 정규화**
- **SHPT**: Khalifa Port, Jebel Ali Port, Abu Dhabi Port
- **DOMESTIC**: Khalifa Port, Abu Dhabi Airport, Dubai Airport

### 5. **검증 규칙**
- **SHPT**: 8개 규칙 (R-001~R-008)
- **DOMESTIC**: 5개 규칙 (R-001~R-005)

## 🚀 실행 방법

### SHPT 시스템 실행
```bash
python shpt_audit_system.py
```

### DOMESTIC 시스템 실행 (별도 프로젝트)
```bash
# 별도 프로젝트에서 실행
python domestic_audit_system.py
```

## 📊 중복 제거 완료

### ✅ 제거된 중복 파일들
1. `updated_architecture_system.py` - DOMESTIC과 중복
2. `domestic_invoice_system.py` - 기본 버전
3. `enhanced_domestic_system.py` - 개선 버전

### ✅ 남은 SHPT 전용 파일들
1. `shpt_audit_system.py` - SHPT 전용 메인 시스템
2. `audit_runner_enhanced.py` - SHPT 감사 실행 엔진
3. `joiners_enhanced.py` - SHPT 데이터 조인 및 분류
4. `rules_enhanced.py` - SHPT 검증 규칙 및 밴드

## 🎯 결론

- ✅ **SHPT와 DOMESTIC 시스템 완전 분리**
- ✅ **중복 코드 제거 완료**
- ✅ **각 시스템별 고유한 설정 및 로직 적용**
- ✅ **명확한 시스템 경계 설정**

**SHPT 전용 Invoice Audit System이 성공적으로 분리되어 중복 없이 운영 가능합니다!** 🎉
