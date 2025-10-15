"""Anomaly Detection Tuning Module

실제 데이터를 분석하여 레인별 최적 threshold를 계산하고 튜닝 보고서를 생성합니다.
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class AnomalyDetectionTuner:
    """Anomaly Detection 튜닝 클래스"""
    
    def __init__(self, results_dir: str = "Results/Sept_2025/CSV"):
        self.results_dir = results_dir
        self.analysis_results = {}
        
    def analyze_historical_data(self, csv_files: List[str]) -> Dict[str, Any]:
        """
        과거 데이터 분석 및 최적 threshold 도출
        
        Args:
            csv_files: 분석할 CSV 파일 경로 리스트
            
        Returns:
            분석 결과 딕셔너리
        """
        logger.info(f"Analyzing historical data from {len(csv_files)} files")
        
        all_data = []
        
        # 모든 CSV 파일 로드
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                all_data.append(df)
                logger.info(f"Loaded {len(df)} rows from {csv_file}")
            except Exception as e:
                logger.warning(f"Failed to load {csv_file}: {e}")
        
        if not all_data:
            logger.error("No data loaded for analysis")
            return {}
        
        # 데이터 병합
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined_df)} rows")
        
        # 레인별 분석
        lane_analysis = {}
        
        for lane in combined_df['sheet_name'].unique():
            if pd.isna(lane):
                continue
                
            lane_data = combined_df[combined_df['sheet_name'] == lane]
            lane_analysis[lane] = self._analyze_lane_data(lane_data, lane)
        
        # 전체 분석
        overall_analysis = self._analyze_overall_data(combined_df)
        
        self.analysis_results = {
            'overall': overall_analysis,
            'lanes': lane_analysis,
            'total_samples': len(combined_df),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return self.analysis_results
    
    def _analyze_lane_data(self, lane_df: pd.DataFrame, lane_name: str) -> Dict[str, Any]:
        """개별 레인 데이터 분석"""
        
        # Delta 분포 분석
        delta_values = lane_df['delta_pct'].dropna()
        
        if len(delta_values) == 0:
            return {
                'lane': lane_name,
                'sample_count': len(lane_df),
                'delta_stats': {},
                'recommendations': {
                    'threshold': 3.0,
                    'min_samples': 10,
                    'confidence': 'low'
                }
            }
        
        # 통계 계산
        delta_stats = {
            'mean': float(delta_values.mean()),
            'std': float(delta_values.std()),
            'median': float(delta_values.median()),
            'q25': float(delta_values.quantile(0.25)),
            'q75': float(delta_values.quantile(0.75)),
            'q90': float(delta_values.quantile(0.90)),
            'q95': float(delta_values.quantile(0.95)),
            'q99': float(delta_values.quantile(0.99)),
            'min': float(delta_values.min()),
            'max': float(delta_values.max()),
            'count': len(delta_values)
        }
        
        # Anomaly Score 분석
        anomaly_scores = []
        for _, row in lane_df.iterrows():
            if pd.notna(row['anomaly_detection']):
                try:
                    if isinstance(row['anomaly_detection'], str):
                        anomaly_data = json.loads(row['anomaly_detection'])
                    else:
                        anomaly_data = row['anomaly_detection']
                    
                    if isinstance(anomaly_data, dict) and 'score' in anomaly_data:
                        anomaly_scores.append(float(anomaly_data['score']))
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
        
        anomaly_stats = {}
        if anomaly_scores:
            anomaly_stats = {
                'mean': float(np.mean(anomaly_scores)),
                'std': float(np.std(anomaly_scores)),
                'median': float(np.median(anomaly_scores)),
                'q95': float(np.percentile(anomaly_scores, 95)),
                'max': float(np.max(anomaly_scores)),
                'count': len(anomaly_scores)
            }
        
        # 권장 threshold 계산
        recommendations = self._calculate_optimal_thresholds(
            delta_stats, anomaly_stats, len(lane_df)
        )
        
        return {
            'lane': lane_name,
            'sample_count': len(lane_df),
            'delta_stats': delta_stats,
            'anomaly_stats': anomaly_stats,
            'recommendations': recommendations
        }
    
    def _analyze_overall_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """전체 데이터 분석"""
        
        # Delta 분포 분석
        delta_values = df['delta_pct'].dropna()
        
        overall_stats = {
            'total_items': len(df),
            'lanes_count': df['sheet_name'].nunique(),
            'delta_distribution': {
                'mean': float(delta_values.mean()) if len(delta_values) > 0 else 0,
                'std': float(delta_values.std()) if len(delta_values) > 0 else 0,
                'median': float(delta_values.median()) if len(delta_values) > 0 else 0,
                'q95': float(delta_values.quantile(0.95)) if len(delta_values) > 0 else 0,
                'q99': float(delta_values.quantile(0.99)) if len(delta_values) > 0 else 0
            }
        }
        
        # Charge Group별 분석
        charge_groups = df['charge_group'].value_counts().to_dict()
        overall_stats['charge_groups'] = charge_groups
        
        # Status별 분석
        status_counts = df['status'].value_counts().to_dict()
        overall_stats['status_distribution'] = status_counts
        
        return overall_stats
    
    def _calculate_optimal_thresholds(
        self, 
        delta_stats: Dict[str, float], 
        anomaly_stats: Dict[str, float], 
        sample_count: int
    ) -> Dict[str, Any]:
        """최적 threshold 계산"""
        
        # 기본 threshold
        base_threshold = 3.0
        min_samples = 10
        
        # 샘플 수에 따른 조정
        if sample_count < 5:
            confidence = 'very_low'
            threshold = 4.0  # 더 보수적
            min_samples = 5
        elif sample_count < 15:
            confidence = 'low'
            threshold = 3.5
            min_samples = 8
        elif sample_count < 30:
            confidence = 'medium'
            threshold = 3.0
            min_samples = 10
        else:
            confidence = 'high'
            threshold = 2.8  # 더 민감하게
            min_samples = 12
        
        # Delta 분포 기반 조정
        if delta_stats.get('std', 0) > 20:  # 높은 변동성
            threshold += 0.5
        elif delta_stats.get('std', 0) < 5:  # 낮은 변동성
            threshold -= 0.3
        
        # Anomaly Score 기반 조정
        if anomaly_stats and anomaly_stats.get('mean', 0) > 50:
            threshold -= 0.2  # 더 민감하게
        elif anomaly_stats and anomaly_stats.get('mean', 0) < 20:
            threshold += 0.3  # 더 보수적으로
        
        # 최종 범위 제한
        threshold = max(2.0, min(4.5, threshold))
        
        return {
            'threshold': round(threshold, 2),
            'min_samples': min_samples,
            'confidence': confidence,
            'rationale': self._generate_rationale(delta_stats, anomaly_stats, sample_count)
        }
    
    def _generate_rationale(
        self, 
        delta_stats: Dict[str, float], 
        anomaly_stats: Dict[str, float], 
        sample_count: int
    ) -> str:
        """권장사항 근거 생성"""
        
        rationale_parts = []
        
        # 샘플 수 기반
        if sample_count < 10:
            rationale_parts.append(f"Small sample size ({sample_count}) - using conservative threshold")
        elif sample_count > 25:
            rationale_parts.append(f"Large sample size ({sample_count}) - can use more sensitive threshold")
        
        # Delta 변동성 기반
        if delta_stats.get('std', 0) > 20:
            rationale_parts.append("High delta variability - increased threshold for stability")
        elif delta_stats.get('std', 0) < 5:
            rationale_parts.append("Low delta variability - can use more sensitive threshold")
        
        # Anomaly Score 기반
        if anomaly_stats and anomaly_stats.get('mean', 0) > 50:
            rationale_parts.append("High anomaly scores detected - more sensitive threshold recommended")
        
        return "; ".join(rationale_parts) if rationale_parts else "Standard threshold based on sample size"
    
    def recommend_thresholds(self, analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """레인별 최적 threshold 추천"""
        
        if not analysis or 'lanes' not in analysis:
            logger.warning("No analysis data available for recommendations")
            return {}
        
        recommendations = {}
        
        for lane_name, lane_analysis in analysis['lanes'].items():
            rec = lane_analysis.get('recommendations', {})
            recommendations[lane_name] = {
                'threshold': rec.get('threshold', 3.0),
                'min_samples': rec.get('min_samples', 10),
                'confidence': rec.get('confidence', 'medium'),
                'rationale': rec.get('rationale', 'Standard recommendation')
            }
        
        return recommendations
    
    def generate_tuning_report(self, output_path: str = None) -> str:
        """튜닝 보고서 생성"""
        
        if not self.analysis_results:
            logger.error("No analysis results available. Run analyze_historical_data() first.")
            return ""
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"ANOMALY_TUNING_REPORT_{timestamp}.md"
        
        # 보고서 생성
        report_content = self._create_report_content()
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Tuning report saved: {output_path}")
        return output_path
    
    def _create_report_content(self) -> str:
        """보고서 내용 생성"""
        
        analysis = self.analysis_results
        
        report = f"""# Anomaly Detection Tuning Report

