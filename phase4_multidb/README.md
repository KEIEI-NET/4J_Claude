# Phase 4: 他データベース展開

**ステータス**: 🔵 計画中
**期間**: 2026年1月6日 - 2月14日

## 目標

全データベース対応完了：MySQL, Redis, Elasticsearch, SQL Server

## 主要機能

### Week 11-12: MySQL対応

#### Task 15.1: MySQLパーサー実装

**実装内容**:
- SQL文解析
- JOIN検出
- トランザクション追跡
- インデックス使用状況

**MySQL固有の問題検出**:
- N+1問題
- フルテーブルスキャン
- トランザクション漏れ
- デッドロックリスク

#### Task 15.2: MySQL統合テスト
- ユニットテスト
- 統合テスト
- パフォーマンステスト

### Week 13-14: Redis/Elasticsearch対応

#### Task 16.1: Redisパーサー実装

**実装内容**:
- Redisコマンド解析
- キャッシュ整合性チェック
- TTL設定検証
- メモリ使用量推定

**Redis固有の問題検出**:
- キャッシュミス率高
- TTL未設定
- メモリリーク
- キー設計の問題

#### Task 16.2: Elasticsearchパーサー実装

**実装内容**:
- クエリDSL解析
- インデックス設計評価
- シャード設定検証
- パフォーマンス問題検出

**Elasticsearch固有の問題検出**:
- インデックス設計の非効率
- シャード数の不適切
- レプリカ設定の問題
- クエリのN+1問題

### Week 15-16: SQL Server対応と最終統合

#### Task 17.1: SQL Serverパーサー実装

**実装内容**:
- T-SQL解析
- ストアドプロシージャ分析
- トランザクション分離レベル
- インデックス最適化

**SQL Server固有の問題検出**:
- ストアドプロシージャのパフォーマンス問題
- トランザクション分離レベルの不適切
- インデックスフラグメンテーション
- 統計情報の更新漏れ

#### Task 17.2: 全DB統合テスト

**テスト内容**:
- 5種DB同時分析
- クロスDB整合性チェック
- パフォーマンステスト
- E2Eテスト

## 成功条件

- [ ] 5種DB全対応
- [ ] クロスDB整合性チェック機能
- [ ] 統合E2Eテスト成功
- [ ] 全DB問題検出率 > 80%

## 予算

Phase 3と同等: $985/月

## ディレクトリ構造（予定）

```
phase4_multidb/
├── src/
│   └── cassandra_analyzer/
│       ├── parsers/
│       │   ├── mysql_parser.py        # MySQLパーサー
│       │   ├── redis_parser.py        # Redisパーサー
│       │   ├── elasticsearch_parser.py # Elasticsearchパーサー
│       │   └── sqlserver_parser.py    # SQL Serverパーサー
│       ├── detectors/
│       │   ├── mysql/
│       │   │   ├── n_plus_one_detector.py
│       │   │   ├── full_scan_detector.py
│       │   │   └── deadlock_detector.py
│       │   ├── redis/
│       │   │   ├── cache_miss_detector.py
│       │   │   └── ttl_detector.py
│       │   ├── elasticsearch/
│       │   │   ├── index_design_detector.py
│       │   │   └── shard_detector.py
│       │   └── sqlserver/
│       │       ├── stored_proc_detector.py
│       │       └── isolation_level_detector.py
│       └── analyzers/
│           └── cross_db_analyzer.py   # クロスDB整合性
├── tests/
│   ├── unit/
│   │   ├── test_mysql_parser.py
│   │   ├── test_redis_parser.py
│   │   ├── test_elasticsearch_parser.py
│   │   └── test_sqlserver_parser.py
│   ├── integration/
│   │   └── test_multi_db_integration.py
│   └── e2e/
│       └── test_full_multi_db_analysis.py
└── README.md                          # このファイル
```

## 対応データベース詳細

### 1. MySQL
- **パーサーライブラリ**: `sqlparse`, `sqlalchemy`
- **主な問題パターン**: N+1, フルスキャン, トランザクション漏れ
- **推定工数**: 3日

### 2. Redis
- **パーサーライブラリ**: カスタム実装（コマンド文字列解析）
- **主な問題パターン**: TTL未設定, メモリリーク, キー設計
- **推定工数**: 2日

### 3. Elasticsearch
- **パーサーライブラリ**: カスタム実装（JSON DSL解析）
- **主な問題パターン**: インデックス設計, シャード設定, クエリN+1
- **推定工数**: 3日

### 4. SQL Server
- **パーサーライブラリ**: `sqlparse`, `pyodbc`
- **主な問題パターン**: ストアドプロシージャ, 分離レベル, インデックス
- **推定工数**: 3日

## クロスDB整合性チェック

### キャッシュ整合性（Cassandra ↔ Redis）
```python
# Cassandraの更新がRedisキャッシュに反映されているかチェック
if cassandra_update_detected:
    check_redis_cache_invalidation()
```

### データ同期（Cassandra ↔ MySQL）
```python
# CassandraとMySQLのデータ整合性チェック
compare_data_between_dbs(cassandra_table, mysql_table)
```

### 検索同期（Cassandra ↔ Elasticsearch）
```python
# Cassandraの更新がElasticsearchインデックスに反映されているかチェック
if cassandra_write_detected:
    check_elasticsearch_index_update()
```

## 詳細計画

詳細なタスクとタイムラインは [`../TODO.md`](../TODO.md) のPhase 4セクションを参照してください。

---

**開始日**: 2026年1月6日（予定）
