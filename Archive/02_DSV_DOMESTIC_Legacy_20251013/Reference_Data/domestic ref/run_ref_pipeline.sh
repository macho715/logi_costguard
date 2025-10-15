#!/usr/bin/env bash
set -e

LEDGER="/mnt/data/DOMESTIC_with_distances.xlsx"      # 집행 완료 데이터
REFDIR="/mnt/data/DOMESTIC_ref"                      # 레퍼런스 산출 폴더
INVOICE="/mnt/data/Domestic_invoice_distance.xlsx"   # 재검증할 인보이스
OUTDIR="/mnt/data/DOMESTIC_verify_out"               # 결과 폴더

python build_reference_from_execution.py --ledger "$LEDGER" --outdir "$REFDIR"
python validate_with_reference.py --invoice "$INVOICE" --refdir "$REFDIR" --outdir "$OUTDIR"
