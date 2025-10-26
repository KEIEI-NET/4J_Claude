# Cassandra Analyzer 使用ガイド

## 概要

Cassandra Analyzerは、JavaコードからCassandraアンチパターンを検出する静的解析ツールです。Phase 2では、LLM統合、ASTパーサー、評価フレームワークなどの高度な機能が追加されました。

## インストール

```bash
# プロジェクトのクローン
git clone <repository-url>
cd cassandra-analyzer

# 依存関係のインストール
pip install -e .

# 必要なパッケージ
# - anthropic (LLM機能を使用する場合)
# - javalang (ASTパーサーを使用する場合)
# - pyyaml (YAML設定ファイルを使用する場合)
```

## コマンドラインインターフェース（CLI）

### 基本的な使用方法

#### 単一ファイルの分析

```bash
# デフォルト設定で分析
cassandra-analyzer analyze UserDao.java

# JSON + Markdown形式でレポート生成
cassandra-analyzer analyze --format json markdown UserDao.java

# カスタム出力ディレクトリ
cassandra-analyzer analyze --output reports/ UserDao.java
```

#### ディレクトリの分析

```bash
# ディレクトリ全体を分析
cassandra-analyzer analyze src/main/java/dao

# カスタムファイルパターン
cassandra-analyzer analyze --pattern "**/*Dao.java" src/

# 詳細出力
cassandra-analyzer analyze --verbose src/
```

#### 設定ファイルの使用

```bash
# 設定ファイルを使用して分析
cassandra-analyzer analyze --config config.yaml src/

# HTML形式でレポート生成
cassandra-analyzer analyze --config config.yaml --format html src/
```

### 設定管理

#### 設定ファイルの初期化

```bash
# デフォルト設定ファイルを生成（YAML）
cassandra-analyzer config --init

# JSON形式で生成
cassandra-analyzer config --init --output config.json

# 既存ファイルを上書き
cassandra-analyzer config --init --force
```

#### 設定ファイルの検証

```bash
# 設定ファイルの妥当性をチェック
cassandra-analyzer config --validate --config my-config.yaml
```

#### 設定の表示

```bash
# デフォルト設定を表示
cassandra-analyzer config --show

# 既存の設定ファイルを表示
cassandra-analyzer config --show --config my-config.yaml
```

## 設定ファイル

### 基本設定（config.yaml）

```yaml
# パーサー設定
parser:
  type: regex  # "regex" または "ast"
  resolve_constants: true  # 定数解決を有効化

# 有効な検出器
detectors:
  - allow_filtering
  - partition_key
  - batch_size
  - prepared_statement

# 検出器ごとの設定
detector_configs:
  allow_filtering:
    enabled: true
    severity: high
    llm_enabled: false  # LLM強化機能（API keyが必要）

  partition_key:
    enabled: true
    severity: critical
    llm_enabled: false  # LLMによるスキーマ推論

  batch_size:
    enabled: true
    severity: medium
    max_batch_size: 100  # バッチサイズの閾値

  prepared_statement:
    enabled: true
    severity: medium

# 出力設定
output:
  formats:
    - json
    - markdown
  directory: reports
  detailed: true
```

### LLM機能を有効化

```yaml
# LLM設定（オプション）
llm:
  anthropic_api_key: your-api-key-here
  model: claude-3-5-sonnet-20241022
  max_retries: 3
  retry_delay: 1.0

# スマート検出器を有効化
detector_configs:
  allow_filtering:
    llm_enabled: true  # コンテキストを理解した誤検出削減

  partition_key:
    llm_enabled: true  # スキーマ推論とMV提案
```

### ASTパーサーの使用

```yaml
parser:
  type: ast  # より正確な解析
  resolve_constants: true
```

## Pythonライブラリとして使用

### 基本的な使用方法

```python
from cassandra_analyzer import CassandraAnalyzer

# アナライザーの初期化
analyzer = CassandraAnalyzer()

# 単一ファイルの分析
result = analyzer.analyze_file("UserDao.java")

# ディレクトリの分析
result = analyzer.analyze_directory("src/main/java/dao", pattern="**/*.java")

# 結果の表示
print(f"Total issues: {result.total_issues}")
for issue in result.issues:
    print(f"{issue.severity}: {issue.message} at {issue.file}:{issue.line}")
```

### 設定付き初期化

```python
# カスタム設定
config = {
    "parser": {"type": "ast"},
    "detectors": ["allow_filtering", "partition_key"],
    "detector_configs": {
        "allow_filtering": {
            "severity": "high",
            "llm_enabled": False
        }
    }
}

analyzer = CassandraAnalyzer(config=config)
result = analyzer.analyze_file("UserDao.java")
```

### レポート生成

```python
from cassandra_analyzer.reporters import JSONReporter, MarkdownReporter

analyzer = CassandraAnalyzer()
result = analyzer.analyze_file("UserDao.java")

# JSON形式で保存
json_reporter = JSONReporter()
json_reporter.generate_and_save(result, "report.json")

# Markdown形式で保存
md_reporter = MarkdownReporter()
md_reporter.generate_and_save(result, "report.md")
```

## 評価フレームワーク

