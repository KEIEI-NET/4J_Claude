"""
検出器の基底クラス
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..models import Issue, CassandraCall


class BaseDetector(ABC):
    """
    全検出器の基底クラス

    全ての検出器はこのクラスを継承し、detect()メソッドを実装する必要がある
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書（オプション）
        """
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._severity = self.config.get("severity", "medium")

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """
        検出器の名前を返す

        Returns:
            検出器の名前（例: "AllowFilteringDetector"）
        """
        pass

    def is_enabled(self) -> bool:
        """
        検出器が有効かどうかを返す

        Returns:
            有効な場合True、無効な場合False
        """
        return self._enabled

    @abstractmethod
    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        Cassandra呼び出しを分析し、問題を検出する

        Args:
            call: 分析対象のCassandra呼び出し

        Returns:
            検出された問題のリスト
        """
        pass

    def _create_issue(
        self,
        issue_type: str,
        call: CassandraCall,
        message: str,
        recommendation: str,
        severity: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        confidence: float = 1.0,
    ) -> Issue:
        """
        Issueオブジェクトを生成するヘルパーメソッド

        Args:
            issue_type: 問題タイプ（例: "ALLOW_FILTERING"）
            call: Cassandra呼び出し
            message: 問題の説明
            recommendation: 推奨事項
            severity: 重要度（None の場合は self._severity を使用）
            evidence: 証拠のリスト
            confidence: 信頼度（0.0-1.0）

        Returns:
            Issue オブジェクト
        """
        return Issue(
            detector_name=self.detector_name,
            issue_type=issue_type,
            severity=severity or self._severity,
            file_path=call.file_path,
            line_number=call.line_number,
            message=message,
            cql_text=call.cql_text,
            recommendation=recommendation,
            evidence=evidence or [],
            confidence=confidence,
        )
