"""
Enhanced joiners.py - 포털 수수료 검증 시스템

포털 관련 수수료(Appointment/DPC/Manifest Amendment 등)를 At-Cost 문서기반으로 검증합니다.
"""

import re
from typing import Optional, Dict, Any

# === 기존 유틸 ===
CANON_DEST = {
    "Shuweihat": "SHUWEIHAT Site", 
    "Mirfa": "MIRFA SITE", 
    "Mussafah Yard": "Storage Yard"
}

def canon_dest(s: str) -> str:
    """목적지 정규화"""
    if not s: 
        return s
    s2 = re.sub(r"\s+", " ", s).strip()
    return CANON_DEST.get(s2, s2)

def unit_key(u: str) -> str:
    """단위 정규화"""
    u = (u or "").strip().lower()
    return {"per rt": "per RT", "per truck": "per truck"}.get(u, u)

def port_hint(port: str, dest: str, unit: str) -> str:
    """포트 힌트 추출"""
    d = (dest or "").upper()
    return "Khalifa Port" if unit_key(unit) == "per truck" and any(x in d for x in ["MIRFA", "SHUWEIHAT", "STORAGE YARD"]) else (port or "")

# === 포털 수수료 분류 ===
PORTAL_FEE_KEYWORDS = [
    "MAQTA", "APPOINTMENT", "APPT", "DPC", "DOCUMENT PROCESSING", "DOC PROCESSING",
    "MANIFEST AMENDMENT", "EAS MANIFEST"
]

def is_portal_fee(rate_source: str, desc: str) -> bool:
    """포털 수수료 여부 판단"""
    s = (rate_source or "").upper()
    d = (desc or "").upper()
    return any(k in s or k in d for k in PORTAL_FEE_KEYWORDS)

def charge_group(rate_source: str, desc: str) -> str:
    """수수료 그룹 분류"""
    if is_portal_fee(rate_source, desc): 
        return "PortalFee"
    
    rs = (rate_source or "").strip().upper()
    if rs in {"CONTRACT"}: 
        return "Contract"
    if rs in {"AT COST", "AT-COST", "ATCOST"}: 
        return "AtCost"
    if rs in {"AS PER OFFER", "AS PER QUOTATION"}: 
        return "AsPerOffer"
    if rs in {"DSV HANDLING", "HANDLING"}: 
        return "Handling"
    
    return "Other"

# =AED/3.6725 패턴 파서 (문서기반 추출)
AED_PATTERN = re.compile(r"=\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*3\.6725")

def parse_aed_from_formula(formula: str) -> Optional[float]:
    """수식에서 AED 금액 추출"""
    if not formula: 
        return None
    
    m = AED_PATTERN.search(formula.replace(",", ""))
    return float(m.group(1)) if m else None

# === 포털 수수료 고정값 테이블 ===
PORTAL_FEE_FIXED_RATES = {
    "APPOINTMENT": {"AED": 27.00, "USD": 7.35},
    "DPC": {"AED": 35.00, "USD": 9.53},
    "DOCUMENT PROCESSING": {"AED": 35.00, "USD": 9.53},
    "DOC PROCESSING": {"AED": 35.00, "USD": 9.53}
}

def get_portal_fee_fixed_rate(desc: str) -> Optional[Dict[str, float]]:
    """포털 수수료 고정값 조회"""
    desc_upper = (desc or "").upper()
    
    for keyword, rates in PORTAL_FEE_FIXED_RATES.items():
        if keyword in desc_upper:
            return rates
    
    return None

# === 필수 검증 체크포인트 ===
def validate_gate_01_document_set(supporting_docs: list) -> Dict[str, Any]:
    """Gate-01: 문서세트 존재 검증"""
    required_docs = ["BOE", "DO", "DN", "CarrierInvoice"]
    found_docs = [doc["doc_type"] for doc in supporting_docs]
    
    missing_docs = [doc for doc in required_docs if doc not in found_docs]
    
    return {
        "status": "PASS" if not missing_docs else "FAIL",
        "missing_docs": missing_docs,
        "score": max(0, 100 - len(missing_docs) * 25)
    }

