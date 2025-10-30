# Phase 6: マルチデータベース対応 - 実装計画書

**バージョン**: 1.0.0
**開始日**: 2025年1月
**目標期限**: 2025年3月 (8週間)
**品質目標**: 100%テストカバレッジ、Grade A セキュリティ

---

## 📋 エグゼクティブサマリー

Phase 6では、Cassandra（Phase 1完了）とNeo4j（Phase 3完了）に加えて、以下のデータベースシステムへの対応を追加します：

- **Elasticsearch** - 検索エンジン
- **MySQL/PostgreSQL** - リレーショナルDB
- **MongoDB** - ドキュメントDB
- **Redis** - インメモリKVS

すべてのDBで以下を実現：
- ✅ コード静的解析
- ✅ 問題検出（パフォーマンス、セキュリティ）
- ✅ LLM統合による最適化提案
- ✅ Neo4jグラフDB統合
- ✅ 統合ダッシュボード
- ✅ 100%テストカバレッジ

---

## 🎯 プロジェクト目標

### 主要目標

1. **4種類のDBシステム対応**
   - Elasticsearch、MySQL/PostgreSQL、MongoDB、Redis

2. **統一された分析フレームワーク**
   - 共通インターフェース設計
   - プラグインアーキテクチャ
   - 横断的な依存関係分析

3. **品質基準達成**
   - テストカバレッジ: 100%
   - ドキュメントカバレッジ: 100%
   - セキュリティスコア: Grade A

4. **既存システムとの統合**
   - Phase 1-5との完全な互換性
   - Neo4jグラフDBへの統合
   - 統一APIエンドポイント

---

## 🏗️ アーキテクチャ設計

### 全体構成

```
phase4_multidb/
├── src/
│   └── multidb_analyzer/
│       ├── core/                    # コアフレームワーク
│       │   ├── base_parser.py       # 基底パーサー
│       │   ├── base_detector.py     # 基底検出器
│       │   ├── plugin_manager.py    # プラグインマネージャー
│       │   └── analyzer_factory.py  # アナライザーファクトリー
│       │
│       ├── elasticsearch/           # Elasticsearch対応
│       │   ├── parsers/
│       │   │   ├── java_client_parser.py
│       │   │   └── query_dsl_parser.py
│       │   ├── detectors/
│       │   │   ├── wildcard_detector.py
│       │   │   ├── script_query_detector.py
│       │   │   ├── mapping_detector.py
│       │   │   └── shard_detector.py
│       │   └── models/
│       │       └── es_models.py
│       │
│       ├── mysql/                   # MySQL/PostgreSQL対応
│       │   ├── parsers/
│       │   │   ├── sql_parser.py
│       │   │   └── jdbc_parser.py
│       │   ├── detectors/
│       │   │   ├── n_plus_one_detector.py
│       │   │   ├── missing_index_detector.py
│       │   │   ├── full_table_scan_detector.py
│       │   │   └── sql_injection_detector.py
│       │   └── models/
│       │       └── sql_models.py
│       │
│       ├── mongodb/                 # MongoDB対応
│       │   ├── parsers/
│       │   │   ├── mongo_client_parser.py
│       │   │   └── aggregation_parser.py
│       │   ├── detectors/
│       │   │   ├── collection_scan_detector.py
│       │   │   ├── large_document_detector.py
│       │   │   └── index_usage_detector.py
│       │   └── models/
│       │       └── mongo_models.py
│       │
│       ├── redis/                   # Redis対応
│       │   ├── parsers/
│       │   │   ├── jedis_parser.py
│       │   │   └── lettuce_parser.py
│       │   ├── detectors/
│       │   │   ├── large_key_detector.py
│       │   │   ├── hot_key_detector.py
│       │   │   └── blocking_command_detector.py
│       │   └── models/
│       │       └── redis_models.py
│       │
│       ├── integration/             # 統合機能
│       │   ├── neo4j_integrator.py  # Neo4j統合
│       │   ├── cross_db_analyzer.py # 横断分析
│       │   └── unified_reporter.py  # 統合レポート
│       │
│       ├── llm/                     # LLM統合
│       │   ├── es_optimizer.py
│       │   ├── sql_optimizer.py
│       │   ├── mongo_optimizer.py
│       │   └── redis_optimizer.py
│       │
│       └── utils/
│           ├── config.py
│           └── helpers.py
│
├── tests/                           # テストスイート
│   ├── unit/
│   │   ├── test_elasticsearch/
│   │   ├── test_mysql/
│   │   ├── test_mongodb/
│   │   └── test_redis/
│   ├── integration/
│   │   ├── test_cross_db/
│   │   └── test_neo4j_integration/
│   └── e2e/
│       └── test_unified_analysis/
│
├── docs/
│   ├── elasticsearch_guide.md
│   ├── mysql_guide.md
│   ├── mongodb_guide.md
│   ├── redis_guide.md
│   └── api_reference.md
│
├── examples/
│   ├── sample_elasticsearch/
│   ├── sample_mysql/
│   ├── sample_mongodb/
│   └── sample_redis/
│
├── pyproject.toml
├── requirements.txt
└── README_MULTIDB.md
```

