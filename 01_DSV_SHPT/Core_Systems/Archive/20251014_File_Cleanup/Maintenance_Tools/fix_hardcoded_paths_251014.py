#!/usr/bin/env python3
"""
하드코딩된 절대 경로를 상대 경로로 자동 수정
"""

import re
from pathlib import Path
import json

# Load hardcoding report
report_file = Path(__file__).parent / "hardcoding_analysis_report_251014.json"
with open(report_file, "r", encoding="utf-8") as f:
    report = json.load(f)

paths_to_fix = report["details"]["paths"]

print("=" * 100)
print("하드코딩 절대 경로 자동 수정")
print("=" * 100)

print(f"\n총 {len(paths_to_fix)}개 파일에서 절대 경로 발견")

# Group by file
files_with_paths = {}
for item in paths_to_fix:
    file_name = item["file"]
    if file_name not in files_with_paths:
        files_with_paths[file_name] = []
    files_with_paths[file_name].append(item["value"])

print(f"수정 필요 파일: {len(files_with_paths)}개")

for file_name, paths in files_with_paths.items():
    print(f"\n{file_name}:")
    for path in paths:
        print(f"  - {path[:80]}...")

print("\n" + "=" * 100)
print("자동 수정 시작")
print("=" * 100)


# Define replacement pattern
def create_relative_path_replacement(old_path: str, file_name: str) -> str:
    """절대 경로를 상대 경로로 변환"""

    # Common patterns
    if "SCNT SHIPMENT DRAFT INVOICE" in old_path:
        if "Data\\DSV 202509" in old_path:
            return 'Path(__file__).parent.parent / "Data" / "DSV 202509" / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"'
        else:
            return 'Path(__file__).parent / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"'

    if "Supporting Documents" in old_path:
        return 'Path(__file__).parent.parent / "SCNT Import (Sept 2025) - Supporting Documents"'

    if "Results" in old_path:
        return 'Path(__file__).parent.parent / "Results"'

    return None


# Apply fixes
fixed_count = 0
for file_name, paths in files_with_paths.items():
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        print(f"\n[SKIP] {file_name} - 파일 없음")
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        modified = False

        for old_path in paths:
            # Escape backslashes for regex
            escaped_path = old_path.replace("\\", "\\\\")

            # Find and replace
            if old_path in content:
                new_path = create_relative_path_replacement(old_path, file_name)
                if new_path:
                    # Replace string literal
                    content = content.replace(f'"{old_path}"', new_path)
                    content = content.replace(f"'{old_path}'", new_path)
                    modified = True

        if modified:
            # Add Path import if not present
            if (
                "from pathlib import Path" not in content
                and "import Path" not in content
            ):
                # Add import at the top
                lines = content.split("\n")
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        import_idx = i + 1

                lines.insert(import_idx, "from pathlib import Path")
                content = "\n".join(lines)

            # Save
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"\n[FIXED] {file_name}")
            print(f"  - {len([p for p in paths if p in original_content])}개 경로 수정")
            fixed_count += 1
        else:
            print(f"\n[NO CHANGE] {file_name}")

    except Exception as e:
        print(f"\n[ERROR] {file_name}: {e}")

print("\n" + "=" * 100)
print(f"[완료] {fixed_count}개 파일 수정 완료")
print("=" * 100)

print("\n다음 단계:")
print("  1. 수정된 파일 검증")
print("  2. Magic numbers 상수화")
print("  3. Sheet 이름 동적 로딩")
