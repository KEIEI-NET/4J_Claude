"""
Test fixtures for CLI tests
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest
from click.testing import CliRunner

from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
from multidb_analyzer.unified.analysis_result import AnalysisResult


@pytest.fixture
def cli_runner():
    """Fixture for Click CLI runner"""
    return CliRunner()


@pytest.fixture
def temp_source_dir(tmp_path):
    """Create temporary source directory with sample files"""
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    # Create Java file
    java_file = source_dir / "Example.java"
    java_file.write_text("""
public class Example {
    public void query() {
        client.search(request);
    }
}
    """)

    # Create Python file
    py_file = source_dir / "example.py"
    py_file.write_text("""
def query():
    cursor.execute("SELECT * FROM users")
    """)

    return source_dir


@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary configuration file"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

reports:
  formats:
    - html
    - json
    """)
    return config_file


@pytest.fixture
def sample_cli_issue():
    """Sample issue for CLI testing"""
    return Issue(
        detector_name="TestDetector",
        severity=Severity.HIGH,
        category=IssueCategory.PERFORMANCE,
        title="Performance issue detected",
        description="This is a test issue",
        file_path=Path("/path/to/file.java"),
        line_number=42,
        query_text="SELECT * FROM users",
        suggestion="Add index to improve performance",
        auto_fix_available=True
    )


@pytest.fixture
def sample_cli_result(sample_cli_issue):
    """Sample analysis result for CLI testing"""
    critical_issue = Issue(
        detector_name="CriticalDetector",
        severity=Severity.CRITICAL,
        category=IssueCategory.SECURITY,
        title="Critical security issue",
        description="Security vulnerability found",
        file_path=Path("/path/to/secure.java"),
        line_number=10,
        suggestion="Fix security vulnerability"
    )

    return AnalysisResult(
        timestamp=datetime(2025, 1, 31, 12, 0, 0),
        total_files=10,
        analyzed_files=10,
        execution_time=5.5,
        issues=[critical_issue, sample_cli_issue],
        warnings=["Warning: Some files skipped"],
        errors=[]
    )


@pytest.fixture
def empty_cli_result():
    """Empty analysis result for CLI testing"""
    return AnalysisResult(
        timestamp=datetime(2025, 1, 31, 12, 0, 0),
        total_files=10,
        analyzed_files=10,
        execution_time=2.5,
        issues=[],
        warnings=[],
        errors=[]
    )
