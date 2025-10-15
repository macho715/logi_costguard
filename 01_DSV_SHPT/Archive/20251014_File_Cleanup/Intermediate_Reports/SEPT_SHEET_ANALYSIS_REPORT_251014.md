# SEPT 시트 구조 분석 보고서

**작성일**: 2025-10-14
**프로젝트**: HVDC Invoice Audit - DSV SHPT System
**분석 대상**: SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm - "SEPT" Sheet

---

## 📋 Executive Summary

### 주요 발견
SEPT 시트는 **28개 Shipment의 요약 정보**를 담고 있으며, MasterData(102개 Line Items)와는 **완전히 다른 구조**입니다.

| 구분 | SEPT 시트 | MasterData 시트 |
|------|-----------|----------------|
| **성격** | Shipment별 **요약** | Line Item별 **상세** |
| **행 개수** | 28 Shipments | 102 Line Items |
| **열 개수** | 26 columns | 13 columns |
| **주요 정보** | POL/POD, Mode, 요금 합계 | DESCRIPTION, RATE, 개별 비용 |
| **연결 키** | Shpt Ref | Order Ref. Number |

### 핵심 가치
1. **Transport Mode 명시** (AIR/FCL) - DO FEE 요율 자동 구분 가능
2. **POL/POD 정보** - Lane Map 자동 확장 가능
3. **Shipment별 요금 합계** - MasterData 검증에 활용 가능

---

## 1️⃣ SEPT 시트 구조 상세

### 1.1 기본 정보
- **행 개수**: 28 Shipments
- **열 개수**: 26 columns
- **데이터 범위**: (28, 26)

### 1.2 컬럼 구조 (26개)

#### A. 기본 정보 컬럼 (9개)
| # | 컬럼명 | Non-null | 설명 |
|---|--------|----------|------|
| 1 | S/No | 28 (100%) | 일련번호 |
| 2 | Shpt Ref | 28 (100%) | **Shipment 참조 번호** (연결 키) |
| 3 | Job # | 28 (100%) | Job Number |
| 4 | Type | 28 (100%) | Shipment Type |
| 5 | BL # | 28 (100%) | Bill of Lading Number |
| 6 | **POL** | 28 (100%) | **Port of Loading** (출발 항구) |
| 7 | **POD** | 28 (100%) | **Port of Discharge** (도착 항구) |
| 8 | **Mode** | 28 (100%) | **운송 모드 (AIR/FCL/LCL)** |
| 9 | No. Of CNTR | 28 (100%) | Container 수량 |

#### B. 물량 정보 컬럼 (3개)
| # | 컬럼명 | Non-null | 설명 |
|---|--------|----------|------|
| 10 | Volume | 28 (100%) | 부피 |
| 11 | Quantity | 28 (100%) | 수량 |
| 12 | # Trips | 27 (96.4%) | Transportation Trips 수 |

#### C. Customs 정보 컬럼 (2개)
| # | 컬럼명 | Non-null | 설명 |
|---|--------|----------|------|
| 13 | Bill of Entry Number | 28 (100%) | BOE 번호 |
| 14 | BOE Issued Date | 28 (100%) | BOE 발행일 |

#### D. **요금 컬럼 (7개) - 가장 중요!**
| # | 컬럼명 | Non-null | 비율 | 설명 |
|---|--------|----------|------|------|
| 15 | **MASTER DO CHARGE** | 24 (85.7%) | ✅ | **Master DO Fee 합계** |
| 16 | **CUSTOMS CLEARANCE CHARGE** | 24 (85.7%) | ✅ | **Customs Clearance Fee 합계** |
| 17 | HOUSE DO CHARGE | 0 (0%) | ❌ | 사용 안 함 |
| 18 | **PORT HANDLING CHARGE** | 6 (21.4%) | ⚠️ | Terminal Handling 등 |
| 19 | **TRANSPORTATION CHARGE** | 6 (21.4%) | ⚠️ | Inland Transportation |
| 20 | TRANSPORTATION CHARGE2 | 0 (0%) | ❌ | 사용 안 함 |
| 21 | DUTY RELATED CHARGES | 3 (10.7%) | ⚠️ | Duty Outlay 등 |

#### E. 기타 컬럼 (5개)
| # | 컬럼명 | Non-null | 설명 |
|---|--------|----------|------|
| 22 | ADDITIONAL AMOUNT | 0 (0%) | 사용 안 함 |
| 23 | AT COST AMOUNT | 7 (25%) | At Cost 항목 합계 |
| 24 | **GRAND TOTAL (USD)** | 28 (100%) | **총 합계** |
| 25 | Remarks | 28 (100%) | 비고 |
| 26 | Unnamed: 0 | 0 (0%) | 빈 컬럼 |

