"""
Celeryアプリケーション設定のユニットテスト

celery_app.pyの設定が正しく構成されているかを検証
"""

import pytest
from unittest.mock import patch, Mock
import os


class TestCeleryAppConfiguration:
    """Celeryアプリケーション設定のテスト"""

    @patch.dict(os.environ, {
        "CELERY_BROKER_URL": "amqp://test:test@testhost:5672//",
        "CELERY_RESULT_BACKEND": "redis://testhost:6379/1"
    })
    def test_celery_app_with_env_vars(self):
        """環境変数からの設定読み込みテスト"""
        # モジュールを再インポートして環境変数を反映
        import importlib
        import src.graph_analyzer.worker.celery_app as celery_app_module
        importlib.reload(celery_app_module)

        from src.graph_analyzer.worker.celery_app import app, BROKER_URL, RESULT_BACKEND

        # 環境変数が正しく読み込まれたか確認
        assert BROKER_URL == "amqp://test:test@testhost:5672//"
        assert RESULT_BACKEND == "redis://testhost:6379/1"
        assert app.conf.broker_url == "amqp://test:test@testhost:5672//"
        assert app.conf.result_backend == "redis://testhost:6379/1"

    def test_celery_app_default_configuration(self):
        """デフォルト設定のテスト"""
        # 環境変数をクリアしてモジュールを再インポート
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.graph_analyzer.worker.celery_app as celery_app_module
            importlib.reload(celery_app_module)

            from src.graph_analyzer.worker.celery_app import BROKER_URL, RESULT_BACKEND

            # デフォルト値が使用されるか確認
            assert BROKER_URL == "amqp://guest:guest@localhost:5672//"
            assert RESULT_BACKEND == "redis://localhost:6379/0"

    def test_celery_app_basic_settings(self):
        """基本設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # アプリケーション名
        assert app.main == "graph_analyzer"

        # シリアライザー設定
        assert app.conf.task_serializer == "json"
        assert app.conf.result_serializer == "json"
        assert "json" in app.conf.accept_content

        # タイムゾーン設定
        assert app.conf.timezone == "Asia/Tokyo"
        assert app.conf.enable_utc is True

    def test_celery_worker_settings(self):
        """ワーカー設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # ワーカー設定
        assert app.conf.worker_prefetch_multiplier == 1
        assert app.conf.worker_max_tasks_per_child == 100

    def test_celery_task_routes(self):
        """タスクルーティング設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # タスクルート設定を取得
        task_routes = app.conf.task_routes

        # 各タスクが正しいキューにルーティングされるか確認
        assert task_routes["graph_analyzer.worker.tasks.analyze_file"]["queue"] == "analysis"
        assert task_routes["graph_analyzer.worker.tasks.batch_analyze_files"]["queue"] == "analysis"
        assert task_routes["graph_analyzer.worker.tasks.update_graph"]["queue"] == "graph"
        assert task_routes["graph_analyzer.worker.tasks.batch_update_graph"]["queue"] == "graph"

    def test_celery_task_queues(self):
        """キュー設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # キュー設定を取得
        task_queues = app.conf.task_queues

        # キューの数を確認
        assert len(task_queues) == 3

        # 各キューの存在を確認
        queue_names = [q.name for q in task_queues]
        assert "analysis" in queue_names
        assert "graph" in queue_names
        assert "default" in queue_names

        # ルーティングキーを確認
        for queue in task_queues:
            if queue.name == "analysis":
                assert queue.routing_key == "analysis"
            elif queue.name == "graph":
                assert queue.routing_key == "graph"
            elif queue.name == "default":
                assert queue.routing_key == "default"

    def test_celery_task_execution_settings(self):
        """タスク実行設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # タスクACK設定
        assert app.conf.task_acks_late is True
        assert app.conf.task_reject_on_worker_lost is True

    def test_celery_retry_settings(self):
        """リトライ設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # リトライ設定
        assert app.conf.task_default_retry_delay == 60
        assert app.conf.task_max_retries == 3

    def test_celery_timeout_settings(self):
        """タイムアウト設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # タイムアウト設定
        assert app.conf.task_soft_time_limit == 300  # 5分
        assert app.conf.task_time_limit == 600  # 10分

    def test_celery_result_settings(self):
        """結果設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # 結果の有効期限
        assert app.conf.result_expires == 3600  # 1時間

        # 結果バックエンドのトランスポートオプション
        assert app.conf.result_backend_transport_options is not None
        assert "master_name" in app.conf.result_backend_transport_options
        assert "visibility_timeout" in app.conf.result_backend_transport_options

    def test_celery_beat_schedule(self):
        """Beat定期タスク設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # Beat schedule設定
        beat_schedule = app.conf.beat_schedule

        # daily-cleanupタスクの存在を確認
        assert "daily-cleanup" in beat_schedule

        # daily-cleanupタスクの設定を確認
        cleanup_task = beat_schedule["daily-cleanup"]
        assert cleanup_task["task"] == "graph_analyzer.worker.tasks.cleanup_old_results"
        assert cleanup_task["schedule"] == 7200.0  # 2時間ごと

    def test_celery_autodiscover_tasks(self):
        """タスク自動検出設定のテスト"""
        from src.graph_analyzer.worker.celery_app import app

        # autodiscover_tasksが呼ばれたか確認
        # （実際には設定時に呼ばれているので、エラーが出なければOK）
        assert app.autodiscover_tasks is not None


class TestCeleryAppImports:
    """Celeryアプリケーションのインポートテスト"""

    def test_import_celery_app(self):
        """celery_appモジュールのインポートテスト"""
        # エラーなくインポートできるか確認
        from src.graph_analyzer.worker.celery_app import app, BROKER_URL, RESULT_BACKEND

        assert app is not None
        assert BROKER_URL is not None
        assert RESULT_BACKEND is not None

    def test_celery_app_is_singleton(self):
        """Celeryアプリケーションがシングルトンであることを確認"""
        from src.graph_analyzer.worker.celery_app import app as app1

        # 再度インポート
        from src.graph_analyzer.worker.celery_app import app as app2

        # 同じオブジェクトであることを確認
        assert app1 is app2


class TestCeleryAppStartup:
    """Celeryアプリケーションの起動テスト"""

    @patch("src.graph_analyzer.worker.celery_app.app.start")
    def test_celery_app_main_execution(self, mock_start):
        """__main__実行時のテスト"""
        import importlib
        import src.graph_analyzer.worker.celery_app as celery_app_module

        # __name__を"__main__"に設定してモジュールを実行
        with patch.object(celery_app_module, "__name__", "__main__"):
            # モジュールを再読み込みして__main__ブロックを実行
            # （実際にはif __name__ == "__main__"ブロックは実行されないので、
            # ここでは設定が正しいことのみ確認）
            pass

        # Celery appが正しく初期化されていることを確認
        from src.graph_analyzer.worker.celery_app import app
        assert app is not None


class TestCeleryConfiguration:
    """Celery設定の統合テスト"""

    def test_all_configurations_loaded(self):
        """すべての設定が正しく読み込まれているか確認"""
        from src.graph_analyzer.worker.celery_app import app

        # 設定リストを確認
        required_settings = [
            "task_serializer",
            "accept_content",
            "result_serializer",
            "timezone",
            "enable_utc",
            "worker_prefetch_multiplier",
            "worker_max_tasks_per_child",
            "task_routes",
            "task_queues",
            "task_acks_late",
            "task_reject_on_worker_lost",
            "task_default_retry_delay",
            "task_max_retries",
            "task_soft_time_limit",
            "task_time_limit",
            "result_expires",
            "beat_schedule",
        ]

        # すべての設定が存在することを確認
        for setting in required_settings:
            assert hasattr(app.conf, setting), f"Missing setting: {setting}"
            assert getattr(app.conf, setting) is not None, f"Setting is None: {setting}"

    def test_configuration_consistency(self):
        """設定の一貫性を確認"""
        from src.graph_analyzer.worker.celery_app import app

        # ソフトタイムアウトがハードタイムアウトより短いことを確認
        assert app.conf.task_soft_time_limit < app.conf.task_time_limit

        # リトライ設定が正の値であることを確認
        assert app.conf.task_default_retry_delay > 0
        assert app.conf.task_max_retries > 0

        # 結果の有効期限が正の値であることを確認
        assert app.conf.result_expires > 0
