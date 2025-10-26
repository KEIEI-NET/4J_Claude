"""
LLMベースのコード分析エンジン

Claude APIを使用してCassandraコードを分析し、
問題を検出して推奨事項を生成
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from cassandra_analyzer.models import CassandraCall, Issue
from .anthropic_client import AnthropicClient


class LLMAnalyzer:
    """
    LLMベースのコード分析エンジン

    AnthropicClientを使用してコードを分析し、
    問題を検出して詳細な推奨事項を生成
    """

    def __init__(
        self,
        client: Optional[AnthropicClient] = None,
        prompts_dir: Optional[Path] = None,
    ):
        """
        Args:
            client: AnthropicClient（Noneの場合は新規作成）
            prompts_dir: プロンプトテンプレートのディレクトリ
        """
        self.client = client or AnthropicClient()

        # プロンプトディレクトリの設定
        if prompts_dir is None:
            self.prompts_dir = Path(__file__).parent / "prompts"
        else:
            self.prompts_dir = prompts_dir

        # プロンプトテンプレートのロード
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """プロンプトテンプレートをロード"""
        prompts = {}

        # デフォルトプロンプトを設定
        prompts["code_analysis"] = self._get_default_code_analysis_prompt()
        prompts["issue_detection"] = self._get_default_issue_detection_prompt()
        prompts["recommendation"] = self._get_default_recommendation_prompt()

        # ファイルから読み込み（存在する場合）
        if self.prompts_dir.exists():
            for prompt_file in self.prompts_dir.glob("*.txt"):
                prompt_name = prompt_file.stem
                prompts[prompt_name] = prompt_file.read_text(encoding="utf-8")

        return prompts

    def _get_default_code_analysis_prompt(self) -> str:
        """デフォルトのコード分析プロンプト"""
        return """You are an expert in Apache Cassandra and Java development.

Analyze the following Java code that uses Cassandra and identify potential issues.

Focus on:
1. ALLOW FILTERING usage (performance concern)
2. Missing partition keys in WHERE clauses (critical performance issue)
3. Large batch operations (memory/network concerns)
4. Unprepared statements (security/performance concern)

For each issue found, provide:
- Issue type
- Severity (critical, high, medium, low)
- Line number (if identifiable)
- Detailed explanation
- Recommended fix

Respond in JSON format:
{
  "issues": [
    {
      "type": "ISSUE_TYPE",
      "severity": "high",
      "line": 42,
      "explanation": "...",
      "recommendation": "..."
    }
  ]
}"""

    def _get_default_issue_detection_prompt(self) -> str:
        """デフォルトの問題検出プロンプト"""
        return """Analyze this Cassandra query and identify any issues:

{cql_query}

Provide a brief analysis focusing on performance and best practices."""

    def _get_default_recommendation_prompt(self) -> str:
        """デフォルトの推奨事項プロンプト"""
        return """Given this Cassandra-related issue, provide a detailed recommendation:

Issue: {issue_description}

CQL Query:
{cql_query}