### 評価データの準備

アノテーションファイル（JSON形式）:

```json
{
  "file_path": "tests/fixtures/sample_dao_bad1.java",
  "ground_truth_issues": [
    {
      "issue_type": "ALLOW_FILTERING",
      "line_number": 28,
      "severity": "high",
      "description": "SELECT query uses ALLOW FILTERING"
    }
  ],
  "metadata": {
    "annotator": "reviewer",
    "date": "2025-01-26"
  }
}
```

### 評価の実行

```bash
# 評価スクリプトの実行
python scripts/evaluate.py \
  --annotations tests/evaluation_data/ \
  --config config.yaml \
  --output evaluation_report.json \
  --detailed

# トレランス調整（行番号の許容範囲）
python scripts/evaluate.py \
  --annotations tests/evaluation_data/ \
  --tolerance 5
```

### Pythonから評価

```python
from cassandra_analyzer.evaluation import Evaluator, EvaluationDataset

# データセットの読み込み
dataset = EvaluationDataset.load_from_directory("tests/evaluation_data/")

# 分析の実行
analyzer = CassandraAnalyzer()
detected_issues = {}
for annotated_file in dataset.annotated_files:
    result = analyzer.analyze_file(annotated_file.file_path)
    detected_issues[annotated_file.file_path] = result.issues

# 評価
evaluator = Evaluator(tolerance=2)
eval_result = evaluator.evaluate_dataset(detected_issues, dataset)

# 結果の表示
print(f"Precision: {eval_result.precision:.2%}")
print(f"Recall: {eval_result.recall:.2%}")
print(f"F1 Score: {eval_result.f1_score:.2%}")
```

## 検出されるアンチパターン

### 1. ALLOW FILTERING

**問題**: フルテーブルスキャンによる性能問題

**検出例**:
```java
session.execute("SELECT * FROM users WHERE email = ? ALLOW FILTERING");
```

**推奨対策**:
- マテリアライズドビューの作成
- セカンダリインデックスの使用（慎重に）
- データモデルの再設計

### 2. パーティションキー未使用

**問題**: クエリにパーティションキーが含まれていない

**検出例**:
```java
session.execute("SELECT * FROM users WHERE name = ?");
```

**推奨対策**:
- パーティションキーを含むクエリに変更
- マテリアライズドビューの作成

### 3. 大量バッチ処理

**問題**: 大きすぎるバッチサイズ

**検出例**:
```java
BatchStatement batch = new BatchStatement();
for (int i = 0; i < 500; i++) {
    batch.add(...);
}
```

**推奨対策**:
- バッチサイズを100以下に制限
- 非同期処理の使用

### 4. Prepared Statement未使用

**問題**: パフォーマンスとセキュリティリスク

**検出例**:
```java
session.execute("SELECT * FROM users WHERE id = '" + userId + "'");
```

**推奨対策**:
```java
PreparedStatement ps = session.prepare("SELECT * FROM users WHERE id = ?");
BoundStatement bs = ps.bind(userId);
session.execute(bs);
```

## LLM強化機能

### LLM機能の有効化

```bash
# 環境変数でAPI Keyを設定
export ANTHROPIC_API_KEY=your-api-key-here

# LLM有効化設定で実行
cassandra-analyzer analyze --config llm-config.yaml src/
```

### スマート検出器の機能

1. **SmartAllowFilteringDetector**
   - ALLOW FILTERINGの妥当性を判断
   - 小規模テーブルや限定的なクエリでは警告を抑制
   - より詳細な推奨事項を生成

2. **SmartPartitionKeyDetector**
   - テーブルスキーマを推論
   - マテリアライズドビューの提案
   - データモデル改善の具体的なアドバイス

## トラブルシューティング

### PyYAMLが見つからない

```bash
pip install pyyaml
```

### javalangが見つからない

```bash
pip install javalang
```

### LLM機能のエラー

```bash
# API Keyが設定されているか確認
echo $ANTHROPIC_API_KEY

# 設定ファイルでLLMが有効化されているか確認
cassandra-analyzer config --show --config config.yaml
```

### 分析が遅い

```yaml
# ASTパーサーをRegexパーサーに変更
parser:
  type: regex

# LLM機能を無効化
detector_configs:
  allow_filtering:
    llm_enabled: false
```

## パフォーマンス

### ベンチマーク結果

- **単一ファイル**: < 1秒
- **100ファイル**: ~1秒（LLMなし）
- **LLM分析**: 設定により可変（キャッシング推奨）

### 最適化のヒント

1. **小規模プロジェクト**: デフォルト設定で十分
2. **大規模プロジェクト**: Regexパーサー + LLMなし
3. **高精度が必要**: ASTパーサー + LLM有効化

## サポート

- **ドキュメント**: README.md, PHASE2_PLAN.md, PHASE2_COMPLETION.md
- **サンプル設定**: config.example.yaml
- **テストケース**: tests/ ディレクトリ
- **評価データ**: tests/evaluation_data/

## バージョン情報

- **Version**: 2.0.0
- **Python**: >=3.11
- **主要依存**: anthropic, javalang, pyyaml

## ライセンス

MIT License
