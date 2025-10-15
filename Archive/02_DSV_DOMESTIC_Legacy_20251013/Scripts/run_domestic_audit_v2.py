import os, json
import pandas as pd
from domestic_validator_v2 import validate_domestic


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Domestic Invoice Audit v2")
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
        help="Executed ledger (special zone) Excel",
    )
    ap.add_argument(
        "--config",
        default="/mnt/data/domestic_audit_v2/config_domestic_v2.json",
        help="Config JSON",
    )
    ap.add_argument(
        "--outdir", default="/mnt/data/Results/Sept_2025_v2", help="Output directory"
    )
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load inputs (Excel or CSV for invoice)
    if args.invoice.lower().endswith(".xlsx"):
        inv_df = pd.read_excel(args.invoice)
    else:
        inv_df = pd.read_csv(args.invoice)

    # Ledger optional
    ledger_df = None
    if os.path.exists(args.ledger):
        try:
            ledger_df = pd.read_excel(args.ledger)
        except Exception:
            ledger_df = None

    df, recap, artifact, proof_hash = validate_domestic(
        invoice_df=inv_df,
        mapping_path=args.mapping,
        config_path=args.config,
        executed_ledger_df=ledger_df,
    )

    # Export
    items_path = os.path.join(args.outdir, "items.csv")
    df.to_csv(items_path, index=False)

    # Summaries
    summary_band = df.groupby("cg_band").size().reset_index(name="count")
    summary_verdict = df.groupby("verdict").size().reset_index(name="count")

    # Excel report
    xlsx_path = os.path.join(args.outdir, "domestic_audit_report_v2.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as w:
        df.to_excel(w, sheet_name="items", index=False)
        summary_band.to_excel(w, sheet_name="summary_band", index=False)
        summary_verdict.to_excel(w, sheet_name="summary_verdict", index=False)

    # Proof artifact
    proof = {"recap_card": recap, "artifact": artifact, "proof_hash_sha256": proof_hash}
    proof_path = os.path.join(args.outdir, "domestic_audit_proof_v2.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    # PATCH 5: alias 제안 저장
    alias = proof.get("artifact", {}).get("alias_suggestions")
    if alias:
        alias_path = os.path.join(args.outdir, "alias_suggestions.csv")
        pd.DataFrame(alias).to_csv(alias_path, index=False)
        print(" -", alias_path, "(alias suggestions)")

    print("Exported:")
    print(" -", items_path)
    print(" -", xlsx_path)
    print(" -", proof_path)
    print("Recap card:")
    for line in recap:
        print(line)


if __name__ == "__main__":
    main()
