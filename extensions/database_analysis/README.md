# Phase 4: Multi-Database Analyzer 🗄️

**エンタープライズ向けマルチデータベース静的解析フレームワーク**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Test Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](tests/)
[![Tests](https://img.shields.io/badge/tests-103%20passed-success.svg)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)

---

## 📋 目次

- [概要](#-概要)
- [主要機能](#-主要機能)
- [対応データベース](#-対応データベース)
- [クイックスタート](#-クイックスタート)
- [使用例](#-使用例)
- [API仕様](#-api仕様)
- [アーキテクチャ](#️-アーキテクチャ)
- [テスト](#-テスト)
- [パフォーマンス](#-パフォーマンス)

---

## 🎯 概要

Phase 4 Multi-Database Analyzerは、エンタープライズアプリケーションで使用される主要なデータベースシステム（MySQL、Redis、Elasticsearch、Cassandra）のソースコードを静的解析し、パフォーマンス問題やアンチパターンを自動検出するPythonフレームワークです。

### なぜPhase 4?

- ✅ **N+1問題の自動検出** - ループ内でのクエリ実行を検出
- ✅ **トランザクション境界の可視化** - 分散トランザクションリスク評価
- ✅ **キャッシュ無効化パターン分析** - Redis操作の最適化提案
- ✅ **Elasticsearchクエリ複雑度分析** - パフォーマンスリスク評価
- ✅ **Neo4jグラフ統合** - データベース依存関係の可視化
- ✅ **RESTful API** - CI/CDパイプライン統合

---

## ✨ 主要機能

### 1. SQL解析エンジン (MySQL / SQL Server)

```java
// N+1問題を検出
for (User user : users) {
    String sql = "SELECT * FROM orders WHERE user_id = ?";
    List<Order> orders = executeQuery(sql, user.getId());  // ⚠️ N+1リスク検出
}
```

**検出項目**:
- ✅ N+1クエリ問題
- ✅ トランザクション境界の欠落
- ✅ プリペアドステートメント未使用
- ✅ クエリ複雑度分析
- ✅ インデックス使用推定

### 2. Redis解析エンジン

```java
// TTL未設定を検出
@CachePut("users")
public User updateUser(User user) {
    redis.set("user:" + user.getId(), user);  // ⚠️ TTL未設定
    return userRepository.save(user);
}
```

**検出項目**:
- ✅ TTL未設定
- ✅ キャッシュ無効化漏れ
- ✅ キャッシュパターン識別（Cache-Aside、Write-Through）
- ✅ Spring Cache アノテーション解析

### 3. Elasticsearch解析エンジン

```javascript
// 複雑クエリを検出
const query = {
  "query": {
    "bool": {
      "must": [ /* 複雑な条件 */ ],  // ⚠️ 複雑度: 8.5/10
      "filter": [ /* ... */ ]
    }
  },
  "aggs": { /* ... */ }
};
```

**検出項目**:
- ✅ Query DSL複雑度分析（1-10スケール）
- ✅ パフォーマンスリスク評価（high/medium/low）
- ✅ ワイルドカード・スクリプト検出
- ✅ ネスト深度分析

### 4. トランザクション解析エンジン

```java
// 分散トランザクションリスクを検出
@Transactional
public void updateUserAndCache(User user) {
    userRepository.save(user);           // MySQL
    redis.set("user:" + id, user);       // Redis
    // ⚠️ 分散トランザクションリスク検出
}
```

**検出項目**:
- ✅ トランザクション境界検出（@Transactional、プログラマティック）
- ✅ 分散トランザクションリスク評価
- ✅ デッドロックリスク評価
- ✅ 隔離レベル・タイムアウト抽出

---

## 🗄️ 対応データベース

| データベース | 解析対象 | 主要検出項目 |
|------------|---------|------------|
| **MySQL / SQL Server** | SQL文、トランザクション | N+1問題、インデックス、トランザクション境界 |
| **Redis** | キャッシュ操作 | TTL未設定、無効化漏れ、パターン |
| **Elasticsearch** | Query DSL | 複雑度、パフォーマンスリスク、ワイルドカード |
| **Cassandra** | CQL文（Phase 1実装） | 整合性レベル、Partition Key、バッチ |

---

## 🚀 クイックスタート

### 前提条件

- Python 3.11+
- pip

### インストール

```bash
cd phase4_multidb
pip install -e .
```

### 基本的な使用方法

#### 1. Pythonスクリプトで使用

```python
from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer
from multidb_analyzer.models.database_models import DatabaseType

# SQLアナライザー初期化
analyzer = SQLAnalyzer(database=DatabaseType.MYSQL)

# ファイル解析
queries = analyzer.analyze_file("src/main/java/UserService.java")

# N+1リスクをフィルタ
n_plus_one_queries = [q for q in queries if q.n_plus_one_risk]

# 結果表示
for query in n_plus_one_queries:
    print(f"⚠️ N+1 Risk: {query.file_path}:{query.line_number}")
    print(f"   Query: {query.query_text[:100]}...")
    print(f"   Complexity: {query.complexity}")
```

#### 2. FastAPI サーバー起動

```bash
uvicorn multidb_analyzer.api.main:app --reload
```

ブラウザで http://localhost:8000/docs にアクセスしてSwagger UIを表示。

#### 3. APIクライアント使用

```python
import requests

# ファイル解析APIを呼び出し
response = requests.post(
    "http://localhost:8000/api/v1/analyze/file",
    json={
        "file_path": "/path/to/UserService.java",
        "database_type": "mysql"
    }
)

result = response.json()
print(f"Total queries: {result['summary']['total_queries']}")
print(f"N+1 risks: {result['summary']['n_plus_one_risks']}")
```

---

## 💡 使用例

### 例1: ディレクトリ一括解析

```python
from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer
from pathlib import Path

analyzer = SQLAnalyzer()
all_queries = []

# src/配下の全Javaファイルを解析
for java_file in Path("src").glob("**/*.java"):
    queries = analyzer.analyze_file(str(java_file))
    all_queries.extend(queries)

# 複雑クエリトップ10を表示
complex_queries = sorted(all_queries, key=lambda q: q.complexity, reverse=True)[:10]
for i, query in enumerate(complex_queries, 1):
    print(f"{i}. Complexity: {query.complexity:.2f} - {query.file_path}:{query.line_number}")
```

### 例2: Redisキャッシュパターン分析

```python
from multidb_analyzer.analyzers.redis_analyzer import RedisAnalyzer

analyzer = RedisAnalyzer()
operations = analyzer.analyze_file("src/main/java/CacheService.java")

# TTL未設定の操作を検出
missing_ttl = [op for op in operations if op.missing_ttl]
print(f"⚠️ Found {len(missing_ttl)} cache operations without TTL")

# キャッシュパターンを判定
pattern = analyzer.detect_cache_pattern(operations)
print(f"Cache pattern: {pattern}")

# 無効化ポイントを検出
invalidation_points = analyzer.find_invalidation_points("user:*", operations)
print(f"Invalidation methods: {invalidation_points}")
```

### 例3: Elasticsearch複雑クエリ検出

```python
from multidb_analyzer.analyzers.elasticsearch_analyzer import ElasticsearchAnalyzer

analyzer = ElasticsearchAnalyzer()
queries = analyzer.analyze_file("src/main/java/SearchService.java")

# 複雑クエリをフィルタ（複雑度 > 5.0）
complex_queries = analyzer.find_complex_queries(min_complexity=5.0)

for query in complex_queries:
    risk = analyzer.assess_performance_risk(query)
    print(f"Complexity: {query.complexity:.1f}/10, Risk: {risk}")
    print(f"Location: {query.file_path}:{query.line_number}")
```

### 例4: トランザクション境界分析

```python
from multidb_analyzer.analyzers.transaction_analyzer import TransactionAnalyzer
from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer

tx_analyzer = TransactionAnalyzer()
sql_analyzer = SQLAnalyzer()

# トランザクション境界を検出
transactions = tx_analyzer.analyze_file("src/main/java/OrderService.java")

# クエリを解析
queries = sql_analyzer.analyze_file("src/main/java/OrderService.java")

# 分散トランザクションチェック
is_distributed, db_count = tx_analyzer.check_distributed_tx(queries)
if is_distributed:
    print(f"⚠️ Distributed transaction detected across {db_count} databases")

# デッドロックリスク評価
risk = tx_analyzer.assess_deadlock_risk(queries)
print(f"Deadlock risk: {risk}")
```

---

## 📡 API仕様

### エンドポイント一覧

#### 1. ファイル解析

**POST** `/api/v1/analyze/file`

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/file" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/UserService.java",
    "database_type": "mysql"
  }'
```

**レスポンス**:
```json
{
  "status": "success",
  "queries": [
    {
      "id": "...",
      "query_text": "SELECT * FROM users WHERE id = ?",
      "query_type": "SELECT",
      "complexity": 2.5,
      "n_plus_one_risk": true,
      "file_path": "UserService.java",
      "line_number": 42
    }
  ],
  "summary": {
    "total_queries": 5,
    "n_plus_one_risks": 2,
    "complex_queries": 1
  }
}
```

#### 2. ディレクトリ解析

**POST** `/api/v1/analyze/directory`

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/src",
    "file_pattern": "**/*.java",
    "include_tests": false
  }'
```

#### 3. DB影響分析

**POST** `/api/v1/impact/database`

```bash
curl -X POST "http://localhost:8000/api/v1/impact/database" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "users",
    "database_type": "mysql"
  }'
```

#### 4. ヘルスチェック

**GET** `/api/v1/health`

```bash
curl http://localhost:8000/api/v1/health
```

---

## 🏗️ アーキテクチャ

### ディレクトリ構造

```
phase4_multidb/
├── src/multidb_analyzer/
│   ├── models/              # Pydantic v2データモデル
│   │   └── database_models.py
│   ├── analyzers/           # データベース特化アナライザー
│   │   ├── sql_analyzer.py           # SQL解析
│   │   ├── redis_analyzer.py         # Redis解析
│   │   ├── elasticsearch_analyzer.py # Elasticsearch解析
│   │   └── transaction_analyzer.py   # トランザクション解析
│   ├── neo4j/               # Neo4jグラフ統合
│   │   ├── schema_extension.py       # スキーマ拡張
│   │   └── graph_exporter.py         # グラフエクスポート
│   └── api/                 # FastAPIエンドポイント
│       └── main.py
├── tests/
│   └── unit/                # ユニットテスト（103テスト）
│       ├── test_sql_analyzer.py
│       ├── test_redis_analyzer.py
│       ├── test_elasticsearch_analyzer.py
│       └── test_transaction_analyzer.py
├── pyproject.toml           # プロジェクト設定
├── README.md                # このファイル
└── PHASE4_SPECIFICATION.md  # 技術仕様書
```

### コンポーネント図

```
┌─────────────────────────────────────────┐
│        FastAPI REST API                  │
│  (POST /analyze/file, /analyze/directory)│
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│    Business Logic Layer                  │
├──────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │   SQL    │ │  Redis   │ │    ES    │ │
│ │ Analyzer │ │ Analyzer │ │ Analyzer │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ ┌────────────────────────────────────┐  │
│ │   Transaction Analyzer              │  │
│ └────────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│       Data Model Layer                   │
│    (Pydantic v2 Models)                  │
├──────────────────────────────────────────┤
│  DatabaseQuery, DatabaseEntity,          │
│  TransactionBoundary, CacheOperation     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│   Neo4j Graph Export Layer               │
│  (MultiDBGraphExporter)                  │
└──────────────────────────────────────────┘
```

---

## 🧪 テスト

### テスト実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=src/multidb_analyzer --cov-report=html

# 特定のテストのみ実行
pytest tests/unit/test_sql_analyzer.py -v
```

### テストカバレッジ

**総合**: **96%** (710行中684行カバー)

| コンポーネント | カバレッジ | 行数 | 未カバー行 |
|--------------|----------|------|----------|
| `database_models.py` | **100%** | 130 | 0 |
| `transaction_analyzer.py` | **99%** | 126 | 1 |
| `elasticsearch_analyzer.py` | **97%** | 138 | 4 |
| `redis_analyzer.py` | **97%** | 119 | 3 |
| `sql_analyzer.py` | **90%** | 186 | 18 |

**総テスト数**: 103テスト（全てパス）

---

## ⚡ パフォーマンス

### ベンチマーク結果

| 項目 | 目標値 | 実測値 | ステータス |
|------|--------|--------|----------|
| 単一ファイル解析 | < 100ms | 50-80ms | ✅ 達成 |
| 10ファイル並列解析 | < 1秒 | 0.5-0.7秒 | ✅ 達成 |
| メモリ使用量（20ファイル） | < 500MB | 200-300MB | ✅ 達成 |
| API応答時間 | < 200ms | 100-150ms | ✅ 達成 |

### 最適化手法

1. **正規表現プリコンパイル** - パターンマッチング高速化
2. **Pydanticモデルキャッシング** - 検証結果再利用
3. **遅延評価** - 必要時のみグラフエクスポート
4. **並列処理** - ThreadPoolExecutorでマルチファイル解析

---

## 📚 ドキュメント

- [技術仕様書](PHASE4_SPECIFICATION.md) - 詳細な実装仕様
- [API仕様](http://localhost:8000/docs) - Swagger UI（サーバー起動後）
- [Neo4jスキーマ](src/multidb_analyzer/neo4j/schema_extension.py) - グラフスキーマ定義

---

**Phase 4: Multi-Database Analyzer** - エンタープライズ品質のデータベース静的解析フレームワーク 🚀
