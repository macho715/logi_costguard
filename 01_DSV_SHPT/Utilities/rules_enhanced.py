"""
Enhanced rules.py - 포털 수수료 검증 규칙

포털 수수료는 ±0.5%, 계약 라인은 ±3% 허용치를 적용합니다.
"""

# === 고정 환율 ===
FIXED_FX = {"USD_AED": 3.6725, "AED_USD": 1/3.6725}

# === 허용치 ===
CONTRACT_TOL = 0.03     # 계약 라인 ±3%
DOC_TOL = 0.005         # 포털 수수료(문서기반) ±0.5%
AUTOFAIL = 0.15         # AUTOFAIL 임계치 15%

def tolerance_for(group: str) -> float:
    """수수료 그룹별 허용치 반환"""
    return DOC_TOL if group == "PortalFee" else CONTRACT_TOL

# === Δ% 밴드 (리포트 표기) ===
CG_BANDS = [
    (0.02, "PASS"),      # ≤2%
    (0.05, "WARN"),      # 2.01-5%
    (0.10, "HIGH"),      # 5.01-10%
    (9.99, "CRITICAL")   # 10.01-15%
]

def cg_band(delta_abs: float) -> str:
    """Delta % 기반 밴드 결정"""
    for thr, name in CG_BANDS:
        if delta_abs <= thr: 
            return name
    return "CRITICAL"

# === 포털 수수료 특별 밴드 ===
PORTAL_FEE_BANDS = [
    (0.005, "PASS"),     # ≤0.5%
    (0.05, "WARN"),      # 0.51-5%
    (0.10, "HIGH"),      # 5.01-10%
    (9.99, "CRITICAL")   # 10.01-15%
]

def portal_fee_band(delta_abs: float) -> str:
    """포털 수수료 전용 밴드 결정"""
    for thr, name in PORTAL_FEE_BANDS:
        if delta_abs <= thr: 
            return name
    return "CRITICAL"

def get_band_for_group(delta_abs: float, group: str) -> str:
    """그룹별 적절한 밴드 결정"""
    if group == "PortalFee":
        return portal_fee_band(delta_abs)
    else:
        return cg_band(delta_abs)

# === 환율 변환 ===
def convert_aed_to_usd(aed_amount: float) -> float:
    """AED를 USD로 변환"""
    return round(aed_amount * FIXED_FX["AED_USD"], 2)

def convert_usd_to_aed(usd_amount: float) -> float:
    """USD를 AED로 변환"""
    return round(usd_amount * FIXED_FX["USD_AED"], 2)

# === 검증 상태 결정 ===
def determine_verification_status(delta_percent: float, group: str, ref_rate: float = None) -> tuple[str, str]:
    """
    검증 상태와 플래그 결정
    
    Returns:
        tuple: (status, flag)
    """
    if ref_rate is None or ref_rate == 0:
        return "REFERENCE_MISSING", "PENDING_REVIEW"
    
    delta_abs = abs(delta_percent)
    tolerance = tolerance_for(group)
    
    if delta_abs <= tolerance:
        return "Verified", "OK"
    elif delta_abs > AUTOFAIL:
        return "COST_GUARD_FAIL", "CRITICAL"
    else:
        return "Pending Review", "WARN"

# === 포털 수수료 특별 처리 ===
def process_portal_fee(invoice_item: dict, ref_rate: float = None) -> dict:
    """
    포털 수수료 특별 처리
    
    Args:
        invoice_item: 송장 항목 데이터
        ref_rate: 참조 요율 (USD)
    
    Returns:
        dict: 처리된 포털 수수료 데이터
    """
    from joiners_enhanced import parse_aed_from_formula, get_portal_fee_fixed_rate
    
    # 1. 수식에서 AED 금액 추출
    formula = invoice_item.get("formula_text", "")
    doc_aed = parse_aed_from_formula(formula)
    
    # 2. 고정값 테이블에서 조회
    if doc_aed is None:
        fixed_rate = get_portal_fee_fixed_rate(invoice_item.get("description", ""))
        if fixed_rate:
            doc_aed = fixed_rate["AED"]
    
    # 3. AED → USD 환산
    if doc_aed is not None:
        ref_rate = convert_aed_to_usd(doc_aed)
    
    # 4. Delta % 계산
    draft_rate = invoice_item.get("rate_usd", 0)
    if ref_rate and ref_rate > 0:
        delta_percent = ((draft_rate - ref_rate) / ref_rate) * 100
    else:
        delta_percent = 0
    
    # 5. 밴드 및 상태 결정
    delta_abs = abs(delta_percent)
    band = get_band_for_group(delta_abs, "PortalFee")
    status, flag = determine_verification_status(delta_percent, "PortalFee", ref_rate)
    
    return {
        "ref_rate_usd": ref_rate,
        "delta_percent": delta_percent,
        "band": band,
        "status": status,
        "flag": flag,
        "doc_aed": doc_aed,
        "tolerance": DOC_TOL
    }

# === 일반 수수료 처리 ===
def process_regular_fee(invoice_item: dict, ref_rate: float = None) -> dict:
    """
    일반 수수료 처리
    
    Args:
        invoice_item: 송장 항목 데이터
        ref_rate: 참조 요율 (USD)
    
    Returns:
        dict: 처리된 일반 수수료 데이터
    """
    from joiners_enhanced import charge_group
    
    group = charge_group(
        invoice_item.get("rate_source", ""), 
        invoice_item.get("description", "")
    )
    
    # Delta % 계산
    draft_rate = invoice_item.get("rate_usd", 0)
    if ref_rate and ref_rate > 0:
        delta_percent = ((draft_rate - ref_rate) / ref_rate) * 100
    else:
        delta_percent = 0
    
    # 밴드 및 상태 결정
    delta_abs = abs(delta_percent)
    band = get_band_for_group(delta_abs, group)
    status, flag = determine_verification_status(delta_percent, group, ref_rate)
    
    return {
        "ref_rate_usd": ref_rate,
        "delta_percent": delta_percent,
        "band": band,
        "status": status,
        "flag": flag,
        "group": group,
        "tolerance": tolerance_for(group)
    }

# === 통합 처리 함수 ===
def process_invoice_item(invoice_item: dict, ref_rate: float = None) -> dict:
    """
    송장 항목 통합 처리
    
    Args:
        invoice_item: 송장 항목 데이터
        ref_rate: 참조 요율 (USD)
    
    Returns:
        dict: 처리된 송장 항목 데이터
    """
    from joiners_enhanced import is_portal_fee, charge_group
    
    # 포털 수수료 여부 확인
    is_portal = is_portal_fee(
        invoice_item.get("rate_source", ""), 
        invoice_item.get("description", "")
    )
    
    if is_portal:
        return process_portal_fee(invoice_item, ref_rate)
    else:
        return process_regular_fee(invoice_item, ref_rate)

# === 검증 규칙 요약 ===
VALIDATION_RULES = {
    "fx_rates": FIXED_FX,
    "tolerances": {
        "Contract": CONTRACT_TOL,
        "PortalFee": DOC_TOL,
        "AtCost": CONTRACT_TOL,
        "Other": CONTRACT_TOL
    },
    "auto_fail_threshold": AUTOFAIL,
    "bands": {
        "regular": CG_BANDS,
        "portal_fee": PORTAL_FEE_BANDS
    }
}

def get_validation_rules() -> dict:
    """검증 규칙 반환"""
    return VALIDATION_RULES
