# ⚙️ Configuration Management Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-14
**Audience**: System Administrators, DevOps, Advanced Users

---

## 목차

1. [Configuration 파일 개요](#configuration-파일-개요)
2. [각 Configuration 파일 상세](#각-configuration-파일-상세)
3. [월별 업데이트 절차](#월별-업데이트-절차)
4. [프로젝트별 Customization](#프로젝트별-customization)
5. [포워더별 설정](#포워더별-설정)
6. [버전 관리](#버전-관리)
7. [검증 및 테스트](#검증-및-테스트)

---

## Configuration 파일 개요

### 파일 목록 및 용도

| 파일 | 용도 | 업데이트 빈도 | 중요도 |
|------|------|---------------|--------|
| `config_metadata.json` | 메타데이터 (월, 프로젝트, 환율) | 월별 | ⭐⭐⭐ |
| `config_template.json` | 변경 항목 가이드 | 1회 | ⭐ |
| `excel_schema.json` | Excel 구조 정의 | 포워더별 | ⭐⭐ |
| `config_shpt_lanes.json` | Lane Map (운송 경로) | 프로젝트별 | ⭐⭐⭐ |
| `config_contract_rates.json` | 계약 고정 요율 | 계약 변경 시 | ⭐⭐⭐ |
| `config_cost_guard_bands.json` | COST-GUARD 밴드 | 연 1회 | ⭐⭐ |
| `config_validation_rules.json` | 검증 규칙 | 연 1회 | ⭐⭐ |

---

## 각 Configuration 파일 상세

### 1. config_metadata.json

#### 구조
```json
{
    "version": "1.0.0",
    "applicable_period": "2025-09",     // 월별 변경
    "forwarder": "DSV",                 // 포워더별 변경
    "project": "HVDC_ADOPT",            // 프로젝트별 변경
    "currency_fx_date": "2025-09-30",   // 월별 변경
    "fx_rates": {
        "USD_AED": 3.6725,              // 월별 변경
        "last_updated": "2025-09-30"    // 월별 변경
    },
    "last_updated": "2025-10-14"
}
```

#### 업데이트 시나리오

**새 월 시작 (예: Oct 2025):**
```json
{
    "applicable_period": "2025-10",
    "currency_fx_date": "2025-10-31",
    "fx_rates": {
        "USD_AED": 3.6750,  // 최신 환율
        "last_updated": "2025-10-31"
    }
}
```

---

### 2. config_shpt_lanes.json

#### 구조
```json
{
    "metadata": {...},
    "sea_transport": {
        "LANE_ID": {
            "lane_id": "L01",
            "rate": 252.00,
            "route": "Port A → Destination B",
            "category": "Container",
            "port": "Khalifa Port",
            "destination": "DSV Mussafah Yard",
            "unit": "per truck"
        }
    },
    "air_transport": {...},
    "normalization_aliases": {
        "ports": {
            "KP": "Khalifa Port",
            "AUH": "Abu Dhabi Airport"
        },
        "destinations": {
            "MIRFA": "MIRFA SITE"
        }
    }
}
```

#### 신규 Lane 추가 예시

**요구사항**: Dubai Airport → New Site (600 USD)

```json
"DXB_NEW_SITE": {
    "lane_id": "L99",
    "rate": 600.00,
    "route": "Dubai Airport → New Site",
    "category": "Air",
    "port": "Dubai Airport",
    "destination": "New Site",
    "unit": "per truck",
    "description": "Air transport to new site"
}
```

**Normalization 추가:**
```json
"normalization_aliases": {
    "destinations": {
        "NEW SITE": "New Site",
        "NEW": "New Site"
    }
}
```

---

### 3. config_contract_rates.json

#### 구조
```json
{
    "metadata": {...},
    "fixed_fees": {
        "DO_FEE_AIR": {
            "rate": 80.00,
            "unit": "per shipment",
            "transport_mode": "AIR",
            "keywords": ["MASTER DO FEE", "DO FEE"]
        }
    },
    "portal_fees_aed": {
        "APPOINTMENT_FEE": {
            "rate_aed": 27.00,
            "rate_usd": 7.35,
            "tolerance_percent": 0.5
        }
    }
}
```

#### 요율 변경 시

**DO FEE 인상 (80 → 85 USD):**
```json
"DO_FEE_AIR": {
    "rate": 85.00,  // 변경
    "unit": "per shipment",
    "transport_mode": "AIR",
    "keywords": ["MASTER DO FEE", "DO FEE"]
}
```

---

### 4. excel_schema.json

#### 필수 컬럼 정의
```json
"required_columns": {
    "No": {
        "type": "int",
        "nullable": false,
        "aliases": ["No", "No.", "Item No", "Line No"]
    }
}
```

#### 포워더별 매핑
```json
"forwarder_specific_mappings": {
    "DSV": {
        "order_ref_column": "Order Ref. Number",
        "masterdata_sheet": "MasterData",
        "summary_sheet": "SEPT"
    },
    "MAERSK": {
        "order_ref_column": "Booking Number",
        "masterdata_sheet": "Invoice",
        "summary_sheet": "Summary"
    }
}
```

---

## 월별 업데이트 절차

### Step-by-Step 가이드

#### 1. 이전 월 Configuration 백업
```bash
cd Rate/
mkdir -p archives/2025-09-HVDC
cp config_metadata.json archives/2025-09-HVDC/
cp config_shpt_lanes.json archives/2025-09-HVDC/
```

#### 2. config_metadata.json 업데이트
```json
{
    "applicable_period": "2025-10",  // 09 → 10
    "currency_fx_date": "2025-10-31",
    "fx_rates": {
        "USD_AED": 3.6750,  // 최신 환율 (중앙은행 확인)
        "last_updated": "2025-10-31"
    },
    "last_updated": "2025-10-14"
}
```

#### 3. Changelog 업데이트
```json
"changelog": [
    {
        "version": "1.1.0",
        "date": "2025-10-14",
        "changes": [
            "Updated for October 2025",
            "FX rate: 3.6725 → 3.6750",
            "No lane changes"
        ]
    },
    ...
]
```

#### 4. 검증 실행
```bash
python validate_masterdata_with_config_251014.py
```

#### 5. 결과 확인 및 승인
- Results/ 디렉토리에서 최신 Excel 확인
- PASS 비율 확인 (목표: ≥50%)
- FAIL 항목 수동 검토

---

## 프로젝트별 Customization

### 신규 프로젝트 추가 (예: ADNOC-NEW)

#### 1. Metadata 생성
```bash
cp config_metadata.json config_metadata_ADNOC_NEW.json
```

```json
{
    "project": "ADNOC_NEW",
    "forwarder": "DSV",
    "applicable_period": "2025-10"
}
```

#### 2. Lane Map 추가
```json
// config_shpt_lanes.json
"sea_transport": {
    "ADNOC_NEW_ROUTE_1": {
        "lane_id": "ADNOC_01",
        "rate": 400.00,
        "port": "Jebel Ali Port",
        "destination": "ADNOC New Site"
    }
}
```

#### 3. Normalization 추가
```json
"normalization_aliases": {
    "destinations": {
        "ADNOC NEW": "ADNOC New Site",
        "ADNOC-NEW": "ADNOC New Site"
    }
}
```

---

## 포워더별 설정

### DSV (현재 구현됨)
- Order Ref 패턴: `HVDC-ADOPT-SCT-0123`
- Mode 식별: HE (AIR), SCT (CONTAINER)
- MasterData Sheet: "MasterData"
- Summary Sheet: "SEPT"

### MAERSK (추후 구현)
- Order Ref 패턴: `MAE-FCL-001234`
- Mode 식별: FCL (CONTAINER), AIR (AIR)
- MasterData Sheet: "Invoice"
- Summary Sheet: "Summary"

### Adapter 구현 (예정)
```python
# forwarder_adapters/dsv_adapter.py
class DSVAdapter(ForwarderAdapter):
    def identify_transport_mode(self, order_ref: str) -> str:
        if 'HE' in order_ref:
            return 'AIR'
        elif 'SCT' in order_ref:
            return 'CONTAINER'
        return 'UNKNOWN'
```

---

## 버전 관리

### Semantic Versioning
- **MAJOR**: 호환성을 깨는 변경 (1.x.x → 2.0.0)
- **MINOR**: 새 기능 추가, 호환성 유지 (1.0.x → 1.1.0)
- **PATCH**: 버그 수정 (1.0.0 → 1.0.1)

### 아카이브 구조
```
Rate/
├── archives/
│   ├── 2025-08-HVDC/
│   │   ├── config_metadata.json
│   │   └── config_shpt_lanes_v1.0.json
│   ├── 2025-09-HVDC/
│   │   ├── config_metadata.json
│   │   └── config_shpt_lanes_v1.1.json
│   └── README.md (archive index)
└── active/ (현재 사용 중)
    ├── config_metadata.json
    └── config_shpt_lanes.json
```

---

## 검증 및 테스트

### Configuration 검증 스크립트
```python
# validate_config.py (추후 구현)
def validate_config_files():
    """모든 Config 파일 JSON 유효성 검증"""
    required_files = [
        'config_metadata.json',
        'config_shpt_lanes.json',
        'config_contract_rates.json'
    ]

    for file in required_files:
        validate_json_schema(file)
        check_required_fields(file)
        verify_data_types(file)
```

### Regression Test
```bash
# 이전 월 인보이스로 검증
python validate_masterdata_with_config_251014.py --test-mode --baseline sept_2025_baseline.json
```

---

## Best Practices

### ✅ DO
- Configuration 변경 전 백업
- 변경 사항을 changelog에 기록
- 변경 후 즉시 검증 실행
- 버전 번호 체계적 관리

### ❌ DON'T
- 직접 코드에 요율 하드코딩
- 여러 파일 동시 수정 (하나씩 변경 후 검증)
- 백업 없이 변경
- 검증 없이 production 적용

---

## 트러블슈팅

### Configuration 로딩 실패
```
ERROR - Failed to load config_shpt_lanes.json
```

**해결:**
1. JSON 구문 오류 확인 (trailing comma, 따옴표 등)
2. 파일 인코딩 확인 (UTF-8)
3. 파일 경로 확인

### Lane Rate가 None 반환
```
DEBUG - Lane Rate for 'Port A → Dest B': None
```

**해결:**
1. config_shpt_lanes.json에 해당 lane 존재 여부 확인
2. port/destination 철자 정확히 일치하는지 확인 (대소문자 구분)
3. normalization_aliases에 약어 등록 확인

---

**문서 작성일**: 2025-10-14
**작성자**: MACHO-GPT v3.4-mini
**다음 업데이트 예정**: Configuration 자동 검증 스크립트 추가

