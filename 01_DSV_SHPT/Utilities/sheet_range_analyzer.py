"""
시트 범위 정확한 분석 도구

각 시트의 실제 데이터 범위를 정확히 파악하여 올바른 송장 데이터를 추출합니다.
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

class SheetRangeAnalyzer:
    """시트 범위 분석기"""
    
    def __init__(self):
        self.excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
        self.output_dir = Path("out")
        self.output_dir.mkdir(exist_ok=True)
        
    def analyze_all_sheets(self) -> Dict:
        """모든 시트의 범위 분석"""
        print("🔍 시트 범위 정확한 분석 시작")
        print("=" * 60)
        
        try:
            # Excel 파일 로드
            excel_data = pd.read_excel(self.excel_file, sheet_name=None, engine='openpyxl')
            print(f"✅ {len(excel_data)}개 시트 로드 완료")
            
            analysis_results = {}
            
            for sheet_name, df in excel_data.items():
                print(f"\n📋 시트 '{sheet_name}' 분석 중...")
                print(f"  - 원본 크기: {df.shape[0]}행 x {df.shape[1]}열")
                
                # 시트 분석
                sheet_analysis = self._analyze_sheet_structure(df, sheet_name)
                analysis_results[sheet_name] = sheet_analysis
                
                # 결과 출력
                print(f"  - 실제 데이터 행: {sheet_analysis['data_rows']}개")
                print(f"  - 헤더 행: {sheet_analysis['header_row']}")
                print(f"  - 데이터 시작 행: {sheet_analysis['data_start_row']}")
                print(f"  - 데이터 끝 행: {sheet_analysis['data_end_row']}")
                print(f"  - 추출된 송장 항목: {sheet_analysis['invoice_items_count']}개")
                
                if sheet_analysis['invoice_items_count'] > 0:
                    print(f"  - 샘플 데이터:")
                    for i, item in enumerate(sheet_analysis['sample_items'][:3]):
                        print(f"    {i+1}. {item}")
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ 분석 오류: {e}")
            return {}
    
    def _analyze_sheet_structure(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """시트 구조 분석"""
        analysis = {
            "sheet_name": sheet_name,
            "original_shape": df.shape,
            "header_row": None,
            "data_start_row": None,
            "data_end_row": None,
            "data_rows": 0,
            "invoice_items_count": 0,
            "sample_items": [],
            "header_columns": [],
            "data_columns": []
        }
        
        try:
            # 1. 헤더 행 찾기
            header_row = self._find_header_row(df)
            analysis["header_row"] = header_row
            
            if header_row is not None:
                # 2. 데이터 시작 행
                data_start_row = header_row + 1
                analysis["data_start_row"] = data_start_row
                
                # 3. 데이터 끝 행 찾기
                data_end_row = self._find_data_end_row(df, data_start_row)
                analysis["data_end_row"] = data_end_row
                
                # 4. 실제 데이터 행 수
                if data_end_row is not None:
                    data_rows = data_end_row - data_start_row + 1
                    analysis["data_rows"] = data_rows
                    
                    # 5. 송장 항목 추출
                    invoice_items = self._extract_invoice_items_from_range(
                        df, data_start_row, data_end_row, sheet_name
                    )
                    analysis["invoice_items_count"] = len(invoice_items)
                    analysis["sample_items"] = invoice_items[:5]  # 샘플 5개
                    
                    # 6. 헤더 컬럼 정보
                    if header_row is not None:
                        header_row_data = df.iloc[header_row]
                        analysis["header_columns"] = [
                            str(cell) for cell in header_row_data if pd.notna(cell)
                        ]
                
                # 7. 데이터 컬럼 정보
                if data_start_row is not None and data_end_row is not None:
                    data_section = df.iloc[data_start_row:data_end_row+1]
                    analysis["data_columns"] = list(data_section.columns)
            
            return analysis
            
        except Exception as e:
            print(f"❌ 시트 '{sheet_name}' 분석 오류: {e}")
            return analysis
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """헤더 행 찾기"""
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            
            # 헤더 키워드 검색
            header_keywords = [
                'S/No', 'Rate Source', 'Description', 'Rate', 'Formula', 
                'Qty', 'Total', 'USD', 'Bill to', 'Draft Invoice Date',
                'Shipment', 'Invoice', 'Amount', 'Currency'
            ]
            
            keyword_count = sum(1 for keyword in header_keywords if keyword in row_str)
            
            if keyword_count >= 3:  # 3개 이상 키워드 매치
                return idx
        
        return None
    
    def _find_data_end_row(self, df: pd.DataFrame, start_row: int) -> int:
        """데이터 끝 행 찾기"""
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            non_null_count = row.notna().sum()
            
            # 연속으로 빈 행이 3개 이상이면 데이터 끝
            if non_null_count == 0:
                # 다음 2행도 확인
                empty_count = 0
                for check_idx in range(idx, min(idx + 3, len(df))):
                    if df.iloc[check_idx].notna().sum() == 0:
                        empty_count += 1
                
                if empty_count >= 3:
                    return idx - 1
        
        return len(df) - 1
    
    def _extract_invoice_items_from_range(self, df: pd.DataFrame, start_row: int, end_row: int, sheet_name: str) -> List[Dict]:
        """지정된 범위에서 송장 항목 추출"""
        invoice_items = []
        
        try:
            for idx in range(start_row, min(end_row + 1, len(df))):
                row = df.iloc[idx]
                
                # 유효한 행인지 확인
                if self._is_valid_invoice_row(row):
                    item = self._create_invoice_item_from_row(row, sheet_name, idx)
                    if item:
                        invoice_items.append(item)
            
            return invoice_items
            
        except Exception as e:
            print(f"❌ 송장 항목 추출 오류: {e}")
            return []
    
    def _is_valid_invoice_row(self, row: pd.Series) -> bool:
        """유효한 송장 행인지 확인"""
        non_null_count = row.notna().sum()
        
        # 최소 3개 이상의 값이 있어야 함
        if non_null_count < 3:
            return False
        
        # 숫자 값이 있는지 확인
        has_number = False
        for cell in row:
            if pd.notna(cell):
                try:
                    float(cell)
                    has_number = True
                    break
                except:
                    continue
        
        return has_number
    
    def _create_invoice_item_from_row(self, row: pd.Series, sheet_name: str, row_idx: int) -> Dict:
        """행에서 송장 항목 생성"""
        try:
            # 기본 정보 추출
            item = {
                "sheet_name": sheet_name,
                "row_number": row_idx + 1,
                "s_no": self._extract_s_no(row),
                "description": self._extract_description(row),
                "rate": self._extract_rate(row),
                "quantity": self._extract_quantity(row),
                "total_usd": self._extract_total_usd(row),
                "currency": self._extract_currency(row),
                "raw_data": [str(cell) if pd.notna(cell) else "" for cell in row]
            }
            
            return item
            
        except Exception as e:
            print(f"❌ 송장 항목 생성 오류 (행 {row_idx}): {e}")
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
    
    def save_analysis_report(self, analysis_results: Dict) -> str:
        """분석 보고서 저장"""
        try:
            # JSON 보고서 저장
            json_file = self.output_dir / "sheet_range_analysis.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
            
            # 요약 보고서 생성
            summary_file = self.output_dir / "sheet_range_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_summary_report(analysis_results))
            
            print(f"\n📄 분석 보고서 저장 완료:")
            print(f"  - JSON: {json_file}")
            print(f"  - 요약: {summary_file}")
            
            return str(json_file)
            
        except Exception as e:
            print(f"❌ 보고서 저장 오류: {e}")
            return None
    
    def _generate_summary_report(self, analysis_results: Dict) -> str:
        """요약 보고서 생성"""
        total_sheets = len(analysis_results)
        total_invoice_items = sum(
            sheet["invoice_items_count"] for sheet in analysis_results.values()
        )
        
        report = f"""
