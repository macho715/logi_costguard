# 개선안(우선순위 → 바로 적용 가능한 패치 포함)

## A. 매칭률 올리는 핵심 패치 (오늘 적용)

1. **토큰세트 기반 유사도 보강**

   * 현재 O/D는 완전일치(=1) 아니면 0에 가까움. `token_set`(교집합/차집합) + n-gram(3gram)로 **부분 일치**를 잡아내자.
   * 임계: **기본 0.60 → 동적 임계**: `sim ≥ 0.55` 또는 `(dist_closeness≥0.75 and sim≥0.50)`이면 허용.

2. **정규화 사전 자동 확장(제안생성)**

   * 인보이스 O/D 토큰 중 **사전에 없는 것**을 빈도순으로 뽑고, 기존 Canonical과 Jaccard≥0.6이면 **후보 alias**로 제안·축적.
   * 월초에 승인된 alias만 NormalizationMap에 합침.

3. **레퍼런스 대체 계층 추가**

   * ApprovedLaneMap 미매칭 시, **Region→Region+Vehicle**(예: Mussafah Cluster ↔ MIRFA Site) 중앙값으로 **대체 ref**.
   * 동일 Vehicle/Unit에서 **거리±15km, $/km±30%** 안에 드는 후보만 풀에 포함.

4. **초근거리 최소요금 모델**

   * 거리≤10km 구간은 **Min-Fare(차량별)** 을 별도 기준으로 적용(Δ% 산출은 Min-Fare 대비).
   * `FIXED_COST_SUSPECT`는 남기되, Min-Fare 매칭 시 **LOW_SIMILARITY 경고 제거**.

> 기대효과: LOW_SIMILARITY 27건 중 **절반 이상을 VERIFIED/REVIEW**로 전환.

### 🔧 드롭인 코드 패치(핵심 부분만)

`domestic_validator_v2.py`의 similarity 로직을 이렇게 바꿔줘:

```python
import re

def _tok(s):  # 알파벳+숫자 토큰
    return set(re.findall(r"[A-Za-z0-9]+", str(s).upper()))

def token_set_sim(a,b):
    A,B=_tok(a),_tok(b)
    if not A or not B: return 0.0
    inter=len(A&B); uni=len(A|B)
    return inter/uni

def trigram_sim(a,b):
    def grams(x):
        x="  "+str(x).upper()+"  "
        return {x[i:i+3] for i in range(len(x)-2)}
    A,B=grams(a),grams(b)
    if not A or not B: return 0.0
    return len(A&B)/len(A|B)

def od_similarity(a,b):
    # 토큰세트 0.6 가중 + 트리그램 0.4 가중
    return 0.6*token_set_sim(a,b) + 0.4*trigram_sim(a,b)

def similarity_score(row, cand, weights, dist_decay_km, rate_decay_pct):
    s=0.0
    s += weights["origin"]      * od_similarity(row["origin_norm"], cand["origin"])
    s += weights["destination"] * od_similarity(row["destination_norm"], cand["destination"])
    s += weights["vehicle"]     * (1.0 if str(row["vehicle"]).strip()==str(cand["vehicle"]).strip() else 0.0)
    # 이하 distance/price closeness는 기존 그대로
    ...
```

그리고 **동적 임계**:

```python
thr_base = cfg["similarity"]["edge_threshold"]  # 0.60
dist_close = closeness_distance(row.get("distance_km"), cand.get("median_distance_km"))  # 0~1
thr = min(0.60, 0.55 + 0.10*(1.0 - dist_close))  # 근접할수록 임계 낮춤 → 0.55~0.60
if score >= thr or (dist_close >= 0.75 and score >= 0.50):
    # accept
```

**Region 대체 레퍼런스**(미매칭 fallback):

```python
def region(place):
    p=str(place).upper()
    if "MUSSAFAH" in p or "ICAD" in p: return "MUSSAFAH"
    if "MINA" in p or "FREEPORT" in p or "ZAYED" in p: return "MINA"
    if "MIRFA" in p: return "MIRFA"
    if "SHUWEIHAT" in p: return "SHUWEIHAT"
    return "OTHER"

if np.isnan(ref_rate):
    pool = baseline[(baseline["vehicle"]==row["vehicle"]) & (baseline["unit"]==row["unit"])]
    pool = pool[ (pool["region_o"]==region(row["origin_norm"])) & (pool["region_d"]==region(row["destination_norm"])) ]
    # 거리±15km & $/km±30% 필터
    ...
```

**Min-Fare 모델**(초근거리):

```python
MIN_FARE = {"FLATBED": 200.0, "LOWBED": 600.0, "3 TON PU": 150.0}  # 예시
if row["distance_km"]<=10 and np.isnan(ref_rate):
    ref_rate = MIN_FARE.get(row["vehicle"], MIN_FARE["FLATBED"])
    band_from_minfare = True
```

---

## B. 데이터·운영 레이어 개선 (이번 주)

* **NormalizationMap 자동 제안**: 인보이스 원시 O/D 중 미정규 키 목록 → Canonical 후보(top-k)와 함께 CSV로 배포(매주 승인).
* **월 스냅샷 ApprovedLaneMap**: 분기/월 요율 변화 흡수(레거시 중앙값에 월 태그).
* **특별구간 화이트리스트**: `domestic result.xlsx`에서 키 생성(O/D/Vehicle/Unit) → **SPECIAL_PASS** 라우팅(Δ/리스크만 기록).
* **헤더 자가치유**: `Distance(km)` → `distance_km` 등 **머리글 일치 자동 수정**.

---

## C. 판단 품질 튜닝 (다음 주)

* **Confidence 게이트**: `confidence≥0.92`면 자동 집행, 그 외 리뷰.
* **Anomaly 완충**: IsolationForest는 레인별 `$ / km` 표준화 후 학습(군집별 오탐↓).
* **Min-Fare 테이블 가시화**: 차량×구간(0–2, 2–5, 5–10km) 3단 슬라브로 정의.

---

## D. 바로 실행 체크리스트

* [ ] 위 **유사도 보강 패치** 적용 후 재실행 → LOW_SIMILARITY 27건 감소 폭 확인
* [ ] **Min-Fare** 값(차량별) 확인/승인 → config에 고정
* [ ] Region 라우팅이 필요한 원산지/목적지 **키워드 리스트** 승인
* [ ] NormalizationMap 신규 alias 10~20건 반영

---

## 예상 효과(이번 배치)

* **LOW_SIMILARITY 27건 중 12~18건** → `VERIFIED/WARN` 재분류
* 최종 미검증(보류) 건수 **40~60% 감소**

필요하면 내가 **패치된 파일 블록**까지 만들어서 올려줄게. 먼저 위 4개 패치(A1~A4)부터 적용해 보자.
