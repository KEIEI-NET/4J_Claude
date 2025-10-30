# Elasticsearch使用ガイド

**バージョン**: v1.0.0
**最終更新**: 2025年01月27日

## 目次

1. [概要](#概要)
2. [セットアップ](#セットアップ)
3. [基本的な使い方](#基本的な使い方)
4. [検出器の詳細](#検出器の詳細)
5. [設定オプション](#設定オプション)
6. [レポート生成](#レポート生成)
7. [トラブルシューティング](#トラブルシューティング)
8. [ベストプラクティス](#ベストプラクティス)

## 概要

Elasticsearch Analyzerは、Javaコードベース内のElasticsearchクエリを静的解析し、パフォーマンス問題、セキュリティリスク、ベストプラクティス違反を検出するツールです。

### 主な機能

- **ワイルドカード検出**: 先頭ワイルドカードの使用を検出
- **N+1クエリ検出**: ループ内でのクエリ実行を検出
- **大きなサイズ検出**: 過度に大きい検索サイズを検出
- **ソート最適化**: 非効率なソート処理を検出
- **スクリプトスコアリング**: パフォーマンスに影響するスクリプト使用を検出
- **フルテーブルスキャン**: インデックスなしの検索を検出
- **接続プール管理**: 不適切な接続設定を検出
- **ディープページング**: メモリを消費する深いページングを検出

## セットアップ

### 前提条件

- Python 3.11以上
- pip (パッケージマネージャー)
- 分析対象のJavaコードベース

### インストール

```bash
# プロジェクトルートに移動
cd "C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_multidb"

# 仮想環境を作成（推奨）
python -m venv venv
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

### 環境変数の設定

`.env`ファイルをプロジェクトルートに作成：

```env
# Anthropic API Key (LLM機能を使用する場合)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# ログレベル（オプション）
LOG_LEVEL=INFO
```

## 基本的な使い方

### コマンドライン実行

```bash
# 基本的な分析
python -m multidb_analyzer analyze /path/to/java/project

# 特定のディレクトリのみ分析
python -m multidb_analyzer analyze /path/to/java/project/src

# 設定ファイルを使用
python -m multidb_analyzer analyze /path/to/java/project --config config.yaml
```

### Pythonコードからの使用

```python
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    NPlusOneDetector,
    LargeSizeDetector
)
from multidb_analyzer.elasticsearch.parsers import JavaElasticsearchParser
from multidb_analyzer.core.base_detector import AnalysisContext

# パーサーを初期化
parser = JavaElasticsearchParser()

# Javaファイルを解析
with open('SearchService.java', 'r', encoding='utf-8') as f:
    code = f.read()

queries = parser.parse_file('SearchService.java', code)

# 検出器を実行
context = AnalysisContext(
    file_path='SearchService.java',
    code_content=code
)

detector = WildcardDetector()
issues = detector.detect(queries, context)

# 結果を表示
for issue in issues:
    print(f"{issue.severity.value}: {issue.title}")
    print(f"  Location: {issue.file_path}:{issue.line_number}")
    print(f"  Suggestion: {issue.suggestion}")
```

## 検出器の詳細

### 1. WildcardDetector

**目的**: 先頭ワイルドカードの使用を検出

**検出パターン**:
```java
// ❌ 検出される（パフォーマンス問題）
wildcardQuery("field", "*value")
wildcardQuery("field", "?value")

// ✅ OK
wildcardQuery("field", "value*")
prefixQuery("field", "value")
```

**重大度**: CRITICAL

**推奨される修正**:
- `prefixQuery()`を使用
- `matchQuery()`を検討
- フルテキスト検索の実装

### 2. NPlusOneDetector

**目的**: ループ内でのクエリ実行を検出

**検出パターン**:
```java
// ❌ 検出される（N+1問題）
for (String id : ids) {
    client.search(request);  // ループ内でクエリ実行
}

// ✅ 推奨される方法
SearchRequest request = new SearchRequest()
    .source(new SearchSourceBuilder()
        .query(QueryBuilders.termsQuery("id", ids)));  // バッチクエリ
client.search(request);
```

**重大度**: HIGH

**推奨される修正**:
- `termsQuery()`でバッチ検索
- `multiSearch()`を使用
- 結果をキャッシュ

### 3. LargeSizeDetector

**目的**: 過度に大きい検索サイズを検出

**検出パターン**:
```java
// ❌ 検出される（メモリ問題）
searchSourceBuilder.size(10000);  // 閾値: 1000

// ✅ 推奨される方法
searchSourceBuilder
    .size(100)
    .searchAfter(lastHit.getSortValues());  // Scroll API使用
```

**重大度**: MEDIUM

**推奨される修正**:
- Scroll APIを使用
- Search Afterを使用
- ページングサイズを削減

### 4. SortOptimizationDetector

**目的**: 非効率なソート処理を検出

**検出パターン**:
```java
// ❌ 検出される（パフォーマンス問題）
searchSourceBuilder.sort("_score")
    .sort(new FieldSortBuilder("date").order(SortOrder.DESC));

// ✅ 推奨される方法
searchSourceBuilder
    .sort(new FieldSortBuilder("date").order(SortOrder.DESC))
    .trackScores(false);  // スコア計算不要
```

**重大度**: MEDIUM

**推奨される修正**:
- 不要なスコア計算を無効化
- ソートフィールドをインデックス化
- doc_valuesを使用

### 5. ScriptScoringDetector

**目的**: パフォーマンスに影響するスクリプト使用を検出

**検出パターン**:
```java
// ❌ 検出される（高コスト）
ScriptScoreQueryBuilder scriptScore = QueryBuilders.scriptScoreQuery(
    boolQuery,
    new Script("Math.log(2 + doc['likes'].value)")
);

// ✅ 代替案
FunctionScoreQueryBuilder functionScore = QueryBuilders.functionScoreQuery(
    boolQuery,
    ScoreFunctionBuilders.fieldValueFactorFunction("likes")
        .modifier(FieldValueFactorFunction.Modifier.LOG1P)
);
```

**重大度**: HIGH

**推奨される修正**:
- Function Score Queryを使用
- 事前計算したフィールドを使用
- Painlessスクリプトを最適化

### 6. FullTableScanDetector

**目的**: インデックスなしの検索を検出

**検出パターン**:
```java
// ❌ 検出される（全体スキャン）
searchSourceBuilder.query(QueryBuilders.matchAllQuery());

// ✅ 推奨される方法
searchSourceBuilder.query(QueryBuilders.termQuery("status", "active"));
```

**重大度**: CRITICAL

**推奨される修正**:
- 適切なフィルタ条件を追加
- インデックスを作成
- クエリを最適化

### 7. ConnectionPoolDetector

**目的**: 不適切な接続設定を検出

**検出パターン**:
```java
// ❌ 検出される（接続プール不足）
RestClientBuilder.setMaxConnPerRoute(5);  // 閾値: 10

// ✅ 推奨される設定
RestClientBuilder.setMaxConnPerRoute(20)
    .setMaxConnTotal(50);
```

**重大度**: MEDIUM

**推奨される修正**:
- 適切な接続プールサイズ
- タイムアウト設定
- リトライポリシー

### 8. DeepPagingDetector

**目的**: メモリを消費する深いページングを検出

**検出パターン**:
```java
// ❌ 検出される（メモリ消費）
searchSourceBuilder.from(5000).size(100);  // 閾値: 1000

// ✅ 推奨される方法
searchSourceBuilder
    .searchAfter(previousPageLastHit.getSortValues())
    .size(100);
```

**重大度**: HIGH

**推奨される修正**:
- Search After APIを使用
- Scroll APIを使用
- ページング深度を制限

## 設定オプション

### 設定ファイル（config.yaml）

```yaml
# 検出器の設定
elasticsearch:
  detectors:
    wildcard:
      enabled: true
      severity: CRITICAL

    n_plus_one:
      enabled: true
      severity: HIGH
      loop_threshold: 5

    large_size:
      enabled: true
      size_threshold: 1000
      severity: MEDIUM

    sort_optimization:
      enabled: true
      severity: MEDIUM

    script_scoring:
      enabled: true
      severity: HIGH

    full_table_scan:
      enabled: true
      severity: CRITICAL

    connection_pool:
      enabled: true
      min_connections: 10
      severity: MEDIUM

    deep_paging:
      enabled: true
      from_threshold: 1000
      severity: HIGH

# レポート設定
reporting:
  formats:
    - html
    - json
    - markdown
  output_dir: ./reports
  include_code_snippets: true
  max_snippet_lines: 10

# パフォーマンス設定
performance:
  max_workers: 4
  timeout: 300
  chunk_size: 100
```

### プログラムからの設定

```python
from multidb_analyzer.elasticsearch.detectors import LargeSizeDetector
from multidb_analyzer.core.base_detector import DetectorConfig

# カスタム設定
config = DetectorConfig(
    enabled=True,
    severity_override='HIGH',
    custom_params={
        'size_threshold': 500  # デフォルト1000から変更
    }
)

detector = LargeSizeDetector(config=config)
```

## レポート生成

### HTMLレポート

```bash
# HTML形式でレポート生成
python -m multidb_analyzer analyze /path/to/project --format html --output ./reports

# ブラウザで開く
start ./reports/analysis_report.html
```

### JSONレポート

```bash
# JSON形式でレポート生成（CI/CD統合向け）
python -m multidb_analyzer analyze /path/to/project --format json --output ./reports/report.json
```

### Markdownレポート

```bash
# Markdown形式でレポート生成
python -m multidb_analyzer analyze /path/to/project --format markdown --output ./reports/REPORT.md
```

### レポートのカスタマイズ

```python
from multidb_analyzer.reporters import HTMLReporter, ReportConfig

config = ReportConfig(
    title="Elasticsearch Analysis Report",
    include_statistics=True,
    include_code_snippets=True,
    max_snippet_lines=15,
    group_by='severity'  # 'file', 'detector', 'severity'
)

reporter = HTMLReporter(config=config)
reporter.generate(issues, output_path='custom_report.html')
```

## トラブルシューティング

### よくある問題と解決策

#### 問題1: パースエラー

**症状**:
```
ERROR: Failed to parse file: SearchService.java
```

**原因**:
- Javaファイルの構文エラー
- サポートされていないJava構文

**解決策**:
```bash
# ファイルを個別にチェック
python -m multidb_analyzer validate SearchService.java

# ログレベルを上げて詳細を確認
LOG_LEVEL=DEBUG python -m multidb_analyzer analyze /path/to/project
```

#### 問題2: メモリ不足

**症状**:
```
MemoryError: Unable to allocate array
```

**原因**:
- 大規模なコードベース
- 同時処理数が多すぎる

**解決策**:
```yaml
# config.yamlで調整
performance:
  max_workers: 2  # デフォルト4から削減
  chunk_size: 50  # デフォルト100から削減
```

#### 問題3: 誤検知

**症状**:
- 正しいコードが問題として報告される

**解決策**:
```python
# コード内でサプレス
# @analyzer-ignore: wildcard
wildcardQuery("field", "*value")  # 正当な理由がある場合

# または設定で無効化
config.yaml:
  detectors:
    wildcard:
      enabled: false
```

## ベストプラクティス

### 1. 定期的な分析

```bash
# CI/CDパイプラインに統合
# .github/workflows/analysis.yml
name: Code Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Elasticsearch Analyzer
        run: |
          python -m multidb_analyzer analyze ./src --format json
          # 結果を確認してビルド失敗判定
```

### 2. 段階的な修正

```python
# 重大度順に修正
1. CRITICAL問題を最優先
2. HIGH問題を次に
3. MEDIUM/LOW問題は計画的に

# 修正の優先順位
- パフォーマンスに直接影響する問題
- セキュリティリスク
- 保守性の問題
```

### 3. チーム教育

```markdown
1. ドキュメントを共有
2. コードレビューで指摘
3. ベストプラクティスを確立
4. 定期的な勉強会
```

### 4. カスタムルール

```python
# プロジェクト固有のルールを追加
from multidb_analyzer.core.base_detector import BaseDetector

class CustomDetector(BaseDetector):
    def detect(self, queries, context):
        # カスタムロジック
        pass
```

## 参考リソース

- [Elasticsearch公式ドキュメント](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Java High Level REST Client](https://www.elastic.co/guide/en/elasticsearch/client/java-rest/current/java-rest-high.html)
- [Elasticsearch Performance Tuning](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)

---

**次のステップ**: [API_REFERENCE.md](./API_REFERENCE.md)で詳細なAPI仕様を確認してください。
