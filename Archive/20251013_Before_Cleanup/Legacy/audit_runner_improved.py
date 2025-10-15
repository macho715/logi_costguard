"""
Invoice Audit System - Enhanced Audit Runner

HVDC Project 송장 감사 시스템의 메인 실행 엔진입니다.
Samsung C&T Logistics & ADNOC·DSV Partnership를 위한 송장 검증 및 비용 분석을 수행합니다.

Author: MACHO-GPT v3.4-mini
Version: 1.0.0
Created: 2025-01-27
"""

import csv
import json
import pathlib
import logging
import argparse
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum

from joiners import canon_dest, unit_key, port_hint
from rules import FIXED_FX, LAYER1_TOL, AUTOFAIL, cg_band

# 프로젝트 루트 경로 설정
ROOT = pathlib.Path(__file__).resolve().parents[1]
IO = ROOT / "io"
OUT = ROOT / "out"
REF = ROOT / "py" / "refs"
LOGS = ROOT / "logs"

# 로그 디렉토리 생성 및 로깅 설정
LOGS.mkdir(exist_ok=True)
LOG = LOGS / "audit.log"

logging.basicConfig(
    filename=LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


class AuditStatus(Enum):
    """감사 상태 열거형"""
    VERIFIED = "Verified"
    PENDING_REVIEW = "Pending Review"
    REFERENCE_MISSING = "REFERENCE_MISSING"
    COST_GUARD_FAIL = "COST_GUARD_FAIL"


class AuditFlag(Enum):
    """감사 플래그 열거형"""
    OK = "OK"
    WARN = "WARN"
    CRITICAL = "CRITICAL"
    PENDING_REVIEW = "PENDING_REVIEW"


@dataclass
class RateInfo:
    """요금 정보 데이터 클래스"""
    amount: float
    currency: str
    unit: str
    tolerance: float = 0.03


@dataclass
class AuditResult:
    """감사 결과 데이터 클래스"""
    sno: Union[str, int]
    rate_source: Optional[str]
    description: Optional[str]
    draft_rate_usd: str
    qty: str
    draft_total_usd: str
    port_join: str
    destination_join: str
    cargo_type: str
    unit: str
    ref_rate_usd: str
    delta_percent: str
    cg_band: str
    status: str
    flag: str
    key: str


class InvoiceAuditError(Exception):
    """송장 감사 시스템 기본 예외 클래스"""
    pass


class FileNotFoundError(InvoiceAuditError):
    """파일을 찾을 수 없을 때 발생하는 예외"""
    pass


class DataValidationError(InvoiceAuditError):
    """데이터 검증 실패 시 발생하는 예외"""
    pass


class AuditRunner:
    """송장 감사 실행 엔진 클래스"""
    
    def __init__(self, shipment_id: str) -> None:
        """
        AuditRunner 초기화
        
        Args:
            shipment_id: 감사할 송장 ID
            
        Raises:
            ValueError: shipment_id가 비어있을 때
        """
        if not shipment_id or not shipment_id.strip():
            raise ValueError("shipment_id는 비어있을 수 없습니다")
        
        self.shipment_id = shipment_id.strip()
        self.ref_index: Dict[Tuple[str, str, str, str], float] = {}
        self.audit_results: List[AuditResult] = []
        
        logger.info(f"AuditRunner 초기화 완료: shipment_id={self.shipment_id}")
    
    def load_reference_data(self, filename: str) -> List[Dict[str, Any]]:
        """
        참조 데이터 파일 로드
        
        Args:
            filename: 참조 데이터 파일명
            
        Returns:
            참조 데이터 레코드 리스트
            
        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때
            json.JSONDecodeError: JSON 파싱 실패 시
        """
        file_path = REF / filename
        
        if not file_path.exists():
            logger.warning(f"참조 데이터 파일을 찾을 수 없습니다: {file_path}")
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 데이터 구조에 따라 레코드 추출
            if isinstance(data, dict):
                records = data.get("records", data)
            else:
                records = data
                
            logger.info(f"참조 데이터 로드 완료: {filename}, 레코드 수: {len(records)}")
            return records
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {filename}, 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"참조 데이터 로드 실패: {filename}, 오류: {e}")
            raise
    
    def build_reference_index(self, records: List[Dict[str, Any]]) -> Dict[Tuple[str, str, str, str], float]:
        """
        참조 데이터 인덱스 구축
        
        Args:
            records: 참조 데이터 레코드 리스트
            
        Returns:
            참조 데이터 인덱스 딕셔너리
        """
        index = {}
        
        for record in records:
            try:
                # 필수 필드 추출 및 정규화
                cargo_type = (record.get("cargo_type") or "").strip()
                port = (record.get("port") or "").strip()
                destination = (record.get("destination") or "") or ""
                unit = (record.get("unit") or "").strip()
                
                # 요금 정보 추출
                rate_data = record.get("rate", {})
                if isinstance(rate_data, dict):
                    rate_amount = rate_data.get("amount")
                else:
                    rate_amount = record.get("rate")
                
                if rate_amount is None:
                    continue
                
                # 정규화된 키 생성
                key = (
                    cargo_type,
                    port,
                    canon_dest(destination),
                    unit_key(unit)
                )
                
                index[key] = float(rate_amount)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"참조 데이터 레코드 건너뛰기: {e}, 레코드: {record}")
                continue
        
        logger.info(f"참조 데이터 인덱스 구축 완료: {len(index)}개 레코드")
        return index
    
    def merge_reference_data(self) -> Dict[Tuple[str, str, str, str], float]:
        """
        모든 참조 데이터 병합
        
        Returns:
            병합된 참조 데이터 인덱스
        """
        reference_files = [
            "air_cargo_rates.json",
            "container_cargo_rates.json", 
            "bulk_cargo_rates.json"
        ]
        
        merged_index = {}
        
        for filename in reference_files:
            try:
                records = self.load_reference_data(filename)
                file_index = self.build_reference_index(records)
                merged_index.update(file_index)
                logger.info(f"참조 데이터 병합 완료: {filename}")
            except Exception as e:
                logger.error(f"참조 데이터 병합 실패: {filename}, 오류: {e}")
                continue
        
        self.ref_index = merged_index
        logger.info(f"전체 참조 데이터 병합 완료: {len(merged_index)}개 레코드")
        return merged_index
    
    def parse_amount(self, value: str, currency: str) -> Tuple[float, str]:
        """
        금액 파싱 및 통화 정규화
        
        Args:
            value: 금액 문자열
            currency: 통화 코드
            
        Returns:
            (금액, 정규화된 통화) 튜플
            
        Raises:
            ValueError: 금액 파싱 실패 시
        """
        try:
            amount = float(value)
            normalized_currency = "USD" if (currency or "USD").upper() == "USD" else currency
            return amount, normalized_currency
        except (ValueError, TypeError) as e:
            logger.error(f"금액 파싱 실패: value={value}, currency={currency}, 오류: {e}")
            raise ValueError(f"유효하지 않은 금액 형식: {value}")
    
    def process_invoice_row(self, row: Dict[str, str], row_number: int) -> AuditResult:
        """
        송장 행 처리 및 감사 결과 생성
        
        Args:
            row: CSV 행 데이터
            row_number: 행 번호
            
        Returns:
            감사 결과 객체
        """
        try:
            # 기본 필드 추출
            cargo_type = (row.get("CargoType") or "").strip()
            port = (row.get("Port") or "").strip()
            destination = canon_dest(row.get("Destination") or "")
            unit = unit_key(row.get("Unit") or "")
            
            # 포트 힌트 적용
            port_join = port_hint(port, destination, unit) or port
            
            # 금액 파싱
            rate_charged = row.get("Rate_Charged") or "0"
            currency = row.get("Currency") or "USD"
            amount, normalized_currency = self.parse_amount(rate_charged, currency)
            
            # 참조 데이터 조회
            key = (cargo_type, port_join, destination, unit)
            ref_rate = self.ref_index.get(key)
            
            # 감사 상태 및 플래그 결정
            if ref_rate is None:
                status = AuditStatus.REFERENCE_MISSING.value
                flag = AuditFlag.PENDING_REVIEW.value
                delta_percent = ""
                cg_band_value = ""
            else:
                delta = (amount - ref_rate) / ref_rate
                delta_abs = abs(delta)
                
                within_tolerance = delta_abs <= LAYER1_TOL
                autofail = delta_abs > AUTOFAIL
                
                if within_tolerance:
                    status = AuditStatus.VERIFIED.value
                    flag = AuditFlag.OK.value
                elif autofail:
                    status = AuditStatus.COST_GUARD_FAIL.value
                    flag = AuditFlag.CRITICAL.value
                else:
                    status = AuditStatus.PENDING_REVIEW.value
                    flag = AuditFlag.WARN.value
                
                delta_percent = f"{(delta * 100):.2f}"
                cg_band_value = cg_band(delta_abs)
            
            # 감사 결과 생성
            result = AuditResult(
                sno=row.get("SNo") or row_number,
                rate_source=row.get("RateSource"),
                description=row.get("Description"),
                draft_rate_usd=f"{amount:.2f}",
                qty=row.get("Qty") or row.get("QTY") or "1",
                draft_total_usd=f"{float(row.get('Total_USD') or 0):.2f}",
                port_join=port_join,
                destination_join=destination,
                cargo_type=cargo_type,
                unit=unit,
                ref_rate_usd=f"{ref_rate:.2f}" if ref_rate is not None else "",
                delta_percent=delta_percent,
                cg_band=cg_band_value,
                status=status,
                flag=flag,
                key="|".join(key)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"송장 행 처리 실패: 행 {row_number}, 오류: {e}")
            # 기본값으로 감사 결과 생성
            return AuditResult(
                sno=row.get("SNo") or row_number,
                rate_source=row.get("RateSource"),
                description=row.get("Description"),
                draft_rate_usd="0.00",
                qty="1",
                draft_total_usd="0.00",
                port_join=port,
                destination_join=destination,
                cargo_type=cargo_type,
                unit=unit,
                ref_rate_usd="",
                delta_percent="",
                cg_band="",
                status=AuditStatus.REFERENCE_MISSING.value,
                flag=AuditFlag.CRITICAL.value,
                key="ERROR"
            )
    
    def save_audit_results(self, results: List[AuditResult], output_path: pathlib.Path) -> None:
        """
        감사 결과를 CSV 파일로 저장
        
        Args:
            results: 감사 결과 리스트
            output_path: 출력 파일 경로
            
        Raises:
            IOError: 파일 저장 실패 시
        """
        try:
            # 출력 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # CSV 파일 작성
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                if results:
                    fieldnames = [
                        "SNo", "RateSource", "Description", "DraftRate_USD", "Qty",
                        "DraftTotal_USD", "Port(Join)", "Destination(Join)", "CargoType",
                        "Unit", "Ref_Rate_USD", "Delta_%", "CG_Band", "Status", "Flag", "Key"
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for result in results:
                        writer.writerow({
                            "SNo": result.sno,
                            "RateSource": result.rate_source,
                            "Description": result.description,
                            "DraftRate_USD": result.draft_rate_usd,
                            "Qty": result.qty,
                            "DraftTotal_USD": result.draft_total_usd,
                            "Port(Join)": result.port_join,
                            "Destination(Join)": result.destination_join,
                            "CargoType": result.cargo_type,
                            "Unit": result.unit,
                            "Ref_Rate_USD": result.ref_rate_usd,
                            "Delta_%": result.delta_percent,
                            "CG_Band": result.cg_band,
                            "Status": result.status,
                            "Flag": result.flag,
                            "Key": result.key
                        })
            
            logger.info(f"감사 결과 저장 완료: {output_path}")
            print(f"감사 결과가 저장되었습니다: {output_path}")
            
        except Exception as e:
            logger.error(f"감사 결과 저장 실패: {output_path}, 오류: {e}")
            raise IOError(f"감사 결과 저장 실패: {e}")
    
    def run_audit(self) -> None:
        """
        송장 감사 실행
        
        Raises:
            FileNotFoundError: 입력 파일을 찾을 수 없을 때
            DataValidationError: 데이터 검증 실패 시
        """
        try:
            # 입력 파일 경로 설정
            input_file = IO / f"{self.shipment_id}_Invoice_Items.csv"
            output_file = OUT / f"{self.shipment_id}_Audit_Result.csv"
            
            # 입력 파일 존재 확인
            if not input_file.exists():
                raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_file}")
            
            logger.info(f"송장 감사 시작: {self.shipment_id}")
            
            # 참조 데이터 병합
            self.merge_reference_data()
            
            # 송장 데이터 처리
            audit_results = []
            
            with open(input_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                for row_number, row in enumerate(reader, start=1):
                    try:
                        result = self.process_invoice_row(row, row_number)
                        audit_results.append(result)
                    except Exception as e:
                        logger.error(f"행 처리 실패: {row_number}, 오류: {e}")
                        continue
            
            # 감사 결과 저장
            self.save_audit_results(audit_results, output_file)
            
            # 감사 통계 출력
            self.print_audit_summary(audit_results)
            
            logger.info(f"송장 감사 완료: {self.shipment_id}")
            
        except Exception as e:
            logger.error(f"송장 감사 실패: {self.shipment_id}, 오류: {e}")
            raise
    
    def print_audit_summary(self, results: List[AuditResult]) -> None:
        """
        감사 결과 요약 출력
        
        Args:
            results: 감사 결과 리스트
        """
        total_items = len(results)
        verified_count = sum(1 for r in results if r.status == AuditStatus.VERIFIED.value)
        pending_count = sum(1 for r in results if r.status == AuditStatus.PENDING_REVIEW.value)
        missing_count = sum(1 for r in results if r.status == AuditStatus.REFERENCE_MISSING.value)
        fail_count = sum(1 for r in results if r.status == AuditStatus.COST_GUARD_FAIL.value)
        
        print(f"\n=== 감사 결과 요약 ===")
        print(f"총 처리 항목: {total_items}")
        print(f"검증 완료: {verified_count} ({verified_count/total_items*100:.1f}%)")
        print(f"검토 대기: {pending_count} ({pending_count/total_items*100:.1f}%)")
        print(f"참조 데이터 없음: {missing_count} ({missing_count/total_items*100:.1f}%)")
        print(f"비용 가드 실패: {fail_count} ({fail_count/total_items*100:.1f}%)")


def main(shipment_id: str) -> None:
    """
    메인 실행 함수
    
    Args:
        shipment_id: 감사할 송장 ID
    """
    try:
        # AuditRunner 인스턴스 생성 및 실행
        runner = AuditRunner(shipment_id)
        runner.run_audit()
        
    except Exception as e:
        logger.error(f"메인 실행 실패: {e}")
        print(f"오류가 발생했습니다: {e}")
        raise


if __name__ == "__main__":
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description="Invoice Audit System - Enhanced Version")
    parser.add_argument("--shipment", required=True, help="감사할 송장 ID")
    
    args = parser.parse_args()
    
    # 메인 함수 실행
    main(args.shipment)
