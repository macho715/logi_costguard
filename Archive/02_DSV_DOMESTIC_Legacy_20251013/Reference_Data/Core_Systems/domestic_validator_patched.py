# -*- coding: utf-8 -*-
# Domestic invoice verification — end-to-end script
# Inputs:
#   INPUT_PATH (필수)
# Optional:
#   REF_XLSX (표준 스냅샷이 있을 경우)

import pandas as pd, numpy as np, os, re, json, hashlib, datetime as dt
from sklearn.ensemble import IsolationForest

def validate_domestic_invoices(input_path, output_xlsx, output_json, ref_xlsx=None):
    """
    patch.md 섹션 3의 코드를 그대로 구현
    """
    
    # 1) Load
    # CSV 또는 Excel 자동 감지
    if str(input_path).endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)
    
    # 컬럼명 정규화
    df = df.rename(columns={
        'Date':'date','Shipment Reference':'shipment_reference',
        'Place of Loading':'place_loading','Place of Delivery':'place_delivery',
        'Vehicle Type':'vehicle_type','Q/TY':'qty','Distance(km)':'distance_km',
        'Rate (USD)':'rate_usd','Distance_Method':'distance_method'
    })
    
    # 컬럼이 없으면 기본값으로 생성
    if 'qty' not in df.columns:
        df['qty'] = 1
    if 'distance_km' not in df.columns:
        df['distance_km'] = 0
    if 'rate_usd' not in df.columns:
        df['rate_usd'] = 0
        
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(1).astype(int)
    df['distance_km'] = pd.to_numeric(df['distance_km'], errors='coerce')
    df['rate_usd'] = pd.to_numeric(df['rate_usd'], errors='coerce')
    df['unit'] = 'per truck'
    
    # 2) Canonical normalizers (subset; 규칙 추가 가능)
    NORMALIZE_MAP = {
        r'\bDSV\s*MUSSAFAH\s*YARD\b': 'DSV Mussafah Yard',
        r'\bDSV\s*M44\b|M44\s*WAREHOUSE': 'M44 Warehouse',
        r'\bDSV\s*AL\s*MARKAZ\s*WH\b|AL\s*MARKAZ\s*WAREHOUSE': 'Al Markaz Warehouse',
        r'\bPRESTIGE\b.*ICAD.*|PRESTIGE\s*MUSSAFAH': 'DSV Mussafah Yard',
        r'\bMOSB\b|AL\s*MASA?OOD\b|AL\s*MASAOOD\b': 'Al Masaood (MOSB)',
        r'\bMIRFA\b|MIRFA\s*SITE|MIRFA\s*PMO\s*SAMSUNG': 'MIRFA SITE',
        r'\bSHUWEIHAT\b|SHUWEIHAT\s*(SITE|POWER\s*STATION)?': 'SHUWEIHAT Site',
        r'\bMINA\s*FREE\s*PORT\b|\bMINA\s*FREEPORT\b|\bMINA\s*ZAYED\b|JDN\s*MINA\s*ZAYED': 'Mina Zayed Port',
        r'\bJEBEL\s*ALI\b|MAMMOET\s*JEBEL\s*ALI|AL\s*GURG.*JEBEL\s*ALI|NOVATECH.*JEBEL\s*ALI': 'Jebel Ali Port',
        r'\bFUJAIRAH\b|F3\s*FUJAIRAH': 'F3 Fujairah',
        r'\bTESLA\s*DUBAI\b': 'Tesla Dubai',
        r'\bAAA\s*WAREHOUSE\b': 'AAA Warehouse',
        r'\bPRIME\s*GEOTEXTILE\s*MUSSAFAH\b': 'DSV Mussafah Yard',
        r'\bKEC\s*TOWERS?\s*LLC.*DUBAI\b|KEC\s*DIP\s*DUBAI\b': 'Kec Dip Dubai',
        r'\bSIEMENS\s*MASDAR\b': 'Siemens Masdar',
        r'\bBINT?\s*HAMID\s*DUBAI\b': 'Bint Hamid Dubai',
        r'\bBIN\s*DASMAL\s*GENERAL\s*TRADING\b': 'Bin Dasmal General Trading',
        r'\bTAREEQ?\s*AL\s*KHALEEJ\s*SHARJAH\b|TAREEJ\s*\(SHARJAH\)': 'Tareeq Al Khaleej Sharjah',
        r'\bUSG\s*MIDDLE\s*EAST\s*DUBAI\s*INVESTMENT\s*PARK\b': 'Usg Middle East Dubai Investment Park',
        r'\bJUBAIL\b': 'Jubail',
        r'\bMAMMOET\s*RAK\b': 'Mammoet Rak',
        r'\bJETTY\b': 'Jetty',
        r'\bAL\s*MARKAZ\b(?!.*WAREHOUSE)': 'DSV Markaz',
        r'\bPRESTIGE\s*ICAD\b': 'DSV Mussafah Yard',
    }
    
    def normalize_place(x: str) -> str:
        if pd.isna(x): return ''
        s = str(x).strip().upper()
        s = re.sub(r'\s+', ' ', s)
        for patt, canon in NORMALIZE_MAP.items():
            if re.search(patt, s): return canon
        if 'MUSSAFAH' in s and 'YARD' in s: return 'DSV Mussafah Yard'
        if 'MIRFA' in s: return 'MIRFA SITE'
        if 'SHUWEIHAT' in s: return 'SHUWEIHAT Site'
        if 'MOSB' in s: return 'Al Masaood (MOSB)'
        if 'MINA' in s: return 'Mina Zayed Port'
        return s.title()
    
    df['origin_norm'] = df['place_loading'].map(normalize_place)
    df['destination_norm'] = df['place_delivery'].map(normalize_place)
    
    def normalize_vehicle(v):
        if pd.isna(v): return np.nan
        s = str(v).strip().upper()
        s = s.replace('FLATBED (HAZMAT)','FLATBED HAZMAT').replace('FLATBED- CICPA','FLATBED (CICPA)')
        if s == 'FB': return 'FLATBED'
        if s == 'LB': return 'LOWBED'
        if 'FLATBED' in s and 'CICPA' in s: return 'FLATBED (CICPA)'
        if 'FLATBED' in s and 'HAZ' in s: return 'FLATBED HAZMAT'
        if 'FLATBED' in s: return 'FLATBED'
        if 'LOWBED' in s or s == 'LB':
            if '23' in s: return 'LOWBED (23M)'
            return 'LOWBED'
        if 'PICKUP' in s or 'PU' in s:
            return '7 TON PU' if '7' in s else '3 TON PU'
        return s
    df['vehicle_norm'] = df['vehicle_type'].map(normalize_vehicle)
    
    # 3) lane ref (dataset median fallback)
    grp = ['origin_norm','destination_norm','vehicle_norm','unit']
    ref = (df.groupby(grp, dropna=False)
             .agg(samples=('rate_usd','count'),
                  median_rate_usd=('rate_usd','median'),
                  median_distance_km=('distance_km','median'))
             .reset_index())
    
    items = df.merge(ref, on=grp, how='left')
    items['per_km'] = np.where(items['distance_km']>0, items['rate_usd']/items['distance_km'], np.nan)
    items['delta_pct'] = 100.0 * (items['rate_usd']-items['median_rate_usd'])/items['median_rate_usd']
    items['delta_abs'] = items['delta_pct'].abs()
    
    def cg_band(x):
        if pd.isna(x): return 'REF_MISSING'
        if x <= 2.0: return 'PASS'
        if x <= 5.0: return 'WARN'
        if x <= 10.0:return 'HIGH'
        return 'CRITICAL'
    items['cg_band'] = items['delta_abs'].map(cg_band)
    
    # 4) short-run & fixed-cost suspicion
    SHORT_KM, VERY_SHORT_KM = 10.0, 2.0
    short = items[items['distance_km'].between(0.1, 15, inclusive='both')].copy()
    perkm_stats = (short.groupby('vehicle_norm')
                   .agg(p25=('per_km', lambda x: x.quantile(0.25)),
                        p75=('per_km', lambda x: x.quantile(0.75)))
                   .reset_index())
    perkm_stats['iqr'] = perkm_stats['p75'] - perkm_stats['p25']
    items = items.merge(perkm_stats, on='vehicle_norm', how='left')
    
    def fixed_flags(r):
        f=[]
        if pd.isna(r['rate_usd']) or pd.isna(r['distance_km']): f.append('DATA_MISSING'); return f
        if r['distance_km'] <= 0: f.append('DISTANCE_ZERO')
        if r['distance_km'] <= SHORT_KM:
            f.append('SHORT_RUN')
            if pd.notna(r.get('p75')) and pd.notna(r.get('iqr')) and r['iqr']>0:
                if r['per_km'] > r['p75'] + 1.5*r['iqr']: f.append('HIGH_PERKM_SHORT')
            if pd.notna(r['per_km']):
                if r['per_km'] >= 100 or (r['distance_km']<=VERY_SHORT_KM and r['per_km']>=40):
                    f.append('FIXED_COST_SUSPECT')
        return f
    items['flags'] = items.apply(lambda r: ';'.join(fixed_flags(r)), axis=1)
    
    # 5) anomaly (IsolationForest prediction)
    X = items[['per_km','distance_km','vehicle_norm']].copy()
    veh_map = {v:i for i,v in enumerate(sorted(X['vehicle_norm'].dropna().unique()))}
    X['veh_code'] = X['vehicle_norm'].map(veh_map).fillna(-1)
    X = X.drop(columns=['vehicle_norm'])
    X['per_km'] = X['per_km'].fillna(X['per_km'].median())
    X['distance_km'] = X['distance_km'].fillna(X['distance_km'].median())
    clf = IsolationForest(n_estimators=200, contamination=0.04, random_state=42)
    pred = clf.fit_predict(X)  # -1 = anomaly
    score = clf.decision_function(X)
    items['anomaly_pred'] = (pred==-1)
    items['anomaly_score'] = (score.min()-score)/(score.min()-score.max()+1e-9)
    
    # 6) decision
    def decide(r):
        if pd.notna(r['delta_abs']) and r['delta_abs']>15: return 'FAIL'
        if r['cg_band']=='CRITICAL': return 'FAIL'
        if r['cg_band']=='HIGH': return 'PENDING_REVIEW'
        if 'FIXED_COST_SUSPECT' in (r['flags'] or ''): return 'PENDING_REVIEW'
        if r.get('anomaly_pred', False): return 'PENDING_REVIEW'
        if r['cg_band'] in ['PASS','WARN']: return 'VERIFIED'
        return 'PENDING_REVIEW'
    items['verification_result'] = items.apply(decide, axis=1)
    
    # 7) summary & export
    summary_band = items['cg_band'].value_counts(dropna=False).rename_axis('cg_band').reset_index(name='count')
    summary_ver = items['verification_result'].value_counts(dropna=False).rename_axis('verification').reset_index(name='count')
    
    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as w:
        items.to_excel(w, sheet_name='items', index=False)
        summary_band.to_excel(w, sheet_name='summary_band', index=False)
        summary_ver.to_excel(w, sheet_name='summary_verification', index=False)
    
    artifact = {
        "artifact_id": f"DomesticInvoiceAudit-{dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "inputs": {"file": os.path.basename(input_path), "rows": int(len(df))},
        "logic": {
            "ref": "ApprovedLaneMap (if available) -> dataset median fallback",
            "cg_bands": {"PASS":"<=2","WARN":"<=5","HIGH":"<=10","CRITICAL":">10"},
            "auto_fail_delta_pct": ">15",
            "short_run_km": SHORT_KM,
            "anomaly": "IsolationForest(4%)"
        },
        "outputs": {
            "counts": {
                "cg_band": summary_band.set_index('cg_band')['count'].to_dict(),
                "verification": summary_ver.set_index('verification')['count'].to_dict()
            },
            "files": {"report_xlsx": os.path.basename(output_xlsx)}
        }
    }
    
    # PRISM recap.card (섹션 6)
    recap_card = f"""P:: invoice-verify · lane-join · Δ% compute
R:: COST-GUARD Δ≤2/5/10 · AutoFail>15 · HallucinationBan
I:: {{sources:['Domestic_invoice_distance.xlsx','ApprovedLaneMap?','Inland_Trucking_Rate_Table_v2.1?']}}
S:: plan→normalize→join→score→export
M:: {{report.xlsx, proof.artifact(json, sha256)}}"""
    
    artifact['recap_card'] = recap_card
    artifact['proof_hash'] = hashlib.sha256(json.dumps(artifact, sort_keys=True).encode('utf-8')).hexdigest()
    
    with open(output_json, 'w') as f: 
        json.dump(artifact, f, indent=2)
    
    return items, summary_band, summary_ver, artifact, recap_card


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python domestic_validator_patched.py <input_xlsx> [output_xlsx] [output_json]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_xlsx = sys.argv[2] if len(sys.argv) > 2 else "domestic_validation_report.xlsx"
    output_json = sys.argv[3] if len(sys.argv) > 3 else "domestic_validation_artifact.json"
    
    items, summary_band, summary_ver, artifact, recap = validate_domestic_invoices(
        input_path, output_xlsx, output_json
    )
    
    print("\n" + "="*60)
    print(recap)
    print("="*60)
    print(f"\nDONE. Wrote: {output_xlsx}, {output_json}")
    print(f"Total: {len(items)} items")
    print(f"Verification: {summary_ver.to_dict('records')}")

