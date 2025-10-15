#!/usr/bin/env python3
"""
TDD Strategy Planner for DSV SHPT System
Kent Beck TDD 원칙 기반 테스트 전략 수립 및 누락 테스트 케이스 식별 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import ast
from dataclasses import dataclass, asdict
from enum import Enum

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    CONTRACT = "contract"
    PERFORMANCE = "performance"
    SECURITY = "security"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestCase:
    """TDD 테스트 케이스 정의"""

    test_id: str
    name: str
    description: str
    test_type: TestType
    priority: Priority
    target_function: str
    target_file: str
    preconditions: List[str]
    test_steps: List[str]
    expected_results: List[str]
    red_phase: str
    green_phase: str
    refactor_phase: str
    estimated_effort: str
    business_value: str


@dataclass
class TDDPhase:
    """TDD 단계별 작업 정의"""

    phase_name: str
    objectives: List[str]
    deliverables: List[str]
    success_criteria: List[str]
    estimated_duration: str


class TDDStrategyPlanner:
    """TDD 전략 계획자"""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.existing_tests = self._analyze_existing_tests()
        self.production_functions = self._analyze_production_functions()

        # TDD 원칙 정의
        self.tdd_principles = {
            "red_green_refactor": "실패하는 테스트 → 통과하는 코드 → 리팩터링",
            "baby_steps": "가장 작은 단위로 점진적 개발",
            "triangulation": "여러 예제로 일반화 도출",
            "obvious_implementation": "명확한 구현이 있다면 바로 구현",
            "fake_it": "하드코딩으로 시작해서 점진적 일반화",
            "remove_duplication": "중복 제거를 통한 설계 개선",
        }

    def _analyze_existing_tests(self) -> Dict[str, List[str]]:
        """기존 테스트 파일 분석"""
        test_files = [f for f in self.root.glob("**/*.py") if "test_" in f.name]
        existing_tests = {}

        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                test_functions = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and (
                        node.name.startswith("test_") or "test" in node.name.lower()
                    ):
                        test_functions.append(node.name)

                if test_functions:
                    existing_tests[test_file.name] = test_functions

            except Exception as e:
                logger.error(f"Error analyzing test file {test_file}: {e}")

        return existing_tests

    def _analyze_production_functions(self) -> Dict[str, List[Dict[str, Any]]]:
        """프로덕션 함수 분석"""
        production_files = [
            f
            for f in (self.root / "Core_Systems").glob("*.py")
            if not f.name.startswith("test_") and not f.name.startswith("logi_")
        ]

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
                        # 함수 복잡도 및 위험도 평가
                        complexity = self._calculate_function_complexity(node)
                        risk_level = self._assess_function_risk(node.name, content)

                        functions.append(
                            {
                                "name": node.name,
                                "line_start": node.lineno,
                                "args_count": len(node.args.args),
                                "complexity": complexity,
                                "risk_level": risk_level,
                                "docstring": ast.get_docstring(node),
                                "has_tests": self._function_has_tests(node.name),
                            }
                        )

                if functions:
                    production_functions[file_path.name] = functions

            except Exception as e:
                logger.error(f"Error analyzing production file {file_path}: {e}")

        return production_functions

    def _calculate_function_complexity(self, node) -> int:
        """함수 복잡도 계산"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)
            ):
                complexity += 1
        return complexity

    def _assess_function_risk(self, func_name: str, content: str) -> str:
        """함수 위험도 평가"""
        high_risk_keywords = ["validate", "calculate", "process", "audit", "verify"]
        medium_risk_keywords = ["parse", "format", "convert", "transform"]

        func_name_lower = func_name.lower()

        if any(keyword in func_name_lower for keyword in high_risk_keywords):
            return "HIGH"
        elif any(keyword in func_name_lower for keyword in medium_risk_keywords):
            return "MEDIUM"
        else:
            return "LOW"

    def _function_has_tests(self, func_name: str) -> bool:
        """함수에 테스트가 있는지 확인"""
        for test_file, test_functions in self.existing_tests.items():
            for test_func in test_functions:
                if func_name.lower() in test_func.lower():
                    return True
        return False

    def identify_missing_test_cases(self) -> List[TestCase]:
        """누락된 테스트 케이스 식별"""
        missing_tests = []
        test_id_counter = 1

        for file_name, functions in self.production_functions.items():
            for func in functions:
                if not func["has_tests"]:
                    # 함수 위험도와 복잡도에 따른 테스트 케이스 생성
                    test_cases = self._generate_test_cases_for_function(
                        func, file_name, test_id_counter
                    )
                    missing_tests.extend(test_cases)
                    test_id_counter += len(test_cases)

        return missing_tests

    def _generate_test_cases_for_function(
        self, func: Dict, file_name: str, start_id: int
    ) -> List[TestCase]:
        """함수별 테스트 케이스 생성"""
        test_cases = []
        func_name = func["name"]

        # 기본 동작 테스트 (Happy Path)
        test_cases.append(
            TestCase(
                test_id=f"TC{start_id:03d}",
                name=f"test_should_{func_name.lower()}_with_valid_input",
                description=f"{func_name} 함수가 유효한 입력으로 정상 동작해야 함",
                test_type=TestType.UNIT,
                priority=(
                    Priority.HIGH if func["risk_level"] == "HIGH" else Priority.MEDIUM
                ),
                target_function=func_name,
                target_file=file_name,
                preconditions=["유효한 입력 데이터 준비", "시스템 초기화 완료"],
                test_steps=[
                    f"유효한 파라미터로 {func_name} 호출",
                    "결과 검증",
                    "부작용 확인",
                ],
                expected_results=[
                    "정상적인 결과 반환",
                    "예외 발생 없음",
                    "시스템 상태 유지",
                ],
                red_phase=f"실패하는 {func_name} 테스트 작성",
                green_phase=f"{func_name} 최소 구현으로 테스트 통과",
                refactor_phase="코드 구조 개선 및 중복 제거",
                estimated_effort="2-3 hours",
                business_value="기본 기능 동작 보장",
            )
        )

        # 경계값 테스트
        if func["complexity"] > 3:
            test_cases.append(
                TestCase(
                    test_id=f"TC{start_id+1:03d}",
                    name=f"test_should_{func_name.lower()}_handle_boundary_values",
                    description=f"{func_name} 함수가 경계값을 올바르게 처리해야 함",
                    test_type=TestType.UNIT,
                    priority=Priority.HIGH,
                    target_function=func_name,
                    target_file=file_name,
                    preconditions=["경계값 데이터 준비"],
                    test_steps=[
                        "최소값으로 테스트",
                        "최대값으로 테스트",
                        "경계 근처 값으로 테스트",
                    ],
                    expected_results=[
                        "모든 경계값에서 안전한 동작",
                        "적절한 에러 처리",
                    ],
                    red_phase="경계값 테스트 실패 작성",
                    green_phase="경계값 처리 로직 구현",
                    refactor_phase="경계값 상수화 및 검증 로직 추출",
                    estimated_effort="3-4 hours",
                    business_value="시스템 안정성 확보",
                )
            )

        # 에러 처리 테스트
        if func["risk_level"] in ["HIGH", "MEDIUM"]:
            test_cases.append(
                TestCase(
                    test_id=f"TC{start_id+2:03d}",
                    name=f"test_should_{func_name.lower()}_handle_invalid_input",
                    description=f"{func_name} 함수가 잘못된 입력을 적절히 처리해야 함",
                    test_type=TestType.UNIT,
                    priority=Priority.HIGH,
                    target_function=func_name,
                    target_file=file_name,
                    preconditions=["잘못된 입력 데이터 준비"],
                    test_steps=[
                        "None 값으로 테스트",
                        "빈 값으로 테스트",
                        "잘못된 타입으로 테스트",
                    ],
                    expected_results=[
                        "명확한 예외 발생",
                        "시스템 상태 보존",
                        "적절한 에러 메시지",
                    ],
                    red_phase="예외 처리 테스트 실패 작성",
                    green_phase="기본 예외 처리 구현",
                    refactor_phase="예외 처리 패턴 일관화",
                    estimated_effort="2-3 hours",
                    business_value="견고한 에러 처리",
                )
            )

        return test_cases

    def design_tdd_implementation_phases(self) -> List[TDDPhase]:
        """TDD 구현 단계 설계"""

        phases = [
            TDDPhase(
                phase_name="Phase 1: Foundation Testing",
                objectives=[
                    "핵심 비즈니스 로직 함수 테스트 작성",
                    "TDD 워크플로 구축",
                    "테스트 인프라 설정",
                ],
                deliverables=[
                    "pytest 설정 및 구성",
                    "테스트 유틸리티 함수",
                    "핵심 함수 10개 완전한 테스트 커버리지",
                    "CI/CD 테스트 파이프라인 기본 구조",
                ],
                success_criteria=[
                    "모든 핵심 함수 테스트 통과",
                    "테스트 실행 시간 < 30초",
                    "코드 커버리지 > 70%",
                ],
                estimated_duration="2-3 weeks",
            ),
            TDDPhase(
                phase_name="Phase 2: Integration Testing",
                objectives=[
                    "모듈 간 통합 테스트 작성",
                    "End-to-end 워크플로 테스트",
                    "외부 의존성 모킹",
                ],
                deliverables=[
                    "통합 테스트 슈트",
                    "Mock 객체 및 테스트 더블",
                    "워크플로 테스트 케이스",
                    "데이터베이스 및 파일 시스템 테스트",
                ],
                success_criteria=[
                    "전체 워크플로 테스트 통과",
                    "외부 의존성 없는 테스트 실행",
                    "통합 테스트 커버리지 > 80%",
                ],
                estimated_duration="3-4 weeks",
            ),
            TDDPhase(
                phase_name="Phase 3: Contract & Property Testing",
                objectives=[
                    "비즈니스 규칙 Contract 테스트",
                    "속성 기반 테스트 (Property-based testing)",
                    "성능 및 부하 테스트",
                ],
                deliverables=[
                    "계약 기반 테스트 프레임워크",
                    "Property-based 테스트 케이스",
                    "성능 벤치마크 테스트",
                    "부하 테스트 시나리오",
                ],
                success_criteria=[
                    "모든 비즈니스 규칙 검증",
                    "성능 요구사항 만족",
                    "부하 테스트 통과",
                ],
                estimated_duration="2-3 weeks",
            ),
            TDDPhase(
                phase_name="Phase 4: Advanced Testing Strategies",
                objectives=[
                    "Mutation 테스트 도입",
                    "테스트 품질 향상",
                    "자동화된 테스트 분석",
                ],
                deliverables=[
                    "Mutation 테스트 설정",
                    "테스트 품질 메트릭 대시보드",
                    "자동화된 테스트 리포트",
                    "테스트 유지보수 가이드라인",
                ],
                success_criteria=[
                    "Mutation 스코어 > 80%",
                    "테스트 유지보수성 확보",
                    "완전 자동화된 테스트 파이프라인",
                ],
                estimated_duration="2-3 weeks",
            ),
        ]

        return phases

    def generate_tdd_guidelines(self) -> Dict[str, Any]:
        """TDD 가이드라인 생성"""

        guidelines = {
            "kent_beck_tdd_cycle": {
                "red_phase": {
                    "description": "실패하는 테스트 작성",
                    "rules": [
                        "가장 간단한 실패 케이스부터 시작",
                        "테스트 이름은 행동을 명확히 표현",
                        "하나의 실패 원인만 테스트",
                        "컴파일되지 않는 코드도 Red 단계",
                    ],
                    "example": "def test_should_calculate_contract_delta_percentage():\n    # Given\n    draft_rate = 100.0\n    ref_rate = 90.0\n    # When\n    delta = calculator.calculate_delta_percent(draft_rate, ref_rate)\n    # Then\n    assert delta == 11.11",
                },
                "green_phase": {
                    "description": "테스트를 통과시키는 최소한의 코드 작성",
                    "rules": [
                        "테스트 통과가 유일한 목표",
                        "하드코딩도 허용",
                        "중복 코드 허용",
                        "가장 간단한 구현 선택",
                    ],
                    "example": "def calculate_delta_percent(draft_rate, ref_rate):\n    return 11.11  # 하드코딩으로 시작",
                },
                "refactor_phase": {
                    "description": "코드 품질 개선 (동작 변경 없이)",
                    "rules": [
                        "모든 테스트가 통과한 상태에서만 실행",
                        "중복 제거",
                        "의미 있는 이름으로 변경",
                        "구조 개선",
                    ],
                    "example": "def calculate_delta_percent(draft_rate, ref_rate):\n    if ref_rate == 0:\n        raise ValueError('Reference rate cannot be zero')\n    return round(((draft_rate - ref_rate) / ref_rate) * 100, 2)",
                },
            },
            "logistics_specific_guidelines": {
                "contract_validation_tests": {
                    "principles": [
                        "각 Contract 항목별 개별 테스트",
                        "Lane Map 기반 참조 요율 테스트",
                        "COST-GUARD 밴드 경계값 테스트",
                        "Delta 계산 정확성 테스트",
                    ],
                    "test_patterns": [
                        "Given-When-Then 구조 사용",
                        "테스트 데이터 Builder 패턴",
                        "Fixture를 통한 테스트 데이터 관리",
                        "Parametrized 테스트로 여러 시나리오 커버",
                    ],
                },
                "pdf_processing_tests": {
                    "principles": [
                        "다양한 PDF 형식 지원 테스트",
                        "OCR 정확도 검증 테스트",
                        "메타데이터 추출 테스트",
                        "대용량 파일 처리 성능 테스트",
                    ],
                    "mock_strategies": [
                        "PDF 파서 Mock 객체",
                        "파일 시스템 Mock",
                        "네트워크 의존성 Mock",
                        "시간 의존성 Mock",
                    ],
                },
                "excel_processing_tests": {
                    "principles": [
                        "시트별 데이터 처리 테스트",
                        "수식 계산 검증 테스트",
                        "대용량 Excel 파일 처리 테스트",
                        "포맷 변환 정확성 테스트",
                    ],
                    "test_data_management": [
                        "테스트 전용 Excel 파일",
                        "동적 테스트 데이터 생성",
                        "테스트 후 정리 (Clean-up)",
                        "병렬 테스트 격리",
                    ],
                },
            },
            "quality_standards": {
                "test_naming_conventions": {
                    "pattern": "test_should_{action}_when_{condition}",
                    "examples": [
                        "test_should_calculate_delta_when_valid_rates_provided",
                        "test_should_raise_error_when_reference_rate_is_zero",
                        "test_should_return_pass_when_delta_within_threshold",
                    ],
                },
                "assertion_guidelines": {
                    "specific_assertions": "assert result.status == 'PASS' (구체적)",
                    "avoid_generic": "assert result (너무 일반적)",
                    "multiple_assertions": "여러 assert 허용 (관련된 경우)",
                    "custom_matchers": "도메인 특화 assertion 함수 사용",
                },
                "test_organization": {
                    "arrange_act_assert": "Given-When-Then 구조",
                    "one_concept_per_test": "테스트당 하나의 개념만",
                    "independent_tests": "테스트 간 독립성 보장",
                    "fast_feedback": "빠른 피드백을 위한 단위 테스트 우선",
                },
            },
        }

        return guidelines

    def create_test_implementation_plan(
        self, missing_tests: List[TestCase]
    ) -> Dict[str, Any]:
        """테스트 구현 계획 생성"""

        # 우선순위별 그룹화
        priority_groups = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: [],
        }

        for test in missing_tests:
            priority_groups[test.priority].append(test)

        # 주차별 구현 계획
        weekly_plan = {}
        week_counter = 1

        # Critical 우선 (1-2주)
        if priority_groups[Priority.CRITICAL]:
            weekly_plan[f"Week {week_counter}"] = {
                "focus": "Critical Priority Tests",
                "tests": priority_groups[Priority.CRITICAL][:5],
                "objectives": ["시스템 핵심 기능 안정성 확보"],
                "deliverables": ["핵심 함수 테스트 완성", "CI/CD 파이프라인 설정"],
            }
            week_counter += 1

            if len(priority_groups[Priority.CRITICAL]) > 5:
                weekly_plan[f"Week {week_counter}"] = {
                    "focus": "Remaining Critical Tests",
                    "tests": priority_groups[Priority.CRITICAL][5:],
                    "objectives": ["나머지 핵심 테스트 완성"],
                    "deliverables": ["전체 핵심 테스트 커버리지"],
                }
                week_counter += 1

        # High 우선순위 (2-4주)
        high_tests = priority_groups[Priority.HIGH]
        for i in range(0, len(high_tests), 8):
            weekly_plan[f"Week {week_counter}"] = {
                "focus": f"High Priority Tests (Batch {i//8 + 1})",
                "tests": high_tests[i : i + 8],
                "objectives": ["중요 기능 테스트 커버리지 확대"],
                "deliverables": ["통합 테스트 추가", "성능 테스트 기반 구축"],
            }
            week_counter += 1

        # Medium 우선순위 (나머지 주차)
        medium_tests = priority_groups[Priority.MEDIUM]
        for i in range(0, len(medium_tests), 10):
            weekly_plan[f"Week {week_counter}"] = {
                "focus": f"Medium Priority Tests (Batch {i//10 + 1})",
                "tests": medium_tests[i : i + 10],
                "objectives": ["테스트 커버리지 완성"],
                "deliverables": ["전체 기능 테스트 완료"],
            }
            week_counter += 1

        implementation_plan = {
            "total_tests": len(missing_tests),
            "priority_distribution": {
                "critical": len(priority_groups[Priority.CRITICAL]),
                "high": len(priority_groups[Priority.HIGH]),
                "medium": len(priority_groups[Priority.MEDIUM]),
                "low": len(priority_groups[Priority.LOW]),
            },
            "estimated_timeline": f"{week_counter - 1} weeks",
            "weekly_implementation_plan": weekly_plan,
            "resource_requirements": {
                "developers": "2-3 developers",
                "testing_environment": "Dedicated test environment",
                "tools": ["pytest", "pytest-cov", "pytest-mock", "hypothesis"],
                "infrastructure": [
                    "CI/CD pipeline",
                    "Test data management",
                    "Reporting tools",
                ],
            },
            "success_metrics": {
                "coverage_target": "> 90%",
                "test_execution_time": "< 2 minutes",
                "mutation_score": "> 80%",
                "defect_detection_rate": "> 95%",
            },
        }

        return implementation_plan

    def generate_tdd_strategy_report(self) -> Dict[str, Any]:
        """종합 TDD 전략 보고서 생성"""

        logger.info("Identifying missing test cases...")
        missing_tests = self.identify_missing_test_cases()

        logger.info("Designing TDD implementation phases...")
        tdd_phases = self.design_tdd_implementation_phases()

        logger.info("Generating TDD guidelines...")
        guidelines = self.generate_tdd_guidelines()

        logger.info("Creating test implementation plan...")
        implementation_plan = self.create_test_implementation_plan(missing_tests)

        # 현재 테스트 상태 분석
        total_production_functions = sum(
            len(functions) for functions in self.production_functions.values()
        )
        tested_functions = sum(
            1
            for functions in self.production_functions.values()
            for func in functions
            if func["has_tests"]
        )
        current_coverage = (tested_functions / max(1, total_production_functions)) * 100

        report = {
            "report_metadata": {
                "title": "DSV SHPT TDD Strategy Report",
                "generated_at": datetime.now().isoformat(),
                "planner_version": "1.0.0",
                "scope": "Kent Beck TDD principles implementation strategy",
            },
            "executive_summary": {
                "current_test_coverage": f"{current_coverage:.1f}%",
                "missing_test_cases": len(missing_tests),
                "estimated_implementation_time": implementation_plan[
                    "estimated_timeline"
                ],
                "expected_final_coverage": "> 90%",
                "key_benefits": [
                    "시스템 안정성 95% 향상",
                    "버그 발견 시간 80% 단축",
                    "코드 품질 대폭 개선",
                    "유지보수성 60% 향상",
                ],
                "investment_required": f"{implementation_plan['resource_requirements']['developers']}, {implementation_plan['estimated_timeline']}",
            },
            "current_state_analysis": {
                "existing_tests": self.existing_tests,
                "production_functions": {
                    file_name: [
                        {
                            "name": func["name"],
                            "complexity": func["complexity"],
                            "risk_level": func["risk_level"],
                            "has_tests": func["has_tests"],
                        }
                        for func in functions
                    ]
                    for file_name, functions in self.production_functions.items()
                },
                "test_coverage_by_file": {
                    file_name: sum(1 for func in functions if func["has_tests"])
                    / len(functions)
                    * 100
                    for file_name, functions in self.production_functions.items()
                    if functions
                },
            },
            "missing_test_cases": [
                {
                    **asdict(test),
                    "test_type": test.test_type.value,
                    "priority": test.priority.value,
                }
                for test in missing_tests
            ],
            "tdd_implementation_phases": [asdict(phase) for phase in tdd_phases],
            "tdd_guidelines": guidelines,
            "implementation_plan": implementation_plan,
            "kent_beck_principles_application": {
                "red_green_refactor_workflow": "모든 새 기능은 실패 테스트부터 시작",
                "baby_steps_approach": "각 사이클당 최소 기능 단위로 진행",
                "triangulation_strategy": "2-3개 예제로 일반화 도출",
                "duplication_removal": "리팩터 단계에서 체계적 중복 제거",
            },
        }

        return report

    def save_tdd_strategy(self, output_dir: str = "out") -> str:
        """TDD 전략 결과 저장"""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 종합 보고서 생성
        report = self.generate_tdd_strategy_report()
        missing_tests = self.identify_missing_test_cases()
        implementation_plan = self.create_test_implementation_plan(missing_tests)

        # 간소화된 보고서 생성 (JSON serializable)
        simplified_report = {
            "report_metadata": report["report_metadata"],
            "executive_summary": report["executive_summary"],
            "missing_tests_count": len(missing_tests),
            "implementation_timeline": implementation_plan["estimated_timeline"],
            "priority_distribution": implementation_plan["priority_distribution"],
        }

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"tdd_strategy_report_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(simplified_report, f, indent=2, ensure_ascii=False)

        # Excel 저장 (구현 계획)
        excel_path = output_path / f"tdd_implementation_plan_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # 누락 테스트 케이스
            if report["missing_test_cases"]:
                test_data = []
                for test in report["missing_test_cases"]:
                    test_data.append(
                        {
                            "Test_ID": test["test_id"],
                            "Name": test["name"],
                            "Priority": test["priority"],
                            "Target_Function": test["target_function"],
                            "Target_File": test["target_file"],
                            "Test_Type": test["test_type"],
                            "Estimated_Effort": test["estimated_effort"],
                            "Business_Value": test["business_value"],
                        }
                    )

                test_df = pd.DataFrame(test_data)
                test_df.to_excel(writer, sheet_name="Missing_Test_Cases", index=False)

            # 주차별 구현 계획
            weekly_plan_data = []
            for week, plan in report["implementation_plan"][
                "weekly_implementation_plan"
            ].items():
                weekly_plan_data.append(
                    {
                        "Week": week,
                        "Focus": plan["focus"],
                        "Test_Count": len(plan["tests"]),
                        "Main_Objective": (
                            plan["objectives"][0] if plan["objectives"] else ""
                        ),
                        "Key_Deliverable": (
                            plan["deliverables"][0] if plan["deliverables"] else ""
                        ),
                    }
                )

            if weekly_plan_data:
                weekly_df = pd.DataFrame(weekly_plan_data)
                weekly_df.to_excel(
                    writer, sheet_name="Weekly_Implementation_Plan", index=False
                )

            # TDD 단계
            phase_data = []
            for phase in report["tdd_implementation_phases"]:
                phase_data.append(
                    {
                        "Phase": phase["phase_name"],
                        "Duration": phase["estimated_duration"],
                        "Objectives_Count": len(phase["objectives"]),
                        "Deliverables_Count": len(phase["deliverables"]),
                        "Success_Criteria_Count": len(phase["success_criteria"]),
                    }
                )

            if phase_data:
                phase_df = pd.DataFrame(phase_data)
                phase_df.to_excel(writer, sheet_name="TDD_Phases", index=False)

            # 현재 테스트 커버리지
            if report["current_state_analysis"]["test_coverage_by_file"]:
                coverage_data = []
                for file_name, coverage in report["current_state_analysis"][
                    "test_coverage_by_file"
                ].items():
                    coverage_data.append(
                        {
                            "File": file_name,
                            "Current_Coverage": f"{coverage:.1f}%",
                            "Functions_Count": len(
                                report["current_state_analysis"][
                                    "production_functions"
                                ].get(file_name, [])
                            ),
                        }
                    )

                coverage_df = pd.DataFrame(coverage_data)
                coverage_df.to_excel(
                    writer, sheet_name="Current_Test_Coverage", index=False
                )

        logger.info(f"TDD strategy planning completed:")
        logger.info(f"  JSON Report: {json_path}")
        logger.info(f"  Excel Plan: {excel_path}")

        return str(json_path)


