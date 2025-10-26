"""
Celery Application Configuration

並列処理基盤のCeleryアプリケーション設定
"""

import os
from celery import Celery
from kombu import Queue

# 環境変数から設定を取得
BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Celeryアプリケーションを作成
app = Celery(
    "graph_analyzer",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

# テスト環境の検出
import sys
import logging

# ロガーを取得
logger = logging.getLogger(__name__)

IS_TEST = "pytest" in sys.modules or os.getenv("CELERY_TASK_ALWAYS_EAGER") == "True"

# デバッグログ: Eager mode検出状態を記録
if IS_TEST:
    logger.info("TEST MODE DETECTED - Enabling Celery Eager mode")
    logger.info(f"  - pytest in sys.modules: {'pytest' in sys.modules}")
    logger.info(f"  - CELERY_TASK_ALWAYS_EAGER: {os.getenv('CELERY_TASK_ALWAYS_EAGER')}")

# Celery設定
app.conf.update(
    # タスク設定
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,

    # テスト環境ではEager modeを有効化
    task_always_eager=IS_TEST,
    task_eager_propagates=IS_TEST,

    # ワーカー設定
    worker_prefetch_multiplier=1,  # 一度に1タスクのみ取得
    worker_max_tasks_per_child=100,  # 100タスクごとにワーカーを再起動

    # タスクルーティング
    task_routes={
        "graph_analyzer.worker.tasks.analyze_file": {"queue": "analysis"},
        "graph_analyzer.worker.tasks.batch_analyze_files": {"queue": "analysis"},
        "graph_analyzer.worker.tasks.update_graph": {"queue": "graph"},
        "graph_analyzer.worker.tasks.batch_update_graph": {"queue": "graph"},
    },

    # キュー設定
    task_queues=(
        Queue("analysis", routing_key="analysis"),
        Queue("graph", routing_key="graph"),
        Queue("default", routing_key="default"),
    ),

    # タスク実行設定
    task_acks_late=True,  # タスク完了後にACK
    task_reject_on_worker_lost=True,  # ワーカーロスト時はリジェクト

    # リトライ設定
    task_default_retry_delay=60,  # 60秒後にリトライ
    task_max_retries=3,  # 最大3回リトライ

    # タイムアウト設定
    task_soft_time_limit=300,  # 5分でソフトタイムアウト
    task_time_limit=600,  # 10分でハードタイムアウト

    # 結果設定
    result_expires=3600,  # 結果を1時間保持
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Beat設定（定期タスク用）
    beat_schedule={
        # 毎日午前2時に実行
        "daily-cleanup": {
            "task": "graph_analyzer.worker.tasks.cleanup_old_results",
            "schedule": 7200.0,  # 2時間ごと
        },
    },
)

# タスクの自動検出
app.autodiscover_tasks(["graph_analyzer.worker"])


if __name__ == "__main__":
    app.start()
