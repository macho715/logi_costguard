# 🚀 Honcho 실행 가이드

**상태**: Honcho 백그라운드 프로세스 시작됨
**문제**: Health endpoint 응답 없음 (원인 파악 필요)
**일자**: 2025-10-14

---

## ⚠️ 현재 상황

### 완료된 설치
- ✅ Redis v7.0.15 (PONG)
- ✅ Python 패키지 48개
- ✅ 가상 환경 생성 (venv)
- ✅ Honcho 백그라운드 시작 시도

### 확인 필요
- ⚠️ FastAPI 서비스 미응답 (port 8080)
- ⚠️ Celery Worker 상태 미확인
- ⚠️ .env 파일 설정 확인 필요

---

## 🔧 수동 실행 방법 (권장)

### Option 1: 별도 WSL2 터미널에서 실행

**1단계: 새 Windows Terminal 열기**
- Windows Terminal 또는 PowerShell 열기

**2단계: WSL2 접속 및 실행**
```bash
wsl
cd /mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-*/HVDC_Invoice_Audit
source venv/bin/activate
bash start_hybrid_system.sh
```

**예상 출력**:
```
🚀 Hybrid System 시작 중...
📡 Redis 연결 확인...
✅ Redis: PONG
🐍 Python 가상 환경 활성화...
✅ venv 활성화 완료
🔧 Honcho 시작 (FastAPI + Celery Worker)...
============================================================

[web]    INFO:     Uvicorn running on http://0.0.0.0:8080
[worker] [2025-10-14 xx:xx:xx,xxx: INFO/MainProcess] celery@hostname ready.
```

---

## 🧪 서비스 확인 방법

### FastAPI Docs (브라우저)
```
http://localhost:8080/docs
```

### Health Check (새 터미널)
```bash
wsl
curl http://localhost:8080/health
```

**예상 응답**:
```json
{
  "status": "ok",
  "broker": "redis",
  "workers": 1,
  "version": "1.0.0"
}
```

### Redis 확인
```bash
wsl
redis-cli ping
redis-cli keys '*'
```

---

## 🐛 문제 해결

### 문제 1: "ModuleNotFoundError: No module named 'hybrid_doc_system'"

**원인**: PYTHONPATH 미설정

**해결**:
```bash
wsl
cd /mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-*/HVDC_Invoice_Audit
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
honcho -f Procfile.dev start
```

### 문제 2: "Port 8080 already in use"

**확인**:
```bash
wsl
lsof -i :8080 || netstat -ano | grep :8080
```

**해결**: 프로세스 종료 후 재시작

### 문제 3: ".env file not found"

**해결**:
```bash
wsl
cd /mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-*/HVDC_Invoice_Audit
cp env.sample .env
nano .env  # 필요 시 편집
```

**필수 설정**:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
USE_HYBRID=true
APP_PORT=8080
LOG_LEVEL=INFO
```

### 문제 4: Honcho 백그라운드 실행 실패

**원인**: Windows 터미널에서 백그라운드 실행 제약

**해결**: 별도 터미널에서 포그라운드 실행 (위 Option 1)

---

## 📋 다음 단계 (Honcho 실행 후)

### 1. Health Check 성공 확인
```bash
curl http://localhost:8080/health
# {"status":"ok", ...}
```

### 2. Unit Tests 실행
```bash
cd 01_DSV_SHPT/Core_Systems
pytest test_hybrid_integration.py -v
```

### 3. E2E 테스트 (USE_HYBRID=true)
```bash
export USE_HYBRID=true
python masterdata_validator.py
```

---

## 🎯 성공 기준

| 항목 | 기준 | 확인 방법 |
|------|------|-----------|
| **FastAPI** | http://localhost:8080/docs 접속 가능 | 브라우저 확인 |
| **Health Check** | `{"status":"ok"}` 응답 | `curl /health` |
| **Celery Worker** | `workers: 1` 이상 | Health 응답 확인 |
| **Redis** | PONG 응답 | `redis-cli ping` |

---

## 📚 관련 파일

- `start_hybrid_system.sh` - 통합 시작 스크립트
- `Procfile.dev` - Process 정의
- `.env` - 환경 변수 (env.sample 참조)
- `README_WSL2_SETUP.md` - 전체 설치 가이드
- `QUICK_START.md` - 빠른 시작 가이드

---

**작성일**: 2025-10-14
**프로젝트**: HVDC Invoice Audit - Honcho Execution Guide

