DOMESTIC 검증 시스템의 주요 로직과 알고리즘을 참조 파일과 함께 보고하겠습니다.

[3 tools called]

# 📋 DOMESTIC 검증 시스템 - 주요 로직 및 알고리즘 보고서

**작성일**: 2025-10-13
**시스템**: DOMESTIC Invoice Audit v1.0
**검증 대상**: Inland Transportation (국내 육상 운송)

---

## 📁 핵심 참조 파일 목록

### 1. 메인 시스템 파일

| 파일명 | 경로 | 역할 | 라인 수 |
|--------|------|------|---------|
| **domestic_sept_2025_audit.py** | `02_DSV_DOMESTIC/Core_Systems/` | 9월 2025 실행 시스템 | 508줄 |
| **domestic_audit_system.py** | `02_DSV_DOMESTIC/Core_Systems/` | 핵심 검증 로직 | 583줄 |
| **domestic_validator_patched.py** | `02_DSV_DOMESTIC/Core_Systems/` | patch.md 알고리즘 구현 | 239줄 |
| **run_domestic_sept2025.py** | `02_DSV_DOMESTIC/Core_Systems/` | 실행 진입점 | 14줄 |

### 2. 참조 문서 및 데이터

| 파일명 | 경로 | 역할 | 크기 |
|--------|------|------|------|
| **patch.md** | `02_DSV_DOMESTIC/` | 519건 통합 검증 알고리즘 설명 | 15KB, 312줄 |
| **DOMESTIC_with_distances.xlsx** | `02_DSV_DOMESTIC/` | 참조 레인 맵 (거리 포함) | 82KB |
| **domestic_result.artifact.json** | `02_DSV_DOMESTIC/` | PRISM 검증 아티팩트 | 4.6KB |

### 3. 외부 참조 (v2 스크립트)

| 파일명 | 경로 | 역할 |
|--------|------|------|
| **run_domestic_audit_v2.py** | `HVDC_Invoice_Audit/` | v2 실행 스크립트 |
| **domestic_validator_v2.py** | `HVDC_Invoice_Audit/` | v2 검증 로직 (307줄) |

---

## 🔧 핵심 알고리즘 (5단계 파이프라인)

### Algorithm 1: 데이터 정규화 (Normalization)

**참조**:
- `domestic_sept_2025_audit.py` (72-103줄)
- `domestic_validator_patched.py` (44-103줄)
- `patch.md` (섹션 1.A)

**로직**:
```python
# 1. Origin/Destination 정규화 (30+ 패턴)
NORMALIZE_MAP = {
    r'\bDSV\s*MUSSAFAH\s*YARD\b': 'DSV Mussafah Yard',
    r'\bMOSB\b|AL\s*MASA?OOD\b': 'Al Masaood (MOSB)',
    r'\bMIRFA\b|MIRFA\s*SITE': 'MIRFA SITE',
    r'\bSHUWEIHAT\b': 'SHUWEIHAT Site',
    r'\bMINA\s*(FREE\s*PORT|ZAYED)\b': 'Mina Zayed Port',
    # ... 30+ 규칙
}

# 2. Vehicle 정규화
FB → FLATBED
LB → LOWBED
3 TON PICKUP/PU → 3 TON PU
FLATBED (HAZMAT) → FLATBED HAZMAT

# 3. Unit 통일: 'per truck'
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_sept_2025_audit.py (Lines 44-103)
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 44-160)
```

---

### Algorithm 2: 참조 레인 매칭 (Reference Lane Join)

**참조**:
- `domestic_audit_system.py` (140-180줄)
- `patch.md` (섹션 1.B, 162-173줄)

