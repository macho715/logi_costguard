#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, argparse
import pandas as pd
from domestic_audit_v2.domestic_validator_v2 import (
    validate_domestic,
)  # adjust if path differs


def main():
    ap = argparse.ArgumentParser(description="Domestic Invoice Audit v2 (patched)")
    ap.add_argument(
        "--invoice",
        required=True,
        help="Path to Domestic_invoice_distance.xlsx (or CSV)",
    )
    ap.add_argument(
        "--mapping",
        default="/mnt/data/mapping_update_20250819.xlsx",
        help="Path to mapping_update_20250819.xlsx",
    )
    ap.add_argument(
        "--ledger",
        default="/mnt/data/domestic result.xlsx",
        help="Executed ledger (SPECIAL_PASS whitelist)",
    )
    ap.add_argument(
        "--config",
        default="/mnt/data/domestic_audit_v2/config_domestic_v2.json",
        help="Config JSON",
    )
    ap.add_argument(
        "--outdir", default="/mnt/data/Results/DOMESTIC_RUN", help="Output directory"
    )
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load inputs
    if args.invoice.lower().endswith((".xlsx", ".xls")):
        inv_df = pd.read_excel(args.invoice)
    else:
        inv_df = pd.read_csv(args.invoice)
    ledger_df = None
    if os.path.exists(args.ledger):
        try:
            ledger_df = pd.read_excel(args.ledger)
        except Exception:
            ledger_df = None

    # Validate
    df, recap, artifact, proof_hash = validate_domestic(
        invoice_df=inv_df,
        mapping_path=args.mapping if os.path.exists(args.mapping) else "",
        config_path=args.config,
        executed_ledger_df=ledger_df,
    )

    # Summaries
    summary_band = df.groupby("cg_band").size().reset_index(name="count")
    summary_verdict = df.groupby("verdict").size().reset_index(name="count")

    # Exports
    items_csv = os.path.join(args.outdir, "items.csv")
    df.to_csv(items_csv, index=False)

    xlsx_path = os.path.join(args.outdir, "domestic_audit_report_v2.xlsx")
    with pd.ExcelWriter(xlsx_path) as w:
        df.to_excel(w, sheet_name="items", index=False)
        summary_band.to_excel(w, sheet_name="summary_band", index=False)
        summary_verdict.to_excel(w, sheet_name="summary_verdict", index=False)

    proof = {"recap_card": recap, "artifact": artifact, "proof_hash_sha256": proof_hash}
    proof_path = os.path.join(args.outdir, "domestic_audit_proof_v2.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    # Alias suggestions CSV (optional)
    alias = proof.get("artifact", {}).get("alias_suggestions")
    if alias:
        pd.DataFrame(alias).to_csv(
            os.path.join(args.outdir, "alias_suggestions.csv"), index=False
        )

    # Console
    print("=== Recap ===")
    for line in recap:
        print(line)
    print("\nSaved:")
    print(" -", items_csv)
    print(" -", xlsx_path)
    print(" -", proof_path)
    if alias:
        print(" -", os.path.join(args.outdir, "alias_suggestions.csv"))


if __name__ == "__main__":
    main()
