"""
Hybrid Analysis Result Model
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Phase 1のモジュールをインポートパスに追加（一度だけ）
phase1_path = Path(__file__).parent.parent.parent.parent.parent / "phase1_cassandra" / "src"
if str(phase1_path) not in sys.path:
    sys.path.insert(0, str(phase1_path))

# Phase 1からインポート（絶対インポート）
try:
    from cassandra_analyzer.models.issue import Issue
except ImportError:
    # テスト環境ではconftest.pyでパスが設定されている
    from cassandra_analyzer.models.issue import Issue  # type: ignore

from .confidence import AnalysisConfidence


@dataclass
class HybridAnalysisResult:
    """
    ハイブリッド分析結果

    静的解析とLLM分析の結果を統合した最終的な分析結果

    Attributes:
        issue: Phase 1の基本Issue情報
        confidence_level: 信頼度レベル（CERTAIN, HIGH, MEDIUM, LOW, UNCERTAIN）
        static_analysis: 静的解析の詳細情報
        llm_analysis: LLM分析の詳細情報
        fix_suggestions: 修正提案のリスト
        impact_scope: 影響範囲の情報
        analysis_context: 分析時のコンテキスト情報
    """

    issue: Issue
    confidence_level: AnalysisConfidence
    static_analysis: Optional[Dict[str, Any]] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    fix_suggestions: List[str] = field(default_factory=list)
    impact_scope: Dict[str, Any] = field(default_factory=dict)
    analysis_context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.static_analysis is None and self.llm_analysis is None:
            raise ValueError("Either static_analysis or llm_analysis must be provided")

    @property
    def has_static_detection(self) -> bool:
        """静的解析で検出されたか"""
        return self.static_analysis is not None

    @property
    def has_llm_detection(self) -> bool:
        """LLM分析で検出されたか"""
        return self.llm_analysis is not None

    @property
    def detection_sources(self) -> List[str]:
        """検出ソースのリスト"""
        sources = []
        if self.has_static_detection:
            sources.append("static")
        if self.has_llm_detection:
            sources.append("llm")
        return sources

    @property
    def confidence_score(self) -> float:
        """
        信頼度スコア（0.0-1.0）

        Returns:
            float: 信頼度スコア
        """
        min_score, max_score = self.confidence_level.score_range
        # 範囲の中央値を返す
        return (min_score + max_score) / 2 / 100

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, Any]: 分析結果の辞書
        """
        return {
            "issue": self.issue.to_dict(),
            "confidence": {
                "level": self.confidence_level.value,
                "score": self.confidence_score,
                "description": self.confidence_level.description,
            },
            "detection_sources": self.detection_sources,
            "static_analysis": self.static_analysis,
            "llm_analysis": self.llm_analysis,
            "fix_suggestions": self.fix_suggestions,
            "impact_scope": self.impact_scope,
            "analysis_context": self.analysis_context,
        }

    @classmethod
    def from_static_only(
        cls,
        issue: Issue,
        static_details: Optional[Dict[str, Any]] = None
    ) -> "HybridAnalysisResult":
        """
        静的解析のみの結果から作成

        Args:
            issue: Phase 1のIssue
            static_details: 静的解析の詳細情報

        Returns:
            HybridAnalysisResult: ハイブリッド分析結果
        """
        return cls(
            issue=issue,
            confidence_level=AnalysisConfidence.CERTAIN,
            static_analysis=static_details or {},
            llm_analysis=None,
            analysis_context={"analysis_type": "static_only"}
        )

    @classmethod
    def from_llm_only(
        cls,
        issue: Issue,
        llm_details: Dict[str, Any],
        llm_confidence: float = 0.85
    ) -> "HybridAnalysisResult":
        """
        LLM分析のみの結果から作成

        Args:
            issue: Phase 1のIssue
            llm_details: LLM分析の詳細情報
            llm_confidence: LLMの信頼度（0.0-1.0）

        Returns:
            HybridAnalysisResult: ハイブリッド分析結果
        """
        confidence_level = AnalysisConfidence.from_score(llm_confidence * 100)
        return cls(
            issue=issue,
            confidence_level=confidence_level,
            static_analysis=None,
            llm_analysis=llm_details,
            analysis_context={"analysis_type": "llm_only", "llm_confidence": llm_confidence}
        )

    @classmethod
    def from_hybrid(
        cls,
        issue: Issue,
        static_details: Dict[str, Any],
        llm_details: Dict[str, Any],
        llm_confidence: float = 0.90
    ) -> "HybridAnalysisResult":
        """
        静的解析とLLM分析の両方から作成

        Args:
            issue: Phase 1のIssue
            static_details: 静的解析の詳細情報
            llm_details: LLM分析の詳細情報
            llm_confidence: LLMの信頼度（0.0-1.0）

        Returns:
            HybridAnalysisResult: ハイブリッド分析結果
        """
        # 両方で検出された場合はHIGH
        confidence_level = AnalysisConfidence.HIGH
        return cls(
            issue=issue,
            confidence_level=confidence_level,
            static_analysis=static_details,
            llm_analysis=llm_details,
            fix_suggestions=llm_details.get("fix_suggestions", []),
            impact_scope=llm_details.get("impact_scope", {}),
            analysis_context={
                "analysis_type": "hybrid",
                "llm_confidence": llm_confidence,
                "agreement": True
            }
        )

    def add_fix_suggestion(self, suggestion: str) -> None:
        """
        修正提案を追加

        Args:
            suggestion: 修正提案
        """
        if suggestion and suggestion not in self.fix_suggestions:
            self.fix_suggestions.append(suggestion)

    def set_impact_scope(self, scope: Dict[str, Any]) -> None:
        """
        影響範囲を設定

        Args:
            scope: 影響範囲の情報
        """
        self.impact_scope = scope

    def merge_llm_analysis(
        self,
        llm_details: Dict[str, Any],
        llm_confidence: float = 0.90
    ) -> None:
        """
        LLM分析結果をマージ

        Args:
            llm_details: LLM分析の詳細情報
            llm_confidence: LLMの信頼度（0.0-1.0）
        """
        self.llm_analysis = llm_details

        # 信頼度レベルを再計算
        self.confidence_level = AnalysisConfidence.from_sources(
            has_static_detection=self.has_static_detection,
            has_llm_detection=True,
            llm_confidence=llm_confidence
        )

        # 修正提案を追加
        if "fix_suggestions" in llm_details:
            for suggestion in llm_details["fix_suggestions"]:
                self.add_fix_suggestion(suggestion)

        # 影響範囲を更新
        if "impact_scope" in llm_details:
            self.set_impact_scope(llm_details["impact_scope"])

        # コンテキストを更新
        self.analysis_context["llm_confidence"] = llm_confidence
        self.analysis_context["llm_merged"] = True
