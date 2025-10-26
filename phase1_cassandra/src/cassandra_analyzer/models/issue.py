"""
検出された問題を表すモデル
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Issue:
    """
    検出された問題

    Attributes:
        detector_name: 検出器の名前
        issue_type: 問題のタイプ（ALLOW_FILTERING、NO_PARTITION_KEY等）
        severity: 重要度（critical、high、medium、low）
        file_path: ファイルパス
        line_number: 行番号
        message: 問題の説明メッセージ
        cql_text: 問題のあるCQLクエリ
        recommendation: 推奨される修正方法
        evidence: 問題の根拠となる証拠のリスト
        confidence: 信頼度（0.0-1.0）
    """

    detector_name: str
    issue_type: str
    severity: str
    file_path: str
    line_number: int
    message: str
    cql_text: str
    recommendation: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.severity not in ["critical", "high", "medium", "low"]:
            raise ValueError(f"Invalid severity: {self.severity}")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0: {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            問題情報の辞書
        """
        return {
            "detector": self.detector_name,
            "type": self.issue_type,
            "severity": self.severity,
            "file": self.file_path,
            "line": self.line_number,
            "message": self.message,
            "cql": self.cql_text,
            "recommendation": self.recommendation,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }

    @property
    def severity_order(self) -> int:
        """
        重要度の順序を返す（ソート用）

        Returns:
            重要度の数値（小さいほど重要）
        """
        order_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return order_map.get(self.severity, 99)
