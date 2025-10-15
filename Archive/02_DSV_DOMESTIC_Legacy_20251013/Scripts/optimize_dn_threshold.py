#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DN 검증 임계값 최적화
현재 임계값 분석 및 최적 임계값 제안
"""

import pandas as pd
import glob
import numpy as np


def analyze_similarity_distribution():
    """유사도 분포 분석 및 최적 임계값 제안"""

    # 최신 파일 찾기
    files = glob.glob(
        "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx"
    )
    if not files:
        print("❌ 파일을 찾을 수 없습니다")
        return

    excel_file = max(files)

    print("=" * 80)
    print("DN 검증 임계값 최적화 분석")
    print("=" * 80)
    print(f"\n📂 파일: {excel_file.split('/')[-1]}")

    # 데이터 로드
    items_df = pd.read_excel(excel_file, sheet_name="items")

    # DN 매칭된 항목만 분석
    matched_df = items_df[items_df["dn_matched"] == "Yes"].copy()

    print(f"\n📊 분석 대상: {len(matched_df)}/44개 (DN 매칭 성공)")

    # 유사도 통계
    print(f"\n📈 유사도 분포 통계:")
    print(f"\n1. Origin 유사도:")
    origin_sim = matched_df["dn_origin_similarity"]
    print(f"   평균: {origin_sim.mean():.3f}")
    print(f"   중앙값: {origin_sim.median():.3f}")
    print(f"   최소: {origin_sim.min():.3f}")
    print(f"   최대: {origin_sim.max():.3f}")
    print(f"   표준편차: {origin_sim.std():.3f}")
    print(f"   25th percentile: {origin_sim.quantile(0.25):.3f}")
    print(f"   75th percentile: {origin_sim.quantile(0.75):.3f}")

    print(f"\n2. Destination 유사도:")
    dest_sim = matched_df["dn_dest_similarity"]
    print(f"   평균: {dest_sim.mean():.3f}")
    print(f"   중앙값: {dest_sim.median():.3f}")
    print(f"   최소: {dest_sim.min():.3f}")
    print(f"   최대: {dest_sim.max():.3f}")
    print(f"   표준편차: {dest_sim.std():.3f}")
    print(f"   25th percentile: {dest_sim.quantile(0.25):.3f}")
    print(f"   75th percentile: {dest_sim.quantile(0.75):.3f}")

    print(f"\n3. Vehicle 유사도:")
    vehicle_sim = matched_df["dn_vehicle_similarity"]
    print(f"   평균: {vehicle_sim.mean():.3f}")
    print(f"   중앙값: {vehicle_sim.median():.3f}")
    print(f"   최소: {vehicle_sim.min():.3f}")
    print(f"   최대: {vehicle_sim.max():.3f}")
    print(f"   표준편차: {vehicle_sim.std():.3f}")

    # 임계값 시뮬레이션
    print(f"\n" + "=" * 80)
    print("임계값 시뮬레이션")
    print("=" * 80)

    thresholds_origin = [0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds_dest = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    thresholds_vehicle = [0.3, 0.4, 0.5, 0.6]

    print(f"\n📊 Origin 임계값별 통과율:")
    for threshold in thresholds_origin:
        pass_count = (origin_sim >= threshold).sum()
        print(f"   ≥{threshold:.1f}: {pass_count}/43 ({pass_count/43*100:.1f}%)")

    print(f"\n📊 Destination 임계값별 통과율:")
    for threshold in thresholds_dest:
        pass_count = (dest_sim >= threshold).sum()
        print(f"   ≥{threshold:.1f}: {pass_count}/43 ({pass_count/43*100:.1f}%)")

    print(f"\n📊 Vehicle 임계값별 통과율:")
    for threshold in thresholds_vehicle:
        pass_count = (vehicle_sim >= threshold).sum()
        print(f"   ≥{threshold:.1f}: {pass_count}/43 ({pass_count/43*100:.1f}%)")

    # 최적 임계값 제안
    print(f"\n" + "=" * 80)
    print("✅ 최적 임계값 제안")
    print("=" * 80)

    # 목표: PASS율 60-80%, FAIL율 10-20%
    print(f"\n🎯 제안 1: 보수적 (높은 정확도)")
    print(f"   Origin: ≥0.40 (통과율: {(origin_sim >= 0.4).sum()/43*100:.1f}%)")
    print(f"   Destination: ≥0.30 (통과율: {(dest_sim >= 0.3).sum()/43*100:.1f}%)")
    print(f"   Vehicle: ≥0.40 (통과율: {(vehicle_sim >= 0.4).sum()/43*100:.1f}%)")

    print(f"\n🎯 제안 2: 균형 (권장)")
    print(f"   Origin: ≥0.30 (통과율: {(origin_sim >= 0.3).sum()/43*100:.1f}%)")
    print(f"   Destination: ≥0.20 (통과율: {(dest_sim >= 0.2).sum()/43*100:.1f}%)")
    print(f"   Vehicle: ≥0.30 (통과율: {(vehicle_sim >= 0.3).sum()/43*100:.1f}%)")

    print(f"\n🎯 제안 3: 관대 (높은 커버리지)")
    print(f"   Origin: ≥0.20 (통과율: {(origin_sim >= 0.2).sum()/43*100:.1f}%)")
    print(f"   Destination: ≥0.10 (통과율: {(dest_sim >= 0.1).sum()/43*100:.1f}%)")
    print(f"   Vehicle: ≥0.20 (통과율: {(vehicle_sim >= 0.2).sum()/43*100:.1f}%)")

    # 현재 임계값으로 PASS 시뮬레이션
    print(f"\n" + "=" * 80)
    print("현재 임계값 (0.70/0.70/0.60) 결과")
    print("=" * 80)

    pass_count_current = (
        (origin_sim >= 0.70) & (dest_sim >= 0.70) & (vehicle_sim >= 0.60)
    ).sum()
    print(f"PASS: {pass_count_current}/43 ({pass_count_current/43*100:.1f}%)")

    # 제안 2로 시뮬레이션
    print(f"\n제안 2 임계값 (0.30/0.20/0.30) 시뮬레이션:")
    pass_count_new = (
        (origin_sim >= 0.30) & (dest_sim >= 0.20) & (vehicle_sim >= 0.30)
    ).sum()
    warn_count_new = (
        ((origin_sim >= 0.30) | (dest_sim >= 0.20))
        & ~((origin_sim >= 0.30) & (dest_sim >= 0.20) & (vehicle_sim >= 0.30))
    ).sum()
    fail_count_new = 43 - pass_count_new - warn_count_new

    print(f"   PASS: {pass_count_new}/43 ({pass_count_new/43*100:.1f}%)")
    print(f"   WARN: {warn_count_new}/43 ({warn_count_new/43*100:.1f}%)")
    print(f"   FAIL: {fail_count_new}/43 ({fail_count_new/43*100:.1f}%)")

    print(f"\n" + "=" * 80)
    print("✅ 분석 완료!")
    print("=" * 80)

    return {
        "recommendation": "threshold_0.30_0.20_0.30",
        "expected_pass_rate": pass_count_new / 43 * 100,
    }


if __name__ == "__main__":
    analyze_similarity_distribution()
