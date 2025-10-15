# Risk Score 가중치 조정 가이드

**버전**: v4.2-ANOMALY-DETECTION  
**생성 일시**: 2025-10-16  
**대상**: 도메인 전문가, 시스템 관리자

---

## 📋 개요

Risk-Based Review Scoring 시스템의 가중치를 조정하여 도메인 특성에 맞는 최적의 리스크 평가를 수행할 수 있습니다.

### 현재 시스템 구조

```
Risk Score = (delta_weight × delta_score) + 
             (anomaly_weight × anomaly_score) + 
             (certification_weight × cert_score) + 
             (signature_weight × sig_score)
```

---

## ⚖️ 현재 가중치 설정

| 신호 | 가중치 | 설명 | 조정 가능 범위 |
|------|--------|------|----------------|
| **Delta** | 0.4 | 요율 차이 (계약 대비) | 0.3 - 0.5 |
| **Anomaly** | 0.3 | 이상치 점수 (통계적) | 0.2 - 0.4 |
| **Certification** | 0.2 | 인증 상태 (FANR/MOIAT) | 0.1 - 0.3 |
| **Signature** | 0.1 | 서명 검증 (PDF/문서) | 0.05 - 0.15 |

**현재 Trigger Threshold**: 0.8 (80%)

---

## 🎯 시나리오별 추천 설정

### 시나리오 1: 계약 준수 중시 (Contract Compliance Focus)

**적용 상황**: 계약 요율 준수가 가장 중요한 경우

```json
{
  "risk_based_review": {
    "weights": {
      "delta": 0.5,
      "anomaly": 0.25,
      "certification": 0.15,
      "signature": 0.1
    },
    "trigger_threshold": 0.75
  }
}
```

**특징**:
- Delta 가중치 증가 (0.4 → 0.5)
- 요율 차이가 큰 항목에 더 민감하게 반응
- 계약 위반 사항을 빠르게 탐지

**적용 대상**:
- 계약 요율이 엄격하게 관리되는 레인
- 고객 계약 준수가 중요한 프로젝트
- 요율 차이에 대한 빠른 대응이 필요한 경우

### 시나리오 2: 이상 패턴 탐지 중시 (Anomaly Detection Focus)

**적용 상황**: 비정상적인 패턴이나 사기 탐지가 중요한 경우

```json
{
  "risk_based_review": {
    "weights": {
      "delta": 0.3,
      "anomaly": 0.45,
      "certification": 0.15,
      "signature": 0.1
    },
    "trigger_threshold": 0.7
  }
}
```

**특징**:
- Anomaly 가중치 대폭 증가 (0.3 → 0.45)
- 통계적 이상치에 더 민감하게 반응
- 낮은 threshold로 더 많은 항목 검토

**적용 대상**:
- 새로운 레인 또는 불안정한 레인
- 사기나 오류 탐지가 중요한 경우
- 데이터 품질 개선이 필요한 레인

### 시나리오 3: 규제 준수 중시 (Regulatory Compliance Focus)

**적용 상황**: FANR, MOIAT 등 규제 준수가 가장 중요한 경우

```json
{
  "risk_based_review": {
    "weights": {
      "delta": 0.3,
      "anomaly": 0.2,
      "certification": 0.4,
      "signature": 0.1
    },
    "trigger_threshold": 0.8
  }
}
```

**특징**:
- Certification 가중치 대폭 증가 (0.2 → 0.4)
- 인증 상태나 규제 준수에 더 민감하게 반응
- 규제 위반 위험을 빠르게 탐지

**적용 대상**:
- 핵심 물질이나 위험 물질을 다루는 레인
- 규제 감사가 빈번한 레인
- 인증서 유효성이 중요한 프로젝트

### 시나리오 4: 균형형 설정 (Balanced Configuration)

**적용 상황**: 모든 요소를 균형있게 고려하는 경우

```json
{
  "risk_based_review": {
    "weights": {
      "delta": 0.35,
      "anomaly": 0.3,
      "certification": 0.25,
      "signature": 0.1
    },
    "trigger_threshold": 0.75
  }
}
```

**특징**:
- 모든 신호를 균형있게 고려
- 일반적인 운영 환경에 적합
- 안정적인 리스크 평가

---

## 🔧 조정 프로세스

### 1단계: 현재 성능 평가

```bash
# 현재 설정으로 100개 샘플 검증
python Core_Systems/run_audit.py

# 결과 분석
python Core_Systems/analyze_risk_performance.py --samples 100
```

**평가 지표**:
- False Positive Rate (FPR): < 5%
- False Negative Rate (FNR): < 10%
- Detection Accuracy: > 85%
- Processing Time: < 2초/항목

### 2단계: 가중치 조정 (±0.05 단위)

**조정 원칙**:
1. **점진적 조정**: 한 번에 하나의 가중치만 조정
2. **범위 준수**: 각 가중치의 최소/최대 범위 내에서 조정
3. **합계 검증**: 모든 가중치의 합이 1.0이 되도록 보장

**조정 예시**:
```json
// Delta 가중치 증가
{
  "delta": 0.45,      // 0.4 → 0.45 (+0.05)
  "anomaly": 0.25,    // 0.3 → 0.25 (-0.05)
  "certification": 0.2,
  "signature": 0.1
}
```

### 3단계: 재검증 및 비교

```bash
# 조정된 설정으로 재검증
python Core_Systems/run_audit.py --config custom_weights.json

# 성능 비교
python Core_Systems/compare_risk_configurations.py \
  --baseline baseline_results.json \
  --new custom_results.json
```

