#!/usr/bin/env python3
"""
Celery Worker (No Docker)
Docling + ADE 통합 PDF 파싱

Version: 1.0.0
Created: 2025-10-14
"""

from celery import Celery
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Celery App
celery_app = Celery(
    "hybrid_tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=int(os.getenv("CELERY_TASK_TIMEOUT", 300)),
    task_soft_time_limit=int(os.getenv("CELERY_TASK_TIMEOUT", 300)) - 30,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Load Routing Rules
routing_rules_path = os.getenv(
    "ROUTING_RULES_PATH", "./hybrid_doc_system/config/routing_rules_hvdc.json"
)
ROUTING_RULES = {}
try:
    with open(routing_rules_path, "r") as f:
        ROUTING_RULES = json.load(f)
    logger.info(
        f"Routing rules loaded: {len(ROUTING_RULES.get('hvdc_rules', []))} rules"
    )
except Exception as e:
    logger.warning(f"Routing rules load failed: {e}. Using default engine.")


@celery_app.task(name="parse_pdf", bind=True, max_retries=3)
def parse_pdf_task(self, pdf_path: str, doc_type: str = "invoice") -> Dict[str, Any]:
    """
    PDF 파싱 Celery Task

    Args:
        pdf_path: PDF 파일 경로
        doc_type: 문서 타입

    Returns:
        Unified IR (blocks + coords)
    """
    try:
        logger.info(f"[START] Parsing {pdf_path} ({doc_type})")

        # 1. PDF 파일 확인
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # 2. Routing Engine 선택
        engine = _select_engine(pdf_file, doc_type)
        logger.info(f"[ENGINE] Selected: {engine}")

        # 3. 파싱 실행
        if engine == "docling":
            unified_ir = _parse_with_docling(pdf_file)
        elif engine == "ade":
            unified_ir = _parse_with_ade(pdf_file)
        else:
            unified_ir = _parse_with_docling(pdf_file)  # Default

        # 4. Unified IR 반환
        unified_ir["engine"] = engine
        unified_ir["doc_type"] = doc_type

        logger.info(
            f"[SUCCESS] Parsed {pdf_file.name} with {engine} ({len(unified_ir.get('blocks', []))} blocks)"
        )

        return unified_ir

    except Exception as exc:
        logger.error(f"[FAIL] Parsing failed: {exc}")

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(
                f"[RETRY] Attempt {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(
                exc=exc, countdown=int(os.getenv("CELERY_RETRY_DELAY", 60))
            )
        else:
            return {
                "doc_id": pdf_path,
                "engine": "none",
                "error": str(exc),
                "blocks": [],
            }


def _select_engine(pdf_file: Path, doc_type: str) -> str:
    """
    Routing Rules 기반 엔진 선택

    Returns:
        "docling" or "ade"
    """
    # Default
    default_engine = ROUTING_RULES.get("default_engine", "docling")

    # Check budget guard
    # TODO: Implement budget tracking

    # Simple heuristics (실제로는 PDF 메타데이터 분석 필요)
    file_size_mb = pdf_file.stat().st_size / 1024 / 1024

    # Rule: Large file → ADE
    if file_size_mb > 5.0:
        return "ade"

    # Rule: Invoice/BOE → ADE (if complex)
    if doc_type in ["invoice", "boe"]:
        return "ade"

    # Rule: DO/DN → Docling (simple)
    if doc_type in ["do", "dn"]:
        return "docling"

    return default_engine


def _parse_with_docling(pdf_file: Path) -> Dict[str, Any]:
    """
    Docling으로 PDF 파싱

    Returns:
        Unified IR
    """
    try:
        # TODO: Implement Docling parsing
        # from docling import DocumentConverter
        # converter = DocumentConverter()
        # result = converter.convert(str(pdf_file))

        # Mock Unified IR (placeholder)
        unified_ir = {
            "doc_id": pdf_file.name,
            "engine": "docling",
            "pages": 1,
            "blocks": [
                {
                    "type": "text",
                    "text": f"[PLACEHOLDER] Docling parsed: {pdf_file.name}",
                }
            ],
            "meta": {"confidence": 0.85, "filename": pdf_file.name},
        }

        return unified_ir

    except Exception as e:
        logger.error(f"Docling parsing failed: {e}")
        raise


def _parse_with_ade(pdf_file: Path) -> Dict[str, Any]:
    """
    ADE (LandingAI)로 PDF 파싱
    실제 구현: pdfplumber 기반 테이블 + 텍스트 추출

    Returns:
        Unified IR
    """
    try:
        # pdfplumber로 실제 파싱 (ADE 대체)
        try:
            import pdfplumber

            blocks = []
            with pdfplumber.open(str(pdf_file)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # 1. 테이블 추출
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            blocks.append(
                                {
                                    "type": "table",
                                    "page": page_num,
                                    "table_id": f"table_{page_num}_{table_idx}",
                                    "rows": table,
                                    "bbox": None,  # pdfplumber doesn't provide bbox
                                }
                            )

                    # 2. 텍스트 추출 (키-값 쌍)
                    text = page.extract_text()
                    if text:
                        blocks.append(
                            {
                                "type": "text",
                                "page": page_num,
                                "text": text,
                                "bbox": None,
                            }
                        )

            unified_ir = {
                "doc_id": pdf_file.name,
                "engine": "ade",  # Actually pdfplumber
                "pages": len(pdf.pages),
                "blocks": blocks,
                "meta": {
                    "confidence": 0.90,
                    "filename": pdf_file.name,
                    "parser": "pdfplumber",
                },
            }

            # Multi-strategy Total Amount Fallback
            # 1. Coordinate-based (우선순위 1)
            total_info = _extract_total_with_coordinates(pdf_file)

            # 2. Table-based (우선순위 2)
            if not total_info:
                total_info = _extract_total_from_table(pdf_file)

            if total_info:
                unified_ir["blocks"].append(
                    {
                        "type": "summary",
                        "total_amount": total_info["total_amount"],
                        "currency": total_info["currency"],
                        "bbox": total_info.get("bbox"),
                        "table_index": total_info.get("table_index"),
                        "row_index": total_info.get("row_index"),
                        "extraction_method": total_info["extraction_method"],
                    }
                )
                logger.info(
                    f"[FALLBACK] Total extracted via {total_info['extraction_method']}: ${total_info['total_amount']:.2f}"
                )

            logger.info(f"[ADE] Extracted {len(blocks)} blocks from {pdf_file.name}")
            return unified_ir

        except ImportError:
            # Fallback: Mock Unified IR (placeholder)
            logger.warning("pdfplumber not installed. Using placeholder.")
            unified_ir = {
                "doc_id": pdf_file.name,
                "engine": "ade",
                "pages": 1,
                "blocks": [
                    {
                        "type": "text",
                        "text": f"[PLACEHOLDER] ADE parsed: {pdf_file.name}",
                    }
                ],
                "meta": {"confidence": 0.50, "filename": pdf_file.name},
            }
            return unified_ir

    except Exception as e:
        logger.error(f"ADE parsing failed: {e}")
        raise


def _parse_number(value_str: str) -> float:
    """
    숫자 파싱 Helper (쉼표 제거, 기본값 0.0)

    Args:
        value_str: 숫자 문자열 (예: "1,234.56", "556.50")

    Returns:
        파싱된 float 값, 실패 시 0.0
    """
    try:
        # Remove commas, whitespace, currency symbols
        cleaned = str(value_str).replace(",", "").replace(" ", "").strip()
        cleaned = cleaned.replace("$", "").replace("AED", "").replace("USD", "")

        if not cleaned or cleaned == "-" or cleaned.lower() in ["n/a", "na", "none"]:
            return 0.0

        return float(cleaned)

    except (ValueError, AttributeError):
        return 0.0


def _extract_total_with_coordinates(pdf_file: Path) -> Optional[Dict]:
    """
    pdfplumber bbox 기반 Total Amount 추출

    Strategy:
    1. extract_words()로 모든 단어의 bbox 획득
    2. "Total Amount" / "TOTAL" 키워드 찾기
    3. 우측 영역 (x1 + 10px ~ x1 + 200px, same y) 검색
    4. 아래 영역 (same x, y1 + 5px ~ y1 + 50px) 검색
    5. 숫자 패턴 매칭

    Args:
        pdf_file: PDF 파일 경로

    Returns:
        {
            "total_amount": 556.50,
            "currency": "AED" or "USD",
            "bbox": {...},
            "extraction_method": "coordinate_right" or "coordinate_below"
        } or None
    """
    try:
        import pdfplumber

        with pdfplumber.open(str(pdf_file)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()

                # "Total Amount" 라벨 찾기
                for i, word in enumerate(words):
                    text_upper = word["text"].upper()

                    # "TOTAL" 키워드 체크
                    if "TOTAL" not in text_upper:
                        continue

                    # 다음 단어가 "AMOUNT"인지 확인
                    label_bbox = None
                    if i + 1 < len(words) and "AMOUNT" in words[i + 1]["text"].upper():
                        label_bbox = (
                            word["x0"],
                            word["top"],
                            words[i + 1]["x1"],
                            words[i + 1]["bottom"],
                        )
                    else:
                        label_bbox = (
                            word["x0"],
                            word["top"],
                            word["x1"],
                            word["bottom"],
                        )

                    x0, y0, x1, y1 = label_bbox

                    # 우측 영역 검색 (same line, ±10px y tolerance)
                    for w in words[i + 2 :]:
                        if w["x0"] >= x1 + 10 and w["x0"] <= 600:  # 페이지 전체 너비
                            if (
                                abs(w["top"] - y0) <= 10
                            ):  # Same line tolerance increased
                                amount = _parse_number(w["text"])
                                if amount > 10:  # Minimum threshold
                                    # Check currency (look for AED nearby)
                                    currency = "USD"
                                    for nearby in words:
                                        if (
                                            abs(nearby["x0"] - w["x0"]) < 50
                                            and "AED" in nearby["text"]
                                        ):
                                            currency = "AED"
                                            break

                                    logger.info(
                                        f"[COORDINATE] Total extracted (right): ${amount:.2f} {currency} on page {page_num+1}"
                                    )
                                    return {
                                        "total_amount": amount,
                                        "currency": currency,
                                        "bbox": {
                                            "page": page_num + 1,
                                            "x0": w["x0"],
                                            "y0": w["top"],
                                            "x1": w["x1"],
                                            "y1": w["bottom"],
                                        },
                                        "extraction_method": "coordinate_right",
                                    }

                    # Strategy 3: 페이지 우측 절반 전체 스캔 (Fallback)
                    # "Total Amount" 라벨과 같은 y축 범위 (±15px)에서 x > 300인 모든 숫자 검색
                    right_side_candidates = []
                    for w in words:
                        if w["x0"] > 300 and abs(w["top"] - y0) <= 15:
                            amount = _parse_number(w["text"])
                            if amount > 10:
                                right_side_candidates.append((amount, w))

                    if right_side_candidates:
                        # 최대값 선택 (보통 Total Amount가 가장 큼)
                        max_amount, max_word = max(
                            right_side_candidates, key=lambda x: x[0]
                        )

                        # Currency 확인
                        currency = "USD"
                        for nearby in words:
                            if (
                                abs(nearby["x0"] - max_word["x0"]) < 50
                                and "AED" in nearby["text"]
                            ):
                                currency = "AED"
                                break

                        logger.info(
                            f"[COORDINATE] Total extracted (right_wide): ${max_amount:.2f} {currency} on page {page_num+1}"
                        )
                        return {
                            "total_amount": max_amount,
                            "currency": currency,
                            "bbox": {
                                "page": page_num + 1,
                                "x0": max_word["x0"],
                                "y0": max_word["top"],
                                "x1": max_word["x1"],
                                "y1": max_word["bottom"],
                            },
                            "extraction_method": "coordinate_right_wide",
                        }

                    # 아래 영역 검색 (next line, same x column ±20px)
                    for w in words[i + 2 :]:
                        if w["top"] >= y1 + 5 and w["top"] <= y1 + 50:
                            if abs(w["x0"] - x0) <= 20:  # Same column
                                amount = _parse_number(w["text"])
                                if amount > 10:
                                    # Check currency
                                    currency = "USD"
                                    for nearby in words:
                                        if (
                                            abs(nearby["x0"] - w["x0"]) < 50
                                            and "AED" in nearby["text"]
                                        ):
                                            currency = "AED"
                                            break

                                    logger.info(
                                        f"[COORDINATE] Total extracted (below): ${amount:.2f} {currency} on page {page_num+1}"
                                    )
                                    return {
                                        "total_amount": amount,
                                        "currency": currency,
                                        "bbox": {
                                            "page": page_num + 1,
                                            "x0": w["x0"],
                                            "y0": w["top"],
                                            "x1": w["x1"],
                                            "y1": w["bottom"],
                                        },
                                        "extraction_method": "coordinate_below",
                                    }

        logger.warning(f"[COORDINATE] No Total Amount found in {pdf_file.name}")
        return None

    except Exception as e:
        logger.error(f"[COORDINATE] Error extracting total: {e}")
        return None


def _extract_total_from_table(pdf_file: Path) -> Optional[Dict]:
    """
    pdfplumber 테이블 기반 Total Amount 추출

    Strategy:
    1. extract_tables()로 모든 테이블 추출
    2. 각 테이블의 마지막 2-3 행 검사
    3. "TOTAL", "GRAND TOTAL", "NET TOTAL" 키워드 포함 행 찾기
    4. 해당 행의 마지막 열에서 최대 숫자 추출

    Returns:
        {
            "total_amount": float,
            "currency": "AED" or "USD",
            "table_index": int,
            "row_index": int,
            "extraction_method": "table"
        } or None
    """
    try:
        import pdfplumber

        with pdfplumber.open(str(pdf_file)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()

                if not tables:
                    continue

                # 각 테이블 검사 (정순 + 역순 모두)
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue

                    # 모든 행 검사 (Summary는 어디든 있을 수 있음)
                    for row_idx, row in enumerate(table):
                        if not row:
                            continue

                        # "TOTAL" 키워드가 있는 행인지 확인
                        row_text = " ".join([str(cell) for cell in row if cell]).upper()

                        # "Total Amount" 또는 "TOTAL" 키워드 확인
                        has_total_keyword = any(
                            kw in row_text
                            for kw in [
                                "TOTAL AMOUNT",
                                "TOTAL VAT",
                                "GRAND TOTAL",
                                "NET TOTAL",
                                "TOTAL",
                            ]
                        )

                        if not has_total_keyword:
                            continue

                        # 해당 행의 모든 셀에서 숫자 추출
                        candidates = []
                        for cell in row:
                            if not cell:
                                continue

                            amount = _parse_number(str(cell))
                            if amount > 10:  # Minimum threshold
                                candidates.append(amount)

                        # 숫자가 발견되면 최대값 반환
                        if candidates:
                            max_amount = max(candidates)

                            # Currency 확인
                            currency = "USD"
                            if "AED" in row_text:
                                currency = "AED"

                            logger.info(
                                f"[TABLE] Total extracted: ${max_amount:.2f} {currency} on page {page_num+1}, table {table_idx}, row {row_idx}"
                            )
                            return {
                                "total_amount": max_amount,
                                "currency": currency,
                                "table_index": table_idx,
                                "row_index": row_idx,
                                "extraction_method": "table",
                            }

        logger.warning(f"[TABLE] No Total Amount found in tables of {pdf_file.name}")
        return None

    except Exception as e:
        logger.error(f"[TABLE] Extraction failed: {e}")
        return None


# Celery task discovery
celery_app.autodiscover_tasks(["hybrid_doc_system.worker"])

if __name__ == "__main__":
    # Worker 실행 (테스트용)
    celery_app.worker_main(["worker", "--loglevel=info", "-P", "solo"])
