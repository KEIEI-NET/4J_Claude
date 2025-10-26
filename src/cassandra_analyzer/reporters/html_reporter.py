"""
HTMLレポーター

分析結果をHTML形式で出力
"""
from typing import Optional
from collections import defaultdict
from datetime import datetime

from cassandra_analyzer.models import AnalysisResult, Issue
from cassandra_analyzer.reporters.base import BaseReporter


class HTMLReporter(BaseReporter):
    """
    HTML形式レポーター

    分析結果をHTML形式で出力する
    埋め込みCSSとJavaScriptを含む
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: レポーター設定
                - title: レポートタイトル（デフォルト: "Cassandra Analysis Report"）
                - include_timestamp: タイムスタンプを含める（デフォルト: True）
        """
        super().__init__(config)
        self.title = self.config.get("title", "Cassandra Analysis Report")
        self.include_timestamp = self.config.get("include_timestamp", True)

    @property
    def format_name(self) -> str:
        """レポート形式の名前"""
        return "HTML"

    @property
    def file_extension(self) -> str:
        """デフォルトのファイル拡張子"""
        return ".html"

    def generate(self, result: AnalysisResult) -> str:
        """
        分析結果からHTMLレポートを生成

        Args:
            result: 分析結果

        Returns:
            HTML形式のレポート文字列
        """
        html = []

        # HTML開始
        html.append("<!DOCTYPE html>")
        html.append("<html lang='ja'>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append(f"    <title>{self.title}</title>")
        html.append(self._generate_css())
        html.append("</head>")
        html.append("<body>")

        # ヘッダー
        html.append(self._generate_header(result))

        # サマリーセクション
        html.append(self._generate_summary(result))

        # 問題セクション
        html.append(self._generate_issues(result))

        # フッター
        html.append(self._generate_footer())

        # JavaScript
        html.append(self._generate_javascript())

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)

    def _generate_css(self) -> str:
        """埋め込みCSSを生成"""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }

        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        header p {
            opacity: 0.9;
        }

        .summary {
            padding: 30px;
            border-bottom: 1px solid #e0e0e0;
        }

        .summary h2 {
            margin-bottom: 20px;
            color: #667eea;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-card {
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .stat-card h3 {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }

        .stat-card .number {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .severity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .severity-card {
            padding: 15px;
            background-color: white;
            border-radius: 8px;
            border: 2px solid;
            text-align: center;
        }

        .severity-card.critical {
            border-color: #dc3545;
        }

        .severity-card.high {
            border-color: #fd7e14;
        }

        .severity-card.medium {
            border-color: #ffc107;
        }

        .severity-card.low {
            border-color: #17a2b8;
        }

        .severity-card .label {
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .severity-card .count {
            font-size: 1.8em;
            font-weight: bold;
        }

        .issues-section {
            padding: 30px;
        }

        .issues-section h2 {
            margin-bottom: 20px;
            color: #667eea;
        }

        .filter-controls {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }

        .filter-controls label {
            margin-right: 20px;
            cursor: pointer;
        }

        .filter-controls input[type="checkbox"] {
            margin-right: 5px;
        }

        .issue {
            margin-bottom: 20px;
            padding: 20px;
            background-color: white;
            border-left: 4px solid;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .issue.critical {
            border-left-color: #dc3545;
        }

        .issue.high {
            border-left-color: #fd7e14;
        }

        .issue.medium {
            border-left-color: #ffc107;
        }

        .issue.low {
            border-left-color: #17a2b8;
        }

        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .issue-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }

        .severity-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            color: white;
        }

        .severity-badge.critical {
            background-color: #dc3545;
        }

        .severity-badge.high {
            background-color: #fd7e14;
        }

        .severity-badge.medium {
            background-color: #ffc107;
            color: #333;
        }

        .severity-badge.low {
            background-color: #17a2b8;
        }

        .issue-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }

        .issue-meta span {
            margin-right: 15px;
        }

        .issue-message {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }

        .code-block {
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
        }

        .code-block pre {
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .recommendation {
            margin-top: 15px;
            padding: 15px;
            background-color: #e7f3ff;
            border-left: 4px solid #0066cc;
            border-radius: 4px;
        }

        .recommendation h4 {
            margin-bottom: 10px;
            color: #0066cc;
        }

        .recommendation p {
            white-space: pre-wrap;
        }

        footer {
            padding: 20px 30px;
            background-color: #f8f9fa;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .no-issues {
            text-align: center;
            padding: 60px 20px;
            color: #28a745;
        }

        .no-issues h3 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        @media (max-width: 768px) {
            .stats {
                grid-template-columns: 1fr;
            }

            .severity-grid {
                grid-template-columns: 1fr 1fr;
            }

            .issue-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .severity-badge {
                margin-top: 10px;
            }
        }
    </style>
"""

    def _generate_header(self, result: AnalysisResult) -> str:
        """ヘッダーセクションを生成"""
        lines = []
        lines.append("<div class='container'>")
        lines.append("    <header>")
        lines.append(f"        <h1>{self.title}</h1>")

        if self.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"        <p>Generated at {timestamp}</p>")

        lines.append("    </header>")
        return "\n".join(lines)

    def _generate_summary(self, result: AnalysisResult) -> str:
        """サマリーセクションを生成"""
        lines = []
        lines.append("    <div class='summary'>")
        lines.append("        <h2>📊 Summary</h2>")
        lines.append("        <div class='stats'>")
        lines.append("            <div class='stat-card'>")
        lines.append("                <h3>Files Analyzed</h3>")
        lines.append(f"                <div class='number'>{result.total_files}</div>")
        lines.append("            </div>")
        lines.append("            <div class='stat-card'>")
        lines.append("                <h3>Cassandra Calls</h3>")
        lines.append(f"                <div class='number'>{result.total_calls}</div>")
        lines.append("            </div>")
        lines.append("            <div class='stat-card'>")
        lines.append("                <h3>Total Issues</h3>")
        lines.append(f"                <div class='number'>{result.total_issues}</div>")
        lines.append("            </div>")
        lines.append("        </div>")

        # 重要度別カウント
        lines.append("        <div class='severity-grid'>")
        lines.append("            <div class='severity-card critical'>")
        lines.append("                <div class='label'>🔴 Critical</div>")
        lines.append(f"                <div class='count'>{result.critical_count}</div>")
        lines.append("            </div>")
        lines.append("            <div class='severity-card high'>")
        lines.append("                <div class='label'>🟠 High</div>")
        lines.append(f"                <div class='count'>{result.high_count}</div>")
        lines.append("            </div>")
        lines.append("            <div class='severity-card medium'>")
        lines.append("                <div class='label'>🟡 Medium</div>")
        lines.append(f"                <div class='count'>{result.medium_count}</div>")
        lines.append("            </div>")
        lines.append("            <div class='severity-card low'>")
        lines.append("                <div class='label'>🔵 Low</div>")
        lines.append(f"                <div class='count'>{result.low_count}</div>")
        lines.append("            </div>")
        lines.append("        </div>")
        lines.append("    </div>")

        return "\n".join(lines)

    def _generate_issues(self, result: AnalysisResult) -> str:
        """問題セクションを生成"""
        lines = []
        lines.append("    <div class='issues-section'>")
        lines.append("        <h2>🔍 Issues</h2>")

        if not result.issues:
            lines.append("        <div class='no-issues'>")
            lines.append("            <h3>✅ No issues found!</h3>")
            lines.append("            <p>Your code looks good.</p>")
            lines.append("        </div>")
        else:
            # フィルターコントロール
            lines.append("        <div class='filter-controls'>")
            lines.append("            <label><input type='checkbox' class='severity-filter' value='critical' checked> Critical</label>")
            lines.append("            <label><input type='checkbox' class='severity-filter' value='high' checked> High</label>")
            lines.append("            <label><input type='checkbox' class='severity-filter' value='medium' checked> Medium</label>")
            lines.append("            <label><input type='checkbox' class='severity-filter' value='low' checked> Low</label>")
            lines.append("        </div>")

            # 問題リスト（重要度でソート）
            sorted_issues = sorted(
                result.issues, key=lambda x: self._severity_order(x.severity)
            )

            for issue in sorted_issues:
                lines.append(self._format_issue(issue))

        lines.append("    </div>")
        return "\n".join(lines)

    def _format_issue(self, issue: Issue) -> str:
        """個別の問題をHTMLフォーマット"""
        lines = []
        severity = issue.severity

        lines.append(f"        <div class='issue {severity}' data-severity='{severity}'>")
        lines.append("            <div class='issue-header'>")
        lines.append(f"                <div class='issue-title'>{self._escape_html(issue.issue_type)}</div>")
        lines.append(f"                <span class='severity-badge {severity}'>{severity.upper()}</span>")
        lines.append("            </div>")

        lines.append("            <div class='issue-meta'>")
        lines.append(f"                <span>📁 {self._escape_html(issue.file_path)}</span>")
        lines.append(f"                <span>📍 Line {issue.line_number}</span>")
        lines.append(f"                <span>🔍 {self._escape_html(issue.detector_name)}</span>")
        lines.append("            </div>")

        lines.append(f"            <div class='issue-message'>{self._escape_html(issue.message)}</div>")

        # CQL
        if issue.cql_text:
            lines.append("            <div class='code-block'>")
            lines.append("                <strong>CQL Query:</strong>")
            lines.append(f"                <pre>{self._escape_html(issue.cql_text)}</pre>")
            lines.append("            </div>")

        # 推奨事項
        if issue.recommendation:
            lines.append("            <div class='recommendation'>")
            lines.append("                <h4>💡 Recommendation</h4>")
            lines.append(f"                <p>{self._escape_html(issue.recommendation)}</p>")
            lines.append("            </div>")

        lines.append("        </div>")
        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """フッターセクションを生成"""
        lines = []
        lines.append("    <footer>")
        lines.append("        <p>Generated by Cassandra Analyzer</p>")
        lines.append("    </footer>")
        lines.append("</div>")
        return "\n".join(lines)

    def _generate_javascript(self) -> str:
        """JavaScriptを生成"""
        return """
    <script>
        // フィルター機能
        document.addEventListener('DOMContentLoaded', function() {
            const filterCheckboxes = document.querySelectorAll('.severity-filter');
            const issues = document.querySelectorAll('.issue');

            filterCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    updateFilters();
                });
            });

            function updateFilters() {
                const selectedSeverities = Array.from(filterCheckboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);

                issues.forEach(issue => {
                    const severity = issue.getAttribute('data-severity');
                    if (selectedSeverities.includes(severity)) {
                        issue.style.display = 'block';
                    } else {
                        issue.style.display = 'none';
                    }
                });
            }
        });
    </script>
"""

    def _severity_order(self, severity: str) -> int:
        """重要度のソート順を返す"""
        order_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return order_map.get(severity, 999)

    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
