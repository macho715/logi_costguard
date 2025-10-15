#!/usr/bin/env python3
"""
시스템 재사용성 점검: 하드코딩 항목 식별
"""

import re
import ast
from pathlib import Path
from collections import defaultdict
import json


class HardcodingAnalyzer:
    """하드코딩된 값 식별 및 분석"""

    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.hardcoded_items = defaultdict(list)

    def analyze_file(self, file_path: Path):
        """단일 파일 분석"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # String literals
            self._find_string_literals(file_path, content)

            # Magic numbers
            self._find_magic_numbers(file_path, content)

            # Hardcoded paths
            self._find_hardcoded_paths(file_path, content)

            # Sheet names
            self._find_sheet_names(file_path, content)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _find_string_literals(self, file_path: Path, content: str):
        """문자열 리터럴 찾기"""

        # Port names
        port_patterns = [
            r'"(Khalifa Port|Jebel Ali Port|Abu Dhabi Airport|Dubai Airport|Mina Zayed|Musaffah Port)"',
            r"'(Khalifa Port|Jebel Ali Port|Abu Dhabi Airport|Dubai Airport|Mina Zayed|Musaffah Port)'",
        ]

        for pattern in port_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.hardcoded_items["ports"].append(
                    {
                        "file": str(file_path.relative_to(self.root)),
                        "value": match,
                        "type": "port_name",
                    }
                )

        # Destination names
        dest_patterns = [
            r'"(MIRFA|SHUWEIHAT|Storage Yard|DSV Mussafah|Hamariya)"',
            r"'(MIRFA|SHUWEIHAT|Storage Yard|DSV Mussafah|Hamariya)'",
        ]

        for pattern in dest_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.hardcoded_items["destinations"].append(
                    {
                        "file": str(file_path.relative_to(self.root)),
                        "value": match,
                        "type": "destination_name",
                    }
                )

        # Column names
        col_patterns = [
            r'"(Order Ref\. Number|DESCRIPTION|RATE SOURCE|CHARGE GROUP)"',
            r"'(Order Ref\. Number|DESCRIPTION|RATE SOURCE|CHARGE GROUP)'",
        ]

        for pattern in col_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.hardcoded_items["columns"].append(
                    {
                        "file": str(file_path.relative_to(self.root)),
                        "value": match,
                        "type": "column_name",
                    }
                )

    def _find_magic_numbers(self, file_path: Path, content: str):
        """Magic numbers 찾기"""

        # Common thresholds
        patterns = [
            (r"\b(0\.9[0-9]|0\.8[0-9]|0\.7[0-9])\b", "threshold"),
            (r"\b(252\.0|150\.0|100\.0)\b", "rate"),
            (r"\b(3\.6725)\b", "fx_rate"),
            (r"\b(4\.0)\b(?!.*tolerance)", "pressure_limit"),
        ]

        for pattern, number_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.hardcoded_items["magic_numbers"].append(
                    {
                        "file": str(file_path.relative_to(self.root)),
                        "value": match,
                        "type": number_type,
                    }
                )

    def _find_hardcoded_paths(self, file_path: Path, content: str):
        """하드코딩된 경로 찾기"""

        patterns = [
            r'"([A-Z]:\\[^"]+)"',
            r"'([A-Z]:\\[^']+)'",
            r'"(\/[^"]+\/[^"]+)"',
            r"'(\/[^']+\/[^']+)'",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if "Users" in match or "Downloads" in match:
                    self.hardcoded_items["paths"].append(
                        {
                            "file": str(file_path.relative_to(self.root)),
                            "value": match,
                            "type": "absolute_path",
                        }
                    )

    def _find_sheet_names(self, file_path: Path, content: str):
        """하드코딩된 시트명 찾기"""

        patterns = [
            r'sheet_name\s*=\s*["\']([^"\']+)["\']',
            r'read_excel\([^,]+,\s*sheet_name\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in ["Sheet1", "Sheet2"]:
                    self.hardcoded_items["sheet_names"].append(
                        {
                            "file": str(file_path.relative_to(self.root)),
                            "value": match,
                            "type": "sheet_name",
                        }
                    )

    def analyze_directory(self, target_dir: Path):
        """디렉토리 내 모든 Python 파일 분석"""

        py_files = list(target_dir.rglob("*.py"))

        print(f"Analyzing {len(py_files)} Python files in {target_dir.name}...")

        for py_file in py_files:
            # Skip test files and temporary files
            if any(
                x in str(py_file) for x in ["test_", "__pycache__", ".pyc", "debug_"]
            ):
                continue

            self.analyze_file(py_file)

        return self.hardcoded_items

    def generate_report(self) -> dict:
        """분석 결과 보고서 생성"""

        report = {"summary": {}, "details": self.hardcoded_items, "recommendations": []}

        # Summary statistics
        for category, items in self.hardcoded_items.items():
            report["summary"][category] = {
                "count": len(items),
                "unique_values": len(set(item["value"] for item in items)),
            }

        # Recommendations
        if report["summary"].get("ports", {}).get("count", 0) > 0:
            report["recommendations"].append(
                {
                    "priority": "HIGH",
                    "category": "ports",
                    "action": "Move port names to config_normalization_aliases.json",
                    "benefit": "Easier to add new ports without code changes",
                }
            )

        if report["summary"].get("magic_numbers", {}).get("count", 0) > 0:
            report["recommendations"].append(
                {
                    "priority": "HIGH",
                    "category": "magic_numbers",
                    "action": "Extract magic numbers to constants or config files",
                    "benefit": "Improved maintainability and clarity",
                }
            )

        if report["summary"].get("sheet_names", {}).get("count", 0) > 0:
            report["recommendations"].append(
                {
                    "priority": "MEDIUM",
                    "category": "sheet_names",
                    "action": "Create excel_schema.json with flexible sheet name mapping",
                    "benefit": "Support different Excel templates",
                }
            )

        if report["summary"].get("paths", {}).get("count", 0) > 0:
            report["recommendations"].append(
                {
                    "priority": "CRITICAL",
                    "category": "paths",
                    "action": "Replace absolute paths with relative paths or Path objects",
                    "benefit": "Portability across different environments",
                }
            )

        return report


# Main execution
if __name__ == "__main__":
    root = Path(__file__).parent
    analyzer = HardcodingAnalyzer(root)

    print("=" * 100)
    print("시스템 재사용성 점검: 하드코딩 항목 분석")
    print("=" * 100)

    # Analyze Core_Systems directory
    core_dir = root
    results = analyzer.analyze_directory(core_dir)

    # Analyze 00_Shared if exists
    shared_dir = root.parent.parent / "00_Shared"
    if shared_dir.exists():
        print(f"\nAnalyzing shared directory...")
        analyzer.analyze_directory(shared_dir)

    # Generate report
    report = analyzer.generate_report()

    print("\n" + "=" * 100)
    print("분석 결과 요약")
    print("=" * 100)

    for category, stats in report["summary"].items():
        print(f"\n{category.upper()}:")
        print(f"  총 발견: {stats['count']}개")
        print(f"  고유 값: {stats['unique_values']}개")

    print("\n" + "=" * 100)
    print("개선 권장사항")
    print("=" * 100)

    for rec in report["recommendations"]:
        print(f"\n[{rec['priority']}] {rec['category']}")
        print(f"  조치: {rec['action']}")
        print(f"  효과: {rec['benefit']}")

    # Save to JSON
    output_file = root / "hardcoding_analysis_report_251014.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n" + "=" * 100)
    print(f"[SAVED] {output_file}")
    print("=" * 100)

    # Calculate reusability score
    total_hardcoded = sum(stats["count"] for stats in report["summary"].values())
    critical_count = len(
        [r for r in report["recommendations"] if r["priority"] in ["CRITICAL", "HIGH"]]
    )

    # Simple scoring: 100 - (hardcoded_count * 0.5) - (critical_issues * 5)
    reusability_score = max(0, 100 - (total_hardcoded * 0.5) - (critical_count * 5))

    print(f"\n재사용성 점수: {reusability_score:.1f}/100")

    if reusability_score >= 80:
        print("평가: 우수 - 재사용성이 높습니다")
    elif reusability_score >= 60:
        print("평가: 양호 - 일부 개선이 필요합니다")
    elif reusability_score >= 40:
        print("평가: 보통 - 상당한 개선이 필요합니다")
    else:
        print("평가: 미흡 - 대대적인 리팩토링이 필요합니다")
