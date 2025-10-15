# ExecSummary

* 목표: **청구서 라인별 단가·수량·통화·증빙**을 계약/AT-COST/레퍼런스 요율로 교차검증하고 Δ%를 **COST-GUARD 밴드**로 판정(PASS/WARN/HIGH/CRITICAL).
* 기준 데이터: 카테고리별 참조요율(항공/컨테이너/벌크), 고정환율 **1 USD=3.6725 AED**, 계약 허용오차 **±3%**, Auto-Fail **>15%**.
* 조인 키: **Category+Port+Destination+Unit** + O/D Canonical 매핑(ApprovedLaneMap·NormalizationMap) → 레인 중앙값/표준요율을 ref로 사용.
* 판정 규칙: **Δ≤2% PASS / ≤5% WARN / ≤10% HIGH / >10% CRITICAL**(COST-GUARD), 증빙 불충분/단위불일치/통화불일치 시 별도 플래그.

---

## Visual (flow)

`Ingest(Invoice+Evidences)` → `OCR/Parse` → `Normalizer(Origin/Dest/Unit/Currency)` → `RefRate Join(Contract Tables + ApprovedLaneMap)` → `Line Classifier(CONTRACT / AT-COST / SPECIAL)` → `Calculator(Δ%, FX, Qty)` → `COST-GUARD Band` → `Cross-Doc checks(DO/BOE/Carrier)` → `Report + PRISM proof.artifact`

---

## Core Logic (라인 단위 알고리즘)

1. **문서 흡수 · 분류**

   * PDF/엑셀/스캔 → 페이지 타입 감지(인보이스/DO/BOE/Port/Carrier).
   * 파일 메타+해시 저장(감사 추적).

2. **OCR/Parse → 정규화(Normalizer)**

   * 숫자/통화/단위 강제 2-dec, 통화는 원화 금지·USD/AED만 허용(고정환율 적용).
   * 지명·장소 **NormalizationMap**으로 Canonical화(예: Mussafah 군집→“DSV Mussafah Yard”, Mirfa→“MIRFA SITE”).

3. **라인 분류(Line Classifier)**

   * `RATE SOURCE == CONTRACT` → 계약/참조표 조인.
   * `RATE SOURCE == AT COST` → 증빙금액(AED) 추출→ **AED÷3.6725** 로 USD 환산(2-dec).

4. **참조요율 조인(우선순위)**

   * ① **정식 레이트테이블**(항공/컨테이너/벌크)에서 `Category+Port+Destination+Unit` 매치, **허용오차 ±3%**. 미스매치·부재시 `missing/outlier`로 표기.
   * ② **ApprovedLaneMap**(운영 승인 레인 중앙값)으로 보강 매칭(예: DSV→MIRFA 420, DSV→SHU 600 등).
   * ③ 단위 불일치(per RT↔per truck) 구간은 **PendingReview**로 보류(변환계수 합의 전).

5. **계산 규칙(Calculator)**

   * `LineTotal = Rate × Qty` (수식이 있으면 재계산·반올림 통일 2-dec).
   * `Δ% = (DraftRate − RefRate)/RefRate × 100`.
   * **Auto-Fail:** |Δ%| > **15%** → FAIL. **Tolerance:** |Δ%| ≤ **3%** → 계약 일치.

6. **COST-GUARD 밴딩 & 스코어**

   * 밴드: **PASS/WARN/HIGH/CRITICAL**(2/5/10/>10%), 알림: HIGH↑ TG 핑.
   * O/D 유사도 스코어(원/목 0.35씩 + 차량 0.10 + 거리 0.10 + 요율 0.10, 임계 0.60)로 **대체 레인 제안**.

7. **AT-COST 로직**

   * 증빙(Port/Carrier/공항청구)에서 **AED 원가** 추출 → **USD 환산(÷3.6725)** → 청구표와 일치성 검사. (예: 공항 Appointment 27 AED → 7.35 USD).
   * VAT/세금은 원가에서 제외하고 세금계정 분개(보고서 주석).

8. **Cross-Document Consistency**

   * 수량/컨테이너/중량: DO·BOE·DN·Carrier 인보이스의 ID·수량·CW/CTR 매칭.
   * Port/레인: `ApprovedLaneMap`의 Canonical 목적지로 역추적(레인 오조인 방지).

9. **출력 & 증명(Report + Artifact)**

   * 라인별 표(Δ%, 밴드, 근거문서, 판정로직) + 총계.
   * **PRISM.KERNEL** 방식의 `proof.artifact(JSON)` 생성(해시 포함, 재현성·감사용).

