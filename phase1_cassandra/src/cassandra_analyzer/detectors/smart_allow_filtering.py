"""
スマートALLOW FILTERING検出器（LLM統合）
"""
from typing import List, Dict, Any, Optional

from .allow_filtering import AllowFilteringDetector
from ..models import Issue, CassandraCall
from ..llm import LLMAnalyzer


class SmartAllowFilteringDetector(AllowFilteringDetector):
    """
    LLMを活用した高度なALLOW FILTERING検出器

    従来の検出器の機能に加え、LLMによる以下の分析を提供:
    - コンテキストに基づいた誤検出の低減
    - より詳細な影響分析
    - データモデル理解に基づく推奨事項
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書
                - llm_enabled: LLM分析を有効化するか（デフォルト: True）
                - anthropic_api_key: Anthropic APIキー
                - その他の基底クラスの設定
        """
        super().__init__(config)

        # LLM分析の設定
        self.llm_enabled = self.config.get("llm_enabled", True)

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
        return "SmartAllowFilteringDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        LLMを活用したALLOW FILTERING検出

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
                # LLMによるコンテキスト分析
                analysis = self._get_llm_analysis(call)

                # 誤検出の可能性をチェック
                if self._is_justified_use(analysis):
                    # 正当な使用と判断された場合は信頼度を下げる
                    issue.confidence = max(0.3, issue.confidence - 0.4)
                    issue.severity = "low"  # 重要度も下げる

                    # 正当化の理由を証拠に追加
                    justification = analysis.get("justification", "")
                    if justification:
                        issue.evidence.append(f"LLM Analysis: {justification}")

                # LLMによる詳細な推奨事項を追加
                enhanced_recommendation = self._get_enhanced_recommendation(
                    call, analysis
                )
                if enhanced_recommendation:
                    issue.recommendation = (
                        f"{issue.recommendation}\n\n"
                        f"## LLM Enhanced Recommendation:\n{enhanced_recommendation}"
                    )

                enhanced_issues.append(issue)

            except Exception as e:
                # LLM分析が失敗した場合は元の問題をそのまま使用
                print(f"Warning: LLM analysis failed: {e}")
                enhanced_issues.append(issue)

        return enhanced_issues

    def _get_llm_analysis(self, call: CassandraCall) -> Dict[str, Any]:
        """
        LLMによるクエリ分析

        Args:
            call: Cassandra呼び出し情報

        Returns:
            LLM分析結果の辞書
        """
        if not self.llm_enabled:
            return {}

        try:
            # カスタムプロンプトを構築
            context = f"""
Analyze the following Cassandra query for ALLOW FILTERING usage:

Query: {call.cql_text}
Method: {call.method_name}
Class: {call.class_name or 'Unknown'}
Method Context: {call.method_context or 'Unknown'}

Determine if the use of ALLOW FILTERING is justified based on:
1. Query selectivity (low cardinality filtering is acceptable)
2. Dataset size (small tables may be acceptable)
3. Query frequency (rare administrative queries may be acceptable)
4. Use case context (batch processing vs real-time queries)

Provide your analysis in JSON format with:
- justified: boolean (true if use is justified)
- justification: string (reason for justification or concern)
- impact: string (expected performance impact)
- alternatives: list of strings (better alternatives if not justified)
"""

            response = self.llm_analyzer.client.analyze_code(
                code=call.cql_text,
                prompt=context,
                max_tokens=1024,
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

    def _is_justified_use(self, analysis: Dict[str, Any]) -> bool:
        """
        LLM分析結果から正当な使用かを判定

        Args:
            analysis: LLM分析結果

        Returns:
            正当な使用の場合True
        """
        if not analysis:
            return False

        return analysis.get("justified", False)

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

        # 影響分析
        impact = analysis.get("impact", "")
        if impact:
            recommendations.append(f"**Performance Impact**: {impact}")

        # 代替案
        alternatives = analysis.get("alternatives", [])
        if alternatives:
            recommendations.append("\n**Recommended Alternatives**:")
            for i, alt in enumerate(alternatives, 1):
                recommendations.append(f"{i}. {alt}")

        # 正当化された場合の注意事項
        if analysis.get("justified", False):
            justification = analysis.get("justification", "")
            recommendations.append(
                f"\n**Note**: While this use may be justified ({justification}), "
                "consider monitoring query performance and dataset growth."
            )

        return "\n".join(recommendations)
