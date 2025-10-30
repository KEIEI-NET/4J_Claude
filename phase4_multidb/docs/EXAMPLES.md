# サンプルコード集

**バージョン**: v1.0.0
**最終更新**: 2025年01月27日

## 目次

1. [基本的な使い方](#基本的な使い方)
2. [カスタム検出器の作成](#カスタム検出器の作成)
3. [LLM統合の実践例](#llm統合の実践例)
4. [レポート生成](#レポート生成)
5. [CI/CD統合](#cicd統合)
6. [高度な使用例](#高度な使用例)

---

## 基本的な使い方

### 例1: シンプルな分析

```python
"""
最もシンプルな分析例
"""
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    NPlusOneDetector,
    LargeSizeDetector
)
from multidb_analyzer.core.base_detector import AnalysisContext

# Javaファイルを読み込み
with open('SearchService.java', 'r', encoding='utf-8') as f:
    code = f.read()

# パーサーでクエリを抽出
parser = JavaElasticsearchParser()
queries = parser.parse_file('SearchService.java', code)

print(f"Found {len(queries)} queries")

# 検出器を実行
context = AnalysisContext(
    file_path='SearchService.java',
    code_content=code
)

detectors = [
    WildcardDetector(),
    NPlusOneDetector(),
    LargeSizeDetector()
]

all_issues = []
for detector in detectors:
    issues = detector.detect(queries, context)
    all_issues.extend(issues)
    print(f"{detector.__class__.__name__}: {len(issues)} issues")

# 結果を表示
for issue in all_issues:
    print(f"\n{issue.severity.value}: {issue.title}")
    print(f"  File: {issue.file_path}:{issue.line_number}")
    print(f"  Description: {issue.description}")
    print(f"  Suggestion: {issue.suggestion}")
```

### 例2: ディレクトリ全体を分析

```python
"""
プロジェクト全体を分析する例
"""
from pathlib import Path
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext

def analyze_project(project_dir: str):
    """プロジェクト内の全Javaファイルを分析"""
    parser = JavaElasticsearchParser()
    detectors = get_all_detectors()

    all_issues = []

    # 全Javaファイルを検索
    project_path = Path(project_dir)
    java_files = list(project_path.rglob('*.java'))

    print(f"Analyzing {len(java_files)} Java files...")

    for java_file in java_files:
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                code = f.read()

            # クエリを抽出
            queries = parser.parse_file(str(java_file), code)

            if not queries:
                continue

            # 検出器を実行
            context = AnalysisContext(
                file_path=str(java_file),
                code_content=code
            )

            for detector in detectors:
                issues = detector.detect(queries, context)
                all_issues.extend(issues)

        except Exception as e:
            print(f"Error analyzing {java_file}: {e}")
            continue

    return all_issues

# 実行
if __name__ == '__main__':
    issues = analyze_project('/path/to/project/src')

    # 重大度別に集計
    from collections import Counter
    severity_counts = Counter(issue.severity.value for issue in issues)

    print("\n=== Analysis Summary ===")
    for severity, count in severity_counts.most_common():
        print(f"{severity}: {count} issues")
```

### 例3: 設定ファイルを使った分析

```python
"""
YAMLコンフィグを使った分析例
"""
import yaml
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    LargeSizeDetector
)
from multidb_analyzer.core.base_detector import DetectorConfig, AnalysisContext

# 設定ファイルを読み込み
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 検出器を設定付きで初期化
wildcard_config = DetectorConfig(
    enabled=config['detectors']['wildcard']['enabled'],
    severity_override=config['detectors']['wildcard'].get('severity')
)

large_size_config = DetectorConfig(
    custom_params={
        'size_threshold': config['detectors']['large_size']['size_threshold']
    }
)

detectors = [
    WildcardDetector(config=wildcard_config),
    LargeSizeDetector(config=large_size_config)
]

# 分析実行
parser = JavaElasticsearchParser()
# ... 以下は例1と同様
```

**config.yaml**:
```yaml
detectors:
  wildcard:
    enabled: true
    severity: CRITICAL

  large_size:
    enabled: true
    size_threshold: 500
```

---

## カスタム検出器の作成

### 例4: カスタム検出器の実装

```python
"""
プロジェクト固有のルールを持つカスタム検出器
"""
from typing import List
from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory,
    AnalysisContext
)
from multidb_analyzer.elasticsearch.models import ElasticsearchQuery

class CustomAggregationDetector(BaseDetector):
    """
    複雑なアグリゲーションを検出するカスタム検出器
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.name = "CustomAggregationDetector"

    def detect(
        self,
        queries: List[ElasticsearchQuery],
        context: AnalysisContext
    ) -> List[Issue]:
        """アグリゲーション関連の問題を検出"""
        issues = []

        for query in queries:
            # カスタムロジック: 5階層以上のネストを検出
            if self._has_deep_nested_aggregations(query):
                issues.append(Issue(
                    detector_name=self.name,
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Deep Nested Aggregations",
                    description=(
                        "Query contains deeply nested aggregations (>5 levels) "
                        "which may cause performance issues and high memory usage."
                    ),
                    file_path=context.file_path,
                    line_number=query.line_number,
                    query_text=query.raw_code,
                    suggestion=(
                        "Consider:\n"
                        "1. Flattening the aggregation structure\n"
                        "2. Using composite aggregations\n"
                        "3. Splitting into multiple queries"
                    )
                ))

            # カスタムロジック: カーディナリティ集約の誤用を検出
            if self._has_high_cardinality_aggregation(query):
                issues.append(Issue(
                    detector_name=self.name,
                    severity=Severity.MEDIUM,
                    category=IssueCategory.PERFORMANCE,
                    title="High Cardinality Aggregation",
                    description=(
                        "Aggregation on high cardinality field without proper limits"
                    ),
                    file_path=context.file_path,
                    line_number=query.line_number,
                    query_text=query.raw_code,
                    suggestion="Use 'size' parameter to limit results"
                ))

        return issues

    def _has_deep_nested_aggregations(self, query: ElasticsearchQuery) -> bool:
        """ネストの深さをチェック"""
        code = query.raw_code.lower()
        # シンプルな実装: "aggregation("の出現回数をカウント
        return code.count('aggregation(') > 5

    def _has_high_cardinality_aggregation(self, query: ElasticsearchQuery) -> bool:
        """高カーディナリティフィールドへの集約をチェック"""
        code = query.raw_code.lower()
        high_cardinality_fields = ['user_id', 'session_id', 'ip_address']

        for field in high_cardinality_fields:
            if f'terms("{field}"' in code or f"terms('{field}'" in code:
                # sizeパラメータがあるかチェック
                if '.size(' not in code:
                    return True
        return False

# 使用例
if __name__ == '__main__':
    from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser

    parser = JavaElasticsearchParser()
    custom_detector = CustomAggregationDetector()

    with open('AnalyticsService.java', 'r') as f:
        code = f.read()

    queries = parser.parse_file('AnalyticsService.java', code)
    context = AnalysisContext(
        file_path='AnalyticsService.java',
        code_content=code
    )

    issues = custom_detector.detect(queries, context)
    print(f"Found {len(issues)} custom issues")
```

---

## LLM統合の実践例

### 例5: 基本的なLLM分析

```python
"""
LLMを使った問題分析の基本例
"""
from multidb_analyzer.llm import LLMOptimizer, ClaudeModel
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import WildcardDetector
from multidb_analyzer.core.base_detector import AnalysisContext

# LLM Optimizerを初期化
optimizer = LLMOptimizer(
    api_key="sk-ant-xxxxx",  # または環境変数から
    model=ClaudeModel.SONNET,
    temperature=0.3  # 技術的な分析には低温度
)

# コードを分析
with open('SearchService.java', 'r', encoding='utf-8') as f:
    code = f.read()

parser = JavaElasticsearchParser()
queries = parser.parse_file('SearchService.java', code)

context = AnalysisContext(
    file_path='SearchService.java',
    code_content=code
)

# 問題を検出
detector = WildcardDetector()
issues = detector.detect(queries, context)

# LLMで詳細分析
for issue in issues:
    print(f"\nAnalyzing: {issue.title}")

    # コードスニペットを抽出（問題の前後5行）
    lines = code.split('\n')
    start = max(0, issue.line_number - 5)
    end = min(len(lines), issue.line_number + 5)
    code_snippet = '\n'.join(lines[start:end])

    # LLMで最適化提案を生成
    result = optimizer.optimize_issue(
        issue=issue,
        code=code_snippet,
        language="java",
        db_type="elasticsearch"
    )

    print(f"\n=== Optimization Result ===")
    print(f"Root Cause: {result.root_cause}")
    print(f"Performance Impact: {result.performance_impact}")
    print(f"\nOptimized Code:\n{result.optimized_code}")
    print(f"\nImplementation Steps:")
    for i, step in enumerate(result.implementation_steps, 1):
        print(f"{i}. {step}")
    print(f"\nTesting Strategy: {result.testing_strategy}")
    print(f"Trade-offs: {result.trade_offs}")
    print(f"Confidence: {result.confidence_score:.2f}")

# API使用統計を確認
stats = optimizer.get_usage_stats()
print(f"\n=== API Usage ===")
print(f"Total requests: {stats['total_requests']}")
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
```

### 例6: バッチ最適化

```python
"""
複数の問題を効率的にバッチ処理
"""
from multidb_analyzer.llm import LLMOptimizer
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext

def extract_code_snippets(code: str, issues: list, context_lines: int = 5):
    """問題箇所のコードスニペットを抽出"""
    lines = code.split('\n')
    snippets = {}

    for issue in issues:
        start = max(0, issue.line_number - context_lines)
        end = min(len(lines), issue.line_number + context_lines)
        snippet = '\n'.join(lines[start:end])

        key = f"{issue.file_path}:{issue.line_number}"
        snippets[key] = snippet

    return snippets

# 分析とバッチ最適化
optimizer = LLMOptimizer(api_key="sk-ant-xxxxx")
parser = JavaElasticsearchParser()
detectors = get_all_detectors()

with open('SearchService.java', 'r') as f:
    code = f.read()

queries = parser.parse_file('SearchService.java', code)
context = AnalysisContext(file_path='SearchService.java', code_content=code)

# すべての問題を検出
all_issues = []
for detector in detectors:
    issues = detector.detect(queries, context)
    all_issues.extend(issues)

print(f"Found {len(all_issues)} issues")

# コードスニペットを抽出
code_snippets = extract_code_snippets(code, all_issues)

# バッチ最適化（APIコールを最小化）
print("Running batch optimization...")
results = optimizer.optimize_batch(
    issues=all_issues,
    code_snippets=code_snippets,
    language="java"
)

# 結果を保存
import json
output_data = {
    'total_issues': len(all_issues),
    'optimizations': [result.to_dict() for result in results]
}

with open('optimization_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"Saved results to optimization_results.json")
```

### 例7: 問題の優先順位付け

```python
"""
LLMを使って問題の優先順位を決定
"""
from multidb_analyzer.llm import LLMOptimizer
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext

# 問題を検出（省略）
# all_issues = ...

optimizer = LLMOptimizer()

# LLMで優先順位を決定
print("Prioritizing issues with LLM...")
prioritization = optimizer.prioritize_issues(all_issues)

# Quick Winsを表示
print("\n=== Quick Wins (easy, high impact) ===")
for issue_id in prioritization['quick_wins']:
    issue = all_issues[int(issue_id)]
    print(f"- {issue.title} ({issue.file_path}:{issue.line_number})")

# High Risk, High Rewardを表示
print("\n=== High Risk, High Reward ===")
for issue_id in prioritization['high_risk_high_reward']:
    issue = all_issues[int(issue_id)]
    print(f"- {issue.title} ({issue.file_path}:{issue.line_number})")

# 優先順位付きリストを表示
print("\n=== Prioritized Issues ===")
for item in prioritization['prioritized_issues']:
    issue = all_issues[item['issue_id']]
    print(f"{item['recommended_order']}. [{item['priority_score']:.2f}] {issue.title}")
    print(f"   {issue.file_path}:{issue.line_number}")
```

### 例8: 自動修正の生成と適用

```python
"""
自動修正コードの生成と適用
"""
from multidb_analyzer.llm import LLMOptimizer
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import WildcardDetector
from multidb_analyzer.core.base_detector import AnalysisContext
import re

def apply_fix(file_path: str, line_number: int, original_code: str, fixed_code: str):
    """ファイルに修正を適用"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 元のコードを検索して置換
    for i, line in enumerate(lines):
        if original_code.strip() in line and i + 1 == line_number:
            lines[i] = line.replace(original_code.strip(), fixed_code.strip())
            break

    # バックアップを作成
    backup_path = f"{file_path}.backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"Applied fix to {file_path} (backup: {backup_path})")

# 問題を検出
optimizer = LLMOptimizer()
parser = JavaElasticsearchParser()

with open('SearchService.java', 'r') as f:
    code = f.read()

queries = parser.parse_file('SearchService.java', code)
context = AnalysisContext(file_path='SearchService.java', code_content=code)

detector = WildcardDetector()
issues = detector.detect(queries, context)

# 自動修正を生成
for issue in issues:
    print(f"\nGenerating fix for: {issue.title}")

    # コードスニペットを抽出
    lines = code.split('\n')
    problem_line = lines[issue.line_number - 1]

    # 自動修正を生成
    fix = optimizer.generate_auto_fix(
        issue=issue,
        code=problem_line,
        db_type="elasticsearch",
        framework="Spring Data",
        language="java"
    )

    print(f"Confidence: {fix['confidence']:.2f}")

    if fix['confidence'] > 0.8:
        print(f"Original: {problem_line.strip()}")
        print(f"Fixed:    {fix['fixed_code'].strip()}")

        # ユーザー確認
        response = input("Apply this fix? (y/n): ")
        if response.lower() == 'y':
            apply_fix(
                file_path='SearchService.java',
                line_number=issue.line_number,
                original_code=problem_line.strip(),
                fixed_code=fix['fixed_code'].strip()
            )
        else:
            print("Skipped")
    else:
        print("Confidence too low, skipping auto-fix")
        print(f"Migration notes: {fix['migration_notes']}")
```

---

## レポート生成

### 例9: HTMLレポートのカスタマイズ

```python
"""
カスタマイズされたHTMLレポートを生成
"""
from multidb_analyzer.reporters import HTMLReporter, ReportConfig
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext
from datetime import datetime

# 分析を実行（省略）
# all_issues = ...

# レポート設定
config = ReportConfig(
    title=f"Elasticsearch Analysis Report - {datetime.now().strftime('%Y-%m-%d')}",
    subtitle="SearchService.java Analysis",
    include_statistics=True,
    include_code_snippets=True,
    max_snippet_lines=10,
    group_by='severity',  # 'file', 'detector', 'severity'
    custom_css="""
        .critical { background-color: #ff4444; }
        .high { background-color: #ffaa00; }
        .medium { background-color: #ffdd00; }
    """
)

# HTMLレポートを生成
reporter = HTMLReporter(config=config)
reporter.generate(
    issues=all_issues,
    output_path='./reports/analysis_report.html'
)

print("Report generated: ./reports/analysis_report.html")
```

### 例10: 複数形式のレポート生成

```python
"""
HTML、JSON、Markdownを同時に生成
"""
from multidb_analyzer.reporters import (
    HTMLReporter,
    JSONReporter,
    MarkdownReporter,
    ReportConfig
)

# 分析結果（省略）
# all_issues = ...

output_dir = './reports'
base_config = ReportConfig(
    title="Elasticsearch Analysis Report",
    include_statistics=True
)

# HTML
html_reporter = HTMLReporter(base_config)
html_reporter.generate(all_issues, f"{output_dir}/report.html")

# JSON (CI/CD向け)
json_reporter = JSONReporter(base_config)
json_reporter.generate(all_issues, f"{output_dir}/report.json")

# Markdown (GitHub向け)
md_reporter = MarkdownReporter(base_config)
md_reporter.generate(all_issues, f"{output_dir}/REPORT.md")

print(f"Reports generated in {output_dir}/")
```

---

## CI/CD統合

### 例11: GitHub Actions統合

```yaml
# .github/workflows/code-analysis.yml
name: Elasticsearch Code Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd phase4_multidb
          pip install -r requirements.txt
          pip install -e .

      - name: Run Elasticsearch Analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m multidb_analyzer analyze ./src \
            --format json \
            --output ./reports/analysis.json

      - name: Check for critical issues
        run: |
          python .github/scripts/check_critical_issues.py ./reports/analysis.json

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: analysis-report
          path: ./reports/analysis.json

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('./reports/analysis.json'));
            const body = `## Elasticsearch Analysis Results

            - Total Issues: ${report.total_issues}
            - Critical: ${report.critical_count}
            - High: ${report.high_count}

            [View Full Report](link-to-artifact)`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

**check_critical_issues.py**:
```python
#!/usr/bin/env python3
"""CI/CDで使用: CRITICALな問題がある場合はビルド失敗"""
import sys
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: check_critical_issues.py <report.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        report = json.load(f)

    critical_issues = [
        issue for issue in report['issues']
        if issue['severity'] == 'CRITICAL'
    ]

    if critical_issues:
        print(f"❌ Found {len(critical_issues)} CRITICAL issues:")
        for issue in critical_issues:
            print(f"  - {issue['title']} ({issue['file_path']}:{issue['line_number']})")
        sys.exit(1)
    else:
        print("✅ No critical issues found")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

---

## 高度な使用例

### 例12: パフォーマンス最適化

```python
"""
大規模コードベースの並列分析
"""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext

def analyze_file(file_path: str):
    """単一ファイルを分析"""
    try:
        parser = JavaElasticsearchParser()
        detectors = get_all_detectors()

        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        queries = parser.parse_file(file_path, code)
        if not queries:
            return []

        context = AnalysisContext(file_path=file_path, code_content=code)

        all_issues = []
        for detector in detectors:
            issues = detector.detect(queries, context)
            all_issues.extend(issues)

        return all_issues

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return []

def parallel_analysis(project_dir: str, max_workers: int = 4):
    """プロジェクトを並列分析"""
    # Javaファイルを検索
    project_path = Path(project_dir)
    java_files = list(project_path.rglob('*.java'))

    print(f"Analyzing {len(java_files)} files with {max_workers} workers...")

    all_issues = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # ファイルを並列処理
        future_to_file = {
            executor.submit(analyze_file, str(f)): f
            for f in java_files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                issues = future.result()
                all_issues.extend(issues)
                print(f"✓ {file_path.name}: {len(issues)} issues")
            except Exception as e:
                print(f"✗ {file_path.name}: {e}")

    return all_issues

# 実行
if __name__ == '__main__':
    issues = parallel_analysis('/path/to/large/project', max_workers=8)
    print(f"\nTotal: {len(issues)} issues found")
```

### 例13: 継続的モニタリング

```python
"""
プロジェクトの変更を監視して自動分析
"""
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.elasticsearch.detectors import get_all_detectors
from multidb_analyzer.core.base_detector import AnalysisContext

class JavaFileHandler(FileSystemEventHandler):
    """Javaファイルの変更を監視"""

    def __init__(self):
        self.parser = JavaElasticsearchParser()
        self.detectors = get_all_detectors()

    def on_modified(self, event):
        if event.is_directory:
            return

        if not event.src_path.endswith('.java'):
            return

        print(f"\n📝 File modified: {event.src_path}")
        self.analyze_file(event.src_path)

    def analyze_file(self, file_path: str):
        """ファイルを分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            queries = self.parser.parse_file(file_path, code)

            if not queries:
                print("  ℹ️ No queries found")
                return

            context = AnalysisContext(file_path=file_path, code_content=code)

            all_issues = []
            for detector in self.detectors:
                issues = detector.detect(queries, context)
                all_issues.extend(issues)

            if all_issues:
                print(f"  ⚠️ Found {len(all_issues)} issues:")
                for issue in all_issues[:5]:  # 最初の5件のみ表示
                    print(f"    - {issue.severity.value}: {issue.title}")
                if len(all_issues) > 5:
                    print(f"    ... and {len(all_issues) - 5} more")
            else:
                print("  ✅ No issues found")

        except Exception as e:
            print(f"  ❌ Error: {e}")

# 監視開始
if __name__ == '__main__':
    path = '/path/to/project/src'
    event_handler = JavaFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print(f"👀 Watching for changes in {path}...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
```

---

## まとめ

このサンプルコード集では、以下のトピックをカバーしました:

1. **基本的な使い方**: シンプルな分析からディレクトリ全体の分析まで
2. **カスタム検出器**: プロジェクト固有のルールを実装
3. **LLM統合**: Claude APIを使った高度な分析
4. **レポート生成**: 複数形式でのレポート出力
5. **CI/CD統合**: GitHub Actionsでの自動化
6. **高度な使用例**: 並列処理と継続的モニタリング

---

**次のステップ**: [LLM_INTEGRATION.md](./LLM_INTEGRATION.md)でLLM統合の詳細を学んでください。