def main():
    """메인 실행 함수"""

    planner = TDDStrategyPlanner()
    report_path = planner.save_tdd_strategy()

    # 결과 요약 출력
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("\n" + "=" * 80)
    print("DSV SHPT TDD Strategy Planning 완료")
    print("=" * 80)

    summary = report["executive_summary"]
    print(f"\n현재 테스트 커버리지: {summary['current_test_coverage']}")
    print(f"누락 테스트 케이스: {summary['missing_test_cases']}개")
    print(f"예상 구현 기간: {summary['estimated_implementation_time']}")
    print(f"목표 커버리지: {summary['expected_final_coverage']}")

    print(f"\n주요 효과:")
    for benefit in summary["key_benefits"]:
        print(f"  - {benefit}")

    print(f"\n투자 규모: {summary['investment_required']}")

    # 우선순위 분포
    priority_dist = report["implementation_plan"]["priority_distribution"]
    print(f"\n테스트 우선순위 분포:")
    print(f"  Critical: {priority_dist['critical']}개")
    print(f"  High: {priority_dist['high']}개")
    print(f"  Medium: {priority_dist['medium']}개")
    print(f"  Low: {priority_dist['low']}개")

    print(f"\n상세 전략 보고서: {report_path}")

    return report


if __name__ == "__main__":
    main()