**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**분석 데이터**: {analysis.get('total_samples', 0)}개 항목
**레인 수**: {len(analysis.get('lanes', {}))}개

---

## 📊 전체 분석 결과

### 기본 통계
- **총 항목 수**: {analysis.get('total_samples', 0)}
- **레인 수**: {analysis.get('total_samples', 0)}

### Delta 분포 (전체)
"""
        
        overall = analysis.get('overall', {})
        delta_dist = overall.get('delta_distribution', {})
        
        if delta_dist:
            report += f"""
- **평균**: {delta_dist.get('mean', 0):.2f}%
- **표준편차**: {delta_dist.get('std', 0):.2f}%
- **중앙값**: {delta_dist.get('median', 0):.2f}%
- **95th Percentile**: {delta_dist.get('q95', 0):.2f}%
- **99th Percentile**: {delta_dist.get('q99', 0):.2f}%
"""
        
        # Charge Group 분포
        charge_groups = overall.get('charge_groups', {})
        if charge_groups:
            report += f"""
### Charge Group 분포
"""
            for group, count in charge_groups.items():
                report += f"- **{group}**: {count}개\n"
        
        # Status 분포
        status_dist = overall.get('status_distribution', {})
        if status_dist:
            report += f"""
### Status 분포
"""
            for status, count in status_dist.items():
                report += f"- **{status}**: {count}개\n"
        
        # 레인별 분석
        report += f"""
