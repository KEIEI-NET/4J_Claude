# Multi-Database Code Analyzer

**バージョン**: 1.0.0
**Phase**: 6 - Multi-Database Support
**ステータス**: ✅ Week 1-2 Elasticsearch完成 + LLM統合 + ドキュメント完備

---

## 📖 概要

Multi-Database Code Analyzerは、複数のデータベースに対する静的コード分析ツールです。アンチパターン、パフォーマンス問題、セキュリティ脆弱性を検出し、具体的な修正提案を提供します。

### サポートデータベース

| DB | ステータス | 検出器数 | テスト |
|----|----------|---------|--------|
| **Elasticsearch** | ✅ 完成 | 4個 | 50ケース |
| **MySQL/PostgreSQL** | 📋 計画中 | - | - |
| **MongoDB** | 📋 計画中 | - | - |
| **Redis** | 📋 計画中 | - | - |

---

## 🚀 クイックスタート

### インストール

```bash
# プロジェクトのクローン
git clone <repository-url>
cd phase4_multidb

# 依存関係のインストール
pip install -r requirements.txt

# 開発用依存関係（テスト含む）
pip install -r requirements-dev.txt

# パッケージのインストール（開発モード）
pip install -e .
```

### 基本的な使用方法

```python
from pathlib import Path
from multidb_analyzer.core import get_plugin_manager, DatabaseType
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector,
    MappingDetector,
    ShardDetector
)

# プラグインマネージャーの取得
manager = get_plugin_manager()

# Elasticsearchプラグインの登録
manager.register_plugin(
    db_type=DatabaseType.ELASTICSEARCH,
    parser=ElasticsearchJavaParser(),
    detectors=[
        WildcardDetector(),
        ScriptQueryDetector(),
        MappingDetector(),
        ShardDetector()
    ]
)

# ファイルの解析
issues = manager.analyze_file(
    Path("src/main/java/SearchService.java"),
    DatabaseType.ELASTICSEARCH
)

# 結果の表示
for issue in issues:
    print(f"{issue.severity.value}: {issue.title}")
    print(f"  File: {issue.file_path}:{issue.line_number}")
    print(f"  Suggestion: {issue.suggestion}")
    if issue.auto_fix_available:
        print(f"  Auto-fix: {issue.auto_fix_code}")
    print()
```

---

## 🤖 LLM統合

本プロジェクトは**Claude API**を統合し、深い意味論的分析と自動最適化を提供します。

### 主な機能

- **深い意味論的理解**: コードの文脈を理解した問題分析
- **最適化提案の生成**: ベストプラクティスに基づいた具体的な修正案
- **自動修正コード生成**: 実際に適用可能なコードの生成
- **問題の優先順位付け**: ビジネス影響を考慮した順序付け
- **コスト追跡**: API使用量とコストのリアルタイム監視

### クイックスタート

```bash
# 環境変数を設定
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# または .env ファイルを作成
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
```

```python
from multidb_analyzer.llm import LLMOptimizer

# LLM Optimizerを初期化
optimizer = LLMOptimizer()

# 問題を最適化
result = optimizer.optimize_issue(
    issue=detected_issue,
    code='wildcardQuery("name", "*smith")',
    language="java"
)

print(f"Root Cause: {result.root_cause}")
print(f"Optimized Code:\n{result.optimized_code}")
print(f"Performance Impact: {result.performance_impact}")

# API使用統計
stats = optimizer.get_usage_stats()
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
```

詳細は **[LLM統合ガイド](docs/LLM_INTEGRATION.md)** を参照してください。

---

## 🔍 Elasticsearch検出器

### 1. WildcardDetector (CRITICAL)

**検出内容**: 先頭ワイルドカードの使用

```java
// ❌ CRITICAL - フルインデックススキャン
QueryBuilders.wildcardQuery("name", "*smith");

// ✅ Auto-fix提案
QueryBuilders.prefixQuery("name", "smith");
```

