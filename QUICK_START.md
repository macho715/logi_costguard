# 🚀 HVDC Hybrid System - 빠른 시작 가이드

**소요 시간**: 10분
**방식**: WSL2 + Redis + Honcho (No Docker)

---

## 📋 3단계 실행

### Step 1: WSL2 + Redis 설치 (1회만)

```bash
# PowerShell (관리자 권한)
wsl --install

# 재부팅 후 WSL2 Ubuntu
wsl
sudo apt update && sudo apt install -y redis-server
sudo service redis-server start
redis-cli ping  # PONG 확인
```

### Step 2: 환경 설정

```bash
cd HVDC_Invoice_Audit

# 환경 변수
cp env.sample .env

# 패키지 설치
pip install -r requirements_hybrid.txt
```

### Step 3: 실행

```bash
# Terminal 1: Hybrid System 시작
honcho -f Procfile.dev start

# Terminal 2: HVDC Audit 실행
cd 01_DSV_SHPT/Core_Systems
python masterdata_validator.py
```

---

## ✅ 확인

### Hybrid System
- FastAPI: http://localhost:8080/docs
- Health: http://localhost:8080/health
- Redis: `redis-cli ping`

### HVDC Audit
```
[OK] Validation complete: 102 rows
PASS: 55 (53.9%)
FAIL: 5 (4.9%)
```

---

## 🔧 문제 해결

### Redis 연결 실패
```bash
wsl
sudo service redis-server start
redis-cli ping
```

### Worker 멈춤
```bash
# Procfile.dev 확인
worker: celery ... -P solo  # ← 필수
```

### 모듈 없음
```bash
pip install -r requirements_hybrid.txt
```

---

**상세 가이드**: `README_WSL2_SETUP.md`
