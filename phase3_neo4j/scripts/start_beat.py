#!/usr/bin/env python
"""
Celery Beat Start Script

Celery Beatスケジューラーを起動するスクリプト
定期タスクを管理
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph_analyzer.worker.celery_app import app


def main():
    """Celery Beatスケジューラーを起動"""
    print("Starting Celery Beat scheduler...")
    print(f"Broker: {os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')}")
    print(f"Backend: {os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')}")
    print("Scheduled tasks:")

    # スケジュールされたタスクを表示
    for task_name, task_config in app.conf.beat_schedule.items():
        schedule = task_config['schedule']
        if isinstance(schedule, (int, float)):
            schedule_str = f"every {schedule}s"
        else:
            schedule_str = str(schedule)
        print(f"  - {task_name}: {task_config['task']} ({schedule_str})")

    # Beatスケジューラーを起動
    app.start(argv=[
        'beat',
        '--loglevel=INFO',
    ])


if __name__ == '__main__':
    main()