시트 범위 분석 보고서
====================

분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Excel 파일: {self.excel_file}
총 시트 수: {total_sheets}개
총 송장 항목: {total_invoice_items}개

📊 시트별 상세 분석
------------------
"""
        
        for sheet_name, analysis in analysis_results.items():
            report += f"""
{sheet_name}:
  - 원본 크기: {analysis['original_shape'][0]}행 x {analysis['original_shape'][1]}열
  - 헤더 행: {analysis['header_row']}
  - 데이터 범위: {analysis['data_start_row']} ~ {analysis['data_end_row']}
  - 실제 데이터 행: {analysis['data_rows']}개
  - 송장 항목: {analysis['invoice_items_count']}개
  - 헤더 컬럼: {', '.join(analysis['header_columns'][:5])}...
"""
        
        report += f"""
====================
분석 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

def main():
    """메인 실행 함수"""
    print("🔍 시트 범위 정확한 분석 도구")
    print("=" * 60)
    
    # 분석기 초기화
    analyzer = SheetRangeAnalyzer()
    
    # 모든 시트 분석
    analysis_results = analyzer.analyze_all_sheets()
    
    if analysis_results:
        # 보고서 저장
        report_file = analyzer.save_analysis_report(analysis_results)
        
        if report_file:
            print(f"\n✅ 분석 완료! 보고서: {report_file}")
            
            # 전체 요약
            total_items = sum(
                sheet["invoice_items_count"] for sheet in analysis_results.values()
            )
            print(f"\n📊 전체 요약:")
            print(f"  - 총 시트 수: {len(analysis_results)}개")
            print(f"  - 총 송장 항목: {total_items}개")
        else:
            print("❌ 보고서 저장 실패")
    else:
        print("❌ 분석 실행 실패")

if __name__ == "__main__":
    main()
