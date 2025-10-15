"""
Enhanced audit_runner.py - 포털 수수료 검증 시스템

포털 수수료는 문서기반 AED 추출 → USD 환산 → ±0.5% 검증을 수행합니다.
"""

import csv
import json
import pathlib
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Enhanced modules
from joiners_enhanced import (
    canon_dest, unit_key, port_hint, charge_group, parse_aed_from_formula,
    get_portal_fee_fixed_rate, run_all_gates
)
from rules_enhanced import (
    FIXED_FX, tolerance_for, AUTOFAIL, get_band_for_group,
    process_invoice_item, convert_aed_to_usd
)

# === 경로 설정 ===
ROOT = pathlib.Path(__file__).resolve().parents[0]
IO = ROOT / "io"
OUT = ROOT / "out"
REF = ROOT / "py" / "refs"
LOGS = ROOT / "logs"

# 로그 디렉토리 생성
LOGS.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(
    filename=LOGS / "audit_enhanced.log", 
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(message)s"
)

def load_ref(fname: str) -> List[Dict[str, Any]]:
    """참조 요율 파일 로드"""
    p = REF / fname
    if not p.exists(): 
        return []
    
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("records", data) if isinstance(data, dict) else data
    except Exception as e:
        logging.error(f"Failed to load ref file {fname}: {e}")
        return []

def build_ref_index(records: List[Dict[str, Any]]) -> Dict[tuple, float]:
    """참조 요율 인덱스 구축"""
    idx = {}
    
    for r in records:
        try:
            c = (r.get("cargo_type") or "").strip()
            p = (r.get("port") or "").strip()
            d = (r.get("destination") or "") or ""
            u = (r.get("unit") or "").strip()
            
            rate = r.get("rate", {}).get("amount") if isinstance(r.get("rate"), dict) else r.get("rate")
            if rate is None: 
                continue
                
            idx[(c, p, d, u)] = float(rate)
        except Exception as e:
            logging.warning(f"ref skip: {e}")
    
    return idx

def merge_refs() -> Dict[tuple, float]:
    """모든 참조 요율 통합"""
    idx = {}
    
    for fn in ["air_cargo_rates.json", "container_cargo_rates.json", "bulk_cargo_rates.json"]:
        idx.update(build_ref_index(load_ref(fn)))
    
    return idx

