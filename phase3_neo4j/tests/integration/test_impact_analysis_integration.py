"""
Impact Analysis Integration Tests

ImpactAnalyzerとNeo4jClientの統合テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.graph_analyzer.graph.neo4j_client import Neo4jClient
from src.graph_analyzer.graph.graph_builder import GraphBuilder
from src.graph_analyzer.analyzers.impact_analyzer import ImpactAnalyzer, RiskLevel


@pytest.fixture
def mock_driver():
    """モックNeo4jドライバー"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver") as mock:
        yield mock


@pytest.fixture
def sample_graph_data():
    """サンプルグラフデータ"""
    return {
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
                "message": "ALLOW FILTERING detected",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Use partition key",
                "evidence": [],
                "confidence": 1.0,
            },
            {
                "detector": "PartitionKeyDetector",
                "type": "NO_PARTITION_KEY",
                "severity": "medium",
                "file": "/src/OrderDAO.java",
                "line": 55,
                "message": "No partition key",
                "cql": "SELECT * FROM orders WHERE status = ?",
                "recommendation": "Add partition key",
                "evidence": [],
                "confidence": 0.9,
            },
        ],
    }


def test_full_impact_analysis_workflow(mock_driver, sample_graph_data):
    """完全な影響分析ワークフローのテスト"""
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

    # 1. Neo4jClientを初期化
    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    # 2. GraphBuilderでグラフを構築
    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(sample_graph_data)

    # 3. グラフをNeo4jにインポート
    node_ids = client.batch_create_nodes(nodes)
    rel_count = client.batch_create_relationships(relationships)

    assert len(node_ids) > 0
    assert rel_count > 0

    # 4. ImpactAnalyzerで影響分析
    analyzer = ImpactAnalyzer(client)

    # テーブル変更の影響分析をモック
    client.execute_query = Mock()
    client.execute_query.side_effect = [
        [
            {
                "file_path": "/src/UserDAO.java",
                "class_name": "UserDAO",
                "method_name": "findByEmail",
                "query_count": 1,
            }
        ],
        [{"query_type": "SELECT", "count": 1}],
        [{"issue_type": "ALLOW_FILTERING", "severity": "high", "issue_count": 1}],
    ]

    result = analyzer.analyze_table_change_impact("users")

    assert result.target == "users"
    assert len(result.affected_files) > 0


def test_graph_to_impact_analysis_pipeline(mock_driver, sample_graph_data):
    """グラフ構築→影響分析のパイプラインテスト"""
    mock_session = MagicMock()
    mock_tx = MagicMock()

    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx

    # Neo4jクライアント
    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    # グラフ構築
    builder = GraphBuilder()
    nodes, relationships = builder.build_from_analysis_result(sample_graph_data)

    # 影響分析準備
    analyzer = ImpactAnalyzer(client)

    # テーブル"users"の影響分析
    client.execute_query = Mock()
    client.execute_query.side_effect = [
        [
            {
                "file_path": "/src/UserDAO.java",
                "class_name": "UserDAO",
                "method_name": "findByEmail",
                "query_count": 1,
            }
        ],
        [{"query_type": "SELECT", "count": 1}],
        [],
    ]

    table_impact = analyzer.analyze_table_change_impact("users")

    # ファイルの影響分析
    client.execute_query.side_effect = [[{"dependent_file": "/src/UserService.java", "depth": 1}]]

    file_impact = analyzer.analyze_file_change_impact("/src/UserDAO.java")

    assert table_impact.target == "users"
    assert file_impact.target == "/src/UserDAO.java"


def test_multi_table_impact_analysis(mock_driver):
    """複数テーブルの影響分析テスト"""
    mock_session = MagicMock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    analyzer = ImpactAnalyzer(client)

    client.execute_query = Mock()

    # "users"テーブルの影響
    client.execute_query.side_effect = [
        [{"file_path": f"/src/UserDAO.java", "class_name": "UserDAO", "method_name": "find", "query_count": 3}],
        [{"query_type": "SELECT", "count": 3}],
        [],
    ]
    users_impact = analyzer.analyze_table_change_impact("users")

    # "orders"テーブルの影響
    client.execute_query.side_effect = [
        [{"file_path": f"/src/OrderDAO.java", "class_name": "OrderDAO", "method_name": "find", "query_count": 5}],
        [{"query_type": "SELECT", "count": 5}],
        [],
    ]
    orders_impact = analyzer.analyze_table_change_impact("orders")

    assert users_impact.affected_files != orders_impact.affected_files


