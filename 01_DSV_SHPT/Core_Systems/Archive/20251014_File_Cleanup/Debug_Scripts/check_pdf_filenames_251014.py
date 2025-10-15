#!/usr/bin/env python3
"""
PDF 파일명 확인 스크립트
"""

from pathlib import Path


def main():
    pdf_dir = Path(
        rPath(__file__).parent.parent / "SCNT Import (Sept 2025) - Supporting Documents"
    )

    if not pdf_dir.exists():
        print(f"[ERROR] Directory not found: {pdf_dir}")
        return

    pdfs = sorted(pdf_dir.glob("*.pdf"))

    print(f"Total PDFs: {len(pdfs)}")
    print(f"\nSample PDF filenames:")
    for pdf in pdfs[:20]:
        print(f"  {pdf.name}")

    # Shipment ID 패턴 분석
    print(f"\n[Shipment ID Patterns]")
    shipment_ids = set()
    for pdf in pdfs:
        # "_" 앞부분이 Shipment ID
        parts = pdf.stem.split("_")
        if len(parts) >= 2:
            shipment_id = parts[0]
            shipment_ids.add(shipment_id)

    print(f"Unique Shipment IDs: {len(shipment_ids)}")
    for sid in sorted(list(shipment_ids))[:15]:
        count = len(list(pdf_dir.glob(f"{sid}_*.pdf")))
        print(f"  {sid}: {count} PDFs")


if __name__ == "__main__":
    main()
