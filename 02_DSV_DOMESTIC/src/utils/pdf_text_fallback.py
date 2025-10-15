# -*- coding: utf-8 -*-
"""
PDF 본문 텍스트 폴백 추출기
- 우선순위: PyMuPDF(fitz) → pypdf → pdfminer.six → pdftotext(외부) → 빈문자열
  (다단/표 혼합 문서의 추출 안정성을 위해 PyMuPDF를 최우선 시도)
"""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Optional


def _try_pymupdf(pdf_path: str) -> str:
    """PyMuPDF(fitz)로 텍스트 추출 - 다단/표 혼합 문서에 강함"""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        texts = []
        for page in doc:
            try:
                # 레이아웃 보존력이 높은 모드 조합
                t = page.get_text("text") or ""
                if not t.strip():
                    t = page.get_text() or ""
                texts.append(t)
            except Exception:
                continue
        doc.close()
        return "\n".join(texts)
    except Exception:
        return ""


def _try_pypdf(pdf_path: str) -> str:
    """pypdf 또는 PyPDF2로 텍스트 추출"""
    try:
        # pypdf 또는 PyPDF2 호환
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(pdf_path)
        texts = []
        for p in getattr(reader, "pages", []):
            try:
                texts.append(p.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts)
    except Exception:
        return ""


def _try_pdfminer(pdf_path: str) -> str:
    """pdfminer.six로 텍스트 추출"""
    try:
        from pdfminer.high_level import extract_text  # type: ignore

        return extract_text(pdf_path) or ""
    except Exception:
        return ""


def _try_pdftotext(pdf_path: str) -> str:
    """외부 pdftotext 명령어로 텍스트 추출"""
    try:
        out_txt = str(Path(pdf_path).with_suffix(".txt"))
        # -layout: 멀티컬럼/표 포맷 유지에 유리
        subprocess.run(
            ["pdftotext", "-layout", pdf_path, out_txt],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if os.path.exists(out_txt):
            with open(out_txt, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        return ""
    except Exception:
        return ""


def extract_text_any(pdf_path: str) -> str:
    """
    가용 백엔드를 순차 시도하여 텍스트 추출.

    우선순위:
    1. PyMuPDF (다단/표 혼합 문서에 가장 강함, 빠름)
    2. pypdf (빠르고 경량)
    3. pdfminer.six (복잡한 레이아웃에 강함)
    4. pdftotext (외부 도구, 가장 견고)

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        추출된 텍스트 (실패 시 빈 문자열)
    """
    pdf_path = str(pdf_path)
    for fn in (_try_pymupdf, _try_pypdf, _try_pdfminer, _try_pdftotext):
        txt = fn(pdf_path)
        if txt and txt.strip():
            return txt
    return ""
