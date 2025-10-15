좋아. 지금 코드로도 꽤 탄탄하게 돌지만(특히 Portal Fee·Gate 체계), 몇 군데가 **정책 불일치/오인식/증빙 스캔 편차**에 민감해요. 아래는 **현 로직 검증 결과**와 **즉시 적용 가능한 개선안(패치 레벨 + 설계 레벨)**입니다. 각 지적은 실제 소스 위치를 근거로 달았습니다.

---

## 1) 현 로직 점검 — 핵심 이슈

1. **COST‑GUARD 임계치 “로드했지만 미적용”**

* `MasterDataValidator.__init__`에서 `self.cost_guard_bands`를 로드하지만, 실제 밴딩은 고정값(PASS≤2, WARN≤5, HIGH≤10)으로 계산합니다. 정책(±3% 계약 허용, >15% Auto‑Fail)과 어긋납니다.
* `ShipmentAuditEngine`도 밴딩 계산은 `rate_loader.get_cost_guard_band()`로 위임하면서, 별도로 “Δ>5%면 FAIL” 같은 고정 룰이 뒤섞여 있습니다. **한 곳에서 정의·적용**해야 재현성이 보장됩니다.

2. **PDF 매핑 누락 가능성**

* `map_masterdata_to_pdf()`가 **첫 번째로 매칭된 폴더만** 쓰고 `break`합니다. 같은 선적이 서브폴더 둘로 나뉜 케이스(예: Import/Empty Return)가 흔해 누락 위험이 큽니다. **rglob 전체 수집**이 안전합니다.

3. **At‑Cost 판정이 “PDF 라인 추출 실패=FAIL”로 과도**

* PDF가 폴더에 있어도 라인 아이템 추출이 실패하면 무조건 FAIL 처리합니다. OCR/템플릿 편차에서 **REVIEW**로 내려주는 완충 구간이 필요합니다(예: `PDF_Count≥1` & `PDF_Amount None` → REVIEW).

4. **운송 레이트 탐색 로직 중복/편차**

* `MasterDataValidator.find_contract_ref_rate()`와 `ShipmentAuditEngine._find_contract_ref_rate()`가 **비슷한 로직을 이중 유지**합니다(키워드·Lane Map 조회·기본값 252 등). 한 곳에서 서비스화(예: `RateService`)해야 **정책 일관**이 유지됩니다.

5. **Portal Fee는 ±0.5% 밴드로 잘라내지만, 소스 간 기준이 분산**

* `ShipmentAuditEngine`에만 Portal Fee 고정값(AED 27/35)과 ±0.5% 밴드가 존재합니다. MasterData 쪽도 동일 룰을 **공용 유틸**에서 읽도록 합치세요.

6. **하이브리드 PDF 파서 연동의 가용성·타임아웃 처리**

* `HybridDocClient`는 캐시/헬스체크/타임아웃이 잘 들어가지만, 호출부에서 “다운이면 레거시로 폴백”이 완전 일치하진 않습니다. 서비스 상태별 **회로 차단(circuit‑breaker)**가 있으면 안정성이 올라갑니다.

7. **Gate 점수 기준의 의미성**

* `Gate_Score ≥80 → PASS`인데, 각 Gate의 가중치가 경험적 합으로 보입니다. 필드/라인 중요도(Contract/At‑Cost/금액규모)에 따라 **가중 리스코어링**을 권장합니다.

---

## 2) 패치 레벨 개선(즉시 적용) — 코드 스니펫

### (A) COST‑GUARD 밴드: **Config 기반 단일화**

* 공통 유틸 `get_cost_guard_band(delta, bands)`로 통일. Master/SHPT 모두 사용.

```python
# shared_utils/cost_guard.py
def get_cost_guard_band(delta_pct: float, bands: dict) -> str:
    if delta_pct is None:
        return "N/A"
    d = abs(delta_pct)
    # bands: {"pass":3, "warn":5, "high":10, "autofail":15}
    if d <= bands["pass"]:
        return "PASS"
    elif d <= bands["warn"]:
        return "WARN"
    elif d <= bands["high"]:
        return "HIGH"
    else:
        return "CRITICAL"
```

