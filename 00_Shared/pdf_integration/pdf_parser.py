"""
DSV Document Parser Module
===========================

독립 실행 가능한 PDF 분해 모듈
HVDC Invoice Audit 시스템과 통합

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

try:
    import pdfplumber

    PDF_PLUMBER_OK = True
except ImportError:
    PDF_PLUMBER_OK = False
    logging.warning("pdfplumber not installed. Install: pip install pdfplumber")

try:
    import PyPDF2

    PYPDF2_OK = True
except ImportError:
    PYPDF2_OK = False


# ==================== Data Classes ====================


@dataclass
class DocumentHeader:
    """문서 공통 헤더"""

    doc_type: str  # BOE, DO, DN, CarrierInvoice, PortInspection
    doc_number: Optional[str] = None
    doc_date: Optional[str] = None
    item_code: Optional[str] = None  # HVDC-ADOPT-XXX-XXXX
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    parsed_at: Optional[str] = None


@dataclass
class BOEData:
    """Bill of Entry (UAE Customs Declaration)"""

    header: DocumentHeader

    # Customs Declaration
    dec_no: Optional[str] = None
    dec_date: Optional[str] = None
    dec_type: Optional[str] = None  # Import/Export
    port_type: Optional[str] = None

    # Shipment
    mbl_no: Optional[str] = None
    vessel: Optional[str] = None
    voyage_no: Optional[str] = None
    manifest_reg_no: Optional[str] = None

    # Containers
    containers: List[str] = None
    num_containers: Optional[int] = None

    # Goods
    hs_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    gross_weight_kg: Optional[float] = None
    net_weight_kg: Optional[float] = None

    # Value & Duty
    value_usd: Optional[float] = None
    value_aed: Optional[float] = None
    cif_value_aed: Optional[float] = None
    duty_aed: Optional[float] = None
    vat_aed: Optional[float] = None
    total_charges_aed: Optional[float] = None

    # Parties
    importer: Optional[str] = None
    importer_trn: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None

    # Debit Notes
    debit_notes: List[Dict[str, Any]] = None

    # Origin/Destination
    pol: Optional[str] = None  # Port of Loading
    pod: Optional[str] = None  # Port of Discharge
    country_origin: Optional[str] = None


@dataclass
class DOData:
    """Delivery Order"""

    header: DocumentHeader

    do_number: Optional[str] = None
    do_date: Optional[str] = None
    delivery_valid_until: Optional[str] = None

    # Shipment
    mbl_no: Optional[str] = None
    hbl_no: Optional[str] = None
    vessel: Optional[str] = None
    voyage_no: Optional[str] = None
    manifest_reg_no: Optional[str] = None

    # Containers
    containers: List[Dict[str, str]] = None  # [{container_no, seal_no, type, size}]
    quantity: Optional[int] = None

    # Weight & Volume
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None

    # Description
    description: Optional[str] = None
    marks_numbers: Optional[str] = None

    # Parties
    importer: Optional[str] = None
    consignee: Optional[str] = None
    shipping_line: Optional[str] = None
    agent_code: Optional[str] = None

    # Ports
    port_origin: Optional[str] = None
    port_loading: Optional[str] = None
    port_discharge: Optional[str] = None

    # Freight
    ocean_freight_usd: Optional[float] = None

    # Empty Return
    empty_return_depot: Optional[str] = None
    empty_return_location: Optional[str] = None


@dataclass
class DNData:
    """Delivery Note (Road Transport)"""

    header: DocumentHeader

    waybill_no: Optional[str] = None
    trip_no: Optional[str] = None
    printed_date: Optional[str] = None

    # Container
    container_no: Optional[str] = None
    container_type: Optional[str] = None
    container_size: Optional[str] = None
    seal_no: Optional[str] = None

    # Transport
    order_number: Optional[str] = None
    job_number: Optional[str] = None
    po_number: Optional[str] = None

    # Origin/Destination
    loading_point: Optional[str] = None
    loading_address: Optional[str] = None
    loading_country: Optional[str] = None
    offloading_address: Optional[str] = None
    offloading_country: Optional[str] = None
    destination_code: Optional[str] = None
    destination: Optional[str] = None

    # Goods
    description: Optional[str] = None
    quantity: Optional[int] = None
    qty_type: Optional[str] = None
    total_weight: Optional[float] = None
    total_volume: Optional[float] = None

    # Parties
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    consignee_name: Optional[str] = None
    consignee_address: Optional[str] = None
    carrier: Optional[str] = None

    # Vehicle
    driver_name: Optional[str] = None
    driver_mobile: Optional[str] = None
    head_plate: Optional[str] = None
    trailer_plate: Optional[str] = None
    truck_type: Optional[str] = None
    trailer_type: Optional[str] = None

    # Timing
    loading_date: Optional[str] = None
    arrival_loading_time: Optional[str] = None
    loading_start_time: Optional[str] = None
    loading_finish_time: Optional[str] = None
    arrival_offloading_time: Optional[str] = None
    offloading_start_time: Optional[str] = None
    offloading_end_time: Optional[str] = None
    asset_release_time_origin: Optional[str] = None
    asset_release_time_dest: Optional[str] = None

    # References
    do_number: Optional[str] = None
    do_validity: Optional[str] = None
    bol_number: Optional[str] = None
    shipping_line: Optional[str] = None


@dataclass
class CarrierInvoiceData:
    """Carrier/Shipping Line Invoice"""

    header: DocumentHeader

    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    payable_by: Optional[str] = None

    # BL/Booking
    bl_number: Optional[str] = None
    booking_ref: Optional[str] = None
    quote_ref: Optional[str] = None

    # Shipment
    vessel: Optional[str] = None
    voyage: Optional[str] = None
    local_voyage_ref: Optional[str] = None

    # Containers
    containers: List[str] = None
    container_types: List[Dict[str, int]] = None  # [{type: '20ST', count: 1}]

    # Ports
    load_port: Optional[str] = None
    discharge_port: Optional[str] = None
    place_receipt: Optional[str] = None
    place_delivery: Optional[str] = None
    call_date: Optional[str] = None

    # Parties
    invoice_to: Optional[str] = None
    invoice_to_address: Optional[str] = None
    payable_to: Optional[str] = None
    payable_to_address: Optional[str] = None
    customer_code: Optional[str] = None
    carrier_no: Optional[str] = None

    # Charges
    line_items: List[Dict[str, Any]] = None
    # [{description, size_type, currency, amount, tax_rate, amount_aed}]

    currency: Optional[str] = None
    total_excl_tax: Optional[float] = None
    total_vat: Optional[float] = None
    vat_rate: Optional[float] = None
    total_incl_tax: Optional[float] = None

    # Payment
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    swift: Optional[str] = None
    account_number: Optional[str] = None

    # Tax
    trn: Optional[str] = None
    invoiced_by_trn: Optional[str] = None


# ==================== PDF Parser Engine ====================


class DSVPDFParser:
    """
    DSV 선적 서류 전용 PDF 파서

    지원 문서:
    - BOE (Bill of Entry)
    - DO (Delivery Order)
    - DN (Delivery Note)
    - CarrierInvoice
    - PortInspection
    """

    def __init__(self, log_level: str = "INFO"):
        self.logger = self._setup_logger(log_level)

        if not PDF_PLUMBER_OK:
            raise ImportError("pdfplumber is required. Install: pip install pdfplumber")

    def _setup_logger(self, level: str) -> logging.Logger:
        logger = logging.getLogger("DSVPDFParser")
        logger.setLevel(getattr(logging, level.upper()))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 SHA256 해시 계산"""
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _infer_doc_type_from_filename(self, filename: str) -> str:
        """파일명에서 문서 타입 추론"""
        filename_lower = filename.lower()

        if "_boe" in filename_lower or "bill_of_entry" in filename_lower:
            return "BOE"
        elif "_do" in filename_lower or "delivery_order" in filename_lower:
            return "DO"
        elif "_dn" in filename_lower or "delivery_note" in filename_lower:
            return "DN"
        elif "_carrierinvoice" in filename_lower or "carrier_invoice" in filename_lower:
            return "CarrierInvoice"
        elif "_portcntinspection" in filename_lower or "inspection" in filename_lower:
            return "PortInspection"
        else:
            return "Unknown"

    def _extract_item_code_from_filename(self, filename: str) -> Optional[str]:
        """파일명에서 HVDC Item Code 추출"""
        # Pattern: HVDC-ADOPT-XXX-XXXX
        match = re.search(r"(HVDC-ADOPT-[A-Z0-9]+-\d+)", filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 전체 텍스트 추출"""
        text_content = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")

        return "\n".join(text_content)

    def _safe_float(self, value: str) -> Optional[float]:
        """문자열을 float로 안전하게 변환"""
        if not value:
            return None
        try:
            # 쉼표 제거 및 변환
            cleaned = str(value).replace(",", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _safe_int(self, value: str) -> Optional[int]:
        """문자열을 int로 안전하게 변환"""
        if not value:
            return None
        try:
            cleaned = str(value).replace(",", "").strip()
            return int(float(cleaned))
        except (ValueError, AttributeError):
            return None

    # ==================== BOE Parser ====================

    def _parse_boe(self, text: str, header: DocumentHeader) -> BOEData:
        """Bill of Entry 파싱"""
        boe = BOEData(header=header)

        # DEC NO
        match = re.search(r"DEC NO[:\s]*(\d{14})", text, re.IGNORECASE)
        if match:
            boe.dec_no = match.group(1)

        # DEC DATE
        match = re.search(r"DEC DATE[:\s]*(\d{2}-\d{2}-\d{4})", text, re.IGNORECASE)
        if match:
            boe.dec_date = match.group(1)

        # MBL/AWB Number
        match = re.search(
            r"B[\\\/]L[-\s]*AWB\s+No[.:]?[\s\\]*MANIF[.\s]*([A-Z0-9]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            boe.mbl_no = match.group(1)

        # Vessel
        match = re.search(
            r"EX[.\s]*VSL[:.\s]*(.+?)\s+VOY", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            boe.vessel = match.group(1).strip()

        # Voyage
        match = re.search(r"VOY[.\s]*NO[:.\s]*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            boe.voyage_no = match.group(1)

        # Manifest Reg. No
        match = re.search(r"Manifest\s+Reg[.\s]*No[.:]?\s*(\d+)", text, re.IGNORECASE)
        if match:
            boe.manifest_reg_no = match.group(1)

        # Containers
        container_pattern = r"(CMAU\d{7}|TGHU\d{7}|TCNU\d{7}|[A-Z]{4}\d{7})"
        containers = re.findall(container_pattern, text)
        if containers:
            boe.containers = list(set(containers))  # 중복 제거
            boe.num_containers = len(boe.containers)

        # HS CODE
        match = re.search(r"H[.\s]*S[.\s]*CODE[:\s]*(\d{10})", text, re.IGNORECASE)
        if match:
            boe.hs_code = match.group(1)

        # Description
        match = re.search(
            r"GOODS DESCRIPTION[:\s]*(.+?)(?:H\.S\.|CUSTOMS)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            boe.description = match.group(1).strip()[:200]  # 최대 200자

        # Gross Weight
        match = re.search(
            r"GROSS WEIGHT[:\s]*([\d,]+\.?\d*)\s*Kgs", text, re.IGNORECASE
        )
        if match:
            boe.gross_weight_kg = self._safe_float(match.group(1))

        # Net Weight
        match = re.search(r"NET WEIGHT[:\s]*([\d,]+\.?\d*)\s*Kgs", text, re.IGNORECASE)
        if match:
            boe.net_weight_kg = self._safe_float(match.group(1))

        # Value USD
        match = re.search(r"USD\s+([\d,]+\.?\d*)", text)
        if match:
            boe.value_usd = self._safe_float(match.group(1))

        # CIF LOCAL VALUE (AED)
        match = re.search(r"CIF[:\s]*([\d,]+\.?\d*)\s*Dhs", text, re.IGNORECASE)
        if match:
            boe.cif_value_aed = self._safe_float(match.group(1))

        # Total Duty
        match = re.search(r"TOTAL DUTY[:\s]*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            boe.duty_aed = self._safe_float(match.group(1))

        # Importer TRN
        match = re.search(r"IMPORTER[:\s]*.+?[\/\\](\d+)", text, re.IGNORECASE)
        if match:
            boe.importer_trn = match.group(1)

        # Debit Notes
        debit_pattern = r"DEBIT NOTE[:\s]*(\d+).*?Amount[:\s]*([\d,]+\.?\d*)"
        debit_matches = re.findall(debit_pattern, text, re.IGNORECASE | re.DOTALL)
        if debit_matches:
            boe.debit_notes = [
                {"note_no": dn[0], "amount_aed": self._safe_float(dn[1])}
                for dn in debit_matches
            ]

        return boe

    # ==================== DO Parser ====================

    def _parse_do(self, text: str, header: DocumentHeader) -> DOData:
        """Delivery Order 파싱"""
        do = DOData(header=header)

        # D.O. No
        match = re.search(r"D[.\s]*O[.\s]*No[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            do.do_number = match.group(1)

        # D.O. Date
        match = re.search(
            r"D[.\s]*O[.\s]*Date[.:]?\s*(\d{1,2}[-/]\w{3}[-/]\d{4})",
            text,
            re.IGNORECASE,
        )
        if match:
            do.do_date = match.group(1)

        # Delivery Valid Until
        match = re.search(
            r"Delivery\s+valid\s+until[.:]?\s*(\d{1,2}/\d{1,2}/\d{4})",
            text,
            re.IGNORECASE,
        )
        if match:
            do.delivery_valid_until = match.group(1)

        # MBL No
        match = re.search(r"MBL\s+No[.:]?\s+([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            do.mbl_no = match.group(1)

        # HBL No
        match = re.search(r"HBL\s+No[.:]?\s+([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            do.hbl_no = match.group(1)

        # Vessel
        match = re.search(
            r"EX[.\s]*VSL[.:]?\s*(.+?)\s+VOY", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            do.vessel = match.group(1).strip()

        # Voyage No
        match = re.search(r"Voy[.\s]*No[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            do.voyage_no = match.group(1)

        # Manifest Reg. No
        match = re.search(r"Manifest\s+Reg[.\s]*No[.:]?\s*(\d+)", text, re.IGNORECASE)
        if match:
            do.manifest_reg_no = match.group(1)

        # Quantity (containers)
        match = re.search(r"Quantity[.:]?\s*(\d+)", text, re.IGNORECASE)
        if match:
            do.quantity = self._safe_int(match.group(1))

        # Weight
        match = re.search(r"Weight\(Kgs\)[.:]?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            do.weight_kg = self._safe_float(match.group(1))

        # Volume
        match = re.search(r"Volume\(CBM\)[.:]?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            do.volume_cbm = self._safe_float(match.group(1))

        # Containers
        container_pattern = (
            r"(CMAU\d{7}|TGHU\d{7}|TCNU\d{7}|[A-Z]{4}\d{7})\s*([A-Z0-9]+)"
        )
        container_matches = re.findall(container_pattern, text)
        if container_matches:
            do.containers = [
                {"container_no": c[0], "seal_no": c[1]} for c in container_matches
            ]

        # Description
        match = re.search(
            r"Description\s+of\s+Goods[.:]?\s*(.+?)(?:Container|Marks|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            do.description = match.group(1).strip()[:200]

        # Shipping Line
        match = re.search(r"For\s+([A-Z\s&-]+LLC)", text, re.IGNORECASE)
        if match:
            do.shipping_line = match.group(1).strip()

        # Empty Return Depot
        match = re.search(
            r"EMPTY RETURN DEPOT[.:]?\s*(.+?)(?:DEPOT LOCATION|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            do.empty_return_depot = match.group(1).strip()

        # Empty Return Location
        match = re.search(r"DEPOT LOCATION[.:]?\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if match:
            do.empty_return_location = match.group(1).strip()

        return do

    # ==================== DN Parser ====================

    def _parse_dn(self, text: str, header: DocumentHeader) -> DNData:
        """Delivery Note 파싱"""
        dn = DNData(header=header)

        # Waybill No
        match = re.search(
            r"Delivery\s+Note[/\\]Waybill\s*#[.:]?\s*([A-Z0-9-]+)", text, re.IGNORECASE
        )
        if match:
            dn.waybill_no = match.group(1)

        # Trip No
        match = re.search(r"Trip\s+No[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            dn.trip_no = match.group(1)

        # Container Number
        match = re.search(r"Container\s*#[.:]?\s*([A-Z]{4}\d{7})", text, re.IGNORECASE)
        if match:
            dn.container_no = match.group(1)

        # Container Type/Size
        match = re.search(r"Container\s+Type[.:]?\s*(\w+)", text, re.IGNORECASE)
        if match:
            dn.container_type = match.group(1)

        match = re.search(r"Container\s+Size[.:]?\s*(\w+)", text, re.IGNORECASE)
        if match:
            dn.container_size = match.group(1)

        # Seal No
        match = re.search(r"Seal\s*#[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            dn.seal_no = match.group(1)

        # Order Number
        match = re.search(r"Order\s+Number[.:]?\s*([A-Z0-9-]+)", text, re.IGNORECASE)
        if match:
            dn.order_number = match.group(1)

        # Job Number
        match = re.search(r"Job\s+Number[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            dn.job_number = match.group(1)

        # Loading Point
        match = re.search(
            r"Loading\s+Point[.:]?\s*(.+?)(?:\n|Loading Country)", text, re.IGNORECASE
        )
        if match:
            dn.loading_point = match.group(1).strip()

        # Destination
        match = re.search(
            r"Destination[.:]?\s*(.+?)(?:\n|Offloading)", text, re.IGNORECASE
        )
        if match:
            dn.destination = match.group(1).strip()

        # Description
        match = re.search(
            r"Description[.:]?\s*(.+?)(?:Sender Section|CONSIGNMENT)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            dn.description = match.group(1).strip()[:200]

        # Driver Name
        match = re.search(
            r"Driver\s+Name[.:]?\s*(.+?)(?:\n|Employee)", text, re.IGNORECASE
        )
        if match:
            dn.driver_name = match.group(1).strip()

        # Truck Type
        match = re.search(
            r"Req\s+Truck\s+Type[.:]?\s*(.+?)(?:\n|Destination)", text, re.IGNORECASE
        )
        if match:
            dn.truck_type = match.group(1).strip()

        # Trailer Type
        match = re.search(
            r"Trailer\s+Type[.:]?\s*(.+?)(?:\n|Trailer Plate)", text, re.IGNORECASE
        )
        if match:
            dn.trailer_type = match.group(1).strip()

        # Head Plate
        match = re.search(r"Head\s+Plate[.:]?\s*([A-Z0-9-]+)", text, re.IGNORECASE)
        if match:
            dn.head_plate = match.group(1)

        # Trailer Plate
        match = re.search(r"Trailer\s+Plate[.:]?\s*([A-Z0-9-]+)", text, re.IGNORECASE)
        if match:
            dn.trailer_plate = match.group(1)

        # Loading Date
        match = re.search(
            r"Loading\s+Date[.:]?\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE
        )
        if match:
            dn.loading_date = match.group(1)

        # Asset Release Time (Origin)
        match = re.search(
            r"ASSET\s+RELEASE\s+DATE\s+&\s+TIME[.:]?\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})",
            text,
            re.IGNORECASE,
        )
        if match:
            dn.asset_release_time_origin = match.group(1)

        # Customer Name
        match = re.search(
            r"Customer'?s\s+Name[.:]?\s*(.+?)(?:\n|Address)", text, re.IGNORECASE
        )
        if match:
            dn.customer_name = match.group(1).strip()

        # Consignee Name
        match = re.search(
            r"Consignee'?s\s+Name[.:]?\s*(.+?)(?:\n|Address)", text, re.IGNORECASE
        )
        if match:
            dn.consignee_name = match.group(1).strip()

        # Carrier
        match = re.search(r"Carrier[.:]?\s*(.+?)(?:\n|Driver)", text, re.IGNORECASE)
        if match:
            dn.carrier = match.group(1).strip()

        return dn

    # ==================== Carrier Invoice Parser ====================

    def _parse_carrier_invoice(
        self, text: str, header: DocumentHeader
    ) -> CarrierInvoiceData:
        """Carrier Invoice 파싱"""
        inv = CarrierInvoiceData(header=header)

        # Invoice Number
        match = re.search(
            r"(?:TAX\s+)?INVOICE\s*#?\s*[.:]?\s*([A-Z0-9]+)", text, re.IGNORECASE
        )
        if match:
            inv.invoice_number = match.group(1)

        # Date
        match = re.search(
            r"Date[.:]?\s*(\d{1,2}[-/]\w{3}[-/]\d{4})", text, re.IGNORECASE
        )
        if match:
            inv.invoice_date = match.group(1)

        # Payable by
        match = re.search(
            r"Payable\s+by[.:]?\s*(\d{1,2}[-/]\w{3}[-/]\d{4})", text, re.IGNORECASE
        )
        if match:
            inv.payable_by = match.group(1)

        # Bill of Lading
        match = re.search(r"Bill\s+of\s+Lading[.:]?\s+([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            inv.bl_number = match.group(1)

        # Booking Ref
        match = re.search(r"Booking\s+Ref[.:]?\s+([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            inv.booking_ref = match.group(1)

        # Vessel
        match = re.search(r"Vessel[.:]?\s+(.+?)(?:\n|Voyage)", text, re.IGNORECASE)
        if match:
            inv.vessel = match.group(1).strip()

        # Voyage
        match = re.search(r"Voyage[.:]?\s+([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            inv.voyage = match.group(1)

        # Load Port
        match = re.search(
            r"Load\s+Port[.:]?\s+(.+?)(?:\n|Discharge)", text, re.IGNORECASE
        )
        if match:
            inv.load_port = match.group(1).strip()

        # Discharge Port
        match = re.search(
            r"Discharge\s+Port[.:]?\s+(.+?)(?:\n|Place)", text, re.IGNORECASE
        )
        if match:
            inv.discharge_port = match.group(1).strip()

        # Containers
        container_pattern = r"(CMAU\d{7}|TGHU\d{7}|TCNU\d{7}|[A-Z]{4}\d{7})"
        containers = re.findall(container_pattern, text)
        if containers:
            inv.containers = list(set(containers))

        # Invoice To
        match = re.search(
            r"Invoice\s+To[.:]?\s*(.+?)(?:Payable to|IBAN)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            inv.invoice_to = match.group(1).strip()[:200]

        # Total Amount (AED)
        match = re.search(r"Total\s+Amount[.:]?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            inv.total_incl_tax = self._safe_float(match.group(1))

        # Currency
        match = re.search(r"Currency[.:]?\s+([A-Z]{3})", text, re.IGNORECASE)
        if match:
            inv.currency = match.group(1)
        else:
            inv.currency = "AED"  # Default

        # VAT
        match = re.search(r"Total\s+VAT\s+([\d.]+)%", text, re.IGNORECASE)
        if match:
            inv.vat_rate = self._safe_float(match.group(1))

        # IBAN
        match = re.search(r"IBAN[.:]?\s+([A-Z]{2}\d{2}[A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            inv.iban = match.group(1)

        # SWIFT
        match = re.search(r"SWIFT[.:]?\s+([A-Z0-9]{8,11})", text, re.IGNORECASE)
        if match:
            inv.swift = match.group(1)

        # TRN (Tax Registration Number)
        trn_pattern = r"TRN\s*#?[.:]?\s*(\d{15})"
        trn_matches = re.findall(trn_pattern, text, re.IGNORECASE)
        if trn_matches:
            inv.trn = trn_matches[0]
            if len(trn_matches) > 1:
                inv.invoiced_by_trn = trn_matches[1]

        return inv

    # ==================== Main Parse Method ====================

    def parse_pdf(
        self, pdf_path: str, doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        PDF 파일 파싱 (메인 진입점)

        Args:
            pdf_path: PDF 파일 경로
            doc_type: 문서 타입 (None이면 자동 추론)

        Returns:
            파싱된 데이터 딕셔너리
        """

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        filename = os.path.basename(pdf_path)

        # 문서 타입 결정
        if not doc_type:
            doc_type = self._infer_doc_type_from_filename(filename)

        # Item Code 추출
        item_code = self._extract_item_code_from_filename(filename)

        # 파일 해시 계산
        file_hash = self._calculate_file_hash(pdf_path)

        # 헤더 생성
        header = DocumentHeader(
            doc_type=doc_type,
            item_code=item_code,
            file_path=pdf_path,
            file_hash=file_hash,
            parsed_at=datetime.now().isoformat(),
        )

        self.logger.info(f"Parsing {doc_type}: {filename}")

        # 텍스트 추출
        text = self._extract_text_from_pdf(pdf_path)

        if not text:
            self.logger.warning(f"No text extracted from {filename}")
            return {
                "header": asdict(header),
                "data": None,
                "error": "No text extracted",
            }

        # 문서 타입별 파싱
        try:
            if doc_type == "BOE":
                parsed_data = self._parse_boe(text, header)
            elif doc_type == "DO":
                parsed_data = self._parse_do(text, header)
            elif doc_type == "DN":
                parsed_data = self._parse_dn(text, header)
            elif doc_type == "CarrierInvoice":
                parsed_data = self._parse_carrier_invoice(text, header)
            else:
                self.logger.warning(f"Unknown document type: {doc_type}")
                return {
                    "header": asdict(header),
                    "data": None,
                    "error": "Unknown document type",
                }

            result = {
                "header": asdict(header),
                "data": asdict(parsed_data),
                "error": None,
            }

            self.logger.info(f"Successfully parsed {filename}")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing {filename}: {e}", exc_info=True)
            return {"header": asdict(header), "data": None, "error": str(e)}

    def parse_folder(
        self, folder_path: str, recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        폴더 내 모든 PDF 파싱

        Args:
            folder_path: 폴더 경로
            recursive: 하위 폴더 포함 여부

        Returns:
            파싱 결과 리스트
        """
        results = []

        if recursive:
            pdf_files = list(Path(folder_path).rglob("*.pdf"))
        else:
            pdf_files = list(Path(folder_path).glob("*.pdf"))

        self.logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")

        for pdf_file in pdf_files:
            try:
                result = self.parse_pdf(str(pdf_file))
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to parse {pdf_file}: {e}")
                results.append(
                    {
                        "header": {"file_path": str(pdf_file)},
                        "data": None,
                        "error": str(e),
                    }
                )

        return results

    def export_to_json(self, results: List[Dict[str, Any]], output_path: str):
        """JSON으로 내보내기"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Exported {len(results)} results to {output_path}")


# ==================== CLI Interface ====================


def main():
    """CLI 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="DSV PDF Document Parser")
    parser.add_argument("input", help="PDF file or folder path")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument(
        "-t",
        "--type",
        choices=["BOE", "DO", "DN", "CarrierInvoice"],
        help="Document type (auto-detect if not specified)",
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Parse folders recursively"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    log_level = "DEBUG" if args.verbose else "INFO"
    parser_engine = DSVPDFParser(log_level=log_level)

    input_path = args.input

    if os.path.isfile(input_path):
        # Single file
        result = parser_engine.parse_pdf(input_path, doc_type=args.type)
        results = [result]
    elif os.path.isdir(input_path):
        # Folder
        results = parser_engine.parse_folder(input_path, recursive=args.recursive)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        return

    # Output
    if args.output:
        parser_engine.export_to_json(results, args.output)
    else:
        # Print to console
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
