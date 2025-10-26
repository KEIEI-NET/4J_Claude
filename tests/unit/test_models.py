"""
modelsパッケージのユニットテスト
"""
import pytest
from cassandra_analyzer.models import AnalysisResult, CassandraCall, Issue


class TestAnalysisResult:
    """AnalysisResultのテストクラス"""

    @pytest.fixture
    def sample_issues(self):
        """サンプル問題リスト"""
        return [
            Issue(
                detector_name="TestDetector",
                issue_type="ALLOW_FILTERING",
                severity="critical",
                file_path="test1.java",
                line_number=10,
                message="Critical issue",
                cql_text="SELECT * FROM users ALLOW FILTERING",
                recommendation="Fix it",
                evidence=["evidence1"],
                confidence=1.0,
            ),
            Issue(
                detector_name="TestDetector",
                issue_type="NO_PARTITION_KEY",
                severity="high",
                file_path="test1.java",
                line_number=20,
                message="High issue",
                cql_text="SELECT * FROM users",
                recommendation="Add partition key",
                evidence=["evidence2"],
                confidence=0.9,
            ),
            Issue(
                detector_name="TestDetector",
                issue_type="BATCH_SIZE",
                severity="medium",
                file_path="test2.java",
                line_number=30,
                message="Medium issue",
                cql_text="BATCH",
                recommendation="Reduce batch size",
                evidence=["evidence3"],
                confidence=0.8,
            ),
        ]

    @pytest.fixture
    def sample_result(self, sample_issues):
        """サンプル分析結果"""
        return AnalysisResult(
            analyzed_files=["test1.java", "test2.java"],
            total_issues=3,
            issues_by_severity={"critical": 1, "high": 1, "medium": 1},
            issues=sample_issues,
            analysis_time=1.5,
        )

    def test_to_dict(self, sample_result):
        """to_dictメソッドのテスト"""
        result_dict = sample_result.to_dict()

        assert "analyzed_files" in result_dict
        assert "total_issues" in result_dict
        assert "issues_by_severity" in result_dict
        assert "issues" in result_dict
        assert "analysis_time_seconds" in result_dict
        assert "timestamp" in result_dict

        assert result_dict["total_issues"] == 3
        assert len(result_dict["issues"]) == 3
        assert result_dict["analysis_time_seconds"] == 1.5

    def test_get_critical_issues(self, sample_result):
        """critical問題の取得"""
        critical = sample_result.get_critical_issues()
        assert len(critical) == 1
        assert critical[0].severity == "critical"
        assert critical[0].issue_type == "ALLOW_FILTERING"

    def test_get_high_issues(self, sample_result):
        """high問題の取得"""
        high = sample_result.get_high_issues()
        assert len(high) == 1
        assert high[0].severity == "high"
        assert high[0].issue_type == "NO_PARTITION_KEY"

    def test_get_issues_by_file(self, sample_result):
        """ファイル別の問題取得"""
        by_file = sample_result.get_issues_by_file()
        assert len(by_file) == 2
        assert len(by_file["test1.java"]) == 2
        assert len(by_file["test2.java"]) == 1

    def test_get_issues_by_type(self, sample_result):
        """タイプ別の問題取得"""
        by_type = sample_result.get_issues_by_type()
        assert len(by_type) == 3
        assert len(by_type["ALLOW_FILTERING"]) == 1
        assert len(by_type["NO_PARTITION_KEY"]) == 1
        assert len(by_type["BATCH_SIZE"]) == 1


