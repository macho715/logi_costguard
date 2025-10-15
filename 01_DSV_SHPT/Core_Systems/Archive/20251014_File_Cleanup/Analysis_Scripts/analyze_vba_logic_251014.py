#!/usr/bin/env python3
"""
VBA Business Logic Analyzer
VBA 파일에서 비즈니스 로직만 추출 (formatting 제외)

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime


class VBALogicAnalyzer:
    """VBA 비즈니스 로직 분석기 (formatting 제외)"""

    def __init__(self, vba_dir: Path):
        self.vba_dir = vba_dir
        self.formatting_patterns = [
            r"\.ColumnWidth\s*=",
            r"\.RowHeight\s*=",
            r"\.HorizontalAlignment\s*=",
            r"\.VerticalAlignment\s*=",
            r"\.Font\.",
            r"\.Interior\.",
            r"\.Color\s*=",
            r"\.Borders\.",
            r"\.NumberFormat\s*=",
            r"\.WrapText\s*=",
            r"\.ShrinkToFit\s*=",
            r"\.Bold\s*=",
            r"\.Italic\s*=",
        ]

    def is_formatting_line(self, line: str) -> bool:
        """formatting 관련 라인인지 확인"""
        line_stripped = line.strip()
        for pattern in self.formatting_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return True
        return False

    def parse_vba_file(self, file_path: Path) -> Dict[str, Any]:
        """VBA 파일 파싱 (한글 인코딩 처리)"""

        encodings = ["utf-8", "cp949", "euc-kr", "latin1"]
        content = None

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            return {"error": f"Could not decode {file_path.name}"}

        lines = content.split("\n")

        # 프로시저 추출
        procedures = []
        current_proc = None
        current_lines = []

        for i, line in enumerate(lines, 1):
            # 프로시저 시작
            if re.match(r"^\s*(Public|Private)?\s*(Sub|Function)", line, re.IGNORECASE):
                if current_proc:
                    procedures.append(
                        {
                            "name": current_proc,
                            "lines": current_lines,
                            "start_line": (
                                current_lines[0]["line_num"] if current_lines else i
                            ),
                        }
                    )

                match = re.search(r"(Sub|Function)\s+(\w+)", line, re.IGNORECASE)
                current_proc = match.group(2) if match else "Unknown"
                current_lines = []

            # 프로시저 종료
            elif re.match(r"^\s*End\s+(Sub|Function)", line, re.IGNORECASE):
                if current_proc:
                    current_lines.append(
                        {"line_num": i, "content": line, "is_formatting": False}
                    )
                    procedures.append(
                        {
                            "name": current_proc,
                            "lines": current_lines,
                            "start_line": (
                                current_lines[0]["line_num"] if current_lines else i
                            ),
                        }
                    )
                    current_proc = None
                    current_lines = []

            # 프로시저 내부
            elif current_proc:
                is_fmt = self.is_formatting_line(line)
                current_lines.append(
                    {"line_num": i, "content": line, "is_formatting": is_fmt}
                )

        return {
            "file_name": file_path.name,
            "total_lines": len(lines),
            "procedures": procedures,
            "encoding_used": encoding if content else None,
        }

    def extract_business_logic(self, proc_data: Dict) -> Dict[str, Any]:
        """비즈니스 로직만 추출 (formatting 제외)"""

        business_lines = []
        formatting_lines = []

        for line_data in proc_data["lines"]:
            if line_data["is_formatting"]:
                formatting_lines.append(line_data)
            else:
                # 공백/주석 제외
                content = line_data["content"].strip()
                if content and not content.startswith("'"):
                    business_lines.append(line_data)

        return {
            "procedure_name": proc_data["name"],
            "business_logic_lines": len(business_lines),
            "formatting_lines": len(formatting_lines),
            "business_logic": business_lines,
            "total_lines": len(proc_data["lines"]),
        }

    def analyze_procedure_calls(
        self, parsed_files: Dict[str, Dict]
    ) -> Dict[str, List[str]]:
        """프로시저 호출 관계 매핑"""

        call_graph = {}

        for file_name, file_data in parsed_files.items():
            if "error" in file_data:
                continue

            for proc in file_data["procedures"]:
                proc_name = proc["name"]
                calls = []

                for line_data in proc["lines"]:
                    content = line_data["content"]
                    # Application.Run, Call, 직접 호출 패턴
                    match = re.search(
                        r'(Application\.Run|Call)\s+"?(\w+)"?', content, re.IGNORECASE
                    )
                    if match:
                        calls.append(match.group(2))
                    else:
                        # 직접 호출 패턴 (함수명만)
                        for other_file_data in parsed_files.values():
                            if "procedures" in other_file_data:
                                for other_proc in other_file_data["procedures"]:
                                    if (
                                        other_proc["name"] in content
                                        and other_proc["name"] != proc_name
                                    ):
                                        calls.append(other_proc["name"])

                call_graph[f"{file_name}::{proc_name}"] = list(set(calls))

        return call_graph

    def analyze_master_generation(
        self, parsed_files: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Master 시트 생성 로직 상세 분석"""

        compile_master = parsed_files.get("modCompileMaster.bas", {})
        if "error" in compile_master:
            return {"error": "modCompileMaster.bas not found or error"}

        master_logic = {
            "sheet_creation": [],
            "header_definition": [],
            "data_collection": [],
            "sheet_iteration": [],
            "key_variables": [],
        }

        for proc in compile_master["procedures"]:
            for line_data in proc["lines"]:
                content = line_data["content"].strip()

                # MasterData 시트 생성
                if "MasterData" in content and (
                    "Add" in content or "Worksheets" in content
                ):
                    master_logic["sheet_creation"].append(
                        {"line": line_data["line_num"], "content": content}
                    )

                # 헤더 정의
                if "headers" in content.lower() or "Array(" in content:
                    master_logic["header_definition"].append(
                        {"line": line_data["line_num"], "content": content}
                    )

                # 데이터 수집 로직
                if "For Each" in content and "Worksheet" in content:
                    master_logic["sheet_iteration"].append(
                        {"line": line_data["line_num"], "content": content}
                    )

                # 변수 선언
                if "Dim " in content:
                    master_logic["key_variables"].append(
                        {"line": line_data["line_num"], "content": content}
                    )

        return master_logic

    def generate_report(
        self, parsed_files: Dict[str, Dict], call_graph: Dict, master_logic: Dict
    ) -> str:
        """분석 보고서 생성"""

        report = []
        report.append("=" * 80)
        report.append("VBA Business Logic Analysis Report")
        report.append("=" * 80)

        # 파일별 요약
        report.append("\n[FILE SUMMARY]")
        for file_name, file_data in parsed_files.items():
            if "error" in file_data:
                report.append(f"\n{file_name}: ERROR - {file_data['error']}")
                continue

            proc_count = len(file_data["procedures"])
            total_lines = file_data["total_lines"]

            report.append(f"\n{file_name}:")
            report.append(f"  Total Lines: {total_lines}")
            report.append(f"  Procedures: {proc_count}")

            for proc in file_data["procedures"]:
                logic = self.extract_business_logic(proc)
                report.append(f"    - {logic['procedure_name']}:")
                report.append(
                    f"        Business Logic: {logic['business_logic_lines']} lines"
                )
                report.append(
                    f"        Formatting: {logic['formatting_lines']} lines (excluded)"
                )

        # 프로시저 호출 관계
        report.append("\n[PROCEDURE CALL GRAPH]")
        for proc, calls in sorted(call_graph.items()):
            if calls:
                report.append(f"\n{proc} calls:")
                for call in calls:
                    report.append(f"  -> {call}")

        # Master 생성 로직
        report.append("\n[MASTER SHEET GENERATION LOGIC]")
        report.append("\nSheet Creation:")
        for item in master_logic.get("sheet_creation", []):
            report.append(f"  Line {item['line']}: {item['content']}")

        report.append("\nHeader Definition:")
        for item in master_logic.get("header_definition", [])[:3]:
            report.append(f"  Line {item['line']}: {item['content'][:80]}...")

        report.append("\nSheet Iteration:")
        for item in master_logic.get("sheet_iteration", []):
            report.append(f"  Line {item['line']}: {item['content']}")

        return "\n".join(report)


