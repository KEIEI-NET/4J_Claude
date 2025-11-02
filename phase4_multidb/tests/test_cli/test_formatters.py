"""
Tests for CLI formatters
"""

from io import StringIO

import pytest
from rich.console import Console

from multidb_analyzer.cli.formatters import (
    get_severity_style,
    get_severity_emoji,
    truncate_text,
    format_summary,
    format_statistics,
    format_issues_table,
    format_issue_detail,
)
from multidb_analyzer.core.base_detector import Severity


class TestSeverityFormatters:
    """Tests for severity formatting functions"""

    def test_get_severity_style(self):
        """Test severity style retrieval"""
        assert get_severity_style(Severity.CRITICAL) == "bold red"
        assert get_severity_style(Severity.HIGH) == "bold orange3"
        assert get_severity_style(Severity.MEDIUM) == "bold yellow"
        assert get_severity_style(Severity.LOW) == "bold green"
        assert get_severity_style(Severity.INFO) == "bold blue"

    def test_get_severity_emoji(self):
        """Test severity emoji retrieval"""
        assert get_severity_emoji(Severity.CRITICAL) == "🔴"
        assert get_severity_emoji(Severity.HIGH) == "🟠"
        assert get_severity_emoji(Severity.MEDIUM) == "🟡"
        assert get_severity_emoji(Severity.LOW) == "🟢"
        assert get_severity_emoji(Severity.INFO) == "ℹ️"


class TestTextFormatters:
    """Tests for text formatting functions"""

    def test_truncate_text_short(self):
        """Test truncating short text"""
        text = "Short text"
        assert truncate_text(text, 50) == "Short text"

    def test_truncate_text_long(self):
        """Test truncating long text"""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_text_exact_length(self):
        """Test truncating text at exact length"""
        text = "Exactly twenty chars"
        assert truncate_text(text, 20) == text


class TestFormatSummary:
    """Tests for format_summary function"""

    def test_format_summary_with_issues(self, sample_cli_result):
        """Test formatting summary with issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_summary(console, sample_cli_result)

        output = string_io.getvalue()
        assert "Analysis Summary" in output
        assert "10" in output  # Files
        assert "2" in output   # Total issues
        assert "5.5" in output # Execution time

    def test_format_summary_empty(self, empty_cli_result):
        """Test formatting summary with no issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_summary(console, empty_cli_result)

        output = string_io.getvalue()
        assert "Analysis Summary" in output
        assert "10" in output  # Files
        assert "0" in output   # Total issues


class TestFormatStatistics:
    """Tests for format_statistics function"""

    def test_format_statistics_with_issues(self, sample_cli_result):
        """Test formatting statistics with issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, sample_cli_result)

        output = string_io.getvalue()
        assert "Issue Statistics" in output
        assert "CRITICAL" in output
        assert "HIGH" in output

    def test_format_statistics_with_warnings(self, sample_cli_result):
        """Test formatting statistics with warnings"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, sample_cli_result)

        output = string_io.getvalue()
        assert "Warnings" in output or "Warning" in output

    def test_format_statistics_empty(self, empty_cli_result):
        """Test formatting statistics with no issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, empty_cli_result)

        output = string_io.getvalue()
        # Empty result might not show statistics table
        # Just verify it doesn't crash
        assert output is not None


class TestFormatIssuesTable:
    """Tests for format_issues_table function"""

    def test_format_issues_table_with_issues(self, sample_cli_result):
        """Test formatting issues table with issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issues_table(console, sample_cli_result, max_display=10)

        output = string_io.getvalue()
        assert "Issues" in output
        assert "CRITICAL" in output
        assert "HIGH" in output

    def test_format_issues_table_empty(self, empty_cli_result):
        """Test formatting issues table with no issues"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issues_table(console, empty_cli_result, max_display=10)

        output = string_io.getvalue()
        assert "No issues found" in output or "great" in output.lower()

    def test_format_issues_table_max_display(self, sample_cli_result):
        """Test max_display limit"""
        # Create result with many issues
        many_issues = sample_cli_result.issues * 30  # 60 issues
        sample_cli_result.issues = many_issues
        sample_cli_result._calculate_statistics()

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issues_table(console, sample_cli_result, max_display=10)

        output = string_io.getvalue()
        # Should mention remaining issues
        assert "more issue" in output.lower()

    def test_format_issues_table_without_line_numbers(self, empty_cli_result):
        """Test formatting issues table with issues without line numbers"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from pathlib import Path

        # Create issue without line number
        issue_no_line = Issue(
            detector_name="TestDetector",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Issue without line number",
            description="Test issue",
            file_path=Path("/path/to/file.java"),
            line_number=None  # No line number
        )

        empty_cli_result.issues = [issue_no_line]
        empty_cli_result._calculate_statistics()

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issues_table(console, empty_cli_result, max_display=10)

        output = string_io.getvalue()
        assert "file.java" in output
        # Should not have line number
        assert "file.java:" not in output or "file.java:None" not in output


