"""
고급 Invoice Audit System 실행 스크립트

실제 Excel 파일을 처리하여 완전한 감사 보고서를 생성합니다.
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

class AdvancedAuditSystem:
    """고급 송장 감사 시스템"""
    
    def __init__(self):
        self.excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
        self.output_dir = Path("out")
        self.output_dir.mkdir(exist_ok=True)
        
        # 환율 설정
        self.fx_rates = {
            "USD_AED": 3.6725,
            "AED_USD": 1/3.6725,
            "USD_EUR": 0.85,
            "EUR_USD": 1/0.85
        }
        
        # COST-GUARD 밴드 설정
        self.cost_guard_bands = {
            "PASS": 2.00,
            "WARN": 5.00,
            "HIGH": 10.00,
            "CRITICAL": 15.00
        }
    
    def load_excel_data(self) -> Dict[str, pd.DataFrame]:
        """Excel 파일에서 모든 시트 데이터 로드"""
        try:
            print(f"📁 Excel 파일 로드 중: {self.excel_file}")
            excel_data = pd.read_excel(self.excel_file, sheet_name=None, engine='openpyxl')
            print(f"✅ {len(excel_data)}개 시트 로드 완료")
            return excel_data
        except Exception as e:
            print(f"❌ Excel 로드 오류: {e}")
            return {}
    
    def extract_invoice_data(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """시트에서 송장 데이터 추출"""
        invoice_items = []
        
        try:
            # 실제 데이터 행 찾기
            data_start_row = self._find_data_start_row(df)
            if data_start_row is None:
                return invoice_items
            
            # 데이터 추출
            for idx, row in df.iloc[data_start_row:].iterrows():
                if self._is_valid_invoice_row(row):
                    item = self._extract_invoice_item(row, sheet_name, idx)
                    if item:
                        invoice_items.append(item)
            
            return invoice_items
            
        except Exception as e:
            print(f"❌ 시트 '{sheet_name}' 데이터 추출 오류: {e}")
            return []
    
    def _find_data_start_row(self, df: pd.DataFrame) -> int:
        """실제 데이터가 시작하는 행 찾기"""
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            if any(keyword in row_str for keyword in ['Bill to:', 'Draft Invoice Date:', 'S/No', 'Rate Source']):
                return idx + 1
        return None
    
    def _is_valid_invoice_row(self, row: pd.Series) -> bool:
        """유효한 송장 행인지 확인"""
        non_null_count = row.notna().sum()
        return non_null_count > 3
    
    def _extract_invoice_item(self, row: pd.Series, sheet_name: str, row_idx: int) -> Dict:
        """행에서 송장 항목 추출"""
        try:
            # 기본 정보 추출
            item = {
                "sheet_name": sheet_name,
                "row_number": row_idx + 1,
                "s_no": self._extract_s_no(row),
                "description": self._extract_description(row),
                "rate_source": self._extract_rate_source(row),
                "rate": self._extract_rate(row),
                "quantity": self._extract_quantity(row),
                "total_usd": self._extract_total_usd(row),
                "currency": self._extract_currency(row),
                "at_cost": self._extract_at_cost(row),
                "formula": self._extract_formula(row)
            }
            
            # 계산된 필드
            item["amount_usd"] = self._calculate_amount_usd(item)
            item["delta_percent"] = self._calculate_delta_percent(item)
            item["cost_guard_band"] = self._determine_cost_guard_band(item["delta_percent"])
            item["status"] = self._determine_status(item)
            
            return item
            
        except Exception as e:
            print(f"❌ 송장 항목 추출 오류 (행 {row_idx}): {e}")
            return None
    
    def _extract_s_no(self, row: pd.Series) -> str:
        """S/No 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if cell_str.isdigit():
                    return cell_str
        return ""
    
    def _extract_description(self, row: pd.Series) -> str:
        """설명 추출"""
        descriptions = []
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if len(cell_str) > 5 and not cell_str.isdigit():
                    descriptions.append(cell_str)
        return " | ".join(descriptions[:2])
    
    def _extract_rate_source(self, row: pd.Series) -> str:
        """Rate Source 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if any(keyword in cell_str.upper() for keyword in ['CONTRACT', 'RATE', 'SOURCE']):
                    return cell_str
        return "Unknown"
    
    def _extract_rate(self, row: pd.Series) -> float:
        """Rate 추출"""
        for cell in row:
            if pd.notna(cell):
                try:
                    return float(cell)
                except:
                    continue
        return 0.0
    
    def _extract_quantity(self, row: pd.Series) -> float:
        """Quantity 추출"""
        for cell in row:
            if pd.notna(cell):
                try:
                    return float(cell)
                except:
                    continue
        return 1.0
    
    def _extract_total_usd(self, row: pd.Series) -> float:
        """Total USD 추출"""
        for cell in row:
            if pd.notna(cell):
                try:
                    return float(cell)
                except:
                    continue
        return 0.0
    
    def _extract_currency(self, row: pd.Series) -> str:
        """통화 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if len(cell_str) == 3 and cell_str.isalpha():
                    return cell_str.upper()
        return "USD"
    
    def _extract_at_cost(self, row: pd.Series) -> float:
        """At-Cost 추출"""
        for cell in row:
            if pd.notna(cell):
                try:
                    return float(cell)
                except:
                    continue
        return 0.0
    
    def _extract_formula(self, row: pd.Series) -> str:
        """Formula 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if '=' in cell_str or '*' in cell_str or '+' in cell_str:
                    return cell_str
        return ""
    
    def _calculate_amount_usd(self, item: Dict) -> float:
        """USD 금액 계산"""
        if item["currency"] == "USD":
            return item["total_usd"]
        elif item["currency"] == "AED":
            return item["total_usd"] * self.fx_rates["AED_USD"]
        else:
            return item["total_usd"]
    
    def _calculate_delta_percent(self, item: Dict) -> float:
        """Delta % 계산"""
        if item["at_cost"] > 0 and item["amount_usd"] > 0:
            return ((item["amount_usd"] - item["at_cost"]) / item["at_cost"]) * 100
        return 0.0
    
    def _determine_cost_guard_band(self, delta_percent: float) -> str:
        """COST-GUARD 밴드 결정"""
        abs_delta = abs(delta_percent)
        if abs_delta <= self.cost_guard_bands["PASS"]:
            return "PASS"
        elif abs_delta <= self.cost_guard_bands["WARN"]:
            return "WARN"
        elif abs_delta <= self.cost_guard_bands["HIGH"]:
            return "HIGH"
        elif abs_delta <= self.cost_guard_bands["CRITICAL"]:
            return "CRITICAL"
        else:
            return "COST_GUARD_FAIL"
    
    def _determine_status(self, item: Dict) -> str:
        """상태 결정"""
        if item["cost_guard_band"] == "COST_GUARD_FAIL":
            return "FAIL"
        elif item["cost_guard_band"] in ["HIGH", "CRITICAL"]:
            return "WARNING"
        else:
            return "PASS"
    
    def run_complete_audit(self) -> Dict:
        """완전한 감사 실행"""
        print("🚀 고급 Invoice Audit System 시작")
        print("=" * 60)
        
        # Excel 데이터 로드
        excel_data = self.load_excel_data()
        if not excel_data:
            return None
        
        # 모든 시트에서 송장 데이터 추출
        all_invoice_items = []
        sheet_summaries = {}
        
        for sheet_name, df in excel_data.items():
            print(f"📋 시트 '{sheet_name}' 처리 중...")
            invoice_items = self.extract_invoice_data(df, sheet_name)
            all_invoice_items.extend(invoice_items)
            
            # 시트별 요약
            sheet_summaries[sheet_name] = {
                "total_items": len(invoice_items),
                "pass_items": len([item for item in invoice_items if item["status"] == "PASS"]),
                "warning_items": len([item for item in invoice_items if item["status"] == "WARNING"]),
                "fail_items": len([item for item in invoice_items if item["status"] == "FAIL"]),
                "total_amount": sum(item["amount_usd"] for item in invoice_items)
            }
        
        # 전체 요약 계산
        total_items = len(all_invoice_items)
        pass_items = len([item for item in all_invoice_items if item["status"] == "PASS"])
        warning_items = len([item for item in all_invoice_items if item["status"] == "WARNING"])
        fail_items = len([item for item in all_invoice_items if item["status"] == "FAIL"])
        total_amount = sum(item["amount_usd"] for item in all_invoice_items)
        
        # 감사 결과 생성
        audit_result = {
            "audit_metadata": {
                "audit_date": datetime.now().isoformat(),
                "excel_file": self.excel_file,
                "total_sheets": len(excel_data),
                "total_invoice_items": total_items
            },
            "summary": {
                "total_items": total_items,
                "pass_items": pass_items,
                "warning_items": warning_items,
                "fail_items": fail_items,
                "pass_rate": (pass_items / total_items * 100) if total_items > 0 else 0,
                "total_amount_usd": total_amount,
                "average_delta_percent": sum(item["delta_percent"] for item in all_invoice_items) / total_items if total_items > 0 else 0
            },
            "cost_guard_analysis": {
                "pass_count": len([item for item in all_invoice_items if item["cost_guard_band"] == "PASS"]),
                "warn_count": len([item for item in all_invoice_items if item["cost_guard_band"] == "WARN"]),
                "high_count": len([item for item in all_invoice_items if item["cost_guard_band"] == "HIGH"]),
                "critical_count": len([item for item in all_invoice_items if item["cost_guard_band"] == "CRITICAL"]),
                "fail_count": len([item for item in all_invoice_items if item["cost_guard_band"] == "COST_GUARD_FAIL"])
            },
            "sheet_summaries": sheet_summaries,
            "invoice_items": all_invoice_items
        }
        
        return audit_result
    
    def save_audit_report(self, audit_result: Dict) -> str:
        """감사 보고서 저장"""
        try:
            # JSON 보고서 저장
            json_file = self.output_dir / "audit_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False, default=str)
            
            # CSV 보고서 저장
            csv_file = self.output_dir / "audit_report.csv"
            df = pd.DataFrame(audit_result["invoice_items"])
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            # 요약 보고서 저장
            summary_file = self.output_dir / "audit_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_summary_report(audit_result))
            
            print(f"📄 감사 보고서 저장 완료:")
            print(f"  - JSON: {json_file}")
            print(f"  - CSV: {csv_file}")
            print(f"  - 요약: {summary_file}")
            
            return str(json_file)
            
        except Exception as e:
            print(f"❌ 보고서 저장 오류: {e}")
            return None
    
    def _generate_summary_report(self, audit_result: Dict) -> str:
        """요약 보고서 생성"""
        summary = audit_result["summary"]
        cg = audit_result["cost_guard_analysis"]
        
        report = f"""