### 2. ScriptQueryDetector (CRITICAL)

**検出内容**: Script Queryの不適切な使用

```java
// ❌ CRITICAL - CPU使用率高
QueryBuilders.scriptQuery(
    new Script("doc['price'].value * doc['quantity'].value > 1000")
);

// ✅ 推奨
QueryBuilders.rangeQuery("total_price").gte(1000);
```

### 3. MappingDetector (MEDIUM)

**検出内容**: Dynamic Mappingへの依存

```java
// ❌ MEDIUM - 型の不一致リスク
IndexRequest request = new IndexRequest("products")
    .source(jsonMap);

// ✅ 推奨 - 明示的マッピング
PutMappingRequest mappingRequest = new PutMappingRequest("products")
    .source(
        "properties", Map.of(
            "description", Map.of("type", "text", "analyzer", "standard")
        )
    );
```

### 4. ShardDetector (HIGH)

**検出内容**: Shard設定の最適化

```java
// ❌ HIGH - 過度なシャーディング（100GBで1000シャード）
CreateIndexRequest request = new CreateIndexRequest("logs")
    .settings(Settings.builder()
        .put("index.number_of_shards", 1000)
        .put("index.number_of_replicas", 1)
    );

// ✅ 推奨（100GBの場合）
CreateIndexRequest request = new CreateIndexRequest("logs")
    .settings(Settings.builder()
        .put("index.number_of_shards", 4)      // 各25GB
        .put("index.number_of_replicas", 1)
    );
```

---

## 🧪 テスト

### テスト実行

```bash
# すべてのテストを実行
pytest

# カバレッジ付き実行
pytest --cov=src/multidb_analyzer --cov-report=html

# HTMLカバレッジレポートを開く
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### テスト統計

- **総テスト数**: 50ケース
- **パーサーテスト**: 20ケース
- **検出器テスト**: 20ケース（各検出器5ケース）
- **統合テスト**: 10ケース
- **目標カバレッジ**: 100%

---

## 📁 プロジェクト構造

```
phase4_multidb/
├── src/multidb_analyzer/
│   ├── core/                      # コアフレームワーク
│   │   ├── base_parser.py         # パーサー基底クラス
│   │   ├── base_detector.py       # 検出器基底クラス
│   │   └── plugin_manager.py      # プラグイン管理
│   └── elasticsearch/             # Elasticsearch実装
│       ├── parsers/
│       │   └── java_client_parser.py
│       ├── models/
│       │   └── es_models.py
│       └── detectors/
│           ├── wildcard_detector.py
│           ├── script_query_detector.py
│           ├── mapping_detector.py
│           └── shard_detector.py
├── tests/                         # テストスイート
│   ├── conftest.py                # 共通フィクスチャ
│   ├── test_parsers/              # パーサーテスト
│   ├── test_detectors/            # 検出器テスト
│   └── test_integration/          # 統合テスト
├── docs/                          # ドキュメント
├── requirements.txt               # 本番依存関係
├── requirements-dev.txt           # 開発依存関係
├── pyproject.toml                 # プロジェクト設定
├── pytest.ini                     # pytest設定
└── README.md                      # このファイル
```

---

## 🏗️ アーキテクチャ

### プラグインベース設計

各データベースは独立したプラグインとして実装され、コアフレームワークに登録されます。

```python
# プラグインの構成要素
class DatabasePlugin:
    db_type: DatabaseType           # データベースタイプ
    parser: BaseParser              # パーサー
    detector_registry: DetectorRegistry  # 検出器レジストリ
```

### 拡張性

新しいデータベースの追加は簡単です：

1. `BaseParser`を継承したパーサーを実装
2. `BaseDetector`を継承した検出器を実装
3. プラグインマネージャーに登録

```python
# 新しいDBの追加例
class MongoDBParser(BaseParser):
    def get_db_type(self) -> DatabaseType:
        return DatabaseType.MONGODB

    def parse_file(self, file_path: Path) -> List[ParsedQuery]:
        # MongoDB特有の解析ロジック
        pass

