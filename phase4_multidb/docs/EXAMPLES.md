# MultiDB Analyzer - Code Examples

**Version:** 1.0.0
**Last Updated:** 2025-11-03

## Table of Contents

- [Basic Usage](#basic-usage)
- [Configuration Examples](#configuration-examples)
- [Programmatic API](#programmatic-api)
- [Custom Detectors](#custom-detectors)
- [Reporting](#reporting)
- [CI/CD Scripts](#cicd-scripts)
- [Advanced Use Cases](#advanced-use-cases)

---

## Basic Usage

### Example 1: Simple Analysis

```bash
# Analyze current directory
multidb-analyzer analyze .

# Analyze specific directory
multidb-analyzer analyze ./src

# Analyze multiple directories
multidb-analyzer analyze ./backend ./frontend ./shared
```

### Example 2: Database-Specific Analysis

```bash
# Elasticsearch only
multidb-analyzer analyze ./src --db elasticsearch

# MySQL only
multidb-analyzer analyze ./src --db mysql

# Both databases
multidb-analyzer analyze ./src --db all
```

### Example 3: Output Formats

```bash
# HTML report
multidb-analyzer analyze ./src --format html

# Multiple formats
multidb-analyzer analyze ./src --format html,json,markdown

# Custom output directory
multidb-analyzer analyze ./src \
  --format html,json \
  --output ./analysis-reports
```

### Example 4: LLM Integration

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Enable LLM analysis
multidb-analyzer analyze ./src --llm

# Or pass API key directly
multidb-analyzer analyze ./src \
  --llm \
  --api-key "sk-ant-..."
```

---

## Configuration Examples

### Example 5: Basic Configuration File

**config.yaml:**
```yaml
# Simple configuration
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

reports:
  formats:
    - html
    - json
  output_dir: "./reports"
```

Usage:
```bash
multidb-analyzer analyze ./src --config config.yaml
```

### Example 6: Advanced Configuration

**advanced-config.yaml:**
```yaml
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

  parsers:
    java:
      include_patterns:
        - "**/*.java"
      exclude_patterns:
        - "**/test/**"
        - "**/generated/**"
        - "**/build/**"
      max_file_size: 500000  # 500KB

    python:
      include_patterns:
        - "**/*.py"
      exclude_patterns:
        - "**/test_*.py"
        - "**/__pycache__/**"
        - "**/venv/**"

reports:
  formats:
    - html
    - json
    - markdown

  output_dir: "./analysis-results"

  html:
    include_toc: true
    include_statistics: true
    theme: "dark"

  json:
    pretty_print: true
    include_metadata: true

llm:
  enabled: true
  model: "claude-sonnet-3-5-20241022"
  temperature: 0.0
  max_retries: 3
  timeout: 30

logging:
  level: "INFO"
  format: "detailed"
```

### Example 7: Team Configuration

**.multidb-analyzer.yml:**
```yaml
# Team-wide configuration
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

  parsers:
    java:
      exclude_patterns:
        - "**/test/**"
        - "**/target/**"

    python:
      exclude_patterns:
        - "**/tests/**"
        - "**/.venv/**"

reports:
  formats:
    - html
    - json

  output_dir: "./reports"

# Quality gates
quality_gates:
  max_critical: 0
  max_high: 5
  max_total: 50
```

---

## Programmatic API

### Example 8: Basic Python API

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from multidb_analyzer.unified.analysis_config import AnalysisConfig

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

### Example 9: Custom Configuration

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
    ],
    max_file_size=500_000
)

# Create analyzer
analyzer = UnifiedAnalyzer(config)

# Analyze
result = analyzer.analyze(["/path/to/code"])

# Filter results
critical_issues = result.filter_by_severity(Severity.CRITICAL)
print(f"Critical issues: {len(critical_issues)}")
```

### Example 10: LLM Analysis

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

# Check LLM-analyzed issues
llm_issues = [i for i in result.issues if i.llm_analyzed]
print(f"LLM analyzed {len(llm_issues)} issues")

# Check auto-fix suggestions
fixable = [i for i in result.issues if i.auto_fix_available]
print(f"{len(fixable)} issues have auto-fix suggestions")
```

### Example 11: Multiple Project Analysis

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

analyzer = UnifiedAnalyzer()

# Multiple projects
projects = {
    "Backend API": "/path/to/backend",
    "Search Service": "/path/to/search",
    "Data Pipeline": "/path/to/pipeline"
}

# Analyze each project
results = {}
for name, path in projects.items():
    logging.info(f"Analyzing {name}...")
    result = analyzer.analyze([path])
    results[name] = result

    # Generate reports
    analyzer.generate_reports(
        result,
        Path(f"./reports/{name.replace(' ', '_').lower()}"),
        formats=["html", "json"]
    )

# Summary
print("\n=== Summary ===")
for name, result in results.items():
    print(f"{name}: {result.total_issues} issues ({result.execution_time:.2f}s)")
```

### Example 12: Progress Callback

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from typing import Optional

def progress_callback(current: int, total: int, file_path: Optional[str] = None):
    """Progress callback for analysis."""
    percent = (current / total) * 100
    print(f"\rProgress: {percent:.1f}% ({current}/{total})", end="")
    if file_path:
        print(f" - {Path(file_path).name}", end="")

analyzer = UnifiedAnalyzer()
result = analyzer.analyze(
    ["/path/to/code"],
    progress_callback=progress_callback
)
print()  # New line after progress
```

---

## Custom Detectors

### Example 13: Simple Custom Detector

```python
from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from pathlib import Path
from typing import List

class CustomElasticsearchDetector(BaseDetector):
    """Detect custom Elasticsearch patterns."""

    def detect(self, code: str, file_path: Path) -> List[Issue]:
        issues = []

        # Example: Detect large size parameter
        if "setSize(10000)" in code:
            issues.append(Issue(
                detector_name="CustomElasticsearchDetector",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                title="Large result set size",
                description="Requesting 10,000 results can cause memory issues",
                file_path=file_path,
                suggestion="Use scroll API for large result sets"
            ))

        # Example: Missing query timeout
        if "SearchRequest" in code and "setTimeout" not in code:
            issues.append(Issue(
                detector_name="CustomElasticsearchDetector",
                severity=Severity.MEDIUM,
                category=IssueCategory.RELIABILITY,
                title="Missing query timeout",
                description="Query without timeout can hang indefinitely",
                file_path=file_path,
                suggestion="Add setTimeout() to SearchRequest"
            ))

        return issues

# Usage
detector = CustomElasticsearchDetector()
issues = detector.detect(code, file_path)
```

### Example 14: Advanced Custom Detector with AST

```python
import javalang
from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from pathlib import Path
from typing import List, Optional

class AdvancedElasticsearchDetector(BaseDetector):
    """Advanced Elasticsearch detector using AST."""

    def detect(self, code: str, file_path: Path) -> List[Issue]:
        issues = []

        try:
            tree = javalang.parse.parse(code)

            # Find method invocations
            for path, node in tree:
                if isinstance(node, javalang.tree.MethodInvocation):
                    if node.member == "search":
                        # Check arguments
                        issue = self._check_search_call(node, file_path)
                        if issue:
                            issues.append(issue)

        except javalang.parser.JavaSyntaxError:
            pass  # Skip files with syntax errors

        return issues

    def _check_search_call(
        self,
        node: javalang.tree.MethodInvocation,
        file_path: Path
    ) -> Optional[Issue]:
        """Check search method call for issues."""

        # Example: Check for wildcard queries
        if self._has_wildcard_query(node):
            return Issue(
                detector_name="AdvancedElasticsearchDetector",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                title="Wildcard query detected",
                description="Wildcard queries can be very slow",
                file_path=file_path,
                suggestion="Use match query or keyword field"
            )

        return None

    def _has_wildcard_query(self, node) -> bool:
        """Check if method call uses wildcard query."""
        # Implementation details...
        return False
```

### Example 15: Register Custom Detector

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer

# Create analyzer
analyzer = UnifiedAnalyzer()

# Register custom detector
analyzer.register_detector(CustomElasticsearchDetector())

# Analyze with custom detector
result = analyzer.analyze(["/path/to/code"])
```

---

## Reporting

### Example 16: Generate Custom HTML Report

```python
from multidb_analyzer.unified.reporters import HTMLReporter
from pathlib import Path

# Analyze
analyzer = UnifiedAnalyzer()
result = analyzer.analyze(["/path/to/code"])

# Create custom HTML report
reporter = HTMLReporter(
    include_toc=True,
    include_statistics=True,
    theme="dark"
)

output_path = reporter.generate(
    result,
    Path("./reports/custom_report.html")
)

print(f"Report generated: {output_path}")
```

### Example 17: Generate Multiple Report Formats

```python
from multidb_analyzer.unified.reporters import (
    HTMLReporter,
    JSONReporter,
    MarkdownReporter,
    ConsoleReporter
)
from pathlib import Path

result = analyzer.analyze(["/path/to/code"])

reports_dir = Path("./reports")
reports_dir.mkdir(exist_ok=True)

# HTML report
html_reporter = HTMLReporter()
html_path = html_reporter.generate(result, reports_dir / "report.html")

# JSON report
json_reporter = JSONReporter(pretty_print=True)
json_path = json_reporter.generate(result, reports_dir / "report.json")

# Markdown report
md_reporter = MarkdownReporter(include_toc=True)
md_path = md_reporter.generate(result, reports_dir / "report.md")

# Console report (to file)
console_reporter = ConsoleReporter()
txt_path = console_reporter.generate(result, reports_dir / "report.txt")

print(f"Generated {len([html_path, json_path, md_path, txt_path])} reports")
```

### Example 18: Custom JSON Processing

```python
import json
from pathlib import Path

# Generate JSON report
result = analyzer.analyze(["/path/to/code"])
json_reporter = JSONReporter()
json_path = json_reporter.generate(result, Path("report.json"))

# Load and process JSON
with open(json_path) as f:
    report = json.load(f)

# Filter critical issues
critical_issues = [
    issue for issue in report['issues']
    if issue['severity'] == 'critical'
]

# Create summary
summary = {
    'total_issues': len(report['issues']),
    'critical': len(critical_issues),
    'files_affected': len(set(i['file_path'] for i in report['issues'])),
    'most_common_detector': max(
        (i['detector_name'] for i in report['issues']),
        key=lambda d: sum(1 for i in report['issues'] if i['detector_name'] == d)
    )
}

print(json.dumps(summary, indent=2))
```

---

## CI/CD Scripts

### Example 19: GitHub Actions Script

**.github/workflows/multidb-analysis.yml:**
```yaml
name: MultiDB Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install MultiDB Analyzer
      run: pip install multidb-analyzer

    - name: Run Analysis
      id: analysis
      run: |
        multidb-analyzer analyze ./src \
          --format json,html \
          --output ./reports

        # Capture exit code
        echo "exit_code=$?" >> $GITHUB_OUTPUT

    - name: Check Quality Gate
      run: |
        python scripts/quality_gate.py reports/analysis_report.json

    - name: Upload Reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: analysis-reports
        path: reports/
```

**scripts/quality_gate.py:**
```python
import json
import sys
from pathlib import Path

def check_quality_gate(report_path: Path) -> int:
    """Check if analysis passes quality gates."""
    with open(report_path) as f:
        report = json.load(f)

    stats = report['statistics']['by_severity']

    # Define thresholds
    if stats.get('critical', 0) > 0:
        print(f"❌ FAILED: {stats['critical']} critical issues")
        return 1

    if stats.get('high', 0) > 10:
        print(f"❌ FAILED: {stats['high']} high issues (max 10)")
        return 1

    if report['summary']['total_issues'] > 100:
        print(f"❌ FAILED: {report['summary']['total_issues']} total issues (max 100)")
        return 1

    print("✅ PASSED: All quality gates passed")
    return 0

if __name__ == "__main__":
    sys.exit(check_quality_gate(Path(sys.argv[1])))
```

### Example 20: GitLab CI Script

**.gitlab-ci.yml:**
```yaml
stages:
  - analyze
  - report
  - notify

variables:
  REPORTS_DIR: "reports"

analyze:
  stage: analyze
  image: python:3.11
  script:
    - pip install multidb-analyzer
    - |
      multidb-analyzer analyze ./src \
        --format json,html \
        --output ${REPORTS_DIR}
  artifacts:
    paths:
      - ${REPORTS_DIR}/
    expire_in: 1 week
  only:
    - merge_requests
    - main

quality_gate:
  stage: report
  image: python:3.11
  script:
    - python scripts/quality_gate.py ${REPORTS_DIR}/analysis_report.json
  needs:
    - analyze
  allow_failure: false

notify_slack:
  stage: notify
  image: python:3.11
  script:
    - pip install requests
    - python scripts/notify_slack.py ${REPORTS_DIR}/analysis_report.json
  needs:
    - analyze
  when: on_failure
```

---

## Advanced Use Cases

### Example 21: Incremental Analysis

```bash
#!/bin/bash
# analyze_changes.sh - Analyze only changed files

# Get changed files in current PR/branch
CHANGED_FILES=$(git diff --name-only origin/main...HEAD | grep -E '\.(java|py)$')

if [ -z "$CHANGED_FILES" ]; then
    echo "No relevant files changed"
    exit 0
fi

echo "Analyzing changed files:"
echo "$CHANGED_FILES"

# Analyze only changed files
multidb-analyzer analyze $CHANGED_FILES \
    --format json,console \
    --output ./reports/incremental
```

### Example 22: Baseline Comparison

```python
import json
from pathlib import Path

def compare_with_baseline(current_report: Path, baseline_report: Path):
    """Compare current analysis with baseline."""

    with open(current_report) as f:
        current = json.load(f)

    with open(baseline_report) as f:
        baseline = json.load(f)

    # Compare statistics
    current_total = current['summary']['total_issues']
    baseline_total = baseline['summary']['total_issues']

    diff = current_total - baseline_total
    percent = (diff / baseline_total * 100) if baseline_total > 0 else 0

    print(f"Current issues: {current_total}")
    print(f"Baseline issues: {baseline_total}")
    print(f"Difference: {diff:+d} ({percent:+.1f}%)")

    # Fail if issues increased significantly
    if diff > 10 or percent > 20:
        print("❌ Too many new issues introduced!")
        return 1

    print("✅ No significant increase in issues")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(compare_with_baseline(
        Path(sys.argv[1]),
        Path(sys.argv[2])
    ))
```

### Example 23: Multi-Repository Analysis

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# Multiple repositories
repositories = [
    {
        "name": "Backend API",
        "path": "/repos/backend-api",
        "databases": ["elasticsearch", "mysql"]
    },
    {
        "name": "Search Service",
        "path": "/repos/search-service",
        "databases": ["elasticsearch"]
    },
    {
        "name": "User Service",
        "path": "/repos/user-service",
        "databases": ["mysql"]
    }
]

# Analyze all repositories
all_results = []

for repo in repositories:
    logging.info(f"Analyzing {repo['name']}...")

    config = AnalysisConfig(
        enable_elasticsearch="elasticsearch" in repo["databases"],
        enable_mysql="mysql" in repo["databases"]
    )

    analyzer = UnifiedAnalyzer(config)
    result = analyzer.analyze([repo["path"]])

    all_results.append({
        "name": repo["name"],
        "result": result
    })

    # Generate reports
    reports_dir = Path(f"./reports/{repo['name'].replace(' ', '-').lower()}")
    analyzer.generate_reports(result, reports_dir, ["html", "json"])

# Summary report
print("\n=== Multi-Repository Analysis Summary ===")
total_issues = 0
for item in all_results:
    issues = item["result"].total_issues
    total_issues += issues
    print(f"{item['name']}: {issues} issues")

print(f"\nTotal across all repositories: {total_issues} issues")
```

### Example 24: Scheduled Analysis

```python
#!/usr/bin/env python3
"""
scheduled_analysis.py - Run analysis on schedule
Usage: Add to crontab:
  0 2 * * * /path/to/scheduled_analysis.py
"""

import sys
from pathlib import Path
from datetime import datetime
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer

def run_scheduled_analysis():
    """Run daily analysis and save results."""

    # Timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Analyze
    analyzer = UnifiedAnalyzer()
    result = analyzer.analyze(["/path/to/code"])

    # Generate reports with timestamp
    reports_dir = Path(f"./reports/scheduled/{timestamp}")
    reports_dir.mkdir(parents=True, exist_ok=True)

    analyzer.generate_reports(result, reports_dir, ["html", "json"])

    # Log results
    log_file = Path("./reports/scheduled/analysis.log")
    with open(log_file, "a") as f:
        f.write(
            f"{timestamp}: {result.total_issues} issues, "
            f"{result.execution_time:.2f}s\n"
        )

    print(f"Analysis complete: {result.total_issues} issues")

    # Return exit code based on results
    if result.issues_by_severity.get('critical', 0) > 0:
        return 2
    elif result.issues_by_severity.get('high', 0) > 10:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(run_scheduled_analysis())
```

---

**For more information:**
- [CLI Usage Guide](./CLI_USAGE.md)
- [API Reference](./API_REFERENCE.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)
