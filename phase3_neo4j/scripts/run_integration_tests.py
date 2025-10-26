#!/usr/bin/env python
"""
Integration Test Runner (Python version)

統合テストを実行するPythonスクリプト
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# プロジェクトルートとsrcディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))
os.environ["PYTHONPATH"] = f"{src_dir}{os.pathsep}{project_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"


def run_command(cmd, capture_output=False, shell=False):
    """コマンドを実行"""
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=shell,
                cwd=project_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=shell, cwd=project_root)
            return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def print_header(text):
    """ヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(step_num, text):
    """ステップを表示"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {text}")
    print('='*60)


def main():
    """統合テストを実行"""
    print_header("Celery Integration Test Runner")

    # ステップ1: 既存のテストコンテナを停止
    print_step(1, "Stopping existing test containers...")
    run_command(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"])

    # ステップ2: Dockerサービスを起動
    print_step(2, "Starting Docker services (RabbitMQ, Redis, Neo4j)...")
    success = run_command([
        "docker-compose", "-f", "docker-compose.test.yml",
        "up", "-d", "rabbitmq-test", "redis-test", "neo4j-test"
    ])

    if not success:
        print("ERROR: Failed to start Docker services")
        return 1

    # ステップ3: サービスの起動を待機
    print_step(3, "Waiting for services to be ready...")
    print("  - Waiting for RabbitMQ...")
    time.sleep(10)
    print("  - Waiting for Redis...")
    time.sleep(5)
    print("  - Waiting for Neo4j...")
    time.sleep(30)
    print("All services should be ready!")

    # ステップ4: Celeryワーカーをバックグラウンドで起動
    print_step(4, "Starting Celery worker in background...")

    # 環境変数を設定
    os.environ["CELERY_BROKER_URL"] = "amqp://test:test@localhost:5673//"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6380/0"

    # Celeryワーカーを起動
    worker_log_file = open(project_root / "celery_worker.log", "w")
    worker_process = subprocess.Popen(
        [sys.executable, "scripts/start_worker.py"],
        stdout=worker_log_file,
        stderr=subprocess.STDOUT,
        cwd=project_root
    )

    print(f"Celery worker started with PID: {worker_process.pid}")
    print("Waiting for worker to initialize...")
    time.sleep(10)

    # ステップ5: 統合テストを実行
    print_step(5, "Running integration tests...")

    # 環境変数を設定
    os.environ["NEO4J_URI"] = "bolt://localhost:7688"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "testpassword"

    # pytestを実行
    test_success = run_command([
        sys.executable, "-m", "pytest",
        "tests/integration/test_celery_integration.py",
        "-v", "--tb=short", "--color=yes"
    ])

    # ステップ6: クリーンアップ
    print_step(6, "Cleanup...")

    # Celeryワーカーを停止
    print("Stopping Celery worker...")
    try:
        worker_process.terminate()
        worker_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        worker_process.kill()
    worker_log_file.close()

    # Dockerサービスを停止
    print("Stopping Docker services...")
    run_command(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"])

    # 結果を表示
    print("\n")
    if test_success:
        print_header("Integration tests PASSED!")
        return 0
    else:
        print_header("Integration tests FAILED!")
        print("\nCheck the logs:")
        print("  - Celery worker: celery_worker.log")
        print("  - Docker services: docker-compose -f docker-compose.test.yml logs")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        print("Cleaning up...")
        run_command(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"])
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
