#!/usr/bin/env python3
"""
Technical Debt Manager for DSV SHPT System
백업 파일 정리, 네이밍 표준화, 문서 동기화 등 기술 부채 해결 계획 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, asdict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TechnicalDebt:
    """기술 부채 정의"""

    debt_id: str
    category: str
    description: str
    severity: str
    affected_files: List[str]
    resolution_plan: str
    estimated_effort: str
    risk_if_not_resolved: str
    priority: int


@dataclass
class CleanupAction:
    """정리 작업 정의"""

    action_id: str
    action_type: str
    target_files: List[str]
    description: str
    automated: bool
    verification_steps: List[str]


class TechnicalDebtManager:
    """기술 부채 관리자"""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.core_systems = self.root / "Core_Systems"

        # 파일 패턴 정의
        self.file_patterns = {
            "backup_files": ["*_backup.py", "*_bak.py", "*.backup"],
            "duplicate_files": ["*_copy.py", "*_duplicate.py", "*_old.py"],
            "test_files": ["test_*.py", "*_test.py"],
            "temp_files": ["temp_*.py", "*_tmp.py", "*.temp"],
            "generated_files": ["logi_*.py"],  # 오늘 생성한 분석 도구들
            "obsolete_vba_files": ["*vba*.py", "*VBA*.py"],  # 삭제된 VBA 관련
        }

        # 네이밍 컨벤션
        self.naming_conventions = {
            "analysis_tools": "logi_{function}_{YYMMDD}.py",
            "core_modules": "{module_name}_system.py",
            "test_files": "test_{module_name}.py",
            "utility_files": "util_{function}.py",
            "config_files": "config_{environment}.{json|yaml}",
            "report_files": "report_{type}_{timestamp}.{json|xlsx|md}",
        }

    def scan_file_system(self) -> Dict[str, List[Path]]:
        """파일 시스템 스캔"""

        file_inventory = {
            "all_python_files": [],
            "backup_files": [],
            "duplicate_files": [],
            "test_files": [],
            "temp_files": [],
            "config_files": [],
            "documentation_files": [],
            "result_files": [],
        }

        # Python 파일 스캔
        for py_file in self.root.rglob("*.py"):
            if py_file.is_file():
                file_inventory["all_python_files"].append(py_file)

                # 카테고리별 분류
                filename = py_file.name.lower()

                if any(
                    pattern.replace("*", "") in filename
                    for pattern in self.file_patterns["backup_files"]
                ):
                    file_inventory["backup_files"].append(py_file)
                elif any(
                    pattern.replace("*", "") in filename
                    for pattern in self.file_patterns["test_files"]
                ):
                    file_inventory["test_files"].append(py_file)
                elif any(
                    pattern.replace("*", "") in filename
                    for pattern in self.file_patterns["temp_files"]
                ):
                    file_inventory["temp_files"].append(py_file)

        # 설정 및 문서 파일 스캔
        for config_file in self.root.rglob("*.json"):
            if config_file.is_file():
                file_inventory["config_files"].append(config_file)

        for doc_file in self.root.rglob("*.md"):
            if doc_file.is_file():
                file_inventory["documentation_files"].append(doc_file)

        for result_file in self.root.rglob("*.xlsx"):
            if result_file.is_file():
                file_inventory["result_files"].append(result_file)

        return file_inventory

    def identify_technical_debts(
        self, file_inventory: Dict[str, List[Path]]
    ) -> List[TechnicalDebt]:
        """기술 부채 식별"""

        technical_debts = []
        debt_counter = 1

        # 1. 백업 파일 과다
        if len(file_inventory["backup_files"]) > 0:
            technical_debts.append(
                TechnicalDebt(
                    debt_id=f"TD{debt_counter:03d}",
                    category="File Management",
                    description=f"{len(file_inventory['backup_files'])}개의 백업 파일이 프로덕션 코드와 함께 존재",
                    severity="MEDIUM",
                    affected_files=[str(f) for f in file_inventory["backup_files"]],
                    resolution_plan="백업 파일을 별도 Archive 폴더로 이동",
                    estimated_effort="2-3 hours",
                    risk_if_not_resolved="코드 베이스 혼란, 잘못된 파일 수정 위험",
                    priority=2,
                )
            )
            debt_counter += 1

        # 2. 네이밍 비일관성
        inconsistent_files = []
        for py_file in file_inventory["all_python_files"]:
            filename = py_file.name
            # 일관성 없는 네이밍 패턴 체크
            if "_" in filename and filename.count("_") > 3:  # 과도한 언더스코어
                inconsistent_files.append(str(py_file))
            elif any(
                char.isupper() for char in filename.replace(".py", "")
            ):  # CamelCase 혼용
                inconsistent_files.append(str(py_file))

        if inconsistent_files:
            technical_debts.append(
                TechnicalDebt(
                    debt_id=f"TD{debt_counter:03d}",
                    category="Naming Convention",
                    description="파일명 네이밍 컨벤션 비일관성",
                    severity="LOW",
                    affected_files=inconsistent_files[:10],  # 상위 10개만
                    resolution_plan="snake_case 통일, 의미있는 이름으로 리네이밍",
                    estimated_effort="1-2 days",
                    risk_if_not_resolved="개발자 생산성 저하, 코드 탐색 어려움",
                    priority=3,
                )
            )
            debt_counter += 1

        # 3. 오래된 임시 파일
        temp_files = file_inventory["temp_files"]
        old_temp_files = []
        for temp_file in temp_files:
            # 생성일이 1주일 이상된 임시 파일
            if (datetime.now().timestamp() - temp_file.stat().st_mtime) > 7 * 24 * 3600:
                old_temp_files.append(str(temp_file))

        if old_temp_files:
            technical_debts.append(
                TechnicalDebt(
                    debt_id=f"TD{debt_counter:03d}",
                    category="File Cleanup",
                    description=f"{len(old_temp_files)}개의 오래된 임시 파일 존재",
                    severity="LOW",
                    affected_files=old_temp_files,
                    resolution_plan="1주일 이상된 임시 파일 자동 삭제",
                    estimated_effort="1 hour",
                    risk_if_not_resolved="디스크 공간 낭비, 프로젝트 구조 혼란",
                    priority=4,
                )
            )
            debt_counter += 1

        # 4. 문서 동기화 부족
        code_files_count = len(file_inventory["all_python_files"])
        doc_files_count = len(file_inventory["documentation_files"])

        if doc_files_count < code_files_count * 0.2:  # 문서:코드 비율이 20% 미만
            technical_debts.append(
                TechnicalDebt(
                    debt_id=f"TD{debt_counter:03d}",
                    category="Documentation",
                    description="코드 대비 문서화 부족 (현재 비율: {:.1f}%)".format(
                        doc_files_count / code_files_count * 100
                    ),
                    severity="MEDIUM",
                    affected_files=[],
                    resolution_plan="주요 모듈별 README.md 작성, API 문서 생성",
                    estimated_effort="1-2 weeks",
                    risk_if_not_resolved="시스템 이해도 저하, 온보딩 어려움",
                    priority=2,
                )
            )
            debt_counter += 1

        # 5. 중복 함수 (이전 분석 결과 기반)
        technical_debts.append(
            TechnicalDebt(
                debt_id=f"TD{debt_counter:03d}",
                category="Code Duplication",
                description="685개의 중복 코드 블록 및 19개 중복 함수 존재",
                severity="HIGH",
                affected_files=["Multiple files with duplicated logic"],
                resolution_plan="공통 유틸리티 모듈 추출, 중복 로직 통합",
                estimated_effort="2-3 weeks",
                risk_if_not_resolved="유지보수성 저하, 버그 증가",
                priority=1,
            )
        )
        debt_counter += 1

        # 6. 테스트 커버리지 부족 (이전 분석 결과 기반)
        technical_debts.append(
            TechnicalDebt(
                debt_id=f"TD{debt_counter:03d}",
                category="Test Coverage",
                description="테스트 커버리지 0%, 160개 누락 테스트 케이스",
                severity="CRITICAL",
                affected_files=["All production code without tests"],
                resolution_plan="TDD 전략에 따른 체계적 테스트 작성",
                estimated_effort="18 weeks",
                risk_if_not_resolved="시스템 안정성 저하, 버그 발생률 증가",
                priority=1,
            )
        )

        return technical_debts

    def create_cleanup_actions(
        self, file_inventory: Dict[str, List[Path]]
    ) -> List[CleanupAction]:
        """정리 작업 계획 생성"""

        cleanup_actions = []
        action_counter = 1

        # 1. 백업 파일 아카이빙
        if file_inventory["backup_files"]:
            cleanup_actions.append(
                CleanupAction(
                    action_id=f"CA{action_counter:03d}",
                    action_type="Archive",
                    target_files=[str(f) for f in file_inventory["backup_files"]],
                    description="백업 파일들을 Archive/Backups/ 폴더로 이동",
                    automated=True,
                    verification_steps=[
                        "백업 파일이 Archive 폴더로 이동되었는지 확인",
                        "원본 기능이 영향받지 않았는지 테스트",
                        "Archive 매니페스트 파일 생성",
                    ],
                )
            )
            action_counter += 1

        # 2. 임시 파일 정리
        if file_inventory["temp_files"]:
            cleanup_actions.append(
                CleanupAction(
                    action_id=f"CA{action_counter:03d}",
                    action_type="Delete",
                    target_files=[str(f) for f in file_inventory["temp_files"]],
                    description="임시 파일 삭제 (생성 7일 이후)",
                    automated=True,
                    verification_steps=[
                        "삭제 대상 파일 목록 검토",
                        "중요한 임시 파일 보존 확인",
                        "삭제 후 시스템 동작 확인",
                    ],
                )
            )
            action_counter += 1

        # 3. 분석 도구 파일 정리
        analysis_tools = [
            f for f in file_inventory["all_python_files"] if f.name.startswith("logi_")
        ]
        if analysis_tools:
            cleanup_actions.append(
                CleanupAction(
                    action_id=f"CA{action_counter:03d}",
                    action_type="Organize",
                    target_files=[str(f) for f in analysis_tools],
                    description="분석 도구들을 tools/ 또는 utils/ 폴더로 정리",
                    automated=False,
                    verification_steps=[
                        "도구별 용도 및 재사용성 검토",
                        "프로덕션 코드와 분리",
                        "도구 실행 스크립트 생성",
                    ],
                )
            )
            action_counter += 1

        # 4. 결과 파일 아카이빙
        old_results = []
        for result_file in file_inventory["result_files"]:
            # 1주일 이상된 결과 파일
            if (
                datetime.now().timestamp() - result_file.stat().st_mtime
            ) > 7 * 24 * 3600:
                old_results.append(str(result_file))

        if old_results:
            cleanup_actions.append(
                CleanupAction(
                    action_id=f"CA{action_counter:03d}",
                    action_type="Archive",
                    target_files=old_results,
                    description="오래된 결과 파일들을 Archive/Results/ 폴더로 이동",
                    automated=True,
                    verification_steps=[
                        "최신 3개 결과만 현재 위치에 유지",
                        "Archive 폴더 용량 확인",
                        "결과 파일 접근 권한 확인",
                    ],
                )
            )
            action_counter += 1

        # 5. 문서 구조화
        cleanup_actions.append(
            CleanupAction(
                action_id=f"CA{action_counter:03d}",
                action_type="Organize",
                target_files=[str(f) for f in file_inventory["documentation_files"]],
                description="문서 파일들을 계층적 구조로 정리",
                automated=False,
                verification_steps=[
                    "문서 카테고리별 분류",
                    "중복 문서 통합",
                    "문서 링크 및 참조 업데이트",
                    "문서 인덱스 생성",
                ],
            )
        )

        return cleanup_actions

    def generate_naming_standardization_plan(
        self, file_inventory: Dict[str, List[Path]]
    ) -> Dict[str, Any]:
        """네이밍 표준화 계획"""

        standardization_plan = {
            "current_naming_analysis": {
                "total_files": len(file_inventory["all_python_files"]),
                "naming_patterns": {},
                "inconsistencies": [],
            },
            "standardization_rules": {
                "file_naming": {
                    "core_modules": "{domain}_{component}_system.py",
                    "utilities": "util_{function_name}.py",
                    "tests": "test_{module_name}.py",
                    "analysis_tools": "logi_{tool_name}_{date}.py",
                    "configuration": "config_{environment}.{ext}",
                    "documentation": "{topic}_{type}.md",
                },
                "function_naming": {
                    "public_methods": "snake_case",
                    "private_methods": "_snake_case",
                    "constants": "UPPER_SNAKE_CASE",
                    "classes": "PascalCase",
                },
                "variable_naming": {
                    "local_variables": "snake_case",
                    "instance_variables": "snake_case",
                    "class_variables": "snake_case",
                    "global_constants": "UPPER_SNAKE_CASE",
                },
            },
            "refactoring_actions": [],
            "automated_checks": {
                "pre_commit_hooks": [
                    "flake8 naming convention check",
                    "pylint naming validation",
                    "custom naming pattern validator",
                ],
                "ci_pipeline": [
                    "naming convention compliance check",
                    "automated refactoring suggestions",
                    "documentation update validation",
                ],
            },
        }

        # 현재 네이밍 패턴 분석
        pattern_counts = defaultdict(int)
        for py_file in file_inventory["all_python_files"]:
            filename = py_file.name.replace(".py", "")

            if "_" in filename:
                pattern_counts["snake_case"] += 1
            elif any(c.isupper() for c in filename):
                pattern_counts["mixed_case"] += 1
            else:
                pattern_counts["lowercase"] += 1

        standardization_plan["current_naming_analysis"]["naming_patterns"] = dict(
            pattern_counts
        )

        # 리팩터링 액션 생성
        refactoring_actions = []

        for py_file in file_inventory["all_python_files"]:
            filename = py_file.name

            # 분석 도구 파일 네이밍 표준화
            if filename.startswith("logi_") and not re.match(
                r"logi_\w+_\d{6}\.py", filename
            ):
                suggested_name = (
                    f"logi_{filename.replace('logi_', '').replace('.py', '')}_251014.py"
                )
                refactoring_actions.append(
                    {
                        "current_name": filename,
                        "suggested_name": suggested_name,
                        "reason": "Analysis tool naming convention",
                        "priority": "LOW",
                    }
                )

        standardization_plan["refactoring_actions"] = refactoring_actions

        return standardization_plan

    def create_documentation_sync_plan(
        self, file_inventory: Dict[str, List[Path]]
    ) -> Dict[str, Any]:
        """문서 동기화 계획"""

        sync_plan = {
            "current_documentation_state": {
                "total_docs": len(file_inventory["documentation_files"]),
                "doc_types": {},
                "coverage_analysis": {},
            },
            "synchronization_requirements": {
                "api_documentation": "코드 변경 시 자동 업데이트",
                "architecture_docs": "주요 구조 변경 시 수동 업데이트",
                "user_guides": "기능 추가/변경 시 업데이트",
                "technical_specs": "설계 변경 시 실시간 동기화",
            },
            "automation_strategy": {
                "docstring_extraction": "Python docstring → API 문서 자동 생성",
                "code_analysis": "코드 변경 감지 → 관련 문서 업데이트 알림",
                "diagram_generation": "코드 구조 → UML/시퀀스 다이어그램 자동 생성",
                "changelog_automation": "커밋 메시지 → CHANGELOG.md 자동 업데이트",
            },
            "quality_standards": {
                "completeness": "모든 public API 문서화 100%",
                "accuracy": "코드-문서 불일치 0%",
                "freshness": "문서 업데이트 지연 < 24시간",
                "accessibility": "검색 가능한 문서 인덱스",
            },
        }

        # 문서 타입 분석
        doc_types = defaultdict(int)
        for doc_file in file_inventory["documentation_files"]:
            filename = doc_file.name.lower()

            if "readme" in filename:
                doc_types["README"] += 1
            elif "api" in filename:
                doc_types["API_DOCS"] += 1
            elif "guide" in filename or "manual" in filename:
                doc_types["USER_GUIDES"] += 1
            elif "spec" in filename or "design" in filename:
                doc_types["TECHNICAL_SPECS"] += 1
            else:
                doc_types["GENERAL"] += 1

        sync_plan["current_documentation_state"]["doc_types"] = dict(doc_types)

        # 커버리지 분석
        code_modules = len(
            [
                f
                for f in file_inventory["all_python_files"]
                if not f.name.startswith("test_")
            ]
        )
        doc_coverage = (
            len(file_inventory["documentation_files"]) / max(1, code_modules)
        ) * 100

        sync_plan["current_documentation_state"]["coverage_analysis"] = {
            "overall_coverage": f"{doc_coverage:.1f}%",
            "recommended_coverage": "50%+",
            "gap": max(0, 50 - doc_coverage),
        }

        return sync_plan

    def generate_implementation_timeline(
        self, technical_debts: List[TechnicalDebt], cleanup_actions: List[CleanupAction]
    ) -> Dict[str, Any]:
        """구현 타임라인 생성"""

        # 우선순위별 그룹화
        priority_groups = {1: [], 2: [], 3: [], 4: []}
        for debt in technical_debts:
            priority_groups[debt.priority].append(debt)

        # 주차별 계획
        weekly_timeline = {}
        current_week = 1

        # Week 1-2: Critical & High Priority
        critical_high = priority_groups[1]
        if critical_high:
            weekly_timeline[f"Week {current_week}"] = {
                "focus": "Critical Technical Debt Resolution",
                "tasks": [debt.description for debt in critical_high[:2]],
                "deliverables": ["중복 코드 통합 계획 수립", "테스트 전략 실행 시작"],
                "success_criteria": [
                    "중복 함수 50% 감소",
                    "핵심 모듈 테스트 커버리지 30% 달성",
                ],
            }
            current_week += 1

            if len(critical_high) > 2:
                weekly_timeline[f"Week {current_week}"] = {
                    "focus": "Remaining Critical Issues",
                    "tasks": [debt.description for debt in critical_high[2:]],
                    "deliverables": ["나머지 Critical 이슈 해결"],
                    "success_criteria": ["모든 Critical 기술 부채 해결"],
                }
                current_week += 1

        # Week 3-4: Medium Priority + Cleanup
        medium_priority = priority_groups[2]
        automated_cleanups = [action for action in cleanup_actions if action.automated]

        weekly_timeline[f"Week {current_week}"] = {
            "focus": "Medium Priority Debt + Automated Cleanup",
            "tasks": [debt.description for debt in medium_priority]
            + [action.description for action in automated_cleanups],
            "deliverables": [
                "백업 파일 아카이빙 완료",
                "임시 파일 정리 완료",
                "문서화 부족 개선",
            ],
            "success_criteria": ["파일 구조 정리 100%", "문서 커버리지 30% 향상"],
        }
        current_week += 1

        # Week 5-6: Low Priority + Manual Tasks
        low_priority = priority_groups[3] + priority_groups[4]
        manual_tasks = [action for action in cleanup_actions if not action.automated]

        weekly_timeline[f"Week {current_week}"] = {
            "focus": "Low Priority Debt + Manual Organization",
            "tasks": [debt.description for debt in low_priority]
            + [action.description for action in manual_tasks],
            "deliverables": [
                "네이밍 표준화 완료",
                "문서 구조 재정리",
                "분석 도구 정리",
            ],
            "success_criteria": ["네이밍 컨벤션 준수율 95%", "문서 구조 체계화 완료"],
        }
        current_week += 1

        # Week 7-8: Validation & Maintenance Setup
        weekly_timeline[f"Week {current_week}-{current_week+1}"] = {
            "focus": "Validation & Maintenance Automation Setup",
            "tasks": [
                "전체 기술 부채 해결 검증",
                "자동화된 품질 체크 설정",
                "유지보수 프로세스 구축",
            ],
            "deliverables": [
                "품질 게이트 자동화",
                "CI/CD 파이프라인 개선",
                "기술 부채 모니터링 대시보드",
            ],
            "success_criteria": [
                "모든 기술 부채 KPI 목표 달성",
                "자동화된 품질 체크 동작",
                "지속적인 부채 관리 체계 구축",
            ],
        }

        timeline = {
            "total_duration": "7-8 weeks",
            "weekly_timeline": weekly_timeline,
            "resource_requirements": {
                "developers": "1-2 developers",
                "devops": "0.5 DevOps engineer",
                "documentation": "0.5 Technical writer",
            },
            "success_metrics": {
                "code_duplication_reduction": "> 80%",
                "test_coverage_increase": "> 90%",
                "file_organization_score": "> 95%",
                "documentation_coverage": "> 50%",
                "naming_convention_compliance": "> 95%",
            },
        }

        return timeline

    def generate_technical_debt_report(self) -> Dict[str, Any]:
        """종합 기술 부채 보고서 생성"""

        logger.info("Scanning file system...")
        file_inventory = self.scan_file_system()

        logger.info("Identifying technical debts...")
        technical_debts = self.identify_technical_debts(file_inventory)

        logger.info("Creating cleanup actions...")
        cleanup_actions = self.create_cleanup_actions(file_inventory)

        logger.info("Generating naming standardization plan...")
        naming_plan = self.generate_naming_standardization_plan(file_inventory)

        logger.info("Creating documentation sync plan...")
        doc_sync_plan = self.create_documentation_sync_plan(file_inventory)

        logger.info("Generating implementation timeline...")
        timeline = self.generate_implementation_timeline(
            technical_debts, cleanup_actions
        )

        # 우선순위별 통계
        debt_by_priority = {1: 0, 2: 0, 3: 0, 4: 0}
        debt_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for debt in technical_debts:
            debt_by_priority[debt.priority] += 1
            debt_by_severity[debt.severity] += 1

        report = {
            "report_metadata": {
                "title": "DSV SHPT Technical Debt Management Report",
                "generated_at": datetime.now().isoformat(),
                "manager_version": "1.0.0",
                "scope": "Comprehensive technical debt resolution plan",
            },
            "executive_summary": {
                "total_technical_debts": len(technical_debts),
                "cleanup_actions_required": len(cleanup_actions),
                "estimated_resolution_time": timeline["total_duration"],
                "priority_distribution": debt_by_priority,
                "severity_distribution": debt_by_severity,
                "key_areas": [
                    "코드 중복 685개 블록 해결",
                    "테스트 커버리지 0% → 90% 향상",
                    "파일 구조 정리 및 네이밍 표준화",
                    "문서화 체계 구축",
                ],
            },
            "file_system_analysis": {
                "total_files": {
                    "python": len(file_inventory["all_python_files"]),
                    "documentation": len(file_inventory["documentation_files"]),
                    "configuration": len(file_inventory["config_files"]),
                    "results": len(file_inventory["result_files"]),
                },
                "file_categories": {
                    "backup_files": len(file_inventory["backup_files"]),
                    "test_files": len(file_inventory["test_files"]),
                    "temp_files": len(file_inventory["temp_files"]),
                },
            },
            "technical_debts": [asdict(debt) for debt in technical_debts],
            "cleanup_actions": [asdict(action) for action in cleanup_actions],
            "naming_standardization": naming_plan,
            "documentation_sync": doc_sync_plan,
            "implementation_timeline": timeline,
        }

        return report

    def save_debt_management_plan(self, output_dir: str = "out") -> str:
        """기술 부채 관리 계획 저장"""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 종합 보고서 생성
        report = self.generate_technical_debt_report()

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"technical_debt_management_plan_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Excel 저장 (상세 계획)
        excel_path = output_path / f"technical_debt_action_plan_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # 기술 부채 목록
            debt_data = []
            for debt in report["technical_debts"]:
                debt_data.append(
                    {
                        "Debt_ID": debt["debt_id"],
                        "Category": debt["category"],
                        "Description": debt["description"],
                        "Severity": debt["severity"],
                        "Priority": debt["priority"],
                        "Estimated_Effort": debt["estimated_effort"],
                        "Risk_If_Not_Resolved": debt["risk_if_not_resolved"],
                    }
                )

            if debt_data:
                debt_df = pd.DataFrame(debt_data)
                debt_df.to_excel(writer, sheet_name="Technical_Debts", index=False)

            # 정리 작업
            cleanup_data = []
            for action in report["cleanup_actions"]:
                cleanup_data.append(
                    {
                        "Action_ID": action["action_id"],
                        "Action_Type": action["action_type"],
                        "Description": action["description"],
                        "Automated": action["automated"],
                        "Target_Files_Count": len(action["target_files"]),
                    }
                )

            if cleanup_data:
                cleanup_df = pd.DataFrame(cleanup_data)
                cleanup_df.to_excel(writer, sheet_name="Cleanup_Actions", index=False)

            # 주차별 타임라인
            timeline_data = []
            for week, plan in report["implementation_timeline"][
                "weekly_timeline"
            ].items():
                timeline_data.append(
                    {
                        "Week": week,
                        "Focus": plan["focus"],
                        "Tasks_Count": len(plan["tasks"]),
                        "Deliverables_Count": len(plan["deliverables"]),
                        "Success_Criteria_Count": len(plan["success_criteria"]),
                    }
                )

            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                timeline_df.to_excel(
                    writer, sheet_name="Implementation_Timeline", index=False
                )

        logger.info(f"Technical debt management plan completed:")
        logger.info(f"  JSON Report: {json_path}")
        logger.info(f"  Excel Action Plan: {excel_path}")

        return str(json_path)


def main():
    """메인 실행 함수"""

    manager = TechnicalDebtManager()
    report_path = manager.save_debt_management_plan()

    # 결과 요약 출력
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("\n" + "=" * 80)
    print("DSV SHPT Technical Debt Management Plan 완료")
    print("=" * 80)

    summary = report["executive_summary"]
    print(f"\n총 기술 부채: {summary['total_technical_debts']}개")
    print(f"필요 정리 작업: {summary['cleanup_actions_required']}개")
    print(f"예상 해결 기간: {summary['estimated_resolution_time']}")

    print(f"\n우선순위 분포:")
    for priority, count in summary["priority_distribution"].items():
        print(f"  Priority {priority}: {count}개")

    print(f"\n심각도 분포:")
    for severity, count in summary["severity_distribution"].items():
        print(f"  {severity}: {count}개")

    print(f"\n주요 해결 영역:")
    for area in summary["key_areas"]:
        print(f"  - {area}")

    # 파일 시스템 현황
    file_stats = report["file_system_analysis"]
    print(f"\n파일 시스템 현황:")
    print(f"  Python 파일: {file_stats['total_files']['python']}개")
    print(f"  문서 파일: {file_stats['total_files']['documentation']}개")
    print(f"  백업 파일: {file_stats['file_categories']['backup_files']}개")
    print(f"  임시 파일: {file_stats['file_categories']['temp_files']}개")

    print(f"\n상세 관리 계획: {report_path}")

    return report


if __name__ == "__main__":
    main()
