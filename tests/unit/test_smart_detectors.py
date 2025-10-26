"""
スマート検出器のユニットテスト
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json

from cassandra_analyzer.detectors import (
    AllowFilteringDetector,
    SmartAllowFilteringDetector,
    SmartPartitionKeyDetector,
)
from cassandra_analyzer.models import CassandraCall, Issue


class TestSmartAllowFilteringDetector:
    """SmartAllowFilteringDetectorのテストクラス"""

    @pytest.fixture
    def detector_no_llm(self):
        """LLMなしの検出器"""
        return SmartAllowFilteringDetector(config={"llm_enabled": False})

    @pytest.fixture
    def detector_with_mock_llm(self):
        """モックLLM付きの検出器"""
        config = {
            "llm_enabled": True,
            "anthropic_api_key": "test-key-123"
        }
        with patch("cassandra_analyzer.detectors.smart_allow_filtering.LLMAnalyzer"):
            detector = SmartAllowFilteringDetector(config=config)
            detector.llm_analyzer = Mock()
            return detector

    @pytest.fixture
    def sample_call_with_allow_filtering(self):
        """ALLOW FILTERINGを含むサンプル呼び出し"""
        return CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="UserDao.java",
            class_name="UserDao",
            method_context="getUserByEmail",
        )

    def test_initialization_without_llm(self):
        """LLMなしで初期化"""
        detector = SmartAllowFilteringDetector(config={"llm_enabled": False})
        assert detector.llm_enabled is False
        assert detector.detector_name == "SmartAllowFilteringDetector"

    def test_initialization_with_llm(self):
        """LLM付きで初期化"""
        config = {
            "llm_enabled": True,
            "anthropic_api_key": "test-key-123"
        }
        with patch("cassandra_analyzer.detectors.smart_allow_filtering.LLMAnalyzer"):
            detector = SmartAllowFilteringDetector(config=config)
            assert detector.llm_enabled is True

    def test_initialization_without_api_key(self):
        """APIキーなしで初期化（LLM無効化）"""
        config = {"llm_enabled": True}
        detector = SmartAllowFilteringDetector(config=config)
        assert detector.llm_enabled is False

    def test_detect_without_llm(self, detector_no_llm, sample_call_with_allow_filtering):
        """LLMなしでの検出（基底クラスの動作）"""
        issues = detector_no_llm.detect(sample_call_with_allow_filtering)

        assert len(issues) == 1
        assert issues[0].issue_type == "ALLOW_FILTERING"
        assert issues[0].severity == "high"

    def test_detect_with_llm_justified_use(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """LLMが正当な使用と判断した場合"""
        # LLMが正当な使用と判断するレスポンスを設定
        mock_response = json.dumps({
            "justified": True,
            "justification": "Low cardinality administrative query",
            "impact": "Minimal - small table with infrequent access",
            "alternatives": []
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

        assert len(issues) == 1
        issue = issues[0]
        # 信頼度が下がり、重要度が低くなる（1.0 - 0.4 = 0.6）
        assert issue.confidence < 0.7
        assert issue.severity == "low"
        # 正当化の理由が証拠に含まれる
        assert any("Low cardinality" in evidence for evidence in issue.evidence)

    def test_detect_with_llm_unjustified_use(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """LLMが正当でない使用と判断した場合"""
        # LLMが正当でないと判断するレスポンスを設定
        mock_response = json.dumps({
            "justified": False,
            "justification": "",
            "impact": "High - full table scan on large dataset",
            "alternatives": [
                "Create a secondary index on email column",
                "Create a materialized view with email as partition key"
            ]
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

        assert len(issues) == 1
        issue = issues[0]
        # 信頼度と重要度は維持される
        assert issue.confidence >= 0.5
        # LLMの推奨事項が含まれる
        assert "Enhanced Recommendation" in issue.recommendation
        assert "secondary index" in issue.recommendation.lower()

    def test_detect_with_llm_error(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """LLM分析がエラーの場合（元の検出結果を返す）"""
        detector_with_mock_llm.llm_analyzer.client.analyze_code.side_effect = Exception("API Error")

        issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

        # エラーでも基本的な検出は行われる
        assert len(issues) == 1
        assert issues[0].issue_type == "ALLOW_FILTERING"

    def test_detect_with_markdown_json_response(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """マークダウン形式のJSONレスポンスを処理"""
        # マークダウンコードブロック形式のレスポンス
        mock_response = """```json
{
    "justified": false,
    "justification": "",
    "impact": "Medium",
    "alternatives": ["Use secondary index"]
}
```"""

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

        assert len(issues) == 1
        assert "Enhanced Recommendation" in issues[0].recommendation

    def test_detect_with_plain_markdown_response(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """プレーンマークダウン形式（```json なし）のレスポンスを処理"""
        # ``` のみのマークダウンコードブロック形式
        mock_response = """```
{
    "justified": false,
    "justification": "",
    "impact": "High",
    "alternatives": ["Create materialized view"]
}
```"""

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

        assert len(issues) == 1
        assert "Enhanced Recommendation" in issues[0].recommendation

    def test_enhance_with_exception_in_processing(
        self, detector_with_mock_llm, sample_call_with_allow_filtering
    ):
        """LLM分析の処理中に例外が発生した場合"""
        from unittest.mock import Mock, patch

        # 基本検出結果を取得
        base_issues = AllowFilteringDetector().detect(sample_call_with_allow_filtering)

        # _is_justified_use が例外を投げるようにモック
        with patch.object(
            detector_with_mock_llm,
            '_is_justified_use',
            side_effect=Exception("Processing error")
        ):
            # 正常なLLMレスポンスを設定
            mock_response = json.dumps({
                "justified": False,
                "justification": "",
                "impact": "High",
                "alternatives": []
            })
            detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

            issues = detector_with_mock_llm.detect(sample_call_with_allow_filtering)

            # 例外が発生しても元の問題が返される
            assert len(issues) == 1
            assert issues[0].issue_type == "ALLOW_FILTERING"