---

## 🎯 레인별 최적 Threshold 추천

| 레인 | 샘플 수 | 현재 Threshold | 권장 Threshold | 신뢰도 | 근거 |
|------|---------|----------------|----------------|--------|------|
"""
        
        lanes = analysis.get('lanes', {})
        for lane_name, lane_data in lanes.items():
            recommendations = lane_data.get('recommendations', {})
            sample_count = lane_data.get('sample_count', 0)
            
            threshold = recommendations.get('threshold', 3.0)
            confidence = recommendations.get('confidence', 'medium')
            rationale = recommendations.get('rationale', 'Standard')
            
            # 신뢰도 이모지
            confidence_emoji = {
                'very_low': '🔴',
                'low': '🟡', 
                'medium': '🟢',
                'high': '✅'
            }.get(confidence, '❓')
            
            report += f"| {lane_name} | {sample_count} | 3.0 | **{threshold}** | {confidence_emoji} {confidence} | {rationale[:50]}... |\n"
        
        # 상세 분석
        report += f"""
---

## 📈 상세 분석

### High-Volume Lanes (샘플 > 20)
"""
        
        high_volume_lanes = {k: v for k, v in lanes.items() 
                           if v.get('sample_count', 0) > 20}
        
        for lane_name, lane_data in high_volume_lanes.items():
            delta_stats = lane_data.get('delta_stats', {})
            recommendations = lane_data.get('recommendations', {})
            
            report += f"""
