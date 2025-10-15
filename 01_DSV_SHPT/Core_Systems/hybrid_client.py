#!/usr/bin/env python3
"""
Hybrid Doc System Client
PDF 파싱 요청 및 Unified IR 수신

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Integration
"""

import requests
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HybridDocClient:
    """
    Hybrid Document System Client
    FastAPI + Celery 기반 PDF 파싱 서비스 연동
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        timeout: int = 60,
        enable_cache: bool = True,
    ):
        """
        Args:
            api_url: Hybrid API 서버 URL
            timeout: 파싱 타임아웃 (초)
            enable_cache: 캐싱 활성화 여부
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.enable_cache = enable_cache
        self.cache = {}  # Simple in-memory cache

        logger.info(f"HybridDocClient initialized: {self.api_url}")

    def parse_pdf(
        self, pdf_path: str, doc_type: str = "invoice"
    ) -> Optional[Dict[str, Any]]:
        """
        PDF 파싱 요청 및 Unified IR 반환

        Args:
            pdf_path: PDF 파일 경로
            doc_type: 문서 타입 (invoice, boe, do, dn)

        Returns:
            Unified IR (blocks + coords) 또는 None (실패 시)

        Example:
            {
                "doc_id": "SCT-0126-BOE.pdf",
                "engine": "ade" or "docling",
                "pages": 3,
                "blocks": [
                    {"type": "table", "table": {"rows": [...]}, "bbox": {...}},
                    {"type": "text", "text": "Invoice No: 12345", "bbox": {...}}
                ],
                "meta": {
                    "filename": "BOE.pdf",
                    "confidence": 0.95,
                    "processing_time_ms": 1250
                }
            }
        """
        pdf_path_obj = Path(pdf_path)

        # Check cache
        cache_key = f"{pdf_path_obj.name}_{doc_type}"
        if self.enable_cache and cache_key in self.cache:
            logger.info(f"[CACHE HIT] {pdf_path_obj.name}")
            return self.cache[cache_key]

        # Check file exists
        if not pdf_path_obj.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None

        try:
            # 1. Upload PDF
            logger.info(f"[UPLOAD] {pdf_path_obj.name} ({doc_type})")
            task_id = self._upload_pdf(pdf_path_obj, doc_type)

            # 2. Poll for result
            logger.info(f"[POLL] Task ID: {task_id}")
            unified_ir = self._poll_result(task_id)

            # Cache result
            if self.enable_cache and unified_ir:
                self.cache[cache_key] = unified_ir

            logger.info(
                f"[SUCCESS] Parsed with {unified_ir.get('engine', 'unknown')} engine"
            )
            return unified_ir

        except Exception as e:
            logger.error(f"[FAIL] PDF parsing failed for {pdf_path_obj.name}: {e}")
            return None

    def _upload_pdf(self, pdf_path: Path, doc_type: str) -> str:
        """
        PDF 파일 업로드

        Returns:
            task_id: Celery Task ID
        """
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                metadata = {"doc_type": doc_type}

                response = requests.post(
                    f"{self.api_url}/upload", files=files, data=metadata, timeout=10
                )

            response.raise_for_status()
            result = response.json()

            return result["task_id"]

        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Cannot connect to Hybrid API at {self.api_url}. "
                "Is the service running? (docker compose up -d)"
            )
        except Exception as e:
            raise Exception(f"Upload failed: {e}")

    def _poll_result(self, task_id: str) -> Dict[str, Any]:
        """
        파싱 결과 폴링

        Returns:
            Unified IR
        """
        start_time = time.time()
        poll_interval = 1  # seconds

        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(f"{self.api_url}/status/{task_id}", timeout=5)
                response.raise_for_status()
                status_data = response.json()

                status = status_data.get("status")

                if status == "completed":
                    return status_data.get("result")
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    raise Exception(f"Parsing failed: {error_msg}")
                elif status in ["pending", "processing"]:
                    # Continue polling
                    time.sleep(poll_interval)
                else:
                    raise Exception(f"Unknown status: {status}")

            except requests.exceptions.Timeout:
                logger.warning(f"Status check timeout for task {task_id}")
                time.sleep(poll_interval)
                continue

        raise TimeoutError(f"Parsing timeout after {self.timeout}s for task {task_id}")

    def parse_pdf_batch(
        self, pdf_paths: list, doc_type: str = "invoice"
    ) -> Dict[str, Dict[str, Any]]:
        """
        배치 PDF 파싱 (병렬 처리)

        Args:
            pdf_paths: PDF 파일 경로 리스트
            doc_type: 문서 타입

        Returns:
            {pdf_path: unified_ir, ...}
        """
        results = {}

        for pdf_path in pdf_paths:
            unified_ir = self.parse_pdf(pdf_path, doc_type)
            results[str(pdf_path)] = unified_ir

        return results

    def check_service_health(self) -> bool:
        """
        Hybrid API 서비스 헬스 체크

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_service_stats(self) -> Optional[Dict[str, Any]]:
        """
        Hybrid API 서비스 통계 조회

        Returns:
            {
                "total_processed": 1234,
                "docling_count": 800,
                "ade_count": 434,
                "avg_latency_ms": 1250,
                "ade_cost_usd": 21.70
            }
        """
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get service stats: {e}")
            return None


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = HybridDocClient(api_url="http://localhost:8080")

    # Health check
    if client.check_service_health():
        print("✅ Hybrid API service is healthy")
    else:
        print("❌ Hybrid API service is not available")
        print("   Start with: cd hybrid_doc_system && docker compose up -d")
        exit(1)

    # Test PDF parsing
    test_pdf = Path("../Data/DSV 202509/sample.pdf")
    if test_pdf.exists():
        unified_ir = client.parse_pdf(str(test_pdf), doc_type="invoice")

        if unified_ir:
            print(f"\n✅ PDF parsed successfully")
            print(f"   Engine: {unified_ir.get('engine')}")
            print(f"   Pages: {unified_ir.get('pages')}")
            print(f"   Blocks: {len(unified_ir.get('blocks', []))}")
        else:
            print("\n❌ PDF parsing failed")
    else:
        print(f"⚠️ Test PDF not found: {test_pdf}")
