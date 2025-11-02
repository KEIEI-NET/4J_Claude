# MultiDB Analyzer CLI Usage Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-03

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Output Formats](#output-formats)
- [Database Support](#database-support)
- [LLM Integration](#llm-integration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/multidb-analyzer.git
cd multidb-analyzer/phase4_multidb

# Install dependencies
pip install -e .

# Verify installation
multidb-analyzer --version
```

### Using pip (Future)

```bash
pip install multidb-analyzer
```

---

## Quick Start

### Basic Analysis

Analyze a directory for database performance issues:

```bash
multidb-analyzer analyze ./src
```

### With Specific Database

Analyze only Elasticsearch issues:

```bash
multidb-analyzer analyze ./src --db elasticsearch
```

### Generate HTML Report

```bash
multidb-analyzer analyze ./src --format html --output ./reports
```

### Enable LLM Optimization

```bash
export ANTHROPIC_API_KEY="your-api-key"
multidb-analyzer analyze ./src --llm
```

---

## Command Reference

### `analyze` Command

Analyze source code for database performance issues and anti-patterns.

#### Syntax

```bash
multidb-analyzer analyze [SOURCE_PATHS...] [OPTIONS]
```

#### Arguments

- `SOURCE_PATHS`: One or more paths to analyze (files or directories)

#### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--db` | choice | Database type to analyze (`elasticsearch`, `mysql`, `all`) | `all` |
| `--llm` | flag | Enable LLM-based semantic analysis | `False` |
| `--api-key` | string | Anthropic API key (or use `ANTHROPIC_API_KEY` env var) | `None` |
| `--format` | choice | Output format (`html`, `json`, `markdown`, `console`) | `html,console` |
| `--output`, `-o` | path | Output directory for reports | `./reports` |
| `--config`, `-c` | path | Configuration file path (YAML) | `None` |
| `--verbose`, `-v` | flag | Enable verbose logging | `False` |
| `--dry-run` | flag | Show what would be analyzed without running | `False` |

#### Exit Codes

- **0**: Success (no issues or only low/medium severity)
- **1**: High severity issues found
- **2**: Critical severity issues found

---

## Configuration

### Configuration File

Create a YAML configuration file to customize analysis:

```yaml
# config.yaml

# Database configuration
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

  # Parser settings
  parsers:
    java:
      include_patterns:
        - "**/*.java"
      exclude_patterns:
        - "**/test/**"
        - "**/generated/**"
    python:
      include_patterns:
        - "**/*.py"

# Report configuration
reports:
  formats:
    - html
    - json
  output_dir: "./reports"

  # HTML report settings
  html:
    include_toc: true
    include_statistics: true
    theme: "dark"  # or "light"

  # JSON report settings
  json:
    pretty_print: true
    include_metadata: true

# LLM configuration (optional)
llm:
  enabled: false
  model: "claude-sonnet-3-5-20241022"
  max_retries: 3
  timeout: 30

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "detailed"  # simple, detailed
```

### Usage with Configuration File

```bash
multidb-analyzer analyze ./src --config config.yaml
```

### Environment Variables

- `ANTHROPIC_API_KEY`: API key for LLM integration
- `MULTIDB_LOG_LEVEL`: Override logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

---

## Output Formats

### HTML Report

Rich, interactive HTML report with:
- Executive summary
- Issue statistics by severity
- Detailed issue listings with code context
- Database-specific sections
- Search and filter capabilities

```bash
multidb-analyzer analyze ./src --format html
```

Output: `./reports/analysis_report.html`

### JSON Report

Machine-readable JSON format for:
- CI/CD integration
- Custom tooling
- Data analysis

```bash
multidb-analyzer analyze ./src --format json
```

Output: `./reports/analysis_report.json`

**JSON Structure:**
```json
{
  "metadata": {
    "timestamp": "2025-11-03T10:30:00Z",
    "version": "1.0.0",
    "analyzer": "multidb-analyzer"
  },
  "summary": {
    "total_files": 150,
    "analyzed_files": 145,
    "total_issues": 42,
    "execution_time": 12.5
  },
  "statistics": {
    "by_severity": {
      "critical": 2,
      "high": 8,
      "medium": 15,
      "low": 17
    },
    "by_category": {
      "performance": 25,
      "security": 5,
      "reliability": 12
    },
    "by_database": {
      "elasticsearch": 20,
      "mysql": 22
    }
  },
  "issues": [
    {
      "id": "ES-001",
      "detector": "ElasticsearchWildcardDetector",
      "severity": "high",
      "category": "performance",
      "title": "Wildcard query on analyzed field",
      "description": "...",
      "file_path": "/path/to/file.java",
      "line_number": 42,
      "code_snippet": "...",
      "suggestion": "...",
      "auto_fix_available": true
    }
  ],
  "warnings": [],
  "errors": []
}
```

### Markdown Report

Readable Markdown format for:
- Documentation
- Code reviews
- GitHub/GitLab integration

```bash
multidb-analyzer analyze ./src --format markdown
```

Output: `./reports/analysis_report.md`

### Console Report

Real-time console output with:
- Color-coded severity levels
- Progress indicators
- Summary tables

```bash
multidb-analyzer analyze ./src --format console
```

Or save to file:
```bash
multidb-analyzer analyze ./src --format console --output ./reports
```

Output: `./reports/analysis_report.txt`

---

## Database Support

### Elasticsearch

Detects issues related to:
- Wildcard queries on analyzed fields
- Deep pagination with `from`/`size`
- Missing query timeouts
- Inefficient sorting
- Large result sets

**Example:**
```bash
multidb-analyzer analyze ./src --db elasticsearch
```

### MySQL

Detects issues related to:
- N+1 query patterns
- Missing indexes
- SELECT N+1 problems
- Inefficient joins
- Missing query limits

**Example:**
```bash
multidb-analyzer analyze ./src --db mysql
```

### Multi-Database

Analyze all supported databases:
```bash
multidb-analyzer analyze ./src --db all
```

---

## LLM Integration

### Setup

1. **Obtain API Key**: Get your Anthropic API key from https://console.anthropic.com/

2. **Set Environment Variable**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

3. **Enable LLM Analysis**:
```bash
multidb-analyzer analyze ./src --llm
```

### Features

When LLM integration is enabled:
- **Deep Semantic Analysis**: Understands code context beyond pattern matching
- **Smart Suggestions**: Provides context-aware optimization recommendations
- **Auto-Fix Generation**: Generates code fixes for common issues
- **False Positive Reduction**: Reduces false positives through semantic understanding

### Configuration

In `config.yaml`:
```yaml
llm:
  enabled: true
  model: "claude-sonnet-3-5-20241022"
  temperature: 0.0
  max_tokens: 4096
  max_retries: 3
  timeout: 30
  batch_size: 10  # Analyze 10 files per batch
```

### Cost Optimization

- **Selective Analysis**: Use `--db` to analyze only specific databases
- **Batch Processing**: Configure `batch_size` to balance speed and cost
- **Caching**: LLM results are cached to avoid redundant API calls

---

## Examples

### Example 1: Basic Java Project Analysis

```bash
# Analyze Java project for Elasticsearch issues
multidb-analyzer analyze ./src/main/java \
  --db elasticsearch \
  --format html,json \
  --output ./reports
```

### Example 2: Python Project with LLM

```bash
# Analyze Python project with LLM optimization
export ANTHROPIC_API_KEY="your-key"
multidb-analyzer analyze ./app \
  --db mysql \
  --llm \
  --format markdown \
  --verbose
```

### Example 3: Multiple Directories

```bash
# Analyze multiple directories
multidb-analyzer analyze \
  ./backend/src \
  ./frontend/api \
  ./shared/utils \
  --db all \
  --format html,json
```

### Example 4: CI/CD Integration

```bash
# CI/CD pipeline script
#!/bin/bash
set -e

# Run analysis
multidb-analyzer analyze ./src \
  --db all \
  --format json \
  --output ./reports

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
  echo "CRITICAL issues found!"
  exit 1
elif [ $EXIT_CODE -eq 1 ]; then
  echo "HIGH severity issues found!"
  exit 1
else
  echo "Analysis passed!"
  exit 0
fi
```

### Example 5: Configuration File

```bash
# Create config file
cat > config.yaml <<EOF
analysis:
  enabled_databases:
    - elasticsearch
    - mysql
  parsers:
    java:
      exclude_patterns:
        - "**/test/**"
        - "**/generated/**"
reports:
  formats:
    - html
    - json
  output_dir: "./analysis-reports"
llm:
  enabled: true
  model: "claude-sonnet-3-5-20241022"
EOF

# Run with config
multidb-analyzer analyze ./src --config config.yaml
```

### Example 6: Dry Run

```bash
# Preview what would be analyzed
multidb-analyzer analyze ./src --dry-run --verbose
```

### Example 7: Filter by Severity

After analysis, filter JSON report:
```bash
# Analyze and generate JSON
multidb-analyzer analyze ./src --format json

# Filter critical issues
jq '.issues[] | select(.severity == "critical")' reports/analysis_report.json
```

---

## Troubleshooting

### Issue: Command Not Found

**Problem:**
```bash
bash: multidb-analyzer: command not found
```

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or use absolute path
python -m multidb_analyzer.cli.main analyze ./src
```

### Issue: API Key Not Found

**Problem:**
```
Error: LLM enabled but no API key provided
```

**Solution:**
```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-key"

# Or pass directly
multidb-analyzer analyze ./src --llm --api-key "your-key"
```

### Issue: No Issues Found

**Problem:**
Analysis completes but reports 0 issues.

**Solution:**
1. Verify file patterns in config
2. Check database type matches your code
3. Enable verbose mode to see what's being analyzed:
```bash
multidb-analyzer analyze ./src --verbose
```

### Issue: Analysis Too Slow

**Problem:**
Analysis takes too long on large codebases.

**Solution:**
1. **Use specific database**: `--db elasticsearch` instead of `--db all`
2. **Exclude test files**: Configure `exclude_patterns` in config
3. **Disable LLM**: Remove `--llm` flag for faster analysis
4. **Parallel processing**: Will be added in future release

### Issue: Permission Denied

**Problem:**
```
PermissionError: [Errno 13] Permission denied: './reports'
```

**Solution:**
```bash
# Create output directory
mkdir -p ./reports
chmod 755 ./reports

# Or specify different directory
multidb-analyzer analyze ./src --output ~/my-reports
```

### Issue: Invalid Configuration

**Problem:**
```
Error: Invalid configuration file
```

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check indentation (YAML is indentation-sensitive)
# Use 2 or 4 spaces, not tabs
```

### Getting Help

```bash
# Show help
multidb-analyzer --help

# Show command help
multidb-analyzer analyze --help

# Check version
multidb-analyzer --version

# Enable debug logging
multidb-analyzer analyze ./src --verbose
```

### Reporting Issues

If you encounter bugs or have feature requests:
1. GitHub Issues: https://github.com/your-org/multidb-analyzer/issues
2. Include:
   - MultiDB Analyzer version (`multidb-analyzer --version`)
   - Python version (`python --version`)
   - Operating system
   - Full error message
   - Steps to reproduce

---

## Advanced Usage

### Custom Detectors

Extend the analyzer with custom detectors:

```python
from multidb_analyzer.core.base_detector import BaseDetector, Issue, Severity

class MyCustomDetector(BaseDetector):
    def detect(self, code: str, file_path: str) -> List[Issue]:
        # Your detection logic
        pass
```

### Programmatic API

Use the analyzer in your Python code:

```python
from multidb_analyzer.unified.analyzer import UnifiedAnalyzer
from multidb_analyzer.unified.analysis_config import AnalysisConfig

# Configure analyzer
config = AnalysisConfig(
    enable_elasticsearch=True,
    enable_mysql=True,
    enable_llm=False
)

# Create analyzer
analyzer = UnifiedAnalyzer(config)

# Run analysis
result = analyzer.analyze(["/path/to/code"])

# Access results
print(f"Found {result.total_issues} issues")
for issue in result.issues:
    print(f"{issue.severity}: {issue.title}")
```

See [API_REFERENCE.md](./API_REFERENCE.md) for detailed API documentation.

---

## Best Practices

### 1. Regular Analysis

Run analysis regularly in CI/CD:
```yaml
# .github/workflows/analysis.yml
name: Code Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run MultiDB Analyzer
        run: |
          pip install -e .
          multidb-analyzer analyze ./src --format json
```

### 2. Incremental Analysis

For large codebases, analyze changed files only:
```bash
# Get changed files
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)

# Analyze only changed files
multidb-analyzer analyze $CHANGED_FILES
```

### 3. Team Configuration

Commit configuration file to repository:
```bash
# .multidb-analyzer.yml
analysis:
  enabled_databases: [elasticsearch, mysql]
  parsers:
    java:
      exclude_patterns: ["**/test/**"]
reports:
  formats: [html, json]
```

### 4. Issue Tracking

Integrate with issue tracking systems:
```bash
# Generate JSON report
multidb-analyzer analyze ./src --format json

# Parse and create issues
python scripts/create_jira_issues.py reports/analysis_report.json
```

---

**For more information:**
- [API Reference](./API_REFERENCE.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)
- [Examples](./EXAMPLES.md)
- [GitHub Repository](https://github.com/your-org/multidb-analyzer)
