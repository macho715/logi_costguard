# Anomaly Detection Tuning Report

**생성 일시**: 2025-10-16 02:02:22
**분석 데이터**: 216개 항목
**레인 수**: 28개

---

## 📊 전체 분석 결과

### 기본 통계
- **총 항목 수**: 216
- **레인 수**: 216

### Delta 분포 (전체)

- **평균**: 2.87%
- **표준편차**: 47.27%
- **중앙값**: 0.00%
- **95th Percentile**: 32.86%
- **99th Percentile**: 109.97%

### Charge Group 분포
- **Contract**: 128개
- **Other**: 52개
- **AtCost**: 28개
- **PortalFee**: 8개

### Status 분포
- **ERROR**: 216개

---

## 🎯 레인별 최적 Threshold 추천

| 레인 | 샘플 수 | 현재 Threshold | 권장 Threshold | 신뢰도 | 근거 |
|------|---------|----------------|----------------|--------|------|
| SCT0126 | 18 | 3.0 | **3.0** | 🟢 medium | Standard threshold based on sample size... |
| SCT0127 | 16 | 3.0 | **3.0** | 🟢 medium | Standard threshold based on sample size... |
| SCT0038 | 2 | 3.0 | **3.7** | 🔴 very_low | Small sample size (2) - using conservative thresho... |
| SCT0122 | 16 | 3.0 | **3.0** | 🟢 medium | Standard threshold based on sample size... |
| SCT0131 | 14 | 3.0 | **4.0** | 🟡 low | High delta variability - increased threshold for s... |
| SCT0123,0124 | 20 | 3.0 | **2.7** | 🟢 medium | Low delta variability - can use more sensitive thr... |
| SCT0134 | 16 | 3.0 | **3.5** | 🟢 medium | High delta variability - increased threshold for s... |
| HE0471 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0472 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0473 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0450,0459,0460 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0466,0467,0468 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0464,0465,0470 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0437,0438-2,0439-2,0440-1,044 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0487 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0438-0454 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0425,0426,0427,0428 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0475 | 4 | 3.0 | **3.7** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0497 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0500 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0488 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0495,0496 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0498 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0501 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0502 | 4 | 3.0 | **4.5** | 🔴 very_low | Small sample size (4) - using conservative thresho... |
| HE0499L1 | 20 | 3.0 | **2.7** | 🟢 medium | Low delta variability - can use more sensitive thr... |
| HE0499L2 | 10 | 3.0 | **3.2** | 🟡 low | Low delta variability - can use more sensitive thr... |
| HE0499L3 | 12 | 3.0 | **4.0** | 🟡 low | High delta variability - increased threshold for s... |

---

## 📈 상세 분석

### High-Volume Lanes (샘플 > 20)

### Medium-Volume Lanes (샘플 10-20)
- **SCT0126**: 18개 샘플, 권장 threshold 3.0
- **SCT0127**: 16개 샘플, 권장 threshold 3.0
- **SCT0122**: 16개 샘플, 권장 threshold 3.0
- **SCT0131**: 14개 샘플, 권장 threshold 4.0
- **SCT0123,0124**: 20개 샘플, 권장 threshold 2.7
- **SCT0134**: 16개 샘플, 권장 threshold 3.5
- **HE0499L1**: 20개 샘플, 권장 threshold 2.7
- **HE0499L2**: 10개 샘플, 권장 threshold 3.2
- **HE0499L3**: 12개 샘플, 권장 threshold 4.0

### Low-Volume Lanes (샘플 < 10)
- **SCT0038**: 2개 샘플, 권장 threshold 3.7 (보수적)
- **HE0471**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0472**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0473**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0450,0459,0460**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0466,0467,0468**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0464,0465,0470**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0437,0438-2,0439-2,0440-1,044**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0487**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0438-0454**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0425,0426,0427,0428**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0475**: 4개 샘플, 권장 threshold 3.7 (보수적)
- **HE0497**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0500**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0488**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0495,0496**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0498**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0501**: 4개 샘플, 권장 threshold 4.5 (보수적)
- **HE0502**: 4개 샘플, 권장 threshold 4.5 (보수적)

---

## 🎯 권장사항

### 즉시 적용 가능
1. **High-Volume Lanes**: 더 민감한 threshold 적용 (2.5-2.8)
2. **Medium-Volume Lanes**: 현재 threshold 유지 (3.0-3.2)
3. **Low-Volume Lanes**: 보수적 threshold 적용 (3.5-4.0)

### 설정 파일 업데이트
```json
{
  "lanes": {
    "SCT0126": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.0,
            "min_samples": 10
          }
        }
      }
    },
    "SCT0127": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.0,
            "min_samples": 10
          }
        }
      }
    },
    "SCT0038": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "SCT0122": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.0,
            "min_samples": 10
          }
        }
      }
    },
    "SCT0131": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.0,
            "min_samples": 8
          }
        }
      }
    },
    "SCT0123,0124": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 2.7,
            "min_samples": 10
          }
        }
      }
    },
    "SCT0134": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.5,
            "min_samples": 10
          }
        }
      }
    },
    "HE0471": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0472": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0473": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0450,0459,0460": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0466,0467,0468": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0464,0465,0470": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0437,0438-2,0439-2,0440-1,044": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0487": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0438-0454": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0425,0426,0427,0428": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0475": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.7,
            "min_samples": 5
          }
        }
      }
    },
    "HE0497": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0500": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0488": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0495,0496": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0498": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0501": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0502": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.5,
            "min_samples": 5
          }
        }
      }
    },
    "HE0499L1": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 2.7,
            "min_samples": 10
          }
        }
      }
    },
    "HE0499L2": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 3.2,
            "min_samples": 8
          }
        }
      }
    },
    "HE0499L3": {
      "anomaly_detection": {
        "enabled": true,
        "model": {
          "type": "robust_zscore",
          "params": {
            "threshold": 4.0,
            "min_samples": 8
          }
        }
      }
    },
  }
}
```

### 모니터링 지표
1. **False Positive Rate**: < 5%
2. **False Negative Rate**: < 10%
3. **Detection Accuracy**: > 85%

### 다음 단계
1. 권장 threshold로 설정 파일 업데이트
2. 1주일 모니터링 후 성능 평가
3. 필요시 추가 조정

---

**보고서 생성자**: AnomalyDetectionTuner
**분석 일시**: 2025-10-16T02:02:22.284395
