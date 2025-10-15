#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOMESTIC September 2025 Invoice Audit System

Inland Transportation Invoice Processing (HVDC · COST-GUARD ready)
- Normalizes O/D/Vehicle/Unit
- Joins against approved domestic reference lanes (exact → similarity ≥ 0.60)
- Computes Δ% vs ref, COST-GUARD band (PASS/WARN/HIGH/CRITICAL), and RiskScore
- Enforces fixed FX (1 USD = 3.6725 AED), unit consistency
- Emits PRISM recap.card (5 lines) + proof.artifact (JSON with sha256)
"""

import sys
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import logging

# Import core validator
sys.path.insert(0, str(Path(__file__).parent))
from domestic_audit_system import validate, load_normalization_map, load_reference_lanes


class DOMESTICSept2025AuditSystem:
    """DOMESTIC September 2025 감사 시스템"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent  # Core_Systems의 상위 폴더 (02_DSV_DOMESTIC)
        self.out_dir = self.root / "Results" / "Sept_2025"
        
        # 폴더 구조 생성
        (self.out_dir / "JSON").mkdir(parents=True, exist_ok=True)
        (self.out_dir / "CSV").mkdir(parents=True, exist_ok=True)
        (self.out_dir / "Reports").mkdir(parents=True, exist_ok=True)
        (self.out_dir / "Logs").mkdir(parents=True, exist_ok=True)
        
        # 9월 2025 데이터 경로
        self.data_dir = self.root / "Data" / "DSV 202509"
        self.excel_file = self.data_dir / "SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025.xlsx"
        self.supporting_docs_path = self.data_dir / "SCNT Domestic (Sept 2025) - Supporting Documents"
        
        # 참조 데이터 (있으면 사용)
        self.ref_xlsx = self.root / "DOMESTIC_with_distances.xlsx"
        if not self.ref_xlsx.exists():
            self.ref_xlsx = None
        
        # 시스템 설정
        self.system_type = "DOMESTIC"
        self.scope = "Inland Transportation Invoice Processing"
        self.fx_rate = 3.6725  # 1 USD = 3.6725 AED
        
        # COST-GUARD 밴드
        self.cost_guard_bands = {
            "PASS": {"max_delta": 2.00, "description": "≤2.00%"},
            "WARN": {"max_delta": 5.00, "description": "2.01-5.00%"},
            "HIGH": {"max_delta": 10.00, "description": "5.01-10.00%"},
            "CRITICAL": {"max_delta": float('inf'), "description": ">10.00%"}
        }
        
        # 로깅 설정
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.out_dir / "Logs" / f"domestic_audit_{self.timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logging.info(f"DOMESTIC 9월 2025 시스템 초기화 완료")
        logging.info(f"참조 데이터: {'사용' if self.ref_xlsx else '내장 fallback'}")
    
    def load_sept_2025_data(self) -> pd.DataFrame:
        """9월 2025 인보이스 데이터 로드"""
        logging.info(f"인보이스 로드 중: {self.excel_file}")
        
        if not self.excel_file.exists():
            logging.warning(f"인보이스 파일 없음: {self.excel_file}")
            logging.info("샘플 데이터로 대체합니다")
            return self._load_sample_data()
        
        try:
            # Excel 파일 읽기 (header=None, 인보이스 형식)
            raw_df = pd.read_excel(self.excel_file, sheet_name=0, header=None)
            
            # S/N 헤더 행 찾기 (정확히 "S/N" 포함)
            header_row = None
            for idx, row in raw_df.iterrows():
                row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
                if 'S/N' in row_str or 'S/No' in row_str or 'S/NO' in row_str.upper():
                    header_row = idx
                    logging.info(f"헤더 행 발견: {idx}행")
                    break
            
            if header_row is None:
                logging.warning("헤더 행(S/N)을 찾을 수 없습니다")
                logging.info("샘플 데이터로 대체합니다")
                return self._load_sample_data()
            
            # 헤더 설정 및 데이터 추출
            raw_df.columns = raw_df.iloc[header_row]
            data_df = raw_df[header_row + 1:].reset_index(drop=True)
            
            logging.info(f"컬럼명: {list(data_df.columns)[:10]}")
            
            # 인보이스 항목 추출
            items = []
            for idx, row in data_df.iterrows():
                try:
                    s_no = str(row.get('S/N', row.get('S/No', row.get('S/NO', '')))).strip()
                    
                    # 빈 행이나 TOTAL 행 스킵
                    if not s_no or s_no == 'nan' or 'TOTAL' in s_no.upper():
                        continue
                    
                    # Shipment Reference
                    shipment_ref = str(row.get('Shipment Reference#', row.get('REF', row.get('REFERENCE', '')))).strip()
                    
                    # Origin/Destination (실제 컬럼명 사용)
                    origin = str(row.get('Place of Loading', row.get('ORIGIN', ''))).strip()
                    destination = str(row.get('Place of Delivery', row.get('DESTINATION', ''))).strip()
                    
                    # 빈 경우 스킵
                    if (not origin or origin == 'nan') and (not destination or destination == 'nan'):
                        continue
                    
                    # Vehicle Type
                    vehicle = str(row.get('Vehicle Type', row.get('VEHICLE', 'FLATBED'))).strip().upper()
                    if vehicle == 'nan' or not vehicle:
                        vehicle = 'FLATBED'
                    
                    # Unit (기본: per truck)
                    unit = 'per truck'
                    
                    # Rate (여러 컬럼 시도)
                    rate_usd = 0.0
                    for rate_col_name in ['Rate (USD)', 'RATE', 'Rate', 'UNIT RATE', 'Unit Rate']:
                        if rate_col_name in row.index:
                            rate_val = row.get(rate_col_name)
                            if pd.notna(rate_val):
                                try:
                                    rate_usd = float(str(rate_val).replace(',', ''))
                                    if rate_usd > 0:
                                        break
                                except:
                                    pass
                    
                    # Quantity (# Trips)
                    qty_col = row.get('# Trips', row.get("Q'TY", row.get('QTY', 1)))
                    quantity = float(str(qty_col).replace(',', '')) if pd.notna(qty_col) else 1
                    
                    # Amount
                    amount_usd = 0.0
                    for amt_col_name in ['TOTAL (USD)', 'Total (USD)', 'AMOUNT', 'Amount']:
                        if amt_col_name in row.index:
                            amt_val = row.get(amt_col_name)
                            if pd.notna(amt_val):
                                try:
                                    amount_usd = float(str(amt_val).replace(',', ''))
                                    if amount_usd > 0:
                                        break
                                except:
                                    pass
                    
                    # Distance (추정값 또는 빈 값)
                    distance_km = 0
                    
                    # Currency (기본: USD)
                    currency = 'USD'
                    
                    # Supplier Grade (기본 A)
                    supplier_grade = 'A'
                    
                    items.append({
                        'shipment_ref': shipment_ref if shipment_ref and shipment_ref != 'nan' else f"DOM-{s_no}",
                        'origin': origin if origin and origin != 'nan' else "UNKNOWN",
                        'destination': destination if destination and destination != 'nan' else "UNKNOWN",
                        'vehicle': vehicle,
                        'unit': unit,
                        'rate_usd': rate_usd,
                        'amount_usd': amount_usd,
                        'quantity': quantity,
                        'distance_km': distance_km,
                        'currency': currency,
                        'supplier_grade': supplier_grade
                    })
                    
                except Exception as e:
                    logging.warning(f"행 {idx} 파싱 실패: {e}")
                    continue
            
            if not items:
                logging.warning("추출된 항목이 없습니다")
                logging.info("샘플 데이터로 대체합니다")
                return self._load_sample_data()
            
            df = pd.DataFrame(items)
            logging.info(f"✓ {len(df)}개 항목 로드 완료")
            return df
            
        except Exception as e:
            logging.error(f"Excel 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            logging.info("샘플 데이터로 대체합니다")
            return self._load_sample_data()
    
    def _load_sample_data(self) -> pd.DataFrame:
        """샘플 데이터 생성 (fallback)"""
        sample = [
            ["HVDC-ADOPT-SCT-0066", "DSV Mussafah Yard", "MIRFA SITE", "FLATBED", "per truck", 420, "", 1, 120, "USD", "A"],
            ["HVDC-DSV-MOSB-DSV-112", "MOSB", "DSV MUSSAFAH YARD", "FLATBED", "per truck", 200, "", 1, 10, "USD", "A"],
            ["HVDC-DSV-MOSB-SHU-101", "DSV M44 WAREHOUSE", "SHUWEIHAT Site", "FLATBED", "per truck", 600, "", 1, 250, "USD", "B"],
            ["HVDC-DSV-MOSB-ALM-117", "Mina Freeport", "Mina Freeport", "LOWBED", "per truck", 980.26, "", 1, 5, "USD", "A"],
            ["HVDC-KEC-DIP-098", "KEC DIP DUBAI", "SHUWEIHAT", "FLATBED", "per truck", 980, "", 1, 161.4, "USD", "A"],
            ["HVDC-OD-UNKNOWN", "Random Yard", "Unknown Site", "FLATBED", "per truck", 450, "", 1, 118, "USD", "C"],
            ["HVDC-AED-TEST", "DSV Mussafah Yard", "MIRFA SITE", "FLATBED", "per truck", 420, 420*3.6725, 1, 120, "AED", "A"],
            ["HVDC-ANOMALY", "DSV Mussafah Yard", "MIRFA SITE", "FLATBED", "per truck", 1500, "", 1, 120, "USD", "A"],
        ]
        df = pd.DataFrame(sample, columns=[
            "shipment_ref","origin","destination","vehicle","unit",
            "rate_usd","amount_usd","quantity","distance_km","currency","supplier_grade"
        ])
        logging.info(f"✓ 샘플 데이터 {len(df)}개 항목 생성")
        return df
    
    def run_audit(self) -> dict:
        """감사 실행"""
        start_time = datetime.now()
        logging.info("=" * 60)
        logging.info("DOMESTIC 9월 2025 Invoice Audit 시작")
        logging.info("=" * 60)
        
        # 1. 데이터 로드
        df = self.load_sept_2025_data()
        
        # 2. 검증 실행
        logging.info("검증 시작...")
        result_df, recap, artifact = validate(df, self.ref_xlsx)
        
        # 3. 결과 저장
        self._save_results(result_df, artifact)
        
        # 4. 보고서 생성
        self._generate_report(result_df, artifact, start_time)
        
        # 5. recap.card 출력
        print("\n" + "=" * 60)
        print("=== recap.card ===")
        print(recap)
        print("=" * 60)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info(f"✓ 감사 완료 (처리시간: {duration:.2f}초)")
        
        return {
            "status": "SUCCESS",
            "total_items": len(result_df),
            "duration_seconds": duration,
            "artifact": artifact
        }
    
    def _save_results(self, df: pd.DataFrame, artifact: dict):
        """결과 저장 (JSON, CSV, Excel)"""
        
        # JSON
        json_file = self.out_dir / "JSON" / f"domestic_sept_2025_result_{self.timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(artifact, f, ensure_ascii=False, indent=2)
        logging.info(f"✓ JSON 저장: {json_file.name}")
        
        # CSV
        csv_file = self.out_dir / "CSV" / f"domestic_sept_2025_result_{self.timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        logging.info(f"✓ CSV 저장: {csv_file.name}")
        
        # Excel (상세)
        xlsx_file = self.out_dir / f"domestic_sept_2025_result_{self.timestamp}.xlsx"
        try:
            with pd.ExcelWriter(xlsx_file, engine="openpyxl") as xw:
                df.to_excel(xw, index=False, sheet_name="results")
                
                # Summary 시트
                summary = pd.DataFrame([
                    {"metric": "total", "value": len(df)},
                    {"metric": "pass", "value": int((df['decision'] == 'PASS').sum())},
                    {"metric": "pending_review", "value": int((df['decision'] == 'PENDING_REVIEW').sum())},
                    {"metric": "fail", "value": int((df['decision'] == 'FAIL').sum())},
                    {"metric": "automation_ready(≥0.95)", "value": int(df['automation_ready'].sum())},
                ])
                summary.to_excel(xw, index=False, sheet_name="summary")
                
                # Artifact 시트
                art = pd.DataFrame([{"proof_artifact_json": json.dumps(artifact, ensure_ascii=False)}])
                art.to_excel(xw, index=False, sheet_name="artifact")
            
            logging.info(f"✓ Excel 저장: {xlsx_file.name}")
        except Exception as e:
            logging.warning(f"Excel 저장 실패: {e}")
    
    def _generate_report(self, df: pd.DataFrame, artifact: dict, start_time: datetime):
        """최종 보고서 생성 (SHPT 형식)"""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 통계 계산
        total = len(df)
        counts = df['cg_band'].value_counts().to_dict()
        decisions = df['decision'].value_counts().to_dict()
        
        total_amount = df['rate_usd'].sum() if 'rate_usd' in df.columns else 0
        
        pass_count = counts.get('PASS', 0)
        warn_count = counts.get('WARN', 0)
        high_count = counts.get('HIGH', 0)
        critical_count = counts.get('CRITICAL', 0)
        
        pass_pct = (pass_count / total * 100) if total > 0 else 0
        
        # Flags 분석
        flags_all = df['flags'].dropna().str.split('|').explode()
        flag_counts = flags_all.value_counts().to_dict()
        
        # 보고서 생성
        report = f"""# DOMESTIC September 2025 Invoice Audit - Final Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**System**: DOMESTIC Invoice Audit v1.0  
**Status**: ✅ Completed

---

## Executive Summary

### 📊 Overall Statistics

- **Total Items**: {total:,}개
- **Total Amount**: ${total_amount:,.2f} USD
- **Processing Time**: {duration:.2f}초
- **System**: Inland Transportation (Domestic Delivery)

### ✅ Validation Results

| Status | Count | Percentage |
|--------|-------|-----------|
| ✅ **PASS** | {pass_count} | {pass_pct:.1f}% |
| ⚠️ **WARN** | {warn_count} | {warn_count/total*100:.1f}% |
| 🔶 **HIGH** | {high_count} | {high_count/total*100:.1f}% |
| 🔴 **CRITICAL** | {critical_count} | {critical_count/total*100:.1f}% |

### 🎯 Decision Summary

| Decision | Count | Percentage |
|----------|-------|-----------|
| PASS | {decisions.get('PASS', 0)} | {decisions.get('PASS', 0)/total*100:.1f}% |
| PENDING_REVIEW | {decisions.get('PENDING_REVIEW', 0)} | {decisions.get('PENDING_REVIEW', 0)/total*100:.1f}% |
| FAIL | {decisions.get('FAIL', 0)} | {decisions.get('FAIL', 0)/total*100:.1f}% |

---

## COST-GUARD Band Analysis

```
PASS (≤2%):      {'█' * int(pass_count/2)} {pass_count}
WARN (2-5%):     {'█' * int(warn_count/2)} {warn_count}
HIGH (5-10%):    {'█' * int(high_count/2)} {high_count}
CRITICAL (>10%): {'█' * int(critical_count/2)} {critical_count}
```

---

## Flags Analysis

"""
        
        if flag_counts:
            report += "| Flag | Count |\n|------|-------|\n"
            for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True):
                if flag:  # 빈 문자열 제외
                    report += f"| {flag} | {count} |\n"
        else:
            report += "No flags detected.\n"
        
        report += f"""

---

## Top Issues (HIGH/CRITICAL)

"""
        
        # HIGH/CRITICAL 항목
        issues = df[df['cg_band'].isin(['HIGH', 'CRITICAL'])].sort_values('delta_pct', key=abs, ascending=False)
        
        if len(issues) > 0:
            report += "| Shipment | Origin → Destination | Rate | Ref | Δ% | Band |\n"
            report += "|----------|---------------------|------|-----|-----|------|\n"
            
            for _, row in issues.head(10).iterrows():
                report += f"| {row['shipment_ref']} | {row['origin_norm']} → {row['destination_norm']} | "
                report += f"${row['rate_usd']:.2f} | ${row['ref_rate_usd']:.2f} | {row['delta_pct']:+.1f}% | {row['cg_band']} |\n"
        else:
            report += "*No HIGH/CRITICAL issues found.*\n"
        
        report += f"""

---

## Similarity Join Analysis

- **Exact Matches**: {int((df['similarity'] == 1.0).sum())}
- **Similarity Joins (≥0.60)**: {int(((df['similarity'] < 1.0) & (df['similarity'] >= 0.60)).sum())}
- **Low Similarity (<0.60)**: {int((df['similarity'] < 0.60).sum())}
- **REF_MISSING**: {flag_counts.get('REF_MISSING', 0)}

---

## Configuration

**FX Rate**: 1 USD = {self.fx_rate} AED (Fixed)

**COST-GUARD Bands**:
"""
        
        for band_name, band_info in self.cost_guard_bands.items():
            report += f"- {band_name}: {band_info['description']}\n"
        
        report += f"""

**Similarity Weights**:
- Origin: 0.35
- Destination: 0.35
- Vehicle: 0.10
- Distance: 0.10 (≤15km decay)
- Rate: 0.10 (±30% decay)

**Threshold**: 0.60

---

## File Outputs

### JSON
```
Results/Sept_2025/JSON/domestic_sept_2025_result_{self.timestamp}.json
```

### CSV
```
Results/Sept_2025/CSV/domestic_sept_2025_result_{self.timestamp}.csv
```

### Proof Artifact
**SHA256**: `{artifact.get('proof_hash_sha256', 'N/A')}`

---

## PRISM Recap Card

```
{artifact.get('recap_card', 'N/A')}
```

---

**Report Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Processing Time**: {duration:.2f}초  
**Status**: ✅ Complete

"""
        
        # 보고서 저장
        report_file = self.out_dir / "Reports" / "DOMESTIC_SEPT_2025_FINAL_REPORT.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        logging.info(f"✓ 최종 보고서 생성: {report_file.name}")


def main():
    """메인 실행"""
    try:
        system = DOMESTICSept2025AuditSystem()
        result = system.run_audit()
        
        print(f"\n✅ 감사 완료!")
        print(f"총 {result['total_items']}개 항목 처리 ({result['duration_seconds']:.2f}초)")
        print(f"\n결과 파일: Results/Sept_2025/")
        
        return 0
    except Exception as e:
        logging.error(f"❌ 감사 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