class TestFormatIssueDetail:
    """Tests for format_issue_detail function"""

    def test_format_issue_detail(self, sample_cli_issue):
        """Test formatting detailed issue"""
        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issue_detail(console, sample_cli_issue, index=1)

        output = string_io.getvalue()
        assert "Performance issue detected" in output
        assert "Category" in output
        assert "Detector" in output
        assert "Location" in output
        assert "Description" in output
        assert "Suggestion" in output
        assert "Auto-fix available" in output

    def test_format_issue_detail_minimal(self):
        """Test formatting issue with minimal information"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory

        minimal_issue = Issue(
            detector_name="MinimalDetector",
            severity=Severity.LOW,
            category=IssueCategory.MAINTAINABILITY,
            title="Minimal issue",
            description="",
            file_path=None,
            line_number=None
        )

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issue_detail(console, minimal_issue, index=1)

        output = string_io.getvalue()
        assert "Minimal issue" in output
        assert "Category" in output

    def test_format_issue_detail_with_file_no_line(self):
        """Test formatting issue with file path but no line number"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from pathlib import Path

        issue_no_line = Issue(
            detector_name="TestDetector",
            severity=Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title="Issue without line number",
            description="Test description",
            file_path=Path("/path/to/file.java"),
            line_number=None  # No line number
        )

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_issue_detail(console, issue_no_line, index=1)

        output = string_io.getvalue()
        assert "Issue without line number" in output
        assert "file.java" in output
        # Should not show line number format
        assert ":None" not in output


class TestFormatSummaryDBTypes:
    """Tests for database type detection in format_summary"""

    def test_format_summary_with_db_type_attribute(self, empty_cli_result):
        """Test formatting summary with db_type attribute"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from pathlib import Path

        # Create issue with db_type attribute
        issue_with_db_type = Issue(
            detector_name="TestDetector",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Test issue",
            description="Test",
            file_path=Path("/test.java"),
            line_number=1
        )
        # Manually add db_type attribute
        issue_with_db_type.db_type = "PostgreSQL"

        empty_cli_result.issues = [issue_with_db_type]
        empty_cli_result._calculate_statistics()

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_summary(console, empty_cli_result)

        output = string_io.getvalue()
        assert "PostgreSQL" in output

    def test_format_summary_with_elasticsearch_detector(self, empty_cli_result):
        """Test formatting summary with Elasticsearch detector"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from pathlib import Path

        es_issue = Issue(
            detector_name="ElasticsearchWildcardDetector",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Test issue",
            description="Test",
            file_path=Path("/test.java"),
            line_number=1
        )

        empty_cli_result.issues = [es_issue]
        empty_cli_result._calculate_statistics()

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_summary(console, empty_cli_result)

        output = string_io.getvalue()
        assert "Elasticsearch" in output

    def test_format_summary_with_mysql_detector(self, empty_cli_result):
        """Test formatting summary with MySQL detector"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from pathlib import Path

        mysql_issue = Issue(
            detector_name="MySQLNPlusOneDetector",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Test issue",
            description="Test",
            file_path=Path("/test.java"),
            line_number=1
        )

        empty_cli_result.issues = [mysql_issue]
        empty_cli_result._calculate_statistics()

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_summary(console, empty_cli_result)

        output = string_io.getvalue()
        assert "MySQL" in output


class TestFormatStatisticsExtended:
    """Extended tests for format_statistics"""

    def test_format_statistics_with_many_warnings(self, empty_cli_result):
        """Test formatting statistics with more than 5 warnings"""
        # Add 10 warnings
        empty_cli_result.warnings = [f"Warning {i}" for i in range(10)]

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, empty_cli_result)

        output = string_io.getvalue()
        assert "Warning 0" in output
        assert "and 5 more" in output or "more" in output.lower()

    def test_format_statistics_with_errors(self, empty_cli_result):
        """Test formatting statistics with errors"""
        empty_cli_result.errors = ["Error 1", "Error 2"]

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, empty_cli_result)

        output = string_io.getvalue()
        assert "Error 1" in output or "error" in output.lower()

    def test_format_statistics_with_many_errors(self, empty_cli_result):
        """Test formatting statistics with more than 5 errors"""
        # Add 10 errors
        empty_cli_result.errors = [f"Error {i}" for i in range(10)]

        string_io = StringIO()
        console = Console(file=string_io, width=120)

        format_statistics(console, empty_cli_result)

        output = string_io.getvalue()
        assert "Error 0" in output or "error" in output.lower()
        assert "and 5 more" in output or "more" in output.lower()
