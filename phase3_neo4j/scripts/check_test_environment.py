#!/usr/bin/env python
"""
Test Environment Checker

統合テスト環境が正しくセットアップされているかを確認するスクリプト
"""

import sys
import subprocess
from pathlib import Path


def check_command(name, cmd):
    """コマンドが利用可能かチェック"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            print(f"[OK] {name} is available")
            return True
        else:
            print(f"[FAIL] {name} is not available")
            return False
    except Exception as e:
        print(f"[FAIL] {name} check failed: {e}")
        return False


def check_file_exists(name, path):
    """ファイルが存在するかチェック"""
    if path.exists():
        print(f"[OK] {name} exists: {path}")
        return True
    else:
        print(f"[FAIL] {name} not found: {path}")
        return False


def check_docker_compose_file(path):
    """docker-compose.test.ymlの内容をチェック"""
    if not path.exists():
        print(f"✗ Docker Compose file not found: {path}")
        return False

    try:
        with open(path, 'r') as f:
            content = f.read()

        required_services = ['rabbitmq-test', 'redis-test', 'neo4j-test']
        all_present = True

        for service in required_services:
            if service in content:
                print(f"  [OK] Service '{service}' is defined")
            else:
                print(f"  [FAIL] Service '{service}' is missing")
                all_present = False

        return all_present
    except Exception as e:
        print(f"[FAIL] Error reading Docker Compose file: {e}")
        return False


def main():
    """環境チェックを実行"""
    print("=" * 60)
    print("  Integration Test Environment Checker")
    print("=" * 60)
    print()

    project_root = Path(__file__).parent.parent
    checks_passed = []

    # 1. Python環境チェック
    print("[1] Python Environment")
    print(f"  Python version: {sys.version}")
    checks_passed.append(True)
    print()

    # 2. Dockerチェック
    print("[2] Docker")
    docker_ok = check_command("Docker", "docker --version")
    checks_passed.append(docker_ok)
    print()

    # 3. Docker Composeチェック
    print("[3] Docker Compose")
    compose_ok = check_command("Docker Compose", "docker-compose --version")
    checks_passed.append(compose_ok)
    print()

    # 4. Pythonパッケージチェック
    print("[4] Python Packages")
    packages = ['pytest', 'celery', 'redis', 'neo4j']
    packages_ok = True
    for package in packages:
        try:
            __import__(package)
            print(f"  [OK] {package} is installed")
        except ImportError:
            print(f"  [FAIL] {package} is not installed")
            packages_ok = False
    checks_passed.append(packages_ok)
    print()

    # 5. 必須ファイルチェック
    print("[5] Required Files")
    files_ok = True

    files_to_check = [
        ("docker-compose.test.yml", project_root / "docker-compose.test.yml"),
        ("Dockerfile.test", project_root / "Dockerfile.test"),
        ("Integration test file", project_root / "tests" / "integration" / "test_celery_integration.py"),
        ("Test fixture 1", project_root / "tests" / "fixtures" / "integration" / "SampleService.java"),
        ("Test fixture 2", project_root / "tests" / "fixtures" / "integration" / "OrderRepository.java"),
        ("Worker start script", project_root / "scripts" / "start_worker.py"),
        ("Test runner script", project_root / "scripts" / "run_integration_tests.py"),
    ]

    for name, path in files_to_check:
        if not check_file_exists(name, path):
            files_ok = False

    checks_passed.append(files_ok)
    print()

    # 6. Docker Compose設定チェック
    print("[6] Docker Compose Configuration")
    compose_config_ok = check_docker_compose_file(project_root / "docker-compose.test.yml")
    checks_passed.append(compose_config_ok)
    print()

    # 7. ポート可用性チェック（オプション）
    print("[7] Port Availability (optional)")
    print("  Required ports for test environment:")
    print("    - 5673  (RabbitMQ AMQP)")
    print("    - 15673 (RabbitMQ Management)")
    print("    - 6380  (Redis)")
    print("    - 7475  (Neo4j HTTP)")
    print("    - 7688  (Neo4j Bolt)")
    print("  Note: Ports will be checked when services start")
    print()

    # 結果サマリー
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    all_ok = all(checks_passed)

    if all_ok:
        print("[OK] All checks passed!")
        print("\nYou can now run integration tests with:")
        print("  python scripts/run_integration_tests.py")
        return 0
    else:
        print("[FAIL] Some checks failed!")
        print("\nPlease fix the issues above before running integration tests.")
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
        print("\nTo install Docker:")
        print("  https://docs.docker.com/get-docker/")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
