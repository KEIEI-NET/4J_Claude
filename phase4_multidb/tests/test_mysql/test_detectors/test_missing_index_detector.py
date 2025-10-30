"""
Tests for Missing Index Detector
"""

import pytest
from multidb_analyzer.mysql.detectors import MissingIndexDetector
from multidb_analyzer.mysql.models import (
    MySQLQuery,
    SQLOperation,
    TableReference,
    JoinInfo,
    JoinType
)
from multidb_analyzer.core.base_detector import (
    Severity,
    IssueCategory
)


class TestMissingIndexDetector:
    """欠落インデックス検出器のテスト"""

    @pytest.fixture
    def detector(self):
        """検出器インスタンス"""
        return MissingIndexDetector()



    def test_detector_initialization(self, detector):
        """検出器の初期化"""
        assert detector.name == "MissingIndexDetector"

    def test_detect_where_without_index_hint(self, detector):
        """WHERE句があるがインデックスヒントがない"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'"],
            has_index_hint=False
        )

        issues = detector.detect([query])

        assert len(issues) >= 1
        issue = issues[0]
        assert issue.severity == Severity.MEDIUM
        assert "index" in issue.title.lower()

    def test_no_issue_with_index_hint(self, detector):
        """インデックスヒントがある場合は問題なし"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users USE INDEX (idx_status) WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'"],
            has_index_hint=True
        )

        issues = detector.detect([query])

        # インデックスヒントがあれば検出されない
        assert len(issues) == 0

    def test_detect_order_by_without_index(self, detector):
        """ORDER BYがあるがインデックスヒントがない"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users ORDER BY created_at DESC",
            file_path="UserDao.java",
            line_number=42,
            has_order_by=True,
            order_by_columns=["created_at DESC"],
            has_index_hint=False
        )

        issues = detector.detect([query])

        assert len(issues) >= 1
        order_by_issues = [i for i in issues if "ORDER BY" in i.title]
        assert len(order_by_issues) > 0

    def test_detect_join_without_index(self, detector):
        """JOINがあるがインデックスヒントがない"""
        users_table = TableReference(name="users")
        orders_table = TableReference(name="orders")

        join = JoinInfo(
            join_type=JoinType.INNER,
            table=orders_table,
            condition="orders.user_id = users.id",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[users_table],
            query_text="SELECT * FROM users INNER JOIN orders ON orders.user_id = users.id",
            file_path="UserDao.java",
            line_number=42,
            joins=[join],
            has_index_hint=False
        )

        issues = detector.detect([query])

        assert len(issues) >= 1
        join_issues = [i for i in issues if "JOIN" in i.title]
        assert len(join_issues) > 0
        assert join_issues[0].severity == Severity.HIGH

    def test_multiple_where_columns(self, detector):
        """複数のWHEREカラム"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE status = 'active' AND created_at > '2024-01-01'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'", "created_at > '2024-01-01'"],
            has_index_hint=False
        )

        issues = detector.detect([query])

        # 複合インデックスの提案
        assert len(issues) >= 1

    def test_non_select_queries_ignored(self, detector):
        """SELECT以外のクエリは無視"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.INSERT,
            tables=[table],
            query_text="INSERT INTO users (name) VALUES (?)",
            file_path="UserDao.java",
            line_number=42
        )

        issues = detector.detect([query])

        # SELECTのみが対象
        assert len(issues) == 0

    def test_suggestion_includes_create_index(self, detector):
        """提案にCREATE INDEX文が含まれる"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'"],
            has_index_hint=False
        )

        issues = detector.detect([query])

        suggestion = issues[0].suggestion
        assert "CREATE INDEX" in suggestion
        assert "users" in suggestion

    def test_empty_query_list(self, detector):
        """空のクエリリスト"""
        issues = detector.detect([])
        assert len(issues) == 0
