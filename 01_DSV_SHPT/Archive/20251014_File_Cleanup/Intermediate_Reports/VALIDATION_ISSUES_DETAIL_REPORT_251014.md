# REVIEW_NEEDED 및 FAIL 상세 분석 보고서

**작성일**: 2025-10-14
**프로젝트**: HVDC Invoice Audit - DSV SHPT System
**분석 대상**: masterdata_validated_20251014_205430.csv (102건)

---

## 📋 Executive Summary

### 전체 검증 현황
| Status | 건수 | 비율 | 설명 |
|--------|------|------|------|
| **PASS** | 36건 | 35.3% | ✅ 허용 오차 내 통과 |
| **REVIEW_NEEDED** | 50건 | 49.0% | ⚠️ 검토 필요 (주로 Ref Rate 미매칭) |
| **FAIL** | 16건 | 15.7% | ❌ 허용 오차 초과 (CRITICAL) |

### 주요 원인 Top 3
1. **Ref Rate 미매칭** (50건) - At Cost, Transportation, Container Fees 등
2. **DO FEE 요율 불일치** (12건) - AIR 청구에 CONTAINER 요율 적용 또는 그 반대
3. **Portal Fee 환율 이슈** (4건) - AED/USD 환율 적용 오류

### 즉시 개선 가능 항목
- ✅ **MASTER DO FEE**: AIR(HE) 항목에 150 USD 청구 → 80 USD로 수정 필요 (10건)
- ✅ **Portal Fees**: AED/USD 환율 재계산 필요 (4건)
- ⚠️ **Transportation/Container Fees**: Configuration 추가 필요 (31건)

---

## 1️⃣ REVIEW_NEEDED 상세 분석 (50건, 49.0%)

### 1.1 Delta % 분포

**특징**: REVIEW_NEEDED 항목은 **모두 Ref Rate가 없는 상태**입니다.
- Delta 값 있음: **0건**
- **원인**: At Cost, Transportation, Container Fees 등 변동 요율 항목

### 1.2 Charge Group 분포

| Charge Group | 건수 | 비율 | 설명 |
|--------------|------|------|------|
| **Other** | 20건 | 40.0% | 일반 비용 (변동 요율) |
| **Contract** | 16건 | 32.0% | 계약 항목이나 Ref Rate 미등록 |
| **AtCost** | 12건 | 24.0% | At Cost 항목 (Ref Rate 불필요) |
| **PortalFee** | 2건 | 4.0% | Portal 수수료 |

### 1.3 Ref Rate 소스 분석

| 소스 | 건수 | 비율 |
|------|------|------|
| **Ref Rate 있음** | 0건 | 0.0% |
| **Ref Rate 없음** | 50건 | 100.0% |
| Config 소스 | 0건 | - |
| PDF 소스 | 34건 | 68.0% |

**분석**: PDF에서 정보를 찾았으나 요율 추출이 안 된 경우가 34건입니다.

### 1.4 DESCRIPTION 카테고리별 분석 (Top 10)

| 순위 | DESCRIPTION | 건수 | 개선 방안 |
|------|-------------|------|----------|
| 1 | TERMINAL HANDLING FEE (1 X 20DC) | 3건 | ⚠️ Config 추가 필요 |
| 2 | TRANSPORTATION CHARGES (1 X 20DC) FROM KHALIFA PORT TO DSV M | 2건 | ⚠️ Lane Map 확장 |
| 3 | BILL OF ENTRY | 2건 | ✅ 이미 Config 있음 (100 USD) |
| 4 | GATE PASS CHARGES | 2건 | ⚠️ Config 추가 필요 |
| 5 | TERMINAL HANDLING CHARGES (CW: 2136 KG) | 2건 | ⚠️ 무게 기반 계산 로직 필요 |
| 6 | CUSTOMS INSPECTION | 2건 | ⚠️ Config 추가 필요 |
| 7 | PRO CUSTOMS | 2건 | ⚠️ Config 추가 필요 |
| 8 | CUSTOMS INSPECITON (오타) | 1건 | ⚠️ 오타 정규화 필요 |
| 9 | Others | 1건 | - |
| 10 | Pass-through Customs Documentation Fee | 1건 | ⚠️ Config 추가 필요 |

