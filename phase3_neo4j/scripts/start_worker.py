#!/usr/bin/env python
"""
Celery Worker Start Script

Celeryワーカーを起動するスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートとsrcディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

from src.graph_analyzer.worker.celery_app import app


def main():
    """Celeryワーカーを起動"""
    # ワーカー設定
    worker_options = {
        'loglevel': 'INFO',
        'concurrency': 4,  # 並列ワーカー数
        'queues': ['analysis', 'graph', 'default'],  # 監視するキュー
        'hostname': 'worker@%h',
        'max_tasks_per_child': 100,  # 100タスクごとにワーカーを再起動
    }

    print("Starting Celery worker...")
    print(f"Broker: {os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')}")
    print(f"Backend: {os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')}")
    print(f"Queues: {worker_options['queues']}")
    print(f"Concurrency: {worker_options['concurrency']}")

    # ワーカーを起動
    # Windowsの場合は-P soloを使用（preforkは未サポート）
    import platform
    pool_type = 'solo' if platform.system() == 'Windows' else 'prefork'

    app.worker_main(argv=[
        'worker',
        f'--loglevel={worker_options["loglevel"]}',
        f'--concurrency={worker_options["concurrency"]}',
        f'--queues={",".join(worker_options["queues"])}',
        f'--hostname={worker_options["hostname"]}',
        f'--max-tasks-per-child={worker_options["max_tasks_per_child"]}',
        f'--pool={pool_type}',
    ])


if __name__ == '__main__':
    main()
