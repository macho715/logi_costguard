#!/usr/bin/env python3
"""
SHPT 전용 Invoice Audit System
HVDC Project 송장 감사 시스템 - SHPT (Shipment) 전용
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

class SHPTAuditSystem:
    """SHPT 전용 송장 감사 시스템"""
    
    def __init__(self):
        self.root = Path(__file__).parent
        self.io_dir = self.root / "io"
        self.out_dir = self.root / "out"
        self.ref_dir = self.root / "ref"
        
        # SHPT 전용 설정
        self.system_type = "SHPT"
        self.scope = "Shipment Invoice Processing (Sea + Air)"
        
        # SHPT 전용 Lane Map (해상 + 항공 운송)
        self.lane_map = {
            # 해상 운송
            "KP_DSV_YD": {"lane_id": "L01", "rate": 252.00, "route": "Khalifa Port→Storage Yard"},
            "DSV_YD_MIRFA": {"lane_id": "L38", "rate": 420.00, "route": "DSV Yard→MIRFA"},
            "DSV_YD_SHUWEIHAT": {"lane_id": "L44", "rate": 600.00, "route": "DSV Yard→SHUWEIHAT"},
            "MOSB_DSV_YD": {"lane_id": "L33", "rate": 200.00, "route": "MOSB→DSV Yard"},
            # 항공 운송
            "AUH_DSV_MUSSAFAH": {"lane_id": "A01", "rate": 100.00, "route": "AUH Airport→DSV Mussafah (3T PU)"}
        }
        
        # SHPT 전용 COST-GUARD 밴드
        self.cost_guard_bands = {
            "PASS": {"max_delta": 2.00, "description": "≤2.00%"},
            "WARN": {"max_delta": 5.00, "description": "2.01-5.00%"},
            "HIGH": {"max_delta": 10.00, "description": "5.01-10.00%"},
            "CRITICAL": {"max_delta": float('inf'), "description": ">10.00%"}
        }
        
        # FX 고정 환율
        self.fx_rate = 3.6725  # 1 USD = 3.6725 AED
        
        # SHPT 전용 계약 정보
        self.contract_info = {
            "contract_no": "HVDC-SHPT-2025-001",
            "incoterm": "FOB/DDP/CIP (assumed)",
            "currency": "USD/AED",
            "fx_rate": self.fx_rate,
            "validity": "2025-01-01 ~ 2025-12-31",
            "parties": "Samsung C&T / ADNOC L&S / DSV (3PL)",
            "scope": "SHPT - Shipment Invoice Processing (Sea + Air)"
        }
        
        # SHPT 전용 정규화 맵 (해상 + 항공)
        self.normalization_map = {
            "port": {
                "Khalifa Port": "KP",
                "Jebel Ali Port": "JAP",
                "Abu Dhabi Port": "ADP",
                "Abu Dhabi Airport": "AUH",
                "Dubai Airport": "DXB"
            },
            "destination": {
                "MIRFA SITE": "MIRFA",
                "SHUWEIHAT Site": "SHUWEIHAT", 
                "DSV MUSSAFAH YARD": "DSV Yard",
                "Storage Yard": "DSV Yard",
                "DSV Mussafah": "DSV Yard"
            },
            "unit": {
                "per truck": "per truck",
                "per RT": "per truck",
                "per cntr": "per cntr",
                "per BL": "per BL",
                "per KG": "per KG",
                "per EA": "per EA",
                "per Trip": "per Trip",
                "per Day": "per Day"
            }
        }
        
        # SHPT 전용 표준 라인 아이템 스펙
        self.standard_line_items = {
            "DOC-DO": {
                "description": "MASTER DO FEE",
                "uom": "per BL",
                "unit_rate": 150.00,
                "cost_center": "DOC",
                "port_wh": "KP",
                "evidence_ref": "Contract Amendment (assumed)"
            },
            "CUS-CLR": {
                "description": "CUSTOMS CLEARANCE FEE", 
                "uom": "per shipment",
                "unit_rate": 150.00,
                "cost_center": "CUSTOMS",
                "port_wh": "KP/AUH",
                "evidence_ref": "Contract Amendment (assumed)"
            },
            "THC-20": {
                "description": "TERMINAL HANDLING FEE (20DC)",
                "uom": "per cntr",
                "unit_rate": 372.00,
                "cost_center": "THC",
                "port_wh": "KP",
                "evidence_ref": "Contract Amendment (assumed)"
            },
            "THC-40": {
                "description": "TERMINAL HANDLING FEE (40HC)",
                "uom": "per cntr", 
                "unit_rate": 479.00,
                "cost_center": "THC",
                "port_wh": "KP",
                "evidence_ref": "Contract Amendment (assumed)"
            },
            "TRK-KP-DSV": {
                "description": "Transportation (Khalifa Port→Storage Yard)",
                "uom": "per truck",
                "unit_rate": 252.00,
                "cost_center": "TRK",
                "port_wh": "KP→DSV Yard",
                "evidence_ref": "Inland Rate Table"
            },
            "TRK-DSV-MIR": {
                "description": "Transportation (DSV Yard→MIRFA, Flatbed)",
                "uom": "per truck",
                "unit_rate": 420.00,
                "cost_center": "TRK", 
                "port_wh": "DSV→MIRFA",
                "evidence_ref": "Lane median L38"
            },
            "TRK-DSV-SHU": {
                "description": "Transportation (DSV Yard→SHUWEIHAT, Flatbed)",
                "uom": "per truck",
                "unit_rate": 600.00,
                "cost_center": "TRK",
                "port_wh": "DSV→SHU", 
                "evidence_ref": "Lane median L44"
            },
            # 항공 운송 라인 아이템 (SIM-0092 기준)
            "AIR-DO": {
                "description": "Master DO Fee (Air)",
                "uom": "per EA",
                "unit_rate": 80.00,
                "cost_center": "DOC",
                "port_wh": "AUH Cargo",
                "evidence_ref": "BOE/DO"
            },
            "AIR-CLR": {
                "description": "Customs Clearance Fee (Air)",
                "uom": "per EA",
                "unit_rate": 150.00,
                "cost_center": "CUSTOMS",
                "port_wh": "AUH Cargo",
                "evidence_ref": "BOE"
            },
            "ATH": {
                "description": "Airport Terminal Handling",
                "uom": "per KG",
                "unit_rate": 0.55,
                "cost_center": "THC",
                "port_wh": "AUH",
                "evidence_ref": "DN/Appt"
            },
            "AIR-TRANSPORT": {
                "description": "Transport AUH→DSV (3T PU)",
                "uom": "per Trip",
                "unit_rate": 100.00,
                "cost_center": "TRK",
                "port_wh": "AUH→Mussafah",
                "evidence_ref": "DN"
            },
            "APPOINTMENT": {
                "description": "Appointment Fee",
                "uom": "per EA",
                "unit_rate": 7.35,  # 27 AED / 3.6725
                "cost_center": "PORT",
                "port_wh": "ATLP",
                "evidence_ref": "Appt=27 AED"
            },
            "DPC": {
                "description": "DPC Fee",
                "uom": "per EA",
                "unit_rate": 9.53,  # 35 AED / 3.6725
                "cost_center": "PORT",
                "port_wh": "ATLP",
                "evidence_ref": "DPC=35 AED"
            },
            "AIR-STORAGE": {
                "description": "Airport Storage",
                "uom": "per Day",
                "unit_rate": 912.62,  # 3,351.60 AED / 3.6725
                "cost_center": "STORAGE",
                "port_wh": "EASC",
                "evidence_ref": "Storage=3,351.60 AED"
            }
        }
        
        # SHPT 전용 검증 규칙
        self.validation_rules = {
            "R-001": {
                "check_type": "금액계산",
                "logic": "ExtAmount = ROUND(UnitRate*Qty,2)",
                "severity": "HIGH",
                "auto_fix": "재계산",
                "evidence": "—"
            },
            "R-002": {
                "check_type": "요율출처",
                "logic": "JOIN key={Category,Port,Destination,Unit} in RateTable → if miss → LaneMap median",
                "severity": "HIGH", 
                "auto_fix": "Lane median로 대체",
                "evidence": "Inland Trucking·LaneMap"
            },
            "R-003": {
                "check_type": "Δ% 밴드",
                "logic": "Δ% = (Draft−Std)/Std → PASS/WARN/HIGH/CRITICAL",
                "severity": "HIGH",
                "auto_fix": "N/A",
                "evidence": "COST-GUARD"
            },
            "R-004": {
                "check_type": "단위정합",
                "logic": "per RT↔per truck 불일치 시 변환금지(가정: 합의 전)",
                "severity": "MED",
                "auto_fix": "알림만",
                "evidence": "LaneMap 주의"
            },
            "R-005": {
                "check_type": "FX고정",
                "logic": "통화는 USD 유지, 병기 시 USD×3.6725=AED",
                "severity": "MED",
                "auto_fix": "자동환산",
                "evidence": "FX 정책"
            },
            "R-006": {
                "check_type": "포트·지명 정규화",
                "logic": "NormalizationMap 사전 매핑 적용",
                "severity": "MED",
                "auto_fix": "자동치환",
                "evidence": "통합 엑셀 사전"
            },
            "R-007": {
                "check_type": "Incoterms",
                "logic": "FOB 가정하 Shipment 부대비용 3PL 귀속",
                "severity": "MED",
                "auto_fix": "태깅",
                "evidence": "—"
            },
            "R-008": {
                "check_type": "증빙필수(At-cost)",
                "logic": "영수증/승인메일 없으면 PENDING_REVIEW",
                "severity": "HIGH",
                "auto_fix": "N/A",
                "evidence": "—"
            },
            # 항공 운송 전용 검증 규칙 (SIM-0092 기준)
            "R-A01": {
                "check_type": "ATH 계산",
                "logic": "ATH = 0.55 * chargeable_kg",
                "severity": "HIGH",
                "auto_fix": "Recalc",
                "evidence": "ATLP Terminal"
            },
            "R-A02": {
                "check_type": "FX 고정",
                "logic": "FX == 3.6725 (AED/USD)",
                "severity": "HIGH",
                "auto_fix": "Lock FX",
                "evidence": "Spec"
            },
            "R-A03": {
                "check_type": "Storage 환산",
                "logic": "Storage(AED) from EASC == draft*FX",
                "severity": "MED",
                "auto_fix": "Convert FX",
                "evidence": "EASC Screen"
            },
            "R-A04": {
                "check_type": "식별자 일치",
                "logic": "MAWB & HAWB & CW & Pkg 일치",
                "severity": "HIGH",
                "auto_fix": "N/A",
                "evidence": "BOE/DO/DN"
            },
            "R-A05": {
                "check_type": "금액 정합",
                "logic": "abs(draft_amt - src_amt) <= 0.01",
                "severity": "HIGH",
                "auto_fix": "Round(0.01)",
                "evidence": "All docs"
            }
        }
        
        # SHPT 전용 예외 등록부
        self.exceptions_register = {
            "EX-001": {
                "type": "Scope",
                "clause": "DG Trailer surcharge (예: HAZMAT Trailer)",
                "impact_usd": 599.05,
                "risk": "HIGH",
                "approval": "PM 승인 필수",
                "valid_from_to": "2025-01-01~2025-12-31"
            },
            "EX-002": {
                "type": "Deviation", 
                "clause": "Port Storage large variance(At-cost)",
                "impact_usd": 313.09,
                "risk": "MED",
                "approval": "Client email",
                "valid_from_to": "2025-01-01~2025-12-31"
            },
            "EX-003": {
                "type": "One-off",
                "clause": "Manifest Amendment Fee",
                "impact_usd": 100.75,
                "risk": "LOW",
                "approval": "Ops 승인",
                "valid_from_to": "2025-01-01~2025-12-31"
            }
        }
        
        # KPI 목표 (SHPT용)
        self.kpi_targets = {
            "validation_accuracy": {"target": 97.00, "unit": "%", "owner": "Ops"},
            "automation_rate": {"target": 94.00, "unit": "%", "owner": "Eng"},
            "lane_coverage": {"target": 95.00, "unit": "%", "owner": "Ops"}
        }
        
        # 로깅 설정
        logging.basicConfig(
            filename=self.out_dir / "shpt_audit.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    def normalize_data(self, data: Dict) -> Dict:
        """데이터 정규화 (포트·지명·단위)"""
        normalized = data.copy()
        
        # 포트 정규화
        if "port" in normalized:
            normalized["port"] = self.normalization_map["port"].get(
                normalized["port"], normalized["port"]
            )
            
        # 목적지 정규화
        if "destination" in normalized:
            normalized["destination"] = self.normalization_map["destination"].get(
                normalized["destination"], normalized["destination"]
            )
            
        # 단위 정규화
        if "unit" in normalized:
            normalized["unit"] = self.normalization_map["unit"].get(
                normalized["unit"], normalized["unit"]
            )
            
        return normalized
        
    def get_standard_rate(self, category: str, port: str, destination: str, unit: str) -> Optional[float]:
        """표준 요율 조회 (LaneMap 우선)"""
        
        # LaneMap에서 조회
        lane_key = f"{port}_{destination}".replace(" ", "_").upper()
        if lane_key in self.lane_map:
            return self.lane_map[lane_key]["rate"]
            
        # 정규화 후 재시도
        normalized_port = self.normalization_map["port"].get(port, port)
        normalized_dest = self.normalization_map["destination"].get(destination, destination)
        lane_key = f"{normalized_port}_{normalized_dest}".replace(" ", "_").upper()
        
        if lane_key in self.lane_map:
            return self.lane_map[lane_key]["rate"]
            
        return None
        
    def calculate_delta_percent(self, draft_rate: float, standard_rate: float) -> float:
        """Delta % 계산"""
        if standard_rate == 0:
            return float('inf')
        return round(((draft_rate - standard_rate) / standard_rate) * 100, 2)
        
    def get_cost_guard_band(self, delta_percent: float) -> str:
        """COST-GUARD 밴드 결정"""
        abs_delta = abs(delta_percent)
        
        for band, config in self.cost_guard_bands.items():
            if abs_delta <= config["max_delta"]:
                return band
                
        return "CRITICAL"
        
    def validate_shpt_invoice_item(self, item: Dict) -> Dict:
        """SHPT 송장 항목 검증"""
        
        # 데이터 정규화
        normalized_item = self.normalize_data(item)
        
        # 기본 정보 추출
        category = normalized_item.get("category", "UNKNOWN")
        port = normalized_item.get("port", "")
        destination = normalized_item.get("destination", "")
        unit = normalized_item.get("unit", "per truck")
        draft_rate = float(normalized_item.get("unit_rate", 0))
        quantity = float(normalized_item.get("quantity", 1))
        total_amount = float(normalized_item.get("total_amount", 0))
        
        # 표준 요율 조회
        standard_rate = self.get_standard_rate(category, port, destination, unit)
        
        # Delta % 계산
        if standard_rate is not None:
            delta_percent = self.calculate_delta_percent(draft_rate, standard_rate)
            cost_guard_band = self.get_cost_guard_band(delta_percent)
        else:
            delta_percent = None
            cost_guard_band = "REF_MISSING"
            
        # 검증 결과
        validation_result = {
            "s_no": item.get("s_no", ""),
            "description": item.get("description", ""),
            "category": category,
            "port": port,
            "destination": destination,
            "unit": unit,
            "draft_rate_usd": draft_rate,
            "standard_rate_usd": standard_rate,
            "delta_percent": delta_percent,
            "cost_guard_band": cost_guard_band,
            "quantity": quantity,
            "ext_amount_usd": round(draft_rate * quantity, 2),
            "total_amount_usd": total_amount,
            "validation_status": "PASS" if cost_guard_band == "PASS" else "FAIL",
            "evidence_ref": self._get_evidence_reference(category, port, destination),
            "lane_id": self._get_lane_id(port, destination),
            "validation_timestamp": datetime.now().isoformat(),
            "system_type": "SHPT"
        }
        
        return validation_result
        
    def _get_evidence_reference(self, category: str, port: str, destination: str) -> str:
        """증빙 참조 정보 생성"""
        if category in ["DOC", "CUS", "THC"]:
            return "Contract Amendment (assumed)"
        elif category == "TRK":
            lane_id = self._get_lane_id(port, destination)
            return f"Lane median {lane_id}" if lane_id else "Inland Rate Table"
        else:
            return "At-cost receipt"
            
    def _get_lane_id(self, port: str, destination: str) -> Optional[str]:
        """Lane ID 조회"""
        lane_key = f"{port}_{destination}".replace(" ", "_").upper()
        if lane_key in self.lane_map:
            return self.lane_map[lane_key]["lane_id"]
        return None
        
    def generate_shpt_report(self, validation_results: List[Dict]) -> Dict:
        """SHPT 전용 보고서 생성"""
        
        # 통계 계산
        total_items = len(validation_results)
        pass_items = len([r for r in validation_results if r["validation_status"] == "PASS"])
        fail_items = total_items - pass_items
        
        # 밴드별 분포
        band_distribution = {}
        for result in validation_results:
            band = result["cost_guard_band"]
            band_distribution[band] = band_distribution.get(band, 0) + 1
            
        # 총 금액
        total_amount = sum(r["ext_amount_usd"] for r in validation_results)
        
        # SHPT 전용 보고서 구조
        report = {
            "exec_summary": {
                "system_type": "SHPT - Shipment Invoice Processing",
                "reference_locked": "Inland Trucking 표준요율 + O/D Lane Map + Δ% 밴드(COST-GUARD)로 자동검증 프레임 고정",
                "fx_bands": f"FX 고정 1 USD = {self.fx_rate} AED; Δ≤2.00% PASS / 2.01–5.00% WARN / 5.01–10.00% HIGH / >10.00% CRITICAL",
                "lane_medians": "승인 레인 중앙값을 표준소스로 사용",
                "scope": "SHPT - Shipment Invoice Processing"
            },
            "contract_map": [
                {"Field": "Contract No", "Value": self.contract_info["contract_no"], "Note": "SHPT v1.1"},
                {"Field": "Scope", "Value": self.contract_info["scope"], "Note": "SHPT only"},
                {"Field": "Incoterm", "Value": self.contract_info["incoterm"], "Note": "Shipment by 3PL"},
                {"Field": "Currency/FX", "Value": f"USD; 1.00 USD = {self.fx_rate} AED", "Note": "Fixed"},
                {"Field": "Validity", "Value": self.contract_info["validity"], "Note": "assumed"},
                {"Field": "Parties", "Value": self.contract_info["parties"], "Note": "roles per scope"}
            ],
            "line_items": [
                {
                    "ItemCode": code,
                    "Description": spec["description"],
                    "UOM": spec["uom"],
                    "Qty": "1.00",
                    "UnitRate": f"{spec['unit_rate']:.2f}",
                    "ExtAmount": f"{spec['unit_rate']:.2f}",
                    "CostCenter": spec["cost_center"],
                    "Port/WH": spec["port_wh"],
                    "Evidence(Ref)": spec["evidence_ref"]
                }
                for code, spec in self.standard_line_items.items()
            ],
            "lane_map": [
                {
                    "LaneID": lane_id,
                    "Route": lane_info["route"],
                    "MedianRate": f"{lane_info['rate']:.2f}",
                    "Unit": "per truck",
                    "Source": "ApprovedLaneMap"
                }
                for lane_id, lane_info in self.lane_map.items()
            ],
            "validation_rules": [
                {
                    "RuleID": rule_id,
                    "CheckType": rule["check_type"],
                    "Logic/Regex/SQL": rule["logic"],
                    "Severity": rule["severity"],
                    "AutoFix": rule["auto_fix"],
                    "Evidence": rule["evidence"]
                }
                for rule_id, rule in self.validation_rules.items()
            ],
            "exceptions": [
                {
                    "ExID": ex_id,
                    "Type": ex["type"],
                    "Clause/Justification": ex["clause"],
                    "Impact(USD)": f"{ex['impact_usd']:.2f}",
                    "Risk": ex["risk"],
                    "Approval": ex["approval"],
                    "Valid-From/To": ex["valid_from_to"]
                }
                for ex_id, ex in self.exceptions_register.items()
            ],
            "statistics": {
                "total_items": total_items,
                "pass_items": pass_items,
                "fail_items": fail_items,
                "pass_rate": f"{(pass_items/total_items*100):.2f}%" if total_items > 0 else "0.00%",
                "total_amount_usd": f"{total_amount:,.2f}",
                "band_distribution": band_distribution,
                "lane_coverage": self._calculate_lane_coverage(validation_results)
            },
            "meta": {
                "version": "v1.0",
                "system_type": "SHPT",
                "generated_at": datetime.now().isoformat(),
                "tz": "Asia/Dubai",
                "currency": ["USD"]
            }
        }
        
        return report
        
    def _calculate_lane_coverage(self, validation_results: List[Dict]) -> str:
        """Lane 커버리지 계산"""
        total_items = len(validation_results)
        if total_items == 0:
            return "0.00%"
            
        covered_items = len([r for r in validation_results if r["standard_rate_usd"] is not None])
        coverage = (covered_items / total_items) * 100
        return f"{coverage:.2f}%"
        
    def run_shpt_audit(self, excel_file_path: str) -> Dict:
        """SHPT 전용 감사 실행"""
        
        print("🚀 SHPT 전용 Invoice Audit System 실행")
        print("=" * 60)
        
        # Excel 파일 로드
        try:
            xls = pd.ExcelFile(excel_file_path, engine='openpyxl')
            sheet_names = xls.sheet_names
            print(f"✅ {len(sheet_names)}개 시트 로드 완료")
        except Exception as e:
            print(f"❌ Excel 파일 로드 실패: {e}")
            return {}
            
        all_validation_results = []
        
        # 각 시트 처리
        for sheet_name in sheet_names:
            print(f"\n📋 시트 '{sheet_name}' 처리 중...")
            
            try:
                df = xls.parse(sheet_name, header=None)
                
                # 헤더 및 데이터 범위 찾기
                header_row, data_start, data_end = self._find_data_range(df)
                
                if header_row is not None:
                    # 헤더를 기준으로 데이터프레임 재구성
                    df_with_header = xls.parse(sheet_name, header=header_row)
                    df_with_header = df_with_header.dropna(how='all')
                    
                    # SHPT 송장 항목 추출 및 검증
                    for idx, row in df_with_header.iterrows():
                        if pd.notna(row.get('S/No', '')) and str(row.get('S/No', '')).strip().isdigit():
                            
                            # 송장 항목 데이터 구성
                            item_data = {
                                "s_no": row.get('S/No', ''),
                                "description": row.get('Description', ''),
                                "category": self._categorize_item(row.get('Description', '')),
                                "port": row.get('Port', ''),
                                "destination": row.get('Destination', ''),
                                "unit": row.get('Unit', 'per truck'),
                                "unit_rate": row.get('Rate', 0),
                                "quantity": row.get('Qty', 1),
                                "total_amount": row.get('Total (USD)', 0)
                            }
                            
                            # SHPT 검증 실행
                            validation_result = self.validate_shpt_invoice_item(item_data)
                            validation_result["sheet_name"] = sheet_name
                            validation_result["row_number"] = header_row + idx + 1
                            
                            all_validation_results.append(validation_result)
                    
                    print(f"  ✅ {len([r for r in all_validation_results if r['sheet_name'] == sheet_name])}개 SHPT 송장 항목 검증 완료")
                    
            except Exception as e:
                print(f"  ❌ 시트 '{sheet_name}' 처리 중 오류: {e}")
                continue
                
        # SHPT 전용 보고서 생성
        print(f"\n📄 SHPT 보고서 생성 중...")
        report = self.generate_shpt_report(all_validation_results)
        
        # 출력 디렉토리 생성
        self.out_dir.mkdir(exist_ok=True)
        
        # JSON 보고서 저장
        json_path = self.out_dir / "shpt_audit_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # CSV 보고서 저장
        csv_path = self.out_dir / "shpt_audit_report.csv"
        df_results = pd.DataFrame(all_validation_results)
        df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 요약 텍스트 보고서 저장
        summary_path = self.out_dir / "shpt_audit_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("SHPT 전용 Invoice Audit System 보고서\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Excel 파일: {excel_file_path}\n")
            f.write(f"시스템 유형: SHPT - Shipment Invoice Processing\n")
            f.write(f"총 시트 수: {len(sheet_names)}개\n")
            f.write(f"총 송장 항목: {len(all_validation_results)}개\n")
            f.write(f"PASS: {report['statistics']['pass_items']}개 ({report['statistics']['pass_rate']})\n")
            f.write(f"FAIL: {report['statistics']['fail_items']}개\n")
            f.write(f"총 금액: ${report['statistics']['total_amount_usd']} USD\n")
            f.write(f"Lane 커버리지: {report['statistics']['lane_coverage']}\n\n")
            f.write("COST-GUARD 밴드 분포:\n")
            for band, count in report['statistics']['band_distribution'].items():
                f.write(f"  {band}: {count}개\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("SHPT 전용 송장 감사 완료\n")
            
        print(f"📄 SHPT 보고서 저장 완료:")
        print(f"  - JSON: {json_path}")
        print(f"  - CSV: {csv_path}")
        print(f"  - 요약: {summary_path}")
        
        print(f"\n✅ SHPT 감사 완료!")
        print(f"📊 최종 요약:")
        print(f"  - 시스템 유형: SHPT - Shipment Invoice Processing")
        print(f"  - 총 송장 항목: {len(all_validation_results)}개")
        print(f"  - PASS: {report['statistics']['pass_items']}개 ({report['statistics']['pass_rate']})")
        print(f"  - FAIL: {report['statistics']['fail_items']}개")
        print(f"  - 총 금액: ${report['statistics']['total_amount_usd']} USD")
        print(f"  - Lane 커버리지: {report['statistics']['lane_coverage']}")
        
        return report
        
    def _find_data_range(self, df: pd.DataFrame) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """데이터 범위 찾기"""
        header_keywords = ["S/No", "Description", "Rate", "Quantity", "Total (USD)"]
        
        # 헤더 행 찾기
        header_row = None
        for i in range(min(10, len(df))):
            row_str = df.iloc[i].astype(str).str.upper().tolist()
            matched_keywords = [kw for kw in header_keywords if any(kw in s for s in row_str)]
            if len(matched_keywords) >= 3:
                header_row = i
                break
                
        if header_row is None:
            return None, None, None
            
        # 데이터 시작 행
        data_start = header_row + 1
        
        # 데이터 끝 행 찾기
        data_end = len(df) - 1
        for i in range(data_start, len(df)):
            if df.iloc[i].dropna().empty:
                data_end = i - 1
                break
                
        return header_row, data_start, data_end
        
    def _categorize_item(self, description: str) -> str:
        """항목 카테고리 분류"""
        desc_upper = description.upper()
        
        if "MASTER DO" in desc_upper:
            return "DOC"
        elif "CUSTOMS" in desc_upper:
            return "CUS"
        elif "TERMINAL HANDLING" in desc_upper:
            return "THC"
        elif "TRANSPORTATION" in desc_upper or "TRUCK" in desc_upper:
            return "TRK"
        elif "AIRPORT" in desc_upper:
            return "AIR"
        elif "PORT" in desc_upper:
            return "PORT"
        else:
            return "OTHER"
    
    def calculate_ath(self, chargeable_kg: float) -> float:
        """Airport Terminal Handling 계산 (0.55/kg)"""
        return round(0.55 * chargeable_kg, 2)
    
    def convert_aed_to_usd(self, aed_amount: float) -> float:
        """AED를 USD로 환산 (고정 환율 3.6725)"""
        return round(aed_amount / self.fx_rate, 2)
    
    def convert_usd_to_aed(self, usd_amount: float) -> float:
        """USD를 AED로 환산 (고정 환율 3.6725)"""
        return round(usd_amount * self.fx_rate, 2)
    
    def validate_air_invoice_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """항공 운송 송장 항목 검증 (SIM-0092 기준)"""
        validation_result = {
            "item_code": item.get("ItemCode", ""),
            "description": item.get("Description", ""),
            "status": "PASS",
            "issues": [],
            "validations": {}
        }
        
        # R-A01: ATH 계산 검증
        if "ATH" in item.get("Description", "").upper():
            expected_ath = self.calculate_ath(item.get("Qty", 0))
            actual_ath = item.get("UnitRate", 0) * item.get("Qty", 0)
            if abs(expected_ath - actual_ath) > 0.01:
                validation_result["status"] = "FAIL"
                validation_result["issues"].append(f"ATH 계산 오류: 예상 {expected_ath}, 실제 {actual_ath}")
            validation_result["validations"]["ath_calculation"] = {
                "expected": expected_ath,
                "actual": actual_ath,
                "delta": abs(expected_ath - actual_ath)
            }
        
        # R-A02: FX 고정 검증
        if "AED" in str(item.get("UnitRate", "")):
            aed_amount = float(str(item.get("UnitRate", "0")).replace("AED", "").strip())
            expected_usd = self.convert_aed_to_usd(aed_amount)
            if abs(expected_usd - item.get("UnitRate", 0)) > 0.01:
                validation_result["status"] = "FAIL"
                validation_result["issues"].append(f"FX 환산 오류: AED {aed_amount} → USD {expected_usd}")
            validation_result["validations"]["fx_conversion"] = {
                "aed_amount": aed_amount,
                "expected_usd": expected_usd,
                "actual_usd": item.get("UnitRate", 0)
            }
        
        # R-A05: 금액 정합 검증
        expected_total = item.get("UnitRate", 0) * item.get("Qty", 0)
        actual_total = item.get("ExtAmount", 0)
        if abs(expected_total - actual_total) > 0.01:
            validation_result["status"] = "FAIL"
            validation_result["issues"].append(f"금액 정합 오류: 예상 {expected_total}, 실제 {actual_total}")
        validation_result["validations"]["amount_consistency"] = {
            "expected": expected_total,
            "actual": actual_total,
            "delta": abs(expected_total - actual_total)
        }
        
        return validation_result
    
    def run_air_import_audit(self, excel_file_path: str) -> Optional[Dict[str, Any]]:
        """항공 운송 전용 감사 실행 (SIM-0092 기준)"""
        try:
            # Excel 파일 로드
            excel_file = pd.ExcelFile(excel_file_path)
            sheet_names = excel_file.sheet_names
            
            print(f"📋 항공 운송 감사 시작: {excel_file_path}")
            print(f"📊 총 {len(sheet_names)}개 시트 발견")
            
            all_validation_results = []
            
            for sheet_name in sheet_names:
                print(f"\n🔍 시트 분석: {sheet_name}")
                
                # 시트 데이터 로드
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                
                # 빈 시트 건너뛰기
                if df.empty:
                    print(f"   ⚠️ 빈 시트: {sheet_name}")
                    continue
                
                # 항공 운송 관련 라인 아이템 찾기 (SIM0092 형식)
                air_items = []
                for idx, row in df.iterrows():
                    # SIM0092 시트의 컬럼 구조에 맞게 수정
                    description = str(row.get("Unnamed: 3", "")).upper()  # DESCRIPTION은 Unnamed: 3
                    if any(keyword in description for keyword in ["DO", "CLEARANCE", "TERMINAL HANDLING", "TRANSPORT", "APPOINTMENT", "DOCUMENTATION PROCESSING", "STORAGE"]):
                        # S/No 컬럼에서 항목 번호 확인 (Unnamed: 1이 S/No)
                        s_no = row.get("Unnamed: 1", "")
                        if str(s_no).isdigit() and int(s_no) >= 1:
                            try:
                                # 안전한 숫자 변환 (RATE, Q'TY, TOTAL 컬럼)
                                unit_rate = 0
                                qty = 0
                                ext_amount = 0
                                
                                # RATE 컬럼 (Unnamed: 4)
                                if pd.notna(row.get("Unnamed: 4")):
                                    unit_rate = float(str(row.get("Unnamed: 4", 0)).replace(',', ''))
                                # Q'TY 컬럼 (Unnamed: 5)  
                                if pd.notna(row.get("Unnamed: 5")):
                                    qty = float(str(row.get("Unnamed: 5", 0)).replace(',', ''))
                                # TOTAL 컬럼 (Unnamed: 6)
                                if pd.notna(row.get("Unnamed: 6")):
                                    ext_amount = float(str(row.get("Unnamed: 6", 0)).replace(',', ''))
                                
                                air_items.append({
                                    "ItemCode": f"L{s_no}",
                                    "Description": row.get("Unnamed: 3", ""),  # DESCRIPTION (Unnamed: 3)
                                    "RateSource": row.get("Unnamed: 2", ""),  # RATE SOURCE (Unnamed: 2)
                                    "UnitRate": unit_rate,
                                    "Qty": qty,
                                    "ExtAmount": ext_amount,
                                    "Remark": row.get("Unnamed: 7", ""),
                                    "UOM": "per EA",  # 기본값
                                    "CostCenter": "",
                                    "HS_Code": "",
                                    "Port_WH": "",
                                    "Evidence_Ref": "Supporting documents provided"
                                })
                            except (ValueError, TypeError) as e:
                                print(f"   ⚠️ 데이터 변환 오류 (행 {idx}): {e}")
                                continue
                
                print(f"   ✈️ 항공 운송 항목 {len(air_items)}개 발견")
                
                # 각 항목 검증
                for item in air_items:
                    validation_result = self.validate_air_invoice_item(item)
                    validation_result["sheet_name"] = sheet_name
                    all_validation_results.append(validation_result)
            
            # 통계 계산
            total_items = len(all_validation_results)
            pass_items = sum(1 for r in all_validation_results if r["status"] == "PASS")
            fail_items = total_items - pass_items
            pass_rate = (pass_items / total_items * 100) if total_items > 0 else 0
            
            # 보고서 생성
            report = {
                "audit_info": {
                    "system_type": "SHPT - Air Import",
                    "audit_date": datetime.now().isoformat(),
                    "excel_file": excel_file_path,
                    "total_sheets": len(sheet_names),
                    "total_items": total_items
                },
                "statistics": {
                    "pass_items": pass_items,
                    "fail_items": fail_items,
                    "pass_rate": f"{pass_rate:.1f}%"
                },
                "validation_results": all_validation_results,
                "air_specific_validations": {
                    "ath_calculation": "0.55 USD/kg",
                    "fx_rate": "3.6725 AED/USD",
                    "appointment_fee": "27 AED (7.35 USD)",
                    "dpc_fee": "35 AED (9.53 USD)",
                    "storage_fee": "3,351.60 AED (912.62 USD)"
                }
            }
            
            # JSON 보고서 저장
            json_path = self.out_dir / "shpt_air_audit_report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # CSV 보고서 저장
            csv_path = self.out_dir / "shpt_air_audit_report.csv"
            df_results = pd.DataFrame(all_validation_results)
            df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 요약 텍스트 보고서 저장
            summary_path = self.out_dir / "shpt_air_audit_summary.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("SHPT 항공 운송 전용 Invoice Audit System 보고서\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Excel 파일: {excel_file_path}\n")
                f.write(f"시스템 유형: SHPT - Air Import (SIM-0092 기준)\n")
                f.write(f"총 시트 수: {len(sheet_names)}개\n")
                f.write(f"총 송장 항목: {total_items}개\n")
                f.write(f"PASS: {pass_items}개 ({pass_rate:.1f}%)\n")
                f.write(f"FAIL: {fail_items}개 ({100-pass_rate:.1f}%)\n\n")
                f.write("항공 운송 전용 검증 규칙:\n")
                f.write("- ATH 계산: 0.55 USD/kg\n")
                f.write("- FX 고정: 3.6725 AED/USD\n")
                f.write("- Appointment Fee: 27 AED (7.35 USD)\n")
                f.write("- DPC Fee: 35 AED (9.53 USD)\n")
                f.write("- Storage Fee: 3,351.60 AED (912.62 USD)\n\n")
                f.write(f"상세 결과: {json_path}\n")
                f.write(f"CSV 결과: {csv_path}\n")
            
            print(f"\n✅ 항공 운송 감사 완료!")
            print(f"   📊 총 항목: {total_items}개")
            print(f"   ✅ PASS: {pass_items}개 ({pass_rate:.1f}%)")
            print(f"   ❌ FAIL: {fail_items}개 ({100-pass_rate:.1f}%)")
            print(f"   📄 보고서: {json_path}")
            
            return report
            
        except Exception as e:
            print(f"❌ 항공 운송 감사 실행 중 오류: {e}")
            return None

def main():
    """메인 실행 함수"""
    system = SHPTAuditSystem()
    
    excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel 파일을 찾을 수 없습니다: {excel_file}")
        return
    
    print("🚀 SHPT 시스템 실행 옵션:")
    print("1. 해상 운송 감사 (기본)")
    print("2. 항공 운송 감사 (SIM-0092 기준)")
    print("3. 전체 감사 (해상 + 항공)")
    
    choice = input("\n선택하세요 (1-3, 기본값: 1): ").strip() or "1"
    
    if choice == "1":
        # 해상 운송 감사 실행
        report = system.run_shpt_audit(excel_file)
        if report:
            print("\n🎯 SHPT 해상 운송 감사 완료!")
            print("SHPT 전용 표준 보고서 형식으로 모든 결과가 생성되었습니다.")
    
    elif choice == "2":
        # 항공 운송 감사 실행
        report = system.run_air_import_audit(excel_file)
        if report:
            print("\n✈️ SHPT 항공 운송 감사 완료!")
            print("SIM-0092 기준 항공 운송 전용 보고서가 생성되었습니다.")
    
    elif choice == "3":
        # 전체 감사 실행
        print("\n🌊 해상 운송 감사 실행 중...")
        sea_report = system.run_shpt_audit(excel_file)
        
        print("\n✈️ 항공 운송 감사 실행 중...")
        air_report = system.run_air_import_audit(excel_file)
        
        if sea_report and air_report:
            print("\n🎯 SHPT 전체 감사 완료!")
            print("해상 운송 + 항공 운송 통합 보고서가 생성되었습니다.")
    
    else:
        print("❌ 잘못된 선택입니다. 기본 해상 운송 감사를 실행합니다.")
        report = system.run_shpt_audit(excel_file)
        if report:
            print("\n🎯 SHPT 전용 송장 감사 완료!")
            print("SHPT 전용 표준 보고서 형식으로 모든 결과가 생성되었습니다.")

if __name__ == "__main__":
    main()