### コアフレームワーク設計

#### 1. 基底パーサー (BaseParser)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    """すべてのDBパーサーの基底クラス"""

    @abstractmethod
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """ファイルを解析してクエリ情報を抽出"""
        pass

    @abstractmethod
    def extract_queries(self, ast) -> List[Dict[str, Any]]:
        """ASTからクエリを抽出"""
        pass

    @abstractmethod
    def get_db_type(self) -> str:
        """データベースタイプを返す"""
        pass
```

#### 2. 基底検出器 (BaseDetector)

```python
class BaseDetector(ABC):
    """すべての検出器の基底クラス"""

    @abstractmethod
    def detect(self, queries: List[Dict[str, Any]]) -> List[Issue]:
        """問題を検出"""
        pass

    @abstractmethod
    def get_severity(self) -> str:
        """重要度を返す (CRITICAL, HIGH, MEDIUM, LOW)"""
        pass
```

#### 3. プラグインマネージャー

```python
class PluginManager:
    """DBプラグインを管理"""

    def register_plugin(self, db_type: str, parser, detectors):
        """プラグインを登録"""

    def get_parser(self, db_type: str) -> BaseParser:
        """パーサーを取得"""

    def get_detectors(self, db_type: str) -> List[BaseDetector]:
        """検出器を取得"""
```

---

## 📊 実装スコープ

### 1. Elasticsearch対応

#### パーサー実装

**対応するJavaクライアント**:
- RestHighLevelClient
- RestClient
- TransportClient (非推奨だが legacy対応)

**解析対象**:
```java
// Search API
SearchRequest searchRequest = new SearchRequest("index");
SearchSourceBuilder searchSourceBuilder = new SearchSourceBuilder();
searchSourceBuilder.query(QueryBuilders.matchQuery("field", "value"));

// Aggregation
AggregationBuilder aggregation = AggregationBuilders
    .terms("by_field")
    .field("field.keyword");

// Script Query (要注意)
ScriptQueryBuilder scriptQuery = QueryBuilders
    .scriptQuery(new Script("doc['field'].value > 100"));
```

#### 検出器実装

1. **WildcardDetector** (HIGH)
   - 問題: `*`始まりのワイルドカード検索
   - 影響: インデックスを使えず全文スキャン
   ```java
   // ❌ 悪い例
   .query(QueryBuilders.wildcardQuery("name", "*smith"))
   ```

2. **ScriptQueryDetector** (CRITICAL)
   - 問題: Script Queryの乱用
   - 影響: CPU使用率増大、パフォーマンス劣化
   ```java
   // ❌ 悪い例
   .scriptQuery(new Script("doc['price'].value * 1.1 > 1000"))
   ```

3. **MappingDetector** (MEDIUM)
   - 問題: Dynamic Mapping依存
   - 影響: 型の不一致、ディスク容量増大

4. **ShardDetector** (HIGH)
   - 問題: Shard数の不適切な設定
   - 影響: メモリ使用量増大、検索パフォーマンス低下

### 2. MySQL/PostgreSQL対応

#### パーサー実装

**対応するJavaクライアント**:
- JDBC
- MyBatis
- Hibernate/JPA
- jOOQ

**解析対象**:
```java
// JDBC
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id = " + userId);

