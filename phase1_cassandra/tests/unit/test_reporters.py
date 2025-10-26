"""
レポーターのユニットテスト
"""
import json
import pytest
from pathlib import Path

from cassandra_analyzer.reporters import (
    BaseReporter,
    JSONReporter,
    MarkdownReporter,
    HTMLReporter,
)
from cassandra_analyzer.models import AnalysisResult, Issue


@pytest.fixture
def sample_issues():
    """サンプルの問題リスト"""
    return [
        Issue(
            detector_name="AllowFilteringDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="ALLOW FILTERING detected",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            recommendation="Create Materialized View",
            evidence=["Query type: SELECT", "Target table: users"],
            confidence=0.9,
        ),
        Issue(
            detector_name="PartitionKeyDetector",
            issue_type="NO_PARTITION_KEY",
            severity="critical",
            file_path="test.java",
            line_number=20,
            message="Partition Key not used",
            cql_text="SELECT * FROM orders WHERE order_date > ?",
            recommendation="Add partition key to WHERE clause",
            evidence=["Query type: SELECT", "No partition key found"],
            confidence=0.95,
        ),
        Issue(
            detector_name="PreparedStatementDetector",
            issue_type="UNPREPARED_STATEMENT",
            severity="low",
            file_path="other.java",
            line_number=30,
            message="Prepared Statement not used",
            cql_text="SELECT * FROM products WHERE id = ?",
            recommendation="Use PreparedStatement",
            evidence=["Unprepared statement detected"],
            confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_result(sample_issues):
    """サンプルの分析結果"""
    # 重要度別カウント
    issues_by_severity = {"critical": 1, "high": 1, "medium": 0, "low": 1}

    result = AnalysisResult(
        analyzed_files=["test.java", "other.java"],
        total_issues=len(sample_issues),
        issues_by_severity=issues_by_severity,
        issues=sample_issues,
    )
    return result


class TestJSONReporter:
    """JSONReporterのテストクラス"""

    @pytest.fixture
    def reporter(self):
        """JSONReporterのフィクスチャ"""
        return JSONReporter()

    def test_format_name(self, reporter):
        """形式名のテスト"""
        assert reporter.format_name == "JSON"

    def test_file_extension(self, reporter):
        """ファイル拡張子のテスト"""
        assert reporter.file_extension == ".json"

    def test_generate(self, reporter, sample_result):
        """レポート生成のテスト"""
        report = reporter.generate(sample_result)

        # JSON形式であることを確認
        data = json.loads(report)

        # サマリーの確認
        assert "summary" in data
        assert data["summary"]["total_files"] == 2
        assert data["summary"]["total_calls"] == 3
        assert data["summary"]["total_issues"] == 3
        assert data["summary"]["critical_issues"] == 1
        assert data["summary"]["high_issues"] == 1
        assert data["summary"]["low_issues"] == 1

        # 問題の確認
        assert "issues" in data
        assert len(data["issues"]) == 3

        # 最初の問題の詳細確認
        first_issue = data["issues"][0]
        assert first_issue["type"] == "ALLOW_FILTERING"
        assert first_issue["severity"] == "high"
        assert first_issue["file"] == "test.java"
        assert first_issue["line"] == 10

    def test_generate_with_custom_indent(self, sample_result):
        """カスタムインデントのテスト"""
        reporter = JSONReporter(config={"indent": 4})
        report = reporter.generate(sample_result)

        # インデントが4スペースになっていることを確認
        lines = report.split("\n")
        # JSON内の最初のキーはインデント4スペース
        assert any(line.startswith("    ") for line in lines)

    def test_save(self, reporter, sample_result, tmp_path):
        """ファイル保存のテスト"""
        output_file = tmp_path / "report.json"
        report = reporter.generate(sample_result)
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

        # 内容が正しいことを確認
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["summary"]["total_issues"] == 3


class TestMarkdownReporter:
    """MarkdownReporterのテストクラス"""

    @pytest.fixture
    def reporter(self):
        """MarkdownReporterのフィクスチャ"""
        return MarkdownReporter()

    def test_format_name(self, reporter):
        """形式名のテスト"""
        assert reporter.format_name == "Markdown"

    def test_file_extension(self, reporter):
        """ファイル拡張子のテスト"""
        assert reporter.file_extension == ".md"

    def test_generate(self, reporter, sample_result):
        """レポート生成のテスト"""
        report = reporter.generate(sample_result)

        # Markdown要素の確認
        assert "# Cassandra Code Analysis Report" in report
        assert "## Summary" in report
        assert "## Issues by File" in report

        # サマリーの確認
        assert "Total Files Analyzed" in report
        assert "Total Cassandra Calls" in report
        assert "Total Issues Found" in report

        # 重要度テーブルの確認
        assert "| Severity | Count |" in report
        assert "🔴 Critical" in report
        assert "🟠 High" in report
        assert "🔵 Low" in report

        # 問題の確認
        assert "ALLOW_FILTERING" in report
        assert "NO_PARTITION_KEY" in report
        assert "UNPREPARED_STATEMENT" in report

        # CQLコードブロックの確認
        assert "```sql" in report

    def test_generate_group_by_severity(self, sample_result):
        """重要度別グループ化のテスト"""
        reporter = MarkdownReporter(config={"group_by_file": False})
        report = reporter.generate(sample_result)

        # 重要度別セクションの確認
        assert "## Issues by Severity" in report
        assert "### 🔴 CRITICAL" in report
        assert "### 🟠 HIGH" in report
        assert "### 🔵 LOW" in report

    def test_generate_no_issues(self, reporter):
        """問題なしの場合のテスト"""
        result = AnalysisResult(
            analyzed_files=["test.java"],
            total_issues=0,
            issues_by_severity={},
            issues=[],
        )
        report = reporter.generate(result)

        assert "✅ No issues found!" in report

    def test_save(self, reporter, sample_result, tmp_path):
        """ファイル保存のテスト"""
        output_file = tmp_path / "report.md"
        report = reporter.generate(sample_result)
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

        # 内容が正しいことを確認
        content = output_file.read_text(encoding="utf-8")
        assert "# Cassandra Code Analysis Report" in content


class TestHTMLReporter:
    """HTMLReporterのテストクラス"""

    @pytest.fixture
    def reporter(self):
        """HTMLReporterのフィクスチャ"""
        return HTMLReporter()

    def test_format_name(self, reporter):
        """形式名のテスト"""
        assert reporter.format_name == "HTML"

    def test_file_extension(self, reporter):
        """ファイル拡張子のテスト"""
        assert reporter.file_extension == ".html"

    def test_generate(self, reporter, sample_result):
        """レポート生成のテスト"""
        report = reporter.generate(sample_result)

        # HTML要素の確認
        assert "<!DOCTYPE html>" in report
        assert "<html lang='ja'>" in report
        assert "</html>" in report

        # メタタグの確認
        assert "<meta charset='UTF-8'>" in report
        assert "<meta name='viewport'" in report

        # タイトルの確認
        assert "<title>" in report

        # スタイルの確認
        assert "<style>" in report
        assert "</style>" in report

        # サマリーセクションの確認
        assert "Summary" in report
        assert "Files Analyzed" in report
        assert "Cassandra Calls" in report
        assert "Total Issues" in report

        # 重要度カードの確認
        assert "Critical" in report
        assert "High" in report
        assert "Low" in report

        # 問題セクションの確認
        assert "ALLOW_FILTERING" in report
        assert "NO_PARTITION_KEY" in report
        assert "UNPREPARED_STATEMENT" in report

        # JavaScriptの確認
        assert "<script>" in report
        assert "severity-filter" in report

    def test_generate_with_custom_title(self, sample_result):
        """カスタムタイトルのテスト"""
        reporter = HTMLReporter(config={"title": "Custom Report"})
        report = reporter.generate(sample_result)

        assert "<title>Custom Report</title>" in report
        assert "<h1>Custom Report</h1>" in report

    def test_generate_no_issues(self, reporter):
        """問題なしの場合のテスト"""
        result = AnalysisResult(
            analyzed_files=["test.java"],
            total_issues=0,
            issues_by_severity={},
            issues=[],
        )
        report = reporter.generate(result)

        assert "✅ No issues found!" in report
        assert "Your code looks good" in report

    def test_html_escaping(self, reporter):
        """HTMLエスケープのテスト"""
        issue = Issue(
            detector_name="TestDetector",
            issue_type="TEST<script>alert('xss')</script>",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="Test & <message>",
            cql_text="SELECT * FROM table WHERE col = '<value>'",
            recommendation="Fix it",
            evidence=[],
            confidence=0.9,
        )

        result = AnalysisResult(
            analyzed_files=["test.java"],
            total_issues=1,
            issues_by_severity={"high": 1},
            issues=[issue],
        )
        report = reporter.generate(result)

        # エスケープされていることを確認
        # issue_typeがエスケープされていることを確認
        assert "TEST&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in report
        # メッセージがエスケープされていることを確認
        assert "Test &amp; &lt;message&gt;" in report
        # CQLがエスケープされていることを確認
        assert "&lt;value&gt;" in report

    def test_escape_html_with_empty_text(self, reporter):
        """空のテキストのHTMLエスケープ"""
        # _escape_htmlメソッドを直接テスト
        assert reporter._escape_html("") == ""
        assert reporter._escape_html(None) == ""

    def test_save(self, reporter, sample_result, tmp_path):
        """ファイル保存のテスト"""
        output_file = tmp_path / "report.html"
        report = reporter.generate(sample_result)
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

        # 内容が正しいことを確認
        content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_generate_and_save(self, reporter, sample_result, tmp_path):
        """generate_and_saveメソッドのテスト"""
        output_file = tmp_path / "report.html"
        report = reporter.generate_and_save(sample_result, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

        # 戻り値が正しいことを確認
        assert "<!DOCTYPE html>" in report


class TestBaseReporter:
    """BaseReporterのテストクラス"""

    def test_cannot_instantiate(self):
        """抽象クラスのインスタンス化はできないことを確認"""
        with pytest.raises(TypeError):
            BaseReporter()

    def test_save_creates_directory(self, sample_result, tmp_path):
        """save()がディレクトリを作成することを確認"""
        reporter = JSONReporter()
        nested_dir = tmp_path / "nested" / "dir"
        output_file = nested_dir / "report.json"

        report = reporter.generate(sample_result)
        reporter.save(report, str(output_file))

        # ディレクトリとファイルが作成されたことを確認
        assert nested_dir.exists()
        assert output_file.exists()


class TestReporterIntegration:
    """レポーター統合テスト"""

    def test_all_reporters_produce_output(self, sample_result):
        """全てのレポーターが出力を生成できることを確認"""
        reporters = [
            JSONReporter(),
            MarkdownReporter(),
            HTMLReporter(),
        ]

        for reporter in reporters:
            report = reporter.generate(sample_result)
            assert isinstance(report, str)
            assert len(report) > 0

    def test_all_reporters_save_files(self, sample_result, tmp_path):
        """全てのレポーターがファイルを保存できることを確認"""
        reporters = [
            (JSONReporter(), "report.json"),
            (MarkdownReporter(), "report.md"),
            (HTMLReporter(), "report.html"),
        ]

        for reporter, filename in reporters:
            output_file = tmp_path / filename
            report = reporter.generate(sample_result)
            reporter.save(report, str(output_file))

            assert output_file.exists()
            assert output_file.stat().st_size > 0
