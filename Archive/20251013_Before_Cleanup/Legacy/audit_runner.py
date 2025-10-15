import csv, json, pathlib, logging, argparse
from joiners import canon_dest, unit_key, port_hint
from rules import FIXED_FX, LAYER1_TOL, AUTOFAIL, cg_band
ROOT = pathlib.Path(__file__).resolve().parents[1]
IO = ROOT / "io"; OUT = ROOT / "out"; REF = ROOT / "py" / "refs"
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True); LOG = LOGS / "audit.log"
logging.basicConfig(filename=LOG, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
def load_ref(fname):
    p = REF/fname
    if not p.exists(): return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f); return data.get("records", data) if isinstance(data, dict) else data
def build_ref_index(records):
    idx={}
    for r in records:
        try:
            c=(r.get("cargo_type") or "").strip(); p=(r.get("port") or "").strip()
            d=(r.get("destination") or "") or ""; u=(r.get("unit") or "").strip()
            rate=r.get("rate",{}).get("amount") if isinstance(r.get("rate"),dict) else r.get("rate")
            if rate is None: continue
            key=(c,p,canon_dest(d),unit_key(u)); idx[key]=float(rate)
        except Exception as e: logging.warning("ref skip: %s", e)
    return idx
def merge_refs():
    idx={}
    for fn in ["air_cargo_rates.json","container_cargo_rates.json","bulk_cargo_rates.json"]:
        idx.update(build_ref_index(load_ref(fn)))
    return idx
def parse_amount(val,ccy):
    amt=float(val); return (amt,"USD") if (ccy or "USD").upper()=="USD" else (amt,ccy)
def main(shipment:str):
    ref=merge_refs(); inp=IO/f"{shipment}_Invoice_Items.csv"; outp=OUT/f"{shipment}_Audit_Result.csv"
    rows_out=[]; 
    if not inp.exists(): raise FileNotFoundError(f"Input not found: {inp}")
    with open(inp,"r",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f)
        for i,row in enumerate(rd,start=1):
            ctype=(row.get("CargoType") or "").strip(); port=(row.get("Port") or "").strip()
            dest=canon_dest(row.get("Destination") or ""); unit=unit_key(row.get("Unit") or "")
            port2=port_hint(port,dest,unit); amt,ccy=parse_amount(row.get("Rate_Charged") or "0", row.get("Currency") or "USD")
            key=(ctype,port2 or port,dest,unit); ref_rate=ref.get(key); status="REFERENCE_MISSING"; delta=""; band=""; flag="PENDING_REVIEW"
            if ref_rate is not None:
                delta=(amt-ref_rate)/ref_rate; band=cg_band(abs(delta))
                within=abs(delta)<=LAYER1_TOL; autofail=abs(delta)>AUTOFAIL
                if within: status="Verified"; flag="OK"
                elif autofail: status="COST_GUARD_FAIL"; flag="CRITICAL"
                else: status="Pending Review"; flag="WARN"
            rows_out.append({
                "SNo": row.get("SNo") or i,
                "RateSource": row.get("RateSource"),
                "Description": row.get("Description"),
                "DraftRate_USD": f"{float(row.get('Rate_Charged') or 0):.2f}",
                "Qty": row.get("Qty") or row.get("QTY") or "1",
                "DraftTotal_USD": f"{float(row.get('Total_USD') or 0):.2f}",
                "Port(Join)": port2 or port, "Destination(Join)": dest, "CargoType": ctype, "Unit": unit,
                "Ref_Rate_USD": f"{ref_rate:.2f}" if ref_rate is not None else "",
                "Delta_%": f"{(float(delta)*100):.2f}" if delta!="" else "",
                "CG_Band": band, "Status": status, "Flag": flag, "Key": "|".join(key)
            })
    OUT.mkdir(exist_ok=True)
    with open(outp,"w",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows_out[0].keys())); wr.writeheader(); wr.writerows(rows_out)
    print(f"Saved: {outp}")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--shipment",required=True); a=ap.parse_args(); main(a.shipment)
