"""
Graph Integration Tests

Neo4jClientとGraphBuilderの統合テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.graph_analyzer.graph.neo4j_client import Neo4jClient
from src.graph_analyzer.graph.graph_builder import GraphBuilder
from src.graph_analyzer.models.schema import NodeType, RelationType


@pytest.fixture
def mock_driver():
    """モックNeo4jドライバー"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock:
        yield mock


@pytest.fixture
def sample_analysis_result():
    """サンプル分析結果"""
    return {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 1,
        "issues_by_severity": {"high": 1},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,
                "message": "ALLOW FILTERING detected",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Use partition key",
                "evidence": ["ALLOW FILTERING found"],
                "confidence": 1.0,
            }
        ],
    }


def test_full_graph_creation_workflow(mock_driver, sample_analysis_result):
    """完全なグラフ作成ワークフローのテスト"""
    # モックセットアップ
    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_result = Mock()
    mock_result.single.return_value = {"node_id": "node-123"}
    mock_tx.run.return_value = mock_result

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    # Neo4jClientを初期化
    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    # GraphBuilderで分析結果をグラフに変換
    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(sample_analysis_result)

    # ノードとリレーションシップが作成されていることを確認
    assert len(nodes) > 0
    assert len(relationships) > 0

    # Neo4jにバッチインポート
    node_ids = client.batch_create_nodes(nodes)
    assert len(node_ids) == len(nodes)

    rel_count = client.batch_create_relationships(relationships)
    assert rel_count == len(relationships)


def test_graph_structure_integrity(sample_analysis_result):
    """グラフ構造の整合性テスト"""
    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(sample_analysis_result)

    # 全てのリレーションシップのfrom_nodeとto_nodeがノードIDマップに存在することを確認
    node_keys = {node.node_id for node in nodes}

    for rel in relationships:
        assert (
            rel.from_node in node_keys or rel.from_node in builder._node_id_map
        ), f"Missing from_node: {rel.from_node}"
        assert (
            rel.to_node in node_keys or rel.to_node in builder._node_id_map
        ), f"Missing to_node: {rel.to_node}"


def test_graph_hierarchy(sample_analysis_result):
    """グラフ階層構造のテスト（File -> Class -> Method -> Query -> Table）"""
    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(sample_analysis_result)

    # ノードタイプのカウント
    node_type_counts = {}
    for node in nodes:
        node_type_counts[node.node_type] = node_type_counts.get(node.node_type, 0) + 1

    # 各レベルにノードが存在することを確認
    assert node_type_counts.get(NodeType.FILE, 0) >= 1
    assert node_type_counts.get(NodeType.CLASS, 0) >= 1
    assert node_type_counts.get(NodeType.METHOD, 0) >= 1
    assert node_type_counts.get(NodeType.QUERY, 0) >= 1
    assert node_type_counts.get(NodeType.TABLE, 0) >= 1
    assert node_type_counts.get(NodeType.ISSUE, 0) >= 1

    # リレーションシップタイプのカウント
    rel_type_counts = {}
    for rel in relationships:
        rel_type_counts[rel.relation_type] = rel_type_counts.get(rel.relation_type, 0) + 1

    # 各リレーションシップタイプが存在することを確認
    assert rel_type_counts.get(RelationType.CONTAINS, 0) >= 1  # File -> Class
    assert rel_type_counts.get(RelationType.DEFINES, 0) >= 1  # Class -> Method
    assert rel_type_counts.get(RelationType.EXECUTES, 0) >= 1  # Method -> Query
    assert rel_type_counts.get(RelationType.ACCESSES, 0) >= 1  # Query -> Table
    assert rel_type_counts.get(RelationType.HAS_ISSUE, 0) >= 1  # Query -> Issue