INVOICE AUDIT SYSTEM - 최종 보고서
=====================================

감사 일시: {audit_result['audit_metadata']['audit_date']}
Excel 파일: {audit_result['audit_metadata']['excel_file']}
총 시트 수: {audit_result['audit_metadata']['total_sheets']}개
총 송장 항목: {summary['total_items']}개

📊 전체 요약
-----------
✅ PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)
⚠️ WARNING: {summary['warning_items']}개
❌ FAIL: {summary['fail_items']}개
💰 총 금액: ${summary['total_amount_usd']:,.2f} USD
📈 평균 Delta: {summary['average_delta_percent']:.2f}%

🚨 COST-GUARD 분석
-----------------
🟢 PASS (≤2%): {cg['pass_count']}개
🟡 WARN (2-5%): {cg['warn_count']}개
🟠 HIGH (5-10%): {cg['high_count']}개
🔴 CRITICAL (10-15%): {cg['critical_count']}개
⚫ FAIL (>15%): {cg['fail_count']}개

📋 시트별 요약
--------------
"""
        
        for sheet_name, sheet_summary in audit_result["sheet_summaries"].items():
            report += f"""
{sheet_name}:
  - 총 항목: {sheet_summary['total_items']}개
  - PASS: {sheet_summary['pass_items']}개
  - WARNING: {sheet_summary['warning_items']}개
  - FAIL: {sheet_summary['fail_items']}개
  - 총 금액: ${sheet_summary['total_amount']:,.2f} USD
"""
        
        report += f"""
=====================================
감사 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

def main():
    """메인 실행 함수"""
    print("🚀 고급 Invoice Audit System 실행")
    print("=" * 60)
    
    # 감사 시스템 초기화
    audit_system = AdvancedAuditSystem()
    
    # 완전한 감사 실행
    audit_result = audit_system.run_complete_audit()
    
    if audit_result:
        # 보고서 저장
        report_file = audit_system.save_audit_report(audit_result)
        
        if report_file:
            print(f"\n✅ 감사 완료! 보고서: {report_file}")
            
            # 요약 출력
            summary = audit_result["summary"]
            print(f"\n📊 최종 요약:")
            print(f"  - 총 송장 항목: {summary['total_items']}개")
            print(f"  - PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)")
            print(f"  - WARNING: {summary['warning_items']}개")
            print(f"  - FAIL: {summary['fail_items']}개")
            print(f"  - 총 금액: ${summary['total_amount_usd']:,.2f} USD")
        else:
            print("❌ 보고서 저장 실패")
    else:
        print("❌ 감사 실행 실패")

if __name__ == "__main__":
    main()
