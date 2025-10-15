#!/usr/bin/env python3
"""
DSV SHPT Code Quality Auditor
순환 복잡도, 중복 코드, 테스트 커버리지 등 코드 품질 메트릭 분석 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import ast
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import hashlib
import re
from collections import defaultdict, Counter
import difflib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LogiCodeQualityAuditor:
    """DSV SHPT 코드 품질 감사기"""

    def __init__(self, core_systems_path: str):
        self.core_systems_path = Path(core_systems_path)
        self.python_files = [
            f
            for f in self.core_systems_path.glob("*.py")
            if not f.name.startswith("__")
        ]

        # 품질 메트릭 저장
        self.quality_metrics = {}
        self.complexity_data = {}
        self.duplication_analysis = {}
        self.test_coverage_analysis = {}

        # 품질 기준점
        self.quality_thresholds = {
            "cyclomatic_complexity": {"good": 5, "acceptable": 10, "poor": 15},
            "function_length": {"good": 20, "acceptable": 50, "poor": 100},
            "file_length": {"good": 300, "acceptable": 500, "poor": 1000},
            "duplicate_threshold": 5,  # 5줄 이상 중복 시 문제
            "test_coverage_target": 80,  # 80% 이상 목표
        }

    def calculate_cyclomatic_complexity(self, node) -> int:
        """순환 복잡도 계산 (McCabe)"""
        complexity = 1  # 기본 복잡도

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def analyze_function_complexity(self, file_path: Path) -> List[Dict[str, Any]]:
        """함수별 순환 복잡도 분석"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self.calculate_cyclomatic_complexity(node)
                    function_lines = (
                        node.end_lineno - node.lineno
                        if hasattr(node, "end_lineno")
                        else 0
                    )

                    # 함수 내 코드 라인 수 계산
                    function_content = content.split("\n")[
                        node.lineno - 1 : getattr(node, "end_lineno", node.lineno)
                    ]
                    code_lines = len(
                        [
                            line
                            for line in function_content
                            if line.strip() and not line.strip().startswith("#")
                        ]
                    )

                    functions.append(
                        {
                            "name": node.name,
                            "line_start": node.lineno,
                            "line_end": getattr(node, "end_lineno", node.lineno),
                            "total_lines": function_lines,
                            "code_lines": code_lines,
                            "cyclomatic_complexity": complexity,
                            "quality_rating": self._get_complexity_rating(complexity),
                            "args_count": len(node.args.args),
                            "returns_count": len(
                                [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                            ),
                        }
                    )

            return functions

        except Exception as e:
            logger.error(f"Error analyzing complexity in {file_path}: {e}")
            return []

    def _get_complexity_rating(self, complexity: int) -> str:
        """복잡도 등급 결정"""
        thresholds = self.quality_thresholds["cyclomatic_complexity"]
        if complexity <= thresholds["good"]:
            return "GOOD"
        elif complexity <= thresholds["acceptable"]:
            return "ACCEPTABLE"
        elif complexity <= thresholds["poor"]:
            return "POOR"
        else:
            return "CRITICAL"

    def detect_code_duplication(self) -> Dict[str, Any]:
        """코드 중복 탐지"""

        duplications = []
        file_hashes = {}

        # 모든 파일의 함수와 코드 블록 분석
        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                file_hashes[str(file_path)] = []

                # 5줄 이상의 연속 코드 블록을 해시화
                for i in range(len(lines) - 4):  # 최소 5줄
                    block = lines[i : i + 5]
                    # 공백과 주석 제거 후 정규화
                    normalized_block = [
                        re.sub(r"\s+", " ", line.strip())
                        for line in block
                        if line.strip() and not line.strip().startswith("#")
                    ]

                    if len(normalized_block) >= 3:  # 유의미한 코드가 3줄 이상
                        block_hash = hashlib.md5(
                            "".join(normalized_block).encode()
                        ).hexdigest()
                        file_hashes[str(file_path)].append(
                            {
                                "hash": block_hash,
                                "start_line": i + 1,
                                "end_line": i + 5,
                                "content": normalized_block,
                            }
                        )

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        # 중복 블록 찾기
        hash_locations = defaultdict(list)
        for file_path, blocks in file_hashes.items():
            for block in blocks:
                hash_locations[block["hash"]].append(
                    {
                        "file": file_path,
                        "start_line": block["start_line"],
                        "end_line": block["end_line"],
                        "content": block["content"],
                    }
                )

        # 중복된 블록들 (2개 파일 이상에서 발견)
        for block_hash, locations in hash_locations.items():
            if len(locations) > 1:
                duplications.append(
                    {
                        "hash": block_hash,
                        "duplicate_count": len(locations),
                        "locations": locations,
                        "severity": "HIGH" if len(locations) > 2 else "MEDIUM",
                    }
                )

        return {
            "total_duplicates": len(duplications),
            "duplicate_blocks": duplications,
            "analysis_summary": {
                "files_analyzed": len(self.python_files),
                "total_code_blocks_checked": sum(
                    len(blocks) for blocks in file_hashes.values()
                ),
                "duplication_ratio": len(duplications)
                / max(1, sum(len(blocks) for blocks in file_hashes.values()))
                * 100,
            },
        }

    def analyze_test_coverage(self) -> Dict[str, Any]:
        """테스트 커버리지 분석"""

        # 테스트 파일과 프로덕션 파일 분리
        test_files = [f for f in self.python_files if "test_" in f.name]
        production_files = [
            f
            for f in self.python_files
            if "test_" not in f.name and not f.name.endswith("_test.py")
        ]

        # 프로덕션 함수 추출
        production_functions = {}
        for file_path in production_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                functions = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith(
                        "_"
                    ):
                        functions.append(node.name)

                if functions:
                    production_functions[file_path.name] = functions

            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")

        # 테스트 함수 추출
        test_functions = {}
        tested_functions = set()

        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                tests = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and (
                        node.name.startswith("test_") or "test" in node.name.lower()
                    ):
                        tests.append(node.name)

                        # 테스트하는 함수명 추측
                        for prod_file, prod_funcs in production_functions.items():
                            for func in prod_funcs:
                                if (
                                    func.lower() in node.name.lower()
                                    or node.name.lower()
                                    .replace("test_", "")
                                    .replace("_", "")
                                    in func.lower().replace("_", "")
                                ):
                                    tested_functions.add(func)

                if tests:
                    test_functions[test_file.name] = tests

            except Exception as e:
                logger.error(f"Error parsing {test_file}: {e}")

        # 커버리지 계산
        total_production_functions = sum(
            len(funcs) for funcs in production_functions.values()
        )
        covered_functions = len(tested_functions)
        coverage_percentage = (
            covered_functions / max(1, total_production_functions)
        ) * 100

        # 미테스트 함수 식별
        untested_functions = []
        for file_name, functions in production_functions.items():
            for func in functions:
                if func not in tested_functions:
                    untested_functions.append(
                        {
                            "file": file_name,
                            "function": func,
                            "risk_level": (
                                "HIGH"
                                if any(
                                    keyword in func.lower()
                                    for keyword in ["validate", "process", "calculate"]
                                )
                                else "MEDIUM"
                            ),
                        }
                    )

        return {
            "coverage_summary": {
                "test_files_count": len(test_files),
                "production_files_count": len(production_files),
                "total_production_functions": total_production_functions,
                "covered_functions": covered_functions,
                "coverage_percentage": round(coverage_percentage, 1),
                "coverage_rating": self._get_coverage_rating(coverage_percentage),
            },
            "test_details": {
                "test_functions": test_functions,
                "production_functions": production_functions,
                "tested_functions": list(tested_functions),
            },
            "untested_functions": untested_functions,
            "recommendations": self._generate_test_recommendations(
                untested_functions, coverage_percentage
            ),
        }

    def _get_coverage_rating(self, coverage: float) -> str:
        """테스트 커버리지 등급"""
        if coverage >= 90:
            return "EXCELLENT"
        elif coverage >= 80:
            return "GOOD"
        elif coverage >= 60:
            return "ACCEPTABLE"
        elif coverage >= 40:
            return "POOR"
        else:
            return "CRITICAL"

    def _generate_test_recommendations(
        self, untested_functions: List[Dict], coverage: float
    ) -> List[str]:
        """테스트 권장사항 생성"""
        recommendations = []

        if coverage < 80:
            recommendations.append(
                f"테스트 커버리지가 {coverage:.1f}%로 목표 80% 미달. 추가 테스트 작성 필요"
            )

        high_risk_untested = [
            f for f in untested_functions if f["risk_level"] == "HIGH"
        ]
        if high_risk_untested:
            recommendations.append(
                f"고위험 미테스트 함수 {len(high_risk_untested)}개 우선 테스트 작성"
            )

        if len(untested_functions) > 20:
            recommendations.append(
                "미테스트 함수가 20개 초과. 체계적인 테스트 작성 계획 수립 필요"
            )

        return recommendations

    def analyze_code_smells(self) -> Dict[str, Any]:
        """코드 냄새 탐지"""

        smells = []

        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()

                # 파일 길이 체크
                if len(lines) > self.quality_thresholds["file_length"]["poor"]:
                    smells.append(
                        {
                            "type": "LARGE_FILE",
                            "file": file_path.name,
                            "severity": "HIGH",
                            "description": f'파일이 {len(lines)}줄로 너무 김 (권장: <{self.quality_thresholds["file_length"]["acceptable"]}줄)',
                            "line": None,
                        }
                    )

                # AST 분석
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    # 긴 함수 체크
                    if isinstance(node, ast.FunctionDef):
                        func_lines = (
                            getattr(node, "end_lineno", node.lineno) - node.lineno
                        )
                        if (
                            func_lines
                            > self.quality_thresholds["function_length"]["poor"]
                        ):
                            smells.append(
                                {
                                    "type": "LONG_FUNCTION",
                                    "file": file_path.name,
                                    "severity": "MEDIUM",
                                    "description": f"함수 {node.name}이 {func_lines}줄로 너무 김",
                                    "line": node.lineno,
                                    "function": node.name,
                                }
                            )

                        # 매개변수 과다 체크
                        if len(node.args.args) > 7:
                            smells.append(
                                {
                                    "type": "TOO_MANY_PARAMETERS",
                                    "file": file_path.name,
                                    "severity": "MEDIUM",
                                    "description": f"함수 {node.name}의 매개변수가 {len(node.args.args)}개로 과다",
                                    "line": node.lineno,
                                    "function": node.name,
                                }
                            )

                    # 깊은 중첩 체크
                    if isinstance(node, (ast.If, ast.For, ast.While)):
                        nesting_level = self._calculate_nesting_level(node)
                        if nesting_level > 4:
                            smells.append(
                                {
                                    "type": "DEEP_NESTING",
                                    "file": file_path.name,
                                    "severity": "MEDIUM",
                                    "description": f"{nesting_level}단계 중첩으로 가독성 저하",
                                    "line": node.lineno,
                                }
                            )

                # 코멘트 밀도 체크
                comment_lines = len(
                    [line for line in lines if line.strip().startswith("#")]
                )
                code_lines = len(
                    [
                        line
                        for line in lines
                        if line.strip() and not line.strip().startswith("#")
                    ]
                )

                if code_lines > 0:
                    comment_ratio = comment_lines / code_lines
                    if comment_ratio < 0.1:  # 코멘트가 10% 미만
                        smells.append(
                            {
                                "type": "INSUFFICIENT_COMMENTS",
                                "file": file_path.name,
                                "severity": "LOW",
                                "description": f"코멘트 비율이 {comment_ratio:.1%}로 부족",
                                "line": None,
                            }
                        )

            except Exception as e:
                logger.error(f"Error analyzing code smells in {file_path}: {e}")

        # 심각도별 분류
        severity_counts = Counter(smell["severity"] for smell in smells)

        return {
            "total_smells": len(smells),
            "severity_distribution": dict(severity_counts),
            "smells_by_type": Counter(smell["type"] for smell in smells),
            "detailed_smells": smells,
            "quality_score": self._calculate_quality_score(smells),
        }

    def _calculate_nesting_level(self, node, level=0) -> int:
        """중첩 레벨 계산"""
        max_level = level
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_level = self._calculate_nesting_level(child, level + 1)
                max_level = max(max_level, child_level)
        return max_level

    def _calculate_quality_score(self, smells: List[Dict]) -> float:
        """전체 품질 점수 계산 (100점 만점)"""
        base_score = 100

        for smell in smells:
            if smell["severity"] == "CRITICAL":
                base_score -= 10
            elif smell["severity"] == "HIGH":
                base_score -= 5
            elif smell["severity"] == "MEDIUM":
                base_score -= 3
            elif smell["severity"] == "LOW":
                base_score -= 1

        return max(0, base_score)

    def generate_comprehensive_quality_report(self) -> Dict[str, Any]:
        """종합 코드 품질 보고서 생성"""

        logger.info("Analyzing cyclomatic complexity...")
        complexity_analysis = {}
        total_functions = 0
        complexity_distribution = {"GOOD": 0, "ACCEPTABLE": 0, "POOR": 0, "CRITICAL": 0}

        for file_path in self.python_files:
            functions = self.analyze_function_complexity(file_path)
            complexity_analysis[file_path.name] = functions
            total_functions += len(functions)

            for func in functions:
                complexity_distribution[func["quality_rating"]] += 1

        logger.info("Detecting code duplication...")
        duplication_analysis = self.detect_code_duplication()

        logger.info("Analyzing test coverage...")
        test_coverage = self.analyze_test_coverage()

        logger.info("Detecting code smells...")
        code_smells = self.analyze_code_smells()

        # 전체 품질 등급 계산
        overall_quality = self._calculate_overall_quality(
            complexity_distribution,
            test_coverage["coverage_summary"]["coverage_percentage"],
            code_smells["quality_score"],
        )

        report = {
            "report_metadata": {
                "title": "DSV SHPT Code Quality Audit Report",
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
                "scope": "Comprehensive code quality analysis",
            },
            "executive_summary": {
                "overall_quality_grade": overall_quality["grade"],
                "overall_quality_score": overall_quality["score"],
                "files_analyzed": len(self.python_files),
                "total_functions": total_functions,
                "key_metrics": {
                    "average_complexity": sum(
                        func["cyclomatic_complexity"]
                        for functions in complexity_analysis.values()
                        for func in functions
                    )
                    / max(1, total_functions),
                    "test_coverage_percentage": test_coverage["coverage_summary"][
                        "coverage_percentage"
                    ],
                    "code_duplications": duplication_analysis["total_duplicates"],
                    "code_smells": code_smells["total_smells"],
                },
                "critical_issues": [
                    f"High complexity functions: {complexity_distribution['CRITICAL'] + complexity_distribution['POOR']}",
                    f"Test coverage: {test_coverage['coverage_summary']['coverage_percentage']:.1f}%",
                    f"Code duplications: {duplication_analysis['total_duplicates']}",
                    f"High severity code smells: {code_smells['severity_distribution'].get('HIGH', 0)}",
                ],
            },
            "complexity_analysis": {
                "distribution": complexity_distribution,
                "detailed_functions": complexity_analysis,
                "recommendations": self._generate_complexity_recommendations(
                    complexity_distribution
                ),
            },
            "duplication_analysis": duplication_analysis,
            "test_coverage": test_coverage,
            "code_smells": code_smells,
            "quality_improvement_plan": self._generate_improvement_plan(
                complexity_distribution,
                test_coverage,
                duplication_analysis,
                code_smells,
            ),
        }

        return report

    def _calculate_overall_quality(
        self, complexity_dist: Dict, coverage: float, smell_score: float
    ) -> Dict[str, Any]:
        """전체 품질 등급 계산"""

        # 복잡도 점수 (40점 만점)
        complexity_score = (
            (
                complexity_dist["GOOD"] * 10
                + complexity_dist["ACCEPTABLE"] * 7
                + complexity_dist["POOR"] * 4
                + complexity_dist["CRITICAL"] * 1
            )
            / max(1, sum(complexity_dist.values()))
            * 4
        )

        # 테스트 커버리지 점수 (30점 만점)
        coverage_score = min(coverage / 100 * 30, 30)

        # 코드 냄새 점수 (30점 만점)
        smell_score_normalized = smell_score / 100 * 30

        total_score = complexity_score + coverage_score + smell_score_normalized

        if total_score >= 85:
            grade = "A"
        elif total_score >= 75:
            grade = "B"
        elif total_score >= 65:
            grade = "C"
        elif total_score >= 50:
            grade = "D"
        else:
            grade = "F"

        return {"score": round(total_score, 1), "grade": grade}

    def _generate_complexity_recommendations(self, distribution: Dict) -> List[str]:
        """복잡도 개선 권장사항"""
        recommendations = []

        critical_count = distribution["CRITICAL"]
        poor_count = distribution["POOR"]

        if critical_count > 0:
            recommendations.append(
                f"CRITICAL 복잡도 함수 {critical_count}개 즉시 리팩터링 필요"
            )

        if poor_count > 0:
            recommendations.append(f"POOR 복잡도 함수 {poor_count}개 분할 검토")

        if critical_count + poor_count > distribution["GOOD"]:
            recommendations.append("전체적인 함수 설계 패턴 재검토 권장")

        return recommendations

    def _generate_improvement_plan(
        self, complexity: Dict, coverage: Dict, duplication: Dict, smells: Dict
    ) -> Dict[str, Any]:
        """품질 개선 계획 수립"""

        plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_objectives": [],
        }

        # 즉시 조치
        if complexity["CRITICAL"] > 0:
            plan["immediate_actions"].append(
                f"Critical 복잡도 함수 {complexity['CRITICAL']}개 리팩터링"
            )

        if duplication["total_duplicates"] > 5:
            plan["immediate_actions"].append(
                f"중복 코드 블록 {duplication['total_duplicates']}개 통합"
            )

        high_smells = smells["severity_distribution"].get("HIGH", 0)
        if high_smells > 0:
            plan["immediate_actions"].append(
                f"High severity 코드 냄새 {high_smells}개 해결"
            )

        # 단기 목표
        if coverage["coverage_summary"]["coverage_percentage"] < 80:
            plan["short_term_goals"].append("테스트 커버리지 80% 달성")

        if complexity["POOR"] > 2:
            plan["short_term_goals"].append("Poor 복잡도 함수들 분할 및 단순화")

        # 장기 목표
        plan["long_term_objectives"].extend(
            [
                "전체 함수 복잡도 평균 5 이하 달성",
                "테스트 커버리지 90% 이상 유지",
                "코드 중복도 1% 이하 달성",
                "자동화된 품질 게이트 구축",
            ]
        )

        return plan

    def save_quality_audit(self, output_dir: str = "out") -> str:
        """품질 감사 결과 저장"""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 종합 보고서 생성
        report = self.generate_comprehensive_quality_report()

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"code_quality_audit_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Excel 저장 (상세 데이터)
        excel_path = output_path / f"code_quality_details_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # 복잡도 상세
            complexity_data = []
            for file_name, functions in report["complexity_analysis"][
                "detailed_functions"
            ].items():
                for func in functions:
                    complexity_data.append(
                        {
                            "File": file_name,
                            "Function": func["name"],
                            "Complexity": func["cyclomatic_complexity"],
                            "Rating": func["quality_rating"],
                            "Lines": func["total_lines"],
                            "Code_Lines": func["code_lines"],
                        }
                    )

            if complexity_data:
                complexity_df = pd.DataFrame(complexity_data)
                complexity_df.to_excel(
                    writer, sheet_name="Function_Complexity", index=False
                )

            # 코드 냄새 상세
            smells_data = []
            for smell in report["code_smells"]["detailed_smells"]:
                smells_data.append(
                    {
                        "Type": smell["type"],
                        "File": smell["file"],
                        "Severity": smell["severity"],
                        "Description": smell["description"],
                        "Line": smell.get("line", "N/A"),
                        "Function": smell.get("function", "N/A"),
                    }
                )

            if smells_data:
                smells_df = pd.DataFrame(smells_data)
                smells_df.to_excel(writer, sheet_name="Code_Smells", index=False)

            # 중복 코드 상세
            if report["duplication_analysis"]["duplicate_blocks"]:
                dup_data = []
                for dup in report["duplication_analysis"]["duplicate_blocks"]:
                    for location in dup["locations"]:
                        dup_data.append(
                            {
                                "Hash": dup["hash"][:8],
                                "File": Path(location["file"]).name,
                                "Start_Line": location["start_line"],
                                "End_Line": location["end_line"],
                                "Severity": dup["severity"],
                                "Total_Duplicates": dup["duplicate_count"],
                            }
                        )

                if dup_data:
                    dup_df = pd.DataFrame(dup_data)
                    dup_df.to_excel(writer, sheet_name="Code_Duplications", index=False)

            # 미테스트 함수들
            if report["test_coverage"]["untested_functions"]:
                untested_df = pd.DataFrame(
                    report["test_coverage"]["untested_functions"]
                )
                untested_df.to_excel(
                    writer, sheet_name="Untested_Functions", index=False
                )

        logger.info(f"Code quality audit completed:")
        logger.info(f"  JSON Report: {json_path}")
        logger.info(f"  Excel Details: {excel_path}")

        return str(json_path)


