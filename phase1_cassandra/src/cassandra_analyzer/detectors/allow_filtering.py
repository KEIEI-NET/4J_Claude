"""
ALLOW FILTERING検出器
"""
from typing import List, Dict, Any, Optional

from .base import BaseDetector
from ..models import Issue, CassandraCall
from ..parsers import CQLParser


class AllowFilteringDetector(BaseDetector):
    """
    ALLOW FILTERINGの使用を検出

    ALLOW FILTERINGは全テーブルスキャンのリスクがあり、
    Materialized ViewやSecondary Indexの使用を推奨する
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書（オプション）
        """
        super().__init__(config)
        # デフォルト重要度は"high"
        if "severity" not in self.config:
            self._severity = "high"
        self.cql_parser = CQLParser()

    @property
    def detector_name(self) -> str:
        """検出器の名前"""
        return "AllowFilteringDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        ALLOW FILTERINGの使用を検出

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

        # ALLOW FILTERINGの検出
        if analysis.has_allow_filtering:
            # 証拠の収集
            evidence = [
                f"Query type: {analysis.query_type.value}",
                f"Target tables: {', '.join(analysis.tables)}",
            ]

            if analysis.where_clause:
                evidence.append(f"WHERE clause: {analysis.where_clause.raw_clause}")

            # 推奨事項の生成
            recommendation = self._generate_recommendation(analysis)

            issue = self._create_issue(
                issue_type="ALLOW_FILTERING",
                call=call,
                message="ALLOW FILTERING detected - full table scan risk",
                recommendation=recommendation,
                severity="high",
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
            "ALLOW FILTERING should be avoided as it causes full table scans across all nodes."
        )

        # テーブルごとの推奨
        if analysis.tables:
            table_name = analysis.tables[0]  # 最初のテーブルを使用
            recommendations.append(
                f"\nRecommended solutions for table '{table_name}':"
            )
            recommendations.append(
                "1. Create a Materialized View with appropriate partition key"
            )
            recommendations.append(
                "2. Create a Secondary Index (use sparingly)"
            )
            recommendations.append(
                "3. Redesign the data model to support the query pattern"
            )

        # WHERE句の情報がある場合
        if analysis.where_clause and analysis.where_clause.columns:
            columns = ", ".join(analysis.where_clause.columns)
            recommendations.append(
                f"\nConsider using these columns as partition/clustering keys: {columns}"
            )

        return "\n".join(recommendations)
