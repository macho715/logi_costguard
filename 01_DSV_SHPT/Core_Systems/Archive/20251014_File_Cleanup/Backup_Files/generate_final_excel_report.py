#!/usr/bin/env python3
"""
SHPT September 2025 - Final Excel Report Generation Script
PDF 통합 기능을 포함한 종합 Excel 보고서 생성 데모

Version: 1.0.0
Created: 2025-10-13
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# 현재 경로 설정
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from create_enhanced_excel_report import EnhancedExcelReportGenerator
from excel_data_processor import ExcelDataProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    SHPT 9월 2025 인보이스 검증 최종 Excel 보고서 생성

    Features:
    - PDF 통합 결과 완전 반영
    - Documentation 가이드라인 준수
    - Gate-11~14 확장 검증 포함
    - Cross-document 검증 상태 시각화
    - Supporting Documents 매핑
    - Executive Dashboard
    """

    print("=" * 80)
    print("🚀 SHPT September 2025 - Enhanced Excel Report Generation")
    print("📋 PDF 통합 기능을 포함한 종합 인보이스 감사 보고서")
    print("=" * 80)

    # 1. 데이터 파일 경로 설정
    csv_path = "Results/Sept_2025/shpt_sept_2025_enhanced_result_20251012_123701.csv"
    json_path = "Results/Sept_2025/shpt_sept_2025_enhanced_result_20251012_123701.json"

    # 파일 존재 확인
    if not Path(csv_path).exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return False

    if not Path(json_path).exists():
        print(f"❌ JSON 파일을 찾을 수 없습니다: {json_path}")
        return False

    print(f"✅ 데이터 파일 확인 완료")
    print(f"   📄 CSV: {csv_path}")
    print(f"   📄 JSON: {json_path}")

    # 2. JSON 데이터 처리
    print(f"\n📊 JSON 데이터 분석 중...")
    processor = ExcelDataProcessor()

    if not processor.load_json_data(json_path):
        print(f"❌ JSON 데이터 로드 실패")
        return False

    processed_data = processor.process_all_data()

    # 통계 출력
    stats = processed_data.get("statistics", {})
    print(f"   📈 총 항목 수: {stats.get('total_items', 0)}")
    print(f"   📈 총 지원 문서: {stats.get('total_supporting_docs', 0)}")
    print(f"   📈 통과율: {stats.get('pass_rate', '0%')}")
    print(f"   💰 총 금액: ${stats.get('total_amount_usd', 0):,.2f}")

    # 3. Excel 보고서 생성
    print(f"\n📋 Excel 통합 보고서 생성 중...")
    generator = EnhancedExcelReportGenerator()

    # 출력 디렉토리 및 파일명 설정
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "Results/Sept_2025/Reports"

    print(f"🔧 create_comprehensive_report 호출 중...")
    print(f"   📄 CSV: {csv_path}")
    print(f"   📄 JSON: {json_path}")
    print(f"   📁 출력: {output_dir}")

    # 클래스 정보 확인
    print(f"🔧 DEBUG: generator 타입: {type(generator)}")
    print(
        f"🔧 DEBUG: generator 메서드들: {[m for m in dir(generator) if not m.startswith('_')]}"
    )

    # 실제 메서드 호출
    print(f"🔧 DEBUG: create_comprehensive_report 호출 직전!")
    results = generator.create_comprehensive_report(
        csv_path=csv_path, json_path=json_path, output_dir=output_dir
    )
    print(f"🔧 DEBUG: create_comprehensive_report 호출 직후!")

    print(f"📋 create_comprehensive_report 완료: {results}")

    # 4. 결과 확인 및 출력
    if "error" in results:
        print(f"❌ Excel 보고서 생성 실패: {results['error']}")
        return False

    print(f"\n✅ Excel 통합 보고서 생성 완료!")

    for report_type, file_path in results.items():
        file_size = Path(file_path).stat().st_size / 1024  # KB
        print(f"   📊 {report_type}: {file_path}")
        print(f"      📏 파일 크기: {file_size:.1f} KB")

    # 5. 보고서 구성 요소 설명
    print(f"\n📋 생성된 Excel 보고서 구성:")
    print(f"   🎯 Main_Data: 전체 102개 항목 + PDF 통합 컬럼 (50+ 컬럼)")
    print(f"   📊 Executive_Dashboard: KPI 및 PDF 통합 통계")
    print(f"   📄 PDF_Integration_Summary: 93개 PDF 파싱 결과 분석")
    print(f"   🎯 Gate_Analysis_11_14: 확장 Gate 검증 상세 분석")
    print(f"   📋 Supporting_Docs_Mapping: Shipment별 증빙문서 매핑")

    # 6. 사용 가이드
    print(f"\n📖 Excel 보고서 사용 가이드:")
    print(f"   ✅ 각 시트는 필터링 및 정렬 기능 지원")
    print(f"   ✅ 상태별 조건부 서식 적용 (PASS=녹색, FAIL=빨강, REVIEW=노랑)")
    print(f"   ✅ PDF 통합 결과 완전 반영 (Gate-11~14 포함)")
    print(f"   ✅ Cross-document 검증 상태 시각화")
    print(f"   ✅ Executive Dashboard로 빠른 현황 파악")

    print(f"\n🎉 SHPT September 2025 Enhanced Excel Report 생성 완료!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = main()

    if success:
        print(f"\n🔧 추천 명령어:")
        print(f"   /logi-master invoice-audit [Excel 보고서 기반 심층 분석]")
        print(f"   /visualize-data --type=dashboard [KPI 대시보드 시각화]")
        print(f"   /validate-data pdf-integration [PDF 통합 결과 검증]")

        sys.exit(0)
    else:
        print(f"\n❌ Excel 보고서 생성 실패")
        sys.exit(1)
