"""
Tests for HybridAnalysisEngine
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os

# conftest.pyでパス設定済み。直接インポート
from cassandra_analyzer.analyzers.hybrid_analyzer import HybridAnalysisEngine
from cassandra_analyzer.models import AnalysisConfidence
from cassandra_analyzer.models.hybrid_result import HybridAnalysisResult
from cassandra_analyzer.models import Issue


@pytest.fixture
def sample_java_file(tmp_path):
    """テスト用のJavaファイルを作成"""
    java_file = tmp_path / "TestDAO.java"
    java_content = """
package com.example;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;

public class TestDAO {
    private final Session session;

    // CQL定数（Phase 1のパーサーが認識するパターン）
    private static final String FIND_BY_EMAIL_CQL = "SELECT * FROM users WHERE email = ? ALLOW FILTERING";
    private static final String INSERT_USER_CQL = "INSERT INTO users (id, name) VALUES (?, ?)";

    public TestDAO(Session session) {
        this.session = session;
    }

    public ResultSet getUserById(String userId) {
        ResultSet rs = session.execute(FIND_BY_EMAIL_CQL, userId);
        return rs;
    }

    public void insertUser(String id, String name) {
        session.execute(INSERT_USER_CQL, id, name);
    }
}
"""
    java_file.write_text(java_content, encoding="utf-8")
    return str(java_file)


@pytest.fixture
def engine_no_llm():
    """LLM無効のエンジン"""
    return HybridAnalysisEngine(enable_llm=False)


@pytest.fixture
def engine_with_mock_llm():
    """モックLLMありのエンジン"""
    engine = HybridAnalysisEngine(api_key="test-key", enable_llm=True)
    # LLMクライアントをモックに置き換え
    engine.anthropic_client = Mock()
    engine.llm_analyzer = Mock()
    return engine


class TestHybridAnalysisEngineInit:
    """初期化のテスト"""

    def test_init_without_llm(self):
        """LLM無効で初期化"""
        engine = HybridAnalysisEngine(enable_llm=False)

        assert engine.parser is not None
        assert len(engine.detectors) == 4  # 4つの検出器
        assert engine.enable_llm is False
        assert engine.anthropic_client is None
        assert engine.llm_analyzer is None

    def test_init_with_llm(self):
        """LLM有効で初期化"""
        engine = HybridAnalysisEngine(api_key="test-key", enable_llm=True)

        assert engine.enable_llm is True
        assert engine.anthropic_client is not None
        assert engine.llm_analyzer is not None

    def test_init_with_custom_threshold(self):
        """カスタム閾値で初期化"""
        engine = HybridAnalysisEngine(
            api_key="test-key",
            enable_llm=True,
            llm_threshold_severity="medium"
        )

        assert engine.llm_threshold_severity == "medium"


class TestShouldUseLLM:
    """LLM使用判定のテスト"""

    @pytest.fixture
    def sample_issue(self):
        """サンプル問題"""
        return Issue(
            detector_name="TestDetector",
            issue_type="TEST",
            severity="high",
            file_path="/test.java",
            line_number=10,
            message="Test message",
            cql_text="SELECT * FROM test",
            recommendation="Fix it"
        )

    def test_should_not_use_llm_when_disabled(self, engine_no_llm, sample_issue):
        """LLM無効時はLLM使用しない"""
        assert not engine_no_llm._should_use_llm(sample_issue, "standard")
        assert not engine_no_llm._should_use_llm(sample_issue, "comprehensive")

    def test_quick_mode_no_llm(self, engine_with_mock_llm, sample_issue):
        """quickモードはLLM使用しない"""
        assert not engine_with_mock_llm._should_use_llm(sample_issue, "quick")

    def test_critical_only_mode(self, engine_with_mock_llm):
        """critical_onlyモードはcriticalのみLLM使用"""
        critical_issue = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="critical",
            file_path="/test.java",
            line_number=10,
            message="Critical",
            cql_text="SELECT *",
            recommendation="Fix"
        )
        high_issue = Issue(
            detector_name="Test",
            issue_type="TEST",
            severity="high",
            file_path="/test.java",
            line_number=10,
            message="High",
            cql_text="SELECT *",
            recommendation="Fix"
        )

        assert engine_with_mock_llm._should_use_llm(critical_issue, "critical_only")
        assert not engine_with_mock_llm._should_use_llm(high_issue, "critical_only")

    def test_comprehensive_mode_all_llm(self, engine_with_mock_llm, sample_issue):
        """comprehensiveモードは全てLLM使用"""
        assert engine_with_mock_llm._should_use_llm(sample_issue, "comprehensive")

    def test_standard_mode_by_severity(self, engine_with_mock_llm):
        """standardモードは重要度でフィルタ"""
        # デフォルト閾値は "high"
        critical_issue = Issue(
            detector_name="Test", issue_type="TEST", severity="critical",
            file_path="/test.java", line_number=10, message="Critical",
            cql_text="SELECT *", recommendation="Fix"
        )
        high_issue = Issue(
            detector_name="Test", issue_type="TEST", severity="high",
            file_path="/test.java", line_number=10, message="High",
            cql_text="SELECT *", recommendation="Fix"
        )
        medium_issue = Issue(
            detector_name="Test", issue_type="TEST", severity="medium",
            file_path="/test.java", line_number=10, message="Medium",
            cql_text="SELECT *", recommendation="Fix"
        )

        # high以上（critical, high）のみTrue
        assert engine_with_mock_llm._should_use_llm(critical_issue, "standard")
        assert engine_with_mock_llm._should_use_llm(high_issue, "standard")
        assert not engine_with_mock_llm._should_use_llm(medium_issue, "standard")


class TestRunStaticAnalysis:
    """静的解析実行のテスト"""

    @pytest.mark.asyncio
    async def test_run_static_analysis_success(self, engine_no_llm, sample_java_file):
        """静的解析が正常に実行される"""
        results = await engine_no_llm._run_static_analysis(sample_java_file)

        # 少なくとも1つの問題が検出される（ALLOW FILTERING）
        assert len(results) > 0

        # Phase 1のIssueクラスとPhase 2のIssueクラスは名前空間が異なるため、型名でチェック
        for i, issue in enumerate(results):
            assert type(issue).__name__ == "Issue", f"Result {i} is not Issue-like: type={type(issue).__name__}"
            assert hasattr(issue, "detector_name"), "Issue should have detector_name"
            assert hasattr(issue, "issue_type"), "Issue should have issue_type"
            assert hasattr(issue, "severity"), "Issue should have severity"

    @pytest.mark.asyncio
    async def test_run_static_analysis_nonexistent_file(self, engine_no_llm):
        """存在しないファイルの場合空リストを返す"""
        results = await engine_no_llm._run_static_analysis("/nonexistent/file.java")

        assert results == []


class TestAnalyzeCodeQuickMode:
    """analyze_code quick モードのテスト"""

    @pytest.mark.asyncio
    async def test_analyze_code_quick_mode(self, engine_no_llm, sample_java_file):
        """quickモードで分析実行"""
        results = await engine_no_llm.analyze_code(sample_java_file, "quick")

        assert isinstance(results, list)
        assert len(results) > 0

        # 全て HybridAnalysisResult
        assert all(isinstance(r, HybridAnalysisResult) for r in results)

        # 静的解析のみ（LLM分析なし）
        for result in results:
            assert result.has_static_detection
            assert not result.has_llm_detection
            assert result.confidence_level == AnalysisConfidence.CERTAIN


class TestGetStatistics:
    """統計情報取得のテスト"""

    def test_get_statistics_empty_results(self, engine_no_llm):
        """空の結果リストで統計情報を取得"""
        stats = engine_no_llm.get_statistics([])

        assert stats["total_issues"] == 0
        assert stats["detection_sources"]["static_only"] == 0
        assert stats["detection_sources"]["llm_only"] == 0
        assert stats["detection_sources"]["hybrid"] == 0
        assert stats["average_confidence_score"] == 0

    def test_get_statistics_with_results(self, engine_no_llm):
        """結果ありで統計情報を取得"""
        # テストデータ作成
        issue1 = Issue(
            detector_name="Test1", issue_type="TEST", severity="high",
            file_path="/test.java", line_number=10, message="Test1",
            cql_text="SELECT *", recommendation="Fix"
        )
        issue2 = Issue(
            detector_name="Test2", issue_type="TEST", severity="medium",
            file_path="/test.java", line_number=20, message="Test2",
            cql_text="SELECT *", recommendation="Fix"
        )

        result1 = HybridAnalysisResult.from_static_only(issue1)
        result2 = HybridAnalysisResult.from_llm_only(
            issue2,
            llm_details={"analysis": "test"},
            llm_confidence=0.85
        )

        stats = engine_no_llm.get_statistics([result1, result2])

        assert stats["total_issues"] == 2
        assert stats["detection_sources"]["static_only"] == 1
        assert stats["detection_sources"]["llm_only"] == 1
        assert stats["detection_sources"]["hybrid"] == 0
        assert stats["average_confidence_score"] > 0

        # 信頼度分布
        assert stats["confidence_distribution"]["certain"] == 1
        assert stats["confidence_distribution"]["medium"] == 1

        # 重要度分布
        assert stats["severity_distribution"]["high"] == 1
        assert stats["severity_distribution"]["medium"] == 1


class TestAnalyzeCodeWithMockedLLM:
    """LLMモックを使った分析テスト"""

    @pytest.mark.asyncio
    async def test_analyze_code_standard_mode_with_llm(
        self,
        engine_with_mock_llm,
        sample_java_file
    ):
        """standardモードでLLM分析を含む"""
        # LLM応答をモック
        engine_with_mock_llm.anthropic_client.analyze_code = Mock(return_value="""{
            "analysis": "This is a test analysis",
            "confidence": 0.90,
            "fix_suggestions": ["Use materialized view"],
            "impact_scope": {"methods": ["getUserById"]},
            "reasoning": "Test reasoning"
        }""")

        results = await engine_with_mock_llm.analyze_code(
            sample_java_file,
            "standard"
        )

        assert len(results) > 0

        # 少なくとも1つの結果がLLM分析を含む可能性
        # （重要度がhigh以上の場合）
        high_severity_results = [
            r for r in results
            if r.issue.severity in ["critical", "high"]
        ]

        if high_severity_results:
            # LLMクライアントが呼ばれたことを確認
            assert engine_with_mock_llm.anthropic_client.analyze_code.called


class TestBuildPrompts:
    """プロンプト構築のテスト"""

    def test_build_deep_analysis_prompt(self, engine_no_llm):
        """深い分析用プロンプトが正しく構築される"""
        issue = Issue(
            detector_name="TestDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="/test.java",
            line_number=42,
            message="Found ALLOW FILTERING",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            recommendation="Create materialized view"
        )

        code = "public class Test { }"
        prompt = engine_no_llm._build_deep_analysis_prompt(code, issue)

        # プロンプトに必要な情報が含まれているか確認
        assert "ALLOW_FILTERING" in prompt
        assert "high" in prompt
        assert "/test.java:42" in prompt
        assert "SELECT * FROM users" in prompt
        assert "public class Test" in prompt

    def test_build_semantic_analysis_prompt(self, engine_no_llm):
        """意味解析用プロンプトが正しく構築される"""
        code = "public class TestDAO { }"
        file_path = "/test/TestDAO.java"

        prompt = engine_no_llm._build_semantic_analysis_prompt(code, file_path)

        # プロンプトに必要な情報が含まれているか確認
        assert "データモデル設計" in prompt or "data model" in prompt.lower()
        assert "public class TestDAO" in prompt


class TestParseResponse:
    """レスポンス解析のテスト"""

    def test_parse_llm_response_valid_json(self, engine_no_llm):
        """有効なJSONレスポンスを解析"""
        response = """{
            "analysis": "Test analysis",
            "confidence": 0.85,
            "fix_suggestions": ["Fix 1", "Fix 2"],
            "impact_scope": {"methods": ["test"]},
            "reasoning": "Because"
        }"""

        result = engine_no_llm._parse_llm_response(response)

        assert result["analysis"] == "Test analysis"
        assert result["confidence"] == 0.85
        assert len(result["fix_suggestions"]) == 2
        assert "methods" in result["impact_scope"]

    def test_parse_llm_response_invalid_json(self, engine_no_llm):
        """無効なJSONレスポンスでもフォールバック"""
        response = "This is not a JSON response"

        result = engine_no_llm._parse_llm_response(response)

        assert "analysis" in result
        assert result["confidence"] == 0.70  # デフォルト値
        assert result["fix_suggestions"] == []

    def test_parse_semantic_response_valid(self, engine_no_llm):
        """有効な意味解析レスポンスを解析"""
        response = """[
            {
                "issue_type": "DATA_MODEL_ISSUE",
                "severity": "high",
                "line_number": 45,
                "message": "Inefficient partition key",
                "cql_text": "SELECT * FROM users",
                "recommendation": "Use composite partition key",
                "confidence": 0.85,
                "fix_suggestions": ["Redesign schema"],
                "impact_scope": {}
            }
        ]"""

        results = engine_no_llm._parse_semantic_response(response, "/test.java")

        assert len(results) == 1
        assert isinstance(results[0], HybridAnalysisResult)
        assert results[0].issue.issue_type == "DATA_MODEL_ISSUE"
        assert results[0].confidence_level == AnalysisConfidence.MEDIUM

    def test_parse_semantic_response_empty_array(self, engine_no_llm):
        """空配列レスポンスの場合"""
        response = "[]"

        results = engine_no_llm._parse_semantic_response(response, "/test.java")

        assert results == []

    def test_parse_semantic_response_invalid(self, engine_no_llm):
        """無効なレスポンスの場合"""
        response = "Invalid response"

        results = engine_no_llm._parse_semantic_response(response, "/test.java")

        assert results == []


class TestComprehensiveMode:
    """comprehensiveモードのテスト（LLM semantic analysis）"""

    @pytest.mark.asyncio
    async def test_analyze_code_comprehensive_mode(self, engine_with_mock_llm, sample_java_file):
        """comprehensiveモードでLLM semantic analysisが実行される"""
        # LLM semantic analysis応答をモック
        engine_with_mock_llm.anthropic_client.analyze_code = Mock(side_effect=[
            # 最初の呼び出し（deep analysis）
            '{"analysis": "Deep analysis", "confidence": 0.90, "fix_suggestions": [], "impact_scope": {}, "reasoning": "Test"}',
            # 2回目の呼び出し（semantic analysis）
            '[]'  # 問題なし
        ])

        results = await engine_with_mock_llm.analyze_code(sample_java_file, "comprehensive")

        # LLMクライアントが複数回呼ばれたことを確認
        assert engine_with_mock_llm.anthropic_client.analyze_code.call_count >= 2

    @pytest.mark.asyncio
    async def test_semantic_analysis_finds_issues(self, engine_with_mock_llm, sample_java_file):
        """LLM semantic analysisが問題を検出する場合"""
        engine_with_mock_llm.anthropic_client.analyze_code = Mock(side_effect=[
            # deep analysis
            '{"analysis": "Test", "confidence": 0.90, "fix_suggestions": [], "impact_scope": {}, "reasoning": "Test"}',
            # semantic analysis - 問題あり
            '''[{
                "issue_type": "DATA_MODEL_ISSUE",
                "severity": "medium",
                "line_number": 10,
                "message": "Inefficient partition key design",
                "cql_text": "SELECT * FROM users",
                "recommendation": "Use composite partition key",
                "confidence": 0.80,
                "fix_suggestions": ["Redesign schema"],
                "impact_scope": {}
            }]'''
        ])

        results = await engine_with_mock_llm.analyze_code(sample_java_file, "comprehensive")

        # LLMのみで検出された問題が含まれることを確認
        llm_only_issues = [r for r in results if r.has_llm_detection and not r.has_static_detection]
        assert len(llm_only_issues) > 0


class TestLLMDeepAnalysisErrors:
    """LLM deep analysis エラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_llm_deep_analysis_exception(self, engine_with_mock_llm, sample_java_file):
        """LLM deep analysisで例外が発生した場合のハンドリング"""
        # LLM呼び出しで例外を発生させる
        engine_with_mock_llm.anthropic_client.analyze_code = Mock(
            side_effect=Exception("LLM API error")
        )

        results = await engine_with_mock_llm.analyze_code(sample_java_file, "standard")

        # 例外が発生してもクラッシュせず、静的解析結果のみが返される
        assert isinstance(results, list)
        assert len(results) > 0

        # 全てが静的解析のみの結果
        for result in results:
            assert result.has_static_detection
            assert not result.has_llm_detection


class TestStatisticsEdgeCases:
    """統計情報のエッジケースのテスト"""

    def test_get_statistics_with_all_severities(self, engine_no_llm):
        """全ての重要度レベルが含まれる統計情報"""
        issues = [
            Issue(
                detector_name="Test", issue_type="TEST", severity=severity,
                file_path="/test.java", line_number=10, message=f"{severity} issue",
                cql_text="SELECT *", recommendation="Fix"
            )
            for severity in ["critical", "high", "medium", "low"]
        ]

        results = [HybridAnalysisResult.from_static_only(issue) for issue in issues]
        stats = engine_no_llm.get_statistics(results)

        assert stats["total_issues"] == 4
        assert stats["severity_distribution"]["critical"] == 1
        assert stats["severity_distribution"]["high"] == 1
        assert stats["severity_distribution"]["medium"] == 1
        assert stats["severity_distribution"]["low"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
