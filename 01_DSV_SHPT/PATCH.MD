Phase 5(Docker Compose)**를 **No-Docker 런타임**으로 치환하는 패치를 한 번에 정리했다. 바로 복붙해서 쓰면 돼.

---

# 1) `Procfile.dev` (루트에 추가)

```Procfile
# Procfile.dev — No-Docker multi-process runtime
# web / worker / beat 을 한 번에 기동 (Honcho/Foreman 호환)
web: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ⚠ Windows 개발 환경은 Celery 풀 제약 → -P solo 권장(개발용)
#   필요 시 eventlet/gevent 대체 가능. (참고 문서 인용)
worker: celery -A app.celery_app worker -l info -P solo

beat: celery -A app.celery_app beat -l info
```

* Procfile 개념/형식: Heroku Dev Center, Honcho 문서. ([devcenter.heroku.com](https://devcenter.heroku.com/articles/procfile?utm_source=chatgpt.com "The Procfile"))
* Honcho로 실행: `pip install honcho` → `honcho -f Procfile.dev start` (또는 Foreman/Heroku Local). ([honcho.readthedocs.io](https://honcho.readthedocs.io/?utm_source=chatgpt.com "Honcho: manage Procfile-based applications — honcho 2.0.1 ..."))
* Windows에서 Celery 풀: `-P solo`(단일 스레드, 개발용) 또는 gevent/eventlet 대안. ([docs.celeryq.dev](https://docs.celeryq.dev/en/stable/userguide/workers.html?utm_source=chatgpt.com "Workers Guide — Celery 5.5.3 documentation"))

---

# 2) `.env.example` (루트에 추가 → 복사해서 `.env` 사용)

```dotenv
# === App ===
APP_ENV=dev
APP_PORT=8000

# === Broker & Backend ===
# Redis (WSL2 권장): sudo apt install redis-server → redis-cli ping (PONG)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# RabbitMQ(WSL2 불가 시 대안): choco install rabbitmq (Erlang 필요)
# CELERY_BROKER_URL=amqp://guest:guest@localhost//
# CELERY_RESULT_BACKEND=rpc://

# === Logging ===
LOG_LEVEL=INFO

# === Feature Flags ===
USE_HYBRID=true
```

* Redis on Windows는 **WSL2** 또는 **Memurai**로 권장 경로가 공식 문서에 정리되어 있음. ([Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-windows/?utm_source=chatgpt.com "Install Redis on Windows | Docs"))
* RabbitMQ Windows 설치는 Erlang 의존성 필수(공식 가이드/매트릭스 참고). ([rabbitmq.com](https://www.rabbitmq.com/docs/install-windows?utm_source=chatgpt.com "Installing on Windows"))

---

# 3) `README_dev.md` (신규 문서)

```markdown
# No-Docker Runtime (Dev) — Procfile + Honcho

회사 PC에서 Docker가 제한된 환경을 위한 **로컬 멀티프로세스 런타임** 안내서입니다.
`Procfile.dev` + **Honcho(또는 Foreman/Heroku Local)** 로 `web / worker / beat`를 동시에 구동합니다.

---

## 0. 사전 준비

### Python 격리
```bash
# venv
py -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
# or: uv (선택) → 훨씬 빠른 설치
# https://docs.astral.sh/uv/
```

### 환경변수

```bash
# .env.example → .env 복사 후 값 확인/수정
copy .env.example .env
```

---

## 1. 브로커 설치 옵션

### A) Redis (권장: WSL2)

1. **WSL2 활성화** 후 Ubuntu 설치
2. `sudo apt update && sudo apt install -y redis-server`
3. 상태 확인: `redis-cli ping` → `PONG`

   * 공식: *Install Redis on Windows (WSL2 or Memurai)*
   * Blog: *Install Redis on Windows 11 (WSL)*

   > 문제가 있으면 Memurai 사용 가능.
   >
   > 참고:
   >

   * [https://redis.io/docs/.../install-redis-on-windows/](https://redis.io/docs/.../install-redis-on-windows/)
   * [https://redis.io/blog/install-redis-windows-11/](https://redis.io/blog/install-redis-windows-11/)

### B) RabbitMQ (WSL2 불가 시)

1. **Erlang 64-bit** 설치(버전 호환표 확인)
2. RabbitMQ 설치(Chocolatey 또는 수동)
3. 서비스 실행 후 관리 콘솔/포트 확인
   * 공식: *Installing on Windows* (Erlang 필요)
   * 수동 가이드: `rabbitmq-server.bat -detached` 로 백그라운드 실행

```

> 출처: Redis on Windows(WSL2/Memurai), RabbitMQ Windows 설치 & Erlang 의존성. :contentReference[oaicite:5]{index=5}

```markdown
---

## 2. 실행

### 의존성 설치
```bash
pip install -r requirements.txt
# 또는
# uv pip install -r requirements.txt
```

### Procfile.dev 구동

```bash
pip install honcho
honcho -f Procfile.dev start
```

* Honcho/Procfile 개요와 사용법은 공식 문서 참고.
  * Honcho Docs / PyPI / Heroku Procfile

```

> 참조: Honcho & Procfile 공식 문서. :contentReference[oaicite:6]{index=6}

```markdown
---

## 3. Windows에서 Celery 워커 주의
- 개발 환경에서는 `-P solo` 사용 권장(단일 작업자).
- 대안: `eventlet`/`gevent` 풀.
- 트레이드오프: solo는 동시성 1 → 워커 프로세스를 **여러 개** 띄워 보완.
  - 공식/가이드: Celery Workers Guide(`solo` 제약), Windows 실행 팁.
```

> 참고: Celery `solo` 제약/특성 및 Windows 대안. ([docs.celeryq.dev](https://docs.celeryq.dev/en/stable/userguide/workers.html?utm_source=chatgpt.com "Workers Guide — Celery 5.5.3 documentation"))

```markdown
---

## 4. 서비스 맵핑(Compose → Procfile.dev)

| Compose 서비스 | Procfile.dev 프로세스 | 포트/역할 |
|---|---|---|
| api (FastAPI) | `web` | :8000 REST API |
| worker | `worker` | Celery Task Worker |
| beat (scheduler) | `beat` | Celery Beat |
| redis/rabbitmq | 외부 서비스 | 로컬 Redis(WSL2) 또는 RabbitMQ(Windows) |

---

## 5. 트러블슈팅

- **`worker`가 멈춘다 / 작업이 실행 안 됨**
  → `-P solo`로 시작했는지 확인. 장시간 작업은 브로커 visibility timeout 영향 주의.
- **Redis 접속 실패**
  → `redis-cli ping`으로 확인, WSL2 네트워킹(127.0.0.1) 매핑 확인.
- **RabbitMQ 연결 실패**
  → Erlang 버전 호환 매트릭스 확인, 서비스 상태 및 사용자/권한 점검.

---

## 6. 테스트 & 품질 게이트

```bash
# Unit
pytest -q

# Lint
ruff check . || flake8 .

# Type
mypy .

# (옵션) Celery E2E
pytest -m "e2e and celery"
```

> 기존 **RED→GREEN→REFACTOR** 루프/머지 게이트 규칙 준수.

```

---

# 4) `plan.md` 변경 요약 (Phase 5 치환)

- **Phase 5: Docker Compose 통합 → Phase 5’: No-Docker Runtime(Procfile + Honcho)**
  - 5’.1 `Procfile.dev` 추가(웹/워커/비트 정의) — 이 답변의 파일 사용. :contentReference[oaicite:8]{index=8}
  - 5’.2 `.env.example` 추가 → `.env` 로컬 구성(브로커 URL/플래그)
  - 5’.3 브로커 설치: **Redis(WSL2 권장)** 또는 **RabbitMQ(Windows 네이티브)**. 공식 가이드 링크 포함. :contentReference[oaicite:9]{index=9}
  - 5’.4 기동: `honcho -f Procfile.dev start` (Heroku Local/Foreman도 호환). :contentReference[oaicite:10]{index=10}
  - 5’.5 Windows Celery 워커 풀 주의(개발: `-P solo`). :contentReference[oaicite:11]{index=11}

---

원하면 위 3개 파일을 **repo에 바로 넣을 수 있게 PR용 패치 블록**으로 재정렬해줄게. 진행할까?
::contentReference[oaicite:12]{index=12}
```