// MyBatis
@Select("SELECT * FROM users WHERE id = #{id}")
User findById(Long id);

// JPA
@Query("SELECT u FROM User u WHERE u.status = ?1")
List<User> findByStatus(String status);
```

#### 検出器実装

1. **NPlusOneDetector** (CRITICAL)
   - 問題: N+1クエリ問題
   - 影響: データベース負荷増大
   ```java
   // ❌ 悪い例
   List<User> users = userRepository.findAll(); // 1回
   for (User user : users) {
       List<Order> orders = orderRepository.findByUserId(user.getId()); // N回
   }
   ```

2. **MissingIndexDetector** (HIGH)
   - 問題: WHERE句にインデックスなし
   - 影響: フルテーブルスキャン

3. **FullTableScanDetector** (HIGH)
   - 問題: `SELECT *` の乱用
   - 影響: 不要なデータ転送

4. **SQLInjectionDetector** (CRITICAL)
   - 問題: 文字列連結によるSQL生成
   - 影響: SQLインジェクション脆弱性
   ```java
   // ❌ 危険
   "SELECT * FROM users WHERE name = '" + userName + "'"
   ```

### 3. MongoDB対応

#### パーサー実装

**対応するJavaドライバー**:
- MongoDB Java Driver
- Spring Data MongoDB

**解析対象**:
```java
// Find
collection.find(eq("status", "active"));

// Aggregation
collection.aggregate(Arrays.asList(
    match(eq("status", "active")),
    group("$category", sum("total", "$amount"))
));

// Update
collection.updateMany(
    eq("status", "inactive"),
    set("archived", true)
);
```

#### 検出器実装

1. **CollectionScanDetector** (HIGH)
   - 問題: インデックスなしのクエリ
   - 影響: コレクション全体スキャン

2. **LargeDocumentDetector** (MEDIUM)
   - 問題: 16MB制限に近い大きなドキュメント
   - 影響: メモリ使用量増大

3. **IndexUsageDetector** (HIGH)
   - 問題: 複合インデックスの誤用
   - 影響: インデックス効率低下

### 4. Redis対応

#### パーサー実装

**対応するJavaクライアント**:
- Jedis
- Lettuce
- Spring Data Redis

**解析対象**:
```java
// Jedis
jedis.get("user:1000");
jedis.keys("user:*"); // 要注意

// Lettuce
RedisCommands<String, String> commands = connection.sync();
commands.set("key", "value");

