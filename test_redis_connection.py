#!/usr/bin/env python3
"""
Redis 연결 테스트
WSL2 Redis 서버 상태 확인

Usage:
    python test_redis_connection.py
"""

import redis
import os
from dotenv import load_dotenv

load_dotenv()


def test_redis_connection():
    """Redis 연결 테스트"""

    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

    print(f"\n{'='*60}")
    print("Redis 연결 테스트")
    print(f"{'='*60}")
    print(f"Broker URL: {broker_url}")

    try:
        # Parse Redis URL
        # redis://localhost:6379/0 → host=localhost, port=6379, db=0
        parts = broker_url.replace("redis://", "").split("/")
        host_port = parts[0].split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 6379
        db = int(parts[1]) if len(parts) > 1 else 0

        # Connect
        r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

        # Ping
        pong = r.ping()

        if pong:
            print(f"\n✅ Redis 연결 성공!")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   DB: {db}")

            # Server info
            info = r.info("server")
            print(f"\n📊 Redis 서버 정보:")
            print(f"   Version: {info.get('redis_version')}")
            print(f"   Mode: {info.get('redis_mode')}")
            print(f"   OS: {info.get('os')}")

            # Memory info
            memory = r.info("memory")
            used_memory_mb = memory.get("used_memory", 0) / 1024 / 1024
            print(f"\n💾 메모리 사용:")
            print(f"   Used: {used_memory_mb:.2f} MB")

            # Key count
            key_count = r.dbsize()
            print(f"\n🔑 키 개수: {key_count}")

            return True
        else:
            print("\n❌ Redis PING 실패")
            return False

    except redis.ConnectionError as e:
        print(f"\n❌ Redis 연결 실패!")
        print(f"   Error: {e}")
        print(f"\n해결 방법:")
        print(f"   1. WSL2에서 Redis 시작:")
        print(f"      wsl")
        print(f"      sudo service redis-server start")
        print(f"   2. Redis 확인:")
        print(f"      redis-cli ping")
        return False

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def test_celery_connection():
    """Celery 연결 테스트"""

    print(f"\n{'='*60}")
    print("Celery 연결 테스트")
    print(f"{'='*60}")

    try:
        from celery import Celery

        broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

        app = Celery("test", broker=broker_url, backend=backend_url)

        # Check broker connection
        app.connection().ensure_connection(max_retries=3)

        print(f"\n✅ Celery Broker 연결 성공!")
        print(f"   Broker: {broker_url}")
        print(f"   Backend: {backend_url}")

        # Check active workers
        inspect = app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            worker_count = len(active_workers)
            print(f"\n👷 활성 Worker: {worker_count}개")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
        else:
            print(f"\n⚠️ 활성 Worker 없음")
            print(f"   Worker 시작 필요:")
            print(f"   honcho -f Procfile.dev start")

        return True

    except Exception as e:
        print(f"\n❌ Celery 연결 실패: {e}")
        return False


if __name__ == "__main__":
    # Redis 테스트
    redis_ok = test_redis_connection()

    # Celery 테스트
    celery_ok = test_celery_connection()

    # 최종 결과
    print(f"\n{'='*60}")
    print("테스트 결과")
    print(f"{'='*60}")
    print(f"Redis:  {'✅ OK' if redis_ok else '❌ FAIL'}")
    print(f"Celery: {'✅ OK' if celery_ok else '❌ FAIL'}")
    print(f"{'='*60}\n")

    if redis_ok and celery_ok:
        print("✅ 모든 테스트 통과! Hybrid System 준비 완료.")
        exit(0)
    else:
        print("❌ 일부 테스트 실패. 위 해결 방법을 확인하세요.")
        exit(1)
