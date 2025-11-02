# MultiDB Analyzer API Reference

**Version:** 1.0.0
**Last Updated:** 2025-11-03

## Table of Contents

- [Overview](#overview)
- [Core Classes](#core-classes)
  - [UnifiedAnalyzer](#unifiedanalyzer)
  - [AnalysisConfig](#analysisconfig)
  - [AnalysisResult](#analysisresult)
  - [Issue](#issue)
- [Detectors](#detectors)
- [Reporters](#reporters)
- [Utilities](#utilities)
- [Examples](#examples)

---

## Overview

The MultiDB Analyzer provides a comprehensive Python API for programmatic analysis of database-related code issues. This document describes the public API for integrating the analyzer into your applications.

### Installation

```python
pip install multidb-analyzer
```

### Quick Start

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from multidb_analyzer.unified.analysis_config import AnalysisConfig

# Configure
config = AnalysisConfig(
    enable_elasticsearch=True,
    enable_mysql=True
)

# Analyze
analyzer = UnifiedAnalyzer(config)
result = analyzer.analyze(["/path/to/code"])

# Results
print(f"Found {result.total_issues} issues")
```

---

## Core Classes

### UnifiedAnalyzer

Main analysis orchestrator that coordinates detection, reporting, and optional LLM integration.

#### Class Definition

```python
class UnifiedAnalyzer:
    """
    Unified analyzer for multi-database static code analysis.

    Coordinates detection across multiple database types and provides
    comprehensive reporting capabilities.
    """
```

#### Constructor

```python
def __init__(
    self,
    config: Optional[AnalysisConfig] = None,
    enable_llm: bool = False,
    api_key: Optional[str] = None
) -> None:
    """
    Initialize UnifiedAnalyzer.

    Args:
        config: Analysis configuration. If None, uses defaults.
        enable_llm: Whether to enable LLM-based semantic analysis.
        api_key: Anthropic API key for LLM integration.

    Raises:
        ValueError: If LLM is enabled but no API key provided.
    """
```

#### Methods

##### `analyze()`

```python
def analyze(
    self,
    source_paths: List[Union[str, Path]],
    recursive: bool = True
) -> AnalysisResult:
    """
    Analyze source code files for database issues.

    Args:
        source_paths: List of file or directory paths to analyze.
        recursive: Whether to recursively scan directories.

    Returns:
        AnalysisResult containing detected issues, statistics, and metadata.

    Raises:
        FileNotFoundError: If a source path doesn't exist.
        PermissionError: If a file cannot be read.

    Example:
        >>> analyzer = UnifiedAnalyzer()
        >>> result = analyzer.analyze(["/path/to/code"])
        >>> print(f"Issues: {result.total_issues}")
    """
```

##### `analyze_file()`

```python
def analyze_file(
    self,
    file_path: Union[str, Path]
) -> List[Issue]:
    """
    Analyze a single file.

    Args:
        file_path: Path to the file to analyze.

    Returns:
        List of issues found in the file.

    Example:
        >>> issues = analyzer.analyze_file("service.java")
        >>> for issue in issues:
        ...     print(issue.title)
    """
```

##### `generate_reports()`

```python
def generate_reports(
    self,
    result: AnalysisResult,
    output_dir: Path,
    formats: List[str] = ["html", "json"]
) -> Dict[str, Path]:
    """
    Generate reports in multiple formats.

    Args:
        result: Analysis result to report.
        output_dir: Directory to save reports.
        formats: List of formats ('html', 'json', 'markdown', 'console').

    Returns:
        Dictionary mapping format to generated file path.

    Example:
        >>> reports = analyzer.generate_reports(
        ...     result,
        ...     Path("./reports"),
        ...     ["html", "json"]
        ... )
        >>> print(reports["html"])
    """
```

---

### AnalysisConfig

Configuration for analysis behavior.

#### Class Definition

```python
@dataclass
class AnalysisConfig:
    """
    Configuration for unified analysis.

    Controls which detectors are enabled, file patterns,
    and analysis behavior.
    """
```

#### Fields

```python
# Database configuration
enable_elasticsearch: bool = True
enable_mysql: bool = True

# Parser configuration
java_include_patterns: List[str] = field(default_factory=lambda: ["**/*.java"])
java_exclude_patterns: List[str] = field(default_factory=lambda: ["**/test/**"])
python_include_patterns: List[str] = field(default_factory=lambda: ["**/*.py"])
python_exclude_patterns: List[str] = field(default_factory=lambda: ["**/test/**"])

# Analysis behavior
max_file_size: int = 1_000_000  # bytes
timeout_per_file: int = 30  # seconds
parallel_analysis: bool = False  # Future feature
max_workers: int = 4

# LLM configuration
llm_model: str = "claude-sonnet-3-5-20241022"
llm_temperature: float = 0.0
llm_max_tokens: int = 4096
llm_max_retries: int = 3
llm_timeout: int = 30
```

#### Example

```python
from multidb_analyzer.unified.analysis_config import AnalysisConfig

config = AnalysisConfig(
    enable_elasticsearch=True,
    enable_mysql=False,
    java_exclude_patterns=["**/test/**", "**/generated/**"],
    max_file_size=500_000
)
```

---

### AnalysisResult

Contains analysis results and statistics.

#### Class Definition

```python
@dataclass
class AnalysisResult:
    """
    Result of code analysis containing issues and metadata.
    """
```

#### Fields

```python
# Metadata
timestamp: datetime
version: str = "1.0.0"

# Statistics
total_files: int
analyzed_files: int
skipped_files: int = 0
execution_time: float  # seconds

# Issues
issues: List[Issue]
warnings: List[str] = field(default_factory=list)
errors: List[str] = field(default_factory=list)

# Statistics (calculated automatically)
total_issues: int = 0
issues_by_severity: Dict[str, int] = field(default_factory=dict)
issues_by_category: Dict[str, int] = field(default_factory=dict)
issues_by_database: Dict[str, int] = field(default_factory=dict)
```

#### Methods

```python
def to_dict(self) -> dict:
    """Convert to dictionary for JSON serialization."""

def to_json(self, indent: int = 2) -> str:
    """Convert to JSON string."""

def filter_by_severity(self, *severities: Severity) -> List[Issue]:
    """Filter issues by severity level."""

def filter_by_category(self, *categories: IssueCategory) -> List[Issue]:
    """Filter issues by category."""

def filter_by_database(self, database: str) -> List[Issue]:
    """Filter issues by database type."""
```

#### Example

```python
result = analyzer.analyze(["/path/to/code"])

# Access statistics
print(f"Analyzed {result.analyzed_files} files")
print(f"Found {result.total_issues} issues")
print(f"Execution time: {result.execution_time:.2f}s")

# Filter issues
critical = result.filter_by_severity(Severity.CRITICAL)
performance = result.filter_by_category(IssueCategory.PERFORMANCE)
es_issues = result.filter_by_database("elasticsearch")
```

---

### Issue

Represents a detected code issue.

#### Class Definition

```python
@dataclass
class Issue:
    """
    Represents a detected code issue with metadata.
    """
```

#### Fields

```python
# Identification
detector_name: str
severity: Severity
category: IssueCategory

# Description
title: str
description: str
suggestion: Optional[str] = None

# Location
file_path: Optional[Path] = None
line_number: Optional[int] = None
column_number: Optional[int] = None
code_snippet: Optional[str] = None

# Context
query_text: Optional[str] = None
method_name: Optional[str] = None
class_name: Optional[str] = None

# Fix information
auto_fix_available: bool = False
fix_code: Optional[str] = None
fix_confidence: float = 0.0

# Metadata
detected_at: datetime = field(default_factory=datetime.now)
llm_analyzed: bool = False
```

#### Enums

```python
class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IssueCategory(Enum):
    """Issue categories."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
```

#### Example

```python
from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory

issue = Issue(
    detector_name="ElasticsearchWildcardDetector",
    severity=Severity.HIGH,
    category=IssueCategory.PERFORMANCE,
    title="Wildcard query on analyzed field",
    description="Using wildcard query on analyzed field causes performance issues",
    file_path=Path("/src/service.java"),
    line_number=42,
    suggestion="Use match query or keyword field"
)
```

---

## Detectors

### Base Detector

All detectors inherit from `BaseDetector`.

```python
from multidb_analyzer.core.base_detector import BaseDetector

class MyDetector(BaseDetector):
    def detect(self, code: str, file_path: Path) -> List[Issue]:
        """
        Detect issues in code.

        Args:
            code: Source code content.
            file_path: Path to the file being analyzed.

        Returns:
            List of detected issues.
        """
        issues = []
        # Your detection logic
        return issues
```

### Elasticsearch Detectors

```python
from multidb_analyzer.elasticsearch.detectors import (
    ElasticsearchWildcardDetector,
    DeepPaginationDetector,
    LargeResultSetDetector,
    MissingTimeoutDetector
)

# Use individually
detector = ElasticsearchWildcardDetector()
issues = detector.detect(code, file_path)
```

### MySQL Detectors

```python
from multidb_analyzer.mysql.detectors import (
    MySQLNPlusOneDetector,
    MissingIndexDetector,
    SelectNPlusOneDetector
)

detector = MySQLNPlusOneDetector()
issues = detector.detect(code, file_path)
```

---

## Reporters

### HTML Reporter

```python
from multidb_analyzer.unified.reporters import HTMLReporter

reporter = HTMLReporter(
    include_toc=True,
    include_statistics=True,
    theme="dark"  # or "light"
)

output_path = reporter.generate(result, Path("report.html"))
```

### JSON Reporter

```python
from multidb_analyzer.unified.reporters import JSONReporter

reporter = JSONReporter(
    pretty_print=True,
    include_metadata=True
)

output_path = reporter.generate(result, Path("report.json"))
```

### Markdown Reporter

```python
from multidb_analyzer.unified.reporters import MarkdownReporter

reporter = MarkdownReporter(
    include_toc=True,
    include_summary=True
)

output_path = reporter.generate(result, Path("report.md"))
```

### Console Reporter

```python
from multidb_analyzer.unified.reporters import ConsoleReporter

reporter = ConsoleReporter(
    color=True,
    verbose=True
)

output_path = reporter.generate(result, Path("report.txt"))
```

---

## Utilities

### File Utilities

```python
from multidb_analyzer.utils.file_utils import (
    find_files,
    read_file,
    is_java_file,
    is_python_file
)

# Find files matching pattern
java_files = find_files("/path/to/code", "**/*.java")

# Read file content
content = read_file(Path("/path/to/file.java"))

# Check file type
if is_java_file(file_path):
    # Process Java file
    pass
```

### Code Parsers

```python
from multidb_analyzer.parsers import JavaParser, PythonParser

# Java parser
java_parser = JavaParser()
ast = java_parser.parse(java_code)
methods = java_parser.extract_methods(ast)

# Python parser
python_parser = PythonParser()
ast = python_parser.parse(python_code)
functions = python_parser.extract_functions(ast)
```

---

## Examples

### Example 1: Basic Analysis

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer

# Create analyzer with defaults
analyzer = UnifiedAnalyzer()

# Analyze directory
result = analyzer.analyze(["/path/to/code"])

# Print summary
print(f"Total files: {result.total_files}")
print(f"Total issues: {result.total_issues}")
print(f"Execution time: {result.execution_time:.2f}s")

# Print issues by severity
for severity, count in result.issues_by_severity.items():
    print(f"{severity}: {count}")
```

### Example 2: Custom Configuration

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from multidb_analyzer.unified.analysis_config import AnalysisConfig

# Custom configuration
config = AnalysisConfig(
    enable_elasticsearch=True,
    enable_mysql=False,
    java_exclude_patterns=[
        "**/test/**",
        "**/generated/**",
        "**/build/**"
    ],
    max_file_size=500_000
)

# Create analyzer
analyzer = UnifiedAnalyzer(config)

# Analyze
result = analyzer.analyze(["/path/to/code"])
```

### Example 3: LLM Integration

```python
import os
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")

# Create analyzer with LLM
analyzer = UnifiedAnalyzer(
    enable_llm=True,
    api_key=api_key
)

# Analyze
result = analyzer.analyze(["/path/to/code"])

# Check which issues were LLM-analyzed
llm_issues = [i for i in result.issues if i.llm_analyzed]
print(f"LLM analyzed {len(llm_issues)} issues")
```

### Example 4: Filtering Issues

```python
from multidb_analyzer.core.base_detector import Severity, IssueCategory

result = analyzer.analyze(["/path/to/code"])

# Get critical and high severity issues
critical_high = result.filter_by_severity(Severity.CRITICAL, Severity.HIGH)
print(f"Critical/High: {len(critical_high)}")

# Get performance issues
performance = result.filter_by_category(IssueCategory.PERFORMANCE)
print(f"Performance issues: {len(performance)}")

# Get Elasticsearch issues
es_issues = result.filter_by_database("elasticsearch")
print(f"Elasticsearch issues: {len(es_issues)}")

# Combine filters
critical_performance = [
    issue for issue in result.issues
    if issue.severity == Severity.CRITICAL
    and issue.category == IssueCategory.PERFORMANCE
]
```

### Example 5: Generate Multiple Reports

```python
from pathlib import Path

result = analyzer.analyze(["/path/to/code"])

# Generate all report formats
reports = analyzer.generate_reports(
    result,
    output_dir=Path("./reports"),
    formats=["html", "json", "markdown", "console"]
)

# Print generated report paths
for format_name, file_path in reports.items():
    print(f"{format_name}: {file_path}")
```

### Example 6: Custom Detector

```python
from multidb_analyzer.core.base_detector import BaseDetector, Issue, Severity, IssueCategory
from pathlib import Path
from typing import List

class CustomElasticsearchDetector(BaseDetector):
    """Custom detector for Elasticsearch issues."""

    def detect(self, code: str, file_path: Path) -> List[Issue]:
        issues = []

        # Custom detection logic
        if "SearchRequest" in code and "setSize(10000)" in code:
            issues.append(Issue(
                detector_name="CustomElasticsearchDetector",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                title="Large result set requested",
                description="Requesting 10,000 results can cause memory issues",
                file_path=file_path,
                suggestion="Use scroll API for large result sets"
            ))

        return issues

# Use custom detector
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer

analyzer = UnifiedAnalyzer()
analyzer.register_detector(CustomElasticsearchDetector())
result = analyzer.analyze(["/path/to/code"])
```

### Example 7: Programmatic Report Generation

```python
from multidb_analyzer.unified.reporters import HTMLReporter, JSONReporter
from pathlib import Path

result = analyzer.analyze(["/path/to/code"])

# HTML report with custom settings
html_reporter = HTMLReporter(
    include_toc=True,
    include_statistics=True,
    theme="dark"
)
html_path = html_reporter.generate(result, Path("custom_report.html"))

# JSON report for CI/CD
json_reporter = JSONReporter(pretty_print=True)
json_path = json_reporter.generate(result, Path("ci_report.json"))

# Parse JSON for further processing
import json
with open(json_path) as f:
    data = json.load(f)
    critical_count = data["statistics"]["by_severity"]["critical"]
    if critical_count > 0:
        raise SystemExit(f"Found {critical_count} critical issues!")
```

### Example 8: Progress Callback

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from typing import Optional

def progress_callback(current: int, total: int, file_path: Optional[str] = None):
    """Called for each file analyzed."""
    percent = (current / total) * 100
    print(f"Progress: {percent:.1f}% ({current}/{total}) - {file_path}")

analyzer = UnifiedAnalyzer()
result = analyzer.analyze(
    ["/path/to/code"],
    progress_callback=progress_callback
)
```

### Example 9: Error Handling

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from multidb_analyzer.core.exceptions import (
    AnalysisError,
    ParsingError,
    DetectionError
)

analyzer = UnifiedAnalyzer()

try:
    result = analyzer.analyze(["/path/to/code"])
except FileNotFoundError as e:
    print(f"Path not found: {e}")
except PermissionError as e:
    print(f"Permission denied: {e}")
except ParsingError as e:
    print(f"Failed to parse file: {e}")
    # Continue with partial results
    result = analyzer.get_partial_results()
except AnalysisError as e:
    print(f"Analysis failed: {e}")
finally:
    # Always generate reports if we have results
    if 'result' in locals():
        analyzer.generate_reports(result, Path("./reports"))
```

### Example 10: Batch Processing

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

analyzer = UnifiedAnalyzer()

# Batch process multiple projects
projects = [
    "/path/to/project1",
    "/path/to/project2",
    "/path/to/project3"
]

results = {}
for project in projects:
    project_name = Path(project).name
    logging.info(f"Analyzing {project_name}...")

    result = analyzer.analyze([project])
    results[project_name] = result

    # Generate individual reports
    analyzer.generate_reports(
        result,
        Path(f"./reports/{project_name}"),
        formats=["html", "json"]
    )

    logging.info(
        f"{project_name}: "
        f"{result.total_issues} issues, "
        f"{result.execution_time:.2f}s"
    )

# Summary report
total_issues = sum(r.total_issues for r in results.values())
print(f"\nTotal issues across {len(projects)} projects: {total_issues}")
```

---

## Type Hints

The API uses comprehensive type hints for better IDE support:

```python
from typing import List, Optional, Union, Dict
from pathlib import Path

def analyze(
    source_paths: List[Union[str, Path]],
    config: Optional[AnalysisConfig] = None
) -> AnalysisResult:
    ...
```

Use a type checker like `mypy` for validation:

```bash
mypy your_script.py
```

---

## Thread Safety

The analyzer is **not thread-safe** by default. For concurrent analysis:

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from concurrent.futures import ThreadPoolExecutor

# Create separate analyzer instances
def analyze_project(project_path):
    analyzer = UnifiedAnalyzer()  # New instance per thread
    return analyzer.analyze([project_path])

with ThreadPoolExecutor(max_workers=4) as executor:
    projects = ["/path1", "/path2", "/path3"]
    results = list(executor.map(analyze_project, projects))
```

---

## Performance Tips

1. **Exclude unnecessary files**: Configure `exclude_patterns` to skip test files, generated code, etc.
2. **Limit file size**: Set `max_file_size` to skip very large files
3. **Disable LLM for large codebases**: LLM analysis is slower but more accurate
4. **Use specific database types**: Enable only the databases you use
5. **Batch file analysis**: Analyze files in batches for better performance

---

## API Versioning

The API follows [Semantic Versioning](https://semver.org/):
- **Major version** (1.x.x): Breaking changes
- **Minor version** (x.1.x): New features, backward compatible
- **Patch version** (x.x.1): Bug fixes

Check version:
```python
import multidb_analyzer
print(multidb_analyzer.__version__)  # "1.0.0"
```

---

**For more information:**
- [CLI Usage Guide](./CLI_USAGE.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)
- [Examples](./EXAMPLES.md)
- [GitHub Repository](https://github.com/your-org/multidb-analyzer)
