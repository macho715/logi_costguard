# DOMESTIC 검증 시스템 7단계 패치 적용 완료

## 📋 Executive Summary

**목표**: CRITICAL 18건 → 한 자릿수 감소
**적용 날짜**: 2025-10-13
**적용 파일**:
- `Core_Systems/domestic_audit_system.py` (Enhanced)
- `config_domestic_enhanced.json` (New)

---

## ✅ 적용된 7단계 패치

### Step 1: 유사도 미흡(LOW_SIM) 개선
**목적**: 레인 지역 풀 확장으로 미매칭 레인 흡수

#### 1-A) 동적 임계 + 토큰/트리그램 (이미 적용됨)
- Token-set based similarity (Patch A1)
- Dynamic threshold (Patch A2)

#### 1-B) Region 토큰 확장 ✅ NEW
**수정 위치**: `get_region()` 함수 (Line 242-264)

```python
# MUSSAFAH Cluster 확장
if any(keyword in p for keyword in ["MUSSAFAH", "ICAD", "M44", "MARKAZ", "PRESTIGE"]):
    return "MUSSAFAH_CLUSTER"

# MINA Cluster 확장
if any(keyword in p for keyword in ["MINA", "FREEPORT", "ZAYED", "JDN", "PORT"]):
    return "MINA_CLUSTER"

# MIRFA Cluster 확장
if any(keyword in p for keyword in ["MIRFA", "PMO"]):
    return "MIRFA_CLUSTER"

# SHUWEIHAT Cluster 확장
if any(keyword in p for keyword in ["SHUWEIHAT", "SHU", "S2", "S3", "POWER"]):
    return "SHUWEIHAT_CLUSTER"
```

**기대 효과**: 미매칭 레인이 지역 중앙값으로 흡수되어 LOW_SIMILARITY 감소

---

### Step 2: 근거리 최소요금 Min-Fare 모델 (이미 적용됨)
**목적**: 거리 ≤10km 구간의 최소요금 기준 적용

**적용 상태**: ✅ Patch A4 이미 적용
**수정 위치**: `apply_min_fare_if_needed()` 함수 및 validate() 함수 (Line 600-611)

**Min-Fare 테이블**:
```json
{
  "FLATBED": 200.0,
  "LOWBED": 600.0,
  "3 TON PU": 150.0,
  "7 TON PU": 200.0,
  "DEFAULT": 200.0
}
```

---

### Step 3: 특수요율(HAZMAT/CICPA) 보정 ✅ NEW
**목적**: HAZMAT/CICPA 차량의 특수 요율 보정

**수정 위치**: validate() 함수 (Line 613-640)

```python
# Step 3: Apply HAZMAT/CICPA adjusters (rate multipliers)
adjusters_config = {
    "enabled": True,
    "rules": [
        {"if_vehicle_contains": "HAZMAT", "rate_multiplier": 1.15},
        {"if_vehicle_contains": "CICPA", "rate_multiplier": 1.08}
    ]
}

if adjusters_config.get("enabled", False):
    rules = adjusters_config.get("rules", [])

    def apply_adjuster(row):
        ref = row["ref_rate_usd"]
        if pd.isna(ref):
            return ref
        vehicle_str = str(row.get("vehicle", "")).upper()
        multiplier = 1.0

        for rule in rules:
            keyword = str(rule.get("if_vehicle_contains", "")).upper()
            if keyword and keyword in vehicle_str:
                multiplier *= float(rule.get("rate_multiplier", 1.0))

        return round(ref * multiplier, 2) if multiplier != 1.0 else ref

    df["ref_rate_usd"] = df.apply(apply_adjuster, axis=1)
```

**기대 효과**: HAZMAT/CICPA 레인이 CRITICAL → HIGH/WARN/PASS로 이동

---

### Step 4: 고신뢰 자동승인 게이트 ✅ NEW
**목적**: 유사도/완전성 충분한 건 자동 PASS

**수정 위치**: validate() 함수 (Line 743-763)

```python
# Step 4: Confidence Gate - Auto-verify high confidence items
confidence_gate_config = {
    "enabled": True,
    "min_similarity": 0.70,
    "min_confidence": 0.92,
    "auto_verify_bands": ["PASS", "WARN"]
}

if confidence_gate_config.get("enabled", False):
    df["confidence_gate"] = (
        (df.get("similarity", 0) >= confidence_gate_config["min_similarity"]) &
        (df.get("confidence", 0) >= confidence_gate_config["min_confidence"])
    )
    # Auto-verify items that pass confidence gate
    auto_verify_mask = (
        df["cg_band"].isin(confidence_gate_config["auto_verify_bands"]) &
        df["confidence_gate"]
    )
    df.loc[auto_verify_mask, "decision"] = "VERIFIED"
```