// Spring Data Redis
redisTemplate.opsForValue().get("key");
```

#### 検出器実装

1. **LargeKeyDetector** (MEDIUM)
   - 問題: 大きなキーサイズ
   - 影響: メモリ使用量増大

2. **HotKeyDetector** (HIGH)
   - 問題: 特定キーへのアクセス集中
   - 影響: パフォーマンス低下

3. **BlockingCommandDetector** (CRITICAL)
   - 問題: `KEYS *`、`FLUSHALL`等のブロッキングコマンド
   - 影響: Redis全体のブロック
   ```java
   // ❌ 本番環境で絶対NG
   jedis.keys("*");
   jedis.flushAll();
   ```

---

## 🧪 テスト戦略

### テストカバレッジ目標: 100%

#### 1. ユニットテスト

**各DB最低50テストケース**:
- パーサーテスト: 20ケース
- 検出器テスト: 20ケース
- モデルテスト: 10ケース

**合計**: 200+ ユニットテスト

#### 2. 統合テスト

- クロスDB分析: 10ケース
- Neo4j統合: 10ケース
- LLM統合: 10ケース

**合計**: 30+ 統合テスト

#### 3. E2Eテスト

- 統一API: 10ケース
- レポート生成: 5ケース

**合計**: 15+ E2Eテスト

#### 総テスト数: 245+

---

## 📅 実装スケジュール (8週間)

### Week 1-2: Elasticsearch実装

**Week 1**:
- [ ] Elasticsearchパーサー実装
- [ ] 基本的な検出器実装 (Wildcard, ScriptQuery)
- [ ] ユニットテスト (50ケース)

**Week 2**:
- [ ] 高度な検出器実装 (Mapping, Shard)
- [ ] LLM統合
- [ ] 統合テスト

**成果物**:
- `elasticsearch/parsers/`
- `elasticsearch/detectors/`
- テストカバレッジ: 100%

### Week 3-4: MySQL/PostgreSQL実装

**Week 3**:
- [ ] SQLパーサー実装
- [ ] JDBC/MyBatis/JPA対応
- [ ] NPlusOne、MissingIndex検出器

**Week 4**:
- [ ] SQLInjection検出器
- [ ] LLM統合
- [ ] ユニットテスト (50ケース)

**成果物**:
- `mysql/parsers/`
- `mysql/detectors/`
- テストカバレッジ: 100%

### Week 5: MongoDB実装

- [ ] MongoDBパーサー実装
- [ ] CollectionScan、LargeDocument検出器
- [ ] LLM統合
- [ ] ユニットテスト (50ケース)

**成果物**:
- `mongodb/parsers/`
- `mongodb/detectors/`
- テストカバレッジ: 100%

### Week 6: Redis実装

- [ ] Redisパーサー実装 (Jedis, Lettuce)
- [ ] BlockingCommand、HotKey検出器
- [ ] LLM統合
- [ ] ユニットテスト (50ケース)

**成果物**:
- `redis/parsers/`
- `redis/detectors/`
- テストカバレッジ: 100%

### Week 7: 統合機能実装

- [ ] Neo4jマルチDB統合
- [ ] クロスDB分析
- [ ] 統一レポート生成
- [ ] 統合テスト (30ケース)

**成果物**:
- `integration/neo4j_integrator.py`
- `integration/cross_db_analyzer.py`
- `integration/unified_reporter.py`

### Week 8: ドキュメント＆最終テスト

- [ ] APIドキュメント作成
- [ ] 各DBガイド作成
- [ ] E2Eテスト (15ケース)
- [ ] パフォーマンステスト
- [ ] セキュリティ監査

**成果物**:
- `docs/` 完全版
- `examples/` サンプルコード
- `README_MULTIDB.md`

---

## 🎯 品質基準

### コード品質

- **テストカバレッジ**: 100%
- **型ヒント**: すべての関数
- **Docstring**: すべての公開API
- **リンティング**: ruff エラー 0
- **型チェック**: mypy エラー 0

### パフォーマンス

| 指標 | 目標値 |
|------|--------|
| 単一ファイル解析 | < 100ms |
| 10ファイル並列解析 | < 1秒 |
| LLM分析/ファイル | < 2秒 |
| Neo4j統合 | < 500ms |

### ドキュメント

- **カバレッジ**: 100%
- **API Reference**: 完全
- **ガイド**: 各DB毎
- **サンプルコード**: 各DB毎

---

## 🔧 技術スタック

### 既存の継続使用

- Python 3.11+
- pytest (テスト)
- Claude API (LLM)
- Neo4j (グラフDB)

### 新規追加

**Elasticsearchパーサー**:
- elasticsearch-dsl-py
- elasticsearch (公式クライアント)

**SQLパーサー**:
- sqlparse
- sqlalchemy (ORM解析用)

**MongoDBパーサー**:
- pymongo
- mongoengine

**Redisパーサー**:
- redis-py

**その他**:
- pydantic (データモデル)
- rich (CLI出力)

---

## 📦 デリバラブル

### 1. ソースコード

- `phase4_multidb/src/` - 全実装コード
- `phase4_multidb/tests/` - 245+ テストケース

### 2. ドキュメント

- `README_MULTIDB.md` - プロジェクト概要
- `docs/elasticsearch_guide.md` - Elasticsearchガイド
- `docs/mysql_guide.md` - MySQL/PostgreSQLガイド
- `docs/mongodb_guide.md` - MongoDBガイド
- `docs/redis_guide.md` - Redisガイド
- `docs/api_reference.md` - API完全リファレンス
- `docs/integration_guide.md` - 統合ガイド

### 3. サンプルコード

- `examples/sample_elasticsearch/` - ESサンプル
- `examples/sample_mysql/` - SQLサンプル
- `examples/sample_mongodb/` - MongoDBサンプル
- `examples/sample_redis/` - Redisサンプル

### 4. テストレポート

- カバレッジレポート (100%)
- パフォーマンステスト結果
- セキュリティ監査レポート

---

## 🚀 API設計

### 統一APIエンドポイント

```python
# 基本的な使用方法
from multidb_analyzer import MultiDBAnalyzer