def test_high_risk_detection(mock_driver):
    """高リスク検出テスト"""
    mock_session = MagicMock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    analyzer = ImpactAnalyzer(client)

    client.execute_query = Mock()
    client.execute_query.return_value = [
        {
            "file_path": "/src/CriticalDAO.java",
            "issue_count": 15,
            "severities": ["critical", "high"],
        }
    ]

    high_risk_files = analyzer.get_high_risk_files()

    assert len(high_risk_files) > 0
    assert high_risk_files[0]["issue_count"] == 15


def test_dependency_chain_tracing(mock_driver):
    """依存関係チェーン追跡テスト"""
    mock_session = Mock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    analyzer = ImpactAnalyzer(client)

    client.execute_query = Mock()
    client.execute_query.return_value = [
        {
            "dependency_chain": [
                "/src/UserDAO.java",
                "/src/UserService.java",
                "/src/UserController.java",
            ]
        }
    ]

    chain = analyzer.trace_dependency_chain("/src/UserDAO.java", "/src/UserController.java")

    assert chain is not None
    assert len(chain) == 3
    assert chain[0] == "/src/UserDAO.java"
    assert chain[-1] == "/src/UserController.java"


def test_class_table_dependencies(mock_driver):
    """クラスとテーブルの依存関係テスト"""
    mock_session = Mock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    analyzer = ImpactAnalyzer(client)

    client.execute_query = Mock()
    client.execute_query.return_value = [
        {"table_name": "users", "query_count": 5},
        {"table_name": "sessions", "query_count": 2},
    ]

    result = analyzer.analyze_class_dependencies("UserDAO")

    assert result.target == "UserDAO"
    assert len(result.details["tables_used"]) == 2


def test_risk_level_calculation_scenarios(mock_driver):
    """各リスクレベルのシナリオテスト"""
    mock_session = Mock()
    mock_driver_instance = MagicMock()
    mock_driver.return_value = mock_driver_instance
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session

    client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    analyzer = ImpactAnalyzer(client)

    client.execute_query = Mock()

    # CRITICAL: 55ファイル影響
    client.execute_query.return_value = [
        {"dependent_file": f"/src/File{i}.java", "depth": 1} for i in range(55)
    ]
    critical_result = analyzer.analyze_file_change_impact("/src/CoreUtil.java")
    assert critical_result.risk_level == RiskLevel.CRITICAL

    # HIGH: 25ファイル影響
    client.execute_query.return_value = [
        {"dependent_file": f"/src/File{i}.java", "depth": 1} for i in range(25)
    ]
    high_result = analyzer.analyze_file_change_impact("/src/ImportantUtil.java")
    assert high_result.risk_level == RiskLevel.HIGH

    # MEDIUM: 10ファイル影響
    client.execute_query.return_value = [
        {"dependent_file": f"/src/File{i}.java", "depth": 1} for i in range(10)
    ]
    medium_result = analyzer.analyze_file_change_impact("/src/CommonUtil.java")
    assert medium_result.risk_level == RiskLevel.MEDIUM

    # LOW: 3ファイル影響
    client.execute_query.return_value = [
        {"dependent_file": f"/src/File{i}.java", "depth": 1} for i in range(3)
    ]
    low_result = analyzer.analyze_file_change_impact("/src/MinorUtil.java")
    assert low_result.risk_level == RiskLevel.LOW


def test_impact_result_serialization():
    """ImpactResult辞書変換テスト"""
    analyzer = ImpactAnalyzer(None)  # クライアント不要

    # リスク計算のみテスト
    risk_level, risk_score = analyzer._calculate_risk(10, 5, 3)

    from src.graph_analyzer.analyzers.impact_analyzer import ImpactResult

    result = ImpactResult(
        target="test_table",
        impact_type="table_change",
        affected_files=["/src/A.java", "/src/B.java"],
        affected_classes=["ClassA", "ClassB"],
        affected_methods=["methodA", "methodB"],
        risk_level=risk_level,
        risk_score=risk_score,
        details={"key": "value"},
    )

    dict_result = result.to_dict()

    assert dict_result["target"] == "test_table"
    assert dict_result["affected_files_count"] == 2
    assert "risk_level" in dict_result
    assert "risk_score" in dict_result
