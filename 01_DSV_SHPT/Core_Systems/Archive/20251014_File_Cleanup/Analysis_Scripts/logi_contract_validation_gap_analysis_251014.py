#!/usr/bin/env python3
"""
Contract Validation Gap Analysis Report Generator
Enhanced vs SHPT 시스템의 Contract 검증 로직 비교 분석 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContractValidationGapAnalyzer:
    """Contract 검증 로직 Gap 분석기"""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.analysis_result = {}

    def analyze_enhanced_system_implementation(self) -> Dict[str, Any]:
        """Enhanced 시스템의 Contract 검증 구현 분석"""

        enhanced_analysis = {
            "system_name": "SHPTSept2025EnhancedAuditSystem",
            "file": "shpt_sept_2025_enhanced_audit.py",
            "contract_detection": {
                "method": "String matching in rate_source",
                "condition": 'elif "CONTRACT" in rate_source_upper:',
                "line_number": 457,
                "implementation_level": "BASIC",
            },
            "ref_rate_lookup": {
                "method": "_find_contract_ref_rate(item)",
                "line_number": 461,
                "implementation_status": "IMPLEMENTED",
                "completeness": "PARTIAL",
            },
            "delta_calculation": {
                "method": "rate_loader.calculate_delta_percent()",
                "line_number": "466-468",
                "implementation_status": "IMPLEMENTED",
                "completeness": "COMPLETE",
            },
            "cost_guard_integration": {
                "method": "rate_loader.get_cost_guard_band()",
                "line_number": "472-473",
                "implementation_status": "IMPLEMENTED",
                "completeness": "COMPLETE",
            },
            "validation_logic": {
                "condition": "abs(delta_pct) > 5.0",
                "line_number": 476,
                "threshold": "5% (WARN threshold)",
                "status_update": "FAIL for HIGH/CRITICAL",
                "implementation_level": "ADVANCED",
            },
            "limitations": [
                "ref_rate 조회 로직이 미완성 상태",
                "Lane Map 기반 조회만 가능",
                "Contract-specific 로직 부족",
                "Description 파싱 로직 없음",
            ],
            "estimated_completion": "60%",
        }

        return enhanced_analysis

    def analyze_shpt_system_implementation(self) -> Dict[str, Any]:
        """SHPT 시스템의 Contract 검증 구현 분석"""

        shpt_analysis = {
            "system_name": "SHPTAuditSystem",
            "file": "shpt_audit_system.py",
            "contract_detection": {
                "method": "Category-based classification",
                "implementation_level": "COMPLETE",
            },
            "ref_rate_lookup": {
                "method": "get_standard_rate(category, port, destination, unit)",
                "line_number": 368,
                "implementation_status": "FULLY_IMPLEMENTED",
                "completeness": "COMPLETE",
                "features": [
                    "Lane Map 기반 조회",
                    "Port/Destination 파싱",
                    "Category 정규화",
                    "Unit 기반 매칭",
                ],
            },
            "lane_map_coverage": {
                "sea_transport": {
                    "KP_DSV_YD": 252.00,
                    "DSV_YD_MIRFA": 420.00,
                    "DSV_YD_SHUWEIHAT": 600.00,
                    "MOSB_DSV_YD": 200.00,
                },
                "air_transport": {"AUH_DSV_MUSSAFAH": 100.00},
                "total_lanes": 5,
            },
            "delta_calculation": {
                "method": "calculate_delta_percent(draft_rate, standard_rate)",
                "line_number": "386-390",
                "implementation_status": "FULLY_IMPLEMENTED",
                "completeness": "COMPLETE",
            },
            "cost_guard_bands": {
                "PASS": "≤2.00%",
                "WARN": "2.01-5.00%",
                "HIGH": "5.01-10.00%",
                "CRITICAL": ">10.00%",
            },
            "validation_completeness": {
                "data_normalization": "COMPLETE",
                "ref_rate_lookup": "COMPLETE",
                "delta_calculation": "COMPLETE",
                "cost_guard_integration": "COMPLETE",
                "result_formatting": "COMPLETE",
            },
            "estimated_completion": "100%",
        }

        return shpt_analysis

    def analyze_actual_results(self) -> Dict[str, Any]:
        """실제 9월 2025 인보이스 검증 결과 분석"""

        # CSV 결과 파일 찾기
        results_dir = self.root / "Results" / "Sept_2025" / "CSV"
        csv_files = list(results_dir.glob("shpt_sept_2025_enhanced_result_*.csv"))

        if not csv_files:
            logger.warning("No CSV result files found")
            return {"error": "No result files available"}

        # 최신 파일 사용
        latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Analyzing results from: {latest_csv.name}")

        try:
            df = pd.read_csv(latest_csv)

            # Contract 항목 분석
            contract_items = df[df["charge_group"] == "Contract"]

            # ref_rate 상태 분석
            ref_rate_analysis = {
                "total_contract_items": len(contract_items),
                "items_with_ref_rate": len(
                    contract_items[contract_items["ref_rate_usd"].notna()]
                ),
                "items_without_ref_rate": len(
                    contract_items[contract_items["ref_rate_usd"].isna()]
                ),
                "ref_rate_coverage": 0.0,
                "validation_effectiveness": "INCOMPLETE",
            }

            if len(contract_items) > 0:
                ref_rate_analysis["ref_rate_coverage"] = (
                    ref_rate_analysis["items_with_ref_rate"]
                    / ref_rate_analysis["total_contract_items"]
                    * 100
                )

            # Delta 분석 (ref_rate가 있는 항목만)
            validated_items = contract_items[contract_items["ref_rate_usd"].notna()]

            delta_analysis = {
                "validated_count": len(validated_items),
                "avg_delta": (
                    float(validated_items["delta_pct"].mean())
                    if len(validated_items) > 0
                    else 0.0
                ),
                "max_delta": (
                    float(validated_items["delta_pct"].max())
                    if len(validated_items) > 0
                    else 0.0
                ),
                "min_delta": (
                    float(validated_items["delta_pct"].min())
                    if len(validated_items) > 0
                    else 0.0
                ),
                "cost_guard_distribution": {},
            }

            if len(validated_items) > 0:
                cg_counts = validated_items["cg_band"].value_counts().to_dict()
                delta_analysis["cost_guard_distribution"] = cg_counts

            # 항목별 상세 분석
            contract_details = []
            for _, row in contract_items.head(10).iterrows():  # 상위 10개만
                contract_details.append(
                    {
                        "s_no": row["s_no"],
                        "description": row["description"],
                        "unit_rate": float(row["unit_rate"]),
                        "ref_rate_usd": (
                            float(row["ref_rate_usd"])
                            if pd.notna(row["ref_rate_usd"])
                            else None
                        ),
                        "delta_pct": (
                            float(row["delta_pct"])
                            if pd.notna(row["delta_pct"])
                            else None
                        ),
                        "validation_status": (
                            "COMPLETE"
                            if pd.notna(row["ref_rate_usd"])
                            else "INCOMPLETE"
                        ),
                    }
                )

            return {
                "source_file": latest_csv.name,
                "ref_rate_analysis": ref_rate_analysis,
                "delta_analysis": delta_analysis,
                "contract_details": contract_details,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {"error": str(e)}

    def identify_gaps_and_improvements(
        self, enhanced_impl: Dict, shpt_impl: Dict, results: Dict
    ) -> Dict[str, Any]:
        """Gap 식별 및 개선 방안 도출"""

        gaps = {
            "critical_gaps": [
                {
                    "category": "ref_rate_lookup_incomplete",
                    "description": "Enhanced 시스템의 _find_contract_ref_rate() 메서드가 미완성",
                    "impact": "64개 Contract 항목 중 대부분이 검증되지 않음",
                    "evidence": f"ref_rate coverage: {results.get('ref_rate_analysis', {}).get('ref_rate_coverage', 0):.1f}%",
                    "severity": "HIGH",
                },
                {
                    "category": "lane_map_integration_missing",
                    "description": "SHPT 시스템의 Lane Map이 Enhanced 시스템에 통합되지 않음",
                    "impact": "표준 운송 요율 조회 불가",
                    "evidence": "SHPT has 5 lanes, Enhanced has incomplete lane integration",
                    "severity": "CRITICAL",
                },
                {
                    "category": "description_parsing_absent",
                    "description": "Description에서 Port/Destination 추출 로직 부재",
                    "impact": "Lane 매칭을 위한 핵심 정보 추출 불가",
                    "evidence": "No port/destination parsing in Enhanced system",
                    "severity": "HIGH",
                },
            ],
            "implementation_gaps": [
                {
                    "component": "Contract Detection",
                    "enhanced_status": enhanced_impl["contract_detection"][
                        "implementation_level"
                    ],
                    "shpt_status": "COMPLETE",
                    "gap_level": "MINOR",
                },
                {
                    "component": "Ref Rate Lookup",
                    "enhanced_status": enhanced_impl["ref_rate_lookup"]["completeness"],
                    "shpt_status": "COMPLETE",
                    "gap_level": "MAJOR",
                },
                {
                    "component": "Delta Calculation",
                    "enhanced_status": enhanced_impl["delta_calculation"][
                        "completeness"
                    ],
                    "shpt_status": "COMPLETE",
                    "gap_level": "NONE",
                },
                {
                    "component": "Cost Guard Integration",
                    "enhanced_status": enhanced_impl["cost_guard_integration"][
                        "completeness"
                    ],
                    "shpt_status": "COMPLETE",
                    "gap_level": "NONE",
                },
            ],
        }

        improvements = {
            "immediate_actions": [
                {
                    "priority": 1,
                    "action": "Integrate SHPT Lane Map to Enhanced System",
                    "description": "Copy lane_map dictionary from SHPT to Enhanced system",
                    "file_changes": ["shpt_sept_2025_enhanced_audit.py"],
                    "estimated_effort": "2 hours",
                    "impact": "Enable standard rate lookup for 5 main transport lanes",
                },
                {
                    "priority": 2,
                    "action": "Implement Description Parsing Logic",
                    "description": "Add port/destination extraction from description text",
                    "file_changes": ["shpt_sept_2025_enhanced_audit.py"],
                    "estimated_effort": "4 hours",
                    "impact": "Enable automatic lane matching for contract items",
                },
                {
                    "priority": 3,
                    "action": "Complete _find_contract_ref_rate() Method",
                    "description": "Implement complete contract reference rate lookup",
                    "file_changes": ["shpt_sept_2025_enhanced_audit.py"],
                    "estimated_effort": "6 hours",
                    "impact": "Achieve 90%+ contract validation coverage",
                },
            ],
            "architectural_improvements": [
                {
                    "improvement": "Unified Rate Lookup Service",
                    "description": "Extract common rate lookup logic to shared service",
                    "benefits": ["Code reuse", "Consistency", "Maintainability"],
                    "estimated_effort": "1 week",
                },
                {
                    "improvement": "Configuration Externalization",
                    "description": "Move lane maps and contract rates to JSON config files",
                    "benefits": [
                        "Easy updates",
                        "Version control",
                        "Environment-specific rates",
                    ],
                    "estimated_effort": "3 days",
                },
            ],
            "expected_outcomes": {
                "contract_validation_coverage": "90%+",
                "processing_performance": "No impact (same algorithms)",
                "system_reliability": "Significantly improved",
                "audit_effectiveness": "Complete contract validation",
            },
        }

        return {"gaps": gaps, "improvements": improvements}

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """종합 분석 보고서 생성"""

        logger.info("Analyzing Enhanced system implementation...")
        enhanced_impl = self.analyze_enhanced_system_implementation()

        logger.info("Analyzing SHPT system implementation...")
        shpt_impl = self.analyze_shpt_system_implementation()

        logger.info("Analyzing actual validation results...")
        results = self.analyze_actual_results()

        logger.info("Identifying gaps and improvements...")
        gap_analysis = self.identify_gaps_and_improvements(
            enhanced_impl, shpt_impl, results
        )

        report = {
            "report_metadata": {
                "title": "Contract Validation Gap Analysis Report",
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "scope": "Enhanced vs SHPT Contract Validation Logic Comparison",
            },
            "executive_summary": {
                "current_status": "INCOMPLETE - Enhanced system has partial Contract validation",
                "key_findings": [
                    f"Enhanced system completion: {enhanced_impl['estimated_completion']}",
                    f"SHPT system completion: {shpt_impl['estimated_completion']}",
                    f"Contract validation coverage: {results.get('ref_rate_analysis', {}).get('ref_rate_coverage', 0):.1f}%",
                    f"Critical gaps identified: {len(gap_analysis['gaps']['critical_gaps'])}",
                ],
                "recommendation": "Immediate integration of SHPT validation logic into Enhanced system",
            },
            "system_implementations": {
                "enhanced_system": enhanced_impl,
                "shpt_system": shpt_impl,
            },
            "validation_results": results,
            "gap_analysis": gap_analysis,
            "technical_specifications": {
                "contract_items_sept_2025": results.get("ref_rate_analysis", {}).get(
                    "total_contract_items", 0
                ),
                "validated_items": results.get("ref_rate_analysis", {}).get(
                    "items_with_ref_rate", 0
                ),
                "validation_rate": f"{results.get('ref_rate_analysis', {}).get('ref_rate_coverage', 0):.1f}%",
                "lane_coverage": {
                    "shpt_system": len(shpt_impl["lane_map_coverage"]["sea_transport"])
                    + len(shpt_impl["lane_map_coverage"]["air_transport"]),
                    "enhanced_system": 0,  # No lane map integration found
                },
            },
        }

        return report

    def save_report(self, output_dir: str = "out") -> str:
        """분석 보고서 저장"""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 종합 보고서 생성
        report = self.generate_comprehensive_report()

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"contract_validation_gap_analysis_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Excel 저장 (상세 데이터)
        excel_path = output_path / f"contract_validation_comparison_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # Gap Summary
            gap_summary = []
            for gap in report["gap_analysis"]["gaps"]["critical_gaps"]:
                gap_summary.append(
                    {
                        "Category": gap["category"],
                        "Description": gap["description"],
                        "Impact": gap["impact"],
                        "Severity": gap["severity"],
                        "Evidence": gap["evidence"],
                    }
                )

            gap_df = pd.DataFrame(gap_summary)
            gap_df.to_excel(writer, sheet_name="Critical_Gaps", index=False)

            # Implementation Comparison
            impl_comparison = []
            for impl in report["gap_analysis"]["gaps"]["implementation_gaps"]:
                impl_comparison.append(
                    {
                        "Component": impl["component"],
                        "Enhanced_Status": impl["enhanced_status"],
                        "SHPT_Status": impl["shpt_status"],
                        "Gap_Level": impl["gap_level"],
                    }
                )

            impl_df = pd.DataFrame(impl_comparison)
            impl_df.to_excel(
                writer, sheet_name="Implementation_Comparison", index=False
            )

            # Improvement Actions
            actions = []
            for action in report["gap_analysis"]["improvements"]["immediate_actions"]:
                actions.append(
                    {
                        "Priority": action["priority"],
                        "Action": action["action"],
                        "Description": action["description"],
                        "Estimated_Effort": action["estimated_effort"],
                        "Impact": action["impact"],
                    }
                )

            actions_df = pd.DataFrame(actions)
            actions_df.to_excel(writer, sheet_name="Improvement_Actions", index=False)

            # Contract Details (if available)
            if "contract_details" in report["validation_results"]:
                details_df = pd.DataFrame(
                    report["validation_results"]["contract_details"]
                )
                details_df.to_excel(
                    writer, sheet_name="Contract_Sample_Analysis", index=False
                )

        logger.info(f"Contract validation gap analysis completed:")
        logger.info(f"  JSON Report: {json_path}")
        logger.info(f"  Excel Details: {excel_path}")

        return str(json_path)


def main():
    """메인 실행 함수"""

    analyzer = ContractValidationGapAnalyzer()
    report_path = analyzer.save_report()

    # 결과 요약 출력
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("\n" + "=" * 80)
    print("Contract Validation Gap Analysis 완료")
    print("=" * 80)

    summary = report["executive_summary"]
    print(f"\n현재 상태: {summary['current_status']}")
    print(f"\n주요 발견사항:")
    for finding in summary["key_findings"]:
        print(f"  • {finding}")

    print(f"\n권장사항: {summary['recommendation']}")

    # 중요 Gap 출력
    critical_gaps = report["gap_analysis"]["gaps"]["critical_gaps"]
    print(f"\n중요 Gap ({len(critical_gaps)}개):")
    for gap in critical_gaps:
        print(f"  {gap['severity']}: {gap['description']}")

    # 즉시 개선 액션
    actions = report["gap_analysis"]["improvements"]["immediate_actions"]
    print(f"\n즉시 개선 액션 (우선순위 순):")
    for action in actions:
        print(
            f"  {action['priority']}. {action['action']} ({action['estimated_effort']})"
        )

    print(f"\n상세 보고서: {report_path}")

    return report


if __name__ == "__main__":
    main()
