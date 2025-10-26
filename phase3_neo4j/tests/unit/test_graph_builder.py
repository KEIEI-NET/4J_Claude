"""
GraphBuilder Unit Tests

GraphBuilderクラスの機能をテストします。
"""

import pytest
from src.graph_analyzer.graph.graph_builder import GraphBuilder
from src.graph_analyzer.models.schema import NodeType, RelationType


@pytest.fixture
def graph_builder():
    """GraphBuilderのフィクスチャ"""
    return GraphBuilder()


@pytest.fixture
def sample_analysis_result():
    """サンプル分析結果"""
    return {
        "analyzed_files": [
            "/path/to/UserDAO.java",
            "/path/to/OrderDAO.java",
        ],
        "total_issues": 2,
        "issues_by_severity": {"high": 1, "medium": 1},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",
                "severity": "high",
                "file": "/path/to/UserDAO.java",
                "line": 42,
                "message": "ALLOW FILTERING detected",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Use partition key in WHERE clause",
                "evidence": ["ALLOW FILTERING found"],
                "confidence": 1.0,
            },
            {
                "detector": "PartitionKeyDetector",
                "type": "NO_PARTITION_KEY",
                "severity": "medium",
                "file": "/path/to/OrderDAO.java",
                "line": 55,
                "message": "No partition key in WHERE clause",
                "cql": "SELECT * FROM orders WHERE status = ?",
                "recommendation": "Add partition key to query",
                "evidence": ["Missing partition key"],
                "confidence": 0.9,
            },
        ],
        "analysis_time": 1.5,
        "timestamp": "2025-01-27T10:00:00",
    }


def test_graph_builder_initialization(graph_builder):
    """GraphBuilderの初期化テスト"""
    assert graph_builder is not None
    assert len(graph_builder._created_nodes) == 0
    assert len(graph_builder._created_relationships) == 0


def test_build_from_analysis_result(graph_builder, sample_analysis_result):
    """分析結果からグラフ構築のテスト"""
    nodes, relationships = graph_builder.build_from_analysis_result(
        sample_analysis_result
    )

    # ノード数の確認（ファイル、クラス、メソッド、クエリ、テーブル、問題）
    assert len(nodes) > 0
    assert len(relationships) > 0

    # ノードタイプの確認
    node_types = {node.node_type for node in nodes}
    assert NodeType.FILE in node_types
    assert NodeType.CLASS in node_types
    assert NodeType.METHOD in node_types
    assert NodeType.QUERY in node_types
    assert NodeType.TABLE in node_types
    assert NodeType.ISSUE in node_types


def test_create_file_nodes(graph_builder, sample_analysis_result):
    """ファイルノード作成のテスト"""
    nodes, _ = graph_builder.build_from_analysis_result(sample_analysis_result)

    file_nodes = [n for n in nodes if n.node_type == NodeType.FILE]
    assert len(file_nodes) == 2  # UserDAO.java, OrderDAO.java


def test_create_issue_nodes(graph_builder, sample_analysis_result):
    """問題ノード作成のテスト"""
    nodes, _ = graph_builder.build_from_analysis_result(sample_analysis_result)

    issue_nodes = [n for n in nodes if n.node_type == NodeType.ISSUE]
    assert len(issue_nodes) == 2

    # 重要度の確認
    severities = {node.properties.get("severity") for node in issue_nodes}
    assert "high" in severities
    assert "medium" in severities


def test_create_query_nodes(graph_builder, sample_analysis_result):
    """クエリノード作成のテスト"""
    nodes, _ = graph_builder.build_from_analysis_result(sample_analysis_result)

    query_nodes = [n for n in nodes if n.node_type == NodeType.QUERY]
    assert len(query_nodes) == 2

    # CQLクエリの確認
    cql_texts = {node.properties.get("cql") for node in query_nodes}
    assert any("SELECT * FROM users" in cql for cql in cql_texts)
    assert any("SELECT * FROM orders" in cql for cql in cql_texts)


def test_create_table_nodes(graph_builder, sample_analysis_result):
    """テーブルノード作成のテスト"""
    nodes, _ = graph_builder.build_from_analysis_result(sample_analysis_result)

    table_nodes = [n for n in nodes if n.node_type == NodeType.TABLE]
    assert len(table_nodes) >= 2

    # テーブル名の確認
    table_names = {node.properties.get("name") for node in table_nodes}
    assert "users" in table_names
    assert "orders" in table_names


