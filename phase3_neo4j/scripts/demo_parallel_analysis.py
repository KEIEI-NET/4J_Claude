#!/usr/bin/env python
"""
Parallel Analysis Demo Script

Celeryを使用した並列ファイル分析とグラフ更新のデモ
"""

import sys
import time
from pathlib import Path
from typing import List

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph_analyzer.worker.tasks import (
    analyze_file,
    batch_analyze_files,
    analyze_and_update_graph,
)


def demo_single_file_analysis():
    """単一ファイル分析のデモ"""
    print("\n" + "="*60)
    print("Demo 1: Single File Analysis")
    print("="*60)

    file_path = "example/UserService.java"
    print(f"Analyzing file: {file_path}")

    # タスクを非同期で実行
    result = analyze_file.delay(file_path, config={"enabled": True})

    print(f"Task ID: {result.id}")
    print("Waiting for result...")

    try:
        # 結果を待機（タイムアウト: 30秒）
        analysis_result = result.get(timeout=30)
        print(f"Analysis completed successfully!")
        print(f"Status: {analysis_result['status']}")
        print(f"Issues found: {len(analysis_result['issues'])}")
    except Exception as e:
        print(f"Analysis failed: {e}")


def demo_batch_analysis():
    """バッチファイル分析のデモ"""
    print("\n" + "="*60)
    print("Demo 2: Batch File Analysis")
    print("="*60)

    file_paths = [
        "example/UserService.java",
        "example/OrderService.java",
        "example/ProductRepository.java",
        "example/CartController.java",
        "example/PaymentProcessor.java",
    ]

    print(f"Analyzing {len(file_paths)} files in parallel...")
    for i, path in enumerate(file_paths, 1):
        print(f"  {i}. {path}")

    # バッチ分析タスクを実行
    start_time = time.time()
    result = batch_analyze_files.delay(file_paths, config={"enabled": True})

    print(f"\nTask ID: {result.id}")
    print("Waiting for results...")

    try:
        # 結果を待機（タイムアウト: 60秒）
        batch_result = result.get(timeout=60)
        elapsed_time = time.time() - start_time

        print(f"\nBatch analysis completed in {elapsed_time:.2f}s")
        print(f"Total files: {batch_result['total_files']}")
        print(f"Successful: {batch_result['successful']}")
        print(f"Failed: {batch_result['failed']}")

        # 各ファイルの結果を表示
        print("\nResults per file:")
        for i, file_result in enumerate(batch_result['results'], 1):
            status = file_result.get('status', 'unknown')
            file_name = file_result.get('file', 'unknown')
            issue_count = len(file_result.get('issues', []))
            print(f"  {i}. {file_name}: {status} ({issue_count} issues)")

    except Exception as e:
        print(f"Batch analysis failed: {e}")


def demo_analyze_and_update_graph():
    """分析とグラフ更新の統合デモ"""
    print("\n" + "="*60)
    print("Demo 3: Analyze and Update Graph (Chord Pattern)")
    print("="*60)

    file_paths = [
        "example/UserService.java",
        "example/OrderService.java",
        "example/ProductRepository.java",
    ]

    print(f"Analyzing {len(file_paths)} files and updating Neo4j graph...")
    for i, path in enumerate(file_paths, 1):
        print(f"  {i}. {path}")

    # Neo4j接続情報
    neo4j_uri = "bolt://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "password"

    # 分析とグラフ更新を実行
    start_time = time.time()
    result = analyze_and_update_graph.delay(
        file_paths,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        config={"enabled": True}
    )

    print(f"\nTask ID: {result.id}")
    print("Chord pattern: files are analyzed in parallel, then graph is updated")
    print("Waiting for completion...")

    try:
        # 結果を待機（タイムアウト: 120秒）
        chord_result = result.get(timeout=120)
        elapsed_time = time.time() - start_time

        print(f"\nAnalysis and graph update completed in {elapsed_time:.2f}s")
        print(f"Status: {chord_result['status']}")
        print(f"Task ID: {chord_result.get('task_id', 'N/A')}")
        print(f"Files processed: {chord_result.get('file_count', 0)}")

    except Exception as e:
        print(f"Chord task failed: {e}")


def demo_task_monitoring():
    """タスク監視のデモ"""
    print("\n" + "="*60)
    print("Demo 4: Task Monitoring")
    print("="*60)

    file_paths = ["example/UserService.java", "example/OrderService.java"]

    # タスクを非同期で実行
    result = batch_analyze_files.delay(file_paths)

    print(f"Task ID: {result.id}")
    print("Monitoring task progress...")

    # タスクの状態を監視
    while not result.ready():
        print(f"  Task state: {result.state}")
        time.sleep(1)

    if result.successful():
        print(f"  Task completed successfully!")
        final_result = result.get()
        print(f"  Results: {final_result['successful']}/{final_result['total_files']} files analyzed")
    else:
        print(f"  Task failed!")


def main():
    """デモを実行"""
    print("\n" + "="*70)
    print(" "*15 + "Celery Parallel Processing Demo")
    print("="*70)
    print("\nMake sure the following services are running:")
    print("  1. RabbitMQ (amqp://localhost:5672)")
    print("  2. Redis (redis://localhost:6379)")
    print("  3. Neo4j (bolt://localhost:7687)")
    print("  4. Celery Worker (python scripts/start_worker.py)")
    print("\nPress Enter to continue, or Ctrl+C to cancel...")

    try:
        input()
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
        return

    # 各デモを実行
    try:
        demo_single_file_analysis()
        time.sleep(2)

        demo_batch_analysis()
        time.sleep(2)

        demo_analyze_and_update_graph()
        time.sleep(2)

        demo_task_monitoring()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("Demo completed!")
    print("="*70)
    print("\nTo monitor tasks in real-time, open Flower UI:")
    print("  http://localhost:5555")
    print("\nTo view Neo4j graph:")
    print("  http://localhost:7474 (user: neo4j, password: password)")


if __name__ == '__main__':
    main()