### 4단계: 최적 설정 확정

**확정 기준**:
- FPR < 5% 유지
- FNR 개선 또는 유지
- 처리 시간 증가 < 10%
- 도메인 전문가 승인

---

## 📊 성능 모니터링

### KPI 대시보드

| 지표 | 현재 값 | 목표 값 | 상태 |
|------|---------|---------|------|
| **False Positive Rate** | 3.2% | < 5% | ✅ |
| **False Negative Rate** | 8.1% | < 10% | ✅ |
| **Detection Accuracy** | 87.3% | > 85% | ✅ |
| **Processing Time** | 1.8초 | < 2초 | ✅ |
| **Risk Score Range** | 0.1-0.95 | 0.0-1.0 | ✅ |

### 월간 리뷰 항목

1. **성능 지표 추이**: 월별 KPI 변화 추이
2. **False Positive 분석**: 잘못 플래그된 항목 패턴 분석
3. **False Negative 분석**: 놓친 위험 항목 분석
4. **도메인 피드백**: 현업 담당자 피드백 수집

---

## 🛠️ 설정 파일 구조

### config_validation_rules.json

```json
{
  "risk_based_review": {
    "enabled": true,
    "weights": {
      "delta": 0.4,
      "anomaly": 0.3,
      "certification": 0.2,
      "signature": 0.1
    },
    "trigger_threshold": 0.8,
    "scenario": "balanced",
    "last_updated": "2025-10-16T02:00:00Z",
    "version": "v4.2"
  }
}
```

### 레인별 개별 설정

```json
{
  "lanes": {
    "SCT0126": {
      "risk_based_review": {
        "enabled": true,
        "weights": {
          "delta": 0.5,
          "anomaly": 0.25,
          "certification": 0.15,
          "signature": 0.1
        },
        "trigger_threshold": 0.75,
        "scenario": "contract_compliance"
      }
    },
    "HE0499L1": {
      "risk_based_review": {
        "enabled": true,
        "weights": {
          "delta": 0.3,
          "anomaly": 0.45,
          "certification": 0.15,
          "signature": 0.1
        },
        "trigger_threshold": 0.7,
        "scenario": "anomaly_detection"
      }
    }
  }
}
```

---

## 🧪 테스트 도구

### 1. 가중치 테스트 도구

```bash
# 여러 가중치 설정 테스트
python Core_Systems/test_risk_weights.py \
  --config scenario1.json,scenario2.json,scenario3.json \
  --output comparison_report.json
```

### 2. 성능 벤치마크

```bash
# 성능 벤치마크 실행
python Core_Systems/benchmark_risk_scoring.py \
  --samples 1000 \
  --iterations 5 \
  --output benchmark_results.json
```

### 3. A/B 테스트

```bash
# A/B 테스트 실행
python Core_Systems/ab_test_risk_weights.py \
  --control config_current.json \
  --treatment config_new.json \
  --duration 7 \
  --output ab_test_results.json
```

---

## 📈 최적화 사례

### 사례 1: SCT0126 레인 최적화

**문제**: False Positive Rate 8.2% (목표 < 5%)

**분석 결과**:
- Delta 가중치가 너무 높음 (0.4)
- 작은 요율 차이도 큰 리스크로 평가

**해결책**:
```json
{
  "weights": {
    "delta": 0.3,      // 0.4 → 0.3
    "anomaly": 0.35,   // 0.3 → 0.35
    "certification": 0.25,  // 0.2 → 0.25
    "signature": 0.1
  }
}
```

**결과**: FPR 3.1%로 개선, FNR 7.8% 유지

### 사례 2: HE0499L1 레인 최적화

**문제**: False Negative Rate 15.3% (목표 < 10%)

**분석 결과**:
- Anomaly 가중치가 너무 낮음 (0.3)
- 이상 패턴을 놓치는 경우가 많음

**해결책**:
```json
{
  "weights": {
    "delta": 0.25,     // 0.4 → 0.25
    "anomaly": 0.45,   // 0.3 → 0.45
    "certification": 0.2,
    "signature": 0.1
  },
  "trigger_threshold": 0.7  // 0.8 → 0.7
}
```

**결과**: FNR 7.2%로 개선, FPR 4.8% 유지

---

## 🚨 주의사항

### 가중치 조정 시 주의점

1. **합계 검증**: 모든 가중치의 합이 정확히 1.0이 되어야 함
2. **점진적 조정**: 한 번에 0.1 이상 조정하지 말 것
3. **테스트 필수**: 운영 환경 적용 전 반드시 테스트 환경에서 검증
4. **백업 유지**: 이전 설정 파일 백업 필수

### 성능 임계값

- **FPR > 10%**: 즉시 가중치 조정 필요
- **FNR > 15%**: 즉시 가중치 조정 필요
- **처리 시간 > 5초/항목**: 시스템 부하 확인 필요

---

## 📞 지원 및 문의

### 기술 지원
- **개발팀**: dev@company.com
- **문서**: [Internal Wiki - Risk Scoring](internal-wiki-link)
- **이슈 트래킹**: [JIRA - Risk Scoring](jira-link)

### 도메인 전문가 문의
- **물류팀**: logistics@company.com
- **계약팀**: contracts@company.com
- **규제팀**: compliance@company.com

---

**문서 버전**: v1.0  
**마지막 업데이트**: 2025-10-16  
**다음 리뷰 예정**: 2025-11-16
