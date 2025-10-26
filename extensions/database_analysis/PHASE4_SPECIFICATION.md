# Phase 4: マルチデータベース解析フレームワーク - 技術仕様書

## 1. 概要

### 1.1 目的
Phase 4では、Phase 1のCassandra特化分析を拡張し、エンタープライズ環境で使用される主要なデータベースシステムを包括的に解析するマルチデータベースフレームワークを構築します。

### 1.2 対象データベース
- **MySQL / SQL Server** - リレーショナルデータベース
- **Redis** - インメモリキャッシュ
- **Elasticsearch** - 分散検索エンジン
- **Cassandra** - 分散NoSQLデータベース（Phase 1で実装済み）

### 1.3 主要機能
1. **SQL解析** - N+1問題検出、トランザクション境界分析
2. **Redis解析** - キャッシュ操作分析、TTL追跡、無効化パターン検出
3. **Elasticsearch解析** - Query DSL複雑度分析、パフォーマンスリスク評価
4. **Neo4jグラフ統合** - データベース操作のグラフ可視化
5. **FastAPI** - RESTful分析APIエンドポイント

---

## 2. アーキテクチャ

### 2.1 コンポーネント構成

```
phase4_multidb/
├── src/multidb_analyzer/
│   ├── models/              # Pydantic v2データモデル
│   │   └── database_models.py
│   ├── analyzers/           # データベース特化アナライザー
│   │   ├── sql_analyzer.py
│   │   ├── redis_analyzer.py
│   │   ├── elasticsearch_analyzer.py
│   │   └── transaction_analyzer.py
│   ├── neo4j/               # Neo4jグラフ統合
│   │   ├── schema_extension.py
│   │   └── graph_exporter.py
│   └── api/                 # FastAPIエンドポイント
│       └── main.py
└── tests/
    └── unit/                # ユニットテスト（103テスト、96%カバレッジ）
```

### 2.2 レイヤードアーキテクチャ

1. **プレゼンテーション層** - FastAPI RESTful API
2. **ビジネスロジック層** - アナライザー群
3. **データモデル層** - Pydantic v2モデル
4. **データアクセス層** - Neo4jグラフエクスポート

---

## 3. データモデル

### 3.1 コアモデル

#### DatabaseQuery
```python
class DatabaseQuery(BaseModel):
    id: str  # UUID
    query_text: str
    query_type: QueryType  # SELECT, INSERT, UPDATE, DELETE, CQL, DSL
    database: DatabaseType
    file_path: str
    line_number: int
    complexity: float  # 1.0 - 10.0
    is_in_loop: bool
    n_plus_one_risk: bool
    missing_transaction: bool
```

#### DatabaseEntity
```python
class DatabaseEntity(BaseModel):
    id: str
    name: str
    type: str  # table, collection, index, cache_key
    database: DatabaseType
    schema: Optional[str]
    has_index: bool
```

#### TransactionBoundary
```python
class TransactionBoundary(BaseModel):
    id: str
    type: str  # begin, commit, rollback
    file_path: str
    line_number: int
    isolation_level: Optional[str]
    is_distributed: bool
```

#### CacheOperation
```python
class CacheOperation(BaseModel):
    id: str
    operation: str  # get, set, delete, expire
    key_pattern: str
    file_path: str
    line_number: int
    ttl: Optional[int]
    missing_ttl: bool
    cache_pattern: Optional[CachePattern]
```

---

## 4. アナライザー実装

### 4.1 SQL Analyzer

**責務**: MySQL/SQL Serverクエリの解析、N+1問題検出

**主要メソッド**:
- `analyze_file(file_path)` - ファイルからSQL抽出
- `_extract_concatenated_sql()` - 文字列連結SQL抽出
- `_detect_n_plus_one_pattern()` - N+1問題検出
- `_calculate_complexity()` - クエリ複雑度計算