class TestSmartPartitionKeyDetector:
    """SmartPartitionKeyDetectorのテストクラス"""

    @pytest.fixture
    def detector_no_llm(self):
        """LLMなしの検出器"""
        return SmartPartitionKeyDetector(config={"llm_enabled": False})

    @pytest.fixture
    def detector_with_mock_llm(self):
        """モックLLM付きの検出器"""
        config = {
            "llm_enabled": True,
            "anthropic_api_key": "test-key-123"
        }
        with patch("cassandra_analyzer.detectors.smart_partition_key.LLMAnalyzer"):
            detector = SmartPartitionKeyDetector(config=config)
            detector.llm_analyzer = Mock()
            return detector

    @pytest.fixture
    def detector_with_schema(self):
        """スキーマ情報付きの検出器"""
        schema = """
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email TEXT,
    name TEXT
);
"""
        config = {
            "llm_enabled": False,
            "table_schema": schema
        }
        return SmartPartitionKeyDetector(config=config)

    @pytest.fixture
    def sample_call_without_partition_key(self):
        """パーティションキーなしのサンプル呼び出し（範囲検索）"""
        return CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users WHERE created_at > ?",
            line_number=15,
            is_prepared=True,
            consistency_level="ONE",
            file_path="UserDao.java",
            class_name="UserDao",
            method_context="findRecent",
        )

    def test_initialization_without_llm(self):
        """LLMなしで初期化"""
        detector = SmartPartitionKeyDetector(config={"llm_enabled": False})
        assert detector.llm_enabled is False
        assert detector.detector_name == "SmartPartitionKeyDetector"

    def test_initialization_with_schema(self, detector_with_schema):
        """スキーマ情報付きで初期化"""
        assert detector_with_schema.table_schema is not None
        assert "CREATE TABLE" in detector_with_schema.table_schema

    def test_detect_without_llm(
        self, detector_no_llm, sample_call_without_partition_key
    ):
        """LLMなしでの検出（基底クラスの動作）"""
        issues = detector_no_llm.detect(sample_call_without_partition_key)

        assert len(issues) == 1
        assert issues[0].issue_type == "NO_PARTITION_KEY"
        assert issues[0].severity == "critical"

    def test_detect_with_llm_schema_inference(
        self, detector_with_mock_llm, sample_call_without_partition_key
    ):
        """LLMがスキーマを推測した場合"""
        # LLMがスキーマを推測するレスポンスを設定
        mock_response = json.dumps({
            "inferred_schema": {
                "partition_keys": ["user_id"],
                "clustering_keys": [],
                "reasoning": "Based on query pattern, user_id is likely the partition key"
            },
            "current_issue": "Query filters by email which is not the partition key",
            "recommended_schema": "CREATE TABLE users_by_email (email TEXT PRIMARY KEY, user_id UUID, ...)",
            "query_rewrite": "SELECT * FROM users_by_email WHERE email = ?",
            "materialized_view_suggestion": "CREATE MATERIALIZED VIEW users_by_email AS ..."
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        assert len(issues) == 1
        issue = issues[0]
        # 推測されたパーティションキーが証拠に含まれる
        assert any("user_id" in evidence for evidence in issue.evidence)
        # LLMの推奨スキーマが含まれる
        assert "Enhanced Data Model Analysis" in issue.recommendation
        assert "users_by_email" in issue.recommendation

    def test_detect_with_llm_mv_suggestion(
        self, detector_with_mock_llm, sample_call_without_partition_key
    ):
        """LLMがMaterialized Viewを提案した場合"""
        mock_response = json.dumps({
            "inferred_schema": {
                "partition_keys": ["user_id"],
                "clustering_keys": ["created_at"],
                "reasoning": "Table appears to be partitioned by user_id"
            },
            "current_issue": "Email-based query requires full scan",
            "recommended_schema": "",
            "query_rewrite": "",
            "materialized_view_suggestion": "CREATE MATERIALIZED VIEW users_by_email AS SELECT * FROM users WHERE email IS NOT NULL PRIMARY KEY (email, user_id)"
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        assert len(issues) == 1
        issue = issues[0]
        # MVの提案が含まれる
        assert "Materialized View Option" in issue.recommendation

    def test_detect_with_llm_error(
        self, detector_with_mock_llm, sample_call_without_partition_key
    ):
        """LLM分析がエラーの場合（元の検出結果を返す）"""
        detector_with_mock_llm.llm_analyzer.client.analyze_code.side_effect = Exception("API Error")

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        # エラーでも基本的な検出は行われる
        assert len(issues) == 1
        assert issues[0].issue_type == "NO_PARTITION_KEY"

    def test_confidence_boost_with_schema_inference(
        self, detector_with_mock_llm, sample_call_without_partition_key
    ):
        """スキーマ推測がある場合の信頼度向上"""
        mock_response = json.dumps({
            "inferred_schema": {
                "partition_keys": ["user_id"],
                "clustering_keys": [],
                "reasoning": "Clear partition key pattern detected"
            },
            "current_issue": "Not using partition key",
            "recommended_schema": "",
            "query_rewrite": "",
            "materialized_view_suggestion": ""
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        assert len(issues) == 1
        # 信頼度が向上している
        assert issues[0].confidence > 0.9

    def test_initialization_with_llm_failure(self):
        """LLMAnalyzer初期化失敗時の処理"""
        with patch("cassandra_analyzer.detectors.smart_partition_key.LLMAnalyzer", side_effect=Exception("Init failed")):
            detector = SmartPartitionKeyDetector(config={"anthropic_api_key": "test_key"})

            # LLMが無効化される (lines 45-47)
            assert detector.llm_enabled is False

    def test_detect_with_schema_context(self, detector_with_schema, sample_call_without_partition_key):
        """スキーマ情報付きでの検出（LLMなし）"""
        # LLMなしでスキーマ情報がある場合
        issues = detector_with_schema.detect(sample_call_without_partition_key)

        assert len(issues) == 1
        assert issues[0].issue_type == "NO_PARTITION_KEY"

    def test_detect_with_llm_and_schema(self, detector_with_mock_llm, sample_call_without_partition_key):
        """LLMとスキーマ情報の両方がある場合"""
        # スキーマ情報を設定
        detector_with_mock_llm.table_schema = """
        CREATE TABLE orders (
            order_id UUID PRIMARY KEY,
            user_id UUID,
            order_date TIMESTAMP
        );
        """

        # LLMレスポンス
        mock_response = json.dumps({
            "inferred_schema": {
                "table_name": "orders",
                "partition_keys": ["order_id"],
                "clustering_keys": [],
                "reasoning": "Test"
            },
            "current_issue": "Missing partition key",
            "recommended_schema": "",
            "query_rewrite": "",
            "materialized_view_suggestion": ""
        })

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        # line 151がカバーされる
        assert len(issues) == 1

    def test_detect_with_llm_json_markdown(self, detector_with_mock_llm, sample_call_without_partition_key):
        """LLM分析でマークダウンJSONレスポンスを処理"""
        # ```json ... ```形式のレスポンス
        mock_response = """```json
{
    "inferred_schema": {
        "table_name": "orders",
        "partition_keys": ["user_id"],
        "clustering_keys": [],
        "reasoning": "Inferred from query"
    },
    "current_issue": "Missing partition key",
    "recommended_schema": "Use user_id",
    "query_rewrite": "",
    "materialized_view_suggestion": ""
}
```"""

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        # line 191がカバーされる
        assert len(issues) == 1

    def test_detect_with_llm_plain_markdown(self, detector_with_mock_llm, sample_call_without_partition_key):
        """LLM分析でプレーンマークダウンレスポンスを処理"""
        # ``` ... ```形式のレスポンス（jsonなし）
        mock_response = """```
{
    "inferred_schema": {
        "table_name": "orders",
        "partition_keys": ["order_id"],
        "clustering_keys": [],
        "reasoning": "Inferred"
    },
    "current_issue": "Missing partition key",
    "recommended_schema": "",
    "query_rewrite": "",
    "materialized_view_suggestion": "CREATE MV"
}
```"""

        detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

        issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

        # line 193がカバーされる
        assert len(issues) == 1

    def test_detect_with_llm_enhancement_error(self, detector_with_mock_llm, sample_call_without_partition_key):
        """LLM分析での拡張処理中のエラー"""
        # _get_enhanced_recommendation が例外を投げるようにモック
        with patch.object(
            detector_with_mock_llm,
            '_get_enhanced_recommendation',
            side_effect=Exception("Processing error")
        ):
            # 正常なLLMレスポンスを設定
            mock_response = json.dumps({
                "inferred_schema": {
                    "table_name": "test",
                    "partition_keys": ["id"],
                    "clustering_keys": [],
                    "reasoning": "Test"
                },
                "current_issue": "Test",
                "recommended_schema": "",
                "query_rewrite": "",
                "materialized_view_suggestion": ""
            })
            detector_with_mock_llm.llm_analyzer.client.analyze_code.return_value = mock_response

            issues = detector_with_mock_llm.detect(sample_call_without_partition_key)

            # 例外が発生しても元の問題が返される (lines 127-130)
            assert len(issues) == 1
            assert issues[0].issue_type == "NO_PARTITION_KEY"


class TestSmartDetectorIntegration:
    """スマート検出器の統合テスト"""

    def test_both_detectors_work_without_llm(self):
        """両方の検出器がLLMなしで動作する"""
        allow_filtering_detector = SmartAllowFilteringDetector(
            config={"llm_enabled": False}
        )
        partition_key_detector = SmartPartitionKeyDetector(
            config={"llm_enabled": False}
        )

        # ALLOW FILTERING検出用
        call1 = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )

        # Partition Key未使用検出用（範囲検索）
        call2 = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users WHERE created_at > ?",
            line_number=15,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )

        # 各検出器で問題を検出
        allow_filtering_issues = allow_filtering_detector.detect(call1)
        partition_key_issues = partition_key_detector.detect(call2)

        # ALLOW FILTERINGは必ず検出される
        assert len(allow_filtering_issues) == 1
        # Partition Key未使用も検出される
        assert len(partition_key_issues) == 1

    def test_detector_fallback_on_llm_failure(self):
        """LLM失敗時に基底検出器にフォールバックする"""
        config = {
            "llm_enabled": True,
            "anthropic_api_key": "test-key-123"
        }

        with patch("cassandra_analyzer.detectors.smart_allow_filtering.LLMAnalyzer") as mock_llm_class:
            # LLM初期化を失敗させる
            mock_llm_class.side_effect = Exception("LLM Init Error")

            detector = SmartAllowFilteringDetector(config=config)
            # LLMが無効化される
            assert detector.llm_enabled is False

            # 基本的な検出は動作する
            call = CassandraCall(
                method_name="execute",
                cql_text="SELECT * FROM users WHERE id = ? ALLOW FILTERING",
                line_number=10,
                is_prepared=False,
                consistency_level=None,
                file_path="test.java",
            )

            issues = detector.detect(call)
            assert len(issues) == 1
