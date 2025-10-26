"""
Tests for HybridAnalysisResult
"""

import pytest

# conftest.pyでパス設定済み。Phase 2のmodelsパッケージから直接インポート
from cassandra_analyzer.models import Issue, AnalysisConfidence
from cassandra_analyzer.models.hybrid_result import HybridAnalysisResult


@pytest.fixture
def sample_issue():
    """テスト用のサンプルIssue"""
    return Issue(
        detector_name="TestDetector",
        issue_type="TEST_ISSUE",
        severity="high",
        file_path="/path/to/file.java",
        line_number=42,
        message="Test issue message",
        cql_text="SELECT * FROM users",
        recommendation="Test recommendation"
    )


class TestHybridAnalysisResult:
    """HybridAnalysisResultのテスト"""

    def test_from_static_only(self, sample_issue):
        """静的解析のみの結果作成をテスト"""
        result = HybridAnalysisResult.from_static_only(
            issue=sample_issue,
            static_details={"method": "pattern_matching"}
        )

        assert result.issue == sample_issue
        assert result.confidence_level == AnalysisConfidence.CERTAIN
        assert result.has_static_detection
        assert not result.has_llm_detection
        assert result.static_analysis == {"method": "pattern_matching"}
        assert result.llm_analysis is None

    def test_from_llm_only(self, sample_issue):
        """LLM分析のみの結果作成をテスト"""
        llm_details = {
            "analysis": "LLM analysis result",
            "confidence": 0.85
        }
        result = HybridAnalysisResult.from_llm_only(
            issue=sample_issue,
            llm_details=llm_details,
            llm_confidence=0.85
        )

        assert result.issue == sample_issue
        assert result.confidence_level == AnalysisConfidence.MEDIUM
        assert not result.has_static_detection
        assert result.has_llm_detection
        assert result.static_analysis is None
        assert result.llm_analysis == llm_details

    def test_from_hybrid(self, sample_issue):
        """ハイブリッド分析の結果作成をテスト"""
        static_details = {"method": "pattern_matching"}
        llm_details = {
            "analysis": "LLM analysis",
            "fix_suggestions": ["Fix 1", "Fix 2"],
            "impact_scope": {"methods": ["method1"]}
        }

        result = HybridAnalysisResult.from_hybrid(
            issue=sample_issue,
            static_details=static_details,
            llm_details=llm_details,
            llm_confidence=0.90
        )

        assert result.issue == sample_issue
        assert result.confidence_level == AnalysisConfidence.HIGH
        assert result.has_static_detection
        assert result.has_llm_detection
        assert result.static_analysis == static_details
        assert result.llm_analysis == llm_details
        assert len(result.fix_suggestions) == 2
        assert result.impact_scope == {"methods": ["method1"]}

    def test_detection_sources_static_only(self, sample_issue):
        """静的解析のみの場合の検出ソースをテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)
        assert result.detection_sources == ["static"]

    def test_detection_sources_llm_only(self, sample_issue):
        """LLM分析のみの場合の検出ソースをテスト"""
        result = HybridAnalysisResult.from_llm_only(
            issue=sample_issue,
            llm_details={},
            llm_confidence=0.85
        )
        assert result.detection_sources == ["llm"]

    def test_detection_sources_hybrid(self, sample_issue):
        """ハイブリッド分析の場合の検出ソースをテスト"""
        result = HybridAnalysisResult.from_hybrid(
            issue=sample_issue,
            static_details={},
            llm_details={},
            llm_confidence=0.90
        )
        assert sorted(result.detection_sources) == ["llm", "static"]

    def test_confidence_score(self, sample_issue):
        """信頼度スコアの計算をテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)
        assert result.confidence_score == 1.0  # CERTAIN: (100+100)/2/100

        result = HybridAnalysisResult.from_hybrid(
            issue=sample_issue,
            static_details={},
            llm_details={},
            llm_confidence=0.90
        )
        assert result.confidence_score == 0.945  # HIGH: (90+99)/2/100

    def test_add_fix_suggestion(self, sample_issue):
        """修正提案の追加をテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)

        result.add_fix_suggestion("Fix 1")
        assert len(result.fix_suggestions) == 1
        assert "Fix 1" in result.fix_suggestions

        result.add_fix_suggestion("Fix 2")
        assert len(result.fix_suggestions) == 2

        # 重複追加は無視される
        result.add_fix_suggestion("Fix 1")
        assert len(result.fix_suggestions) == 2

    def test_set_impact_scope(self, sample_issue):
        """影響範囲の設定をテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)

        scope = {"methods": ["method1", "method2"], "risk": "high"}
        result.set_impact_scope(scope)

        assert result.impact_scope == scope

    def test_merge_llm_analysis(self, sample_issue):
        """LLM分析結果のマージをテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)

        # 初期状態
        assert not result.has_llm_detection
        assert result.confidence_level == AnalysisConfidence.CERTAIN

        # LLM分析をマージ
        llm_details = {
            "analysis": "LLM analysis",
            "fix_suggestions": ["Fix A", "Fix B"],
            "impact_scope": {"methods": ["m1"]}
        }
        result.merge_llm_analysis(llm_details, llm_confidence=0.90)

        # マージ後の状態
        assert result.has_llm_detection
        assert result.confidence_level == AnalysisConfidence.HIGH
        assert result.llm_analysis == llm_details
        assert len(result.fix_suggestions) == 2
        assert result.impact_scope == {"methods": ["m1"]}

    def test_to_dict(self, sample_issue):
        """辞書形式への変換をテスト"""
        result = HybridAnalysisResult.from_hybrid(
            issue=sample_issue,
            static_details={"method": "pattern"},
            llm_details={"analysis": "LLM"},
            llm_confidence=0.90
        )

        result_dict = result.to_dict()

        assert "issue" in result_dict
        assert "confidence" in result_dict
        assert "detection_sources" in result_dict
        assert "static_analysis" in result_dict
        assert "llm_analysis" in result_dict
        assert "fix_suggestions" in result_dict
        assert "impact_scope" in result_dict
        assert "analysis_context" in result_dict

        # confidence詳細
        assert "level" in result_dict["confidence"]
        assert "score" in result_dict["confidence"]
        assert "description" in result_dict["confidence"]

    def test_validation_both_none(self, sample_issue):
        """静的解析とLLM分析の両方がNoneの場合にエラーをテスト"""
        with pytest.raises(ValueError, match="Either static_analysis or llm_analysis must be provided"):
            HybridAnalysisResult(
                issue=sample_issue,
                confidence_level=AnalysisConfidence.UNCERTAIN,
                static_analysis=None,
                llm_analysis=None
            )

    def test_analysis_context(self, sample_issue):
        """分析コンテキストの保存をテスト"""
        result = HybridAnalysisResult.from_static_only(issue=sample_issue)
        assert result.analysis_context["analysis_type"] == "static_only"

        result = HybridAnalysisResult.from_llm_only(
            issue=sample_issue,
            llm_details={},
            llm_confidence=0.85
        )
        assert result.analysis_context["analysis_type"] == "llm_only"
        assert result.analysis_context["llm_confidence"] == 0.85

        result = HybridAnalysisResult.from_hybrid(
            issue=sample_issue,
            static_details={},
            llm_details={},
            llm_confidence=0.90
        )
        assert result.analysis_context["analysis_type"] == "hybrid"
        assert result.analysis_context["llm_confidence"] == 0.90
        assert result.analysis_context["agreement"] is True
