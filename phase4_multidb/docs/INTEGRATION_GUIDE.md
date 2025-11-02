# MultiDB Analyzer Integration Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-03

## Table of Contents

- [CI/CD Integration](#cicd-integration)
  - [GitHub Actions](#github-actions)
  - [GitLab CI](#gitlab-ci)
  - [Jenkins](#jenkins)
  - [Azure Pipelines](#azure-pipelines)
- [Git Hooks](#git-hooks)
- [IDE Integration](#ide-integration)
- [Build Tools](#build-tools)
- [Issue Tracking](#issue-tracking)
- [Monitoring & Metrics](#monitoring--metrics)
- [Custom Integrations](#custom-integrations)

---

## CI/CD Integration

### GitHub Actions

#### Basic Workflow

Create `.github/workflows/multidb-analysis.yml`:

```yaml
name: MultiDB Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

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
      run: |
        pip install multidb-analyzer

    - name: Run Analysis
      run: |
        multidb-analyzer analyze ./src \
          --format json,html \
          --output ./reports

    - name: Check Results
      run: |
        # Fail if critical issues found (exit code 2)
        if [ $? -eq 2 ]; then
          echo "❌ Critical issues found!"
          exit 1
        fi

    - name: Upload Reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: analysis-reports
        path: reports/
```

#### Advanced Workflow with LLM

```yaml
name: MultiDB Analysis (LLM)

on:
  pull_request:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for changed files

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install MultiDB Analyzer
      run: pip install multidb-analyzer

    - name: Get Changed Files
      id: changed-files
      uses: tj-actions/changed-files@v37
      with:
        files: |
          **/*.java
          **/*.py

    - name: Run Analysis on Changed Files
      if: steps.changed-files.outputs.any_changed == 'true'
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        multidb-analyzer analyze \
          ${{ steps.changed-files.outputs.all_changed_files }} \
          --llm \
          --format json,markdown \
          --output ./reports

    - name: Comment PR with Results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const report = fs.readFileSync('./reports/analysis_report.md', 'utf8');

          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## 📊 MultiDB Analysis Results\n\n${report}`
          });

    - name: Upload Artifacts
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: multidb-reports
        path: reports/
```

#### Matrix Strategy for Multiple Projects

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project:
          - { path: './backend', db: 'elasticsearch,mysql' }
          - { path: './api', db: 'mysql' }
          - { path: './search-service', db: 'elasticsearch' }

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install MultiDB Analyzer
      run: pip install multidb-analyzer

    - name: Analyze ${{ matrix.project.path }}
      run: |
        multidb-analyzer analyze ${{ matrix.project.path }} \
          --db ${{ matrix.project.db }} \
          --format json \
          --output ./reports/${{ matrix.project.path }}

    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: reports-${{ matrix.project.path }}
        path: reports/
```

---

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - analyze
  - report

variables:
  REPORTS_DIR: "reports"

multidb_analysis:
  stage: analyze
  image: python:3.11
  before_script:
    - pip install multidb-analyzer
  script:
    - |
      multidb-analyzer analyze ./src \
        --format json,html \
        --output ${REPORTS_DIR}
  artifacts:
    when: always
    paths:
      - ${REPORTS_DIR}/
    reports:
      junit: ${REPORTS_DIR}/analysis_report.json
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'

generate_badges:
  stage: report
  image: python:3.11
  script:
    - python scripts/generate_badges.py ${REPORTS_DIR}/analysis_report.json
  artifacts:
    paths:
      - badges/
  needs:
    - multidb_analysis
```

#### With Quality Gates

```yaml
multidb_analysis:
  stage: analyze
  image: python:3.11
  script:
    - pip install multidb-analyzer
    - |
      multidb-analyzer analyze ./src \
        --format json \
        --output ${REPORTS_DIR}
    - python scripts/check_quality_gate.py ${REPORTS_DIR}/analysis_report.json
  allow_failure: false
```

**scripts/check_quality_gate.py:**

```python
import json
import sys
from pathlib import Path

def check_quality_gate(report_path: Path) -> int:
    """Check if analysis meets quality gates."""
    with open(report_path) as f:
        report = json.load(f)

    stats = report['statistics']['by_severity']

    # Define thresholds
    if stats.get('critical', 0) > 0:
        print("❌ Quality gate failed: Critical issues found")
        return 1

    if stats.get('high', 0) > 5:
        print(f"❌ Quality gate failed: Too many high severity issues ({stats['high']})")
        return 1

    print("✅ Quality gate passed")
    return 0

if __name__ == "__main__":
    sys.exit(check_quality_gate(Path(sys.argv[1])))
```

---

### Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
        REPORTS_DIR = 'reports'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install multidb-analyzer
                '''
            }
        }

        stage('Analysis') {
            steps {
                sh '''
                    . venv/bin/activate
                    multidb-analyzer analyze ./src \
                        --llm \
                        --format json,html \
                        --output ${REPORTS_DIR}
                '''
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def report = readJSON file: "${REPORTS_DIR}/analysis_report.json"
                    def critical = report.statistics.by_severity.critical ?: 0

                    if (critical > 0) {
                        error("Quality gate failed: ${critical} critical issues found")
                    }
                }
            }
        }

        stage('Publish') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: "${REPORTS_DIR}",
                    reportFiles: 'analysis_report.html',
                    reportName: 'MultiDB Analysis Report'
                ])
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: "${REPORTS_DIR}/**/*", allowEmptyArchive: true
        }
        failure {
            emailext(
                subject: "MultiDB Analysis Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Analysis found critical issues. Check ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

---

### Azure Pipelines

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
    - main
    - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'
  reportsDir: '$(Build.ArtifactStagingDirectory)/reports'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'
  displayName: 'Use Python $(pythonVersion)'

- script: |
    pip install multidb-analyzer
  displayName: 'Install MultiDB Analyzer'

- script: |
    multidb-analyzer analyze ./src \
      --format json,html \
      --output $(reportsDir)
  displayName: 'Run Analysis'
  env:
    ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: '$(reportsDir)'
    ArtifactName: 'multidb-reports'
  displayName: 'Publish Reports'
  condition: always()

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '$(reportsDir)/**/*.json'
  displayName: 'Publish Test Results'
  condition: always()
```

---

## Git Hooks

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# MultiDB Analyzer pre-commit hook

echo "🔍 Running MultiDB Analyzer on staged files..."

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(java|py)$')

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No relevant files to analyze"
    exit 0
fi

# Run analyzer on staged files
multidb-analyzer analyze $STAGED_FILES \
    --format json \
    --output /tmp/multidb-analysis

EXIT_CODE=$?

# Check results
if [ $EXIT_CODE -eq 2 ]; then
    echo "❌ Critical issues found! Commit blocked."
    echo "Run 'multidb-analyzer analyze' to see details."
    exit 1
elif [ $EXIT_CODE -eq 1 ]; then
    echo "⚠️  High severity issues found."
    read -p "Continue with commit? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Analysis passed"
exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Pre-push Hook

Create `.git/hooks/pre-push`:

```bash
#!/bin/bash

# MultiDB Analyzer pre-push hook

echo "🔍 Running full analysis before push..."

multidb-analyzer analyze ./src \
    --format json \
    --output /tmp/multidb-analysis

EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo "❌ Critical issues found! Push blocked."
    echo "Fix issues before pushing or use --no-verify to bypass."
    exit 1
fi

echo "✅ Analysis passed"
exit 0
```

### Using pre-commit Framework

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: multidb-analyzer
        name: MultiDB Analyzer
        entry: multidb-analyzer analyze
        language: system
        types: [java, python]
        args: ['--format', 'console']
        pass_filenames: true
        verbose: true
```

Install:
```bash
pip install pre-commit
pre-commit install
```

---

## IDE Integration

### VS Code

#### Task Configuration

Create `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "MultiDB Analyzer: Current File",
            "type": "shell",
            "command": "multidb-analyzer",
            "args": [
                "analyze",
                "${file}",
                "--format",
                "console"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "MultiDB Analyzer: Project",
            "type": "shell",
            "command": "multidb-analyzer",
            "args": [
                "analyze",
                "${workspaceFolder}/src",
                "--format",
                "html",
                "--output",
                "${workspaceFolder}/reports"
            ],
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            }
        }
    ]
}
```

#### Launch Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "MultiDB Analyzer: Debug",
            "type": "python",
            "request": "launch",
            "module": "multidb_analyzer.cli.main",
            "args": [
                "analyze",
                "${workspaceFolder}/src",
                "--verbose"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

### IntelliJ IDEA

#### External Tools

1. **Settings** → **Tools** → **External Tools**
2. **Add** new tool:
   - **Name**: MultiDB Analyzer
   - **Program**: `multidb-analyzer`
   - **Arguments**: `analyze $FilePath$ --format console`
   - **Working directory**: `$ProjectFileDir$`

#### Run Configuration

Create run configuration for full project analysis:

1. **Run** → **Edit Configurations**
2. **Add** → **Shell Script**
3. Configure:
   - **Script text**: `multidb-analyzer analyze ./src --format html --output ./reports`
   - **Working directory**: Project root

---

## Build Tools

### Maven

Add to `pom.xml`:

```xml
<project>
    <build>
        <plugins>
            <plugin>
                <groupId>org.codehaus.mojo</groupId>
                <artifactId>exec-maven-plugin</artifactId>
                <version>3.1.0</version>
                <executions>
                    <execution>
                        <id>multidb-analysis</id>
                        <phase>verify</phase>
                        <goals>
                            <goal>exec</goal>
                        </goals>
                        <configuration>
                            <executable>multidb-analyzer</executable>
                            <arguments>
                                <argument>analyze</argument>
                                <argument>${project.basedir}/src</argument>
                                <argument>--format</argument>
                                <argument>json,html</argument>
                                <argument>--output</argument>
                                <argument>${project.build.directory}/multidb-reports</argument>
                            </arguments>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

Run:
```bash
mvn verify
```

### Gradle

Add to `build.gradle`:

```groovy
task multidbAnalysis(type: Exec) {
    description = 'Run MultiDB Analyzer'
    group = 'verification'

    commandLine 'multidb-analyzer', 'analyze', 'src',
                '--format', 'json,html',
                '--output', "${buildDir}/multidb-reports"
}

check.dependsOn multidbAnalysis
```

Run:
```bash
./gradlew multidbAnalysis
```

### Make

Add to `Makefile`:

```makefile
.PHONY: analyze
analyze:
	multidb-analyzer analyze ./src \
		--format html,json \
		--output ./reports

.PHONY: analyze-llm
analyze-llm:
	multidb-analyzer analyze ./src \
		--llm \
		--format html,json \
		--output ./reports

.PHONY: analyze-ci
analyze-ci:
	multidb-analyzer analyze ./src \
		--format json \
		--output ./reports
	@if [ $$? -eq 2 ]; then \
		echo "Critical issues found!"; \
		exit 1; \
	fi
```

Run:
```bash
make analyze
make analyze-llm
make analyze-ci
```

---

## Issue Tracking

### JIRA Integration

**scripts/create_jira_issues.py:**

```python
import json
import sys
from jira import JIRA

def create_jira_issues(report_path: str, jira_url: str, api_token: str):
    """Create JIRA issues from analysis report."""

    # Connect to JIRA
    jira = JIRA(server=jira_url, token_auth=api_token)

    # Load report
    with open(report_path) as f:
        report = json.load(f)

    # Create issues for critical/high severity
    for issue in report['issues']:
        if issue['severity'] in ['critical', 'high']:
            jira.create_issue(
                project='TECH_DEBT',
                summary=f"[DB] {issue['title']}",
                description=f"""
*File:* {issue['file_path']}:{issue.get('line_number', 'N/A')}
*Severity:* {issue['severity'].upper()}
*Category:* {issue['category']}

h3. Description
{issue['description']}

h3. Suggestion
{issue.get('suggestion', 'No suggestion provided')}

*Detected by:* {issue['detector_name']}
                """,
                issuetype={'name': 'Technical Debt'},
                priority={'name': 'High' if issue['severity'] == 'critical' else 'Medium'}
            )
            print(f"Created JIRA issue for: {issue['title']}")

if __name__ == "__main__":
    create_jira_issues(
        sys.argv[1],
        "https://your-company.atlassian.net",
        sys.argv[2]
    )
```

Usage in CI:
```bash
multidb-analyzer analyze ./src --format json
python scripts/create_jira_issues.py reports/analysis_report.json $JIRA_API_TOKEN
```

### GitHub Issues

```python
import json
import sys
from github import Github

def create_github_issues(report_path: str, repo_name: str, token: str):
    """Create GitHub issues from analysis report."""

    g = Github(token)
    repo = g.get_repo(repo_name)

    with open(report_path) as f:
        report = json.load(f)

    for issue in report['issues']:
        if issue['severity'] in ['critical', 'high']:
            repo.create_issue(
                title=f"[{issue['severity'].upper()}] {issue['title']}",
                body=f"""
## Details
- **File:** `{issue['file_path']}:{issue.get('line_number', 'N/A')}`
- **Severity:** {issue['severity'].upper()}
- **Category:** {issue['category']}
- **Detector:** {issue['detector_name']}

## Description
{issue['description']}

## Suggestion
{issue.get('suggestion', 'No suggestion provided')}
                """,
                labels=['technical-debt', 'database', issue['severity']]
            )

if __name__ == "__main__":
    create_github_issues(sys.argv[1], sys.argv[2], sys.argv[3])
```

---

## Monitoring & Metrics

### Prometheus

Export metrics:

**scripts/export_metrics.py:**

```python
import json
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def export_metrics(report_path: str, pushgateway_url: str):
    """Export analysis metrics to Prometheus."""

    with open(report_path) as f:
        report = json.load(f)

    registry = CollectorRegistry()

    # Define metrics
    total_issues = Gauge('multidb_total_issues', 'Total issues found', registry=registry)
    critical_issues = Gauge('multidb_critical_issues', 'Critical issues', registry=registry)
    high_issues = Gauge('multidb_high_issues', 'High severity issues', registry=registry)
    analysis_time = Gauge('multidb_analysis_time_seconds', 'Analysis execution time', registry=registry)

    # Set values
    total_issues.set(report['summary']['total_issues'])
    critical_issues.set(report['statistics']['by_severity'].get('critical', 0))
    high_issues.set(report['statistics']['by_severity'].get('high', 0))
    analysis_time.set(report['summary']['execution_time'])

    # Push to gateway
    push_to_gateway(pushgateway_url, job='multidb-analyzer', registry=registry)

if __name__ == "__main__":
    import sys
    export_metrics(sys.argv[1], sys.argv[2])
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "MultiDB Analyzer Metrics",
    "panels": [
      {
        "title": "Issues by Severity",
        "targets": [
          {
            "expr": "multidb_critical_issues",
            "legendFormat": "Critical"
          },
          {
            "expr": "multidb_high_issues",
            "legendFormat": "High"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Total Issues Trend",
        "targets": [
          {
            "expr": "multidb_total_issues",
            "legendFormat": "Total Issues"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## Custom Integrations

### Slack Notifications

```python
import json
import sys
import requests

def send_slack_notification(report_path: str, webhook_url: str):
    """Send analysis results to Slack."""

    with open(report_path) as f:
        report = json.load(f)

    stats = report['statistics']['by_severity']
    critical = stats.get('critical', 0)
    high = stats.get('high', 0)

    color = 'danger' if critical > 0 else ('warning' if high > 5 else 'good')

    message = {
        "attachments": [
            {
                "color": color,
                "title": "MultiDB Analysis Results",
                "fields": [
                    {"title": "Total Issues", "value": str(report['summary']['total_issues']), "short": True},
                    {"title": "Critical", "value": str(critical), "short": True},
                    {"title": "High", "value": str(high), "short": True},
                    {"title": "Execution Time", "value": f"{report['summary']['execution_time']:.2f}s", "short": True}
                ]
            }
        ]
    }

    requests.post(webhook_url, json=message)

if __name__ == "__main__":
    send_slack_notification(sys.argv[1], sys.argv[2])
```

### SonarQube

Generate SonarQube-compatible report:

```python
import json
from xml.etree import ElementTree as ET

def convert_to_sonarqube(report_path: str, output_path: str):
    """Convert MultiDB report to SonarQube format."""

    with open(report_path) as f:
        report = json.load(f)

    root = ET.Element("issues")

    for issue in report['issues']:
        issue_elem = ET.SubElement(root, "issue")

        ET.SubElement(issue_elem, "file").text = issue['file_path']
        ET.SubElement(issue_elem, "line").text = str(issue.get('line_number', 1))
        ET.SubElement(issue_elem, "rule").text = issue['detector_name']
        ET.SubElement(issue_elem, "severity").text = issue['severity'].upper()
        ET.SubElement(issue_elem, "message").text = issue['title']
        ET.SubElement(issue_elem, "description").text = issue['description']

    tree = ET.ElementTree(root)
    tree.write(output_path)

if __name__ == "__main__":
    import sys
    convert_to_sonarqube(sys.argv[1], sys.argv[2])
```

---

**For more information:**
- [CLI Usage Guide](./CLI_USAGE.md)
- [API Reference](./API_REFERENCE.md)
- [Examples](./EXAMPLES.md)