def main():
    """메인 실행 함수"""

    vba_dir = Path(__file__).parent.parent / "VBA"

    if not vba_dir.exists():
        print(f"[ERROR] VBA directory not found: {vba_dir}")
        return

    print(f"[INFO] Analyzing VBA files in: {vba_dir}")

    analyzer = VBALogicAnalyzer(vba_dir)

    # 모든 VBA 파일 파싱
    parsed_files = {}
    for vba_file in vba_dir.glob("*.bas"):
        print(f"  Parsing: {vba_file.name}")
        parsed_files[vba_file.name] = analyzer.parse_vba_file(vba_file)

    # 프로시저 호출 관계 분석
    call_graph = analyzer.analyze_procedure_calls(parsed_files)

    # Master 생성 로직 분석
    master_logic = analyzer.analyze_master_generation(parsed_files)

    # 보고서 생성
    report = analyzer.generate_report(parsed_files, call_graph, master_logic)
    print("\n" + report)

    # JSON 저장
    output_dir = Path(__file__).parent / "out"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 파싱 결과 저장
    json_path = output_dir / f"vba_logic_analysis_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "parsed_files": parsed_files,
                "call_graph": call_graph,
                "master_logic": master_logic,
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print(f"\n[SAVED] Analysis saved to: {json_path}")

    # 텍스트 보고서 저장
    report_path = output_dir / f"vba_logic_report_{timestamp}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[SAVED] Report saved to: {report_path}")


if __name__ == "__main__":
    main()