# アナライザーの初期化
analyzer = MultiDBAnalyzer()

# Elasticsearchファイルの解析
es_results = analyzer.analyze(
    file_path="src/SearchService.java",
    db_type="elasticsearch"
)

# MySQLファイルの解析
mysql_results = analyzer.analyze(
    file_path="src/UserRepository.java",
    db_type="mysql"
)

# クロスDB分析
cross_results = analyzer.analyze_cross_db(
    base_path="src/",
    db_types=["elasticsearch", "mysql", "mongodb", "redis"]
)

# Neo4j統合
analyzer.integrate_with_neo4j(
    neo4j_uri="bolt://localhost:7687",
    results=cross_results
)

# 統一レポート生成
analyzer.generate_report(
    results=cross_results,
    output_format="html",
    output_path="report.html"
)
```

### CLIインターフェース

```bash
# Elasticsearch解析
multidb-analyzer analyze --type elasticsearch --path src/

# MySQL解析
multidb-analyzer analyze --type mysql --path src/

# クロスDB解析
multidb-analyzer analyze-all --path src/

# レポート生成
multidb-analyzer report --input results.json --output report.html

# Neo4j統合
multidb-analyzer integrate-neo4j --uri bolt://localhost:7687
```

---

## 📈 成功基準

### 必須要件

- [x] 4種類のDB対応完了 (Elasticsearch, MySQL, MongoDB, Redis)
- [x] テストカバレッジ 100%
- [x] ドキュメント完全版
- [x] Neo4j統合完了
- [x] LLM統合完了

### パフォーマンス要件

- [x] 単一ファイル解析 < 100ms
- [x] 10ファイル並列 < 1秒
- [x] メモリ使用量 < 1GB

### 品質要件

- [x] ruff エラー 0
- [x] mypy エラー 0
- [x] セキュリティスコア Grade A

---

## 🎓 学習リソース

### Elasticsearch

- [Elasticsearch: The Definitive Guide](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html)
- [Elasticsearch Performance Tuning](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)

### MySQL/PostgreSQL

- [High Performance MySQL](https://www.oreilly.com/library/view/high-performance-mysql/9781449332471/)
- [PostgreSQL Performance Optimization](https://www.postgresql.org/docs/current/performance-tips.html)

### MongoDB

- [MongoDB Performance Best Practices](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/)

### Redis

- [Redis Best Practices](https://redis.io/docs/management/optimization/)

---

## ✅ チェックリスト

### 開始前

- [ ] Phase 1-5の完了確認
- [ ] 開発環境セットアップ
- [ ] 依存ライブラリインストール
- [ ] Neo4j起動確認

### Week 1-2完了時

- [ ] Elasticsearchパーサー実装
- [ ] 検出器4種類実装
- [ ] ユニットテスト50ケース
- [ ] テストカバレッジ100%

### Week 3-4完了時

- [ ] SQLパーサー実装
- [ ] 検出器4種類実装
- [ ] ユニットテスト50ケース
- [ ] テストカバレッジ100%

### Week 5完了時

- [ ] MongoDBパーサー実装
- [ ] 検出器3種類実装
- [ ] ユニットテスト50ケース

### Week 6完了時

- [ ] Redisパーサー実装
- [ ] 検出器3種類実装
- [ ] ユニットテスト50ケース

### Week 7完了時

- [ ] Neo4j統合完了
- [ ] クロスDB分析完了
- [ ] 統合テスト30ケース

### Week 8完了時

- [ ] 全ドキュメント完成
- [ ] E2Eテスト15ケース
- [ ] Phase 6完了宣言

---

**ドキュメント管理**:
- **作成日**: 2025年1月
- **バージョン**: 1.0.0
- **レビュー担当**: Architecture Team
- **承認**: Project Manager