def main():
    """메인 실행 함수"""

    current_dir = Path(__file__).parent
    auditor = LogiCodeQualityAuditor(current_dir)
    report_path = auditor.save_quality_audit()

    # 결과 요약 출력
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("\n" + "=" * 80)
    print("DSV SHPT Code Quality Audit 완료")
    print("=" * 80)

    summary = report["executive_summary"]
    print(
        f"\n전체 품질 등급: {summary['overall_quality_grade']} ({summary['overall_quality_score']}/100)"
    )
    print(f"분석 파일: {summary['files_analyzed']}개")
    print(f"분석 함수: {summary['total_functions']}개")

    print(f"\n핵심 메트릭:")
    metrics = summary["key_metrics"]
    print(f"  평균 복잡도: {metrics['average_complexity']:.1f}")
    print(f"  테스트 커버리지: {metrics['test_coverage_percentage']:.1f}%")
    print(f"  코드 중복: {metrics['code_duplications']}개")
    print(f"  코드 냄새: {metrics['code_smells']}개")

    print(f"\n중요 이슈:")
    for issue in summary["critical_issues"]:
        print(f"  • {issue}")

    # 개선 계획
    plan = report["quality_improvement_plan"]
    if plan["immediate_actions"]:
        print(f"\n즉시 조치 필요:")
        for action in plan["immediate_actions"]:
            print(f"  1. {action}")

    print(f"\n상세 보고서: {report_path}")

    return report


if __name__ == "__main__":
    main()
