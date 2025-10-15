#!/usr/bin/env python3
"""
Rate JSON 파일 검증 스크립트
HVDC Project - Rate Data Validation
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import sys


class RateJSONValidator:
    """Rate JSON 파일 검증"""

    def __init__(self, rate_dir: Path):
        self.rate_dir = rate_dir
        self.validation_results = {}

    def validate_all_files(self) -> Dict[str, Any]:
        """모든 JSON 파일 검증"""
        json_files = list(self.rate_dir.glob("*.json"))

        results = {
            "total_files": len(json_files),
            "files": {},
            "summary": {
                "total_records": 0,
                "valid_records": 0,
                "invalid_records": 0,
                "duplicates": 0,
            },
        }

        for json_file in json_files:
            file_result = self.validate_file(json_file)
            results["files"][json_file.name] = file_result

            # 요약 업데이트
            results["summary"]["total_records"] += file_result["total_records"]
            results["summary"]["valid_records"] += file_result["valid_records"]
            results["summary"]["invalid_records"] += file_result["invalid_records"]
            results["summary"]["duplicates"] += file_result["duplicates"]

        # 유효 비율 계산
        if results["summary"]["total_records"] > 0:
            results["summary"]["valid_rate"] = (
                results["summary"]["valid_records"]
                / results["summary"]["total_records"]
                * 100
            )

        self.validation_results = results
        return results

    def validate_file(self, json_file: Path) -> Dict[str, Any]:
        """개별 JSON 파일 검증"""
        result = {
            "file": json_file.name,
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "duplicates": 0,
            "issues": [],
        }

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 기본 구조 검증
            if "records" not in data:
                result["issues"].append("ERROR: 'records' 필드 누락")
                return result

            records = data["records"]
            result["total_records"] = len(records)

            # 중복 탐지용
            seen = set()

            # 각 레코드 검증
            for idx, record in enumerate(records):
                issues = self.validate_record(record, idx)

                if issues:
                    result["invalid_records"] += 1
                    result["issues"].extend(issues)
                else:
                    result["valid_records"] += 1

                # 중복 체크
                key = self.get_record_key(record)
                if key in seen:
                    result["duplicates"] += 1
                    result["issues"].append(f"DUPLICATE: Record #{idx} - {key}")
                seen.add(key)

        except json.JSONDecodeError as e:
            result["issues"].append(f"JSON_ERROR: {e}")
        except Exception as e:
            result["issues"].append(f"FILE_ERROR: {e}")

        return result

    def validate_record(self, record: Dict, idx: int) -> List[str]:
        """개별 레코드 검증"""
        issues = []

        # 필수 필드 검증
        required_fields = ["port", "description", "unit"]
        for field in required_fields:
            if field not in record or record[field] is None:
                issues.append(f"Record #{idx}: 필수 필드 '{field}' 누락")

        # Rate 필드 검증 (rate dict 또는 rates(usd))
        has_rate = False
        if "rate" in record and isinstance(record["rate"], dict):
            if "amount" in record["rate"]:
                rate_amount = record["rate"]["amount"]
                if not isinstance(rate_amount, (int, float)):
                    issues.append(
                        f"Record #{idx}: rate.amount는 숫자여야 함 (현재: {type(rate_amount)})"
                    )
                has_rate = True

                # Tolerance 검증
                if "tolerance" in record["rate"]:
                    tolerance = record["rate"]["tolerance"]
                    if tolerance != 0.03:
                        issues.append(
                            f"Record #{idx}: tolerance는 0.03이어야 함 (현재: {tolerance})"
                        )

        if "rates(usd)" in record:
            # At cost, Case by Case 등은 유효
            has_rate = True

        if not has_rate:
            issues.append(f"Record #{idx}: 'rate' 또는 'rates(usd)' 필드 누락")

        return issues

    def get_record_key(self, record: Dict) -> str:
        """레코드 고유 키 생성 (중복 탐지용)"""
        port = record.get("port", "")
        destination = record.get("destination", "")
        description = record.get("description", "")
        unit = record.get("unit", "")

        return f"{port}|{destination}|{description}|{unit}"

    def print_report(self):
        """검증 결과 리포트 출력"""
        if not self.validation_results:
            print("[WARNING] 검증 결과 없음. validate_all_files()를 먼저 실행하세요.")
            return

        print("=" * 80)
        print("Rate JSON File Validation Results")
        print("=" * 80)
        print()

        # 파일별 결과
        for filename, file_result in self.validation_results["files"].items():
            print(f"[FILE] {filename}")
            print(f"  Total Records: {file_result['total_records']}")
            print(f"  Valid: {file_result['valid_records']} [OK]")
            print(f"  Invalid: {file_result['invalid_records']} [ERROR]")
            print(f"  Duplicates: {file_result['duplicates']} [WARN]")

            if file_result["issues"]:
                print(f"  Issues ({len(file_result['issues'])}개):")
                for issue in file_result["issues"][:5]:  # 최대 5개만 표시
                    print(f"    - {issue}")
                if len(file_result["issues"]) > 5:
                    print(f"    ... 외 {len(file_result['issues']) - 5}개")
            print()

        # 전체 요약
        summary = self.validation_results["summary"]
        print("=" * 80)
        print("Overall Summary")
        print("=" * 80)
        print(f"Total Files: {self.validation_results['total_files']}")
        print(f"Total Records: {summary['total_records']}")
        print(
            f"Valid Records: {summary['valid_records']} ({summary.get('valid_rate', 0):.1f}%)"
        )
        print(f"Invalid Records: {summary['invalid_records']}")
        print(f"Duplicate Records: {summary['duplicates']}")
        print()

        # 품질 판정
        valid_rate = summary.get("valid_rate", 0)
        if valid_rate >= 95:
            print("[PASS] Quality Check PASS (>=95%)")
        elif valid_rate >= 90:
            print("[WARN] Quality Check WARN (90-95%)")
        else:
            print("[FAIL] Quality Check FAIL (<90%)")

        return self.validation_results


def main():
    """메인 실행 함수"""
    # Rate 폴더 경로
    script_dir = Path(__file__).parent
    rate_dir = script_dir.parent / "Rate"

    if not rate_dir.exists():
        print(f"[ERROR] Rate folder not found: {rate_dir}")
        sys.exit(1)

    # 검증 실행
    validator = RateJSONValidator(rate_dir)
    results = validator.validate_all_files()

    # 결과 출력
    validator.print_report()

    # JSON 저장
    output_file = script_dir / "rate_validation_report.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[SAVED] Detailed results: {output_file}")

    # 종료 코드 결정
    valid_rate = results["summary"].get("valid_rate", 0)
    if valid_rate < 95:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
