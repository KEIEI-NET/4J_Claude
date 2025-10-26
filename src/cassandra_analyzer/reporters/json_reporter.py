"""
JSONレポーター

分析結果をJSON形式で出力
"""
import json
from typing import Optional

from cassandra_analyzer.models import AnalysisResult
from cassandra_analyzer.reporters.base import BaseReporter


class JSONReporter(BaseReporter):
    """
    JSON形式レポーター

    分析結果をJSON形式で出力する
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: レポーター設定
                - indent: インデント幅（デフォルト: 2）
                - ensure_ascii: ASCII文字のみ使用（デフォルト: False）
        """
        super().__init__(config)
        self.indent = self.config.get("indent", 2)
        self.ensure_ascii = self.config.get("ensure_ascii", False)

    @property
    def format_name(self) -> str:
        """レポート形式の名前"""
        return "JSON"

    @property
    def file_extension(self) -> str:
        """デフォルトのファイル拡張子"""
        return ".json"

    def generate(self, result: AnalysisResult) -> str:
        """
        分析結果からJSONレポートを生成

        Args:
            result: 分析結果

        Returns:
            JSON形式のレポート文字列
        """
        # AnalysisResultをdictに変換
        report_data = {
            "summary": {
                "total_files": result.total_files,
                "total_calls": result.total_calls,
                "total_issues": result.total_issues,
                "critical_issues": result.critical_count,
                "high_issues": result.high_count,
                "medium_issues": result.medium_count,
                "low_issues": result.low_count,
            },
            "issues": [
                {
                    "detector": issue.detector_name,
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "message": issue.message,
                    "cql": issue.cql_text,
                    "recommendation": issue.recommendation,
                    "evidence": issue.evidence,
                    "confidence": issue.confidence,
                }
                for issue in result.issues
            ],
            "files": result.files_analyzed,
        }

        # JSONに変換
        return json.dumps(
            report_data, indent=self.indent, ensure_ascii=self.ensure_ascii
        )