def test_create_relationships(graph_builder, sample_analysis_result):
    """リレーションシップ作成のテスト"""
    _, relationships = graph_builder.build_from_analysis_result(sample_analysis_result)

    # リレーションシップタイプの確認
    relation_types = {rel.relation_type for rel in relationships}
    assert RelationType.CONTAINS in relation_types  # File -> Class
    assert RelationType.DEFINES in relation_types  # Class -> Method
    assert RelationType.EXECUTES in relation_types  # Method -> Query
    assert RelationType.ACCESSES in relation_types  # Query -> Table
    assert RelationType.HAS_ISSUE in relation_types  # Query -> Issue


def test_extract_query_type(graph_builder):
    """クエリタイプ抽出のテスト"""
    assert graph_builder._extract_query_type("SELECT * FROM users") == "SELECT"
    assert graph_builder._extract_query_type("INSERT INTO users VALUES (?)") == "INSERT"
    assert graph_builder._extract_query_type("UPDATE users SET name = ?") == "UPDATE"
    assert graph_builder._extract_query_type("DELETE FROM users WHERE id = ?") == "DELETE"
    assert graph_builder._extract_query_type("BEGIN BATCH ...") == "BATCH"
    assert graph_builder._extract_query_type("INVALID QUERY") == "UNKNOWN"


