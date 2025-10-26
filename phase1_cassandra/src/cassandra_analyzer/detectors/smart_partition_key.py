"""
スマートPartition Key検出器（LLM統合）
"""
from typing import List, Dict, Any, Optional

from .partition_key import PartitionKeyDetector
from ..models import Issue, CassandraCall
from ..llm import LLMAnalyzer


class SmartPartitionKeyDetector(PartitionKeyDetector):
    """
    LLMを活用した高度なPartition Key検出器

    従来の検出器の機能に加え、LLMによる以下の分析を提供:
    - データモデルの理解に基づいた推奨事項
    - テーブルスキーマの推測
    - 実際のパーティションキー候補の提案
    - クエリパターンとデータモデルの整合性分析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書
                - llm_enabled: LLM分析を有効化するか（デフォルト: True）
                - anthropic_api_key: Anthropic APIキー
                - table_schema: テーブルスキーマ情報（オプション）
                - その他の基底クラスの設定
        """
        super().__init__(config)

        # LLM分析の設定
        self.llm_enabled = self.config.get("llm_enabled", True)

        # テーブルスキーマ情報（提供されている場合）
        self.table_schema = self.config.get("table_schema")

        # LLMアナライザーの初期化
        if self.llm_enabled:
            api_key = self.config.get("anthropic_api_key")
            if api_key:
                try:
                    self.llm_analyzer = LLMAnalyzer(api_key=api_key)
                except Exception as e:
                    print(f"Warning: Failed to initialize LLMAnalyzer: {e}")
                    self.llm_enabled = False
            else:
                # APIキーがない場合は無効化
                self.llm_enabled = False

    @property
    def detector_name(self) -> str:
        """検出器の名前"""
        return "SmartPartitionKeyDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        LLMを活用したPartition Key検出

        Args:
            call: 分析対象のCassandra呼び出し

        Returns:
            検出された問題のリスト（LLMによる拡張分析付き）
        """
        # 基本的な検出は親クラスに委譲
        issues = super().detect(call)

        # LLMによる拡張分析
        if self.llm_enabled and issues:
            issues = self._enhance_issues_with_llm(issues, call)

        return issues

    def _enhance_issues_with_llm(
        self, issues: List[Issue], call: CassandraCall
    ) -> List[Issue]:
        """
        LLMを使用して検出結果を拡張

        Args:
            issues: 基本検出器が検出した問題のリスト
            call: Cassandra呼び出し情報

        Returns:
            LLMによる分析で拡張された問題のリスト
        """
        enhanced_issues = []

        for issue in issues:
            try:
                # LLMによるデータモデル分析
                analysis = self._get_llm_analysis(call)

                # 推測されたスキーマ情報を証拠に追加
                inferred_schema = analysis.get("inferred_schema", {})
                if inferred_schema:
                    partition_keys = inferred_schema.get("partition_keys", [])
                    clustering_keys = inferred_schema.get("clustering_keys", [])

                    if partition_keys:
                        issue.evidence.append(
                            f"LLM Inferred Partition Keys: {', '.join(partition_keys)}"
                        )
                    if clustering_keys:
                        issue.evidence.append(
                            f"LLM Inferred Clustering Keys: {', '.join(clustering_keys)}"
                        )

                # LLMによる詳細な推奨事項を追加
                enhanced_recommendation = self._get_enhanced_recommendation(
                    call, analysis
                )
                if enhanced_recommendation:
                    issue.recommendation = (
                        f"{issue.recommendation}\n\n"
                        f"## LLM Enhanced Data Model Analysis:\n{enhanced_recommendation}"
                    )

                # 信頼度の調整（スキーマ推測がある場合は上げる）
                if inferred_schema and inferred_schema.get("partition_keys"):
                    issue.confidence = min(0.95, issue.confidence + 0.05)

                enhanced_issues.append(issue)

            except Exception as e:
                # LLM分析が失敗した場合は元の問題をそのまま使用
                print(f"Warning: LLM analysis failed: {e}")
                enhanced_issues.append(issue)

        return enhanced_issues

    def _get_llm_analysis(self, call: CassandraCall) -> Dict[str, Any]:
        """
        LLMによるクエリとデータモデルの分析

        Args:
            call: Cassandra呼び出し情報

        Returns:
            LLM分析結果の辞書
        """
        if not self.llm_enabled:
            return {}

        try:
            # スキーマ情報の構築
            schema_context = ""
            if self.table_schema:
                schema_context = f"\n\nTable Schema:\n{self.table_schema}"

            # カスタムプロンプトを構築
            context = f"""
Analyze the following Cassandra query for partition key usage:

Query: {call.cql_text}
Method: {call.method_name}
Class: {call.class_name or 'Unknown'}
Method Context: {call.method_context or 'Unknown'}{schema_context}

Based on the query pattern and context:
1. Infer the likely partition key(s) for the table
2. Infer the likely clustering key(s) if any
3. Analyze the current WHERE clause usage
4. Suggest specific data model improvements
5. Provide query rewriting suggestions

Provide your analysis in JSON format with:
- inferred_schema: object with:
  - partition_keys: list of likely partition key columns
  - clustering_keys: list of likely clustering key columns
  - reasoning: string explaining the inference
- current_issue: string (description of the current problem)
- recommended_schema: string (suggested schema design)
- query_rewrite: string (suggested query improvement)
- materialized_view_suggestion: string (suggested MV if applicable)
"""

            response = self.llm_analyzer.client.analyze_code(
                code=call.cql_text,
                prompt=context,
                max_tokens=1500,
                temperature=0.1
            )

            # JSONレスポンスをパース
            import json
            # マークダウンコードブロックの除去
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            return json.loads(response)

        except Exception as e:
            print(f"Warning: Failed to get LLM analysis: {e}")
            return {}

    def _get_enhanced_recommendation(
        self, call: CassandraCall, analysis: Dict[str, Any]
    ) -> str:
        """
        LLM分析に基づいた詳細な推奨事項を生成

        Args:
            call: Cassandra呼び出し情報
            analysis: LLM分析結果

        Returns:
            詳細な推奨事項の文字列
        """
        if not analysis:
            return ""

        recommendations = []

        # 推測されたスキーマ
        inferred_schema = analysis.get("inferred_schema", {})
        if inferred_schema:
            reasoning = inferred_schema.get("reasoning", "")
            if reasoning:
                recommendations.append(f"**Schema Analysis**: {reasoning}")

        # 現在の問題の説明
        current_issue = analysis.get("current_issue", "")
        if current_issue:
            recommendations.append(f"\n**Current Issue**: {current_issue}")

        # 推奨スキーマ設計
        recommended_schema = analysis.get("recommended_schema", "")
        if recommended_schema:
            recommendations.append(
                f"\n**Recommended Schema Design**:\n```cql\n{recommended_schema}\n```"
            )

        # クエリの書き換え提案
        query_rewrite = analysis.get("query_rewrite", "")
        if query_rewrite:
            recommendations.append(
                f"\n**Suggested Query Improvement**:\n```cql\n{query_rewrite}\n```"
            )

        # Materialized View提案
        mv_suggestion = analysis.get("materialized_view_suggestion", "")
        if mv_suggestion:
            recommendations.append(
                f"\n**Materialized View Option**:\n```cql\n{mv_suggestion}\n```"
            )

        return "\n".join(recommendations)
