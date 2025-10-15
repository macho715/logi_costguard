#!/usr/bin/env python3
"""
MD 파일 중복 분석 스크립트
"""

from pathlib import Path
import hashlib


def analyze_md_files():
    """MD 파일 분석"""
    rate_dir = Path(__file__).parent.parent / "Rate"
    md_files = list(rate_dir.glob("*.md"))

    print("=" * 80)
    print("MD File Analysis")
    print("=" * 80)
    print()

    results = []
    for md_file in md_files:
        size = md_file.stat().st_size

        # MD5 해시 계산
        with open(md_file, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]

        # 첫 10줄 읽기
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[:10]
            preview = "".join(lines)[:200]

        results.append(
            {
                "name": md_file.name,
                "size": size,
                "hash": file_hash,
                "lines": len(open(md_file, "r", encoding="utf-8").readlines()),
            }
        )

    # 크기순 정렬
    results.sort(key=lambda x: x["size"], reverse=True)

    print(f"Total MD Files: {len(results)}")
    print()

    for r in results:
        print(f"[FILE] {r['name']}")
        print(f"  Size: {r['size']:,} bytes ({r['size']/1024:.1f} KB)")
        print(f"  Lines: {r['lines']:,}")
        print(f"  Hash: {r['hash']}")
        print()

    # 중복 분석
    print("=" * 80)
    print("Duplication Analysis")
    print("=" * 80)
    print()

    # 파일명 패턴 분석
    full_files = [r for r in results if "full" in r["name"].lower()]
    container_files = [
        r
        for r in results
        if "container" in r["name"].lower() and "full" not in r["name"].lower()
    ]
    bulk_files = [
        r
        for r in results
        if "bulk" in r["name"].lower() and "full" not in r["name"].lower()
    ]
    other_files = [
        r for r in results if r not in full_files + container_files + bulk_files
    ]

    print(f"Full version: {len(full_files)} file(s)")
    for f in full_files:
        print(f"  - {f['name']} ({f['size']/1024:.1f} KB, {f['lines']} lines)")

    print(f"\nContainer version: {len(container_files)} file(s)")
    for f in container_files:
        print(f"  - {f['name']} ({f['size']/1024:.1f} KB, {f['lines']} lines)")

    print(f"\nBulk version: {len(bulk_files)} file(s)")
    for f in bulk_files:
        print(f"  - {f['name']} ({f['size']/1024:.1f} KB, {f['lines']} lines)")

    print(f"\nOther files: {len(other_files)} file(s)")
    for f in other_files:
        print(f"  - {f['name']} ({f['size']/1024:.1f} KB, {f['lines']} lines)")

    # 권장사항
    print()
    print("=" * 80)
    print("Recommendations")
    print("=" * 80)

    if full_files:
        print(f"[KEEP] {full_files[0]['name']} - Master reference (Full version)")

    if container_files or bulk_files:
        print(f"[CONSIDER_DELETE] Container/Bulk specific versions")
        print("  Reason: Redundant if Full version contains all data")

    print(f"[KEEP] contract_inland_trucking_charge_rates_v1.3.md - Contract spec")
    print(f"[KEEP] PRISM_KERNEL_README_HVDC_v2.md - Validation framework")


if __name__ == "__main__":
    analyze_md_files()