---

## 2️⃣ 샘플 데이터 분석

### 2.1 기본 정보 샘플
```
S/No                  Shpt Ref   POL   POD Mode No. Of CNTR
   1       HVDC-ADOPT-SCT-0126 KRPUS AEKHL  FCL           3
   2       HVDC-ADOPT-SCT-0127 CNSGH AEKHL  FCL           1
   3       HVDC-ADOPT-SCT-0122 KRPUS AEKHL  FCL           1
   4       HVDC-ADOPT-SCT-0131 KRICN AEAUH  AIR           0  <-- AIR 모드!
   5 HVDC-ADOPT-SCT-0123, 0124 KRPUS AEKHL  FCL           1
   6       HVDC-ADOPT-SCT-0134 KRICN AEAUH  AIR           0  <-- AIR 모드!
   7        HVDC-ADOPT-HE-0471 BEANR AEKHL  FCL           4
   8        HVDC-ADOPT-HE-0472 BEANR AEKHL  FCL           6
   9        HVDC-ADOPT-HE-0473 BEANR AEKHL  FCL           7
```

**발견**:
- **SCT-0131, SCT-0134**: Mode = **AIR**인데 Shpt Ref는 SCT (CONTAINER)
- **HE-0471~0473**: Mode = **FCL**인데 Shpt Ref는 HE (AIR로 추정)
- **No. Of CNTR = 0**: AIR 모드일 때

### 2.2 요금 컬럼 샘플
```
                Shpt Ref  MASTER DO  CUSTOMS  PORT HANDLING  TRANSPORTATION
     HVDC-ADOPT-SCT-0126      150.0    150.0         1330.0          1512.0
     HVDC-ADOPT-SCT-0127      150.0    150.0          372.0           252.0
     HVDC-ADOPT-SCT-0122      150.0    150.0          372.0           252.0
     HVDC-ADOPT-SCT-0131       80.0    150.0         1174.8           200.0  <-- DO FEE 80!
HVDC-ADOPT-SCT-0123, 0124      150.0    150.0          479.0           252.0
     HVDC-ADOPT-SCT-0134       80.0    150.0         1197.9           910.0  <-- DO FEE 80!
      HVDC-ADOPT-HE-0471      150.0    150.0            NaN             NaN  <-- DO FEE 150!
      HVDC-ADOPT-HE-0472      150.0    150.0            NaN             NaN  <-- DO FEE 150!
      HVDC-ADOPT-HE-0473      150.0    150.0            NaN             NaN  <-- DO FEE 150!
```

---

## 3️⃣ 중대 발견: FAIL 16건의 진짜 원인!

### 🔴 Problem: Mode 정보 불일치

**FAIL 항목 분석 결과**:
1. **SCT-0131** (Mode = AIR):
   - SEPT: MASTER DO = **80 USD** ✅
   - MasterData: RATE = 80 USD
   - Python 검증: Ref Rate = **150 USD** (SCT → CONTAINER로 오판)
   - **Delta: -46.67%** → FAIL

2. **SCT-0134** (Mode = AIR):
   - SEPT: MASTER DO = **80 USD** ✅
   - MasterData: RATE = 80 USD
   - Python 검증: Ref Rate = **150 USD** (SCT → CONTAINER로 오판)
   - **Delta: -46.67%** → FAIL

3. **HE-0471~0475** (Mode = FCL):
   - SEPT: MASTER DO = **150 USD** ✅
   - MasterData: RATE = 150 USD
   - Python 검증: Ref Rate = **80 USD** (HE → AIR로 오판)
   - **Delta: +87.50%** → FAIL (10건)

### 🎯 근본 원인

**현재 로직 (validate_masterdata_with_config_251014.py)**:
```python
def _identify_transport_mode(self, row: pd.Series) -> str:
    order_ref = str(row.get("Order Ref. Number", "")).upper()
    if "HE" in order_ref or "-HE-" in order_ref:
        return "AIR"
    elif "SCT" in order_ref or "-SCT-" in order_ref:
        return "CONTAINER"
    return "CONTAINER"
```

**문제점**:
- Order Ref의 HE/SCT 패턴으로만 판단
- **실제 Mode 정보 무시**
- SCT인데 AIR 모드인 경우 오판 (2건)
- HE인데 FCL 모드인 경우 오판 (10건)

