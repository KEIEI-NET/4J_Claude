"""Neo4jClient Unit Tests"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.graph_analyzer.graph.neo4j_client import Neo4jClient
from src.graph_analyzer.models.schema import FileNode, NodeType


@pytest.fixture
def mock_driver():
    """モックNeo4jドライバー"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock:
        yield mock


def test_neo4j_client_initialization(mock_driver):
    """クライアント初期化のテスト"""
    client = Neo4jClient(
        uri="bolt://localhost:7687", user="neo4j", password="password"
    )

    assert client.uri == "bolt://localhost:7687"
    assert client.user == "neo4j"
    mock_driver.assert_called_once()


def test_verify_connectivity(mock_driver):
    """接続確認のテスト"""
    mock_session = Mock()
    mock_result = Mock()
    mock_result.single.return_value = {"num": 1}
    mock_session.run.return_value = mock_result

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    assert client.verify_connectivity() is True


def test_verify_connectivity_failure(mock_driver):
    """接続確認失敗のテスト"""
    mock_session = Mock()
    mock_session.run.side_effect = Exception("Connection failed")

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    assert client.verify_connectivity() is False


def test_context_manager(mock_driver):
    """コンテキストマネージャーのテスト"""
    with Neo4jClient("bolt://localhost:7687", "neo4j", "password") as client:
        assert client is not None

    # closeが呼ばれることを確認
    mock_driver.return_value.close.assert_called_once()


def test_execute_query(mock_driver):
    """クエリ実行のテスト"""
    mock_session = MagicMock()

    # Mockレコードを作成 - dict()で変換可能にする
    class MockRecord:
        def __init__(self, data):
            self._data = data

        def __iter__(self):
            return iter(self._data.items())

        def __getitem__(self, key):
            return self._data[key]

        def keys(self):
            return self._data.keys()

        def values(self):
            return self._data.values()

        def items(self):
            return self._data.items()

    mock_record1 = MockRecord({"name": "test1"})
    mock_record2 = MockRecord({"name": "test2"})

    mock_session.run.return_value = [mock_record1, mock_record2]

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    results = client.execute_query("MATCH (n) RETURN n")

    assert len(results) == 2
    assert results[0]["name"] == "test1"
    assert results[1]["name"] == "test2"
    mock_session.run.assert_called_once()


def test_create_node(mock_driver):
    """ノード作成のテスト"""
    mock_session = Mock()
    mock_result = Mock()
    mock_result.single.return_value = {"node_id": "node-123"}
    mock_session.run.return_value = mock_result

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    file_node = FileNode(
        node_id="test-file",
        path="/test/file.java",
        language="java",
        size_bytes=1024,
    )

    node_id = client.create_node(file_node)
    assert node_id == "node-123"
    mock_session.run.assert_called_once()


def test_batch_create_nodes(mock_driver):
    """バッチノード作成のテスト"""
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

    nodes = [
        FileNode(
            node_id=f"file-{i}",
            path=f"/test/file{i}.java",
            language="java",
            size_bytes=1024,
        )
        for i in range(5)
    ]

    node_ids = client.batch_create_nodes(nodes)
    assert len(node_ids) == 5
    assert all(nid == "node-123" for nid in node_ids)


def test_batch_create_relationships(mock_driver):
    """バッチリレーションシップ作成のテスト"""
    from src.graph_analyzer.models.schema import GraphRelationship, RelationType

    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    relationships = [
        GraphRelationship(
            from_node=f"node-{i}",
            to_node=f"node-{i+1}",
            relation_type=RelationType.CONTAINS,
        )
        for i in range(3)
    ]

    count = client.batch_create_relationships(relationships)
    assert count == 3
    assert mock_tx.run.call_count == 3


def test_with_transaction_success(mock_driver):
    """トランザクション成功のテスト"""
    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    def test_function(tx, value):
        return value * 2

    result = client.with_transaction(test_function, 5)
    assert result == 10
    mock_tx.commit.assert_called_once()


def test_with_transaction_rollback(mock_driver):
    """トランザクションロールバックのテスト"""
    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    def failing_function(tx):
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        client.with_transaction(failing_function)

    mock_tx.rollback.assert_called_once()


def test_batch_size_handling(mock_driver):
    """バッチサイズ処理のテスト"""
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

    # 2500個のノードを作成（バッチサイズ1000）
    nodes = [
        FileNode(
            node_id=f"file-{i}",
            path=f"/test/file{i}.java",
            language="java",
            size_bytes=1024,
        )
        for i in range(2500)
    ]

    node_ids = client.batch_create_nodes(nodes, batch_size=1000)
    assert len(node_ids) == 2500

    # 3回のトランザクションが実行される（1000 + 1000 + 500）
    assert mock_tx.commit.call_count == 3

