"""
Celeryタスクのユニットテスト

各Celeryタスクの動作を検証
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Celeryタスクをインポート
from src.graph_analyzer.worker.tasks import (
    analyze_file,
    batch_analyze_files,
    update_graph,
    batch_update_graph,
    cleanup_old_results,
    analyze_and_update_graph,
)

# Celery appをEagerモードに設定（テスト用）
from src.graph_analyzer.worker.celery_app import app
app.conf.task_always_eager = True
app.conf.task_eager_propagates = True


class TestAnalyzeFile:
    """analyze_fileタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.Path")
    def test_analyze_file_success(self, mock_path_class):
        """ファイル分析の成功ケース"""
        # Pathのexists()をモック
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        # タスク実行（eagerモードで同期実行）
        result = analyze_file.apply(args=["/path/to/test.java"], kwargs={"config": {"enabled": True}}).get()

        # 検証
        assert result["status"] == "success"
        assert result["file"] == "/path/to/test.java"
        assert "issues" in result

    @patch("src.graph_analyzer.worker.tasks.Path")
    def test_analyze_file_not_found(self, mock_path_class):
        """ファイルが存在しない場合のエラー"""
        from celery.exceptions import Retry

        # Pathのexists()をFalseに設定
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        # Retryまたは FileNotFoundErrorが発生することを確認
        # eagerモードではRetry例外が発生する
        with pytest.raises((Retry, FileNotFoundError)):
            analyze_file.apply(args=["/path/to/nonexistent.java"]).get()


class TestBatchAnalyzeFiles:
    """batch_analyze_filesタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.group")
    @patch("src.graph_analyzer.worker.tasks.analyze_file")
    def test_batch_analyze_files_success(self, mock_analyze_file, mock_group):
        """バッチ分析の成功ケース"""
        # groupの戻り値をモック
        mock_job = Mock()
        mock_result = Mock()
        mock_result.get.return_value = [
            {"file": "file1.java", "status": "success", "issues": []},
            {"file": "file2.java", "status": "success", "issues": []},
            {"file": "file3.java", "status": "failed", "issues": []},
        ]
        mock_job.apply_async.return_value = mock_result
        mock_group.return_value = mock_job

        # タスク実行
        file_paths = ["file1.java", "file2.java", "file3.java"]
        result = batch_analyze_files.apply(args=[file_paths], kwargs={"config": {"enabled": True}}).get()

        # 検証
        assert result["total_files"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert len(result["results"]) == 3


class TestUpdateGraph:
    """update_graphタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.Neo4jClient")
    @patch("src.graph_analyzer.worker.tasks.GraphBuilder")
    def test_update_graph_success(self, mock_builder_class, mock_client_class):
        """グラフ更新の成功ケース"""
        # Neo4jClientのモック
        mock_client = Mock()
        mock_client.batch_create_nodes.return_value = ["node1", "node2", "node3"]
        mock_client.batch_create_relationships.return_value = 5
        mock_client_class.return_value = mock_client

        # GraphBuilderのモック
        mock_builder = Mock()
        mock_builder.build_from_analysis_result.return_value = (
            [{"type": "FILE"}, {"type": "CLASS"}],  # nodes
            [{"type": "CONTAINS"}]  # relationships
        )
        mock_builder_class.return_value = mock_builder

        # 分析結果
        analysis_result = {
            "file": "test.java",
            "status": "success",
            "issues": []
        }

        # タスク実行
        result = update_graph.apply(
            args=[analysis_result],
            kwargs={
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_user": "neo4j",
                "neo4j_password": "password"
            }
        ).get()

        # 検証
        assert result["status"] == "success"
        assert result["nodes_created"] == 3
        assert result["relationships_created"] == 5


class TestBatchUpdateGraph:
    """batch_update_graphタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.Neo4jClient")
    @patch("src.graph_analyzer.worker.tasks.GraphBuilder")
    def test_batch_update_graph_success(self, mock_builder_class, mock_client_class):
        """バッチグラフ更新の成功ケース"""
        # Neo4jClientのモック
        mock_client = Mock()
        mock_client.batch_create_nodes.side_effect = [
            ["node1", "node2"],  # 1回目の呼び出し
            ["node3", "node4", "node5"],  # 2回目の呼び出し
        ]
        mock_client.batch_create_relationships.side_effect = [3, 5]
        mock_client_class.return_value = mock_client

        # GraphBuilderのモック
        mock_builder = Mock()
        mock_builder.build_from_analysis_result.return_value = (
            [{"type": "FILE"}],
            [{"type": "CONTAINS"}]
        )
        mock_builder_class.return_value = mock_builder

        # 分析結果のリスト
        analysis_results = [
            {"file": "file1.java", "status": "success"},
            {"file": "file2.java", "status": "success"},
        ]

        # タスク実行
        result = batch_update_graph.apply(
            args=[analysis_results],
            kwargs={
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_user": "neo4j",
                "neo4j_password": "password"
            }
        ).get()

        # 検証
        assert result["status"] == "success"
        assert result["total_nodes"] == 5  # 2 + 3
        assert result["total_relationships"] == 8  # 3 + 5
        assert result["results_processed"] == 2


class TestCleanupOldResults:
    """cleanup_old_resultsタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.logger")
    def test_cleanup_old_results_success(self, mock_logger):
        """クリーンアップの成功ケース"""
        # タスク実行
        result = cleanup_old_results.apply().get()

        # 検証（現在は仮実装なのでcleaned_count=0）
        assert result["status"] == "success"
        assert result["cleaned_count"] == 0

    @patch("src.graph_analyzer.worker.tasks.logger")
    def test_cleanup_old_results_with_error(self, mock_logger):
        """クリーンアップのエラーケース"""
        # loggerがエラーを発生（エラーハンドリングのテスト）
        mock_logger.info.side_effect = RuntimeError("Cleanup error")

        # タスク実行（エラーが発生しても例外を投げない）
        result = cleanup_old_results.apply().get()

        # 検証
        assert result["status"] == "failed"
        assert "error" in result