### 1.5 카테고리 분포

| 카테고리 | 건수 | 비율 | 개선 우선순위 |
|----------|------|------|--------------|
| **Transportation** | 18건 | 36.0% | **P1** (Lane Map 확장) |
| **Container Fees** | 13건 | 26.0% | **P2** (변동 요율, PDF 의존) |
| **Terminal Handling** | 7건 | 14.0% | **P1** (THC 추가) |
| **Others** | 6건 | 12.0% | P3 |
| **Documentation** | 2건 | 4.0% | P2 |
| **Gate/Inspection** | 2건 | 4.0% | P2 |
| **Duty/Outlay** | 1건 | 2.0% | P3 (계산 로직) |
| **DO Fee** | 1건 | 2.0% | ✅ 이미 해결됨 |

---

## 2️⃣ FAIL 상세 분석 (16건, 15.7%)

### 2.1 실패 원인 분류

| 원인 | 건수 | 비율 | 설명 |
|------|------|------|------|
| **No Ref Rate** | 0건 | 0.0% | Ref Rate가 아예 없는 경우 |
| **High Delta (>3%)** | 16건 | 100.0% | ❌ Ref Rate는 있으나 Delta 허용 오차 초과 |
| **Other** | 0건 | 0.0% | - |

**중요**: FAIL 16건은 **모두 Ref Rate가 있지만 허용 오차(3%)를 초과**한 경우입니다!

### 2.2 Charge Group 및 CG_Band 분포

| Charge Group | 건수 | 비율 |
|--------------|------|------|
| **Contract** | 12건 | 75.0% |
| **PortalFee** | 4건 | 25.0% |

| CG_Band | 건수 | 비율 |
|---------|------|------|
| **CRITICAL** | 16건 | 100.0% |

**분석**: 모든 FAIL 항목이 CRITICAL 등급이며, 75%가 Contract 항목입니다.

### 2.3 카테고리 분포

| 카테고리 | 건수 | 비율 | 문제 유형 |
|----------|------|------|----------|
| **DO Fee** | 12건 | 75.0% | ❌ **요율 불일치** (AIR ↔ CONTAINER 혼동) |
| **Portal Fees** | 2건 | 12.5% | ❌ **환율 오류** (267% Delta) |
| **Documentation** | 2건 | 12.5% | ❌ **환율 오류** (671% Delta) |

### 2.4 전체 FAIL 항목 상세 (16건)

#### 🔴 Problem 1: MASTER DO FEE 요율 불일치 (12건)

**패턴 A: AIR 청구인데 CONTAINER 요율 적용됨** (2건)
| No | Order Ref | 청구 RATE | Ref Rate | Delta | 문제 |
|----|-----------|-----------|----------|-------|------|
| 24 | HVDC-ADOPT-SCT-0131 | 80.00 | 150.0 | -46.67% | SCT(CONTAINER)인데 80 USD 청구 |
| 39 | HVDC-ADOPT-SCT-0134 | 80.00 | 150.0 | -46.67% | SCT(CONTAINER)인데 80 USD 청구 |

**원인**: CONTAINER 항목인데 AIR 요율(80 USD)로 잘못 청구됨
**해결**: Invoice 수정 요청 (80 → 150 USD)

