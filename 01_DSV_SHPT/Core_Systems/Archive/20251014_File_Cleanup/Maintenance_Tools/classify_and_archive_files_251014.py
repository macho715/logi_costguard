#!/usr/bin/env python3
"""
파일 분류 및 Archive 이동 자동화
"""

import shutil
from pathlib import Path
from datetime import datetime


class FileClassifier:
    """파일 분류 및 Archive 관리"""

    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.archive_base = root_dir / "Archive" / "20251014_File_Cleanup"

        # 핵심 파일 (KEEP)
        self.core_files = {
            # 메인 검증 시스템
            "validate_masterdata_with_config_251014.py",
            "invoice_pdf_integration.py",
            "generate_final_report_pandas_251014.py",
            "shpt_audit_system.py",
            "shpt_sept_2025_enhanced_audit.py",
            "excel_data_processor.py",
            "run_full_validation_with_config_251014.py",
            # 유지보수 도구
            "fix_hardcoded_paths_251014.py",
            "analyze_hardcoding_251014.py",
            "hardcoding_analysis_report_251014.json",
        }

        # Archive 카테고리
        self.archive_categories = {
            "Analysis_Scripts": ["analyze_", "logi_", "show_final_fails"],
            "Debug_Scripts": ["debug_", "check_", "trace_"],
            "Test_Scripts": ["test_", "verify_", "compare_"],
            "Backup_Files": [
                "_backup",
                "comprehensive_invoice_validator",
                "create_enhanced_excel_report.py",
                "create_excel_report.py",
                "generate_comprehensive_excel_report.py",
                "generate_final_excel_report.py",
            ],
            "Other_Scripts": [
                "run_comprehensive_validation",
                "run_shpt_sept2025",
                "find_transportation_rates",
                "insert_validation_to_original",
            ],
        }

    def classify_file(self, file_path: Path) -> str:
        """파일 분류 (KEEP/ARCHIVE)"""

        file_name = file_path.name

        # 핵심 파일
        if file_name in self.core_files:
            return "KEEP"

        # Archive 카테고리 확인
        for category, patterns in self.archive_categories.items():
            for pattern in patterns:
                if pattern in file_name:
                    return f"ARCHIVE:{category}"

        # 기본값: KEEP (보수적)
        return "KEEP"

    def create_archive_structure(self):
        """Archive 디렉토리 구조 생성"""

        self.archive_base.mkdir(parents=True, exist_ok=True)

        for category in self.archive_categories.keys():
            (self.archive_base / category).mkdir(exist_ok=True)

        print(f"[OK] Archive structure created: {self.archive_base}")

    def move_to_archive(self, file_path: Path, category: str):
        """파일을 Archive로 이동"""

        target_dir = self.archive_base / category
        target_path = target_dir / file_path.name

        try:
            shutil.move(str(file_path), str(target_path))
            return True
        except Exception as e:
            print(f"[ERROR] Failed to move {file_path.name}: {e}")
            return False

    def generate_report(self, classification: dict) -> dict:
        """분류 결과 보고서 생성"""

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "details": classification,
        }

        # Summary
        for status, files in classification.items():
            report["summary"][status] = len(files)

        return report


# Main execution
if __name__ == "__main__":
    root = Path(__file__).parent
    classifier = FileClassifier(root)

    print("=" * 100)
    print("파일 분류 및 Archive 이동")
    print("=" * 100)

    # Step 1: 파일 분류
    print("\n[Step 1] 파일 분류 중...")

    py_files = [f for f in root.glob("*.py") if f.is_file()]
    json_files = [f for f in root.glob("*.json") if f.is_file()]
    md_files = [f for f in root.glob("*.md") if f.is_file()]

    all_files = py_files + json_files + md_files

    classification = {}
    for file_path in all_files:
        status = classifier.classify_file(file_path)
        if status not in classification:
            classification[status] = []
        classification[status].append(file_path)

    # 결과 출력
    print(f"\n총 {len(all_files)}개 파일 분류 완료:")
    for status, files in sorted(classification.items()):
        print(f"  {status}: {len(files)}개")

    # KEEP 파일 목록
    print("\n" + "=" * 100)
    print("KEEP (유지할 파일)")
    print("=" * 100)
    keep_files = classification.get("KEEP", [])
    for f in sorted(keep_files):
        print(f"  [KEEP] {f.name}")

    # ARCHIVE 파일 목록 (카테고리별)
    print("\n" + "=" * 100)
    print("ARCHIVE (이동할 파일)")
    print("=" * 100)

    archive_count = 0
    for status, files in sorted(classification.items()):
        if status.startswith("ARCHIVE:"):
            category = status.split(":")[1]
            print(f"\n{category} ({len(files)}개):")
            for f in sorted(files)[:5]:  # 처음 5개만 표시
                print(f"  [ARCHIVE] {f.name}")
            if len(files) > 5:
                print(f"  ... 외 {len(files)-5}개")
            archive_count += len(files)

    print(f"\n총 Archive 대상: {archive_count}개")

    # Step 2: Archive 디렉토리 생성
    print("\n" + "=" * 100)
    print("[Step 2] Archive 디렉토리 생성")
    print("=" * 100)

    classifier.create_archive_structure()

    # Step 3: 파일 이동
    print("\n" + "=" * 100)
    print("[Step 3] 파일 이동 실행")
    print("=" * 100)

    moved_count = 0
    failed_count = 0

    for status, files in classification.items():
        if status.startswith("ARCHIVE:"):
            category = status.split(":")[1]
            print(f"\n{category}:")

            for file_path in files:
                success = classifier.move_to_archive(file_path, category)
                if success:
                    print(f"  [OK] {file_path.name}")
                    moved_count += 1
                else:
                    print(f"  [FAIL] {file_path.name}")
                    failed_count += 1

    # 결과
    print("\n" + "=" * 100)
    print("[완료] 파일 이동 완료")
    print("=" * 100)

    print(f"\n이동 성공: {moved_count}개")
    print(f"이동 실패: {failed_count}개")
    print(f"유지: {len(keep_files)}개")

    print(f"\nArchive 위치: {classifier.archive_base}")

    # 보고서 저장
    report = classifier.generate_report(classification)
    report_file = root / "file_cleanup_report_251014.json"

    import json

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[SAVED] {report_file}")
