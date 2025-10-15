#!/usr/bin/env python3
"""
FastAPI Upload Service (No Docker)
Redis + Celery 기반 PDF 파싱 API

Version: 1.0.0
Created: 2025-10-14
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from celery import Celery
from celery.result import AsyncResult
import os
from pathlib import Path
import logging
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

# FastAPI App
app = FastAPI(
    title="Hybrid Doc System API",
    description="PDF Parsing with Docling + ADE",
    version="1.0.0",
)

# Upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...), doc_type: str = "invoice"
) -> JSONResponse:
    """
    PDF 파일 업로드 및 파싱 작업 시작

    Args:
        file: PDF 파일
        doc_type: 문서 타입 (invoice, boe, do, dn)

    Returns:
        {"task_id": "abc-123-def", "status": "pending"}
    """
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"[UPLOAD] {file.filename} ({doc_type}) - {len(content)} bytes")

        # Enqueue parsing task
        task = celery_app.send_task(
            "parse_pdf", args=[str(file_path), doc_type], kwargs={}
        )

        return JSONResponse(
            {
                "task_id": task.id,
                "status": "pending",
                "filename": file.filename,
                "doc_type": doc_type,
            }
        )

    except Exception as e:
        logger.error(f"[ERROR] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> JSONResponse:
    """
    파싱 작업 상태 조회

    Returns:
        {
            "status": "pending" | "processing" | "completed" | "failed",
            "result": {...} (completed 시),
            "error": "..." (failed 시)
        }
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        response = {"task_id": task_id, "status": task.status.lower()}

        if task.ready():
            if task.successful():
                response["status"] = "completed"
                response["result"] = task.result
            else:
                response["status"] = "failed"
                response["error"] = str(task.info)
        else:
            response["status"] = "processing" if task.state == "STARTED" else "pending"

        return JSONResponse(response)

    except Exception as e:
        logger.error(f"[ERROR] Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    서비스 헬스 체크

    Returns:
        {"status": "ok", "broker": "redis", "workers": 2}
    """
    try:
        # Check Redis connection
        celery_app.connection().ensure_connection(max_retries=3)

        # Check active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        worker_count = len(active_workers) if active_workers else 0

        return {
            "status": "ok",
            "broker": "redis",
            "workers": worker_count,
            "version": "1.0.0",
        }

    except Exception as e:
        logger.error(f"[ERROR] Health check failed: {e}")
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)


@app.get("/stats")
async def get_stats():
    """
    파싱 통계 조회

    Returns:
        {
            "total_processed": 123,
            "docling_count": 80,
            "ade_count": 43,
            "avg_latency_ms": 1250
        }
    """
    # TODO: Implement stats collection
    return {
        "total_processed": 0,
        "docling_count": 0,
        "ade_count": 0,
        "avg_latency_ms": 0,
        "note": "Stats collection not implemented yet",
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Hybrid Doc System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 8080)),
        reload=True,
    )