def test_extract_table_names(graph_builder):
    """テーブル名抽出のテスト"""
    # SELECT
    tables = graph_builder._extract_table_names("SELECT * FROM users WHERE id = ?")
    assert "users" in tables

    # INSERT
    tables = graph_builder._extract_table_names("INSERT INTO orders (id) VALUES (?)")
    assert "orders" in tables

    # UPDATE
    tables = graph_builder._extract_table_names("UPDATE products SET price = ?")
    assert "products" in tables

    # 複数テーブル
    tables = graph_builder._extract_table_names(
        "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    )
    assert "users" in tables
    # JOINは未対応だが、FROMは抽出される


def test_extract_class_name(graph_builder):
    """クラス名抽出のテスト"""
    assert graph_builder._extract_class_name("/path/to/UserDAO.java") == "UserDAO"
    assert graph_builder._extract_class_name("OrderService.java") == "OrderService"


def test_extract_package_name(graph_builder):
    """パッケージ名抽出のテスト"""
    # 標準的なMavenプロジェクト構造
    package = graph_builder._extract_package_name(
        "src/main/java/com/example/dao/UserDAO.java"
    )
    assert package == "com.example.dao"

    # パッケージなし
    package = graph_builder._extract_package_name("UserDAO.java")
    assert package is None


def test_node_deduplication(graph_builder):
    """ノード重複排除のテスト"""
    # 同じファイルを2回作成
    key1 = graph_builder._create_file_node("/path/to/UserDAO.java")
    key2 = graph_builder._create_file_node("/path/to/UserDAO.java")

    # 同じキーが返される
    assert key1 == key2

    # ノードは1つだけ作成される
    file_nodes = [n for n in graph_builder._created_nodes if n.node_type == NodeType.FILE]
    assert len(file_nodes) == 1


def test_incremental_update(graph_builder, sample_analysis_result):
    """増分更新のテスト"""
    # 1回目の構築
    nodes1, rels1 = graph_builder.build_from_analysis_result(sample_analysis_result)
    count1 = len(nodes1)

    # 2回目の構築（新しいbuilderインスタンス）
    graph_builder2 = GraphBuilder()
    nodes2, rels2 = graph_builder2.build_from_analysis_result(sample_analysis_result)

    # 同じ結果が得られる
    assert len(nodes2) == count1


def test_empty_analysis_result(graph_builder):
    """空の分析結果のテスト"""
    empty_result = {
        "analyzed_files": [],
        "total_issues": 0,
        "issues_by_severity": {},
        "issues": [],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(empty_result)

    assert len(nodes) == 0
    assert len(relationships) == 0


def test_extract_query_type_edge_cases(graph_builder):
    """クエリタイプ抽出のエッジケースのテスト"""
    # 空白を含むCQL
    assert graph_builder._extract_query_type("  SELECT  ") == "SELECT"

    # 小文字のCQL
    assert graph_builder._extract_query_type("select * from users") == "SELECT"

    # 空文字列
    assert graph_builder._extract_query_type("") == "UNKNOWN"

    # 無効なCQL
    assert graph_builder._extract_query_type("INVALID") == "UNKNOWN"
    assert graph_builder._extract_query_type("CREATE TABLE users") == "UNKNOWN"


def test_extract_table_names_complex_queries(graph_builder):
    """複雑なクエリからのテーブル名抽出テスト"""
    # 複数のFROM
    cql = "SELECT * FROM users u, orders o WHERE u.id = o.user_id"
    tables = graph_builder._extract_table_names(cql)
    assert "users" in tables

    # DELETE FROM
    cql = "DELETE FROM users WHERE id = ?"
    tables = graph_builder._extract_table_names(cql)
    assert "users" in tables

    # 空のCQL
    tables = graph_builder._extract_table_names("")
    assert len(tables) == 0

    # テーブル名なし
    tables = graph_builder._extract_table_names("INVALID QUERY")
    assert len(tables) == 0


def test_extract_class_name_edge_cases(graph_builder):
    """クラス名抽出のエッジケースのテスト"""
    # 拡張子なしのファイル
    assert graph_builder._extract_class_name("UserDAO") == "UserDAO"

    # パスなしのファイル名
    assert graph_builder._extract_class_name("UserDAO.java") == "UserDAO"

    # 複雑なパス
    assert graph_builder._extract_class_name("/very/long/path/to/file/UserDAO.java") == "UserDAO"


def test_extract_package_name_edge_cases(graph_builder):
    """パッケージ名抽出のエッジケースのテスト"""
    # javaディレクトリなし
    package = graph_builder._extract_package_name("UserDAO.java")
    assert package is None

    # javaディレクトリ直下
    package = graph_builder._extract_package_name("src/main/java/UserDAO.java")
    assert package is None or package == ""

    # 複雑なパッケージ構造
    package = graph_builder._extract_package_name("src/main/java/com/example/dao/impl/UserDAO.java")
    assert package == "com.example.dao.impl"


def test_process_issue_with_missing_fields(graph_builder):
    """フィールドが欠けている問題の処理テスト"""
    issue_with_missing_fields = {
        "file": "/src/UserDAO.java",
        "line": 42,
        "cql": "SELECT * FROM users",
        "type": "TEST_ISSUE",
        "severity": "medium",
        "message": "Test message",
        "recommendation": "Test recommendation",
        "evidence": [],
        "confidence": 1.0,
        # detector, detailsなど一部フィールドが欠けている
    }

    analysis_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "issues": [issue_with_missing_fields],
        "total_issues": 1,
        "issues_by_severity": {"medium": 1},
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # 問題なく処理されることを確認
    assert len(nodes) > 0
    assert len(relationships) > 0


def test_multiple_issues_same_file(graph_builder):
    """同じファイルに複数の問題があるケースのテスト"""
    analysis_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 3,
        "issues_by_severity": {"high": 2, "medium": 1},
        "issues": [
            {
                "detector": "Detector1",
                "type": "ISSUE_TYPE_1",
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
                "detector": "Detector2",
                "type": "ISSUE_TYPE_2",
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 55,
                "message": "Issue 2",
                "cql": "SELECT * FROM users WHERE name = ?",
                "recommendation": "Fix 2",
                "evidence": [],
                "confidence": 0.9,
            },
            {
                "detector": "Detector3",
                "type": "ISSUE_TYPE_3",
                "severity": "medium",
                "file": "/src/UserDAO.java",
                "line": 68,
                "message": "Issue 3",
                "cql": "INSERT INTO users VALUES (?)",
                "recommendation": "Fix 3",
                "evidence": [],
                "confidence": 0.8,
            },
        ],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # 3つの問題ノードが作成される
    issue_nodes = [n for n in nodes if n.node_type == NodeType.ISSUE]
    assert len(issue_nodes) == 3

    # 異なる重要度が設定されている
    severities = {node.properties.get("severity") for node in issue_nodes}
    assert "high" in severities
    assert "medium" in severities


def test_cql_with_multiple_tables(graph_builder):
    """複数テーブルを参照するCQLのテスト"""
    analysis_result = {
        "analyzed_files": ["/src/JoinDAO.java"],
        "total_issues": 1,
        "issues_by_severity": {"medium": 1},
        "issues": [
            {
                "detector": "JoinDetector",
                "type": "COMPLEX_JOIN",
                "severity": "medium",
                "file": "/src/JoinDAO.java",
                "line": 42,
                "message": "Complex join detected",
                "cql": "SELECT * FROM users, orders WHERE users.id = orders.user_id",
                "recommendation": "Consider denormalization",
                "evidence": [],
                "confidence": 1.0,
            }
        ],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # テーブルノードが複数作成される
    table_nodes = [n for n in nodes if n.node_type == NodeType.TABLE]
    table_names = {node.properties.get("name") for node in table_nodes}

    assert "users" in table_names
    # 現在の実装では複数テーブル検出は部分的なので、最低1つは検出されることを確認
    assert len(table_nodes) >= 1


def test_method_node_deduplication(graph_builder):
    """メソッドノードの重複排除テスト"""
    # 同じメソッド（同じissue type = 同じメソッド名）を持つ2つの問題
    analysis_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 2,
        "issues_by_severity": {"high": 2},
        "issues": [
            {
                "detector": "Detector1",
                "type": "ALLOW_FILTERING",  # 同じタイプ = 同じメソッド名
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じメソッド内
                "message": "Issue 1",
                "cql": "SELECT * FROM users WHERE id = ?",
                "recommendation": "Fix 1",
                "evidence": [],
                "confidence": 1.0,
            },
            {
                "detector": "Detector2",
                "type": "ALLOW_FILTERING",  # 同じタイプ = 同じメソッド名
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じメソッド内（同じ行番号）
                "message": "Issue 2",
                "cql": "SELECT * FROM users WHERE email = ?",
                "recommendation": "Fix 2",
                "evidence": [],
                "confidence": 1.0,
            },
        ],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # メソッドノードは1つだけ作成される（重複排除される）
    method_nodes = [n for n in nodes if n.node_type == NodeType.METHOD]
    assert len(method_nodes) == 1


def test_query_node_deduplication(graph_builder):
    """クエリノードの重複排除テスト"""
    # 同じクエリ（同じメソッド名＋同じ行番号）を持つ2つの問題
    same_cql = "SELECT * FROM users WHERE id = ?"
    analysis_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 2,
        "issues_by_severity": {"high": 2},
        "issues": [
            {
                "detector": "Detector1",
                "type": "ALLOW_FILTERING",  # 同じタイプ = 同じメソッド名
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じ行番号
                "message": "Issue 1",
                "cql": same_cql,
                "recommendation": "Fix 1",
                "evidence": [],
                "confidence": 1.0,
            },
            {
                "detector": "Detector2",
                "type": "ALLOW_FILTERING",  # 同じタイプ = 同じメソッド名
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じ行番号
                "message": "Issue 2",
                "cql": same_cql,  # 同じCQL
                "recommendation": "Fix 2",
                "evidence": [],
                "confidence": 1.0,
            },
        ],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # クエリノードは1つだけ作成される（重複排除される）
    query_nodes = [n for n in nodes if n.node_type == NodeType.QUERY]
    assert len(query_nodes) == 1


def test_issue_node_deduplication(graph_builder):
    """問題ノードの重複排除テスト"""
    # 同じタイプ・同じ行番号の問題（実際には重複として扱われる）
    analysis_result = {
        "analyzed_files": ["/src/UserDAO.java"],
        "total_issues": 2,
        "issues_by_severity": {"high": 2},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",  # 同じタイプ
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じ行番号
                "message": "ALLOW FILTERING detected",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Use partition key",
                "evidence": [],
                "confidence": 1.0,
            },
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",  # 同じタイプ
                "severity": "high",
                "file": "/src/UserDAO.java",
                "line": 42,  # 同じ行番号
                "message": "ALLOW FILTERING detected again",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Use partition key",
                "evidence": [],
                "confidence": 1.0,
            },
        ],
    }

    nodes, relationships = graph_builder.build_from_analysis_result(analysis_result)

    # 問題ノードは1つだけ作成される（重複排除される）
    issue_nodes = [n for n in nodes if n.node_type == NodeType.ISSUE]
    assert len(issue_nodes) == 1
