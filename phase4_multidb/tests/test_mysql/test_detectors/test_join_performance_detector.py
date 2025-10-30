"""
Tests for JOIN Performance Detector
"""

import pytest
from multidb_analyzer.mysql.detectors import JoinPerformanceDetector
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


class TestJoinPerformanceDetector:
    """JOINパフォーマンス検出器のテスト"""

    @pytest.fixture
    def detector(self):
        """検出器インスタンス"""
        return JoinPerformanceDetector()



    def test_detector_initialization(self, detector):
        """検出器の初期化"""
        assert detector.name == "JoinPerformanceDetector"
        assert detector.join_count_threshold == 4

    def test_detect_excessive_joins(self, detector):
        """過剰なJOIN数の検出"""
        # 4つ以上のJOINを作成
        main_table = TableReference(name="orders")
        joins = [
            JoinInfo(JoinType.INNER, TableReference(name=f"table{i}"), f"condition{i}", 42)
            for i in range(1, 5)
        ]

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders JOIN table1... JOIN table4...",
            file_path="OrderDao.java",
            line_number=42,
            joins=joins
        )

        issues = detector.detect([query])

        excessive_join_issues = [i for i in issues if "Excessive" in i.title or str(len(joins)) in i.title]
        assert len(excessive_join_issues) > 0
        issue = excessive_join_issues[0]
        assert issue.severity == Severity.HIGH

    def test_no_issue_for_few_joins(self, detector):
        """少数のJOINは問題なし"""
        main_table = TableReference(name="orders")
        joins = [
            JoinInfo(JoinType.INNER, TableReference(name="users"), "orders.user_id = users.id", 42),
            JoinInfo(JoinType.LEFT, TableReference(name="products"), "orders.product_id = products.id", 43)
        ]

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders JOIN users... LEFT JOIN products...",
            file_path="OrderDao.java",
            line_number=42,
            joins=joins,
            where_conditions=["status = 'completed'"]  # WHERE句あり
        )

        issues = detector.detect([query])

        # 3個以下のJOINは過剰として検出されない
        excessive_join_issues = [i for i in issues if "Excessive" in i.title]
        assert len(excessive_join_issues) == 0

    def test_detect_cross_join(self, detector):
        """CROSS JOINの検出"""
        main_table = TableReference(name="orders")
        cross_join = JoinInfo(
            join_type=JoinType.CROSS,
            table=TableReference(name="products"),
            condition="",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders CROSS JOIN products",
            file_path="OrderDao.java",
            line_number=42,
            joins=[cross_join]
        )

        issues = detector.detect([query])

        cross_join_issues = [i for i in issues if "CROSS" in i.title or "Cartesian" in i.title]
        assert len(cross_join_issues) > 0
        issue = cross_join_issues[0]
        assert issue.severity == Severity.CRITICAL

    def test_detect_select_star_with_join(self, detector):
        """SELECT *とJOINの組み合わせ検出"""
        main_table = TableReference(name="orders")
        join = JoinInfo(
            join_type=JoinType.INNER,
            table=TableReference(name="users"),
            condition="orders.user_id = users.id",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders INNER JOIN users ON orders.user_id = users.id",
            file_path="OrderDao.java",
            line_number=42,
            joins=[join],
            uses_select_star=True
        )

        issues = detector.detect([query])

        select_star_issues = [i for i in issues if "SELECT *" in i.title]
        assert len(select_star_issues) > 0
        issue = select_star_issues[0]
        assert issue.severity == Severity.MEDIUM

    def test_detect_join_without_where(self, detector):
        """WHERE句なしのJOIN検出"""
        main_table = TableReference(name="orders")
        join = JoinInfo(
            join_type=JoinType.INNER,
            table=TableReference(name="users"),
            condition="orders.user_id = users.id",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders INNER JOIN users ON orders.user_id = users.id",
            file_path="OrderDao.java",
            line_number=42,
            joins=[join],
            where_conditions=[]  # WHERE句なし
        )

        issues = detector.detect([query])

        where_issues = [i for i in issues if "WHERE" in i.title]
        assert len(where_issues) > 0
        issue = where_issues[0]
        assert issue.severity == Severity.MEDIUM

    def test_no_issue_for_join_with_where(self, detector):
        """WHERE句ありのJOINは検出しない"""
        main_table = TableReference(name="orders")
        join = JoinInfo(
            join_type=JoinType.INNER,
            table=TableReference(name="users"),
            condition="orders.user_id = users.id",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders INNER JOIN users... WHERE status = 'completed'",
            file_path="OrderDao.java",
            line_number=42,
            joins=[join],
            where_conditions=["status = 'completed'"],
            uses_select_star=False
        )

        issues = detector.detect([query])

        # WHERE句ありなら、その点では問題なし
        where_issues = [i for i in issues if "WHERE" in i.title]
        assert len(where_issues) == 0

    def test_no_issue_for_queries_without_joins(self, detector):
        """JOINなしのクエリは検出しない"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42,
            joins=[]
        )

        issues = detector.detect([query])

        # JOINがないので何も検出されない
        assert len(issues) == 0

    def test_multiple_join_types(self, detector):
        """複数のJOINタイプ"""
        main_table = TableReference(name="orders")
        joins = [
            JoinInfo(JoinType.INNER, TableReference(name="users"), "cond1", 42),
            JoinInfo(JoinType.LEFT, TableReference(name="products"), "cond2", 43),
            JoinInfo(JoinType.RIGHT, TableReference(name="payments"), "cond3", 44),
            JoinInfo(JoinType.CROSS, TableReference(name="categories"), "cond4", 45)
        ]

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders ...",
            file_path="OrderDao.java",
            line_number=42,
            joins=joins
        )

        issues = detector.detect([query])

        # 過剰なJOINとCROSS JOINの両方が検出される
        assert len(issues) >= 2

    def test_suggestion_quality(self, detector):
        """提案の品質確認"""
        main_table = TableReference(name="orders")
        joins = [
            JoinInfo(JoinType.INNER, TableReference(name=f"table{i}"), f"condition{i}", 42)
            for i in range(1, 5)
        ]

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[main_table],
            query_text="SELECT * FROM orders...",
            file_path="OrderDao.java",
            line_number=42,
            joins=joins
        )

        issues = detector.detect([query])

        excessive_issues = [i for i in issues if "Excessive" in i.title or "4" in i.title]
        if excessive_issues:
            suggestion = excessive_issues[0].suggestion
            # 提案に分割やサブクエリなどの解決策が含まれる
            assert any(keyword in suggestion.lower() for keyword in ['split', 'subquer', 'denormalize'])

    def test_empty_query_list(self, detector):
        """空のクエリリスト"""
        issues = detector.detect([])
        assert len(issues) == 0