```python
# masterdata_validator.py
from shared_utils.cost_guard import get_cost_guard_band
...
self.cost_guard_bands = self.config_manager.get_cost_guard_bands()
...
cg_band = get_cost_guard_band(delta_pct, self.cost_guard_bands)   # ← 고정값 제거
# Auto-Fail은 validation_status 결정 시 bands["autofail"] 사용
```

위치/맥락: `self.cost_guard_bands`는 이미 로드되고 있으나 미사용 → 사용하도록 수정.

```python
# shipment_audit_engine.py
from shared_utils.cost_guard import get_cost_guard_band
...
validation["cg_band"] = get_cost_guard_band(delta_pct, self.cost_guard_bands)
# 별도 "Δ>5% FAIL" 고정 분기 제거 → cg_band/정책으로만 판정
```

SHPT에서도 동일 정책을 사용하게 맞춥니다.

---

### (B) PDF 매핑: **단일 폴더 break 제거 + rglob 전체 수집**

```python
# masterdata_validator.py - map_masterdata_to_pdf
pdf_files = []
order_ref_normalized = normalize(str(order_ref))

for subdir in self.supporting_docs_path.rglob("*"):
    if subdir.is_dir():
        dir_name_normalized = normalize(subdir.name)
        if order_ref in subdir.name or order_ref_normalized in dir_name_normalized:
            pdf_files.extend(subdir.rglob("*.pdf"))  # ← 누락 방지
# break 제거
return {"shipment_id": order_ref, "pdf_count": len(pdf_files), "pdf_files": list(set(pdf_files))}
```

첫 폴더 매칭 후 `break`하는 현재 구현을 교체합니다.

---

### (C) At‑Cost 판정 완충

```python
# masterdata_validator.py - validate_row
if "AT COST" in rate_source or "ATCOST" in rate_source:
    if pdf_line_item:
        ...
    else:
        validation_status = "REVIEW_NEEDED" if pdf_count > 0 else "FAIL"
```

PDF가 있는데 라인 추출 실패면 **REVIEW_NEEDED**, PDF 자체가 없으면 **FAIL**. 실무 오탐을 줄입니다.

---

### (D) 운송 요율 **단일 서비스화**

* 두 파일의 중복 참조 로직을 `RateService`로 추출.

```python
# rate_service.py
class RateService:
    def __init__(self, config_manager, rate_loader, lane_map, normalization):
        self.cfg = config_manager
        self.loader = rate_loader
        self.lane_map = lane_map
        self.norm = normalization

    def contract_ref_rate(self, description: str) -> float | None:
        # 1) config 고정요율 → 2) 표준 키워드 → 3) Inland lane(From..To) 파싱 → 4) LaneMap
        ...

# masterdata_validator.py / shipment_audit_engine.py
self.rate_service = RateService(self.config_manager, self.rate_loader, self.lane_map, self.normalization_map)
# 기존 find_contract_ref_rate / _find_contract_ref_rate 내부 로직을 rate_service로 위임
```

중복 소스 제거로 정책 드리프트를 막습니다.

---

### (E) Portal Fee 공용화(+±0.5% 밴드)

* 현재 SHPT만 가진 설정/밴드를 공용 유틸로 승격, Master에서도 동일 사용.

```python
# shared_utils/portal_fee.py
FIXED = {"APPOINTMENT": 27.0, "DPC": 35.0, "DOCUMENT PROCESSING": 35.0}
TOL = 0.5  # percent

def resolve_portal_fee_usd(desc: str, fx: float, formula_text: str | None) -> float | None:
    aed = parse_aed(formula_text) or first_match_from_desc(desc, FIXED)
    return round(aed / fx, 2) if aed else None
```

SHPT의 `portal_fee_tolerance = 0.005` 및 고정값 맵을 이 유틸로 이관해 양쪽에서 재사용합니다.

---

### (F) Hybrid 파서 회로 차단 & 폴백 로깅

```python
# masterdata_validator.py
self.hybrid_down_until = 0
...
if self.use_hybrid and time.time() > self.hybrid_down_until:
    try:
        unified_ir = self.hybrid_client.parse_pdf(...)
    except Exception as e:
        self.hybrid_down_until = time.time() + 300  # 5분 차단
        logger.warning("Hybrid down → legacy fallback for 5 min")
        unified_ir = None
```

