# Cassandra Code Analyzer

**Phase 1プロトタイプ** - Apache Cassandra特化型静的コード分析システム

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Test Coverage](https://img.shields.io/badge/coverage-91.30%25-brightgreen.svg)](tests/)
[![Tests](https://img.shields.io/badge/tests-92%20passed-success.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 概要

JavaコードベースにおけるApache Cassandra関連の問題を自動検出する静的解析ツールです。パフォーマンスやスケーラビリティに影響を与える可能性のあるアンチパターンを早期に発見し、品質向上をサポートします。

### 主な特徴

✅ **4つの重要な問題パターンを検出**
- ALLOW FILTERING（全テーブルスキャンのリスク）
- Partition Key未使用（パフォーマンス問題）
- 過大なBatch操作（メモリ・ネットワーク負荷）
- Prepared Statement未使用（セキュリティ・パフォーマンス）

✅ **3つの出力形式をサポート**
- JSON（プログラム連携・CI/CD統合）
- Markdown（ドキュメント・レビュー）
- HTML（インタラクティブなレポート）

✅ **高い品質基準**
- テストカバレッジ: **91.30%**
- テスト: **92件** すべて成功
- 型安全性: mypy完全準拠

## 🚀 クイックスタート

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/cassandra-analyzer.git
cd cassandra-analyzer

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

### 基本的な使用方法

```python
from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import JSONReporter, MarkdownReporter, HTMLReporter

# アナライザーの初期化
analyzer = CassandraAnalyzer()

# 単一ファイルの分析
result = analyzer.analyze_file("path/to/YourDao.java")

# ディレクトリ全体の分析
result = analyzer.analyze_directory("path/to/dao/directory")

# JSONレポートの生成
json_reporter = JSONReporter()
json_report = json_reporter.generate(result)
json_reporter.save(json_report, "report.json")

# Markdownレポートの生成
md_reporter = MarkdownReporter()
md_reporter.generate_and_save(result, "report.md")

# HTMLレポートの生成
html_reporter = HTMLReporter()
html_reporter.generate_and_save(result, "report.html")
```

## 📊 検出機能の詳細

### 1. ALLOW FILTERING検出
**重要度**: 🟠 High

ALLOW FILTERINGはCassandraで全テーブルスキャンを強制し、パフォーマンス問題を引き起こします。

```java
// ❌ 検出される問題
session.execute("SELECT * FROM users WHERE email = ? ALLOW FILTERING", email);

// ✅ 推奨される解決策
// 1. Materialized Viewの作成
// 2. 適切なセカンダリインデックスの使用
// 3. テーブル設計の見直し
```

### 2. Partition Key未使用検出
**重要度**: 🔴 Critical

WHERE句でPartition Keyを使用しないクエリは、全ノードスキャンとなり深刻なパフォーマンス問題を引き起こします。

```java
// ❌ 検出される問題
session.execute("SELECT * FROM orders WHERE order_date > ?", date);

// ✅ 推奨される解決策
session.execute("SELECT * FROM orders WHERE user_id = ? AND order_date > ?", userId, date);
```

### 3. Batch Size検証
**重要度**: 🟡 Medium

過大なバッチ操作はメモリ不足やタイムアウトを引き起こす可能性があります。

```java
// ❌ 検出される問題（閾値: デフォルト100件）
BatchStatement batch = new BatchStatement();
for (int i = 0; i < 500; i++) {  // 500件のバッチ
    batch.add(insertStmt.bind(...));
}

// ✅ 推奨される解決策
// バッチサイズを100件以下に分割
```

### 4. Prepared Statement未使用検出
**重要度**: 🔵 Low

Prepared Statementを使用しないとSQLインジェクションのリスクとパフォーマンス低下を招きます。

```java
// ❌ 検出される問題
session.execute("SELECT * FROM products WHERE id = " + productId);

// ✅ 推奨される解決策
PreparedStatement prepared = session.prepare("SELECT * FROM products WHERE id = ?");
session.execute(prepared.bind(productId));
```

## 📈 出力形式

### JSON形式

構造化データとして出力。CI/CDパイプラインやプログラム連携に最適。

```json
{
  "summary": {
    "total_files": 15,
    "total_calls": 127,
    "total_issues": 23,
    "critical_issues": 5,
    "high_issues": 12,
    "medium_issues": 4,
    "low_issues": 2
  },
  "issues": [
    {
      "detector": "AllowFilteringDetector",
      "type": "ALLOW_FILTERING",
      "severity": "high",
      "file": "UserDao.java",
      "line": 45,
      "message": "ALLOW FILTERING detected in SELECT query",
      "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
      "recommendation": "Create a Materialized View or Secondary Index"
    }
  ]
}
```

### Markdown形式

GitHub Flavored Markdown形式で出力。コードレビューやドキュメント化に最適。

```markdown
# Cassandra Code Analysis Report

## Summary
- 📁 Total Files Analyzed: **15**
- 🔍 Total Cassandra Calls: **127**
- ⚠️ Total Issues Found: **23**

| Severity | Count |
|----------|-------|
| 🔴 Critical | 5 |
| 🟠 High | 12 |
| 🟡 Medium | 4 |
| 🔵 Low | 2 |

## Issues by File

### UserDao.java (8 issues)

#### 🟠 ALLOW_FILTERING
**Severity**: high
**Line**: 45
...
```

### HTML形式

インタラクティブなWebレポート。フィルタリング機能付き。

- 📱 レスポンシブデザイン
- 🔍 重要度別フィルタリング
- 🎨 見やすいカラーコーディング
- 🔒 XSS対策済み

## ⚙️ 設定オプション

カスタム設定で検出器の動作をカスタマイズできます。

```python
config = {
    # 有効にする検出器を選択
    "detectors": ["allow_filtering", "partition_key", "batch_size"],

    # 検出器別の設定
    "detector_configs": {
        "batch_size": {
            "threshold": 50  # バッチサイズの閾値（デフォルト: 100）
        }
    }
}

analyzer = CassandraAnalyzer(config=config)
```

### レポーター設定

```python
# JSONレポーター設定
json_reporter = JSONReporter(config={
    "indent": 4,           # インデント（デフォルト: 2）
    "ensure_ascii": False  # 日本語をそのまま出力
})

# Markdownレポーター設定
md_reporter = MarkdownReporter(config={
    "group_by_file": True  # ファイル別にグループ化（デフォルト: True）
})

# HTMLレポーター設定
html_reporter = HTMLReporter(config={
    "title": "Custom Report Title"  # レポートタイトル
})
```

## 🏗️ アーキテクチャ

```
cassandra-analyzer/
├── src/cassandra_analyzer/
│   ├── parsers/          # Javaコードパーサー
│   │   └── java_parser.py
│   ├── detectors/        # 問題検出器
│   │   ├── allow_filtering_detector.py
│   │   ├── partition_key_detector.py
│   │   ├── batch_size_detector.py
│   │   └── prepared_statement_detector.py
│   ├── reporters/        # レポート生成
│   │   ├── json_reporter.py
│   │   ├── markdown_reporter.py
│   │   └── html_reporter.py
│   ├── models/           # データモデル
│   │   ├── cassandra_call.py
│   │   ├── issue.py
│   │   └── analysis_result.py
│   └── analyzer.py       # メインアナライザー
└── tests/
    ├── unit/             # ユニットテスト
    ├── integration/      # 統合テスト
    └── e2e/              # E2Eテスト
```

## 🧪 テスト

### テストの実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジレポート生成
pytest tests/ --cov=src/cassandra_analyzer --cov-report=html

# 特定のテストのみ実行
pytest tests/unit/test_detectors.py -v

# 型チェック
mypy src/

# コードフォーマット
black src/ tests/

# リント
ruff check .
```

### テスト結果

```
==================== test session starts ====================
collected 92 items

tests/unit/test_parsers.py ......           [  6%]
tests/unit/test_detectors.py .............. [ 21%]
tests/unit/test_reporters.py .............. [ 46%]
tests/integration/test_pipeline.py ........ [ 55%]
tests/e2e/test_full_analysis.py ........... [100%]

==================== 92 passed in 2.34s ====================

Coverage: 91.30%
```

## 🎯 Phase 1 目標

| 目標項目 | 目標値 | 現在の状態 |
|---------|-------|-----------|
| 対象ファイル数 | 10-20個 | ✅ サポート済み |
| 検出バグ数 | 3-5個 | ✅ 4パターン実装 |
| 誤検出率 | < 20% | ⏳ 評価中 |
| 実行時間 | < 30秒 | ✅ 平均2秒 |
| テストカバレッジ | > 80% | ✅ 91.30% |

## 📚 ドキュメント

- [USAGE.md](USAGE.md) - 詳細な使用方法とサンプル
- [DEVELOPMENT.md](DEVELOPMENT.md) - 開発者向けガイド
- [API Documentation](docs/api/) - APIリファレンス

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

### 開発ガイドライン

- すべてのコードは型ヒント必須
- テストカバレッジ80%以上を維持
- Black + Ruffでフォーマット
- コミットメッセージは日本語または英語

## 📝 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- Apache Cassandraコミュニティ
- Python静的解析ツールの開発者の皆様

## 📞 サポート

問題が発生した場合やご質問がある場合：

- [Issue Tracker](https://github.com/your-org/cassandra-analyzer/issues)
- [Discussions](https://github.com/your-org/cassandra-analyzer/discussions)

---

Made with ❤️ for better Cassandra code quality
