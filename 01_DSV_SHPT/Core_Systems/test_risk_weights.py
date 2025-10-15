"""Risk Score Weight Testing Tool

여러 가중치 설정을 테스트하고 결과를 비교하는 도구입니다.
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import os
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class RiskWeightTester:
    """Risk Score Weight 테스트 클래스"""
    
    def __init__(self, results_dir: str = "Results/Sept_2025/CSV"):
        self.results_dir = results_dir
        self.test_results = {}
        
    def test_weight_configurations(
        self, 
        validation_data: pd.DataFrame,
        weight_configs: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        여러 가중치 설정을 테스트하고 결과 비교
        
        Args:
            validation_data: 검증 결과 DataFrame
            weight_configs: 테스트할 가중치 설정 리스트
            
        Returns:
            비교 결과 DataFrame (설정별 정확도, FP/FN rate)
        """
        
        logger.info(f"Testing {len(weight_configs)} weight configurations")
        
        comparison_results = []
        
        for i, config in enumerate(weight_configs):
            config_name = config.get('name', f'config_{i+1}')
            weights = config.get('weights', {})
            threshold = config.get('trigger_threshold', 0.8)
            
            logger.info(f"Testing configuration: {config_name}")
            
            # 해당 설정으로 리스크 점수 재계산
            recalculated_scores = self._recalculate_risk_scores(
                validation_data, weights, threshold
            )
            
            # 성능 지표 계산
            performance_metrics = self._calculate_performance_metrics(
                validation_data, recalculated_scores, threshold
            )
            
            result = {
                'config_name': config_name,
                'weights': weights,
                'trigger_threshold': threshold,
                'performance_metrics': performance_metrics,
                'recalculated_scores': recalculated_scores
            }
            
            comparison_results.append(result)
        
        # 결과를 DataFrame으로 변환
        comparison_df = self._create_comparison_dataframe(comparison_results)
        
        return comparison_df
    
    def _recalculate_risk_scores(
        self, 
        df: pd.DataFrame, 
        weights: Dict[str, float], 
        threshold: float
    ) -> pd.Series:
        """가중치 설정으로 리스크 점수 재계산"""
        
        # 기본 가중치 (현재 설정)
        default_weights = {
            'delta': 0.4,
            'anomaly': 0.3,
            'certification': 0.2,
            'signature': 0.1
        }
        
        # 가중치 업데이트
        final_weights = {**default_weights, **weights}
        
        # 가중치 합계 검증
        weight_sum = sum(final_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            logger.warning(f"Weight sum is {weight_sum}, normalizing to 1.0")
            final_weights = {k: v/weight_sum for k, v in final_weights.items()}
        
        # 리스크 점수 재계산
        risk_scores = []
        
        for _, row in df.iterrows():
            # 각 구성 요소 점수 추출
            delta_score = self._extract_component_score(row, 'delta')
            anomaly_score = self._extract_component_score(row, 'anomaly')
            cert_score = self._extract_component_score(row, 'certification')
            sig_score = self._extract_component_score(row, 'signature')
            
            # 가중 평균 계산
            risk_score = (
                final_weights['delta'] * delta_score +
                final_weights['anomaly'] * anomaly_score +
                final_weights['certification'] * cert_score +
                final_weights['signature'] * sig_score
            )
            
            risk_scores.append(risk_score)
        
        return pd.Series(risk_scores, index=df.index)
    
    def _extract_component_score(self, row: pd.Series, component: str) -> float:
        """risk_components에서 개별 구성 요소 점수 추출"""
        
        try:
            risk_components = row.get('risk_components', {})
            
            if isinstance(risk_components, str):
                components = json.loads(risk_components)
            elif isinstance(risk_components, dict):
                components = risk_components
            else:
                return 0.0
            
            return float(components.get(component, 0.0))
            
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            return 0.0
    
    def _calculate_performance_metrics(
        self, 
        df: pd.DataFrame, 
        new_risk_scores: pd.Series, 
        threshold: float
    ) -> Dict[str, float]:
        """성능 지표 계산"""
        
        # 현재 리스크 트리거 상태
        current_triggered = df['risk_triggered'].fillna(False)
        
        # 새로운 리스크 트리거 상태 (threshold 기반)
        new_triggered = new_risk_scores >= threshold
        
        # 실제 상태 (검증 결과 기반)
        actual_status = df['status'].fillna('UNKNOWN')
        is_high_risk = actual_status.isin(['ERROR', 'FAIL', 'REVIEW_NEEDED'])
        
        # True Positive: 올바르게 위험으로 식별
        tp = ((new_triggered == True) & (is_high_risk == True)).sum()
        
        # False Positive: 잘못 위험으로 식별
        fp = ((new_triggered == True) & (is_high_risk == False)).sum()
        
        # True Negative: 올바르게 안전으로 식별
        tn = ((new_triggered == False) & (is_high_risk == False)).sum()
        
        # False Negative: 잘못 안전으로 식별
        fn = ((new_triggered == False) & (is_high_risk == True)).sum()
        
        # 성능 지표 계산
        total = len(df)
        
        metrics = {
            'total_items': total,
            'true_positive': int(tp),
            'false_positive': int(fp),
            'true_negative': int(tn),
            'false_negative': int(fn),
            'false_positive_rate': float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
            'false_negative_rate': float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
            'precision': float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0,
            'recall': float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0,
            'accuracy': float((tp + tn) / total) if total > 0 else 0.0,
            'f1_score': 0.0
        }
        
        # F1 Score 계산
        if metrics['precision'] > 0 and metrics['recall'] > 0:
            metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
        
        return metrics
    
    def _create_comparison_dataframe(self, comparison_results: List[Dict]) -> pd.DataFrame:
        """비교 결과를 DataFrame으로 변환"""
        
        comparison_data = []
        
        for result in comparison_results:
            config_name = result['config_name']
            weights = result['weights']
            threshold = result['trigger_threshold']
            metrics = result['performance_metrics']
            
            row = {
                'config_name': config_name,
                'delta_weight': weights.get('delta', 0.4),
                'anomaly_weight': weights.get('anomaly', 0.3),
                'certification_weight': weights.get('certification', 0.2),
                'signature_weight': weights.get('signature', 0.1),
                'trigger_threshold': threshold,
                'total_items': metrics['total_items'],
                'true_positive': metrics['true_positive'],
                'false_positive': metrics['false_positive'],
                'true_negative': metrics['true_negative'],
                'false_negative': metrics['false_negative'],
                'false_positive_rate': metrics['false_positive_rate'],
                'false_negative_rate': metrics['false_negative_rate'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'accuracy': metrics['accuracy'],
                'f1_score': metrics['f1_score']
            }
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def generate_comparison_report(self, comparison_df: pd.DataFrame, output_path: str = None) -> str:
        """비교 보고서 생성"""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"RISK_WEIGHT_COMPARISON_REPORT_{timestamp}.md"
        
        # 보고서 생성
        report_content = self._create_comparison_report_content(comparison_df)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Comparison report saved: {output_path}")
        return output_path
    
    def _create_comparison_report_content(self, comparison_df: pd.DataFrame) -> str:
        """비교 보고서 내용 생성"""
        
        report = f"""# Risk Score Weight Configuration Comparison Report

**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**테스트 설정 수**: {len(comparison_df)}
**테스트 항목 수**: {comparison_df['total_items'].iloc[0] if len(comparison_df) > 0 else 0}

---

## 📊 설정별 성능 비교

| 설정명 | Delta | Anomaly | Cert | Sig | Threshold | FPR | FNR | Precision | Recall | F1 | Accuracy |
|--------|-------|---------|------|-----|-----------|-----|-----|-----------|--------|----|-----------|
"""
        
        for _, row in comparison_df.iterrows():
            report += f"| {row['config_name']} | {row['delta_weight']:.2f} | {row['anomaly_weight']:.2f} | {row['certification_weight']:.2f} | {row['signature_weight']:.2f} | {row['trigger_threshold']:.2f} | {row['false_positive_rate']:.1%} | {row['false_negative_rate']:.1%} | {row['precision']:.3f} | {row['recall']:.3f} | {row['f1_score']:.3f} | {row['accuracy']:.3f} |\n"
        
        # 최고 성능 설정 찾기
        best_f1 = comparison_df.loc[comparison_df['f1_score'].idxmax()]
        best_accuracy = comparison_df.loc[comparison_df['accuracy'].idxmax()]
        best_low_fpr = comparison_df.loc[comparison_df['false_positive_rate'].idxmin()]
        
        report += f"""
---

## 🏆 최고 성능 설정

### 최고 F1 Score
- **설정**: {best_f1['config_name']}
- **F1 Score**: {best_f1['f1_score']:.3f}
- **가중치**: Delta={best_f1['delta_weight']:.2f}, Anomaly={best_f1['anomaly_weight']:.2f}, Cert={best_f1['certification_weight']:.2f}, Sig={best_f1['signature_weight']:.2f}
- **Threshold**: {best_f1['trigger_threshold']:.2f}

### 최고 Accuracy
- **설정**: {best_accuracy['config_name']}
- **Accuracy**: {best_accuracy['accuracy']:.3f}
- **FPR**: {best_accuracy['false_positive_rate']:.1%}
- **FNR**: {best_accuracy['false_negative_rate']:.1%}

### 최저 False Positive Rate
- **설정**: {best_low_fpr['config_name']}
- **FPR**: {best_low_fpr['false_positive_rate']:.1%}
- **FNR**: {best_low_fpr['false_negative_rate']:.1%}
- **Trade-off**: FPR 감소로 인한 FNR 증가

---

## 📈 상세 분석

### 성능 지표 분포

"""
        
        # 성능 지표 통계
        metrics_stats = comparison_df[['false_positive_rate', 'false_negative_rate', 'precision', 'recall', 'accuracy', 'f1_score']].describe()
        
        for metric in ['false_positive_rate', 'false_negative_rate', 'precision', 'recall', 'accuracy', 'f1_score']:
            mean_val = metrics_stats.loc['mean', metric]
            std_val = metrics_stats.loc['std', metric]
            min_val = metrics_stats.loc['min', metric]
            max_val = metrics_stats.loc['max', metric]
            
            report += f"- **{metric.replace('_', ' ').title()}**: 평균 {mean_val:.3f} (±{std_val:.3f}), 범위 {min_val:.3f}-{max_val:.3f}\n"
        
        # 권장사항
        report += f"""
---

## 🎯 권장사항

### 즉시 적용 가능한 설정
"""
        
        # F1 Score 기준 상위 3개 설정
        top_configs = comparison_df.nlargest(3, 'f1_score')
        
        for i, (_, config) in enumerate(top_configs.iterrows(), 1):
            report += f"""
#### {i}순위: {config['config_name']}
- **F1 Score**: {config['f1_score']:.3f}
- **Accuracy**: {config['accuracy']:.3f}
- **FPR**: {config['false_positive_rate']:.1%}
- **FNR**: {config['false_negative_rate']:.1%}
- **권장 이유**: 균형잡힌 성능과 낮은 오류율
"""
        
        # 시나리오별 추천
        report += f"""
### 시나리오별 추천

#### 계약 준수 중시
- **추천 설정**: Delta 가중치가 높은 설정
- **기준**: Delta weight > 0.4, FPR < 5%

#### 이상 패턴 탐지 중시  
- **추천 설정**: Anomaly 가중치가 높은 설정
- **기준**: Anomaly weight > 0.35, FNR < 10%

#### 균형형 운영
- **추천 설정**: F1 Score가 높은 설정
- **기준**: F1 Score > 0.8, FPR < 5%, FNR < 10%

---

## 📋 다음 단계

1. **도메인 전문가 검토**: 추천 설정에 대한 비즈니스 검토
2. **A/B 테스트**: 운영 환경에서 제한적 테스트
3. **성능 모니터링**: 1주일 모니터링 후 성능 평가
4. **최종 적용**: 성능 검증 후 전체 적용

---

**보고서 생성자**: RiskWeightTester
**분석 일시**: {datetime.now().isoformat()}
"""
        
        return report


def test_risk_weights(
    results_dir: str = "Results/Sept_2025/CSV",
    config_files: List[str] = None,
    output_path: str = None
) -> str:
    """
    Risk Score 가중치 테스트 실행 (편의 함수)
    
    Args:
        results_dir: 결과 CSV 파일들이 있는 디렉토리
        config_files: 테스트할 설정 파일 경로 리스트
        output_path: 비교 보고서 출력 경로
        
    Returns:
        생성된 보고서 파일 경로
    """
    
    tester = RiskWeightTester(results_dir)
    
    # 기본 테스트 설정 (설정 파일이 없는 경우)
    if not config_files:
        default_configs = [
            {
                'name': 'current',
                'weights': {'delta': 0.4, 'anomaly': 0.3, 'certification': 0.2, 'signature': 0.1},
                'trigger_threshold': 0.8
            },
            {
                'name': 'contract_focus',
                'weights': {'delta': 0.5, 'anomaly': 0.25, 'certification': 0.15, 'signature': 0.1},
                'trigger_threshold': 0.75
            },
            {
                'name': 'anomaly_focus',
                'weights': {'delta': 0.3, 'anomaly': 0.45, 'certification': 0.15, 'signature': 0.1},
                'trigger_threshold': 0.7
            },
            {
                'name': 'compliance_focus',
                'weights': {'delta': 0.3, 'anomaly': 0.2, 'certification': 0.4, 'signature': 0.1},
                'trigger_threshold': 0.8
            },
            {
                'name': 'balanced',
                'weights': {'delta': 0.35, 'anomaly': 0.3, 'certification': 0.25, 'signature': 0.1},
                'trigger_threshold': 0.75
            }
        ]
        
        weight_configs = default_configs
    else:
        # 설정 파일에서 로드
        weight_configs = []
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    weight_configs.append(config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
    
    # 최신 CSV 파일 로드
    csv_files = list(Path(results_dir).glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {results_dir}")
        return ""
    
    latest_csv = max(csv_files, key=os.path.getctime)
    validation_data = pd.read_csv(latest_csv)
    
    logger.info(f"Loaded {len(validation_data)} rows from {latest_csv}")
    
    # 테스트 실행
    comparison_df = tester.test_weight_configurations(validation_data, weight_configs)
    
    # 보고서 생성
    report_path = tester.generate_comparison_report(comparison_df, output_path)
    
    return report_path


if __name__ == "__main__":
    # 테스트 실행
    report_path = test_risk_weights()
    print(f"Risk weight comparison report created: {report_path}")
