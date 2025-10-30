"""
LLM Optimizer

LLMを使用したコード最適化エンジン。
Claude APIを利用して、データベースクエリの最適化提案を生成します。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from multidb_analyzer.core.base_detector import Issue
from multidb_analyzer.llm.claude_client import ClaudeClient, ClaudeModel
from multidb_analyzer.llm.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class OptimizationResult:
    """最適化結果"""

    def __init__(
        self,
        issue: Issue,
        root_cause: str,
        performance_impact: str,
        optimized_code: str,
        implementation_steps: List[str],
        testing_strategy: str,
        trade_offs: str,
        confidence_score: float
    ):
        self.issue = issue
        self.root_cause = root_cause
        self.performance_impact = performance_impact
        self.optimized_code = optimized_code
        self.implementation_steps = implementation_steps
        self.testing_strategy = testing_strategy
        self.trade_offs = trade_offs
        self.confidence_score = confidence_score

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            'issue': {
                'title': self.issue.title,
                'severity': self.issue.severity.value,
                'file_path': self.issue.file_path,
                'line_number': self.issue.line_number,
            },
            'root_cause': self.root_cause,
            'performance_impact': self.performance_impact,
            'optimized_code': self.optimized_code,
            'implementation_steps': self.implementation_steps,
            'testing_strategy': self.testing_strategy,
            'trade_offs': self.trade_offs,
            'confidence_score': self.confidence_score
        }


class LLMOptimizer:
    """
    LLM最適化エンジン

    Claude APIを使用して、データベースクエリの最適化提案を生成します。

    機能:
    - 問題の根本原因分析
    - パフォーマンス影響の定量化
    - 最適化コードの生成
    - 実装手順の提供
    - 問題の優先度付け
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: ClaudeModel = ClaudeModel.SONNET,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        """
        LLM Optimizerを初期化

        Args:
            api_key: Claude APIキー
            model: 使用するClaudeモデル
            temperature: 生成の温度（0.0-1.0、低いほど確定的）
            max_tokens: 最大生成トークン数
        """
        self.client = ClaudeClient(api_key=api_key, model=model)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def optimize_issue(
        self,
        issue: Issue,
        code: str,
        language: str = "java",
        db_type: str = "elasticsearch"
    ) -> OptimizationResult:
        """
        単一の問題を最適化

        Args:
            issue: 検出された問題
            code: 元のコード
            language: プログラミング言語
            db_type: データベースタイプ

        Returns:
            最適化結果
        """
        logger.info(f"Optimizing issue: {issue.title}")

        # プロンプトを生成
        if db_type.lower() == "elasticsearch":
            prompt = PromptTemplates.format_elasticsearch_optimization(
                issue=issue,
                code=code,
                language=language
            )
        else:
            # 他のDBタイプ用のフォールバック
            prompt = PromptTemplates.format_elasticsearch_optimization(
                issue=issue,
                code=code,
                language=language
            )

        # Claude APIで最適化提案を生成
        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=PromptTemplates.SYSTEM_PROMPT,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # JSONレスポンスを解析
            result_data = self._parse_optimization_response(response)

            return OptimizationResult(
                issue=issue,
                root_cause=result_data.get('root_cause', 'Analysis not available'),
                performance_impact=result_data.get('performance_impact', 'Not quantified'),
                optimized_code=result_data.get('optimized_code', code),
                implementation_steps=result_data.get('implementation_steps', []),
                testing_strategy=result_data.get('testing_strategy', 'Standard unit tests'),
                trade_offs=result_data.get('trade_offs', 'None identified'),
                confidence_score=result_data.get('confidence_score', 0.8)
            )

        except Exception as e:
            logger.error(f"Failed to optimize issue: {e}")
            # フォールバック: 基本的な結果を返す
            return OptimizationResult(
                issue=issue,
                root_cause="LLM analysis failed",
                performance_impact="Unknown",
                optimized_code=code,
                implementation_steps=[issue.suggestion],
                testing_strategy="Manual testing required",
                trade_offs="N/A",
                confidence_score=0.0
            )

    def optimize_batch(
        self,
        issues: List[Issue],
        code_snippets: Dict[str, str],
        language: str = "java",
        db_type: str = "elasticsearch"
    ) -> List[OptimizationResult]:
        """
        複数の問題をバッチで最適化

        Args:
            issues: 問題のリスト
            code_snippets: 問題IDとコードのマッピング
            language: プログラミング言語
            db_type: データベースタイプ

        Returns:
            最適化結果のリスト
        """
        results = []

        for issue in issues:
            # コードスニペットを取得（存在しない場合はクエリテキストを使用）
            code = code_snippets.get(
                f"{issue.file_path}:{issue.line_number}",
                issue.query_text or ""
            )

            result = self.optimize_issue(
                issue=issue,
                code=code,
                language=language,
                db_type=db_type
            )
            results.append(result)

        return results

    def prioritize_issues(
        self,
        issues: List[Issue]
    ) -> Dict[str, Any]:
        """
        問題の優先度付け

        Args:
            issues: 問題のリスト

        Returns:
            優先度付け結果
        """
        logger.info(f"Prioritizing {len(issues)} issues")

        prompt = PromptTemplates.format_prioritize_issues(issues)

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=PromptTemplates.SYSTEM_PROMPT,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return self._parse_json_response(response)

        except Exception as e:
            logger.error(f"Failed to prioritize issues: {e}")
            # フォールバック: シンプルな優先度付け
            return {
                'prioritized_issues': [
                    {
                        'issue_id': i,
                        'priority_score': self._calculate_simple_priority(issue),
                        'recommended_order': i + 1
                    }
                    for i, issue in enumerate(issues)
                ],
                'quick_wins': [],
                'high_risk_high_reward': [],
                'technical_debt': []
            }

    def generate_auto_fix(
        self,
        issue: Issue,
        code: str,
        db_type: str = "elasticsearch",
        framework: str = "Spring Data",
        language: str = "java"
    ) -> Dict[str, Any]:
        """
        自動修正コードを生成

        Args:
            issue: 問題
            code: 元のコード
            db_type: データベースタイプ
            framework: フレームワーク
            language: プログラミング言語

        Returns:
            自動修正情報
        """
        logger.info(f"Generating auto-fix for: {issue.title}")

        prompt = PromptTemplates.format_auto_fix(
            issue=issue,
            code=code,
            db_type=db_type,
            framework=framework,
            language=language
        )

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=PromptTemplates.SYSTEM_PROMPT,
                max_tokens=self.max_tokens,
                temperature=0.1  # 低温度で確定的な生成
            )

            # コードブロックを抽出
            fixed_code = self._extract_code_block(response, language)

            return {
                'fixed_code': fixed_code,
                'confidence': 0.9,  # デフォルト
                'breaking_changes': False,
                'migration_notes': 'Please review the changes before applying'
            }

        except Exception as e:
            logger.error(f"Failed to generate auto-fix: {e}")
            return {
                'fixed_code': code,
                'confidence': 0.0,
                'breaking_changes': False,
                'migration_notes': 'Auto-fix generation failed'
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        """API使用統計を取得"""
        return self.client.get_usage_stats()

    # プライベートメソッド

    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """最適化レスポンスを解析"""
        try:
            # JSONブロックを抽出
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

            logger.warning("No JSON found in response, using raw response")
            return {'raw_response': response}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {'raw_response': response}

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSONレスポンスを解析"""
        return self._parse_optimization_response(response)

    def _extract_code_block(self, response: str, language: str) -> str:
        """コードブロックを抽出"""
        # ```language または ``` で囲まれたコードを探す
        markers = [f"```{language}", "```java", "```"]

        for marker in markers:
            start = response.find(marker)
            if start >= 0:
                start += len(marker)
                end = response.find("```", start)
                if end > start:
                    return response[start:end].strip()

        # コードブロックが見つからない場合はレスポンス全体を返す
        return response.strip()

    def _calculate_simple_priority(self, issue: Issue) -> float:
        """シンプルな優先度計算"""
        severity_scores = {
            'CRITICAL': 10.0,
            'HIGH': 7.5,
            'MEDIUM': 5.0,
            'LOW': 2.5,
            'INFO': 1.0
        }
        return severity_scores.get(issue.severity.value, 5.0)
