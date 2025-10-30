"""
Tests for Base Detector

基底検出器のテスト
"""

import pytest
from datetime import datetime
from multidb_analyzer.core.base_detector import (
    BaseDetector,
    DetectorRegistry,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.core.base_parser import ParsedQuery, QueryType


class DummyDetector(BaseDetector):
    """テスト用ダミー検出器"""

    def __init__(self, config=None, name="DummyDetector"):
        super().__init__(config)
        self._name = name

    def get_name(self) -> str:
        return self._name

    def get_severity(self) -> Severity:
        return Severity.MEDIUM

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(self, queries):
        # テスト用: 1つ問題を作成
        if queries:
            return [
                self.create_issue(
                    title="Test Issue",
                    description="Test description",
                    file_path="test.java",
                    line_number=10
                )
            ]
        return []


class DisabledDetector(DummyDetector):
    """無効化されたダミー検出器"""

    def __init__(self):
        super().__init__(config={'enabled': False}, name="DisabledDetector")


class TestIssue:
    """Issue クラスのテスト"""

    def test_create_issue(self):
        """Issue作成のテスト"""
        issue = Issue(
            detector_name="TestDetector",
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            title="Test Issue",
            description="This is a test issue",
            file_path="/path/to/file.java",
            line_number=42
        )

        assert issue.detector_name == "TestDetector"
        assert issue.severity == Severity.HIGH
        assert issue.category == IssueCategory.SECURITY
        assert issue.title == "Test Issue"
        assert issue.line_number == 42

    def test_issue_to_dict(self):
        """Issueの辞書変換テスト"""
        issue = Issue(
            detector_name="TestDetector",
            severity=Severity.CRITICAL,
            category=IssueCategory.PERFORMANCE,
            title="Performance Issue",
            description="Slow query detected",
            file_path="/path/to/file.java",
            line_number=100,
            query_text="SELECT * FROM users",
            method_name="getUsers",
            class_name="UserService",
            suggestion="Add an index",
            auto_fix_available=True,
            auto_fix_code="CREATE INDEX idx_users",
            tags=['database', 'performance']
        )

        issue_dict = issue.to_dict()

        assert issue_dict['detector_name'] == "TestDetector"
        assert issue_dict['severity'] == 'critical'
        assert issue_dict['category'] == 'performance'
        assert issue_dict['title'] == "Performance Issue"
        assert issue_dict['query_text'] == "SELECT * FROM users"
        assert issue_dict['method_name'] == "getUsers"
        assert issue_dict['class_name'] == "UserService"
        assert issue_dict['auto_fix_available'] is True
        assert 'database' in issue_dict['tags']

    def test_get_severity_score(self):
        """重要度スコア取得のテスト"""
        critical_issue = Issue(
            detector_name="Test",
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            title="Critical",
            description="desc",
            file_path="file.java",
            line_number=1
        )
        high_issue = Issue(
            detector_name="Test",
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            title="High",
            description="desc",
            file_path="file.java",
            line_number=1
        )
        medium_issue = Issue(
            detector_name="Test",
            severity=Severity.MEDIUM,
            category=IssueCategory.SECURITY,
            title="Medium",
            description="desc",
            file_path="file.java",
            line_number=1
        )
        low_issue = Issue(
            detector_name="Test",
            severity=Severity.LOW,
            category=IssueCategory.SECURITY,
            title="Low",
            description="desc",
            file_path="file.java",
            line_number=1
        )
        info_issue = Issue(
            detector_name="Test",
            severity=Severity.INFO,
            category=IssueCategory.SECURITY,
            title="Info",
            description="desc",
            file_path="file.java",
            line_number=1
        )

        assert critical_issue.get_severity_score() == 100
        assert high_issue.get_severity_score() == 75
        assert medium_issue.get_severity_score() == 50
        assert low_issue.get_severity_score() == 25
        assert info_issue.get_severity_score() == 0


class TestBaseDetector:
    """BaseDetector クラスのテスト"""

    @pytest.fixture
    def detector(self):
        """ダミー検出器を作成"""
        return DummyDetector()

    @pytest.fixture
    def detector_with_config(self):
        """設定付き検出器を作成"""
        config = {
            'enabled': True,
            'thresholds': {
                'max_complexity': 10,
                'min_items': 5
            },
            'custom_setting': 'value'
        }
        return DummyDetector(config=config)

    def test_get_name(self, detector):
        """検出器名取得のテスト"""
        assert detector.get_name() == "DummyDetector"

    def test_get_severity(self, detector):
        """重要度取得のテスト"""
        assert detector.get_severity() == Severity.MEDIUM

    def test_get_category(self, detector):
        """カテゴリ取得のテスト"""
        assert detector.get_category() == IssueCategory.PERFORMANCE

    def test_detect(self, detector):
        """検出処理のテスト"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text="test",
                file_path="test.java",
                line_number=1
            )
        ]

        issues = detector.detect(queries)
        assert len(issues) == 1
        assert issues[0].title == "Test Issue"

    def test_get_description(self, detector):
        """説明取得のテスト"""
        description = detector.get_description()
        assert isinstance(description, str)

    def test_is_enabled_default_true(self, detector):
        """デフォルトで有効化されているテスト"""
        assert detector.is_enabled() is True

    def test_is_enabled_explicit_false(self):
        """明示的に無効化されているテスト"""
        disabled_detector = DisabledDetector()
        assert disabled_detector.is_enabled() is False

    def test_get_threshold(self, detector_with_config):
        """閾値取得のテスト"""
        max_complexity = detector_with_config.get_threshold('max_complexity')
        min_items = detector_with_config.get_threshold('min_items')
        non_existent = detector_with_config.get_threshold('non_existent', default=999)

        assert max_complexity == 10
        assert min_items == 5
        assert non_existent == 999

    def test_get_config_value(self, detector_with_config):
        """設定値取得のテスト"""
        enabled = detector_with_config.get_config_value('enabled')
        custom = detector_with_config.get_config_value('custom_setting')
        non_existent = detector_with_config.get_config_value('non_existent', default='default')

        assert enabled is True
        assert custom == 'value'
        assert non_existent == 'default'

    def test_create_issue_with_defaults(self, detector):
        """デフォルト値でのIssue作成"""
        issue = detector.create_issue(
            title="Test",
            description="Description",
            file_path="test.java",
            line_number=10
        )

        assert issue.detector_name == "DummyDetector"
        assert issue.severity == Severity.MEDIUM
        assert issue.category == IssueCategory.PERFORMANCE

    def test_create_issue_with_override(self, detector):
        """オーバーライド値でのIssue作成"""
        issue = detector.create_issue(
            title="Test",
            description="Description",
            file_path="test.java",
            line_number=10,
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            query_text="SELECT *",
            suggestion="Fix it"
        )

        assert issue.severity == Severity.CRITICAL
        assert issue.category == IssueCategory.SECURITY
        assert issue.query_text == "SELECT *"
        assert issue.suggestion == "Fix it"

    def test_get_statistics(self, detector):
        """統計情報取得のテスト"""
        # 複数のIssueを作成
        detector.create_issue("Issue 1", "desc", "file1.java", 1, severity=Severity.HIGH)
        detector.create_issue("Issue 2", "desc", "file2.java", 2, severity=Severity.HIGH)
        detector.create_issue("Issue 3", "desc", "file3.java", 3, severity=Severity.MEDIUM)

        stats = detector.get_statistics()

        assert stats['detector_name'] == "DummyDetector"
        assert stats['total_issues'] == 3
        assert stats['severity_counts']['high'] == 2
        assert stats['severity_counts']['medium'] == 1
        assert stats['category'] == 'performance'

    def test_clear_issues(self, detector):
        """問題クリアのテスト"""
        detector.create_issue("Issue", "desc", "file.java", 1)
        assert len(detector._issues) == 1

        detector.clear_issues()
        assert len(detector._issues) == 0


class TestDetectorRegistry:
    """DetectorRegistry クラスのテスト"""

    @pytest.fixture
    def registry(self):
        """レジストリを作成"""
        return DetectorRegistry()

    @pytest.fixture
    def detector1(self):
        return DummyDetector(name="Detector1")

    @pytest.fixture
    def detector2(self):
        return DummyDetector(name="Detector2")

    def test_register_detector(self, registry, detector1):
        """検出器登録のテスト"""
        registry.register(detector1)

        retrieved = registry.get_detector("Detector1")
        assert retrieved == detector1

    def test_register_duplicate_detector(self, registry, detector1):
        """重複検出器登録のテスト"""
        registry.register(detector1)

        # 同じ名前で再登録しようとするとエラー
        detector1_copy = DummyDetector(name="Detector1")
        with pytest.raises(ValueError, match="already registered"):
            registry.register(detector1_copy)

    def test_unregister_detector(self, registry, detector1):
        """検出器登録解除のテスト"""
        registry.register(detector1)
        assert registry.get_detector("Detector1") is not None

        registry.unregister("Detector1")
        assert registry.get_detector("Detector1") is None

    def test_unregister_nonexistent_detector(self, registry):
        """存在しない検出器の登録解除テスト"""
        # 存在しない検出器を登録解除してもエラーにならない
        registry.unregister("NonExistent")
        # 何も起こらないことを確認
        assert registry.get_detector("NonExistent") is None

    def test_get_all_detectors(self, registry, detector1, detector2):
        """全検出器取得のテスト"""
        registry.register(detector1)
        registry.register(detector2)

        detectors = registry.get_all_detectors()
        assert len(detectors) == 2
        assert detector1 in detectors
        assert detector2 in detectors

    def test_get_enabled_detectors(self, registry, detector1):
        """有効な検出器のみ取得のテスト"""
        disabled_detector = DisabledDetector()

        registry.register(detector1)
        registry.register(disabled_detector)

        enabled = registry.get_enabled_detectors()
        assert len(enabled) == 1
        assert detector1 in enabled
        assert disabled_detector not in enabled

    def test_run_all(self, registry, detector1, detector2):
        """全検出器実行のテスト"""
        registry.register(detector1)
        registry.register(detector2)

        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text="test",
                file_path="test.java",
                line_number=1
            )
        ]

        issues = registry.run_all(queries)

        # 各検出器が1つずつIssueを返すので合計2つ
        assert len(issues) == 2

    def test_run_all_with_error(self, registry):
        """エラーハンドリング付き実行のテスト"""
        class ErrorDetector(DummyDetector):
            def detect(self, queries):
                raise Exception("Test error")

        error_detector = ErrorDetector(name="ErrorDetector")
        good_detector = DummyDetector(name="GoodDetector")

        registry.register(error_detector)
        registry.register(good_detector)

        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text="test",
                file_path="test.java",
                line_number=1
            )
        ]

        # エラーが発生しても他の検出器は実行される
        issues = registry.run_all(queries)
        assert len(issues) == 1  # GoodDetectorのみ成功


class TestBaseDetectorAbstractMethods:
    """Test abstract method requirements of BaseDetector"""

    def test_cannot_instantiate_without_implementing_abstract_methods(self):
        """Test that BaseDetector cannot be instantiated without implementing abstract methods"""
        # Trying to instantiate a class that doesn't implement all abstract methods
        with pytest.raises(TypeError):
            class IncompleteDetector(BaseDetector):
                # Missing get_name, get_severity, get_category, detect
                pass

            IncompleteDetector()

    def test_must_implement_get_name(self):
        """Test that get_name must be implemented"""
        with pytest.raises(TypeError):
            class NoGetNameDetector(BaseDetector):
                # Missing get_name
                def get_severity(self) -> Severity:
                    return Severity.LOW

                def get_category(self) -> IssueCategory:
                    return IssueCategory.BEST_PRACTICE

                def detect(self, queries):
                    return []

            NoGetNameDetector()

    def test_must_implement_get_severity(self):
        """Test that get_severity must be implemented"""
        with pytest.raises(TypeError):
            class NoGetSeverityDetector(BaseDetector):
                def get_name(self) -> str:
                    return "Test"
                # Missing get_severity

                def get_category(self) -> IssueCategory:
                    return IssueCategory.BEST_PRACTICE

                def detect(self, queries):
                    return []

            NoGetSeverityDetector()

    def test_must_implement_get_category(self):
        """Test that get_category must be implemented"""
        with pytest.raises(TypeError):
            class NoGetCategoryDetector(BaseDetector):
                def get_name(self) -> str:
                    return "Test"

                def get_severity(self) -> Severity:
                    return Severity.LOW
                # Missing get_category

                def detect(self, queries):
                    return []

            NoGetCategoryDetector()

    def test_must_implement_detect(self):
        """Test that detect must be implemented"""
        with pytest.raises(TypeError):
            class NoDetectDetector(BaseDetector):
                def get_name(self) -> str:
                    return "Test"

                def get_severity(self) -> Severity:
                    return Severity.LOW

                def get_category(self) -> IssueCategory:
                    return IssueCategory.BEST_PRACTICE
                # Missing detect

            NoDetectDetector()