**패턴 B: CONTAINER 청구인데 AIR 요율 적용됨** (10건)
| No | Order Ref | 청구 RATE | Ref Rate | Delta | 문제 |
|----|-----------|-----------|----------|-------|------|
| 46 | HVDC-ADOPT-HE-0471 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 48 | HVDC-ADOPT-HE-0472 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 50 | HVDC-ADOPT-HE-0473 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 52 | HVDC-ADOPT-HE-0450, 0459, 0460 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 54 | HVDC-ADOPT-HE-0466,0467,0468 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 56 | HVDC-ADOPT-HE-0464,0465,0470 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 58 | HVDC-ADOPT-HE-0437,0438-2,0439-2,0440-2,0441-1 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 62 | HVDC-ADOPT-HE-0438, 0439, 0440-1, 0441, 0482, 0454 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 64 | HVDC-ADOPT-HE-0425, 0426, 0427, 0428 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |
| 66 | HVDC-ADOPT-HE-0475 | 150.00 | 80.0 | +87.50% | HE(AIR)인데 150 USD 청구 |

**원인**: AIR 항목인데 CONTAINER 요율(150 USD)로 과다 청구됨
**해결**: **Invoice 수정 요청 (150 → 80 USD)** - 총 과다 청구액: 10건 × 70 USD = **700 USD 환급 필요**

#### 🔴 Problem 2: Portal Fees 환율 오류 (4건)

| No | Order Ref | Description | 청구 RATE | Ref Rate | Delta | 문제 |
|----|-----------|-------------|-----------|----------|-------|------|
| 28 | HVDC-ADOPT-SCT-0131 | APPOINTMENT FEE | 7.35 | 2.00 | +267.35% | PDF에서 AED 요율을 USD로 오인 |
| 29 | HVDC-ADOPT-SCT-0131 | DPC FEE | 9.53 | 2.59 | +267.26% | PDF에서 AED 요율을 USD로 오인 |
| 45 | HVDC-ADOPT-SCT-0134 | TRUCK APPOINTMENT FEE | 7.35 | 2.00 | +267.35% | PDF에서 AED 요율을 USD로 오인 |
| 98 | HVDC-ADOPT-HE-0499(LOT3) | DOCUMENT PROCESSING FEE | 20.01 | 2.59 | +671.11% | PDF에서 AED 요율을 USD로 오인 |

**원인**: PDF에서 추출한 요율이 AED인데 USD로 잘못 해석됨
- **실제 정상 요율**:
  - APPOINTMENT FEE: 27 AED = 7.35 USD ✅
  - DPC FEE: 35 AED = 9.53 USD ✅
  - DOCUMENT PROCESSING FEE: 35 AED (추정)

**해결**: PDF 파싱 시 통화 단위 명시적 확인 및 환율 변환 로직 개선

---

## 3️⃣ 개선 권장사항

### 🚨 Priority 1: 즉시 개선 (Critical)

#### 1.1 MASTER DO FEE Invoice 수정 (12건)
**재무 영향**: 700 USD 환급 필요 (AIR 10건 × 70 USD 과다 청구)

| 조치 | Order Ref | 현재 | 변경 후 | 차액 |
|------|-----------|------|---------|------|
| **환급** | HE-0471, 0472, 0473 등 (10건) | 150 USD | 80 USD | -70 USD/건 |
| **추가 청구** | SCT-0131, 0134 (2건) | 80 USD | 150 USD | +70 USD/건 |

**Action Items**:
1. [ ] Invoice 수정 요청서 작성
2. [ ] DSV 담당자 승인
3. [ ] Credit Note 발행
4. [ ] 차기 Invoice에 반영

#### 1.2 Portal Fees PDF 파싱 개선
**문제**: AED 요율을 USD로 오인하여 267~671% Delta 발생

**해결**:
```python
# PDF 파싱 시 통화 명시적 확인
if "AED" in pdf_text or "د.إ" in pdf_text:
    rate_usd = rate_aed / 3.6725
    currency = "AED"
else:
    rate_usd = rate
    currency = "USD"
```