**検出パターン**:
```java
// Pattern 1: String literals
String sql = "SELECT * FROM users WHERE id = ?";

// Pattern 2: String concatenation
String sql = "SELECT * FROM users " +
           "WHERE id = ?";

// Pattern 3: Spring Data @Query
@Query("SELECT u FROM User u WHERE u.email = :email")
User findByEmail(@Param("email") String email);
```

**N+1検出ロジック**:
```python
def _detect_n_plus_one_pattern(sql, context):
    if not context.is_in_loop:
        return False
    if not sql.startswith("SELECT"):
        return False
    if self._has_foreign_key_condition(sql):
        return True
    return False
```

### 4.2 Redis Analyzer

**責務**: Redisキャッシュ操作の解析、TTL追跡

**主要メソッド**:
- `analyze_file(file_path)` - キャッシュ操作抽出
- `_extract_ttl()` - TTL値抽出
- `detect_cache_pattern()` - キャッシュパターン識別
- `find_invalidation_points()` - 無効化ポイント検出

**検出パターン**:
```java
// Pattern 1: Direct Redis calls
redis.get("user:123");
redis.set("user:123", user);
redis.setex("user:123", 3600, user);
redis.del("user:123");

// Pattern 2: Spring Cache annotations
@Cacheable("users")
User findById(Long id);

@CachePut("users")
User updateUser(User user);

@CacheEvict("users")
void deleteUser(Long id);
```

**キャッシュパターン**:
- `CACHE_ASIDE` - 読み取り時キャッシュ確認
- `WRITE_THROUGH` - 書き込み時キャッシュ更新
- `WRITE_BEHIND` - 非同期キャッシュ更新

### 4.3 Elasticsearch Analyzer

**責務**: Elasticsearch Query DSL解析、複雑度分析

**主要メソッド**:
- `analyze_file(file_path)` - Query DSL抽出
- `_extract_json_strings()` - ブレースカウントでJSON抽出
- `_calculate_es_complexity()` - 複雑度計算
- `assess_performance_risk()` - パフォーマンスリスク評価

**複雑度計算**:
```python
complexity = 1.0
complexity += depth * 1.0  # ネスト深度
complexity += clause_count * 0.5  # bool句数
complexity += len(aggs) * 1.5  # aggregations数
if uses_script:
    complexity += 2.0  # スクリプト使用
return min(complexity, 10.0)
```

**リスク評価**:
- `high` - スクリプト使用 or ワイルドカード or 複雑度 > 7.0
- `medium` - 複雑度 > 4.0
- `low` - 複雑度 ≤ 4.0

### 4.4 Transaction Analyzer

**責務**: トランザクション境界解析、デッドロックリスク評価

**主要メソッド**:
- `analyze_file(file_path)` - トランザクション境界抽出
- `assess_deadlock_risk()` - デッドロックリスク評価
- `check_distributed_tx()` - 分散トランザクション検出

**検出パターン**:
```java
// Pattern 1: Spring @Transactional
@Transactional(isolation = Isolation.SERIALIZABLE)
public void updateUser(User user) { }

// Pattern 2: Programmatic transaction
Transaction tx = session.beginTransaction();
try {
    // operations
    tx.commit();
} catch (Exception e) {
    tx.rollback();
}
```

**デッドロックリスク評価**:
```python
write_tables = set()
for query in write_queries:
    table = extract_table_name(query)
    write_tables.add(table)

if len(write_tables) > 3:
    return "high"
elif len(write_tables) > 1:
    return "medium"
else:
    return "low"
```

---

## 5. Neo4jグラフスキーマ拡張

### 5.1 新規ノードタイプ

#### DatabaseQuery ノード
```cypher
(:DatabaseQuery {
  id: "query_uuid",
  queryText: "SELECT * FROM users WHERE id = ?",
  queryType: "SELECT",
  database: "mysql",
  complexity: 2.5,
  isInLoop: true,
  nPlusOneRisk: true
})
```

