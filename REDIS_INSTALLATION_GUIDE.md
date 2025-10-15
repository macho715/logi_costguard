# 🔴 Redis 설치 안내

**현재 상태**: Redis가 WSL2에 설치되지 않음
**필요 작업**: 사용자가 직접 WSL2 터미널에서 Redis 설치

---

## 📋 설치 절차 (약 3분 소요)

### 1단계: WSL2 터미널 열기

**Option A: Windows Terminal 사용**
```powershell
wsl
```

**Option B: PowerShell에서 직접**
```powershell
wsl
```

### 2단계: Redis 설치 명령 실행

WSL2 Ubuntu 터미널에서 다음 명령어를 **한 줄씩** 실행하세요:

```bash
# 패키지 목록 업데이트
sudo apt update

# Redis 설치
sudo apt install -y redis-server

# Redis 서비스 시작
sudo service redis-server start

# 연결 확인 (PONG 출력되어야 함)
redis-cli ping
```

### 3단계: 결과 확인

마지막 명령(`redis-cli ping`)을 실행했을 때 **PONG**이 출력되면 성공입니다:

```
$ redis-cli ping
PONG  ✅
```

---

## ❓ 문제 해결

### 문제: "sudo: password for ..." 비밀번호 요청

**해결**: WSL2 Ubuntu 사용자 비밀번호 입력
- WSL2 처음 설치 시 설정한 비밀번호
- 비밀번호 입력 시 화면에 표시되지 않음 (정상)

### 문제: "E: Unable to locate package redis-server"

**해결**:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y redis-server
```

### 문제: "redis-cli: command not found"

**해결**: Redis가 설치되지 않은 상태. 위 2단계 다시 실행

---

## 📌 다음 단계

Redis 설치 완료 후, **이 파일을 닫고** Cursor에게 다음과 같이 말씀해주세요:

```
Redis 설치 완료했습니다. 다음 단계 진행해주세요.
```

그러면 자동으로 다음 단계(Python 패키지 설치, 시스템 검증)가 진행됩니다.

---

**작성일**: 2025-10-14
**프로젝트**: HVDC Invoice Audit - Redis Setup