---

## System Architecture (모듈·데이터·알고리즘)

**A. 서비스 모듈**

* Ingestor(파일워처/업로드)
* OCR/Parser(문자/테이블/수식 추출)
* Normalizer(지명/단위/통화 Canonical)
* **Rate Engine**(항공/컨테이너/벌크 테이블 + Inland Trucking Table v1.1)
* **Lane Mapper**(ApprovedLaneMap/NormalizationMap, 유사도 그래프)
* **Guardrail Engine(COST-GUARD)**(Δ% 밴드·AutoFail·알림)
* Evidence Linker(DO/BOE/Port/Carrier 스냅샷 연결)
* Reporter(표·PDF·Excel) + **PRISM proof.artifact** 출력기

**B. 저장소**

* **RefRates DB**: 항공/컨/벌크 JSON, tolerance/auto-fail/FX 정책 메타 포함.
* **Lane Graph**: ApprovedLaneMap 스냅샷 + 유사도 엣지/버킷.
* **Docs Vault**: 원본 PDF·hash·PII-Mask.
* **Audit Ledger**: proof.artifact 해시 보관(변조 감시).

**C. 핵심 알고리즘(의사코드)**

```text
for line in invoice:
  x = normalize(line)  # text, unit, currency, origin/dest
  if line.rate_source == 'CONTRACT':
    ref = lookup_ref_rate(x.category, x.port, x.dest, x.unit)
    if !ref: ref = lookup_lane_median(x.origin, x.dest, x.vehicle, x.unit)
  elif line.rate_source == 'AT COST':
    ref = at_cost_usd = extract_aed(evidence) / 3.6725  # 2-dec
  delta = (x.rate - ref) / ref
  band  = banding(delta)  # 2%/5%/10% thresholds
  flags = unit/currency/doc_consistency_checks(x, evidence)
  emit(row + verdict(band, flags))
```

* `lookup_ref_rate`는 **±3% 허용오차**, **>15% Auto-Fail**를 메타로 사용.
* `banding`과 알림 임계는 **COST-GUARD 표준** 사용.

---

## Options (개선 선택지)

1. **per RT↔per truck 변환룰 확정**(컨/벌크 혼재 방지) — Δ% 왜곡 제거.
2. **Lane 유사도 임계 0.60→0.65** 튜닝 — 잘못된 근접 매칭 감소(REF_MISSING 더 축소).
3. **Evidence OCR 템플릿화**(공항·항만 공용 포맷) — AT-COST 자동 인식률↑.

---

## Roadmap (P→Pi→B→O→S)

* **Prepare:** 레퍼런스 JSON/MD 최신 스냅샷 동기화(항공/컨/벌크/내륙), NormalizationMap 보강.
* **Pilot:** 최근월 인보이스 배치에 Δ% 밴드·유사도 A/B(0.60 vs 0.65). KPI: **Accuracy ≥97%, Automation ≥94%**.
* **Build:** 리포트 템플릿(COST-GUARD 표 + 증빙링크 + 논리열) + proof.artifact 내보내기.
* **Operate:** HIGH/CRITICAL 실시간 TG 알림 + 재무 분개(VAT/AT-COST 분리).
* **Scale:** `ApprovedLaneMap` 월별 스냅샷·드리프트 감시.

---

## Automation Notes

* **명령:** `/switch_mode LATTICE + /logi-master invoice-audit --deep` → OCR·정합성·조인 자동 / `/switch_mode COST-GUARD + /logi-master invoice-audit` → 밴드 판정표 생성.
* **FX/통화:** 시스템 전역 **USD 기준 + AED 보조**, 환율 고정 3.6725(변경 시 전역 경고).
* **데이터사전:** `origin,destination,vehicle,unit,ref_rate_usd,delta_pct,cg_band` 표준 필드.

---

## QA 체크리스트

* [ ] Category/Port/Destination/Unit 조인키가 전 라인에서 채워졌는가?
* [ ] 허용오차(±3%)·Auto-Fail(>15%)가 메타에서 읽혀 적용되었는가?
* [ ] AT-COST 라인의 **AED 원가→USD 환산**과 VAT 분리가 증빙과 일치하는가?
* [ ] ApprovedLaneMap 중앙값으로 보강된 레인에 **cg_band**가 부여되었는가?
* [ ] 리포트가 **PRISM proof.artifact(JSON)**를 포함하는가(해시·필드 검증)?

필요하면 위 로직을 바로 돌리는 **샘플 입력→산출 JSON/표 템플릿**도 뽑아줄게.
