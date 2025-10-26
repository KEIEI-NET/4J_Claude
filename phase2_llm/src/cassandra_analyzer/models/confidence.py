"""
Analysis Confidence Levels
"""

from enum import Enum
from typing import Dict


class AnalysisConfidence(Enum):
    """
    信頼度レベル

    静的解析とLLM分析の結果を統合する際に使用する信頼度スコア
    """

    CERTAIN = "certain"          # 100% 確実（静的解析で証明可能）
    HIGH = "high"                # 90-99%（静的解析とLLMが一致）
    MEDIUM = "medium"            # 70-89%（LLM推定のみ）
    LOW = "low"                  # 50-69%（推測レベル）
    UNCERTAIN = "uncertain"      # <50%（人間の判断が必要）

    @property
    def score_range(self) -> tuple[int, int]:
        """
        信頼度スコアの範囲を返す

        Returns:
            tuple[int, int]: (最小スコア, 最大スコア)
        """
        ranges = {
            AnalysisConfidence.CERTAIN: (100, 100),
            AnalysisConfidence.HIGH: (90, 99),
            AnalysisConfidence.MEDIUM: (70, 89),
            AnalysisConfidence.LOW: (50, 69),
            AnalysisConfidence.UNCERTAIN: (0, 49),
        }
        return ranges[self]

    @property
    def description(self) -> str:
        """
        信頼度の説明を返す

        Returns:
            str: 信頼度の説明
        """
        descriptions = {
            AnalysisConfidence.CERTAIN: "静的解析により確実に検出された問題",
            AnalysisConfidence.HIGH: "静的解析とLLMの両方で検出された問題",
            AnalysisConfidence.MEDIUM: "LLMによって検出された可能性のある問題",
            AnalysisConfidence.LOW: "推測レベルの問題（要確認）",
            AnalysisConfidence.UNCERTAIN: "人間の判断が必要な問題",
        }
        return descriptions[self]

    @classmethod
    def from_score(cls, score: float) -> "AnalysisConfidence":
        """
        スコアから信頼度レベルを判定

        Args:
            score: 信頼度スコア（0-100）

        Returns:
            AnalysisConfidence: 対応する信頼度レベル
        """
        if score >= 100:
            return cls.CERTAIN
        elif score >= 90:
            return cls.HIGH
        elif score >= 70:
            return cls.MEDIUM
        elif score >= 50:
            return cls.LOW
        else:
            return cls.UNCERTAIN

    @classmethod
    def from_sources(
        cls,
        has_static_detection: bool,
        has_llm_detection: bool,
        llm_confidence: float = 0.85
    ) -> "AnalysisConfidence":
        """
        検出ソースから信頼度を計算

        Args:
            has_static_detection: 静的解析で検出されたか
            has_llm_detection: LLM分析で検出されたか
            llm_confidence: LLMの信頼度（0.0-1.0）

        Returns:
            AnalysisConfidence: 計算された信頼度レベル
        """
        if has_static_detection and has_llm_detection:
            # 両方で検出された場合は HIGH
            return cls.HIGH
        elif has_static_detection:
            # 静的解析のみの場合は CERTAIN
            return cls.CERTAIN
        elif has_llm_detection:
            # LLMのみの場合は、LLMの信頼度に基づく
            score = llm_confidence * 100
            if score >= 90:
                return cls.HIGH
            elif score >= 70:
                return cls.MEDIUM
            elif score >= 50:
                return cls.LOW
            else:
                return cls.UNCERTAIN
        else:
            # どちらでも検出されていない場合
            return cls.UNCERTAIN

    def to_dict(self) -> Dict[str, any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, any]: 信頼度情報の辞書
        """
        min_score, max_score = self.score_range
        return {
            "level": self.value,
            "score_range": {
                "min": min_score,
                "max": max_score,
            },
            "description": self.description,
        }