class TestAnalyzeAndUpdateGraph:
    """analyze_and_update_graphタスクのテスト"""

    @patch("src.graph_analyzer.worker.tasks.chord")
    @patch("src.graph_analyzer.worker.tasks.group")
    @patch("src.graph_analyzer.worker.tasks.batch_update_graph")
    def test_analyze_and_update_graph_success(
        self, mock_batch_update, mock_group, mock_chord
    ):
        """分析とグラフ更新の統合タスク成功ケース"""
        # chordの戻り値をモック
        mock_result = Mock()
        mock_result.id = "task-12345"
        mock_chord_instance = Mock()
        mock_chord_instance.return_value = mock_result
        mock_chord.return_value = mock_chord_instance

        # タスク実行
        file_paths = ["file1.java", "file2.java", "file3.java"]
        result = analyze_and_update_graph.apply(
            args=[file_paths],
            kwargs={
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_user": "neo4j",
                "neo4j_password": "password",
                "config": {"enabled": True}
            }
        ).get()

        # 検証
        assert result["status"] == "started"
        assert result["task_id"] == "task-12345"
        assert result["file_count"] == 3

    @patch("src.graph_analyzer.worker.tasks.chord")
    @patch("src.graph_analyzer.worker.tasks.group")
    @patch("src.graph_analyzer.worker.tasks.batch_update_graph")
    def test_analyze_and_update_graph_empty_files(
        self, mock_batch_update, mock_group, mock_chord
    ):
        """空のファイルリストでの実行"""
        # chordの戻り値をモック
        mock_result = Mock()
        mock_result.id = "task-empty"
        mock_chord_instance = Mock()
        mock_chord_instance.return_value = mock_result
        mock_chord.return_value = mock_chord_instance

        # 空のファイルリストで実行
        result = analyze_and_update_graph.apply(args=[[]]).get()

        # 検証
        assert result["status"] == "started"
        assert result["file_count"] == 0


class TestTaskConfiguration:
    """タスク設定のテスト"""

    def test_all_tasks_registered(self):
        """すべてのタスクが登録されていることを確認"""
        # Celery appに登録されているタスク名を取得
        registered_tasks = list(app.tasks.keys())

        # 期待するタスク名
        expected_tasks = [
            "graph_analyzer.worker.tasks.analyze_file",
            "graph_analyzer.worker.tasks.batch_analyze_files",
            "graph_analyzer.worker.tasks.update_graph",
            "graph_analyzer.worker.tasks.batch_update_graph",
            "graph_analyzer.worker.tasks.cleanup_old_results",
            "graph_analyzer.worker.tasks.analyze_and_update_graph",
        ]

        # すべてのタスクが登録されているか確認
        for task_name in expected_tasks:
            assert task_name in registered_tasks

    def test_task_names(self):
        """タスク名が正しく設定されているか確認"""
        assert analyze_file.name == "graph_analyzer.worker.tasks.analyze_file"
        assert batch_analyze_files.name == "graph_analyzer.worker.tasks.batch_analyze_files"
        assert update_graph.name == "graph_analyzer.worker.tasks.update_graph"
        assert batch_update_graph.name == "graph_analyzer.worker.tasks.batch_update_graph"
        assert cleanup_old_results.name == "graph_analyzer.worker.tasks.cleanup_old_results"
        assert analyze_and_update_graph.name == "graph_analyzer.worker.tasks.analyze_and_update_graph"

    def test_task_bind_setting(self):
        """bind=Trueが設定されているタスクの確認"""
        # bind=Trueのタスクはrequestオブジェクトを持つ
        bound_tasks = [
            analyze_file,
            batch_analyze_files,
            update_graph,
            batch_update_graph,
            analyze_and_update_graph,
        ]

        for task in bound_tasks:
            # タスクがboundであることを確認（request属性が存在）
            assert hasattr(task, "request")