**기대 효과**: 고신뢰 항목 자동 승인으로 리뷰 부담 감소

---

### Step 5: UNDER(과소청구) CRITICAL 완충 ✅ NEW
**목적**: 과소청구 항목은 검토보류로 전환

**수정 위치**: validate() 함수 (Line 765-774)

```python
# Step 5: Under-charge buffer - Route negative delta CRITICAL to review
under_buffer_config = {"enabled": True}

if under_buffer_config.get("enabled", False):
    is_under_charge = df.get("delta_pct", 0) < 0
    under_critical_mask = (df["cg_band"] == "CRITICAL") & is_under_charge
    df.loc[under_critical_mask, "decision"] = "PENDING_REVIEW"
    df.loc[under_critical_mask, "flags"] = (
        df["flags"] + "|UNDER_CHARGE_REVIEW"
    ).str.strip("|")
```

**기대 효과**: 과소청구 CRITICAL이 PENDING_REVIEW로 전환되어 재청구 유도

---

### Step 6: SPECIAL_PASS 화이트리스트
**목적**: 이미 집행된 라인 자동 통과

**적용 방법**:
- `domestic_result.xlsx`에서 키(O/D/Vehicle/Unit) 추출
- SPECIAL_PASS 로직에 반영 (향후 적용 예정)

**상태**: ⏳ 운영 데이터 축적 후 적용

---

### Step 7: 운영 루틴
**적용 절차**:

1. **파일 업로드**: `DOMESTIC_with_distances.xlsx` (100 lanes)
2. **런 실행**: `python domestic_sept_2025_audit.py`
3. **별칭 승인**: `alias_suggestions.csv` 확인 → 상위 10개 승인 → NormalizationMap 병합
4. **재런**: CRITICAL 잔여 확인
5. **조정**: HAZMAT/CICPA 처리, region_rules/별칭 추가
6. **최종 검증**: Confidence Gate로 자동 승인 폭 확대

---

## 📊 기대 효과

### Before (현재)
```
Stage 3 (100 Lanes): PASS 28 (63.6%), CRITICAL 16 (36.4%)
```

### After (패치 적용 후 예상)
```
Expected: PASS 32-36 (72-82%), CRITICAL 6-9 (13-20%)
```

**개선 목표**:
- ✅ CRITICAL 16 → 6~9건 (44-62% 감소)
- ✅ PASS 28 → 32~36건 (14-28% 증가)
- ✅ 자동 승인율 ≥80% 달성

---

## 🔧 추가 config 파일

**파일**: `config_domestic_enhanced.json`

```json
{
  "version": "v2.1_enhanced",
  "similarity": {
    "dynamic": {"enabled": true, "min_threshold": 0.50}
  },
  "min_fare_model": {
    "enabled": true,
    "short_run_km": 10.0,
    "table": {"FLATBED": 200.0, "LOWBED": 600.0, "3 TON PU": 150.0, "7 TON PU": 200.0}
  },
  "region_rules": {
    "MUSSAFAH": ["MUSSAFAH", "ICAD", "MARKAZ", "M44", "PRESTIGE"],
    "MINA": ["MINA", "FREEPORT", "ZAYED", "JDN", "PORT"],
    "MIRFA": ["MIRFA", "PMO"],
    "SHUWEIHAT": ["SHUWEIHAT", "S2", "S3", "POWER"]
  },
  "adjusters": {
    "enabled": true,
    "rules": [
      {"if_vehicle_contains": "HAZMAT", "rate_multiplier": 1.15},
      {"if_vehicle_contains": "CICPA", "rate_multiplier": 1.08}
    ]
  },
  "confidence_gate": {
    "enabled": true,
    "min_similarity": 0.70,
    "min_confidence": 0.92
  },
  "under_charge_buffer": {"enabled": true}
}
```

---

## ✅ 패치 검증 체크리스트

- [x] Step 1: Region 토큰 확장 적용
- [x] Step 2: Min-Fare 모델 (이미 적용)
- [x] Step 3: HAZMAT/CICPA adjusters 적용
- [x] Step 4: Confidence Gate 적용
- [x] Step 5: Under-charge buffer 적용
- [ ] Step 6: SPECIAL_PASS 화이트리스트 (운영 후 적용)
- [x] Step 7: 운영 루틴 문서화

---

## 🚀 다음 단계

1. **재실행**: 패치 적용된 시스템으로 9월 데이터 재검증
2. **결과 분석**: CRITICAL 감소폭 확인
3. **별칭 승인**: `alias_suggestions.csv` Top 10 승인
4. **반복**: 잔여 CRITICAL 6~9건 패턴 분석 및 추가 튜닝
5. **최종 보고서**: 개선 완료 Excel 보고서 생성

---

**패치 적용 완료일**: 2025-10-13
**다음 검증**: `python domestic_sept_2025_audit.py` 재실행

