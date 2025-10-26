"""
ImpactAnalyzer Unit Tests

ImpactAnalyzerクラスの機能をテストします。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.graph_analyzer.analyzers.impact_analyzer import (
    ImpactAnalyzer,
    ImpactResult,
    RiskLevel,
)
from src.graph_analyzer.graph.neo4j_client import Neo4jClient


@pytest.fixture
def mock_neo4j_client():
    """モックNeo4jクライアント"""
    with patch("src.graph_analyzer.graph.neo4j_client.GraphDatabase.driver"):
        client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
        client.execute_query = Mock()
        return client


@pytest.fixture
def impact_analyzer(mock_neo4j_client):
    """ImpactAnalyzerのフィクスチャ"""
    return ImpactAnalyzer(mock_neo4j_client)


def test_impact_analyzer_initialization(impact_analyzer):
    """ImpactAnalyzer初期化のテスト"""
    assert impact_analyzer is not None
    assert impact_analyzer.client is not None
    assert impact_analyzer.queries is not None


def test_analyze_table_change_impact(impact_analyzer, mock_neo4j_client):
    """テーブル変更影響分析のテスト"""
    # モックデータ
    files_data = [
        {
            "file_path": "/src/UserDAO.java",
            "class_name": "UserDAO",
            "method_name": "findByEmail",
            "query_count": 2,
        },
        {
            "file_path": "/src/UserService.java",
            "class_name": "UserService",
            "method_name": "getUser",
            "query_count": 1,
        },
    ]

    access_patterns = [
        {"query_type": "SELECT", "count": 5},
        {"query_type": "INSERT", "count": 2},
    ]

    issues_data = [
        {"issue_type": "ALLOW_FILTERING", "severity": "high", "issue_count": 1}
    ]

    # モックの戻り値を設定
    mock_neo4j_client.execute_query.side_effect = [
        files_data,
        access_patterns,
        issues_data,
    ]

    # テーブル変更影響分析を実行
    result = impact_analyzer.analyze_table_change_impact("users")

    # 結果の検証
    assert result.target == "users"
    assert result.impact_type == "table_change"
    assert len(result.affected_files) == 2
    assert "/src/UserDAO.java" in result.affected_files
    assert len(result.affected_classes) == 2
    assert "UserDAO" in result.affected_classes
    assert result.risk_level == RiskLevel.LOW  # 2 files = LOW
    assert 0.0 <= result.risk_score <= 1.0


def test_analyze_file_change_impact_non_recursive(impact_analyzer, mock_neo4j_client):
    """ファイル変更影響分析（非再帰）のテスト"""
    dependencies = [
        {"dependent_file": "/src/OrderDAO.java"},
        {"dependent_file": "/src/ProductDAO.java"},
    ]

    mock_neo4j_client.execute_query.return_value = dependencies

    result = impact_analyzer.analyze_file_change_impact("/src/UserDAO.java", recursive=False)

    assert result.target == "/src/UserDAO.java"
    assert result.impact_type == "file_change"
    assert len(result.affected_files) == 2
    assert result.risk_level == RiskLevel.LOW


def test_analyze_file_change_impact_recursive(impact_analyzer, mock_neo4j_client):
    """ファイル変更影響分析（再帰）のテスト"""
    dependencies = [
        {"dependent_file": "/src/OrderDAO.java", "depth": 1},
        {"dependent_file": "/src/ProductDAO.java", "depth": 1},
        {"dependent_file": "/src/ReportService.java", "depth": 2},
    ]

    mock_neo4j_client.execute_query.return_value = dependencies

    result = impact_analyzer.analyze_file_change_impact("/src/UserDAO.java", recursive=True)

    assert len(result.affected_files) == 3
    assert result.details["dependencies"][0]["depth"] == 1


def test_analyze_class_dependencies(impact_analyzer, mock_neo4j_client):
    """クラス依存関係分析のテスト"""
    tables_data = [
        {"table_name": "users", "query_count": 5},
        {"table_name": "orders", "query_count": 3},
    ]

    mock_neo4j_client.execute_query.return_value = tables_data

    result = impact_analyzer.analyze_class_dependencies("UserDAO")

    assert result.target == "UserDAO"
    assert result.impact_type == "class_dependencies"
    assert len(result.details["tables_used"]) == 2
    assert result.details["tables_used"][0]["table"] == "users"


def test_get_high_risk_files(impact_analyzer, mock_neo4j_client):
    """高リスクファイル取得のテスト"""
    high_risk_data = [
        {
            "file_path": "/src/UserDAO.java",
            "issue_count": 10,
            "severities": ["critical", "high"],
        },
        {
            "file_path": "/src/OrderDAO.java",
            "issue_count": 5,
            "severities": ["high"],
        },
    ]

    mock_neo4j_client.execute_query.return_value = high_risk_data

    results = impact_analyzer.get_high_risk_files(severities=["critical", "high"], limit=10)

    assert len(results) == 2
    assert results[0]["file_path"] == "/src/UserDAO.java"
    assert results[0]["issue_count"] == 10


def test_trace_dependency_chain_found(impact_analyzer, mock_neo4j_client):
    """依存関係チェーン追跡（成功）のテスト"""
    chain_data = [
        {
            "dependency_chain": [
                "/src/UserDAO.java",
                "/src/UserService.java",
                "/src/UserController.java",
            ]
        }
    ]

    mock_neo4j_client.execute_query.return_value = chain_data

    chain = impact_analyzer.trace_dependency_chain(
        "/src/UserDAO.java", "/src/UserController.java"
    )

    assert chain is not None
    assert len(chain) == 3
    assert chain[0] == "/src/UserDAO.java"
    assert chain[-1] == "/src/UserController.java"


def test_trace_dependency_chain_not_found(impact_analyzer, mock_neo4j_client):
    """依存関係チェーン追跡（見つからない）のテスト"""
    mock_neo4j_client.execute_query.return_value = []

    chain = impact_analyzer.trace_dependency_chain(
        "/src/UserDAO.java", "/src/UnrelatedService.java"
    )

    assert chain is None


def test_calculate_risk_critical(impact_analyzer):
    """リスク計算（CRITICAL）のテスト"""
    risk_level, risk_score = impact_analyzer._calculate_risk(
        affected_files=55, affected_classes=10, affected_methods=20
    )

    assert risk_level == RiskLevel.CRITICAL
    assert 0.0 <= risk_score <= 1.0


def test_calculate_risk_high(impact_analyzer):
    """リスク計算（HIGH）のテスト"""
    risk_level, risk_score = impact_analyzer._calculate_risk(
        affected_files=25, affected_classes=5, affected_methods=10
    )

    assert risk_level == RiskLevel.HIGH


def test_calculate_risk_medium(impact_analyzer):
    """リスク計算（MEDIUM）のテスト"""
    risk_level, risk_score = impact_analyzer._calculate_risk(
        affected_files=10, affected_classes=3, affected_methods=5
    )

    assert risk_level == RiskLevel.MEDIUM


def test_calculate_risk_low(impact_analyzer):
    """リスク計算（LOW）のテスト"""
    risk_level, risk_score = impact_analyzer._calculate_risk(
        affected_files=2, affected_classes=1, affected_methods=1
    )

    assert risk_level == RiskLevel.LOW


def test_calculate_risk_minimal(impact_analyzer):
    """リスク計算（MINIMAL）のテスト"""
    risk_level, risk_score = impact_analyzer._calculate_risk(
        affected_files=0, affected_classes=0, affected_methods=0
    )

    assert risk_level == RiskLevel.MINIMAL
    assert risk_score == 0.0


def test_impact_result_to_dict():
    """ImpactResult.to_dict()のテスト"""
    result = ImpactResult(
        target="users",
        impact_type="table_change",
        affected_files=["/src/UserDAO.java", "/src/OrderDAO.java"],
        affected_classes=["UserDAO", "OrderDAO"],
        affected_methods=["findByEmail", "getUser"],
        risk_level=RiskLevel.LOW,
        risk_score=0.25,
        details={"test": "data"},
    )

    dict_result = result.to_dict()

    assert dict_result["target"] == "users"
    assert dict_result["impact_type"] == "table_change"
    assert dict_result["affected_files_count"] == 2
    assert dict_result["risk_level"] == "low"
    assert dict_result["risk_score"] == 0.25
    assert dict_result["details"]["test"] == "data"


def test_multiple_table_analysis(impact_analyzer, mock_neo4j_client):
    """複数テーブルの影響分析テスト"""
    # 1つ目のテーブル
    mock_neo4j_client.execute_query.side_effect = [
        [{"file_path": "/src/UserDAO.java", "class_name": "UserDAO", "method_name": "find", "query_count": 1}],
        [{"query_type": "SELECT", "count": 1}],
        [],
    ]
    result1 = impact_analyzer.analyze_table_change_impact("users")

    # 2つ目のテーブル
    mock_neo4j_client.execute_query.side_effect = [
        [{"file_path": "/src/OrderDAO.java", "class_name": "OrderDAO", "method_name": "find", "query_count": 1}],
        [{"query_type": "SELECT", "count": 1}],
        [],
    ]
    result2 = impact_analyzer.analyze_table_change_impact("orders")

    assert result1.target == "users"
    assert result2.target == "orders"
    assert result1.affected_files != result2.affected_files


def test_empty_dependencies(impact_analyzer, mock_neo4j_client):
    """依存関係なしのテスト"""
    mock_neo4j_client.execute_query.return_value = []

    result = impact_analyzer.analyze_file_change_impact("/src/StandaloneUtil.java")

    assert len(result.affected_files) == 0
    assert result.risk_level == RiskLevel.MINIMAL


def test_large_scale_impact(impact_analyzer, mock_neo4j_client):
    """大規模影響のテスト"""
    # 60ファイルに影響
    large_dependencies = [
        {"dependent_file": f"/src/File{i}.java", "depth": 1}
        for i in range(60)
    ]

    mock_neo4j_client.execute_query.return_value = large_dependencies

    result = impact_analyzer.analyze_file_change_impact("/src/CoreUtil.java")

    assert len(result.affected_files) == 60
    assert result.risk_level == RiskLevel.CRITICAL