#### {lane_name}
- **샘플 수**: {lane_data.get('sample_count', 0)}
- **Delta 평균**: {delta_stats.get('mean', 0):.2f}%
- **Delta 표준편차**: {delta_stats.get('std', 0):.2f}%
- **권장 Threshold**: {recommendations.get('threshold', 3.0)}
- **신뢰도**: {recommendations.get('confidence', 'medium')}
"""
        
        report += f"""
### Medium-Volume Lanes (샘플 10-20)
"""
        
        medium_volume_lanes = {k: v for k, v in lanes.items() 
                             if 10 <= v.get('sample_count', 0) <= 20}
        
        for lane_name, lane_data in medium_volume_lanes.items():
            recommendations = lane_data.get('recommendations', {})
            report += f"- **{lane_name}**: {lane_data.get('sample_count', 0)}개 샘플, 권장 threshold {recommendations.get('threshold', 3.0)}\n"
        
        report += f"""
### Low-Volume Lanes (샘플 < 10)
"""
        
        low_volume_lanes = {k: v for k, v in lanes.items() 
                          if v.get('sample_count', 0) < 10}
        
        for lane_name, lane_data in low_volume_lanes.items():
            recommendations = lane_data.get('recommendations', {})
            report += f"- **{lane_name}**: {lane_data.get('sample_count', 0)}개 샘플, 권장 threshold {recommendations.get('threshold', 3.0)} (보수적)\n"
        
        # 권장사항
        report += f"""
---

## 🎯 권장사항

### 즉시 적용 가능
1. **High-Volume Lanes**: 더 민감한 threshold 적용 (2.5-2.8)
2. **Medium-Volume Lanes**: 현재 threshold 유지 (3.0-3.2)
3. **Low-Volume Lanes**: 보수적 threshold 적용 (3.5-4.0)

### 설정 파일 업데이트
```json
{{
  "lanes": {{
"""
        
        # JSON 설정 예시 생성
        for lane_name, lane_data in lanes.items():
            recommendations = lane_data.get('recommendations', {})
            threshold = recommendations.get('threshold', 3.0)
            min_samples = recommendations.get('min_samples', 10)
            
            report += f"""    "{lane_name}": {{
      "anomaly_detection": {{
        "enabled": true,
        "model": {{
          "type": "robust_zscore",
          "params": {{
            "threshold": {threshold},
            "min_samples": {min_samples}
          }}
        }}
      }}
    }},
"""
        
        report += f"""  }}
}}
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
**분석 일시**: {analysis.get('analysis_timestamp', 'N/A')}
"""
        
        return report


def tune_anomaly_detection(
    results_dir: str = "Results/Sept_2025/CSV",
    output_path: str = None
) -> str:
    """
    Anomaly Detection 튜닝 실행 (편의 함수)
    
    Args:
        results_dir: 결과 CSV 파일들이 있는 디렉토리
        output_path: 튜닝 보고서 출력 경로
        
    Returns:
        생성된 보고서 파일 경로
    """
    
    tuner = AnomalyDetectionTuner(results_dir)
    
    # CSV 파일 찾기
    csv_files = []
    if os.path.exists(results_dir):
        csv_files = list(Path(results_dir).glob("*.csv"))
    
    if not csv_files:
        logger.error(f"No CSV files found in {results_dir}")
        return ""
    
    # 분석 실행
    analysis = tuner.analyze_historical_data([str(f) for f in csv_files])
    
    if not analysis:
        logger.error("Analysis failed")
        return ""
    
    # 보고서 생성
    report_path = tuner.generate_tuning_report(output_path)
    
    return report_path


if __name__ == "__main__":
    # 테스트 실행
    report_path = tune_anomaly_detection()
    print(f"Tuning report created: {report_path}")
