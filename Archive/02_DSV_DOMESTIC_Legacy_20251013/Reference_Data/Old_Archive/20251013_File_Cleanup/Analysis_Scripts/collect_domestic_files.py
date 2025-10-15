#!/usr/bin/env python3
"""
Collect and catalog all DOMESTIC system files
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def collect_domestic_files():
    """DOMESTIC 시스템의 모든 파일 수집"""
    base_dir = Path(__file__).parent

    files = {
        "Core Scripts": [],
        "Utilities": [],
        "Configuration": [],
        "Reference Data": [],
        "Results (CSV)": [],
        "Results (Excel)": [],
        "Results (JSON)": [],
        "Documentation": [],
        "Analysis Scripts": [],
        "Reference-from-Execution": [],
    }

    # Core Scripts
    for script in [
        "domestic_audit_system.py",
        "domestic_sept_2025_audit.py",
        "domestic_validator_v2.py",
    ]:
        path = base_dir / "Core_Systems" / script
        if path.exists():
            stat = path.stat()
            files["Core Scripts"].append(
                {
                    "file": script,
                    "path": str(path.relative_to(base_dir)),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "lines": len(
                        path.read_text(encoding="utf-8", errors="ignore").splitlines()
                    ),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

    # Utilities
    util_dir = base_dir / "Core_Systems"
    for py_file in util_dir.glob("*.py"):
        if py_file.name not in [
            "domestic_audit_system.py",
            "domestic_sept_2025_audit.py",
        ]:
            stat = py_file.stat()
            files["Utilities"].append(
                {
                    "file": py_file.name,
                    "path": str(py_file.relative_to(base_dir)),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

    # Root utilities
    for py_file in base_dir.glob("*.py"):
        stat = py_file.stat()
        files["Utilities"].append(
            {
                "file": py_file.name,
                "path": str(py_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
            }
        )

    # Configuration
    for config_file in base_dir.glob("*.json"):
        stat = config_file.stat()
        files["Configuration"].append(
            {
                "file": config_file.name,
                "path": str(config_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
            }
        )

    # Reference Data
    for data_file in ["DOMESTIC_with_distances.xlsx", "domestic_result.xlsx"]:
        path = base_dir / data_file
        if path.exists():
            stat = path.stat()
            files["Reference Data"].append(
                {
                    "file": data_file,
                    "path": str(path.relative_to(base_dir)),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

    # Results
    results_dir = base_dir / "Results" / "Sept_2025"

    for csv_file in (results_dir / "CSV").glob("*.csv"):
        stat = csv_file.stat()
        files["Results (CSV)"].append(
            {
                "file": csv_file.name,
                "path": str(csv_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        )

    for xlsx_file in (results_dir / "Reports").glob("*.xlsx"):
        stat = xlsx_file.stat()
        files["Results (Excel)"].append(
            {
                "file": xlsx_file.name,
                "path": str(xlsx_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        )

    for json_file in (results_dir / "JSON").glob("*.json"):
        stat = json_file.stat()
        files["Results (JSON)"].append(
            {
                "file": json_file.name,
                "path": str(json_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
        )

    # Documentation
    for md_file in base_dir.glob("*.md"):
        stat = md_file.stat()
        files["Documentation"].append(
            {
                "file": md_file.name,
                "path": str(md_file.relative_to(base_dir)),
                "size_kb": round(stat.st_size / 1024, 2),
                "lines": len(
                    md_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                ),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
            }
        )

    # Reference-from-Execution
    ref_exec_dir = base_dir / "domestic ref"
    if ref_exec_dir.exists():
        for file in ref_exec_dir.glob("*.py"):
            stat = file.stat()
            files["Reference-from-Execution"].append(
                {
                    "file": file.name,
                    "path": str(file.relative_to(base_dir)),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "lines": len(
                        file.read_text(encoding="utf-8", errors="ignore").splitlines()
                    ),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

    return files


def main():
    print("=" * 80)
    print("DOMESTIC System File Collection")
    print("=" * 80)

    files = collect_domestic_files()

    print("\nFile Inventory:")
    print("-" * 80)

    total_files = 0
    for category, file_list in files.items():
        print(f"\n{category}: {len(file_list)} files")
        total_files += len(file_list)

        if len(file_list) > 0 and len(file_list) <= 10:
            for f in file_list:
                print(f"  - {f['file']}")
        elif len(file_list) > 10:
            for f in file_list[:3]:
                print(f"  - {f['file']}")
            print(f"  ... and {len(file_list) - 3} more")

    print(f"\nTotal DOMESTIC files: {total_files}")

    # Save to Excel
    output_excel = Path(__file__).parent / "DOMESTIC_FILE_CATALOG.xlsx"

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        for category, file_list in files.items():
            if file_list:
                df = pd.DataFrame(file_list)
                sheet_name = (
                    category.replace(" ", "_").replace("(", "").replace(")", "")[:31]
                )
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n[OK] Catalog saved: {output_excel}")

    return files


if __name__ == "__main__":
    main()
