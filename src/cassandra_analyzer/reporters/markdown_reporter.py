"""
Markdownレポーター

分析結果をMarkdown形式で出力
"""
from typing import Optional
from collections import defaultdict

from cassandra_analyzer.models import AnalysisResult, Issue
from cassandra_analyzer.reporters.base import BaseReporter


class MarkdownReporter(BaseReporter):
    """
    Markdown形式レポーター

    分析結果をMarkdown形式で出力する
    GitHub Flavored Markdown対応
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: レポーター設定
                - include_evidence: 証拠を含める（デフォルト: True）
                - group_by_file: ファイルごとにグループ化（デフォルト: True）
        """
        super().__init__(config)
        self.include_evidence = self.config.get("include_evidence", True)
        self.group_by_file = self.config.get("group_by_file", True)

    @property
    def format_name(self) -> str:
        """レポート形式の名前"""
        return "Markdown"

    @property
    def file_extension(self) -> str:
        """デフォルトのファイル拡張子"""
        return ".md"

    def generate(self, result: AnalysisResult) -> str:
        """
        分析結果からMarkdownレポートを生成

        Args:
            result: 分析結果

        Returns:
            Markdown形式のレポート文字列
        """
        lines = []

        # タイトル
        lines.append("# Cassandra Code Analysis Report")
        lines.append("")

        # サマリーセクション
        lines.extend(self._generate_summary(result))
        lines.append("")

        # 問題セクション
        if result.issues:
            if self.group_by_file:
                lines.extend(self._generate_issues_by_file(result))
            else:
                lines.extend(self._generate_issues_by_severity(result))
        else:
            lines.append("## Issues")
            lines.append("")
            lines.append("✅ No issues found!")
            lines.append("")

        return "\n".join(lines)

    def _generate_summary(self, result: AnalysisResult) -> list:
        """サマリーセクションを生成"""
        lines = []
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Files Analyzed**: {result.total_files}")
        lines.append(f"- **Total Cassandra Calls**: {result.total_calls}")
        lines.append(f"- **Total Issues Found**: {result.total_issues}")
        lines.append("")

        # 重要度別カウント
        lines.append("### Issues by Severity")
        lines.append("")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| 🔴 Critical | {result.critical_count} |")
        lines.append(f"| 🟠 High | {result.high_count} |")
        lines.append(f"| 🟡 Medium | {result.medium_count} |")
        lines.append(f"| 🔵 Low | {result.low_count} |")
        lines.append("")

        return lines

    def _generate_issues_by_file(self, result: AnalysisResult) -> list:
        """ファイル別に問題を生成"""
        lines = []
        lines.append("## Issues by File")
        lines.append("")

        # ファイルごとにグループ化
        issues_by_file = defaultdict(list)
        for issue in result.issues:
            issues_by_file[issue.file_path].append(issue)

        # ファイル名でソート
        for file_path in sorted(issues_by_file.keys()):
            issues = issues_by_file[file_path]
            lines.append(f"### {file_path}")
            lines.append("")
            lines.append(f"**{len(issues)} issue(s) found**")
            lines.append("")

            # 重要度でソート
            sorted_issues = sorted(
                issues, key=lambda x: self._severity_order(x.severity)
            )

            for issue in sorted_issues:
                lines.extend(self._format_issue(issue))
                lines.append("")

        return lines

    def _generate_issues_by_severity(self, result: AnalysisResult) -> list:
        """重要度別に問題を生成"""
        lines = []
        lines.append("## Issues by Severity")
        lines.append("")

        # 重要度でグループ化
        issues_by_severity = defaultdict(list)
        for issue in result.issues:
            issues_by_severity[issue.severity].append(issue)

        # 重要度順に出力
        for severity in ["critical", "high", "medium", "low"]:
            if severity not in issues_by_severity:
                continue

            issues = issues_by_severity[severity]
            emoji = self._severity_emoji(severity)

            lines.append(f"### {emoji} {severity.upper()} ({len(issues)})")
            lines.append("")

            for issue in issues:
                lines.extend(self._format_issue(issue))
                lines.append("")

        return lines

    def _format_issue(self, issue: Issue) -> list:
        """個別の問題をフォーマット"""
        lines = []

        emoji = self._severity_emoji(issue.severity)
        lines.append(f"#### {emoji} {issue.issue_type}")
        lines.append("")
        lines.append(f"**Severity**: {issue.severity}  ")
        lines.append(f"**Location**: Line {issue.line_number}  ")
        lines.append(f"**Detector**: {issue.detector_name}  ")
        lines.append("")

        # メッセージ
        lines.append(f"**Message**: {issue.message}")
        lines.append("")

        # CQL
        if issue.cql_text:
            lines.append("**CQL Query**:")
            lines.append("```sql")
            lines.append(issue.cql_text)
            lines.append("```")
            lines.append("")

        # 推奨事項
        if issue.recommendation:
            lines.append("**Recommendation**:")
            lines.append("")
            # 推奨事項を箇条書きに変換
            for line in issue.recommendation.split("\n"):
                if line.strip():
                    lines.append(f"> {line}")
            lines.append("")

        # 証拠
        if self.include_evidence and issue.evidence:
            lines.append("<details>")
            lines.append("<summary>Evidence Details</summary>")
            lines.append("")
            for evidence in issue.evidence:
                lines.append(f"- {evidence}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        return lines

    def _severity_emoji(self, severity: str) -> str:
        """重要度に対応する絵文字を返す"""
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
        }
        return emoji_map.get(severity, "⚪")

    def _severity_order(self, severity: str) -> int:
        """重要度のソート順を返す"""
        order_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return order_map.get(severity, 999)