class TestCassandraCall:
    """CassandraCallのテストクラス"""

    def test_initialization(self):
        """初期化のテスト"""
        call = CassandraCall(
            method_name="getUserById",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level="ONE",
            file_path="test.java",
            class_name="UserDao",
        )

        assert call.cql_text == "SELECT * FROM users"
        assert call.line_number == 10
        assert call.file_path == "test.java"
        assert call.method_name == "getUserById"
        assert call.class_name == "UserDao"

    def test_str_representation(self):
        """文字列表現のテスト"""
        call = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )

        str_repr = str(call)
        assert "test.java" in str_repr
        assert "10" in str_repr

    def test_batch_call_type(self):
        """batchメソッドの検出"""
        from cassandra_analyzer.models.cassandra_call import CallType
        call = CassandraCall(
            method_name="batch",
            cql_text="BATCH",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )
        assert call.call_type == CallType.BATCH

    def test_is_constant_reference(self):
        """定数参照の判定"""
        call = CassandraCall(
            method_name="execute",
            cql_text="[CONSTANT:MY_QUERY]",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )
        assert call.is_constant_reference() is True

        call2 = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )
        assert call2.is_constant_reference() is False

    def test_get_short_location(self):
        """短縮位置情報の取得"""
        call = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="/path/to/test.java",
        )
        location = call.get_short_location()
        assert location == "test.java:10"


class TestIssue:
    """Issueのテストクラス"""

    def test_initialization(self):
        """初期化のテスト"""
        issue = Issue(
            detector_name="TestDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="Test message",
            cql_text="SELECT * FROM users",
            recommendation="Fix it",
            evidence=["evidence1"],
            confidence=0.95,
        )

        assert issue.detector_name == "TestDetector"
        assert issue.issue_type == "ALLOW_FILTERING"
        assert issue.severity == "high"
        assert issue.file_path == "test.java"
        assert issue.line_number == 10
        assert issue.message == "Test message"
        assert issue.cql_text == "SELECT * FROM users"
        assert issue.recommendation == "Fix it"
        assert issue.evidence == ["evidence1"]
        assert issue.confidence == 0.95

    def test_to_dict(self):
        """to_dictメソッドのテスト"""
        issue = Issue(
            detector_name="TestDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="Test message",
            cql_text="SELECT * FROM users",
            recommendation="Fix it",
            evidence=["evidence1", "evidence2"],
            confidence=0.95,
        )

        result = issue.to_dict()
        assert result["detector"] == "TestDetector"
        assert result["type"] == "ALLOW_FILTERING"
        assert result["severity"] == "high"
        assert result["file"] == "test.java"
        assert result["line"] == 10
        assert result["message"] == "Test message"
        assert result["cql"] == "SELECT * FROM users"
        assert result["recommendation"] == "Fix it"
        assert result["evidence"] == ["evidence1", "evidence2"]
        assert result["confidence"] == 0.95

    def test_str_representation(self):
        """文字列表現のテスト"""
        issue = Issue(
            detector_name="TestDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="Test message",
            cql_text="SELECT * FROM users",
            recommendation="Fix it",
            evidence=[],
            confidence=0.95,
        )

        str_repr = str(issue)
        assert "ALLOW_FILTERING" in str_repr
        assert "high" in str_repr
        assert "test.java" in str_repr
        assert "10" in str_repr

    def test_invalid_severity(self):
        """不正なseverityでエラー"""
        with pytest.raises(ValueError, match="Invalid severity"):
            Issue(
                detector_name="TestDetector",
                issue_type="ALLOW_FILTERING",
                severity="invalid",
                file_path="test.java",
                line_number=10,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=0.95,
            )

    def test_invalid_confidence(self):
        """不正なconfidenceでエラー"""
        with pytest.raises(ValueError, match="Confidence must be between"):
            Issue(
                detector_name="TestDetector",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=10,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.5,  # 不正な値
            )

    def test_severity_order(self):
        """severity_orderプロパティのテスト"""
        critical = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="critical",
            file_path="test.java",
            line_number=1,
            message="",
            cql_text="",
            recommendation="",
            evidence=[],
            confidence=1.0,
        )
        high = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="high",
            file_path="test.java",
            line_number=1,
            message="",
            cql_text="",
            recommendation="",
            evidence=[],
            confidence=1.0,
        )
        medium = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="medium",
            file_path="test.java",
            line_number=1,
            message="",
            cql_text="",
            recommendation="",
            evidence=[],
            confidence=1.0,
        )
        low = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="low",
            file_path="test.java",
            line_number=1,
            message="",
            cql_text="",
            recommendation="",
            evidence=[],
            confidence=1.0,
        )

        assert critical.severity_order == 0
        assert high.severity_order == 1
        assert medium.severity_order == 2
        assert low.severity_order == 3
