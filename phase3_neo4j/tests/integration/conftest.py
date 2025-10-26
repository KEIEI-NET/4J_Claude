"""
Integration Test Configuration

統合テスト用の共通設定
"""

import os
import pytest
from pathlib import Path

# IMPORTANT: 環境変数をモジュールレベルで設定（フィクスチャより前に実行される）
# これにより、celery_appのインポート時にEager modeが有効になる
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "True"
os.environ["CELERY_TASK_EAGER_PROPAGATES"] = "True"

# テスト環境の接続設定
os.environ.setdefault("CELERY_BROKER_URL", "amqp://test:test@localhost:5673//")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7688")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "testpassword")


# テストフィクスチャのパス
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "integration"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境のセットアップとクリーンアップ"""
    # 環境変数は既にモジュールレベルで設定済み
    yield

    # クリーンアップ（オプション - テスト後に環境変数を削除）
    # 注: 通常はテストプロセス終了時に自動的にクリーンアップされるため不要
    # os.environ.pop("CELERY_TASK_ALWAYS_EAGER", None)
    # os.environ.pop("CELERY_TASK_EAGER_PROPAGATES", None)
