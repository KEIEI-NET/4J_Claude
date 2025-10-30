"""
Tests for N+1 Query Detector
"""

import pytest
from multidb_analyzer.mysql.detectors import NPlusOneDetector
from multidb_analyzer.mysql.models import (
    MySQLQuery,
    SQLOperation,
    TableReference
)
from multidb_analyzer.core.base_detector import (
    Severity,
    IssueCategory
)


class TestNPlusOneDetector:
    """N+1クエリ検出器のテスト"""

    @pytest.fixture
    def detector(self):
        """検出器インスタンス"""
        return NPlusOneDetector()



    def test_detector_initialization(self, detector):
        """検出器の初期化"""
        assert detector.name == "NPlusOneDetector"

    def test_detect_query_in_for_loop(self, detector):
        """forループ内のクエリ検出"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE id = ?",
            file_path="UserService.java",
            line_number=42,
            is_in_loop=True,
            loop_type="for"
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.HIGH
        assert issue.category == IssueCategory.PERFORMANCE
        assert "N+1" in issue.title
        assert "for" in issue.description.lower()
        assert "batch" in issue.suggestion.lower() or "join" in issue.suggestion.lower()

    def test_detect_query_in_while_loop(self, detector):
        """whileループ内のクエリ検出"""
        table = TableReference(name="orders")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM orders WHERE user_id = ?",
            file_path="OrderService.java",
            line_number=100,
            is_in_loop=True,
            loop_type="while"
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        assert "while" in issues[0].description.lower()

    def test_no_issue_for_non_loop_query(self, detector):
        """ループ外のクエリは検出しない"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserService.java",
            line_number=42,
            is_in_loop=False
        )

        issues = detector.detect([query])

        assert len(issues) == 0

    def test_no_issue_for_insert_in_loop(self, detector):
        """INSERTはN+1検出の対象外（SELECTのみ）"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.INSERT,
            tables=[table],
            query_text="INSERT INTO users (name) VALUES (?)",
            file_path="UserService.java",
            line_number=42,
            is_in_loop=True,
            loop_type="for"
        )

        issues = detector.detect([query])

        # INSERTはN+1として検出されない（SELECTのみ対象）
        assert len(issues) == 0

    def test_multiple_loops(self, detector):
        """複数のループ内クエリ"""
        queries = [
            MySQLQuery(
                operation=SQLOperation.SELECT,
                tables=[TableReference(name="users")],
                query_text="SELECT * FROM users WHERE id = ?",
                file_path="UserService.java",
                line_number=42,
                is_in_loop=True,
                loop_type="for"
            ),
            MySQLQuery(
                operation=SQLOperation.SELECT,
                tables=[TableReference(name="orders")],
                query_text="SELECT * FROM orders WHERE user_id = ?",
                file_path="OrderService.java",
                line_number=100,
                is_in_loop=True,
                loop_type="while"
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) == 2

    def test_issue_metadata(self, detector):
        """問題のメタデータ確認"""
        table = TableReference(name="products")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM products WHERE id = ?",
            file_path="ProductService.java",
            line_number=200,
            is_in_loop=True,
            loop_type="for",
            method_name="findProducts",
            class_name="ProductService"
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.metadata['loop_type'] == "for"
        assert issue.metadata['table'] == "products"
        assert issue.metadata['operation'] == "SELECT"
        assert issue.metadata['method_name'] == "findProducts"

    def test_suggestion_includes_batch_query(self, detector):
        """提案にバッチクエリが含まれる"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE id = ?",
            file_path="UserService.java",
            line_number=42,
            is_in_loop=True,
            loop_type="for"
        )

        issues = detector.detect([query])

        suggestion = issues[0].suggestion
        assert "IN" in suggestion or "batch" in suggestion.lower()
        assert "JOIN" in suggestion

    def test_empty_query_list(self, detector):
        """空のクエリリスト"""
        issues = detector.detect([])
        assert len(issues) == 0