def test_multiple_files_graph(mock_driver):
    """複数ファイルのグラフ構築テスト"""
    multi_file_result = {
        "analyzed_files": ["/src/UserDAO.java", "/src/OrderDAO.java"],
        "total_issues": 2,
        "issues_by_severity": {"high": 1, "medium": 1},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,
                "message": "Issue 1",
                "cql": "SELECT * FROM users WHERE email = ?",
                "recommendation": "Fix 1",
                "evidence": [],
                "confidence": 1.0,
            },
            {
                "detector": "PartitionKeyDetector",
                "type": "NO_PARTITION_KEY",
                "severity": "medium",
                "file": "/src/OrderDAO.java",
                "line": 55,
                "message": "Issue 2",
                "cql": "SELECT * FROM orders WHERE status = ?",
                "recommendation": "Fix 2",
                "evidence": [],
                "confidence": 0.9,
            },
        ],
    }

    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(multi_file_result)

    # 2つのファイルノードが作成される
    file_nodes = [n for n in nodes if n.node_type == NodeType.FILE]
    assert len(file_nodes) == 2

    # 2つの問題ノードが作成される
    issue_nodes = [n for n in nodes if n.node_type == NodeType.ISSUE]
    assert len(issue_nodes) == 2


def test_transaction_atomicity(mock_driver):
    """トランザクションの原子性テスト"""
    mock_session = MagicMock()
    mock_tx = MagicMock()

    # 1回目の呼び出しは成功、2回目は失敗
    mock_tx.run.side_effect = [Mock(single=lambda: {"node_id": "node-1"}), Exception("DB Error")]

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    def create_multiple_nodes(tx):
        tx.run("CREATE (:Node1)")
        tx.run("CREATE (:Node2)")  # これが失敗する

    # トランザクションがロールバックされる
    with pytest.raises(Exception):
        client.with_transaction(create_multiple_nodes)

    mock_tx.rollback.assert_called_once()


def test_large_batch_performance(mock_driver):
    """大量データのバッチ処理テスト"""
    from src.graph_analyzer.models.schema import FileNode

    mock_session = MagicMock()
    mock_tx = MagicMock()
    mock_result = Mock()
    mock_result.single.return_value = {"node_id": "node-123"}
    mock_tx.run.return_value = mock_result

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    # 10,000ノードを作成
    nodes = [
        FileNode(
            node_id=f"file-{i}",
            path=f"/src/File{i}.java",
            language="java",
            size_bytes=1024,
        )
        for i in range(10000)
    ]

    # バッチサイズ1000で処理
    node_ids = client.batch_create_nodes(nodes, batch_size=1000)
    assert len(node_ids) == 10000

    # 10回のバッチトランザクションが実行される
    assert mock_tx.commit.call_count == 10


def test_incremental_graph_update():
    """増分グラフ更新のテスト"""
    initial_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 1,
        "issues_by_severity": {"high": 1},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,
                "message": "Issue 1",
                "cql": "SELECT * FROM users WHERE id = ?",
                "recommendation": "Fix 1",
                "evidence": [],
                "confidence": 1.0,
            }
        ],
    }

    # 1回目の構築
    builder1 = GraphBuilder()
    nodes1, rels1 = builder1.build_from_analysis_result(initial_result)
    initial_node_count = len(nodes1)

    # 新しいファイルを追加
    updated_result = {
        "analyzed_files": ["/src/UserDAO.java", "/src/OrderDAO.java"],
        "total_issues": 2,
        "issues_by_severity": {"high": 1, "medium": 1},
        "issues": initial_result["issues"]
        + [
            {
                "detector": "PartitionKeyDetector",
                "type": "NO_PARTITION_KEY",
                "severity": "medium",
                "file": "/src/OrderDAO.java",
                "line": 55,
                "message": "Issue 2",
                "cql": "SELECT * FROM orders WHERE status = ?",
                "recommendation": "Fix 2",
                "evidence": [],
                "confidence": 0.9,
            }
        ],
    }

    # 2回目の構築（増分）
    builder2 = GraphBuilder()
    nodes2, rels2 = builder2.build_from_analysis_result(updated_result)

    # 新しいノードが追加されている
    assert len(nodes2) > initial_node_count