### ✅ 해결 방안

**SEPT 시트의 Mode 정보 활용**:
```python
# 1. SEPT 시트 로드 (Shipment별 Mode 정보)
sept_df = pd.read_excel(excel_path, sheet_name="SEPT")
mode_lookup = dict(zip(sept_df["Shpt Ref"], sept_df["Mode"]))

# 2. Order Ref로 Mode 조회
def _identify_transport_mode(self, row: pd.Series) -> str:
    order_ref = str(row.get("Order Ref. Number", ""))

    # SEPT 시트에서 Mode 직접 조회
    if order_ref in self.mode_lookup:
        mode = self.mode_lookup[order_ref]
        if mode == "AIR":
            return "AIR"
        elif mode in ["FCL", "LCL"]:
            return "CONTAINER"

    # Fallback: 기존 로직
    if "HE" in order_ref.upper():
        return "AIR"
    return "CONTAINER"
```

---

## 4️⃣ SEPT vs MasterData 비교

### 4.1 컬럼 비교

**공통 컬럼**: 1개만! (S/No)

**SEPT에만 있는 중요 컬럼 (25개)**:
1. **Shpt Ref** - Shipment 참조 번호
2. **POL** - Port of Loading
3. **POD** - Port of Discharge
4. **Mode** - **AIR/FCL/LCL (가장 중요!)**
5. **No. Of CNTR** - Container 수량
6. **# Trips** - Transportation Trips
7. **MASTER DO CHARGE** - DO Fee 합계
8. **CUSTOMS CLEARANCE CHARGE** - Customs Fee 합계
9. **PORT HANDLING CHARGE** - THC 등 합계
10. **TRANSPORTATION CHARGE** - Inland Transport 합계
11. **GRAND TOTAL (USD)** - 총 합계

**MasterData에만 있는 컬럼 (12개)**:
1. **Order Ref. Number** - Line Item 참조
2. **DESCRIPTION** - 비용 항목 상세
3. **RATE** - 단가
4. **Q'TY** - 수량
5. **TOTAL (USD)** - 금액
6. **RATE SOURCE** - 요율 출처

### 4.2 데이터 관계

| 관계 | 설명 |
|------|------|
| **1:N** | 1 Shipment (SEPT) → N Line Items (MasterData) |
| **연결 키** | Shpt Ref ↔ Order Ref. Number |
| **검증** | SEPT.GRAND TOTAL = SUM(MasterData.TOTAL) by Shpt Ref |

---

## 5️⃣ 활용 가능 정보 및 개선 방안

### 🎯 Priority 1: 즉시 개선 (FAIL 16건 해결)

#### 1.1 Mode 정보 활용 - **FAIL 12건 해결**
```python
# SEPT 시트에서 Mode 정보 로드
sept_mode_lookup = load_sept_mode_info()

# Transport Mode 식별 시 SEPT Mode 우선
def _identify_transport_mode(order_ref):
    if order_ref in sept_mode_lookup:
        return "AIR" if sept_mode_lookup[order_ref] == "AIR" else "CONTAINER"
    # Fallback: 기존 로직
    return identify_by_pattern(order_ref)
```

**예상 효과**:
- FAIL 16건 → 4건 (Portal Fee 환율 이슈만 남음)
- FAIL 비율: 15.7% → 3.9%
- **75% 감소** ⬇️

#### 1.2 Portal Fee 환율 이슈 해결 - **FAIL 4건 해결**
(이미 앞서 제안됨 - PDF 파싱 개선)

### 🚀 Priority 2: 중기 개선 (REVIEW_NEEDED 감소)

#### 2.1 POL/POD로 Lane Map 자동 확장
```python
# SEPT 시트에서 경로 정보 추출
transportation_lanes = sept_df[["POL", "POD", "TRANSPORTATION CHARGE", "# Trips"]]

# 평균 요율 계산
lane_rates = transportation_lanes.groupby(["POL", "POD"]).agg({
    "TRANSPORTATION CHARGE": "mean",
    "# Trips": "mean"
}).reset_index()

# Lane Map에 자동 추가
for _, row in lane_rates.iterrows():
    add_to_lane_map(row["POL"], row["POD"], row["TRANSPORTATION CHARGE"] / row["# Trips"])
```

**예상 효과**:
- Transportation 미매칭 18건 → 5건 이하
- **70% 감소** ⬇️

