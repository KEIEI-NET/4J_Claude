"""
Partition Key検証検出器
"""
from typing import List, Dict, Any, Optional

from .base import BaseDetector
from ..models import Issue, CassandraCall
from ..parsers import CQLParser, QueryType


class PartitionKeyDetector(BaseDetector):
    """
    Partition Keyの未使用を検出

    SELECTクエリでPartition Keyを使用していない場合、
    複数ノードにまたがるフルスキャンが発生するため、
    パフォーマンスの重大な問題となる
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書（オプション）
        """
        super().__init__(config)
        # デフォルト重要度は"critical"
        if "severity" not in self.config:
            self._severity = "critical"
        self.cql_parser = CQLParser()

    @property
    def detector_name(self) -> str:
        """検出器の名前"""
        return "PartitionKeyDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        Partition Keyの未使用を検出

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

        # SELECTクエリのみを対象とする
        if analysis.query_type != QueryType.SELECT:
            return issues

        # Partition Key未使用の検出
        if not analysis.uses_partition_key:
            # 証拠の収集
            evidence = [
                f"Query type: {analysis.query_type.value}",
                f"Target tables: {', '.join(analysis.tables)}",
            ]

            if analysis.where_clause:
                evidence.append(
                    f"WHERE clause columns: {', '.join(analysis.where_clause.columns)}"
                )
                if analysis.where_clause.has_range:
                    evidence.append("Range condition detected (not using equality for partition key)")
            else:
                evidence.append("No WHERE clause found")

            # ALLOW FILTERINGの有無
            if analysis.has_allow_filtering:
                evidence.append("ALLOW FILTERING is used (compounds the problem)")

            # 推奨事項の生成
            recommendation = self._generate_recommendation(analysis)

            issue = self._create_issue(
                issue_type="NO_PARTITION_KEY",
                call=call,
                message="Partition Key not used - multi-node scan will occur",
                recommendation=recommendation,
                severity="critical",
                evidence=evidence,
                confidence=0.9,  # スキーマ情報がないため信頼度は若干低め
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
            "Queries without partition key cause full cluster scans, "
            "which severely impact performance and scalability."
        )

        if analysis.tables:
            table_name = analysis.tables[0]  # 最初のテーブルを使用
            recommendations.append(
                f"\nFor table '{table_name}':"
            )

        recommendations.append(
            "\nRecommended solutions:"
        )
        recommendations.append(
            "1. Add partition key to WHERE clause with equality condition (=)"
        )
        recommendations.append(
            "2. If the current query pattern is essential, create a Materialized View"
        )
        recommendations.append(
            "3. Redesign the data model to align with query patterns"
        )

        # WHERE句の情報がある場合
        if analysis.where_clause and analysis.where_clause.columns:
            columns = ", ".join(analysis.where_clause.columns)
            recommendations.append(
                f"\nCurrent WHERE clause uses: {columns}"
            )
            recommendations.append(
                "Ensure at least one of these columns is the partition key with an equality condition."
            )
        else:
            recommendations.append(
                "\nNo WHERE clause detected. Add a WHERE clause with partition key filter."
            )

        return "\n".join(recommendations)
