#!/usr/bin/env bash
# Hybrid System 재시작 스크립트 (개선된 Worker 포함)
# 실행: wsl bash restart_hybrid_system.sh

set -euo pipefail

PROJECT_DIR="/mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-20251012T195441Z-1-001/HVDC_Invoice_Audit"

echo "🔄 Hybrid System 재시작 중..."
echo ""

# 1. 기존 프로세스 종료
echo "📡 기존 프로세스 확인..."
PIDS=$(ps aux | grep -E 'honcho|uvicorn|celery' | grep -v grep | awk '{print $2}' || true)

if [ -n "$PIDS" ]; then
    echo "   기존 프로세스 발견: $PIDS"
    echo "   종료 중..."
    echo "$PIDS" | xargs kill -15 2>/dev/null || true
    sleep 2
    echo "✅ 기존 프로세스 종료 완료"
else
    echo "   실행 중인 프로세스 없음"
fi
echo ""

# 2. 디렉토리 이동
cd "$PROJECT_DIR" || exit 1

# 3. Redis 상태 확인
echo "📡 Redis 연결 확인..."
redis-cli ping > /dev/null 2>&1 || {
    echo "❌ Redis가 실행되지 않음. 시작 중..."
    sudo service redis-server start
}
echo "✅ Redis: PONG"
echo ""

# 4. 가상 환경 활성화
echo "🐍 Python 가상 환경 활성화..."
source venv/bin/activate
echo "✅ venv 활성화 완료"
echo ""

# 5. pdfplumber 설치 확인
echo "📦 pdfplumber 설치 확인..."
python -c "import pdfplumber; print('✅ pdfplumber:', pdfplumber.__version__)" 2>/dev/null || {
    echo "   pdfplumber 미설치. 설치 중..."
    pip install pdfplumber==0.10.3
}
echo ""

# 6. Honcho 재시작
echo "🔧 Honcho 재시작 (개선된 Worker 포함)..."
echo "   - FastAPI: http://localhost:8080"
echo "   - Celery Worker: -P solo --concurrency=2"
echo "   - pdfplumber: 실제 PDF 파싱 활성화"
echo ""
echo "⏸️  중지하려면: Ctrl+C"
echo "============================================================"
echo ""

# Honcho 시작
honcho -f Procfile.dev start