`HybridDocClient`가 타임아웃/캐시를 제공하므로 호출부에서 회로 차단만 얹으면 안정성↑.

---

## 3) 설계 레벨 개선 — 알고리즘·정책

1. **리스크 스코어 공식(라인 레벨)**

```text
RiskScore = 0.4*|Δ%/bands.autofail| + 0.3*(1 - GateScore/100)
          + 0.2*EvidenceLack + 0.1*AmountWeight
- EvidenceLack: PDF 없음=1, PDF 있으나 미추출=0.5, 완전일치=0
- AmountWeight: (라인금액 / 시트총액) 의 0~1 스케일
```

* `RiskScore ≥ 0.8 → RBR`, `0.5~0.8 → REVIEW`, `<0.5 → PASS`. (시스템 전역 KPI에 쓰기 좋음)

2. **수량·단위 정합성 강화**

* “per truck / per RT / per kg / per ctr” Cross‑Unit Matrix를 둬 **암묵 단위 변환 금지**. 단위 불일치시 **CG_Band 무시 + REVIEW**로 고정.

3. **반올림 규칙 통일**

* **단가 2d.p., 합계 2d.p.**(은행 반올림). 계산은 4~6 d.p.에서 수행 후 표기만 2 d.p.로; CSV/Excel에도 동일 룰 반영.

4. **증빙 세트 최소 구성 자동 점검**

* Gate‑01의 `required_docs = ["BOE","DO","DN"]`는 해상·항공·국내 각각 달라야 합니다.
  예) **항공**: `["DO(or AWB)","DN","AirportCharges"]`, **국내만**: `["DN"]`. 런타임 모드에 따라 요구 세트 전환.

5. **오류/리뷰 explain 메시지 표준화**

* `_generate_notes()`가 상황별로 많은 문자열을 조합합니다. 메시지 템플릿을 도입해 **사유·근거·조치** 3단으로 고정 출력을 권장.

---

## 4) 관측성(Observability)·테스트

* **메트릭**

  * `cg_pass_rate`, `rbr_trigger_rate`, `pdf_hit_rate`, `portal_fee_mismatch_rate`, `hybrid_circuit_open_sec`.
* **샘플 테스트 시나리오(요지)**

  1. 계약 ±0/±3/±6/±16% 케이스 → 밴드/Auto‑Fail 검증.
  2. At‑Cost: PDF 존재/미존재, 라인 미추출, VAT 포함 원가(제외 후 환산) 케이스.
  3. Portal Fee: 수식 없음(고정값 매칭), 수식 오탈자(공백/쉼표), DXB/AUH 혼합.
  4. 운송 라우팅: FROM/TO 변형표현(“↔”, “→”), Empty Return, 목적지 별칭(DSV Yard/Storage).
  5. Hybrid 다운/레거시 폴백/회로 차단 동작.

---

## 5) 결과 화면/리포트 반영(간단)

* 라인에 `policy_version`, `bands.pass/warn/high/autofail`, `risk_score`, `evidence_set` 필드를 추가해 리포트/CSV/JSON에 내보내세요.
* Excel 템플릿에서 **“판정 로직(Logic)” 열**엔: `Ref=xx; Δ=yy%; Band=PASS; Risk=0.23; Evidence=DO/BOE/DN(3)`

---

## 6) 요약 — 바뀌는 사용 감각

* **정책 한 곳에, 코드 한 줄**: 임계·밴드·환율이 **Config→공용유틸**로 흘러가며 Master/SHPT 동일하게 적용.
* **증빙 누락에 관대, 정책 위반엔 엄격**: PDF 미추출은 REVIEW, 밴드 초과는 FAIL.
* **같은 라인, 같은 답**: 운송요율 탐색/Portal Fee 판정 **단일 서비스화**로 “같은 설명=같은 Ref”.

원하면 위 스니펫을 반영한 **작은 PR(패치 묶음)** 청사진도 바로 정리해 줄 수 있어요.