manager.register_plugin(
    DatabaseType.MONGODB,
    MongoDBParser(),
    [MongoDBDetector1(), MongoDBDetector2()]
)
```

---

## 📊 統計情報

### 実装統計（Elasticsearch）

| カテゴリ | ファイル数 | 行数 | 完成度 |
|---------|-----------|------|--------|
| コアフレームワーク | 4 | 860 | 100% |
| Elasticsearchパーサー | 2 | 450 | 100% |
| Elasticsearchモデル | 2 | 200 | 100% |
| Elasticsearch検出器 | 5 | 1,100 | 100% |
| テストスイート | 11 | 2,300 | 100% |
| **合計** | **24** | **4,910行** | **100%** |

### 検出能力

- **検出パターン数**: 14種類
- **重要度レベル**: CRITICAL/HIGH/MEDIUM/LOW/INFO
- **Auto-fix対応**: 1/4検出器（WildcardDetector）

---

## 🔧 開発

### コード品質

```bash
# Linting
ruff check src/ tests/

# Formatting
black src/ tests/

# Type checking
mypy src/
```

### 品質基準

- ✅ 100% 型ヒント
- ✅ 100% docstring
- ✅ 100% テストカバレッジ
- ✅ ruff エラー 0
- ✅ mypy エラー 0

---

## 📚 ドキュメント

### 🎓 ユーザーガイド

- **[Elasticsearch使用ガイド](docs/ELASTICSEARCH_GUIDE.md)** - 完全な使い方、検出器の詳細、トラブルシューティング
- **[APIリファレンス](docs/API_REFERENCE.md)** - 全クラス・メソッドの詳細仕様
- **[サンプルコード集](docs/EXAMPLES.md)** - 実践的なコード例とCI/CD統合
- **[LLM統合ガイド](docs/LLM_INTEGRATION.md)** - Claude API統合、コスト管理、ベストプラクティス

### 📋 プロジェクトドキュメント

- `PHASE6_MULTIDB_PLAN.md` - 8週間実装計画
- `DETECTOR_COMPLETION_REPORT.md` - 検出器完成レポート
- `TEST_COMPLETION_REPORT.md` - テスト完成レポート
- `WEEK1-2_COMPLETION_SUMMARY.md` - Week 1-2完成サマリー

---

## 🗓️ ロードマップ

### Phase 6 (8週間計画)

```
Week 1-2: Elasticsearch     ████████████████████ 100% ✅
Week 3-4: MySQL/PostgreSQL  ░░░░░░░░░░░░░░░░░░░░ 0%
Week 5:   MongoDB           ░░░░░░░░░░░░░░░░░░░░ 0%
Week 6:   Redis             ░░░░░░░░░░░░░░░░░░░░ 0%
Week 7:   統合機能          ░░░░░░░░░░░░░░░░░░░░ 0%
Week 8:   最終化・ドキュメント ░░░░░░░░░░░░░░░░░░░░ 0%

総進捗: 25% (2週間/8週間)
```

### 次のマイルストーン

**Week 3-4: MySQL/PostgreSQL実装**
- SQLパーサー実装
- JDBC/MyBatis対応
- 4種類の検出器実装
- 50テストケース

---

## 🤝 貢献

貢献を歓迎します！以下の手順でコントリビューションできます：

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

### コントリビューションガイドライン

- テストカバレッジ100%を維持
- 型ヒントとdocstringを必須とする
- ruffとmypyのチェックをパスする
- 既存のコードスタイルに従う

---

## 📄 ライセンス

MIT License

---

## 📧 お問い合わせ

プロジェクトに関する質問や提案は、Issueトラッカーをご利用ください。

---

**最終更新**: 2025年1月27日
**バージョン**: 1.0.0
**ステータス**: ✅ Elasticsearch 100%完成
