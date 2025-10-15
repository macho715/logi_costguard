#!/usr/bin/env bash
# Hybrid System 시작 스크립트 (WSL2)
# 실행: wsl bash start_hybrid_system.sh

set -euo pipefail

PROJECT_DIR="/mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-20251012T195441Z-1-001/HVDC_Invoice_Audit"

echo "🚀 Hybrid System 시작 중..."
echo ""

# 1. 디렉토리 이동
cd "$PROJECT_DIR" || exit 1

# 2. Redis 상태 확인
echo "📡 Redis 연결 확인..."
redis-cli ping > /dev/null 2>&1 || {
    echo "❌ Redis가 실행되지 않음. 시작 중..."
    sudo service redis-server start
}
echo "✅ Redis: PONG"
echo ""

# 3. 가상 환경 활성화
echo "🐍 Python 가상 환경 활성화..."
source venv/bin/activate
echo "✅ venv 활성화 완료"
echo ""

# 4. Honcho 실행
echo "🔧 Honcho 시작 (FastAPI + Celery Worker)..."
echo "   - FastAPI: http://localhost:8080"
echo "   - Celery Worker: -P solo --concurrency=2"
echo ""
echo "⏸️  중지하려면: Ctrl+C"
echo "============================================================"
echo ""

# Honcho 실행
honcho -f Procfile.dev start