#### 2.2 Shipment별 합계 검증
```python
# MasterData를 Shpt Ref로 그룹화
masterdata_totals = masterdata_df.groupby("Order Ref. Number")["TOTAL (USD)"].sum()

# SEPT GRAND TOTAL과 비교
for shpt_ref in sept_df["Shpt Ref"]:
    sept_total = sept_df.loc[sept_df["Shpt Ref"] == shpt_ref, "GRAND TOTAL (USD)"].values[0]
    masterdata_total = masterdata_totals.get(shpt_ref, 0)

    if abs(sept_total - masterdata_total) > sept_total * 0.01:  # 1% 오차
        flag_discrepancy(shpt_ref, sept_total, masterdata_total)
```

### 💡 Priority 3: 장기 개선

1. **Container 수량 검증**: No. Of CNTR로 THC 수량 검증
2. **Trips 수 검증**: # Trips로 Transportation 요금 검증
3. **BOE 정보 활용**: Customs 관련 비용 검증

---

## 6️⃣ 구현 계획

### Phase 1: Mode 정보 통합 (즉시)

**파일**: `validate_masterdata_with_config_251014.py`

1. **SEPT 시트 로드 추가**:
```python
def __init__(self, ...):
    # 기존 초기화...

    # SEPT 시트에서 Mode 정보 로드
    sept_df = pd.read_excel(self.excel_file, sheet_name="SEPT")
    self.mode_lookup = dict(zip(sept_df["Shpt Ref"], sept_df["Mode"]))
    self.pol_pod_lookup = dict(zip(sept_df["Shpt Ref"],
                                    zip(sept_df["POL"], sept_df["POD"])))
```

2. **_identify_transport_mode 수정**:
```python
def _identify_transport_mode(self, row: pd.Series) -> str:
    """Transport Mode 식별 (SEPT Mode 우선)"""

    order_ref = str(row.get("Order Ref. Number", ""))

    # Priority 1: SEPT 시트의 Mode 정보
    if order_ref in self.mode_lookup:
        mode = self.mode_lookup[order_ref]
        if mode == "AIR":
            return "AIR"
        elif mode in ["FCL", "LCL"]:
            return "CONTAINER"

    # Priority 2: Order Ref 패턴 (Fallback)
    order_ref_upper = order_ref.upper()
    if "HE" in order_ref_upper or "-HE-" in order_ref_upper:
        return "AIR"
    elif "SCT" in order_ref_upper or "-SCT-" in order_ref_upper:
        return "CONTAINER"

    # Priority 3: DESCRIPTION 키워드 (Fallback)
    description = str(row.get("DESCRIPTION", "")).upper()
    air_keywords = ["AIR", "AIRPORT", "FLIGHT"]
    if any(kw in description for kw in air_keywords):
        return "AIR"

    return "CONTAINER"
```

### Phase 2: 재검증 및 결과 확인

1. 전체 MasterData 재검증
2. FAIL 16건 → 4건 확인
3. 최종 보고서 생성

---

## 7️⃣ 예상 개선 효과

| 지표 | 현재 | Phase 1 후 | Phase 2 후 | 개선율 |
|------|------|------------|------------|--------|
| **FAIL 건수** | 16건 (15.7%) | 4건 (3.9%) | 0건 (0%) | **-100%** |
| **FAIL 원인** | Mode 오판 12건 + 환율 4건 | 환율 4건만 | 없음 | - |
| **REVIEW_NEEDED** | 50건 (49.0%) | 50건 | 30건 (30%) | **-40%** |
| **PASS** | 36건 (35.3%) | 48건 (47.1%) | 72건 (70%+) | **+100%** |
| **Contract 검증률** | 75.0% | 90%+ | 95%+ | **+27%** |

---

## 8️⃣ 결론

### 핵심 발견
1. **SEPT 시트에 Mode 정보 있음** - 현재 활용 안 됨
2. **FAIL 16건 중 12건이 Mode 오판 때문**
3. **POL/POD 정보로 Lane Map 확장 가능**

### 즉시 조치 필요
1. ✅ **SEPT Mode 정보 통합** → FAIL 75% 감소
2. ✅ **Portal Fee 환율 개선** → FAIL 100% 해결
3. ⚠️ **POL/POD Lane Map 확장** → REVIEW_NEEDED 40% 감소

### 장기 가치
- Shipment별 합계 검증
- Container/Trips 수량 검증
- BOE 정보 활용

---

**작성자**: MACHO-GPT v3.6-APEX
**분석 완료**: 2025-10-14
**다음 단계**: SEPT Mode 정보 통합 구현