#### 1.3 고빈도 항목 Configuration 추가 (5건)
| DESCRIPTION | 건수 | 권장 요율 | 소스 |
|-------------|------|----------|------|
| TERMINAL HANDLING FEE (20DC) | 3건 | 280 USD | 기존 config 확인 |
| GATE PASS CHARGES | 2건 | 조사 필요 | PDF/시장 조사 |
| CUSTOMS INSPECTION | 2건 | 조사 필요 | PDF/시장 조사 |
| PRO CUSTOMS | 2건 | 조사 필요 | PDF/시장 조사 |

### ⚠️ Priority 2: 중기 개선 (1-2개월)

#### 2.1 Transportation Lane Map 확장 (18건)
- 현재: 8개 Lane 등록
- 목표: 주요 Transportation 경로 20개 이상 등록
- 데이터 소스: 과거 Invoice PDF 분석

#### 2.2 Container Fees 변동 요율 패턴 분석 (13건)
- Port Container Fees (Washing, Inspection, Admin 등)
- Carrier Container Fees (Maintenance, Repositioning 등)
- 패턴 식별 후 자동 매칭 로직 개발

#### 2.3 At Cost 항목 검증 로직 개선 (12건)
- At Cost 항목도 PDF 요율과 비교
- "Reasonable" 범위 설정 (과거 데이터 기반)

### 💡 Priority 3: 장기 개선 (3-6개월)

#### 3.1 AI 기반 요율 예측
- 과거 Invoice 데이터 학습
- 신규 항목 자동 요율 추정
- 신뢰도 점수 제공

#### 3.2 실시간 시장 요율 연동
- 항공/해상 운임 지수 API 연동
- 포털 수수료 자동 업데이트
- 환율 실시간 반영

---

## 4️⃣ 요약 통계 및 KPI

### 개선 필요 항목 요약
| 항목 | 건수 | 비율 | 우선순위 |
|------|------|------|----------|
| Ref Rate 미매칭 | 50건 | 49.0% | P1/P2 |
| High Delta (>15%) | 16건 | 15.7% | **P1** |
| Contract 항목 중 이슈 | 28건 | 27.5% | **P1** |

### 예상 개선 효과
| 개선 항목 | 현재 | 목표 | 효과 |
|-----------|------|------|------|
| **Contract 검증률** | 75.0% | 90%+ | +15% |
| **FAIL 건수** | 16건 (15.7%) | 5건 이하 (5%) | -69% |
| **REVIEW_NEEDED** | 50건 (49.0%) | 30건 이하 (30%) | -40% |
| **PASS 비율** | 35.3% | 65%+ | +84% |

### 재무 영향
- **즉시 환급 필요**: 700 USD (MASTER DO FEE AIR 과다 청구)
- **추가 청구 필요**: 140 USD (MASTER DO FEE CONTAINER 과소 청구)
- **순 영향**: -560 USD (환급 > 추가 청구)

---

## 5️⃣ 부록: 상세 데이터

### A. REVIEW_NEEDED 항목별 상세
*(50건 전체 리스트는 CSV 파일 참조)*

### B. FAIL 항목별 상세
*(16건 전체 리스트는 위 섹션 2.4 참조)*

### C. 개선 추적 체크리스트

#### Phase 1 (즉시, 1-2주)
- [ ] MASTER DO FEE Invoice 수정 (12건)
- [ ] Portal Fees PDF 파싱 로직 개선
- [ ] THC, GATE PASS 등 5개 항목 Configuration 추가

#### Phase 2 (중기, 1-2개월)
- [ ] Transportation Lane Map 20개 이상 등록
- [ ] Container Fees 패턴 분석 및 자동 매칭
- [ ] At Cost 검증 로직 개선

#### Phase 3 (장기, 3-6개월)
- [ ] AI 기반 요율 예측 시스템
- [ ] 실시간 시장 요율 연동

---

**작성자**: MACHO-GPT v3.6-APEX
**분석 완료**: 2025-10-14
**다음 리뷰**: 2025-10-21 (1주 후)