def test_connection_error_service_unavailable():
    """接続エラー（ServiceUnavailable）のテスト"""
    from neo4j.exceptions import ServiceUnavailable

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        mock_driver.side_effect = ServiceUnavailable("Connection failed")

        with pytest.raises(ServiceUnavailable):
            Neo4jClient("bolt://localhost:7687", "neo4j", "password")


def test_connection_error_auth_error():
    """接続エラー（AuthError）のテスト"""
    from neo4j.exceptions import AuthError

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        mock_driver.side_effect = AuthError("Auth failed")

        with pytest.raises(AuthError):
            Neo4jClient("bolt://localhost:7687", "neo4j", "wrong_password")


def test_initialize_schema(mock_driver):
    """スキーマ初期化のテスト"""
    mock_session = MagicMock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    client.initialize_schema()

    # 制約とインデックス作成のクエリが実行されることを確認
    assert mock_session.run.call_count > 0


def test_clear_all(mock_driver):
    """全データ削除のテスト"""
    mock_session = MagicMock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    client.clear_all()

    # DELETEクエリが実行されることを確認
    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args[0][0]
    assert "DELETE" in call_args or "DETACH DELETE" in call_args

def test_verify_connectivity_no_driver():
    """Driver未初期化時の接続確認テスト"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに
        assert client.verify_connectivity() is False


def test_initialize_schema_no_driver():
    """Driver未初期化時のスキーマ初期化テスト"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.initialize_schema()


def test_initialize_schema_with_error(mock_driver):
    """スキーマ初期化でエラーが発生するテスト"""
    mock_session = MagicMock()
    # スキーマステートメント実行時にエラーを発生させる
    mock_session.run.side_effect = Exception("Constraint already exists")

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    # エラーが発生してもスキーマ初期化は完了する（警告ログのみ）
    client.initialize_schema()  # 例外は発生しない


def test_create_relationship(mock_driver):
    """単一リレーションシップ作成のテスト"""
    from src.graph_analyzer.models.schema import GraphRelationship, RelationType

    mock_session = MagicMock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    relationship = GraphRelationship(
        from_node="node-1",
        to_node="node-2",
        relation_type=RelationType.CONTAINS,
        properties={"created_at": "2025-01-27"},
    )

    client.create_relationship(relationship)
    mock_session.run.assert_called_once()


def test_execute_query_no_driver():
    """Driver未初期化時のクエリ実行テスト"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.execute_query("MATCH (n) RETURN n")


def test_create_node_no_driver():
    """Driver未初期化時のノード作成テスト"""
    from src.graph_analyzer.models.schema import FileNode

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        file_node = FileNode(
            node_id="test-file",
            path="/test/file.java",
            language="java",
            size_bytes=1024,
        )

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.create_node(file_node)


def test_create_relationship_no_driver():
    """Driver未初期化時のリレーションシップ作成テスト"""
    from src.graph_analyzer.models.schema import GraphRelationship, RelationType

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        relationship = GraphRelationship(
            from_node="node-1",
            to_node="node-2",
            relation_type=RelationType.CONTAINS,
            properties={},
        )

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.create_relationship(relationship)

def test_batch_create_nodes_no_driver():
    """Driver未初期化時のバッチノード作成テスト"""
    from src.graph_analyzer.models.schema import FileNode

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        nodes = [
            FileNode(
                node_id=f"file-{i}",
                path=f"/test/file{i}.java",
                language="java",
                size_bytes=1024,
            )
            for i in range(3)
        ]

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.batch_create_nodes(nodes)


def test_batch_create_relationships_no_driver():
    """Driver未初期化時のバッチリレーションシップ作成テスト"""
    from src.graph_analyzer.models.schema import GraphRelationship, RelationType

    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        relationships = [
            GraphRelationship(
                from_node="node-1",
                to_node="node-2",
                relation_type=RelationType.CONTAINS,
                properties={},
            )
        ]

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.batch_create_relationships(relationships)


def test_with_transaction_no_driver():
    """Driver未初期化時のトランザクション実行テスト"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        def dummy_func(tx):
            return "result"

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.with_transaction(dummy_func)


def test_clear_all_no_driver():
    """Driver未初期化時の全データ削除テスト"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock_driver:
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client._driver = None  # Driverを強制的にNoneに

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            client.clear_all()


def test_create_node_failure(mock_driver):
    """ノード作成失敗のテスト（recordがNoneの場合）"""
    from src.graph_analyzer.models.schema import FileNode

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.single.return_value = None  # レコードがNone

    mock_session.run.return_value = mock_result

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    file_node = FileNode(
        node_id="test-file",
        path="/test/file.java",
        language="java",
        size_bytes=1024,
    )

    with pytest.raises(RuntimeError, match="Failed to create node"):
        client.create_node(file_node)
