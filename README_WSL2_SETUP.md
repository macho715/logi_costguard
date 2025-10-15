# 🐧 WSL2 + Redis + Honcho 설정 가이드

**목적**: Docker 없이 HVDC + Hybrid Doc System을 로컬 환경에서 실행
**런타임**: WSL2 (Ubuntu) + Redis + Honcho
**소요 시간**: ~10분

---

## 📋 사전 요구사항

- Windows 10/11 (Build 19041+)
- 관리자 권한
- 인터넷 연결

---

## 🚀 설치 단계

### Step 1: WSL2 활성화 및 Ubuntu 설치

#### PowerShell (관리자 권한)
```powershell
# WSL2 설치
wsl --install

# 기본 버전 설정
wsl --set-default-version 2
```

#### 재부팅 후 확인
```powershell
wsl --status
# Default Version: 2

wsl -l -v
# NAME      STATE   VERSION
# Ubuntu    Running 2
```

**참고**: [WSL 공식 문서](https://learn.microsoft.com/en-us/windows/wsl/install)

---

### Step 2: Redis 설치 (WSL2 Ubuntu)

#### WSL2 Ubuntu 접속
```bash
wsl
```

#### Redis 설치
```bash
# 패키지 업데이트
sudo apt update

# Redis 설치
sudo apt install -y redis-server

# Redis 시작
sudo service redis-server start

# 확인
redis-cli ping
# 출력: PONG ✅
```

#### Redis 자동 시작 설정 (선택)
```bash
# /etc/wsl.conf 편집
sudo nano /etc/wsl.conf

# 추가:
[boot]
command="service redis-server start"
```

**참고**: [Redis on Windows (WSL2)](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/)

---

### Step 3: Python 환경 설정

#### 가상 환경 생성 (권장)
```bash
# Python 버전 확인
python3 --version
# Python 3.8+ 필요

# 가상 환경 생성
cd /mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-*/HVDC_Invoice_Audit
python3 -m venv venv

# 활성화
source venv/bin/activate
```

#### 패키지 설치
```bash
# pip 업그레이드
python -m pip install -U pip

# Hybrid System 의존성 설치
pip install -r requirements_hybrid.txt

# 빠른 설치 (uv 사용, 선택)
# pip install uv
# uv pip install -r requirements_hybrid.txt
```

**참고**: [uv - 빠른 Python 패키지 관리자](https://docs.astral.sh/uv/)

---

### Step 4: 환경 변수 설정

```bash
# env.sample → .env 복사
cp env.sample .env

# .env 편집
nano .env
```

**필수 설정**:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
USE_HYBRID=true
HYBRID_API_URL=http://localhost:8080
```

**선택 설정** (ADE 사용 시):
```bash
ADE_API_KEY=your_landing_ai_api_key_here
ADE_ENDPOINT=https://api.landing.ai
```

---

### Step 5: Honcho 실행

#### Honcho 설치 확인
```bash
pip list | grep honcho
# honcho 1.1.0
```

#### Procfile.dev 실행
```bash
honcho -f Procfile.dev start
```

**예상 출력**:
```
[web]    INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
[worker] [2025-10-14 23:30:00,123: INFO/MainProcess] celery@hostname ready.
[worker] [2025-10-14 23:30:00,124: INFO/MainProcess] concurrent: 2
```

**참고**: [Honcho 공식 문서](https://honcho.readthedocs.io/)

---

### Step 6: HVDC Audit 실행

#### 별도 터미널 (WSL2 또는 Windows)
```bash
# WSL2
cd /mnt/c/Users/minky/Downloads/HVDC_Invoice_Audit-*/HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems

# 또는 Windows PowerShell
cd C:\Users\minky\Downloads\HVDC_Invoice_Audit-*\HVDC_Invoice_Audit\01_DSV_SHPT\Core_Systems

# 실행
python masterdata_validator.py
```

**예상 로그**:
```
[UPLOAD] BOE.pdf (boe)
[POLL] Task ID: abc-123-def
[SUCCESS] Parsed with docling engine
[OK] Validation complete: 102 rows × 22 columns
```

---

## 🔧 서비스 확인

### FastAPI Docs
```bash
# 브라우저에서 열기
http://localhost:8080/docs
```

### Health Check
```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

### Redis 확인
```bash
redis-cli
> ping
PONG
> keys *
(list of celery tasks)
> exit
```

---

## 🐛 트러블슈팅

### 문제 1: "Redis connection refused"

**원인**: Redis 서비스 미실행

**해결**:
```bash
wsl
sudo service redis-server start
redis-cli ping  # PONG 확인
```

### 문제 2: "Worker가 멈춘다 / 작업 실행 안 됨"

**원인**: Windows Celery 풀 제약

**해결**:
```bash
# Procfile.dev 확인
worker: celery ... -P solo  # ← solo 확인

# 또는 eventlet/gevent 설치
pip install eventlet
worker: celery ... -P eventlet
```

**참고**: [Celery Workers Guide - Windows](https://docs.celeryq.dev/en/stable/userguide/workers.html)

### 문제 3: "ModuleNotFoundError: No module named 'hybrid_doc_system'"

**원인**: Python path 문제

**해결**:
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 또는 __init__.py 추가
touch hybrid_doc_system/__init__.py
touch hybrid_doc_system/api/__init__.py
touch hybrid_doc_system/worker/__init__.py
```

### 문제 4: "Port 8080 already in use"

**해결**:
```bash
# 프로세스 확인
lsof -i :8080  # Linux/WSL2
netstat -ano | findstr :8080  # Windows

# 프로세스 종료 후 재시작
```

### 문제 5: "uvicorn command not found"

**원인**: 가상 환경 미활성화

**해결**:
```bash
source venv/bin/activate  # WSL2
.\venv\Scripts\activate  # Windows PowerShell
```

---

## 📊 성능 비교

### Docker Compose vs Honcho

| 지표 | Docker | Honcho (WSL2) | 개선 |
|------|--------|---------------|------|
| **설치 시간** | ~30분 | **~10분** | -67% |
| **메모리 사용** | ~2GB | **~500MB** | -75% |
| **시작 시간** | ~30초 | **~5초** | -83% |
| **코드 변경 반영** | 이미지 재빌드 (~5분) | **Auto-reload (~1초)** | -99% |
| **팀 온보딩** | Docker 학습 필요 | Python만 알면 됨 | 간단 |

---

## 🎯 다음 단계

### 개발 완료 후 프로덕션 배포

**Option 1: Docker (권장)**
```bash
# docker-compose-integrated.yaml 사용
docker compose -f docker-compose-integrated.yaml up -d
```

**Option 2: Kubernetes**
```bash
# k8s/ 매니페스트 사용
kubectl apply -f hybrid_doc_system/k8s/
```

**Option 3: Systemd (Linux 서버)**
```bash
# systemd service 파일 생성
sudo systemctl enable hvdc-hybrid
sudo systemctl start hvdc-hybrid
```

---

## 📚 참고 문서

### 공식 문서
- **WSL2**: [Microsoft WSL 문서](https://learn.microsoft.com/en-us/windows/wsl/)
- **Redis**: [Redis on Windows](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/)
- **Honcho**: [Honcho 문서](https://honcho.readthedocs.io/)
- **Procfile**: [Heroku Procfile](https://devcenter.heroku.com/articles/procfile)
- **Celery**: [Celery Workers Guide](https://docs.celeryq.dev/en/stable/userguide/workers.html)

### 관련 블로그
- Redis on Windows 11 with WSL
- Celery + FastAPI Best Practices
- uv - Fast Python Package Manager

---

**작성일**: 2025-10-14
**작성자**: MACHO-GPT v3.4-mini
**프로젝트**: HVDC Invoice Audit - WSL2 Development Setup