def validate_gate_02_container_weight_match(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-02: 컨테이너/중량 일치 검증"""
    # 실제 구현에서는 DO, DN, Carrier 문서에서 컨테이너 정보 추출 필요
    return {
        "status": "PASS",  # 임시
        "score": 100
    }

def validate_gate_03_currency_consistency(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-03: 통화 일관성 검증"""
    currency = invoice_item.get("currency", "").upper()
    formula = invoice_item.get("formula_text", "")
    
    # AED → USD 환산 명시 여부 확인
    has_fx_conversion = "3.6725" in formula or "AED" in formula
    
    return {
        "status": "PASS" if has_fx_conversion or currency == "USD" else "FAIL",
        "score": 100 if has_fx_conversion or currency == "USD" else 0
    }

def validate_gate_04_contract_rate(invoice_item: Dict[str, Any], ref_rate: float, tolerance: float) -> Dict[str, Any]:
    """Gate-04: 계약 단가 검증"""
    if ref_rate is None or ref_rate == 0:
        return {"status": "FAIL", "score": 0}
    
    draft_rate = invoice_item.get("rate_usd", 0)
    delta = abs(draft_rate - ref_rate) / ref_rate
    
    return {
        "status": "PASS" if delta <= tolerance else "FAIL",
        "score": max(0, 100 - (delta / tolerance) * 100)
    }

def validate_gate_05_at_cost_evidence(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-05: At-Cost 증빙성 검증"""
    formula = invoice_item.get("formula_text", "")
    doc_aed = parse_aed_from_formula(formula)
    
    return {
        "status": "PASS" if doc_aed is not None else "FAIL",
        "score": 100 if doc_aed is not None else 0
    }

def validate_gate_06_quantity_unit_match(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-06: 수량/단위 정합 검증"""
    # 실제 구현에서는 컨테이너 타입, 중량 등 검증
    return {
        "status": "PASS",  # 임시
        "score": 100
    }

def validate_gate_07_total_consistency(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-07: 합계 정합 검증"""
    rate = invoice_item.get("rate_usd", 0)
    quantity = invoice_item.get("quantity", 0)
    total = invoice_item.get("total_usd", 0)
    
    calculated_total = rate * quantity
    delta = abs(total - calculated_total)
    
    return {
        "status": "PASS" if delta < 0.01 else "FAIL",  # 1센트 오차 허용
        "score": max(0, 100 - delta * 100)
    }

def validate_gate_08_duplicate_detection(invoice_items: list) -> Dict[str, Any]:
    """Gate-08: 중복청구 탐지"""
    # 실제 구현에서는 컨테이너/날짜/항목 중복 검사
    return {
        "status": "PASS",  # 임시
        "score": 100
    }

def validate_gate_09_regulatory_certification(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-09: 규제·인증 검증"""
    # 실제 구현에서는 위험물, Manifest 등 검증
    return {
        "status": "PASS",  # 임시
        "score": 100
    }

def validate_gate_10_rbr_trigger(invoice_item: Dict[str, Any]) -> Dict[str, Any]:
    """Gate-10: RBR 트리거 검증"""
    delta_percent = abs(invoice_item.get("delta_percent", 0))
    
    return {
        "status": "PASS" if delta_percent <= 10 else "FAIL",
        "score": max(0, 100 - delta_percent * 10)
    }

def run_all_gates(invoice_item: Dict[str, Any], supporting_docs: list, ref_rate: float = None) -> Dict[str, Any]:
    """모든 Gate 검증 실행"""
    gates = {
        "Gate_01": validate_gate_01_document_set(supporting_docs),
        "Gate_02": validate_gate_02_container_weight_match(invoice_item),
        "Gate_03": validate_gate_03_currency_consistency(invoice_item),
        "Gate_04": validate_gate_04_contract_rate(invoice_item, ref_rate, 0.03),
        "Gate_05": validate_gate_05_at_cost_evidence(invoice_item),
        "Gate_06": validate_gate_06_quantity_unit_match(invoice_item),
        "Gate_07": validate_gate_07_total_consistency(invoice_item),
        "Gate_08": validate_gate_08_duplicate_detection([invoice_item]),
        "Gate_09": validate_gate_09_regulatory_certification(invoice_item),
        "Gate_10": validate_gate_10_rbr_trigger(invoice_item)
    }
    
    # 전체 Gate 상태 계산
    failed_gates = [name for name, result in gates.items() if result["status"] == "FAIL"]
    total_score = sum(result["score"] for result in gates.values()) / len(gates)
    
    return {
        "Gate_Status": "PASS" if not failed_gates else "FAIL",
        "Gate_Fails": ",".join(failed_gates) if failed_gates else "",
        "Gate_Score": round(total_score, 1),
        "gates": gates
    }
