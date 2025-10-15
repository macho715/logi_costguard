#!/usr/bin/env python3
"""
Root 및 Documentation 디렉토리 정리
"""

import shutil
from pathlib import Path

root = Path(__file__).parent
archive_base = root / "Archive" / "20251014_File_Cleanup"

# Root MD 파일 정리
print("=" * 100)
print("Root 디렉토리 MD 파일 정리")
print("=" * 100)

root_keep = [
    "README.md",
    "SYSTEM_REUSABILITY_ASSESSMENT_251014.md",
    "HARDCODING_REMOVAL_COMPLETE_251014.md",
    "PATCH.MD",  # 추가 유지
]

root_archive = [
    "COMPREHENSIVE_SYSTEM_ANALYSIS_SUMMARY.md",
    "CONTRACT_INTEGRATION_COMPLETE_REPORT.md",
    "FINAL_VALIDATION_COMPLETE_REPORT.md",
    "FIXED_RATES_INTEGRATION_COMPLETE_REPORT_251014.md",
    "IMPLEMENTATION_COMPLETE_SUMMARY_251014.md",
    "PDF_INTEGRATION_CENTRALIZATION_COMPLETE_251014.md",
    "SEPT_SHEET_ANALYSIS_REPORT_251014.md",
    "SYSTEM_ENHANCEMENT_SUMMARY.md",
    "VALIDATION_ISSUES_DETAIL_REPORT_251014.md",
]

# Archive 디렉토리 생성
intermediate_reports_dir = archive_base / "Intermediate_Reports"
intermediate_reports_dir.mkdir(parents=True, exist_ok=True)

print(f"\n[KEEP] Root MD 파일 ({len(root_keep)}개):")
for f in root_keep:
    if (root / f).exists():
        print(f"  [KEEP] {f}")

print(f"\n[ARCHIVE] Root MD 파일 ({len(root_archive)}개):")
moved_root = 0
for f in root_archive:
    src = root / f
    if src.exists():
        dst = intermediate_reports_dir / f
        try:
            shutil.move(str(src), str(dst))
            print(f"  [OK] {f}")
            moved_root += 1
        except Exception as e:
            print(f"  [FAIL] {f}: {e}")
    else:
        print(f"  [SKIP] {f} - not found")

# Documentation 정리
print("\n" + "=" * 100)
print("Documentation 디렉토리 정리")
print("=" * 100)

doc_dir = root / "Documentation"
doc_keep = ["USER_GUIDE.md", "CONFIGURATION_GUIDE.md", "SYSTEM_ARCHITECTURE_FINAL.md"]

doc_archive = [
    "CONTRACT_ANALYSIS_SUMMARY.md",
    "PDF_INTEGRATION_COMPLETE_REPORT_INDEX.md",
    "PDF_INTEGRATION_COMPLETE_REPORT_PART1_OVERVIEW.md",
    "PDF_INTEGRATION_COMPLETE_REPORT_PART2_ALGORITHMS.md",
    "PDF_INTEGRATION_COMPLETE_REPORT_PART3_IMPLEMENTATION.md",
    "PDF_INTEGRATION_COMPLETE_REPORT_PART4_ARCHITECTURE.md",
    "PDF_INTEGRATION_GUIDE.md",
    "SHPT_SYSTEM_UPDATE_SUMMARY.md",
]

doc_archive_dir = intermediate_reports_dir / "Documentation"
doc_archive_dir.mkdir(parents=True, exist_ok=True)

print(f"\n[KEEP] Documentation ({len(doc_keep)}개):")
for f in doc_keep:
    if (doc_dir / f).exists():
        print(f"  [KEEP] {f}")

print(f"\n[ARCHIVE] Documentation ({len(doc_archive)}개):")
moved_doc = 0
for f in doc_archive:
    src = doc_dir / f
    if src.exists():
        dst = doc_archive_dir / f
        try:
            shutil.move(str(src), str(dst))
            print(f"  [OK] {f}")
            moved_doc += 1
        except Exception as e:
            print(f"  [FAIL] {f}: {e}")
    else:
        print(f"  [SKIP] {f} - not found")

# Technical 디렉토리도 이동
tech_dir = doc_dir / "Technical"
if tech_dir.exists():
    tech_archive = doc_archive_dir / "Technical"
    try:
        shutil.move(str(tech_dir), str(tech_archive))
        print(f"  [OK] Technical/ directory")
        moved_doc += 1
    except Exception as e:
        print(f"  [FAIL] Technical/: {e}")

# 결과
print("\n" + "=" * 100)
print("[완료] Root 및 Documentation 정리 완료")
print("=" * 100)

print(f"\nRoot MD 파일:")
print(f"  이동: {moved_root}개")
print(f"  유지: {len(root_keep)}개")

print(f"\nDocumentation:")
print(f"  이동: {moved_doc}개")
print(f"  유지: {len(doc_keep)}개")

print(f"\n총 이동: {moved_root + moved_doc}개")
print(f"\nArchive 위치: {intermediate_reports_dir}")