**로직**:
```python
# 1. Exact Match (우선순위 1)
key = f"{origin_norm}||{destination_norm}||{vehicle}||{unit}"
if key in approved_lane_map:
    return approved_lane_map[key]  # median_rate_usd

# 2. Similarity Join (≥0.60, 우선순위 2)
similarity_score = (
    0.35 × origin_match +      # Origin 일치도
    0.35 × destination_match + # Destination 일치도
    0.10 × vehicle_match +     # Vehicle 일치도
    0.10 × distance_closeness + # ≤15km decay
    0.10 × rate_closeness      # ±30% decay
)

if similarity_score >= 0.60:
    return best_candidate.median_rate_usd

# 3. Fallback (데이터셋 중앙값)
return dataset_median_by_vehicle_type
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_audit_system.py (Lines 140-280)
patch.md (Lines 162-173: "3) lane ref (dataset median fallback)")
```

---

### Algorithm 3: Delta % 계산 및 COST-GUARD 밴드

**참조**:
- `domestic_audit_system.py` (58-63줄)
- `patch.md` (175-181줄)

**로직**:
```python
# 1. Delta % 계산
delta_pct = ((draft_rate - ref_rate) / ref_rate) * 100.0

# 2. COST-GUARD 밴드 결정
if abs(delta_pct) <= 2.00:  → PASS
elif abs(delta_pct) <= 5.00: → WARN
elif abs(delta_pct) <= 10.00: → HIGH
else:                         → CRITICAL

# 3. Auto-Fail 규칙
if abs(delta_pct) > 15.00:  → FAIL (즉시 거부)
```

**밴드 정의 위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_sept_2025_audit.py (Lines 54-60)
02_DSV_DOMESTIC/Core_Systems/domestic_audit_system.py (Lines 58-63)
patch.md (Lines 34, 175-181)
```

---

### Algorithm 4: 초근거리 & 고정요금 의심 탐지

**참조**:
- `domestic_validator_patched.py` (183-206줄)
- `patch.md` (섹션 1.C, 183-205줄)

**로직**:
```python
# 1. 초근거리 정의
SHORT_RUN_KM = 10.0
VERY_SHORT_KM = 2.0

# 2. Per-km 분석
per_km = rate_usd / distance_km

# 3. IQR 기반 이상치 탐지
for each vehicle_type:
    p25, p75 = percentile_25, percentile_75
    IQR = p75 - p25

    if per_km > p75 + 1.5 × IQR:
        flag = 'HIGH_PERKM_SHORT'

# 4. 절대 임계값
if distance_km <= 2km AND per_km >= 40 USD/km:
    flag = 'FIXED_COST_SUSPECT'

if per_km >= 100 USD/km:
    flag = 'FIXED_COST_SUSPECT'

# → 결과: PENDING_REVIEW
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 183-206)
patch.md (Lines 183-205: "4) short-run & fixed-cost suspicion")
```

---

### Algorithm 5: 이상치 탐지 & 리스크 스코어

**참조**:
- `domestic_validator_patched.py` (207-230줄)
- `patch.md` (섹션 1.D, 207-230줄)

**로직**:
```python
# 1. IsolationForest (Anomaly Detection)
features = ['per_km', 'distance_km', 'vehicle_code']
iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.04,  # 4% 이상치 예상
    random_state=42
)
anomaly_pred = iso_forest.fit_predict(features)
# -1 = anomaly, 1 = normal

# 2. Risk Score 계산
risk_score = (
    0.4 × delta_normalized +  # Δ% 정규화 (0~1)
    0.3 × anomaly_flag +      # 이상치 여부 (0 or 1)
    0.2 × cert_missing +      # 인증 누락 (DOMESTIC은 0)
    0.1 × signature_risk      # 서명 리스크 (DOMESTIC은 0)
)

# 3. RBR (Risk-Based Review) 트리거
if risk_score >= 0.70:
    trigger = 'RBR_HIGH_RISK'
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 207-230)
patch.md (Lines 207-230: "5) anomaly (IsolationForest prediction)")
domestic_validator_v2.py (Lines 246-279: Risk score formula)
```

---

## 🎯 최종 판정 규칙 (Decision Logic)

**참조**:
- `domestic_validator_patched.py` (221-230줄)
- `domestic_validator_v2.py` (231-243줄)
- `patch.md` (섹션 1.D, 47-53줄)

**Decision Tree**:
```
if abs(delta_pct) > 15%:
    → FAIL (Auto-Fail)

