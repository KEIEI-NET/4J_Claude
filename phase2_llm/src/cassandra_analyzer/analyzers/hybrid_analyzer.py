"""
Hybrid Analysis Engine

静的解析とLLM分析を統合するエンジン
"""

from __future__ import annotations  # PEP 563: 型ヒントを文字列として扱う

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import asyncio
import logging

# Phase 1のモジュールをインポートパスに追加
phase1_path = Path(__file__).parent.parent.parent.parent.parent / "phase1_cassandra" / "src"
phase1_path_resolved = phase1_path.resolve()
if phase1_path_resolved.exists() and str(phase1_path_resolved) not in sys.path:
    sys.path.insert(0, str(phase1_path_resolved))

# Phase 1からのインポート
if TYPE_CHECKING:
    from cassandra_analyzer.models.issue import Issue
else:
    # 実行時は__init__.pyから取得
    from ..models import Issue

# Phase 1のパーサー、検出器、LLMクライアントをインポート
# 専用のインポートヘルパーを使用（名前空間の競合を回避）
from .phase1_imports import (
    JavaCassandraParser,
    AllowFilteringDetector,
    PartitionKeyDetector,
    BatchSizeDetector,
    PreparedStatementDetector,
    AnthropicClient,
    LLMAnalyzer,
)

from ..models.confidence import AnalysisConfidence
from ..models.hybrid_result import HybridAnalysisResult


logger = logging.getLogger(__name__)


class HybridAnalysisEngine:
    """
    静的解析とLLM分析を統合するハイブリッド分析エンジン

    4つの分析モード:
    - quick: 静的解析のみ
    - standard: 静的解析 + 条件付きLLM
    - comprehensive: 静的解析 + フルLLM
    - critical_only: Criticalな問題のみLLM分析
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_llm: bool = True,
        llm_threshold_severity: str = "high"
    ):
        """
        初期化

        Args:
            api_key: Claude API Key
            enable_llm: LLM分析を有効にするか
            llm_threshold_severity: LLM分析を実行する最小重要度（critical/high/medium/low）
        """
        # Phase 1のパーサーと検出器
        self.parser = JavaCassandraParser()
        self.detectors = [
            AllowFilteringDetector(),
            PartitionKeyDetector(),
            BatchSizeDetector(),
            PreparedStatementDetector(),
        ]

        # LLM関連
        self.enable_llm = enable_llm
        self.llm_threshold_severity = llm_threshold_severity
        self.anthropic_client = AnthropicClient(api_key=api_key) if enable_llm else None
        self.llm_analyzer = LLMAnalyzer(client=self.anthropic_client) if enable_llm else None

        self._severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    async def analyze_code(
        self,
        file_path: str,
        analysis_type: str = "standard"
    ) -> List[HybridAnalysisResult]:
        """
        コードファイルを分析

        Args:
            file_path: 分析対象のJavaファイルパス
            analysis_type: 分析タイプ（quick/standard/comprehensive/critical_only）

        Returns:
            List[HybridAnalysisResult]: ハイブリッド分析結果のリスト
        """
        logger.info(f"Starting {analysis_type} analysis for {file_path}")

        # Step 1: 静的解析を実行
        static_results = await self._run_static_analysis(file_path)
        logger.info(f"Static analysis found {len(static_results)} issues")

        results: List[HybridAnalysisResult] = []

        # Step 2: 静的解析結果をHybridAnalysisResultに変換
        for static_issue in static_results:
            hybrid_result = HybridAnalysisResult.from_static_only(
                issue=static_issue,
                static_details={
                    "detector": static_issue.detector_name,
                    "detection_method": "pattern_matching"
                }
            )

            # LLM分析が必要か判定
            if self._should_use_llm(static_issue, analysis_type):
                logger.info(f"LLM deep analysis required for {static_issue.issue_type}")
                llm_details = await self._llm_deep_analysis(file_path, static_issue)
                if llm_details:
                    hybrid_result.merge_llm_analysis(
                        llm_details=llm_details,
                        llm_confidence=llm_details.get("confidence", 0.85)
                    )

            results.append(hybrid_result)

        # Step 3: LLM独自の分析（comprehensive モードのみ）
        if analysis_type == "comprehensive" and self.enable_llm:
            logger.info("Running LLM semantic analysis")
            llm_only_results = await self._llm_semantic_analysis(file_path)
            results.extend(llm_only_results)

        logger.info(f"Analysis complete. Total {len(results)} hybrid results")
        return results

    async def _run_static_analysis(self, file_path: str) -> List[Issue]:
        """
        静的解析を実行

        Args:
            file_path: Javaファイルパス

        Returns:
            List[Issue]: 検出された問題のリスト
        """
        # ファイルを解析
        parse_result = self.parser.parse_file(file_path)
        if not parse_result:
            logger.warning(f"Failed to parse {file_path}")
            return []

        # 全検出器を実行
        all_issues: List[Issue] = []
        for detector in self.detectors:
            issues = detector.detect(parse_result)
            all_issues.extend(issues)

        return all_issues

    def _should_use_llm(self, issue: Issue, analysis_type: str) -> bool:
        """
        LLM分析が必要かどうかを判定

        Args:
            issue: 静的解析で検出された問題
            analysis_type: 分析タイプ

        Returns:
            bool: LLM分析が必要な場合True
        """
        if not self.enable_llm:
            return False

        if analysis_type == "quick":
            # quickモードではLLM不使用
            return False

        if analysis_type == "critical_only":
            # criticalな問題のみLLM使用
            return issue.severity == "critical"

        if analysis_type == "comprehensive":
            # 全問題にLLM使用
            return True

        # standardモードの場合、重要度でフィルタ
        if analysis_type == "standard":
            threshold_order = self._severity_order.get(self.llm_threshold_severity, 1)
            issue_order = self._severity_order.get(issue.severity, 3)
            return issue_order <= threshold_order

        return False

    async def _llm_deep_analysis(
        self,
        file_path: str,
        static_issue: Issue
    ) -> Optional[Dict[str, Any]]:
        """
        LLMによる深い分析

        Args:
            file_path: Javaファイルパス
            static_issue: 静的解析で検出された問題

        Returns:
            Optional[Dict[str, Any]]: LLM分析結果
        """
        if not self.llm_analyzer:
            return None

        try:
            # ファイル全体を読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()

            # LLM分析用のプロンプトを構築
            prompt = self._build_deep_analysis_prompt(code_content, static_issue)

            # LLM分析を実行
            response = await asyncio.to_thread(
                self.anthropic_client.analyze_code,
                prompt=prompt,
                max_tokens=2000
            )

            # レスポンスを解析
            llm_result = self._parse_llm_response(response)

            return {
                "analysis": llm_result.get("analysis", ""),
                "confidence": llm_result.get("confidence", 0.85),
                "fix_suggestions": llm_result.get("fix_suggestions", []),
                "impact_scope": llm_result.get("impact_scope", {}),
                "reasoning": llm_result.get("reasoning", ""),
            }

        except Exception as e:
            logger.error(f"LLM deep analysis failed: {e}")
            return None

    def _build_deep_analysis_prompt(self, code: str, issue: Issue) -> str:
        """
        LLM深い分析用のプロンプトを構築

        Args:
            code: コード全体
            issue: 静的解析で検出された問題

        Returns:
            str: プロンプト
        """
        prompt = f"""
