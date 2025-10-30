"""
Tests for Full Table Scan Detector
"""

import pytest
from multidb_analyzer.mysql.detectors import FullTableScanDetector
from multidb_analyzer.mysql.models import (
    MySQLQuery,
    SQLOperation,
    TableReference
)
from multidb_analyzer.core.base_detector import (
    Severity,
    IssueCategory
)


class TestFullTableScanDetector:
    """フルテーブルスキャン検出器のテスト"""

    @pytest.fixture
    def detector(self):
        """検出器インスタンス"""
        return FullTableScanDetector()



    def test_detector_initialization(self, detector):
        """検出器の初期化"""
        assert detector.name == "FullTableScanDetector"
        assert 'LOWER' in detector.non_sargable_functions

    def test_detect_select_without_where(self, detector):
        """WHERE句なしのSELECT検出"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=[]
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.HIGH
        assert "WHERE" in issue.title
        assert "full table scan" in issue.description.lower()

    def test_detect_update_without_where(self, detector):
        """WHERE句なしのUPDATE検出（CRITICAL）"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.UPDATE,
            tables=[table],
            query_text="UPDATE users SET status = 'inactive'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=[]
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.CRITICAL  # UPDATEはCRITICAL
        assert "WHERE" in issue.title

    def test_detect_delete_without_where(self, detector):
        """WHERE句なしのDELETE検出（CRITICAL）"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.DELETE,
            tables=[table],
            query_text="DELETE FROM users",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=[]
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.CRITICAL

    def test_no_issue_for_select_with_where(self, detector):
        """WHERE句ありのSELECTは問題なし"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'"]
        )

        issues = detector.detect([query])

        # WHERE句にSARGABLE条件があれば、フルスキャンとは検出されない
        # （関数やワイルドカードがなければ）
        assert all("Non-Sargable" not in issue.title for issue in issues)

    def test_detect_function_in_where(self, detector):
        """WHERE句での関数使用検出"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE LOWER(name) = 'john'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["LOWER(name) = 'john'"]
        )

        issues = detector.detect([query])

        # 関数使用による非SARGABLE条件
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.HIGH
        assert "Non-Sargable" in issue.title or "Function" in issue.title

    def test_detect_leading_wildcard(self, detector):
        """先頭ワイルドカードLIKE検出"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE name LIKE '%smith'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["name LIKE '%smith'"]
        )

        issues = detector.detect([query])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == Severity.CRITICAL
        assert "wildcard" in issue.title.lower() or "LIKE" in issue.title

    def test_trailing_wildcard_ok(self, detector):
        """後方ワイルドカードは問題なし"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE name LIKE 'smith%'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["name LIKE 'smith%'"]
        )

        issues = detector.detect([query])

        # 後方ワイルドカードはインデックス使用可能
        leading_wildcard_issues = [i for i in issues if "wildcard" in i.title.lower()]
        assert len(leading_wildcard_issues) == 0

    def test_multiple_non_sargable_functions(self, detector):
        """複数の非SARGABLE関数"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE UPPER(name) = 'JOHN' AND YEAR(created_at) = 2024",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["UPPER(name) = 'JOHN'", "YEAR(created_at) = 2024"]
        )

        issues = detector.detect([query])

        # 関数使用による問題が1つ検出される
        function_issues = [i for i in issues if "Function" in i.title or "Non-Sargable" in i.title]
        assert len(function_issues) >= 1

    def test_insert_ignored(self, detector):
        """INSERTはチェックされない"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.INSERT,
            tables=[table],
            query_text="INSERT INTO users (name) VALUES ('John')",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=[]
        )

        issues = detector.detect([query])

        # INSERTは検出対象外
        assert len(issues) == 0

    def test_suggestion_includes_alternatives(self, detector):
        """提案に代替案が含まれる"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=[]
        )

        issues = detector.detect([query])

        suggestion = issues[0].suggestion
        assert "WHERE" in suggestion
        assert "sql" in suggestion.lower()  # SQL例が含まれる

    def test_empty_query_list(self, detector):
        """空のクエリリスト"""
        issues = detector.detect([])
        assert len(issues) == 0