elif cg_band == 'CRITICAL':
    → FAIL

elif cg_band == 'HIGH':
    → PENDING_REVIEW

elif 'FIXED_COST_SUSPECT' in flags:
    → PENDING_REVIEW

elif anomaly_pred == -1:
    → PENDING_REVIEW

elif cg_band in ['PASS', 'WARN']:
    → VERIFIED (또는 PASS)

else:
    → PENDING_REVIEW
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 221-230)
HVDC_Invoice_Audit/domestic_validator_v2.py (Lines 231-243)
patch.md (Lines 47-53: "판정 규칙")
```

---

## 📊 설정 파라미터

### COST-GUARD Bands

| Band | Delta % Range | 설명 |
|------|---------------|------|
| **PASS** | ≤2.00% | 정확한 청구 |
| **WARN** | 2.01-5.00% | 경미한 차이 |
| **HIGH** | 5.01-10.00% | 주의 필요 |
| **CRITICAL** | >10.00% | 검토 필수 |

**위치**: `domestic_sept_2025_audit.py` (54-60줄)

### Similarity Weights

| 요소 | 가중치 | Decay 조건 |
|------|--------|------------|
| Origin 일치 | 0.35 | Exact match |
| Destination 일치 | 0.35 | Exact match |
| Vehicle 일치 | 0.10 | Exact match |
| Distance 근접 | 0.10 | ≤15km decay |
| Rate 근접 | 0.10 | ±30% decay |
| **임계값** | **≥0.60** | Accept |

**위치**: `domestic_audit_system.py` (66줄), `patch.md` (96-102줄)

### 고정 파라미터

```python
FX_RATE = 3.6725         # 1 USD = 3.6725 AED (고정)
AUTO_FAIL_PCT = 15.0     # Auto-Fail 임계값
CONTRACT_TOL_PCT = 3.0   # 계약 허용 오차
SHORT_RUN_KM = 10.0      # 초근거리 기준
VERY_SHORT_KM = 2.0      # 극초근거리
ISO_CONTAMINATION = 0.04 # 이상치 4%
```

**위치**: `domestic_audit_system.py` (55-76줄)

---

## 🗂️ 데이터 흐름도

```
[Step 1] 인보이스 로드
    ↓
    파일: 02_DSV_DOMESTIC/Core_Systems/domestic_sept_2025_audit.py (77-135줄)

[Step 2] 정규화 (O/D/Vehicle/Unit)
    ↓
    파일: domestic_validator_patched.py (44-160줄)
    참조: patch.md (섹션 1.A, Lines 26-28)

[Step 3] 참조 레인 매칭
    ↓
    파일: domestic_audit_system.py (140-280줄)
    알고리즘: Exact → Similarity(≥0.60) → Fallback
    참조: patch.md (Lines 162-173)

[Step 4] Delta % 및 COST-GUARD 계산
    ↓
    파일: domestic_audit_system.py (400-450줄)
    참조: patch.md (Lines 175-181)

[Step 5] 초근거리/이상치 탐지
    ↓
    파일: domestic_validator_patched.py (183-230줄)
    알고리즘: IQR + IsolationForest
    참조: patch.md (Lines 183-230)

[Step 6] 최종 판정 (Decision)
    ↓
    파일: domestic_audit_system.py (480-520줄)
    참조: patch.md (Lines 221-230, 47-53)

[Step 7] 결과 저장 (JSON/CSV/Excel)
    ↓
    파일: domestic_sept_2025_audit.py (400-508줄)
```

---

## 💡 핵심 알고리즘 상세 설명

### 1. Normalization Algorithm (정규화)

**목적**: 다양한 표기를 표준 형태로 통일

**파일**: `domestic_sept_2025_audit.py` Lines 44-103

**알고리즘**:
```
FOR each invoice item:
    1. Extract origin and destination text
    2. Apply regex patterns (30+ rules)
       - DSV MUSSAFAH → DSV Mussafah Yard
       - MIRFA/MIRFA PMO → MIRFA SITE
       - MOSB/AL MASAOOD → Al Masaood (MOSB)
       - SHUWEIHAT → SHUWEIHAT Site
    3. Fallback: keyword matching
    4. Final fallback: Title case

    Vehicle normalization:
    - FB → FLATBED
    - LB → LOWBED
    - Special: FLATBED HAZMAT, FLATBED (CICPA)
