"""
Tests for AnalysisConfidence
"""

import pytest

# conftest.pyでパス設定済み。直接インポート
from cassandra_analyzer.models.confidence import AnalysisConfidence


class TestAnalysisConfidence:
    """AnalysisConfidenceのテスト"""

    def test_score_range_certain(self):
        """CERTAINのスコア範囲が正しいことを確認"""
        confidence = AnalysisConfidence.CERTAIN
        assert confidence.score_range == (100, 100)

    def test_score_range_high(self):
        """HIGHのスコア範囲が正しいことを確認"""
        confidence = AnalysisConfidence.HIGH
        assert confidence.score_range == (90, 99)

    def test_score_range_medium(self):
        """MEDIUMのスコア範囲が正しいことを確認"""
        confidence = AnalysisConfidence.MEDIUM
        assert confidence.score_range == (70, 89)

    def test_score_range_low(self):
        """LOWのスコア範囲が正しいことを確認"""
        confidence = AnalysisConfidence.LOW
        assert confidence.score_range == (50, 69)

    def test_score_range_uncertain(self):
        """UNCERTAINのスコア範囲が正しいことを確認"""
        confidence = AnalysisConfidence.UNCERTAIN
        assert confidence.score_range == (0, 49)

    def test_description(self):
        """説明文が存在することを確認"""
        for confidence in AnalysisConfidence:
            assert isinstance(confidence.description, str)
            assert len(confidence.description) > 0

    def test_from_score_certain(self):
        """スコア100でCERTAINが返されることを確認"""
        assert AnalysisConfidence.from_score(100) == AnalysisConfidence.CERTAIN

    def test_from_score_high(self):
        """スコア90-99でHIGHが返されることを確認"""
        assert AnalysisConfidence.from_score(95) == AnalysisConfidence.HIGH
        assert AnalysisConfidence.from_score(90) == AnalysisConfidence.HIGH
        assert AnalysisConfidence.from_score(99) == AnalysisConfidence.HIGH

    def test_from_score_medium(self):
        """スコア70-89でMEDIUMが返されることを確認"""
        assert AnalysisConfidence.from_score(80) == AnalysisConfidence.MEDIUM
        assert AnalysisConfidence.from_score(70) == AnalysisConfidence.MEDIUM
        assert AnalysisConfidence.from_score(89) == AnalysisConfidence.MEDIUM

    def test_from_score_low(self):
        """スコア50-69でLOWが返されることを確認"""
        assert AnalysisConfidence.from_score(60) == AnalysisConfidence.LOW
        assert AnalysisConfidence.from_score(50) == AnalysisConfidence.LOW
        assert AnalysisConfidence.from_score(69) == AnalysisConfidence.LOW

    def test_from_score_uncertain(self):
        """スコア0-49でUNCERTAINが返されることを確認"""
        assert AnalysisConfidence.from_score(30) == AnalysisConfidence.UNCERTAIN
        assert AnalysisConfidence.from_score(0) == AnalysisConfidence.UNCERTAIN
        assert AnalysisConfidence.from_score(49) == AnalysisConfidence.UNCERTAIN

    def test_from_sources_static_only(self):
        """静的解析のみの場合CERTAINが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=True,
            has_llm_detection=False
        )
        assert confidence == AnalysisConfidence.CERTAIN

    def test_from_sources_both_detected(self):
        """両方で検出された場合HIGHが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=True,
            has_llm_detection=True
        )
        assert confidence == AnalysisConfidence.HIGH

    def test_from_sources_llm_only_high_confidence(self):
        """LLMのみで高信頼度の場合HIGHが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=False,
            has_llm_detection=True,
            llm_confidence=0.95
        )
        assert confidence == AnalysisConfidence.HIGH

    def test_from_sources_llm_only_medium_confidence(self):
        """LLMのみで中信頼度の場合MEDIUMが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=False,
            has_llm_detection=True,
            llm_confidence=0.80
        )
        assert confidence == AnalysisConfidence.MEDIUM

    def test_from_sources_llm_only_low_confidence(self):
        """LLMのみで低信頼度の場合LOWが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=False,
            has_llm_detection=True,
            llm_confidence=0.60
        )
        assert confidence == AnalysisConfidence.LOW

    def test_from_sources_llm_only_uncertain(self):
        """LLMのみで超低信頼度の場合UNCERTAINが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=False,
            has_llm_detection=True,
            llm_confidence=0.30
        )
        assert confidence == AnalysisConfidence.UNCERTAIN

    def test_from_sources_neither(self):
        """どちらでも検出されない場合UNCERTAINが返されることを確認"""
        confidence = AnalysisConfidence.from_sources(
            has_static_detection=False,
            has_llm_detection=False
        )
        assert confidence == AnalysisConfidence.UNCERTAIN

    def test_to_dict(self):
        """to_dict()が正しい形式で返されることを確認"""
        confidence = AnalysisConfidence.HIGH
        result = confidence.to_dict()

        assert "level" in result
        assert "score_range" in result
        assert "description" in result
        assert result["level"] == "high"
        assert result["score_range"]["min"] == 90
        assert result["score_range"]["max"] == 99
        assert isinstance(result["description"], str)

    def test_all_confidence_levels_have_valid_properties(self):
        """全ての信頼度レベルが有効なプロパティを持つことを確認"""
        for confidence in AnalysisConfidence:
            # score_rangeが有効
            min_score, max_score = confidence.score_range
            assert 0 <= min_score <= 100
            assert 0 <= max_score <= 100
            assert min_score <= max_score

            # descriptionが存在
            assert len(confidence.description) > 0

            # to_dict()が動作
            result = confidence.to_dict()
            assert "level" in result
            assert "score_range" in result
            assert "description" in result
