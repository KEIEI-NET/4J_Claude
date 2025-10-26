"""
Batch Size検出器
"""
from typing import List, Dict, Any, Optional

from .base import BaseDetector
from ..models import Issue, CassandraCall
from ..parsers import CQLParser, QueryType


class BatchSizeDetector(BaseDetector):
    """
    大量BATCH処理の検出

    Cassandraでは大量のBATCHステートメントは
    パフォーマンス低下やタイムアウトを引き起こす可能性がある
    推奨値は100ステートメント以下
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書（オプション）
                    - threshold: バッチサイズの閾値（デフォルト: 100）
        """
        super().__init__(config)
        # デフォルト重要度は"medium"
        if "severity" not in self.config:
            self._severity = "medium"

        # バッチサイズの閾値（設定から取得、デフォルトは100）
        self.threshold = self.config.get("threshold", 100)

        self.cql_parser = CQLParser(config={"batch_threshold": self.threshold})

    @property
    def detector_name(self) -> str:
        """検出器の名前"""
        return "BatchSizeDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        大量BATCH処理を検出

        Args:
            call: 分析対象のCassandra呼び出し

        Returns:
            検出された問題のリスト
        """
        issues: List[Issue] = []

        # CQL文字列を解析
        try:
            analysis = self.cql_parser.analyze(call.cql_text)
        except Exception as e:
            # 解析エラーの場合はスキップ
            return issues

        # BATCHクエリのみを対象とする
        if not analysis.is_batch:
            return issues

        # バッチサイズが閾値を超えているかチェック
        if analysis.batch_size > self.threshold:
            # 証拠の収集
            evidence = [
                f"Batch size: {analysis.batch_size} statements",
                f"Threshold: {self.threshold} statements",
                f"Exceeded by: {analysis.batch_size - self.threshold} statements",
            ]

            # テーブル情報
            if analysis.tables:
                evidence.append(f"Target tables: {', '.join(analysis.tables)}")

            # 推奨事項の生成
            recommendation = self._generate_recommendation(analysis)

            # 重要度の調整（極端に大きい場合はhighに）
            severity = self._severity
            if analysis.batch_size > self.threshold * 2:
                severity = "high"

            issue = self._create_issue(
                issue_type="LARGE_BATCH",
                call=call,
                message=f"Large batch processing: {analysis.batch_size} statements "
                        f"(threshold: {self.threshold})",
                recommendation=recommendation,
                severity=severity,
                evidence=evidence,
                confidence=1.0,
            )

            issues.append(issue)

        return issues

    def _generate_recommendation(self, analysis) -> str:
        """
        分析結果に基づいて推奨事項を生成

        Args:
            analysis: CQL分析結果

        Returns:
            推奨事項の文字列
        """
        recommendations = []

        # 基本的な推奨事項
        recommendations.append(
            f"Large batch operations (>{self.threshold} statements) can cause performance degradation, "
            "timeouts, and increased memory pressure on coordinator nodes."
        )

        # 分割の推奨
        chunk_size = self.threshold
        num_chunks = (analysis.batch_size + chunk_size - 1) // chunk_size  # 切り上げ除算

        recommendations.append(
            f"\nCurrent batch: {analysis.batch_size} statements"
        )
        recommendations.append(
            f"Recommended solutions:"
        )
        recommendations.append(
            f"1. Split into {num_chunks} smaller batches of {chunk_size} statements or less"
        )
        recommendations.append(
            "2. Use asynchronous execution with limited concurrency"
        )
        recommendations.append(
            "3. Consider using UNLOGGED BATCH for independent writes to different partitions"
        )

        # パフォーマンスへの影響
        recommendations.append(
            "\nPerformance impact:"
        )
        recommendations.append(
            f"- Coordinator node must hold {analysis.batch_size} mutations in memory"
        )
        recommendations.append(
            "- Increased latency and timeout risk"
        )
        recommendations.append(
            "- Potential impact on other queries during execution"
        )

        # ベストプラクティス
        recommendations.append(
            "\nBest practices:"
        )
        recommendations.append(
            f"- Keep batch size under {self.threshold} statements"
        )
        recommendations.append(
            "- Use batches only for atomicity within the same partition"
        )
        recommendations.append(
            "- For bulk loading, consider using Cassandra's bulk loader tool"
        )

        return "\n".join(recommendations)
