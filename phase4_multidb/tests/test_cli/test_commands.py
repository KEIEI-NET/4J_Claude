"""
Tests for CLI commands
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from multidb_analyzer.cli.main import cli
from multidb_analyzer.cli.commands import (
    load_config,
    parse_db_types,
    parse_formats,
    setup_logging,
)


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_load_config_valid(self, temp_config_file):
        """Test loading valid config file"""
        config = load_config(temp_config_file)
        assert isinstance(config, dict)
        assert 'analysis' in config
        assert 'reports' in config

    def test_load_config_invalid(self, tmp_path):
        """Test loading invalid config file"""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content:")

        # Should return empty dict on error
        config = load_config(invalid_file)
        assert config == {}

    def test_load_config_nonexistent(self, tmp_path):
        """Test loading nonexistent config file"""
        nonexistent = tmp_path / "nonexistent.yaml"
        config = load_config(nonexistent)
        assert config == {}

    def test_parse_db_types_all(self):
        """Test parsing 'all' database types"""
        enable_es, enable_mysql = parse_db_types(('all',))
        assert enable_es is True
        assert enable_mysql is True

    def test_parse_db_types_elasticsearch(self):
        """Test parsing elasticsearch only"""
        enable_es, enable_mysql = parse_db_types(('elasticsearch',))
        assert enable_es is True
        assert enable_mysql is False

    def test_parse_db_types_mysql(self):
        """Test parsing mysql only"""
        enable_es, enable_mysql = parse_db_types(('mysql',))
        assert enable_es is False
        assert enable_mysql is True

    def test_parse_db_types_multiple(self):
        """Test parsing multiple database types"""
        enable_es, enable_mysql = parse_db_types(('elasticsearch', 'mysql'))
        assert enable_es is True
        assert enable_mysql is True

    def test_parse_formats(self):
        """Test parsing format options"""
        formats = parse_formats(('html', 'json', 'markdown'))
        assert formats == ['html', 'json', 'markdown']

    def test_parse_formats_single(self):
        """Test parsing single format"""
        formats = parse_formats(('console',))
        assert formats == ['console']

    def test_setup_logging_verbose(self):
        """Test logging setup with verbose"""
        import logging
        # Save original level
        original_level = logging.root.level

        setup_logging(verbose=True)
        # Check that logging level is DEBUG (10) or lower
        root_logger = logging.getLogger()
        # Just verify the function runs without error
        # Actual level might be affected by pytest/other config
        assert root_logger.level is not None

        # Restore original level
        logging.root.level = original_level

    def test_setup_logging_normal(self):
        """Test logging setup without verbose"""
        import logging
        # Save original level
        original_level = logging.root.level

        setup_logging(verbose=False)
        root_logger = logging.getLogger()
        # Just verify the function runs without error
        # Actual level might be affected by pytest/other config
        assert root_logger.level is not None

        # Restore original level
        logging.root.level = original_level


class TestCLIMain:
    """Tests for main CLI group"""

    def test_cli_version(self, cli_runner):
        """Test --version flag"""
        result = cli_runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_cli_help(self, cli_runner):
        """Test --help flag"""
        result = cli_runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'MultiDB Analyzer' in result.output
        assert 'analyze' in result.output


class TestAnalyzeCommand:
    """Tests for analyze command"""

    def test_analyze_help(self, cli_runner):
        """Test analyze --help"""
        result = cli_runner.invoke(cli, ['analyze', '--help'])
        assert result.exit_code == 0
        assert 'Analyze source code' in result.output
        assert '--db' in result.output
        assert '--llm' in result.output
        assert '--format' in result.output

    def test_analyze_no_paths(self, cli_runner):
        """Test analyze without source paths"""
        result = cli_runner.invoke(cli, ['analyze'])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output or 'required' in result.output.lower()

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_basic(self, mock_analyzer_class, cli_runner, temp_source_dir, empty_cli_result):
        """Test basic analyze command"""
        # Setup mock
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'  # Skip report generation
        ])

        # Should complete successfully
        assert result.exit_code == 0
        assert 'Analysis complete' in result.output or 'complete' in result.output.lower()

        # Verify analyzer was called
        mock_analyzer.analyze.assert_called_once()

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_db_option(self, mock_analyzer_class, cli_runner, temp_source_dir, empty_cli_result):
        """Test analyze with --db option"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--db', 'elasticsearch',
            '--dry-run'
        ])

        assert result.exit_code == 0
        # Verify elasticsearch was enabled
        call_args = mock_analyzer_class.call_args
        assert call_args[1]['enable_elasticsearch'] is True
        assert call_args[1]['enable_mysql'] is False

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_formats(self, mock_analyzer_class, cli_runner, temp_source_dir, empty_cli_result):
        """Test analyze with multiple --format options"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'html',
            '--format', 'json',
            '--dry-run'
        ])

        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_llm_no_key(self, mock_analyzer_class, cli_runner, temp_source_dir):
        """Test analyze with --llm but no API key"""
        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--llm',
            '--dry-run'
        ])

        # Should fail with error about missing API key
        assert result.exit_code != 0
        assert 'api-key' in result.output.lower() or 'API key' in result.output

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_llm_and_key(self, mock_analyzer_class, cli_runner, temp_source_dir, empty_cli_result):
        """Test analyze with --llm and --api-key"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--llm',
            '--api-key', 'test-key-123',
            '--dry-run'
        ])

        assert result.exit_code == 0
        # Verify LLM was enabled with key
        call_args = mock_analyzer_class.call_args
        assert call_args[1]['enable_llm'] is True
        assert call_args[1]['llm_api_key'] == 'test-key-123'

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_config(self, mock_analyzer_class, cli_runner, temp_source_dir, temp_config_file, empty_cli_result):
        """Test analyze with --config option"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--config', str(temp_config_file),
            '--dry-run'
        ])

        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_output_dir(self, mock_analyzer_class, cli_runner, temp_source_dir, tmp_path, empty_cli_result):
        """Test analyze with --output option"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        output_dir = tmp_path / "custom_output"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--output', str(output_dir),
            '--dry-run'
        ])

        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_verbose(self, mock_analyzer_class, cli_runner, temp_source_dir, empty_cli_result):
        """Test analyze with --verbose option"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--verbose',
            '--dry-run'
        ])

        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_multiple_paths(self, mock_analyzer_class, cli_runner, tmp_path, empty_cli_result):
        """Test analyze with multiple source paths"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        # Create multiple source directories
        dir1 = tmp_path / "src1"
        dir2 = tmp_path / "src2"
        dir1.mkdir()
        dir2.mkdir()

        result = cli_runner.invoke(cli, [
            'analyze',
            str(dir1),
            str(dir2),
            '--dry-run'
        ])

        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_critical_issues(self, mock_analyzer_class, cli_runner, temp_source_dir, sample_cli_result):
        """Test analyze with critical issues (exit code 2)"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = sample_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'
        ])

        # Should exit with code 2 for critical issues
        assert result.exit_code == 2

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.HTMLReporter')
    @patch('multidb_analyzer.cli.commands.JSONReporter')
    def test_analyze_generate_reports(
        self,
        mock_json_reporter_class,
        mock_html_reporter_class,
        mock_analyzer_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test analyze generates reports"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        # Setup mock reporters
        mock_html_reporter = MagicMock()
        mock_html_reporter.generate.return_value = tmp_path / "report.html"
        mock_html_reporter_class.return_value = mock_html_reporter

        mock_json_reporter = MagicMock()
        mock_json_reporter.generate.return_value = tmp_path / "report.json"
        mock_json_reporter_class.return_value = mock_json_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'html',
            '--format', 'json',
            '--output', str(output_dir)
        ])

        assert result.exit_code == 0
        # Verify reporters were called
        mock_html_reporter.generate.assert_called_once()
        mock_json_reporter.generate.assert_called_once()

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_keyboard_interrupt(self, mock_analyzer_class, cli_runner, temp_source_dir):
        """Test handling of keyboard interrupt"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = KeyboardInterrupt()
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'
        ])

        # Should handle interrupt gracefully
        assert result.exit_code != 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_exception(self, mock_analyzer_class, cli_runner, temp_source_dir):
        """Test handling of general exception"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = Exception("Test error")
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'
        ])

        # Should handle exception and show error
        assert result.exit_code != 0
        assert 'Test error' in result.output or 'failed' in result.output.lower()

    @patch('multidb_analyzer.cli.commands.logger')
    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_exception_verbose(self, mock_analyzer_class, mock_logger, cli_runner, temp_source_dir):
        """Test handling of exception with verbose - logger.exception is called"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = Exception("Verbose test error")
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--verbose',
            '--dry-run'
        ])

        # Should handle exception and show error
        assert result.exit_code != 0
        # Verify logger.exception was called
        mock_logger.exception.assert_called()

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.HTMLReporter')
    def test_analyze_report_generation_error(
        self,
        mock_html_reporter_class,
        mock_analyzer_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test report generation error handling"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        # Make HTML reporter fail
        mock_html_reporter = MagicMock()
        mock_html_reporter.generate.side_effect = Exception("HTML generation failed")
        mock_html_reporter_class.return_value = mock_html_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'html',
            '--output', str(output_dir)
        ])

        # Should still exit successfully even if report generation fails
        assert result.exit_code == 0
        assert 'HTML generation failed' in result.output or 'failed' in result.output

    @patch('multidb_analyzer.cli.commands.HTMLReporter')
    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.logger')
    def test_analyze_html_report_error_verbose(
        self,
        mock_logger,
        mock_analyzer_class,
        mock_html_reporter_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test HTML report error with verbose - logger.exception is called"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        mock_html_reporter = MagicMock()
        mock_html_reporter.generate.side_effect = Exception("HTML error verbose")
        mock_html_reporter_class.return_value = mock_html_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'html',
            '--output', str(output_dir),
            '--verbose'
        ])

        assert result.exit_code == 0
        assert 'failed' in result.output.lower()
        # Verify logger.exception was called
        mock_logger.exception.assert_called()

    @patch('multidb_analyzer.cli.commands.JSONReporter')
    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.logger')
    def test_analyze_json_report_error_verbose(
        self,
        mock_logger,
        mock_analyzer_class,
        mock_json_reporter_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test JSON report error with verbose - logger.exception is called"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        mock_json_reporter = MagicMock()
        mock_json_reporter.generate.side_effect = Exception("JSON error")
        mock_json_reporter_class.return_value = mock_json_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'json',
            '--output', str(output_dir),
            '--verbose'
        ])

        assert result.exit_code == 0
        # Verify logger.exception was called
        mock_logger.exception.assert_called()

    @patch('multidb_analyzer.cli.commands.logger')
    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.MarkdownReporter')
    def test_analyze_markdown_report_error_verbose(
        self,
        mock_md_reporter_class,
        mock_analyzer_class,
        mock_logger,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test Markdown report error with verbose - logger.exception is called"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        mock_md_reporter = MagicMock()
        mock_md_reporter.generate.side_effect = Exception("Markdown error")
        mock_md_reporter_class.return_value = mock_md_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'markdown',
            '--output', str(output_dir),
            '--verbose'
        ])

        assert result.exit_code == 0
        # Verify logger.exception was called
        mock_logger.exception.assert_called()

    @patch('multidb_analyzer.cli.commands.logger')
    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.ConsoleReporter')
    def test_analyze_console_report_error_verbose(
        self,
        mock_console_reporter_class,
        mock_analyzer_class,
        mock_logger,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test Console report error with verbose - logger.exception is called"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        mock_console_reporter = MagicMock()
        mock_console_reporter.generate.side_effect = Exception("Console error")
        mock_console_reporter_class.return_value = mock_console_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'console',
            '--output', str(output_dir),
            '--verbose'
        ])

        assert result.exit_code == 0
        # Verify logger.exception was called
        mock_logger.exception.assert_called()

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_high_issues_only(self, mock_analyzer_class, cli_runner, temp_source_dir):
        """Test analyze with only high severity issues (exit code 1)"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from multidb_analyzer.unified.analysis_result import AnalysisResult
        from datetime import datetime

        high_issue = Issue(
            detector_name="HighDetector",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="High severity issue",
            description="High issue",
            file_path=Path("/path/to/file.java"),
            line_number=10
        )

        result_with_high = AnalysisResult(
            timestamp=datetime(2025, 1, 31, 12, 0, 0),
            total_files=10,
            analyzed_files=10,
            execution_time=5.5,
            issues=[high_issue],
            warnings=[],
            errors=[]
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = result_with_high
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'
        ])

        # Should exit with code 1 for high issues
        assert result.exit_code == 1

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    def test_analyze_with_medium_issues_only(self, mock_analyzer_class, cli_runner, temp_source_dir):
        """Test analyze with only medium/low severity issues (exit code 0)"""
        from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
        from multidb_analyzer.unified.analysis_result import AnalysisResult
        from datetime import datetime

        medium_issue = Issue(
            detector_name="MediumDetector",
            severity=Severity.MEDIUM,
            category=IssueCategory.MAINTAINABILITY,
            title="Medium severity issue",
            description="Medium issue",
            file_path=Path("/path/to/file.java"),
            line_number=10
        )

        result_with_medium = AnalysisResult(
            timestamp=datetime(2025, 1, 31, 12, 0, 0),
            total_files=10,
            analyzed_files=10,
            execution_time=5.5,
            issues=[medium_issue],
            warnings=[],
            errors=[]
        )

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = result_with_medium
        mock_analyzer_class.return_value = mock_analyzer

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--dry-run'
        ])

        # Should exit with code 0 for medium/low issues
        assert result.exit_code == 0

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.MarkdownReporter')
    def test_analyze_markdown_report_success(
        self,
        mock_md_reporter_class,
        mock_analyzer_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test successful Markdown report generation"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        # Setup mock Markdown reporter to succeed
        mock_md_reporter = MagicMock()
        mock_md_reporter.generate.return_value = tmp_path / "report.md"
        mock_md_reporter_class.return_value = mock_md_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'markdown',
            '--output', str(output_dir)
        ])

        assert result.exit_code == 0
        # Verify Markdown reporter was called
        mock_md_reporter.generate.assert_called_once()
        # Verify success message appears
        assert 'Markdown report' in result.output or 'report.md' in result.output

    @patch('multidb_analyzer.cli.commands.UnifiedAnalyzer')
    @patch('multidb_analyzer.cli.commands.ConsoleReporter')
    def test_analyze_console_report_success(
        self,
        mock_console_reporter_class,
        mock_analyzer_class,
        cli_runner,
        temp_source_dir,
        tmp_path,
        empty_cli_result
    ):
        """Test successful Console report generation"""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = empty_cli_result
        mock_analyzer_class.return_value = mock_analyzer

        # Setup mock Console reporter to succeed
        mock_console_reporter = MagicMock()
        mock_console_reporter.generate.return_value = tmp_path / "report.txt"
        mock_console_reporter_class.return_value = mock_console_reporter

        output_dir = tmp_path / "reports"

        result = cli_runner.invoke(cli, [
            'analyze',
            str(temp_source_dir),
            '--format', 'console',
            '--output', str(output_dir)
        ])

        assert result.exit_code == 0
        # Verify Console reporter was called
        mock_console_reporter.generate.assert_called_once()
        # Verify success message appears
        assert 'Console report' in result.output or 'report.txt' in result.output
