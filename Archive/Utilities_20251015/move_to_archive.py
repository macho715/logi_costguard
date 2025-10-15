#!/usr/bin/env python3
"""
Move Files to Archive
중복/레거시/백업 파일을 Archive 폴더로 이동
"""

import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows


def create_archive_structure(root_dir):
    """Archive 폴더 구조 생성"""
    timestamp = datetime.now().strftime("%Y%m%d")
    archive_root = root_dir / "Archive" / f"{timestamp}_Before_Cleanup"

    folders = [
        archive_root / "Duplicates",
        archive_root / "Legacy",
        archive_root / "Backups",
        archive_root / "Superseded",
        archive_root / "Old_Results",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    return archive_root


def move_file_safely(source, destination_dir, manifest):
    """파일을 안전하게 이동 (manifest 기록)"""
    source_path = Path(source)

    if not source_path.exists():
        print(f"  [SKIP] File not found: {source_path.name}")
        return False

    # Create destination with same relative structure
    dest_path = destination_dir / source_path.name

    # Handle name conflicts
    counter = 1
    original_dest = dest_path
    while dest_path.exists():
        stem = original_dest.stem
        suffix = original_dest.suffix
        dest_path = destination_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        shutil.move(str(source_path), str(dest_path))
        manifest.append(
            {
                "source": str(source_path),
                "destination": str(dest_path),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "size_kb": (
                    source_path.stat().st_size / 1024 if source_path.exists() else 0
                ),
            }
        )
        return True
    except Exception as e:
        print(f"  [ERROR] Cannot move {source_path.name}: {e}")
        return False


def main():
    print("=" * 80)
    print("Move Files to Archive")
    print("=" * 80)

    root_dir = Path(__file__).parent

    # Load analysis reports
    duplicate_file = root_dir / "DUPLICATE_ANALYSIS.xlsx"
    legacy_file = root_dir / "LEGACY_FILES_REPORT.xlsx"

    if not duplicate_file.exists():
        print("[ERROR] DUPLICATE_ANALYSIS.xlsx not found.")
        return

    if not legacy_file.exists():
        print("[ERROR] LEGACY_FILES_REPORT.xlsx not found.")
        return

    # Create archive structure
    print("\n[Step 1] Creating archive structure...")
    archive_root = create_archive_structure(root_dir)
    print(f"  Archive location: {archive_root}")

    # Movement manifest
    manifest = []

    # Move backup files
    print("\n[Step 2] Moving backup files...")
    try:
        backup_df = pd.read_excel(duplicate_file, sheet_name="Backup_Files")
        moved_count = 0
        for idx, row in backup_df.iterrows():
            source = root_dir / row["full_path"]
            if move_file_safely(source, archive_root / "Backups", manifest):
                moved_count += 1
        print(f"  Moved {moved_count} / {len(backup_df)} backup files")
    except Exception as e:
        print(f"  [WARN] Backup files: {e}")

    # Move legacy files
    print("\n[Step 3] Moving legacy files...")
    try:
        legacy_df = pd.read_excel(legacy_file, sheet_name="Legacy_Files")
        moved_count = 0
        for idx, row in legacy_df.iterrows():
            source = root_dir / row["full_path"]
            if move_file_safely(source, archive_root / "Legacy", manifest):
                moved_count += 1
        print(f"  Moved {moved_count} / {len(legacy_df)} legacy files")
    except Exception as e:
        print(f"  [WARN] Legacy files: {e}")

    # Move superseded files
    print("\n[Step 4] Moving superseded files...")
    try:
        superseded_df = pd.read_excel(legacy_file, sheet_name="Superseded_Files")
        moved_count = 0
        for idx, row in superseded_df.iterrows():
            source = root_dir / row["full_path"]
            if move_file_safely(source, archive_root / "Superseded", manifest):
                moved_count += 1
        print(f"  Moved {moved_count} / {len(superseded_df)} superseded files")
    except Exception as e:
        print(f"  [WARN] Superseded files: {e}")

    # Move old results
    print("\n[Step 5] Moving old result files...")
    try:
        old_results_df = pd.read_excel(legacy_file, sheet_name="Old_Results")
        moved_count = 0
        for idx, row in old_results_df.iterrows():
            source = root_dir / row["full_path"]
            if move_file_safely(source, archive_root / "Old_Results", manifest):
                moved_count += 1
        print(f"  Moved {moved_count} / {len(old_results_df)} old result files")
    except Exception as e:
        print(f"  [WARN] Old results: {e}")

    # Save manifest
    print("\n[Step 6] Saving manifest...")
    manifest_df = pd.DataFrame(manifest)
    manifest_excel = archive_root / "ARCHIVE_MANIFEST.xlsx"

    if len(manifest) > 0:
        with pd.ExcelWriter(manifest_excel, engine="openpyxl") as writer:
            manifest_df.to_excel(writer, sheet_name="Moved_Files", index=False)

            # Summary
            summary = {
                "Category": ["Backups", "Legacy", "Superseded", "Old Results", "Total"],
                "Files Moved": [
                    len([m for m in manifest if "Backups" in m["destination"]]),
                    len([m for m in manifest if "Legacy" in m["destination"]]),
                    len([m for m in manifest if "Superseded" in m["destination"]]),
                    len([m for m in manifest if "Old_Results" in m["destination"]]),
                    len(manifest),
                ],
            }
            pd.DataFrame(summary).to_excel(writer, sheet_name="Summary", index=False)

        print(f"  Manifest saved: {manifest_excel}")
        print(f"  Total files moved: {len(manifest)}")
    else:
        print("  [WARN] No files were moved")

    # Print summary
    print("\n" + "=" * 80)
    print("Archive Complete")
    print("=" * 80)
    print(f"\nArchive Location: {archive_root}")
    print(f"Files Moved: {len(manifest)}")
    print(f"\nManifest: {manifest_excel}")

    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Verify systems still work (Step 6)")
    print("2. Create clean file structure documentation (Step 7)")
    print("=" * 80)


if __name__ == "__main__":
    main()