```

---

### 2. Lane Matching Algorithm (레인 매칭)

**목적**: 각 인보이스 항목에 대한 참조 요율 찾기

**파일**: `domestic_audit_system.py` Lines 140-280

**알고리즘**:
```
FUNCTION find_reference_rate(invoice_item):
    key = f"{origin_norm}||{destination_norm}||{vehicle}||{unit}"

    # Priority 1: Exact Match
    IF key EXISTS in ApprovedLaneMap:
        RETURN approved_lane.median_rate_usd

    # Priority 2: Similarity Match
    candidates = ApprovedLaneMap.filter_by(vehicle, unit)
    best_score = 0
    best_candidate = None

    FOR each candidate IN candidates:
        score = calculate_similarity(invoice_item, candidate)
        IF score >= 0.60 AND score > best_score:
            best_candidate = candidate
            best_score = score

    IF best_candidate:
        RETURN best_candidate.median_rate_usd

    # Priority 3: Fallback (Dataset Median)
    RETURN dataset_median_by_vehicle_type
```

**Similarity 계산식**:
```
similarity =
    0.35 × (origin_match ? 1 : 0) +
    0.35 × (destination_match ? 1 : 0) +
    0.10 × (vehicle_match ? 1 : 0) +
    0.10 × distance_closeness +  # max(0, 1 - |dist_diff|/15km)
    0.10 × rate_closeness        # max(0, 1 - |rate_diff%|/30%)
```

---

### 3. COST-GUARD Band Algorithm

**목적**: Delta %를 4개 밴드로 분류

**파일**: `domestic_audit_system.py` Lines 58-63

**알고리즘**:
```
FUNCTION get_cost_guard_band(delta_pct):
    abs_delta = abs(delta_pct)

    IF abs_delta <= 2.00:
        RETURN 'PASS'
    ELIF abs_delta <= 5.00:
        RETURN 'WARN'
    ELIF abs_delta <= 10.00:
        RETURN 'HIGH'
    ELSE:
        RETURN 'CRITICAL'
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_audit_system.py (Lines 58-63)
02_DSV_DOMESTIC/Core_Systems/domestic_sept_2025_audit.py (Lines 54-60)
```

---

### 4. Short-Run Detection Algorithm

**목적**: 초근거리 고정요금 의심 항목 탐지

**파일**: `domestic_validator_patched.py` Lines 183-206

**알고리즘**:
```
FUNCTION detect_short_run_issues(item):
    flags = []
    per_km = item.rate_usd / item.distance_km

    IF distance_km <= 10.0:
        flags.append('SHORT_RUN')

        # IQR-based outlier detection
        p25, p75 = vehicle_group.percentile_25_75(per_km)
        IQR = p75 - p25

        IF per_km > p75 + 1.5 × IQR:
            flags.append('HIGH_PERKM_SHORT')

        # Absolute threshold
        IF distance_km <= 2.0 AND per_km >= 40:
            flags.append('FIXED_COST_SUSPECT')

        IF per_km >= 100:
            flags.append('FIXED_COST_SUSPECT')

    RETURN flags
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 183-206)
patch.md (Lines 183-205: "4) short-run & fixed-cost suspicion")
```

---

### 5. IsolationForest Anomaly Detection

**목적**: 머신러닝 기반 이상치 탐지

**파일**: `domestic_validator_patched.py` Lines 207-220

**알고리즘**:
```
FUNCTION detect_anomalies(items):
    # Feature engineering
    features = [
        'per_km',           # $/km
        'distance_km',      # 거리
        'vehicle_code'      # Vehicle type encoded
    ]

    # IsolationForest model
    model = IsolationForest(
        n_estimators=200,
        contamination=0.04,  # 4% contamination
        random_state=42
    )

    predictions = model.fit_predict(features)
    # -1 = anomaly, 1 = normal

    anomaly_scores = model.decision_function(features)
    # Normalized to 0-1 range

    RETURN anomaly_flags, anomaly_scores
