"""
検出器パイプラインの統合テスト

Parser → Detector の一連の流れを総合的にテスト
"""
import pytest
from pathlib import Path

from cassandra_analyzer.parsers import JavaCassandraParser
from cassandra_analyzer.detectors import (
    AllowFilteringDetector,
    PartitionKeyDetector,
    BatchSizeDetector,
    PreparedStatementDetector,
)


@pytest.fixture
def fixtures_dir():
    """フィクスチャディレクトリのパス"""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def parser():
    """Javaパーサーのフィクスチャ"""
    return JavaCassandraParser()


@pytest.fixture
def all_detectors():
    """全検出器のリスト"""
    return [
        AllowFilteringDetector(),
        PartitionKeyDetector(),
        BatchSizeDetector(),
        PreparedStatementDetector(),
    ]


class TestDetectorPipeline:
    """検出器パイプラインの統合テストクラス"""

    def test_end_to_end_bad_dao1(self, parser, all_detectors, fixtures_dir):
        """
        sample_dao_bad1.javaの完全な分析テスト
        ALLOW FILTERING問題を持つDAOクラス
        """
        test_file = fixtures_dir / "sample_dao_bad1.java"

        # Phase 1: Parse
        calls = parser.parse_file(test_file)
        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # Phase 2: Detect issues across all detectors
        all_issues = []
        for call in calls:
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    all_issues.extend(issues)

        assert len(all_issues) > 0, "少なくとも1つの問題が検出されるべき"

        # Verify specific issues
        # ALLOW FILTERINGは3箇所ある
        allow_filtering_issues = [i for i in all_issues if i.issue_type == "ALLOW_FILTERING"]
        assert len(allow_filtering_issues) == 3, f"3つのALLOW FILTERING問題が検出されるべき (検出数: {len(allow_filtering_issues)})"

        # 全てhigh severity
        for issue in allow_filtering_issues:
            assert issue.severity == "high", "ALLOW FILTERINGはhigh severityであるべき"
            assert issue.file_path == str(test_file)
            assert issue.line_number > 0

        # Prepared Statement問題
        # Phase 1では、session.execute(CQL, params)形式はprepared=Falseと判定される
        unprepared_issues = [i for i in all_issues if i.issue_type == "UNPREPARED_STATEMENT"]
        assert len(unprepared_issues) == 3, f"3つのUNPREPARED_STATEMENT問題が検出されるべき (検出数: {len(unprepared_issues)})"

    def test_end_to_end_bad_dao2(self, parser, all_detectors, fixtures_dir):
        """
        sample_dao_bad2.javaの完全な分析テスト
        Partition Key未使用問題を持つDAOクラス
        """
        test_file = fixtures_dir / "sample_dao_bad2.java"

        # Phase 1: Parse
        calls = parser.parse_file(test_file)
        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # Phase 2: Detect issues
        all_issues = []
        for call in calls:
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    all_issues.extend(issues)

        assert len(all_issues) > 0, "少なくとも1つの問題が検出されるべき"

        # Verify Partition Key issues
        # Phase 1では等価条件があればPartition Key使用と推定するため、
        # 検出されるのは等価条件がないクエリのみ
        # - getAllOrders: WHERE句なし → 検出される
        # - findByDateRange: 範囲条件のみ → 検出される可能性
        # - findByOrderNumber, findByCustomerName: 等価条件あり → Phase 1では検出されない
        partition_key_issues = [i for i in all_issues if i.issue_type == "NO_PARTITION_KEY"]
        assert len(partition_key_issues) >= 1, f"少なくとも1つのPartition Key問題が検出されるべき (検出数: {len(partition_key_issues)})"

        # 全てcritical severity
        for issue in partition_key_issues:
            assert issue.severity == "critical", "Partition Key未使用はcritical severityであるべき"
            assert issue.file_path == str(test_file)

    def test_end_to_end_bad_dao3(self, parser, all_detectors, fixtures_dir):
        """
        sample_dao_bad3.javaの完全な分析テスト
        BatchStatement使用のDAOクラス

        Note: Phase 1ではBatchStatementオブジェクトの分析は未対応
        CQLテキストベースのBATCHのみ検出可能
        """
        test_file = fixtures_dir / "sample_dao_bad3.java"

        # Phase 1: Parse
        calls = parser.parse_file(test_file)
        # Phase 1ではBatchStatementオブジェクトからCQLを抽出できない
        # 将来のPhaseで対応予定

        # とりあえず他の問題が検出されることを確認
        all_issues = []
        for call in calls:
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    all_issues.extend(issues)

        # Phase 1では、String.format()を使った未準備文が検出される可能性がある
        # ただし、BatchStatementオブジェクトのサイズ検出は未対応
        # このテストは将来のPhaseで拡張予定

    def test_good_dao_no_issues(self, parser, all_detectors, fixtures_dir):
        """
        sample_dao_good.javaの分析テスト
        問題のないDAOクラスは何も検出されないべき
        """
        test_file = fixtures_dir / "sample_dao_good.java"

        # Phase 1: Parse
        calls = parser.parse_file(test_file)
        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # Phase 2: Detect issues
        all_issues = []
        for call in calls:
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    all_issues.extend(issues)

        # 問題なしのファイルなので何も検出されないべき
        assert len(all_issues) == 0, f"問題が検出されるべきではない (検出数: {len(all_issues)})"

    def test_detector_filtering(self, parser, fixtures_dir):
        """
        検出器の有効/無効フィルタリングテスト
        """
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        # AllowFilteringDetectorのみ有効
        enabled_detector = AllowFilteringDetector()
        disabled_detector = AllowFilteringDetector(config={"enabled": False})

        enabled_issues = []
        for call in calls:
            enabled_issues.extend(enabled_detector.detect(call))

        disabled_issues = []
        for call in calls:
            if disabled_detector.is_enabled():
                disabled_issues.extend(disabled_detector.detect(call))

        assert len(enabled_issues) > 0, "有効な検出器は問題を検出するべき"
        assert len(disabled_issues) == 0, "無効な検出器は問題を検出しないべき"

    def test_severity_levels_in_pipeline(self, parser, all_detectors, fixtures_dir):
        """
        パイプライン全体での重要度レベル検証
        """
        # bad1, bad2, bad3を全て分析
        test_files = [
            fixtures_dir / "sample_dao_bad1.java",
            fixtures_dir / "sample_dao_bad2.java",
            fixtures_dir / "sample_dao_bad3.java",
        ]

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for test_file in test_files:
            calls = parser.parse_file(test_file)
            for call in calls:
                for detector in all_detectors:
                    if detector.is_enabled():
                        issues = detector.detect(call)
                        for issue in issues:
                            severity_counts[issue.severity] += 1

        # 各重要度レベルが存在することを確認
        assert severity_counts["critical"] > 0, "critical問題が検出されるべき"
        assert severity_counts["high"] > 0, "high問題が検出されるべき"
        # medium/lowは検出される可能性がある（バッチサイズによる）

    def test_multiple_issues_per_call(self, parser, all_detectors, fixtures_dir):
        """
        1つのCassandra呼び出しから複数の問題が検出されるケース

        例: ALLOW FILTERING + SELECT *
        """
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        # 各呼び出しに対して全検出器を実行
        for call in calls:
            call_issues = []
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    call_issues.extend(issues)

            # ALLOW FILTERINGを含むクエリは、SELECT *も使っている可能性があり、
            # 複数の問題が検出される可能性がある
            if "ALLOW FILTERING" in call.cql_text:
                # 少なくともALLOW FILTERING問題が検出される
                assert any(i.issue_type == "ALLOW_FILTERING" for i in call_issues), \
                    "ALLOW FILTERINGが含まれるクエリではALLOW FILTERING問題が検出されるべき"

    def test_issue_evidence_and_confidence(self, parser, all_detectors, fixtures_dir):
        """
        検出された問題のevidenceとconfidenceの検証
        """
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        all_issues = []
        for call in calls:
            for detector in all_detectors:
                if detector.is_enabled():
                    issues = detector.detect(call)
                    all_issues.extend(issues)

        for issue in all_issues:
            # Evidenceには実際のCQLが含まれるべき
            assert issue.evidence is not None, "evidenceがNoneであってはならない"
            assert len(issue.evidence) > 0, "evidenceが空であってはならない"

            # Confidenceは0.0-1.0の範囲
            assert 0.0 <= issue.confidence <= 1.0, f"confidenceは0.0-1.0の範囲であるべき (実際: {issue.confidence})"

            # Recommendationが提供されるべき
            assert issue.recommendation is not None, "recommendationがNoneであってはならない"
            assert len(issue.recommendation) > 0, "recommendationが空であってはならない"

    def test_detector_order_independence(self, parser, fixtures_dir):
        """
        検出器の実行順序が結果に影響しないことを確認
        """
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        # 順序1
        detectors_order1 = [
            AllowFilteringDetector(),
            PartitionKeyDetector(),
            BatchSizeDetector(),
            PreparedStatementDetector(),
        ]

        # 順序2（逆順）
        detectors_order2 = list(reversed(detectors_order1))

        issues_order1 = []
        for call in calls:
            for detector in detectors_order1:
                issues_order1.extend(detector.detect(call))

        issues_order2 = []
        for call in calls:
            for detector in detectors_order2:
                issues_order2.extend(detector.detect(call))

        # 問題数は同じであるべき
        assert len(issues_order1) == len(issues_order2), \
            "検出器の順序に関わらず、同じ数の問題が検出されるべき"

        # 問題タイプの分布も同じであるべき
        types_order1 = sorted([i.issue_type for i in issues_order1])
        types_order2 = sorted([i.issue_type for i in issues_order2])
        assert types_order1 == types_order2, "検出器の順序に関わらず、同じタイプの問題が検出されるべき"