以下のJavaコードで、静的解析により潜在的な問題が検出されました。
この問題について深い分析を行い、影響範囲と修正提案を提供してください。

## 検出された問題
- タイプ: {issue.issue_type}
- 重要度: {issue.severity}
- 場所: {issue.file_path}:{issue.line_number}
- メッセージ: {issue.message}
- CQLクエリ: {issue.cql_text}

## コード
```java
{code}
```

## 分析してほしいこと
1. この問題が実際にパフォーマンスや正確性に影響を与えるか
2. 影響範囲（どのメソッド/クラスに影響するか）
3. 具体的な修正提案（コード例を含む）
4. この問題の信頼度（0.0-1.0）

以下のJSON形式で回答してください：
{{
  "analysis": "問題の詳細分析",
  "confidence": 0.85,
  "fix_suggestions": ["修正提案1", "修正提案2"],
  "impact_scope": {{
    "affected_methods": ["method1", "method2"],
    "severity_justification": "なぜこの重要度なのか"
  }},
  "reasoning": "分析の根拠"
}}
"""
        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        LLMレスポンスを解析

        Args:
            response: LLMの生レスポンス

        Returns:
            Dict[str, Any]: 解析されたレスポンス
        """
        import json
        import re

        try:
            # JSON部分を抽出
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")

        # パース失敗時のデフォルト値
        return {
            "analysis": response,
            "confidence": 0.70,
            "fix_suggestions": [],
            "impact_scope": {},
            "reasoning": "Response parsing failed"
        }

    async def _llm_semantic_analysis(
        self,
        file_path: str
    ) -> List[HybridAnalysisResult]:
        """
        LLMによる意味解析（静的解析で検出できない問題を発見）

        Args:
            file_path: Javaファイルパス

        Returns:
            List[HybridAnalysisResult]: LLMのみで検出された問題
        """
        if not self.llm_analyzer:
            return []

        try:
            # ファイル全体を読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()

            # LLM意味解析
            prompt = self._build_semantic_analysis_prompt(code_content, file_path)
            response = await asyncio.to_thread(
                self.anthropic_client.analyze_code,
                prompt=prompt,
                max_tokens=3000
            )

            # レスポンスを解析してHybridAnalysisResultに変換
            llm_issues = self._parse_semantic_response(response, file_path)

            return llm_issues

        except Exception as e:
            logger.error(f"LLM semantic analysis failed: {e}")
            return []

    def _build_semantic_analysis_prompt(self, code: str, file_path: str) -> str:
        """
        LLM意味解析用のプロンプトを構築

        Args:
            code: コード全体
            file_path: ファイルパス

        Returns:
            str: プロンプト
        """
        prompt = f"""
以下のJavaコードを分析し、静的解析では検出できない以下のような問題を発見してください：

1. データモデル設計の問題
   - パーティションキー設計の非効率性
   - クラスタリングキーの順序問題
   - ホットスポットのリスク

2. 一貫性レベルの問題
   - 不適切なConsistency Level
   - Read + Write < Replication Factor の問題

3. クエリパフォーマンスの問題
   - 不要なフルスキャン
   - 非効率なデータ取得パターン

## コード
```java
{code}
```

問題を発見した場合、以下のJSON配列形式で回答してください：
[
  {{
    "issue_type": "DATA_MODEL_ISSUE",
    "severity": "high",
    "line_number": 45,
    "message": "問題の説明",
    "cql_text": "関連するCQLクエリ",
    "recommendation": "推奨される修正方法",
    "confidence": 0.85,
    "fix_suggestions": ["修正提案1"],
    "impact_scope": {{}}
  }}
]

問題が見つからない場合は空配列 [] を返してください。
"""
        return prompt

    def _parse_semantic_response(
        self,
        response: str,
        file_path: str
    ) -> List[HybridAnalysisResult]:
        """
        LLM意味解析レスポンスを解析

        Args:
            response: LLMの生レスポンス
            file_path: ファイルパス

        Returns:
            List[HybridAnalysisResult]: 検出された問題のリスト
        """
        import json
        import re

        results: List[HybridAnalysisResult] = []

        try:
            # JSON配列部分を抽出
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                issues_data = json.loads(json_str)

                for issue_data in issues_data:
                    # Issueオブジェクトを作成
                    issue = Issue(
                        detector_name="LLM_Semantic_Analyzer",
                        issue_type=issue_data.get("issue_type", "UNKNOWN"),
                        severity=issue_data.get("severity", "medium"),
                        file_path=file_path,
                        line_number=issue_data.get("line_number", 0),
                        message=issue_data.get("message", ""),
                        cql_text=issue_data.get("cql_text", ""),
                        recommendation=issue_data.get("recommendation", ""),
                        confidence=issue_data.get("confidence", 0.70)
                    )

                    # HybridAnalysisResultを作成
                    hybrid_result = HybridAnalysisResult.from_llm_only(
                        issue=issue,
                        llm_details={
                            "analysis": "LLM semantic analysis",
                            "fix_suggestions": issue_data.get("fix_suggestions", []),
                            "impact_scope": issue_data.get("impact_scope", {}),
                        },
                        llm_confidence=issue_data.get("confidence", 0.70)
                    )

                    results.append(hybrid_result)

        except Exception as e:
            logger.error(f"Failed to parse semantic response: {e}")

        return results

    def get_statistics(self, results: List[HybridAnalysisResult]) -> Dict[str, Any]:
        """
        分析結果の統計情報を取得

        Args:
            results: ハイブリッド分析結果のリスト

        Returns:
            Dict[str, Any]: 統計情報
        """
        total = len(results)
        static_only = sum(1 for r in results if r.has_static_detection and not r.has_llm_detection)
        llm_only = sum(1 for r in results if r.has_llm_detection and not r.has_static_detection)
        hybrid = sum(1 for r in results if r.has_static_detection and r.has_llm_detection)

        confidence_distribution = {}
        for confidence_level in AnalysisConfidence:
            count = sum(1 for r in results if r.confidence_level == confidence_level)
            confidence_distribution[confidence_level.value] = count

        severity_distribution = {}
        for result in results:
            severity = result.issue.severity
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

        return {
            "total_issues": total,
            "detection_sources": {
                "static_only": static_only,
                "llm_only": llm_only,
                "hybrid": hybrid,
            },
            "confidence_distribution": confidence_distribution,
            "severity_distribution": severity_distribution,
            "average_confidence_score": sum(r.confidence_score for r in results) / total if total > 0 else 0,
        }
