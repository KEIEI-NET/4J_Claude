# USAGE.md - 使用方法ガイド

Cassandra Code Analyzerの詳細な使用方法とサンプルコード集です。

## 目次

- [基本的な使い方](#基本的な使い方)
- [分析方法](#分析方法)
- [レポート生成](#レポート生成)
- [設定とカスタマイズ](#設定とカスタマイズ)
- [実践的なユースケース](#実践的なユースケース)
- [トラブルシューティング](#トラブルシューティング)

## 基本的な使い方

### Pythonスクリプトでの使用

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# 基本的な分析
analyzer = CassandraAnalyzer()
result = analyzer.analyze_file("path/to/UserDao.java")

# 結果の表示
print(f"検出された問題: {result.total_issues}件")
print(f"Critical: {result.critical_count}件")
print(f"High: {result.high_count}件")
print(f"Medium: {result.medium_count}件")
print(f"Low: {result.low_count}件")
```

### インタラクティブシェルでの使用

```python
>>> from cassandra_analyzer.analyzer import CassandraAnalyzer
>>> from cassandra_analyzer.reporters import MarkdownReporter

>>> analyzer = CassandraAnalyzer()
>>> result = analyzer.analyze_directory("./dao")
>>>
>>> # 重要度の高い問題のみ表示
>>> critical_issues = result.get_critical_issues()
>>> for issue in critical_issues:
...     print(f"{issue.file_path}:{issue.line_number} - {issue.message}")
```

## 分析方法

### 単一ファイルの分析

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

analyzer = CassandraAnalyzer()

# ファイルパスを指定して分析
result = analyzer.analyze_file("src/main/java/com/example/dao/UserDao.java")

# 結果の確認
if result.total_issues > 0:
    print(f"⚠️ {result.total_issues}個の問題が検出されました")
    for issue in result.issues:
        print(f"  - {issue.severity.upper()}: {issue.message} ({issue.file_path}:{issue.line_number})")
else:
    print("✅ 問題は検出されませんでした")
```

### ディレクトリ全体の分析

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

analyzer = CassandraAnalyzer()

# ディレクトリを再帰的に分析
result = analyzer.analyze_directory(
    directory="src/main/java/com/example/dao",
    pattern="**/*.java"  # デフォルト: 全Javaファイル
)

# ファイル別の問題を表示
issues_by_file = result.get_issues_by_file()
for file_path, issues in issues_by_file.items():
    print(f"\n📁 {file_path}")
    for issue in issues:
        print(f"  L{issue.line_number}: [{issue.severity}] {issue.message}")
```

### 複数ファイルの個別分析

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

analyzer = CassandraAnalyzer()

# 特定のファイルリストを分析
files_to_analyze = [
    "dao/UserDao.java",
    "dao/OrderDao.java",
    "dao/ProductDao.java",
]

result = analyzer.analyze_files(files_to_analyze)

print(f"分析ファイル数: {result.total_files}")
print(f"検出問題数: {result.total_issues}")
```

## レポート生成

### JSON形式のレポート

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import JSONReporter

# 分析実行
analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# JSONレポート生成
json_reporter = JSONReporter()
report = json_reporter.generate(result)

# ファイルに保存
json_reporter.save(report, "reports/analysis_report.json")

# または一括で生成・保存
json_reporter.generate_and_save(result, "reports/analysis_report.json")

print("✅ JSONレポートを生成しました: reports/analysis_report.json")
```

#### JSONレポートのカスタマイズ

```python
from cassandra_analyzer.reporters import JSONReporter

# カスタム設定でレポーター作成
json_reporter = JSONReporter(config={
    "indent": 4,            # インデントを4スペースに
    "ensure_ascii": False   # 日本語をそのまま出力
})

report = json_reporter.generate(result)
json_reporter.save(report, "reports/custom_report.json")
```

### Markdown形式のレポート

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import MarkdownReporter

analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# Markdownレポート生成
md_reporter = MarkdownReporter()
md_reporter.generate_and_save(result, "reports/analysis_report.md")

print("✅ Markdownレポートを生成しました: reports/analysis_report.md")
```

#### Markdownレポートのグループ化オプション

```python
from cassandra_analyzer.reporters import MarkdownReporter

# ファイル別にグループ化（デフォルト）
md_reporter_by_file = MarkdownReporter(config={
    "group_by_file": True
})
md_reporter_by_file.generate_and_save(result, "reports/by_file.md")

# 重要度別にグループ化
md_reporter_by_severity = MarkdownReporter(config={
    "group_by_file": False
})
md_reporter_by_severity.generate_and_save(result, "reports/by_severity.md")
```

### HTML形式のレポート

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import HTMLReporter

analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# HTMLレポート生成
html_reporter = HTMLReporter()
html_reporter.generate_and_save(result, "reports/analysis_report.html")

print("✅ HTMLレポートを生成しました: reports/analysis_report.html")
print("   ブラウザで開いて確認してください")
```

#### HTMLレポートのカスタマイズ

```python
from cassandra_analyzer.reporters import HTMLReporter

# カスタムタイトルでレポート生成
html_reporter = HTMLReporter(config={
    "title": "Production Code Analysis - 2025-01-15"
})
html_reporter.generate_and_save(result, "reports/production_analysis.html")
```

### 全形式のレポートを一括生成

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import JSONReporter, MarkdownReporter, HTMLReporter

# 分析実行
analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# 3形式全てのレポートを生成
reporters = {
    "json": JSONReporter(),
    "markdown": MarkdownReporter(),
    "html": HTMLReporter(),
}

for format_name, reporter in reporters.items():
    output_file = f"reports/analysis_report.{reporter.file_extension.lstrip('.')}"
    reporter.generate_and_save(result, output_file)
    print(f"✅ {reporter.format_name}レポートを生成: {output_file}")
```

## 設定とカスタマイズ

### 検出器の選択的有効化

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# ALLOW FILTERINGとPartition Key問題のみ検出
config = {
    "detectors": ["allow_filtering", "partition_key"]
}

analyzer = CassandraAnalyzer(config=config)
result = analyzer.analyze_directory("./dao")
```

### 検出器パラメータのカスタマイズ

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# Batch Sizeの閾値を変更
config = {
    "detector_configs": {
        "batch_size": {
            "threshold": 50  # デフォルトは100
        }
    }
}

analyzer = CassandraAnalyzer(config=config)
result = analyzer.analyze_file("dao/OrderDao.java")
```

### 複合設定例

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# 詳細な設定
config = {
    # 有効な検出器を指定
    "detectors": [
        "allow_filtering",
        "partition_key",
        "batch_size"
    ],

    # 検出器別の設定
    "detector_configs": {
        "batch_size": {
            "threshold": 50
        }
    }
}

analyzer = CassandraAnalyzer(config=config)
result = analyzer.analyze_directory("./dao")

print(f"有効な検出器数: {len(analyzer.detectors)}")
```

## 実践的なユースケース

### ユースケース1: CI/CDパイプラインへの統合

```python
#!/usr/bin/env python3
"""
CI/CD用分析スクリプト
"""
import sys
from pathlib import Path
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import JSONReporter

def main():
    # プロジェクトのDAOディレクトリを分析
    analyzer = CassandraAnalyzer()
    result = analyzer.analyze_directory("src/main/java/com/example/dao")

    # JSONレポート生成
    json_reporter = JSONReporter()
    json_reporter.generate_and_save(result, "reports/ci_analysis.json")

    # Critical問題があればビルド失敗
    if result.critical_count > 0:
        print(f"❌ Critical問題が{result.critical_count}件検出されました")
        for issue in result.get_critical_issues():
            print(f"  {issue.file_path}:{issue.line_number} - {issue.message}")
        sys.exit(1)

    # High問題があれば警告
    if result.high_count > 0:
        print(f"⚠️ High問題が{result.high_count}件検出されました")
        # 警告として扱い、ビルドは継続

    print(f"✅ 分析完了: {result.total_files}ファイル, {result.total_issues}問題")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### ユースケース2: コードレビュー支援

```python
#!/usr/bin/env python3
"""
Pull Request用分析スクリプト
"""
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import MarkdownReporter

def analyze_pr_changes(changed_files):
    """変更されたファイルのみを分析"""
    analyzer = CassandraAnalyzer()

    # Javaファイルのみフィルタ
    java_files = [f for f in changed_files if f.endswith('.java')]

    if not java_files:
        print("✅ Java DAOファイルの変更なし")
        return

    # 変更されたファイルを分析
    result = analyzer.analyze_files(java_files)

    # Markdownレポート生成（PRコメント用）
    md_reporter = MarkdownReporter()
    report = md_reporter.generate(result)

    # レポートをファイルに保存
    with open("pr_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📝 PR分析レポートを生成しました: pr_analysis.md")
    print(f"   {result.total_issues}個の問題を検出")

if __name__ == "__main__":
    # 例: gitで変更されたファイルリストを取得
    # git diff --name-only origin/main...HEAD
    changed_files = [
        "src/main/java/com/example/dao/UserDao.java",
        "src/main/java/com/example/dao/OrderDao.java",
    ]

    analyze_pr_changes(changed_files)
```

### ユースケース3: 定期的なコード品質チェック

```python
#!/usr/bin/env python3
"""
週次品質レポート生成スクリプト
"""
from datetime import datetime
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import HTMLReporter, JSONReporter

def generate_weekly_report():
    """週次レポートを生成"""
    # タイムスタンプ
    timestamp = datetime.now().strftime("%Y-%m-%d")

    # 全DAOファイルを分析
    analyzer = CassandraAnalyzer()
    result = analyzer.analyze_directory("src/main/java/com/example/dao")

    # HTMLレポート（閲覧用）
    html_reporter = HTMLReporter(config={
        "title": f"Weekly Code Quality Report - {timestamp}"
    })
    html_reporter.generate_and_save(
        result,
        f"reports/weekly/report_{timestamp}.html"
    )

    # JSONレポート（トレンド分析用）
    json_reporter = JSONReporter()
    json_reporter.generate_and_save(
        result,
        f"reports/weekly/report_{timestamp}.json"
    )

    # サマリーを出力
    print(f"📊 週次レポート生成完了 ({timestamp})")
    print(f"  分析ファイル数: {result.total_files}")
    print(f"  検出問題数: {result.total_issues}")
    print(f"    🔴 Critical: {result.critical_count}")
    print(f"    🟠 High: {result.high_count}")
    print(f"    🟡 Medium: {result.medium_count}")
    print(f"    🔵 Low: {result.low_count}")
    print(f"  分析時間: {result.analysis_time:.2f}秒")

if __name__ == "__main__":
    generate_weekly_report()
```

### ユースケース4: 問題のフィルタリングと詳細表示

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# 分析実行
analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# ALLOW FILTERING問題のみ抽出
allow_filtering_issues = [
    issue for issue in result.issues
    if issue.issue_type == "ALLOW_FILTERING"
]

print(f"ALLOW FILTERING問題: {len(allow_filtering_issues)}件")
for issue in allow_filtering_issues:
    print(f"\n📍 {issue.file_path}:{issue.line_number}")
    print(f"   CQL: {issue.cql_text}")
    print(f"   推奨: {issue.recommendation}")
    print(f"   信頼度: {issue.confidence * 100:.0f}%")
```

### ユースケース5: 結果のカスタム処理

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
import json

# 分析実行
analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./dao")

# カスタムフォーマットでデータを処理
custom_report = {
    "scan_date": result.timestamp,
    "summary": {
        "files": result.total_files,
        "issues": result.total_issues,
        "critical_files": len([
            f for f, issues in result.get_issues_by_file().items()
            if any(i.severity == "critical" for i in issues)
        ])
    },
    "top_issues": [
        {
            "file": issue.file_path,
            "line": issue.line_number,
            "type": issue.issue_type,
            "severity": issue.severity,
        }
        for issue in sorted(
            result.issues,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.severity]
        )[:10]  # Top 10問題
    ]
}

# Slackやチャットツールに送信するためのフォーマット
print(json.dumps(custom_report, indent=2, ensure_ascii=False))
```

## トラブルシューティング

### 問題: ファイルが見つからない

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from pathlib import Path

file_path = "path/to/file.java"

# ファイルの存在確認
if not Path(file_path).exists():
    print(f"❌ ファイルが見つかりません: {file_path}")
    exit(1)

analyzer = CassandraAnalyzer()
result = analyzer.analyze_file(file_path)
```

### 問題: 問題が検出されない

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

analyzer = CassandraAnalyzer()
result = analyzer.analyze_file("dao/UserDao.java")

if result.total_issues == 0:
    print("✅ 問題は検出されませんでした")
    print(f"   分析ファイル数: {result.total_files}")
    print(f"   有効な検出器: {len(analyzer.detectors)}")
    print(f"   検出器リスト: {[d.__class__.__name__ for d in analyzer.detectors]}")
else:
    print(f"⚠️ {result.total_issues}個の問題を検出")
```

### 問題: 特定の検出器が動作しない

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer

# デバッグ用設定
config = {
    "detectors": ["allow_filtering"]  # 1つずつテスト
}

analyzer = CassandraAnalyzer(config=config)
result = analyzer.analyze_file("dao/UserDao.java")

print(f"検出器数: {len(analyzer.detectors)}")
print(f"検出問題数: {result.total_issues}")

# 各検出器の詳細
for detector in analyzer.detectors:
    print(f"  - {detector.__class__.__name__}: 有効={detector.is_enabled()}")
```

### 問題: パフォーマンスが遅い

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
import time

# 大量のファイルを分析する場合
start = time.time()

analyzer = CassandraAnalyzer()
result = analyzer.analyze_directory("./large_project")

elapsed = time.time() - start

print(f"分析時間: {elapsed:.2f}秒")
print(f"ファイル数: {result.total_files}")
print(f"平均: {elapsed / result.total_files:.3f}秒/ファイル")

# 遅い場合は検出器を減らすことを検討
config = {
    "detectors": ["allow_filtering", "partition_key"]  # 最重要のみ
}
```

### 問題: レポートの文字化け

```python
from cassandra_analyzer.reporters import JSONReporter

# UTF-8エンコーディングを明示
json_reporter = JSONReporter(config={
    "ensure_ascii": False  # 日本語をそのまま出力
})

report = json_reporter.generate(result)

# ファイル保存時もUTF-8を指定
with open("report.json", "w", encoding="utf-8") as f:
    f.write(report)
```

## ヘルプとサポート

詳細な情報は以下を参照してください：

- [README.md](README.md) - プロジェクト概要
- [DEVELOPMENT.md](DEVELOPMENT.md) - 開発者向けガイド
- [Issue Tracker](https://github.com/your-org/cassandra-analyzer/issues) - バグ報告・質問

---

このガイドで不明な点があれば、お気軽にIssueを作成してください。