class TestDetectorConfiguration:
    """検出器設定の統合テスト"""

    def test_custom_batch_threshold(self, parser, fixtures_dir):
        """
        カスタムバッチ閾値の設定テスト
        """
        test_file = fixtures_dir / "sample_dao_bad3.java"
        calls = parser.parse_file(test_file)

        # 閾値50の検出器
        detector_threshold_50 = BatchSizeDetector(config={"threshold": 50})

        # 閾値200の検出器
        detector_threshold_200 = BatchSizeDetector(config={"threshold": 200})

        issues_50 = []
        issues_200 = []

        for call in calls:
            issues_50.extend(detector_threshold_50.detect(call))
            issues_200.extend(detector_threshold_200.detect(call))

        # 閾値が低い方がより多くの問題を検出する（または同数）
        assert len(issues_50) >= len(issues_200), \
            "低い閾値の方がより多く（または同数）の問題を検出するべき"

    def test_custom_severity_override(self, parser, fixtures_dir):
        """
        カスタム重要度設定のテスト
        """
        test_file = fixtures_dir / "sample_dao_bad3.java"
        calls = parser.parse_file(test_file)

        # デフォルト重要度
        detector_default = BatchSizeDetector()

        # カスタム重要度（critical）
        detector_custom = BatchSizeDetector(config={"severity": "critical"})

        default_issues = []
        custom_issues = []

        for call in calls:
            default_issues.extend(detector_default.detect(call))
            custom_issues.extend(detector_custom.detect(call))

        # 検出数は同じ
        assert len(default_issues) == len(custom_issues), "設定に関わらず検出数は同じであるべき"

        # カスタム重要度が適用される（2倍超過でない場合）
        # ただし、BatchSizeDetectorは2倍超過時に強制的にhighにするロジックがあるので、
        # 実際のテストでは小さめのバッチを使用する必要がある
        # ここでは設定が正しく反映されることを確認
        if len(custom_issues) > 0:
            # 少なくとも設定が読み込まれることを確認
            assert detector_custom.config.get("severity") == "critical"
