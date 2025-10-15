#!/usr/bin/env python3
"""
기존 shpt_audit_system.py를 9월 2025 데이터로 실행하는 래퍼 스크립트
코드 변경 없이 경로만 동적으로 설정
"""

import sys
from pathlib import Path

# shpt_audit_system 임포트
from shpt_audit_system import SHPTAuditSystem

# 9월 2025 데이터 경로 설정을 위한 래퍼 클래스
class SHPTSept2025Wrapper(SHPTAuditSystem):
    """SHPT 시스템 9월 2025 래퍼 (코드 변경 없음)"""
    
    def __init__(self):
        super().__init__()
        
        # 9월 경로로 오버라이드
        self.excel_file_sept = Path("Data/DSV 202509/SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm")
        self.supporting_docs_path_sept = Path("Data/DSV 202509/SCNT Import (Sept 2025) - Supporting Documents")

def main():
    """메인 실행"""
    print("🚀 SHPT 시스템 - 9월 2025 데이터 실행")
    print("=" * 60)
    
    system = SHPTSept2025Wrapper()
    
    # 9월 Excel 파일 경로
    excel_file = "Data/DSV 202509/SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm"
    
    if not Path(excel_file).exists():
        print(f"❌ Excel 파일을 찾을 수 없습니다: {excel_file}")
        return
    
    print(f"📁 Excel 파일: {excel_file}")
    print(f"📁 Supporting Docs: Data/DSV 202509/SCNT Import (Sept 2025) - Supporting Documents")
    print()
    
    # 해상 운송 감사 실행 (기본)
    print("🌊 해상 운송 감사 실행 중...")
    report = system.run_shpt_audit(excel_file)
    
    if report:
        print("\n✅ SHPT 9월 2025 감사 완료!")
        print("=" * 60)
    else:
        print("\n❌ 감사 실행 실패")

if __name__ == "__main__":
    main()