```

**위치**:
```
02_DSV_DOMESTIC/Core_Systems/domestic_validator_patched.py (Lines 207-220)
HVDC_Invoice_Audit/domestic_validator_v2.py (Lines 246-262)
patch.md (Lines 207-220: "5) anomaly (IsolationForest)")
```

---

## 📐 수학적 공식 요약

### Delta % 계산
```
Δ% = ((Draft_Rate - Ref_Rate) / Ref_Rate) × 100
```

### Similarity Score
```
S = 0.35×O + 0.35×D + 0.10×V + 0.10×dist_close + 0.10×rate_close

where:
  O = 1 if origin matches, else 0
  D = 1 if destination matches, else 0
  V = 1 if vehicle matches, else 0
  dist_close = max(0, 1 - |dist_diff|/15km)
  rate_close = max(0, 1 - |rate_diff%|/30%)
```

### Risk Score
```
Risk = 0.4×Δ_norm + 0.3×Anomaly + 0.2×Cert + 0.1×Sign

where:
  Δ_norm = min(1.0, abs(Δ%)/15%)
  Anomaly = 1 if IsolationForest predicts -1, else 0
  Cert = 0 (DOMESTIC doesn't require)
  Sign = 0 (DOMESTIC doesn't require)
```

**위치**: `domestic_validator_v2.py` Lines 270-278

---

## 📚 참조 파일 전체 경로

### 핵심 시스템 파일

```
C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\02_DSV_DOMESTIC\Core_Systems\domestic_sept_2025_audit.py

C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\02_DSV_DOMESTIC\Core_Systems\domestic_audit_system.py

C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\02_DSV_DOMESTIC\Core_Systems\domestic_validator_patched.py
```

### 알고리즘 설명 문서

```
C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\02_DSV_DOMESTIC\patch.md
```

### v2 스크립트 (고급 검증)

```
C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\run_domestic_audit_v2.py

C:\Users\minky\Downloads\HVDC_Invoice_Audit-20251012T195441Z-1-001\HVDC_Invoice_Audit\domestic_validator_v2.py
```

---

## 🔍 알고리즘 비교표

| 알고리즘 | SHPT | DOMESTIC | 차이점 |
|---------|------|----------|--------|
| **Normalization** | Port/Container 중심 | O/D/Vehicle 중심 | DOMESTIC은 30+ 장소 규칙 |
| **Ref Matching** | Direct lookup | Exact → Similarity → Fallback | DOMESTIC은 3단계 매칭 |
| **Delta Calc** | 동일 | 동일 | 둘 다 (draft-ref)/ref×100 |
| **COST-GUARD** | 2/5/10% | 2/5/10% | 동일한 밴드 |
| **Special Logic** | Portal Fee (±0.5%) | Short-run, Anomaly | DOMESTIC은 ML 사용 |
| **Auto-Fail** | >5% (Contract) | >15% (All) | DOMESTIC이 더 관대 |

---

## ✅ 검증 품질 지표

### 9월 2025 실행 결과

| 지표 | 값 | 설명 |
|------|-----|------|
| **Total Items** | 44 | 전체 검증 항목 |
| **Ref Match Rate** | 100% | 참조 요율 매칭률 |
| **Exact Match** | 9 (20.5%) | 완벽 일치 |
| **Similarity Match** | 8 (18.2%) | 유사 매칭 (≥0.60) |
| **Low Similarity** | 27 (61.4%) | 낮은 유사도 (<0.60) |
| **Processing Time** | 0.35초 | 초당 126 items |

---

🔧 **추천 명령어:**
`/logi-master algorithm-deep-dive` [알고리즘 상세 분석 - 수학적 증명 포함]
`/visualize-data similarity-distribution` [Similarity Score 분포 시각화 - 매칭 품질]
`/automate algorithm-doc-generate` [알고리즘 문서 자동 생성 - 기술 문서화]
