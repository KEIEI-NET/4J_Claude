"""
Celery Tasks for Parallel Processing

並列処理用のCeleryタスク定義
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from celery import group, chord
from .celery_app import app
from ..graph.neo4j_client import Neo4jClient
from ..graph.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


@app.task(bind=True, name="graph_analyzer.worker.tasks.analyze_file")
def analyze_file(
    self,
    file_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    単一ファイルを分析

    Args:
        file_path: 分析対象ファイルのパス
        config: 分析設定

    Returns:
        分析結果の辞書
    """
    try:
        logger.info(f"Analyzing file: {file_path}")

        # ファイルの存在確認
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # TODO: Phase 1の分析ロジックを統合
        # 現在は仮の実装
        result = {
            "file": file_path,
            "status": "success",
            "issues": [],
            "analyzed_at": "2025-01-27T00:00:00",
        }

        logger.info(f"Analysis completed: {file_path}")
        return result

    except Exception as e:
        logger.error(f"Analysis failed for {file_path}: {e}")
        # Celeryのリトライ機能を使用
        raise self.retry(exc=e, countdown=60, max_retries=3)


@app.task(bind=True, name="graph_analyzer.worker.tasks.batch_analyze_files")
def batch_analyze_files(
    self,
    file_paths: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    複数ファイルをバッチ分析

    Args:
        file_paths: 分析対象ファイルのパスリスト
        config: 分析設定

    Returns:
        バッチ分析結果
    """
    try:
        logger.info(f"Starting batch analysis of {len(file_paths)} files")

        # Eager modeの場合は直接実行、そうでない場合はgroupを使用
        if app.conf.task_always_eager:
            # Eager mode: 各タスクを直接実行して結果を収集
            results = []
            for file_path in file_paths:
                try:
                    result = analyze_file(file_path, config)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}")
                    results.append({"status": "error", "error": str(e)})
        else:
            # 本番環境: groupで並列処理（callback使用）
            job = group(analyze_file.s(file_path, config) for file_path in file_paths)
            result = job.apply_async()
            # 注: 本番環境ではこの結果はGroupResultとして返され、
            # 呼び出し側で.get()を使って結果を取得する
            return {
                "status": "submitted",
                "total_files": len(file_paths),
                "task_id": result.id
            }

        # 統計情報を集計（Eager modeのみ）
        total_files = len(results)
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = total_files - successful

        batch_result = {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "results": results,
        }

        logger.info(f"Batch analysis completed: {successful}/{total_files} successful")
        return batch_result

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)


@app.task(bind=True, name="graph_analyzer.worker.tasks.update_graph")
def update_graph(
    self,
    analysis_result: Dict[str, Any],
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """
    分析結果からグラフを更新

    Args:
        analysis_result: 分析結果
        neo4j_uri: Neo4j接続URI
        neo4j_user: Neo4jユーザー名
        neo4j_password: Neo4jパスワード

    Returns:
        グラフ更新結果
    """
    try:
        logger.info("Updating graph with analysis results")

        # Neo4jクライアントを初期化
        client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)

        # GraphBuilderでグラフを構築
        builder = GraphBuilder()
        nodes, relationships = builder.build_from_analysis_result(analysis_result)

        # グラフをNeo4jにインポート
        node_ids = client.batch_create_nodes(nodes)
        rel_count = client.batch_create_relationships(relationships)

        # 接続を閉じる
        client.close()

        result = {
            "status": "success",
            "nodes_created": len(node_ids),
            "relationships_created": rel_count,
        }

        logger.info(f"Graph updated: {len(node_ids)} nodes, {rel_count} relationships")
        return result

    except Exception as e:
        logger.error(f"Graph update failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@app.task(bind=True, name="graph_analyzer.worker.tasks.batch_update_graph")
def batch_update_graph(
    self,
    analysis_results: List[Dict[str, Any]],
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """
    複数の分析結果からグラフをバッチ更新

    Args:
        analysis_results: 分析結果のリスト
        neo4j_uri: Neo4j接続URI
        neo4j_user: Neo4jユーザー名
        neo4j_password: Neo4jパスワード

    Returns:
        バッチ更新結果
    """
    try:
        logger.info(f"Batch updating graph with {len(analysis_results)} results")

        total_nodes = 0
        total_rels = 0

        # Neo4jクライアントを初期化
        client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)

        for result in analysis_results:
            # GraphBuilderでグラフを構築
            builder = GraphBuilder()
            nodes, relationships = builder.build_from_analysis_result(result)

            # グラフをNeo4jにインポート
            node_ids = client.batch_create_nodes(nodes)
            rel_count = client.batch_create_relationships(relationships)

            total_nodes += len(node_ids)
            total_rels += rel_count

        # 接続を閉じる
        client.close()

        batch_result = {
            "status": "success",
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
            "results_processed": len(analysis_results),
        }

        logger.info(f"Batch graph update completed: {total_nodes} nodes, {total_rels} relationships")
        return batch_result

    except Exception as e:
        logger.error(f"Batch graph update failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)


@app.task(name="graph_analyzer.worker.tasks.cleanup_old_results")
def cleanup_old_results() -> Dict[str, Any]:
    """
    古い分析結果をクリーンアップ

    Returns:
        クリーンアップ結果
    """
    try:
        logger.info("Starting cleanup of old results")

        # TODO: Redis/データベースから古い結果を削除
        # 現在は仮の実装
        cleaned_count = 0

        result = {
            "status": "success",
            "cleaned_count": cleaned_count,
        }

        logger.info(f"Cleanup completed: {cleaned_count} old results removed")
        return result

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


@app.task(bind=True, name="graph_analyzer.worker.tasks.analyze_and_update_graph")
def analyze_and_update_graph(
    self,
    file_paths: List[str],
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    ファイル分析とグラフ更新を一貫して実行

    Chordパターンを使用して、分析完了後にグラフ更新を実行

    Args:
        file_paths: 分析対象ファイルのパスリスト
        neo4j_uri: Neo4j接続URI
        neo4j_user: Neo4jユーザー名
        neo4j_password: Neo4jパスワード
        config: 分析設定

    Returns:
        実行結果
    """
    try:
        logger.info(f"Starting analyze_and_update_graph for {len(file_paths)} files")

        # Eager modeの場合は直接実行
        if app.conf.task_always_eager:
            # Eager mode: 分析を実行してから更新
            analysis_results = []
            for file_path in file_paths:
                try:
                    result = analyze_file(file_path, config)
                    analysis_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}")
                    analysis_results.append({"status": "error", "error": str(e)})

            # グラフを更新
            update_result = batch_update_graph(
                analysis_results,
                neo4j_uri,
                neo4j_user,
                neo4j_password
            )

            return {
                "status": "completed",
                "file_count": len(file_paths),
                "analysis_results": analysis_results,
                "update_result": update_result,
            }
        else:
            # 本番環境: Chordパターンで並列実行
            callback = batch_update_graph.s(neo4j_uri, neo4j_user, neo4j_password)
            header = group(analyze_file.s(fp, config) for fp in file_paths)

            result = chord(header)(callback)

            return {
                "status": "started",
                "task_id": result.id,
                "file_count": len(file_paths),
            }

    except Exception as e:
        logger.error(f"analyze_and_update_graph failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)