#### DatabaseEntity ノード
```cypher
(:DatabaseEntity {
  id: "entity_uuid",
  name: "users",
  type: "table",
  database: "mysql",
  hasIndex: true
})
```

#### TransactionBoundary ノード
```cypher
(:TransactionBoundary {
  id: "tx_uuid",
  type: "begin",
  isolationLevel: "READ_COMMITTED",
  isDistributed: false
})
```

#### CacheOperation ノード
```cypher
(:CacheOperation {
  id: "cache_uuid",
  operation: "set",
  keyPattern: "user:*",
  ttl: 3600,
  missingTtl: false
})
```

### 5.2 新規関係タイプ

#### EXECUTES_QUERY
```cypher
(:Method)-[:EXECUTES_QUERY {
  frequency: 1,
  isInLoop: true,
  lineNumber: 145
}]->(:DatabaseQuery)
```

#### ACCESSES_ENTITY
```cypher
(:DatabaseQuery)-[:ACCESSES_ENTITY {
  operation: "read",
  isIndexed: true
}]->(:DatabaseEntity)
```

#### IN_TRANSACTION
```cypher
(:DatabaseQuery)-[:IN_TRANSACTION {
  position: 0
}]->(:TransactionBoundary)
```

---

## 6. FastAPI エンドポイント

### 6.1 エンドポイント一覧

#### POST /api/v1/analyze/file
**説明**: 単一ファイルのデータベース操作を解析

**リクエスト**:
```json
{
  "file_path": "/path/to/UserService.java",
  "database_type": "mysql"
}
```

**レスポンス**:
```json
{
  "status": "success",
  "queries": [...],
  "transactions": [...],
  "cache_operations": [...],
  "summary": {
    "total_queries": 5,
    "n_plus_one_risks": 2,
    "missing_transactions": 1
  }
}
```

#### POST /api/v1/analyze/directory
**説明**: ディレクトリ内のすべてのファイルを解析

**リクエスト**:
```json
{
  "directory_path": "/path/to/src",
  "file_pattern": "**/*.java",
  "include_tests": false
}
```

#### POST /api/v1/impact/database
**説明**: 特定のデータベースエンティティへの影響を分析

**リクエスト**:
```json
{
  "entity_name": "users",
  "database_type": "mysql"
}
```

**レスポンス**:
```json
{
  "entity_name": "users",
  "database_type": "mysql",
  "affected_queries": [...],
  "affected_methods": ["UserService.findById", "UserService.update"],
  "risk_assessment": "medium",
  "recommendations": [...]
}
```

#### GET /api/v1/health
**説明**: ヘルスチェック

**レスポンス**:
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "analyzers": {
    "sql": "available",
    "redis": "available",
    "elasticsearch": "available",
    "transaction": "available"
  }
}
```

---

## 7. テスト戦略

### 7.1 テストカバレッジ

**総合**: 96% (710行中684行カバー)

**コンポーネント別**:
- `database_models.py`: **100%** (130行)
- `transaction_analyzer.py`: **99%** (126行)
- `elasticsearch_analyzer.py`: **97%** (138行)
- `redis_analyzer.py`: **97%** (119行)
- `sql_analyzer.py`: **90%** (186行)

### 7.2 テスト構成

**総テスト数**: 103テスト

**カテゴリ別**:
- Elasticsearch Analyzer: 28テスト
- Redis Analyzer: 24テスト
- SQL Analyzer: 34テスト
- Transaction Analyzer: 17テスト

### 7.3 主要テストケース

#### N+1問題検出テスト
```python
def test_detect_n_plus_one_in_loop(self, tmp_path):
    test_file = tmp_path / "test.java"
    test_file.write_text('''
        for (User user : users) {
            String sql = "SELECT * FROM orders WHERE user_id = ?";
            executeQuery(sql, user.getId());
        }
    ''')
    queries = analyzer.analyze_file(str(test_file))
    assert queries[0].is_in_loop is True
    assert queries[0].n_plus_one_risk is True
