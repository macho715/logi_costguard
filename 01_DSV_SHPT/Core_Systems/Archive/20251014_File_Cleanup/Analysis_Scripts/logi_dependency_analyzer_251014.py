#!/usr/bin/env python3
"""
MACHO-GPT Dependency Analyzer for DSV SHPT System
의존성 매트릭스 생성기 및 기능 중복도 분석 도구

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import ast
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import logging
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LogiDependencyAnalyzer:
    """DSV SHPT 시스템 의존성 및 중복도 분석기"""

    def __init__(self, core_systems_path: str):
        self.core_systems_path = Path(core_systems_path)
        self.python_files = list(self.core_systems_path.glob("*.py"))

        # 분석 결과 저장
        self.modules_info = {}
        self.dependency_matrix = {}
        self.function_inventory = {}
        self.duplication_analysis = {}

        # 키워드 분류 시스템
        self.function_categories = {
            "audit": ["audit", "validate", "check", "verify", "review"],
            "excel": ["excel", "sheet", "workbook", "xlsx", "xlsm", "cell"],
            "vba": ["vba", "macro", "formula", "compile"],
            "pdf": ["pdf", "parse", "extract", "document"],
            "report": ["report", "generate", "create", "output", "export"],
            "data": ["data", "process", "clean", "normalize", "transform"],
            "config": ["config", "setting", "parameter", "setup"],
            "test": ["test", "unit", "integration", "mock"],
        }

    def analyze_file_imports(self, file_path: Path) -> Dict[str, List[str]]:
        """파일의 import 구문 분석"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            imports = {
                "standard_library": [],
                "third_party": [],
                "local_modules": [],
                "relative_imports": [],
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports["standard_library"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.level > 0:  # 상대 import
                            imports["relative_imports"].append(node.module or "")
                        elif node.module in [
                            "pandas",
                            "numpy",
                            "json",
                            "pathlib",
                            "openpyxl",
                        ]:
                            imports["third_party"].append(node.module)
                        else:
                            imports["local_modules"].append(node.module)

            return imports

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {
                "standard_library": [],
                "third_party": [],
                "local_modules": [],
                "relative_imports": [],
            }

    def extract_classes_and_functions(self, file_path: Path) -> Dict[str, List[str]]:
        """클래스와 함수 정의 추출"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)

            return {"classes": classes, "functions": functions}

        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return {"classes": [], "functions": []}

    def categorize_functions(self, functions: List[str]) -> Dict[str, List[str]]:
        """함수를 기능별로 분류"""
        categorized = {category: [] for category in self.function_categories.keys()}
        uncategorized = []

        for func in functions:
            func_lower = func.lower()
            categorized_flag = False

            for category, keywords in self.function_categories.items():
                if any(keyword in func_lower for keyword in keywords):
                    categorized[category].append(func)
                    categorized_flag = True
                    break

            if not categorized_flag:
                uncategorized.append(func)

        categorized["uncategorized"] = uncategorized
        return categorized

    def analyze_all_modules(self):
        """모든 모듈 분석 실행"""
        logger.info(f"Analyzing {len(self.python_files)} Python files in Core_Systems")

        for file_path in self.python_files:
            if file_path.name.startswith("__"):
                continue

            logger.info(f"Analyzing: {file_path.name}")

            # 기본 정보
            module_info = {
                "file_path": str(file_path),
                "file_size_kb": file_path.stat().st_size / 1024,
                "lines_of_code": len(
                    file_path.read_text(encoding="utf-8").splitlines()
                ),
            }

            # Import 분석
            module_info["imports"] = self.analyze_file_imports(file_path)

            # 클래스/함수 추출
            code_elements = self.extract_classes_and_functions(file_path)
            module_info.update(code_elements)

            # 함수 분류
            module_info["function_categories"] = self.categorize_functions(
                code_elements["functions"]
            )

            self.modules_info[file_path.name] = module_info

    def build_dependency_matrix(self) -> pd.DataFrame:
        """의존성 매트릭스 생성"""
        files = list(self.modules_info.keys())
        matrix = pd.DataFrame(0, index=files, columns=files)

        for file_name, info in self.modules_info.items():
            local_modules = info["imports"]["local_modules"]

            for target_file in files:
                target_stem = target_file.replace(".py", "")

                # 직접 import 확인
                if any(target_stem in module for module in local_modules):
                    matrix.loc[file_name, target_file] = 1

                # 클래스/함수명 기반 의존성 추정
                target_info = self.modules_info[target_file]
                for class_name in target_info["classes"]:
                    if class_name in str(info):
                        matrix.loc[file_name, target_file] = 1

        return matrix

    def analyze_function_duplication(self) -> Dict[str, Any]:
        """함수 중복도 분석"""
        all_functions = {}

        # 모든 함수 수집
        for file_name, info in self.modules_info.items():
            for func in info["functions"]:
                if func not in all_functions:
                    all_functions[func] = []
                all_functions[func].append(file_name)

        # 중복 함수 식별
        duplicated = {
            func: files for func, files in all_functions.items() if len(files) > 1
        }

        # 기능별 중복 분석
        category_overlap = {}
        for category in self.function_categories.keys():
            category_functions = {}
            for file_name, info in self.modules_info.items():
                cat_funcs = info["function_categories"].get(category, [])
                if cat_funcs:
                    category_functions[file_name] = cat_funcs

            # 카테고리 내 중복 계산
            if len(category_functions) > 1:
                overlap_score = self._calculate_category_overlap(category_functions)
                category_overlap[category] = overlap_score

        return {
            "total_unique_functions": len(all_functions),
            "duplicated_functions": duplicated,
            "duplication_count": len(duplicated),
            "category_overlap_scores": category_overlap,
        }

    def _calculate_category_overlap(
        self, category_functions: Dict[str, List[str]]
    ) -> float:
        """카테고리별 중복도 점수 계산"""
        files = list(category_functions.keys())
        total_pairs = 0
        overlap_pairs = 0

        for i, file1 in enumerate(files):
            for file2 in files[i + 1 :]:
                total_pairs += 1
                funcs1 = set(category_functions[file1])
                funcs2 = set(category_functions[file2])

                if funcs1.intersection(funcs2):
                    overlap_pairs += 1

        return overlap_pairs / total_pairs if total_pairs > 0 else 0.0

    def generate_architecture_report(self) -> Dict[str, Any]:
        """아키텍처 분석 보고서 생성"""

        # 의존성 매트릭스 생성
        dep_matrix = self.build_dependency_matrix()

        # 중복도 분석
        duplication = self.analyze_function_duplication()

        # 복잡도 메트릭
        complexity_metrics = {}
        for file_name, info in self.modules_info.items():
            complexity_metrics[file_name] = {
                "lines_of_code": info["lines_of_code"],
                "num_classes": len(info["classes"]),
                "num_functions": len(info["functions"]),
                "import_count": sum(
                    len(imp_list) for imp_list in info["imports"].values()
                ),
                "complexity_score": info["lines_of_code"] / 100
                + len(info["functions"]) / 10,
            }

        # 핵심 모듈 식별 (의존성 높은 모듈)
        dependency_scores = dep_matrix.sum(axis=0).sort_values(ascending=False)
        core_modules = dependency_scores.head(5).to_dict()

        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_modules": len(self.modules_info),
            "dependency_matrix": dep_matrix.to_dict(),
            "duplication_analysis": duplication,
            "complexity_metrics": complexity_metrics,
            "core_modules": core_modules,
            "recommendations": self._generate_recommendations(
                duplication, complexity_metrics
            ),
        }

        return report

    def _generate_recommendations(
        self, duplication: Dict, complexity: Dict
    ) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []

        # 중복도가 높은 경우
        if duplication["duplication_count"] > 10:
            recommendations.append(
                f"HIGH_DUPLICATION: {duplication['duplication_count']}개 중복 함수 발견. "
                "공통 모듈로 리팩터링 필요."
            )

        # 복잡도가 높은 파일들
        complex_files = [
            name
            for name, metrics in complexity.items()
            if metrics["complexity_score"] > 50
        ]
        if complex_files:
            recommendations.append(
                f"HIGH_COMPLEXITY: {len(complex_files)}개 파일이 고복잡도. "
                f"분할 검토 필요: {', '.join(complex_files[:3])}"
            )

        # VBA 통합 개선
        vba_files = [name for name in self.modules_info.keys() if "vba" in name.lower()]
        if len(vba_files) > 3:
            recommendations.append(
                f"VBA_CONSOLIDATION: {len(vba_files)}개 VBA 모듈 통합 검토 필요."
            )

        return recommendations

    def save_results(self, output_dir: str = "out"):
        """분석 결과 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 전체 보고서 생성
        report = self.generate_architecture_report()

        # JSON 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"logi_dependency_analysis_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Excel 저장
        excel_path = output_path / f"logi_dependency_matrix_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # 의존성 매트릭스
            dep_df = pd.DataFrame(report["dependency_matrix"])
            dep_df.to_excel(writer, sheet_name="Dependency_Matrix")

            # 복잡도 메트릭
            complexity_df = pd.DataFrame(report["complexity_metrics"]).T
            complexity_df.to_excel(writer, sheet_name="Complexity_Metrics")

            # 중복 함수 목록
            if report["duplication_analysis"]["duplicated_functions"]:
                dup_data = []
                for func, files in report["duplication_analysis"][
                    "duplicated_functions"
                ].items():
                    dup_data.append(
                        {
                            "Function": func,
                            "Files": ", ".join(files),
                            "Count": len(files),
                        }
                    )
                dup_df = pd.DataFrame(dup_data)
                dup_df.to_excel(writer, sheet_name="Duplicated_Functions", index=False)

        logger.info(f"Analysis results saved to:")
        logger.info(f"  JSON: {json_path}")
        logger.info(f"  Excel: {excel_path}")

        return report


def main():
    """메인 실행 함수"""
    current_dir = Path(__file__).parent

    analyzer = LogiDependencyAnalyzer(current_dir)
    analyzer.analyze_all_modules()

    report = analyzer.save_results()

    print("\n" + "=" * 60)
    print("DSV SHPT 시스템 의존성 분석 완료")
    print("=" * 60)
    print(f"총 분석 모듈: {report['total_modules']}개")
    print(f"중복 함수: {report['duplication_analysis']['duplication_count']}개")
    print(f"핵심 모듈 (의존성 상위 3개):")

    for i, (module, score) in enumerate(list(report["core_modules"].items())[:3], 1):
        print(f"  {i}. {module}: {score}개 의존성")

    print(f"\n권장사항 ({len(report['recommendations'])}개):")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")

    return report


if __name__ == "__main__":
    main()