Provide specific, actionable steps to fix this issue."""

    def analyze_code_file(self, file_path: str, code: str) -> List[Issue]:
        """
        コードファイルを分析して問題を検出

        Args:
            file_path: ファイルパス
            code: Javaコード

        Returns:
            検出された問題のリスト
        """
        prompt = self.prompts["code_analysis"]

        try:
            # LLMで分析
            response = self.client.analyze_code(
                code=code,
                prompt=prompt,
                max_tokens=4096,
                temperature=0.0,
            )

            # JSONレスポンスをパース
            issues = self._parse_analysis_response(response, file_path)
            return issues

        except Exception as e:
            # エラーの場合は空のリストを返す
            # （分析を継続するため）
            return []

    def _parse_analysis_response(
        self, response: str, file_path: str
    ) -> List[Issue]:
        """
        LLMのレスポンスをパースしてIssueオブジェクトに変換

        Args:
            response: LLMのレスポンス
            file_path: ファイルパス

        Returns:
            Issueオブジェクトのリスト
        """
        issues = []

        try:
            # JSONの抽出（マークダウンコードブロック内の可能性あり）
            json_text = response
            if "```json" in response:
                # ```json ... ``` を抽出
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_text = response[start:end].strip()
            elif "```" in response:
                # ``` ... ``` を抽出
                start = response.find("```") + 3
                end = response.find("```", start)
                json_text = response[start:end].strip()

            # JSONパース
            data = json.loads(json_text)

            # Issueオブジェクトに変換
            for issue_data in data.get("issues", []):
                issue = Issue(
                    detector_name="LLMAnalyzer",
                    issue_type=issue_data.get("type", "UNKNOWN"),
                    severity=issue_data.get("severity", "medium"),
                    file_path=file_path,
                    line_number=issue_data.get("line", 0),
                    message=issue_data.get("explanation", ""),
                    cql_text=issue_data.get("cql", ""),
                    recommendation=issue_data.get("recommendation", ""),
                    evidence=[issue_data.get("explanation", "")],
                    confidence=0.9,  # LLMの信頼度
                )
                issues.append(issue)

        except json.JSONDecodeError:
            # JSONパースエラーの場合は空のリストを返す
            pass
        except Exception:
            # その他のエラーも無視
            pass

        return issues

    def analyze_cassandra_call(self, call: CassandraCall) -> Optional[str]:
        """
        Cassandra呼び出しを分析

        Args:
            call: Cassandra呼び出し情報

        Returns:
            分析結果のテキスト（エラーの場合はNone）
        """
        prompt = self.prompts["issue_detection"].format(
            cql_query=call.cql_text
        )

        try:
            response = self.client.analyze_code(
                code=call.cql_text,
                prompt=prompt,
                max_tokens=1024,
                temperature=0.0,
            )
            return response

        except Exception:
            return None

    def enhance_issue(self, issue: Issue) -> Issue:
        """
        検出された問題をLLMで強化（推奨事項の詳細化）

        Args:
            issue: 元の問題

        Returns:
            強化された問題
        """
        try:
            # LLMで推奨事項を生成
            recommendation = self.client.generate_recommendation(
                issue_description=f"{issue.issue_type}: {issue.message}",
                code_context=issue.cql_text,
                max_tokens=1024,
            )

            # 推奨事項を更新
            enhanced_issue = Issue(
                detector_name=issue.detector_name,
                issue_type=issue.issue_type,
                severity=issue.severity,
                file_path=issue.file_path,
                line_number=issue.line_number,
                message=issue.message,
                cql_text=issue.cql_text,
                recommendation=recommendation,  # LLM生成の推奨事項
                evidence=issue.evidence,
                confidence=issue.confidence,
            )

            return enhanced_issue

        except Exception:
            # エラーの場合は元の問題をそのまま返す
            return issue

    def batch_enhance_issues(self, issues: List[Issue]) -> List[Issue]:
        """
        複数の問題を一括で強化

        Args:
            issues: 問題のリスト

        Returns:
            強化された問題のリスト
        """
        enhanced_issues = []

        for issue in issues:
            enhanced = self.enhance_issue(issue)
            enhanced_issues.append(enhanced)

        return enhanced_issues

    def get_context_aware_analysis(
        self,
        code: str,
        table_schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        コンテキストを考慮した分析

        Args:
            code: Javaコード
            table_schema: Cassandraテーブルスキーマ（オプション）

        Returns:
            分析結果の辞書
        """
        # コンテキストを含むプロンプトを構築
        context_parts = []
        if table_schema:
            context_parts.append(f"Table Schema:\n{table_schema}")

        context = "\n\n".join(context_parts) if context_parts else ""

        prompt = f"""{self.prompts["code_analysis"]}

{context}

Analyze the code considering the provided context."""

        try:
            response = self.client.analyze_code(
                code=code,
                prompt=prompt,
                max_tokens=4096,
                temperature=0.0,
            )

            return {
                "success": True,
                "analysis": response,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