```

#### キャッシュTTL検出テスト
```python
def test_extract_ttl_from_setex(self):
    redis_call = "redis.setex('key', 7200, value)"
    ttl = analyzer._extract_ttl(redis_call)
    assert ttl == 7200
```

#### Elasticsearch複雑度テスト
```python
def test_calculate_complexity_nested(self):
    query_dsl = {
        "query": {
            "bool": {
                "must": [...],
                "should": [...]
            }
        },
        "aggs": {...}
    }
    complexity = analyzer._calculate_es_complexity(query_dsl)
    assert complexity > 3.0
```

---

## 8. 使用方法

### 8.1 インストール

```bash
cd phase4_multidb
pip install -e .
```

### 8.2 プログラマティック使用

```python
from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer
from multidb_analyzer.models.database_models import DatabaseType

# SQLアナライザー
analyzer = SQLAnalyzer(database=DatabaseType.MYSQL)
queries = analyzer.analyze_file("src/UserService.java")

# N+1リスクをフィルタ
n_plus_one_queries = [q for q in queries if q.n_plus_one_risk]

# 複雑クエリをフィルタ
complex_queries = [q for q in queries if q.complexity > 5.0]
```

### 8.3 FastAPI起動

```bash
cd phase4_multidb
uvicorn multidb_analyzer.api.main:app --reload
```

ブラウザで http://localhost:8000/docs にアクセスしてSwagger UIを表示。

### 8.4 APIクライアント使用例

```python
import requests

# ファイル解析
response = requests.post(
    "http://localhost:8000/api/v1/analyze/file",
    json={
        "file_path": "/path/to/UserService.java",
        "database_type": "mysql"
    }
)
result = response.json()

# N+1リスクを表示
for query in result["queries"]:
    if query["n_plus_one_risk"]:
        print(f"N+1 Risk: {query['file_path']}:{query['line_number']}")
```

---

## 9. パフォーマンス

### 9.1 目標性能

| メトリック | 目標値 | 実測値 |
|----------|--------|--------|
| 単一ファイル解析 | < 100ms | 達成 |
| 10ファイル並列解析 | < 1秒 | 達成 |
| メモリ使用量 | < 500MB | 達成 |
| API応答時間 | < 200ms | 達成 |

### 9.2 最適化手法

1. **並列処理**: ThreadPoolExecutorでマルチファイル解析
2. **正規表現最適化**: プリコンパイル、効率的パターン
3. **Pydanticキャッシング**: モデル検証結果キャッシュ
4. **遅延評価**: 必要時のみNeo4jエクスポート

---

## 10. 制限事項と既知の問題

### 10.1 現在の制限

1. **スキーマ情報なし**: 実際のDBスキーマと照合不可
2. **動的SQL**: 実行時構築SQLは検出困難
3. **ORM複雑性**: Hibernate/MyBatis複雑クエリは部分検出
4. **パフォーマンス推定**: 実測値なし、静的推定のみ

### 10.2 今後の改善

1. **スキーマ統合**: DBスキーマ情報の取り込み
2. **動的解析**: 実行時トレース統合
3. **ML活用**: 異常検出モデル
4. **LLM統合**: Phase 2のLLM分析統合

---

## 11. まとめ

Phase 4では、エンタープライズ環境の主要データベースを包括的に解析する堅牢なフレームワークを構築しました。

**主要成果**:
- ✅ 4種のデータベース対応（MySQL, Redis, Elasticsearch, Cassandra）
- ✅ N+1問題、キャッシュ無効化、トランザクション境界の自動検出
- ✅ 96%テストカバレッジ、103テスト
- ✅ Neo4jグラフ統合、FastAPI RESTful API
- ✅ Pydantic v2による型安全性

Phase 4は、Phase 1-3の成果を統合し、Phase 5（React可視化）の基盤を提供します。