def process_invoice_row(row: Dict[str, str], ref_index: Dict[tuple, float], 
                       supporting_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """송장 행 처리"""
    try:
        # 기본 정보 추출
        desc = (row.get("Description") or "").strip()
        src = (row.get("RateSource") or "").strip()
        group = charge_group(src, desc)
        
        # 입력 키 구성
        ctype = (row.get("CargoType") or "").strip()
        port = (row.get("Port") or "").strip()
        dest = canon_dest(row.get("Destination") or "")
        unit = unit_key(row.get("Unit") or "")
        port2 = port_hint(port, dest, unit)
        key = (ctype, port2 or port, dest, unit)
        
        # Draft 금액(USD)
        amt = float(row.get("Rate_Charged") or 0)
        qty = row.get("Qty") or row.get("QTY") or "1"
        total = float(row.get("Total_USD") or 0)
        
        # 참조금액(USD) - 기본값
        ref_rate = ref_index.get(key)
        
        # 송장 항목 데이터 구성
        invoice_item = {
            "s_no": row.get("SNo") or "",
            "rate_source": src,
            "description": desc,
            "rate_usd": amt,
            "quantity": float(qty) if qty.replace(".", "").isdigit() else 1,
            "total_usd": total,
            "currency": row.get("Currency", "USD"),
            "formula_text": row.get("Formula", ""),
            "cargo_type": ctype,
            "port": port2 or port,
            "destination": dest,
            "unit": unit
        }
        
        # 포털 수수료 특별 처리
        if group == "PortalFee":
            # 1. 수식에서 AED 금액 추출
            doc_aed = parse_aed_from_formula(invoice_item["formula_text"])
            
            # 2. 고정값 테이블에서 조회
            if doc_aed is None:
                fixed_rate = get_portal_fee_fixed_rate(desc)
                if fixed_rate:
                    doc_aed = fixed_rate["AED"]
            
            # 3. AED → USD 환산
            if doc_aed is not None:
                ref_rate = convert_aed_to_usd(doc_aed)
                logging.info(f"Portal fee AED {doc_aed} → USD {ref_rate}")
        
        # 송장 항목 처리
        processed_item = process_invoice_item(invoice_item, ref_rate)
        
        # Gate 검증 실행
        gate_result = run_all_gates(invoice_item, supporting_docs or [], ref_rate)
        
        # 결과 구성
        result = {
            "SNo": invoice_item["s_no"],
            "RateSource": src,
            "ChargeGroup": group,
            "Description": desc,
            "DraftRate_USD": f"{amt:.2f}",
            "Qty": qty,
            "DraftTotal_USD": f"{total:.2f}",
            "Port(Join)": port2 or port,
            "Destination(Join)": dest,
            "CargoType": ctype,
            "Unit": unit,
            "Ref_Rate_USD": f"{ref_rate:.2f}" if ref_rate is not None else "",
            "Delta_%": f"{processed_item['delta_percent']:.2f}",
            "CG_Band": processed_item['band'],
            "Status": processed_item['status'],
            "Flag": processed_item['flag'],
            "Key": "|".join(key),
            "Gate_Status": gate_result["Gate_Status"],
            "Gate_Fails": gate_result["Gate_Fails"],
            "Gate_Score": gate_result["Gate_Score"]
        }
        
        # 포털 수수료 특별 정보 추가
        if group == "PortalFee":
            result.update({
                "Doc_AED": f"{processed_item.get('doc_aed', 0):.2f}" if processed_item.get('doc_aed') else "",
                "Tolerance": f"{processed_item.get('tolerance', 0)*100:.1f}%",
                "FX_Rate": "3.6725"
            })
        
        return result
        
    except Exception as e:
        logging.error(f"Error processing row: {e}")
        return {
            "SNo": row.get("SNo", ""),
            "RateSource": row.get("RateSource", ""),
            "ChargeGroup": "Error",
            "Description": row.get("Description", ""),
            "Status": "ERROR",
            "Flag": "ERROR",
            "Error": str(e)
        }

def main(shipment: str):
    """메인 실행 함수"""
    try:
        # 참조 요율 로드
        ref = merge_refs()
        logging.info(f"Loaded {len(ref)} reference rates")
        
        # 입출력 파일 경로 (SCNT_ 접두사 포함)
        inp = IO / f"SCNT_{shipment}_Invoice_Items.csv"
        outp = OUT / f"{shipment}_Audit_Result_Enhanced.csv"
        
        # 출력 디렉토리 생성
        OUT.mkdir(exist_ok=True)
        
        if not inp.exists():
            raise FileNotFoundError(f"Input not found: {inp}")
        
        # CSV 처리
        rows_out = []
        
        with open(inp, "r", encoding="utf-8-sig") as f:
            rd = csv.DictReader(f)
            for i, row in enumerate(rd, start=1):
                processed_row = process_invoice_row(row, ref)
                rows_out.append(processed_row)
                
                if i % 10 == 0:
                    logging.info(f"Processed {i} rows")
        
        # 결과 저장
        if rows_out:
            with open(outp, "w", encoding="utf-8", newline="") as f:
                wr = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
                wr.writeheader()
                wr.writerows(rows_out)
            
            logging.info(f"Saved {len(rows_out)} rows to {outp}")
            
            # 요약 통계
            total_rows = len(rows_out)
            portal_fees = len([r for r in rows_out if r.get("ChargeGroup") == "PortalFee"])
            verified = len([r for r in rows_out if r.get("Status") == "Verified"])
            failed = len([r for r in rows_out if r.get("Status") == "COST_GUARD_FAIL"])
            
            print(f"✅ Enhanced audit completed for {shipment}")
            print(f"   Total rows: {total_rows}")
            print(f"   Portal fees: {portal_fees}")
            print(f"   Verified: {verified}")
            print(f"   Failed: {failed}")
            print(f"   Output: {outp}")
        else:
            print("❌ No data processed")
            
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Enhanced Invoice Audit System")
    ap.add_argument("--shipment", required=True, help="Shipment ID")
    args = ap.parse_args()
    main(args.shipment)
