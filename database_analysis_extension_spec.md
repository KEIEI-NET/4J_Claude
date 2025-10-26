# データベース特化型分析機能 拡張仕様書

## 1. データベース関連バグの課題分析

### 1.1 典型的なデータベースバグパターン

プロジェクトで発生しているデータベース関連バグの典型例を分類いたしました:

| バグカテゴリ | 発生頻度 | 影響度 | 検出難易度 |
|------------|---------|--------|-----------|
| N+1クエリ問題 | 高 | 中 | 中 |
| コネクションプール枯渇 | 中 | 高 | 高 |
| トランザクション境界の誤り | 高 | 高 | 高 |
| インデックス不足によるスロークエリ | 高 | 中 | 中 |
| データ不整合 (分散トランザクション) | 中 | 高 | 高 |
| キャッシュ同期の問題 (Redis) | 中 | 中 | 高 |
| Cassandra整合性レベルの誤設定 | 低 | 高 | 高 |
| Elasticsearch検索条件の誤り | 中 | 中 | 低 |
| デッドロック | 低 | 高 | 高 |
| リソースリーク (未クローズ接続) | 中 | 高 | 中 |

### 1.2 対象データベースの特性

#### Cassandra
- **特性**: 分散NoSQL、AP型(可用性・分断耐性重視)
- **主なバグ**: 整合性レベルの誤設定、Partition keyの設計ミス、Tombstoneの蓄積
- **検出対象**: CQL文、整合性レベル、バッチ処理、非同期処理

#### Elasticsearch
- **特性**: 分散検索エンジン、全文検索
- **主なバグ**: 複雑なクエリ、インデックス設計、シャード不均衡
- **検出対象**: Search API呼び出し、インデックス操作、バルク処理

#### Redis
- **特性**: インメモリキャッシュ、Key-Value Store
- **主なバグ**: キャッシュ無効化漏れ、TTL設定ミス、メモリ枯渇
- **検出対象**: キャッシュ操作、キー命名規則、Pub/Sub

#### MySQL / SQL Server
- **特性**: RDBMS、ACID保証
- **主なバグ**: SQLインジェクション、トランザクション管理、ロック競合
- **検出対象**: SQL文、トランザクション境界、接続管理

---

## 2. 拡張データモデル設計

### 2.1 新規ノードタイプ

#### 2.1.1 DatabaseQueryノード
```cypher
(:DatabaseQuery {
  id: "query_uuid",
  queryText: "SELECT * FROM users WHERE email = ?",
  queryType: "SELECT|INSERT|UPDATE|DELETE|CQL|DSL",
  database: "mysql|sqlserver|cassandra|elasticsearch|redis",
  isPrepared: true,
  hasParameters: true,
  complexity: 5.2,  // クエリ複雑度
  estimatedRows: 1000,  // 想定返却行数
  hasIndex: true,  // インデックス使用有無
  executionTime: 0.025,  // 実行時間(秒) - プロファイリングから
  lineNumber: 145
})
```

#### 2.1.2 DatabaseEntityノード (テーブル/コレクション)
```cypher
(:DatabaseEntity {
  id: "entity_uuid",
  name: "users",
  type: "table|collection|index|cache_key",
  database: "mysql",
  schema: "public",
  estimatedSize: 1000000,  // レコード数
  hasIndex: true,
  primaryKey: ["id"],
  foreignKeys: ["company_id"],
  accessFrequency: "high|medium|low"
})
```

#### 2.1.3 TransactionBoundaryノード
```cypher
(:TransactionBoundary {
  id: "tx_uuid",
  type: "begin|commit|rollback",
  isolationLevel: "READ_COMMITTED|SERIALIZABLE|...",
  isDistributed: false,
  lineNumber: 89,
  methodId: "com.example.Service.updateUser"
})
```

#### 2.1.4 ConnectionPoolノード
```cypher
(:ConnectionPool {
  id: "pool_uuid",
  database: "mysql",
  maxConnections: 20,
  minConnections: 5,
  timeout: 30000,
  configFile: "/config/database.yml",
  usageLocations: ["ServiceA.java", "ServiceB.java"]
})
```

#### 2.1.5 CacheOperationノード (Redis特化)
```cypher
(:CacheOperation {
  id: "cache_op_uuid",
  operation: "get|set|delete|expire",
  keyPattern: "user:*:profile",
  ttl: 3600,
  isDistributed: true,
  lineNumber: 67
})
```

#### 2.1.6 DataAccessLayerノード (DAO/Repository)
```cypher
(:DataAccessLayer {
  id: "dao_uuid",
  name: "UserRepository",
  type: "DAO|Repository|Mapper",
  framework: "MyBatis|Hibernate|Spring Data|Custom",
  database: "mysql",
  entityName: "User",
  methods: ["findById", "save", "update", "delete"]
})
```

### 2.2 新規関係性タイプ

#### 2.2.1 EXECUTES_QUERY
```cypher
(:Method)-[:EXECUTES_QUERY {
  frequency: 5,  // 静的解析での出現回数
  isConditional: false,
  isInLoop: true,  // ループ内での実行
  isAsync: false,
  lineNumber: 145
}]->(:DatabaseQuery)
```

#### 2.2.2 ACCESSES_ENTITY
```cypher
(:DatabaseQuery)-[:ACCESSES_ENTITY {
  operation: "read|write|readwrite",
  isIndexed: true,
  estimatedCost: 1.5  // クエリコスト
}]->(:DatabaseEntity)
```

#### 2.2.3 WITHIN_TRANSACTION
```cypher
(:DatabaseQuery)-[:WITHIN_TRANSACTION {
  position: 2,  // トランザクション内での順序
  canRollback: true
}]->(:TransactionBoundary)
```

#### 2.2.4 USES_CONNECTION_POOL
```cypher
(:DataAccessLayer)-[:USES_CONNECTION_POOL {
  isDirect: false,
  framework: "Spring"
}]->(:ConnectionPool)
```

#### 2.2.5 INVALIDATES_CACHE
```cypher
(:Method)-[:INVALIDATES_CACHE {
  strategy: "explicit|implicit|pattern",
  lineNumber: 89
}]->(:CacheOperation)
```

#### 2.2.6 DEPENDS_ON_CACHE
```cypher
(:Method)-[:DEPENDS_ON_CACHE {
  isCritical: true,  // キャッシュミス時の影響
  fallbackExists: true,
  lineNumber: 45
}]->(:CacheOperation)
```

#### 2.2.7 CROSS_DATABASE_OPERATION
```cypher
(:Method)-[:CROSS_DATABASE_OPERATION {
  databases: ["mysql", "cassandra"],
  hasDistributedTx: false,  // 分散トランザクション有無
  consistencyRisk: "high|medium|low"
}]->(:Method)
```

---

## 3. データベース特化型パーサー拡張

### 3.1 SQL/CQL/DSL解析エンジン

#### 3.1.1 SQL解析 (MySQL/SQL Server)
```python
class SQLAnalyzer:
    def __init__(self):
        self.parser = sqlparse.Parser()
        
    def analyze_sql_in_code(self, file_path: str) -> List[DatabaseQuery]:
        """
        コード内のSQL文を抽出・解析
        """
        queries = []
        
        # パターン1: 文字列リテラル内のSQL
        sql_patterns = [
            r'\"(SELECT|INSERT|UPDATE|DELETE).*?\"',
            r'\'(SELECT|INSERT|UPDATE|DELETE).*?\'',
        ]
        
        # パターン2: MyBatis XMLマッピング
        mybatis_queries = self._parse_mybatis_xml(file_path)
        
        # パターン3: Hibernate HQL
        hql_queries = self._parse_hql(file_path)
        
        # パターン4: Spring Data Query annotations
        spring_queries = self._parse_spring_data_queries(file_path)
        
        for sql in all_queries:
            query_info = self._analyze_single_query(sql)
            queries.append(query_info)
            
        return queries
    
    def _analyze_single_query(self, sql: str) -> DatabaseQuery:
        """
        個別のSQLを詳細に解析
        """
        parsed = sqlparse.parse(sql)[0]
        
        # クエリタイプの判定
        query_type = self._get_query_type(parsed)
        
        # テーブル抽出
        tables = self._extract_tables(parsed)
        
        # WHERE句の分析
        where_clauses = self._analyze_where_clause(parsed)
        
        # JOINの検出
        joins = self._extract_joins(parsed)
        
        # サブクエリの検出
        subqueries = self._detect_subqueries(parsed)
        
        # インデックス使用の推定
        has_index = self._estimate_index_usage(tables, where_clauses)
        
        # N+1問題の可能性
        n_plus_one_risk = self._detect_n_plus_one_pattern(sql, context)
        
        return DatabaseQuery(
            queryText=sql,
            queryType=query_type,
            tables=tables,
            hasIndex=has_index,
            complexity=self._calculate_complexity(parsed),
            nPlusOneRisk=n_plus_one_risk
        )
    
    def _detect_n_plus_one_pattern(self, sql: str, context: CodeContext) -> bool:
        """
        N+1問題の検出
        """
        # ループ内でのSELECTクエリ実行を検出
        if context.is_in_loop and sql.strip().upper().startswith('SELECT'):
            # 外部キーに対するWHERE句を持つ
            if self._has_foreign_key_condition(sql):
                return True
        return False
```

#### 3.1.2 Cassandra CQL解析
```python
class CassandraAnalyzer:
    def analyze_cql(self, cql: str, context: CodeContext) -> CassandraQuery:
        """
        CQL固有の問題を検出
        """
        # Consistency Levelの取得
        consistency_level = self._extract_consistency_level(context)
        
        # Partition Keyの使用確認
        uses_partition_key = self._check_partition_key_usage(cql)
        
        # ALLOW FILTERINGの検出 (アンチパターン)
        has_allow_filtering = 'ALLOW FILTERING' in cql.upper()
        
        # バッチ処理のサイズチェック
        is_large_batch = self._check_batch_size(cql, context)
        
        # Tombstoneリスク
        tombstone_risk = self._assess_tombstone_risk(cql)
        
        return CassandraQuery(
            cql=cql,
            consistencyLevel=consistency_level,
            usesPartitionKey=uses_partition_key,
            hasAllowFiltering=has_allow_filtering,
            isLargeBatch=is_large_batch,
            tombstoneRisk=tombstone_risk
        )
    
    def _check_partition_key_usage(self, cql: str) -> bool:
        """
        WHERE句でPartition Keyが使用されているか確認
        """
        # データモデルとの照合が必要
        # ここではシンプルな検出ロジック
        where_clause = self._extract_where_clause(cql)
        # Partition Key定義と照合
        return True  # 実装は複雑
```

#### 3.1.3 Elasticsearch DSL解析
```python
class ElasticsearchAnalyzer:
    def analyze_es_query(self, query_dsl: dict, context: CodeContext) -> ESQuery:
        """
        Elasticsearch Query DSLを解析
        """
        # クエリの種類
        query_type = self._detect_query_type(query_dsl)
        
        # 複雑度の計算
        complexity = self._calculate_es_complexity(query_dsl)
        
        # フィルタリング vs クエリング
        uses_filter = 'filter' in json.dumps(query_dsl)
        
        # アグリゲーションの検出
        has_aggregation = 'aggs' in query_dsl
        
        # スクリプトの使用 (パフォーマンス懸念)
        uses_script = self._detect_script_usage(query_dsl)
        
        # ワイルドカードクエリ (アンチパターン)
        has_wildcard = self._detect_wildcard_query(query_dsl)
        
        return ESQuery(
            queryDsl=query_dsl,
            queryType=query_type,
            complexity=complexity,
            usesScript=uses_script,
            hasWildcard=has_wildcard,
            performanceRisk=self._assess_performance_risk(query_dsl)
        )
```

#### 3.1.4 Redis操作解析
```python
class RedisAnalyzer:
    def analyze_redis_operations(self, file_path: str) -> List[CacheOperation]:
        """
        Redisキャッシュ操作を解析
        """
        operations = []
        
        # Redisクライアント呼び出しを検出
        redis_calls = self._find_redis_calls(file_path)
        
        for call in redis_calls:
            # キャッシュキーのパターン抽出
            key_pattern = self._extract_key_pattern(call)
            
            # TTL設定の有無
            has_ttl = self._check_ttl_setting(call)
            
            # キャッシュ無効化の追跡
            invalidation_points = self._find_invalidation_points(key_pattern)
            
            # Cache-Aside vs Read/Write-Through検出
            cache_pattern = self._detect_cache_pattern(call)
            
            operations.append(CacheOperation(
                keyPattern=key_pattern,
                hasTTL=has_ttl,
                cachePattern=cache_pattern,
                invalidationPoints=invalidation_points
            ))
        
        return operations
    
    def _find_invalidation_points(self, key_pattern: str) -> List[str]:
        """
        特定のキャッシュキーを無効化する箇所を全て特定
        """
        # グラフDBクエリで関連する削除操作を検索
        query = """
        MATCH (cache:CacheOperation {keyPattern: $pattern, operation: 'delete'})
        MATCH (method:Method)-[:EXECUTES_CACHE_OP]->(cache)
        RETURN method.name as methodName, method.id as methodId
        """
        return neo4j_driver.execute_query(query, pattern=key_pattern)
```

### 3.2 トランザクション境界の自動検出

```python
class TransactionAnalyzer:
    def analyze_transactions(self, file_path: str) -> List[TransactionBoundary]:
        """
        トランザクション境界を自動検出
        """
        transactions = []
        
        # アノテーションベースの検出 (Spring @Transactional)
        spring_tx = self._detect_spring_transactional(file_path)
        
        # プログラマティックトランザクション
        programmatic_tx = self._detect_programmatic_tx(file_path)
        
        # トランザクション内のクエリを特定
        for tx in all_transactions:
            queries = self._find_queries_in_transaction(tx)
            
            # 分散トランザクションの検出
            is_distributed = self._check_distributed_tx(queries)
            
            # デッドロックリスクの評価
            deadlock_risk = self._assess_deadlock_risk(queries)
            
            transactions.append(TransactionBoundary(
                isolationLevel=tx.isolation,
                isDistributed=is_distributed,
                deadlockRisk=deadlock_risk,
                queries=queries
            ))
        
        return transactions
    
    def _assess_deadlock_risk(self, queries: List[DatabaseQuery]) -> str:
        """
        デッドロックのリスクを評価
        """
        # 複数テーブルへの書き込み
        write_tables = [q.tables for q in queries if q.is_write()]
        
        # ロック順序の不整合を検出
        if len(write_tables) > 1:
            # 他のトランザクションと比較
            return "high"
        
        return "low"
```

---

## 4. データベース特化型分析クエリ

### 4.1 N+1問題の検出

```cypher
// N+1問題の可能性があるメソッドを検出
MATCH (method:Method)-[exec:EXECUTES_QUERY]->(query:DatabaseQuery)
WHERE exec.isInLoop = true 
  AND query.queryType = 'SELECT'
  AND query.hasParameters = true
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN file.path, 
       class.name, 
       method.name,
       query.queryText,
       exec.frequency as loopExecutionCount,
       'N+1 Problem Risk' as issue
ORDER BY loopExecutionCount DESC
```

### 4.2 トランザクション未管理のDB操作

```cypher
// トランザクション外でのDB書き込み操作
MATCH (method:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
WHERE query.queryType IN ['INSERT', 'UPDATE', 'DELETE']
  AND NOT (query)-[:WITHIN_TRANSACTION]->(:TransactionBoundary)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN file.path,
       class.name,
       method.name,
       query.queryText,
       'Missing Transaction Boundary' as issue
```

### 4.3 キャッシュ無効化漏れの検出

```cypher
// データ更新するがキャッシュ無効化しないメソッド
MATCH (updateMethod:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
WHERE query.queryType IN ['INSERT', 'UPDATE', 'DELETE']
MATCH (query)-[:ACCESSES_ENTITY]->(entity:DatabaseEntity)
MATCH (readMethod:Method)-[:DEPENDS_ON_CACHE]->(cache:CacheOperation)
WHERE cache.keyPattern CONTAINS entity.name
  AND NOT (updateMethod)-[:INVALIDATES_CACHE]->()
RETURN updateMethod.name as updatingMethod,
       entity.name as affectedEntity,
       readMethod.name as cachedReadMethod,
       'Cache Invalidation Missing' as issue
```

### 4.4 コネクションリークの検出

```cypher
// コネクションを開くが明示的にクローズしないメソッド
MATCH (method:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
MATCH (method)-[:USES_CONNECTION_POOL]->(pool:ConnectionPool)
WHERE NOT EXISTS {
  MATCH (method)-[:CONTAINS]->(stmt)
  WHERE stmt.type = 'try-with-resources' 
     OR stmt.type = 'finally-close'
}
RETURN method.name,
       pool.database,
       'Potential Connection Leak' as issue
```

### 4.5 クロスデータベース整合性リスク

```cypher
// 複数のデータベースを操作するが分散トランザクション未使用
MATCH (method:Method)-[:EXECUTES_QUERY]->(q1:DatabaseQuery)
MATCH (method)-[:EXECUTES_QUERY]->(q2:DatabaseQuery)
WHERE q1.database <> q2.database
  AND q1.queryType IN ['INSERT', 'UPDATE', 'DELETE']
  AND q2.queryType IN ['INSERT', 'UPDATE', 'DELETE']
  AND NOT (method)-[:CROSS_DATABASE_OPERATION {hasDistributedTx: true}]->()
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN file.path,
       method.name,
       collect(DISTINCT q1.database) as databases,
       'Cross-Database Consistency Risk' as issue
```

### 4.6 インデックス不足の検出

```cypher
// インデックスが使用されていない高頻度クエリ
MATCH (method:Method)-[exec:EXECUTES_QUERY]->(query:DatabaseQuery)
WHERE query.hasIndex = false
  AND exec.frequency > 10
  AND query.estimatedRows > 1000
MATCH (query)-[:ACCESSES_ENTITY]->(entity:DatabaseEntity)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN file.path,
       method.name,
       query.queryText,
       entity.name as table,
       query.estimatedRows as rowCount,
       'Missing Index - Performance Issue' as issue
ORDER BY query.estimatedRows DESC
```

### 4.7 Cassandra整合性レベルの不整合

```cypher
// 読み込みと書き込みで整合性レベルが合わない
MATCH (readMethod:Method)-[:EXECUTES_QUERY]->(readQuery:DatabaseQuery)
WHERE readQuery.database = 'cassandra'
  AND readQuery.queryType = 'SELECT'
MATCH (writeMethod:Method)-[:EXECUTES_QUERY]->(writeQuery:DatabaseQuery)
WHERE writeQuery.database = 'cassandra'
  AND writeQuery.queryType IN ['INSERT', 'UPDATE']
MATCH (readQuery)-[:ACCESSES_ENTITY]->(entity:DatabaseEntity)
MATCH (writeQuery)-[:ACCESSES_ENTITY]->(entity)
WHERE readQuery.consistencyLevel <> writeQuery.consistencyLevel
RETURN readMethod.name,
       writeMethod.name,
       entity.name,
       readQuery.consistencyLevel as readCL,
       writeQuery.consistencyLevel as writeCL,
       'Consistency Level Mismatch' as issue
```

### 4.8 Elasticsearch重いクエリの検出

```cypher
// 複雑すぎるElasticsearchクエリ
MATCH (method:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
WHERE query.database = 'elasticsearch'
  AND query.complexity > 7.0
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN file.path,
       method.name,
       query.complexity,
       query.usesScript as hasScript,
       query.hasWildcard as hasWildcard,
       'Complex Elasticsearch Query' as issue
ORDER BY query.complexity DESC
```

---

## 5. データベースバグ影響範囲分析API

### 5.1 新規APIエンドポイント

```python
from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

@app.post("/api/v1/database/analyze/impact")
async def analyze_database_impact(
    query_id: str,
    depth: int = 3
):
    """
    特定のデータベースクエリの変更が及ぼす影響を分析
    """
    cypher_query = """
    MATCH (query:DatabaseQuery {id: $queryId})
    MATCH (query)-[:ACCESSES_ENTITY]->(entity:DatabaseEntity)
    
    // このエンティティにアクセスする他のクエリ
    MATCH (otherQuery:DatabaseQuery)-[:ACCESSES_ENTITY]->(entity)
    MATCH (method:Method)-[:EXECUTES_QUERY]->(otherQuery)
    MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    
    // キャッシュ依存関係
    OPTIONAL MATCH (method)-[:DEPENDS_ON_CACHE]->(cache:CacheOperation)
    WHERE cache.keyPattern CONTAINS entity.name
    
    RETURN DISTINCT 
        file.path,
        class.name,
        method.name,
        otherQuery.queryText,
        collect(cache.keyPattern) as affectedCaches
    """
    
    results = neo4j_driver.execute_query(cypher_query, queryId=query_id)
    
    return {
        "query_id": query_id,
        "affected_methods": results,
        "cache_invalidation_required": [r['affectedCaches'] for r in results if r['affectedCaches']]
    }

@app.get("/api/v1/database/detect/n-plus-one")
async def detect_n_plus_one_problems(
    database: Optional[str] = None,
    severity: str = Query("all", regex="^(all|high|medium|low)$")
):
    """
    N+1問題を検出
    """
    cypher_query = """
    MATCH (method:Method)-[exec:EXECUTES_QUERY]->(query:DatabaseQuery)
    WHERE exec.isInLoop = true 
      AND query.queryType = 'SELECT'
      AND ($database IS NULL OR query.database = $database)
    MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    
    // ループの深さを計算
    OPTIONAL MATCH loopPath = (method)-[:CALLS*1..3]->(loopMethod:Method)
    WHERE loopMethod.name CONTAINS 'forEach' OR loopMethod.name CONTAINS 'map'
    
    RETURN file.path,
           class.name,
           method.name,
           query.queryText,
           exec.frequency as executionCount,
           length(loopPath) as loopDepth,
           CASE 
             WHEN exec.frequency > 100 THEN 'high'
             WHEN exec.frequency > 50 THEN 'medium'
             ELSE 'low'
           END as severity
    ORDER BY executionCount DESC
    """
    
    results = neo4j_driver.execute_query(cypher_query, database=database)
    
    if severity != "all":
        results = [r for r in results if r['severity'] == severity]
    
    return {
        "n_plus_one_issues": results,
        "total_count": len(results),
        "recommendations": [
            "Use eager loading / JOIN FETCH",
            "Implement batch fetching",
            "Consider caching frequently accessed data"
        ]
    }

@app.get("/api/v1/database/detect/missing-transactions")
async def detect_missing_transactions(database: Optional[str] = None):
    """
    トランザクション境界が欠けているDB書き込み操作を検出
    """
    cypher_query = """
    MATCH (method:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
    WHERE query.queryType IN ['INSERT', 'UPDATE', 'DELETE']
      AND NOT (query)-[:WITHIN_TRANSACTION]->(:TransactionBoundary)
      AND ($database IS NULL OR query.database = $database)
    MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    RETURN file.path,
           class.name,
           method.name,
           query.queryText,
           query.database
    """
    
    results = neo4j_driver.execute_query(cypher_query, database=database)
    
    return {
        "missing_transactions": results,
        "total_count": len(results),
        "risk_level": "high" if len(results) > 0 else "low"
    }

@app.get("/api/v1/database/detect/cache-inconsistency")
async def detect_cache_inconsistency():
    """
    キャッシュ無効化漏れを検出
    """
    cypher_query = """
    MATCH (updateMethod:Method)-[:EXECUTES_QUERY]->(query:DatabaseQuery)
    WHERE query.queryType IN ['INSERT', 'UPDATE', 'DELETE']
    MATCH (query)-[:ACCESSES_ENTITY]->(entity:DatabaseEntity)
    
    // このエンティティをキャッシュしているメソッド
    MATCH (readMethod:Method)-[:DEPENDS_ON_CACHE]->(cache:CacheOperation)
    WHERE cache.keyPattern CONTAINS entity.name
    
    // 無効化処理がない
    WHERE NOT (updateMethod)-[:INVALIDATES_CACHE]->()
    
    MATCH (updateMethod)<-[:CONTAINS]-(updateClass:Class)<-[:CONTAINS]-(updateFile:File)
    MATCH (readMethod)<-[:CONTAINS]-(readClass:Class)<-[:CONTAINS]-(readFile:File)
    
    RETURN updateFile.path as updateLocation,
           updateMethod.name as updateMethod,
           entity.name as affectedEntity,
           readFile.path as cachedLocation,
           readMethod.name as cachedMethod,
           cache.keyPattern as cacheKey
    """
    
    results = neo4j_driver.execute_query(cypher_query)
    
    return {
        "cache_inconsistencies": results,
        "total_count": len(results),
        "recommendations": [
            "Add cache invalidation after data modification",
            "Use cache-aside pattern consistently",
            "Consider event-driven cache invalidation"
        ]
    }

@app.get("/api/v1/database/analyze/connection-usage")
async def analyze_connection_pool_usage():
    """
    コネクションプールの使用状況を分析
    """
    cypher_query = """
    MATCH (pool:ConnectionPool)
    MATCH (dal:DataAccessLayer)-[:USES_CONNECTION_POOL]->(pool)
    MATCH (method:Method)-[:CALLS]->(dalMethod:Method)
    WHERE dalMethod.name IN dal.methods
    
    WITH pool, 
         count(DISTINCT method) as usageCount,
         collect(DISTINCT method.name) as usageMethods
    
    RETURN pool.database,
           pool.maxConnections,
           usageCount,
           CASE 
             WHEN usageCount > pool.maxConnections * 0.8 THEN 'high'
             WHEN usageCount > pool.maxConnections * 0.5 THEN 'medium'
             ELSE 'low'
           END as utilizationLevel,
           usageMethods[0..10] as topMethods
    """
    
    results = neo4j_driver.execute_query(cypher_query)
    
    return {
        "connection_pools": results,
        "warnings": [
            r for r in results if r['utilizationLevel'] == 'high'
        ]
    }

@app.post("/api/v1/database/simulate/table-change")
async def simulate_table_change(
    table_name: str,
    database: str,
    change_type: str = Query(..., regex="^(add_column|remove_column|rename|delete)$")
):
    """
    テーブル変更の影響をシミュレーション
    """
    cypher_query = """
    MATCH (entity:DatabaseEntity {name: $tableName, database: $database})
    
    // このテーブルにアクセスするクエリ
    MATCH (query:DatabaseQuery)-[:ACCESSES_ENTITY]->(entity)
    MATCH (method:Method)-[:EXECUTES_QUERY]->(query)
    MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    
    // 依存するキャッシュ
    OPTIONAL MATCH (cacheMethod:Method)-[:DEPENDS_ON_CACHE]->(cache:CacheOperation)
    WHERE cache.keyPattern CONTAINS entity.name
    
    // このメソッドから呼ばれる上流
    OPTIONAL MATCH upstream = (caller:Method)-[:CALLS*1..3]->(method)
    
    RETURN file.path,
           class.name,
           method.name,
           query.queryText,
           query.queryType,
           collect(DISTINCT cache.keyPattern) as affectedCaches,
           count(DISTINCT caller) as upstreamCallers
    ORDER BY upstreamCallers DESC
    """
    
    results = neo4j_driver.execute_query(
        cypher_query, 
        tableName=table_name, 
        database=database
    )
    
    # 影響度スコアの計算
    impact_score = sum([
        len(r['affectedCaches']) * 2 +  # キャッシュ影響
        r['upstreamCallers']  # 呼び出し元の数
        for r in results
    ])
    
    return {
        "table_name": table_name,
        "change_type": change_type,
        "affected_queries": len(results),
        "affected_files": len(set(r['file.path'] for r in results)),
        "impact_score": impact_score,
        "impact_level": "high" if impact_score > 50 else "medium" if impact_score > 20 else "low",
        "details": results,
        "recommendations": generate_change_recommendations(change_type, results)
    }

def generate_change_recommendations(change_type: str, affected: List[dict]) -> List[str]:
    """
    変更タイプに応じた推奨事項を生成
    """
    recommendations = []
    
    if change_type == "add_column":
        recommendations.append("既存のSELECT * は影響を受けない可能性がありますが、確認が必要です")
        recommendations.append("アプリケーションレイヤーでのカラムマッピングを更新してください")
    elif change_type == "remove_column":
        recommendations.append(f"{len(affected)} 箇所のクエリで削除されるカラムを参照しています")
        recommendations.append("該当するクエリを先に修正してからマイグレーションを実行してください")
    elif change_type == "rename":
        recommendations.append("すべてのクエリとORMマッピングの更新が必要です")
        recommendations.append("Blue-Green deploymentを検討してください")
    
    return recommendations

@app.get("/api/v1/database/detect/cross-database-issues")
async def detect_cross_database_issues():
    """
    複数データベースにまたがる整合性問題を検出
    """
    cypher_query = """
    MATCH (method:Method)-[:EXECUTES_QUERY]->(q1:DatabaseQuery)
    MATCH (method)-[:EXECUTES_QUERY]->(q2:DatabaseQuery)
    WHERE q1.database <> q2.database
      AND (q1.queryType IN ['INSERT', 'UPDATE', 'DELETE'] 
           OR q2.queryType IN ['INSERT', 'UPDATE', 'DELETE'])
    MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    
    WITH method, file, class, 
         collect(DISTINCT q1.database) + collect(DISTINCT q2.database) as databases,
         count(*) as queryCount
    
    WHERE NOT (method)-[:CROSS_DATABASE_OPERATION {hasDistributedTx: true}]->()
    
    RETURN file.path,
           class.name,
           method.name,
           databases,
           queryCount,
           'Missing Distributed Transaction' as issue
    """
    
    results = neo4j_driver.execute_query(cypher_query)
    
    return {
        "cross_database_issues": results,
        "total_count": len(results),
        "risk_assessment": "HIGH - Data inconsistency possible",
        "recommendations": [
            "Implement distributed transaction (2PC or Saga pattern)",
            "Add compensating transactions for rollback",
            "Consider eventual consistency with event sourcing"
        ]
    }
```

---

## 6. データベース特化型UI拡張

### 6.1 データベースダッシュボード

```typescript
// DatabaseDashboard.tsx
interface DatabaseMetrics {
  database: string;
  queryCount: number;
  nPlusOneIssues: number;
  missingTransactions: number;
  cacheInconsistencies: number;
  connectionPoolUtilization: number;
}

export const DatabaseDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DatabaseMetrics[]>([]);
  
  useEffect(() => {
    fetchDatabaseMetrics().then(setMetrics);
  }, []);
  
  return (
    <div className="database-dashboard">
      <h1>データベース品質ダッシュボード</h1>
      
      {/* データベース別の問題サマリー */}
      <div className="db-summary-grid">
        {metrics.map(db => (
          <Card key={db.database}>
            <h3>{db.database.toUpperCase()}</h3>
            <MetricBadge 
              label="N+1問題" 
              value={db.nPlusOneIssues} 
              severity={db.nPlusOneIssues > 10 ? 'high' : 'low'} 
            />
            <MetricBadge 
              label="トランザクション未管理" 
              value={db.missingTransactions}
              severity={db.missingTransactions > 0 ? 'high' : 'low'} 
            />
            <MetricBadge 
              label="キャッシュ不整合" 
              value={db.cacheInconsistencies}
              severity={db.cacheInconsistencies > 5 ? 'medium' : 'low'} 
            />
            <ProgressBar 
              label="接続プール使用率" 
              value={db.connectionPoolUtilization} 
            />
          </Card>
        ))}
      </div>
      
      {/* クエリ実行頻度のヒートマップ */}
      <QueryHeatmap />
      
      {/* データベース間の関係図 */}
      <CrossDatabaseDependencyGraph />
    </div>
  );
};
```

### 6.2 クエリ影響範囲ビジュアライザー

```typescript
// QueryImpactVisualizer.tsx
interface QueryImpactProps {
  queryId: string;
}

export const QueryImpactVisualizer: React.FC<QueryImpactProps> = ({ queryId }) => {
  const [impactData, setImpactData] = useState(null);
  
  useEffect(() => {
    fetch(`/api/v1/database/analyze/impact`, {
      method: 'POST',
      body: JSON.stringify({ query_id: queryId, depth: 5 })
    })
    .then(res => res.json())
    .then(setImpactData);
  }, [queryId]);
  
  if (!impactData) return <Loading />;
  
  return (
    <div className="query-impact-visualizer">
      <h2>クエリ影響範囲分析</h2>
      
      {/* 中心にクエリ、放射状に影響を受けるメソッド */}
      <ForceDirectedGraph
        centerNode={{
          id: queryId,
          type: 'query',
          label: impactData.queryText
        }}
        affectedNodes={impactData.affected_methods.map(m => ({
          id: m.method_id,
          type: 'method',
          label: `${m.class_name}.${m.method_name}`,
          file: m.file_path
        }))}
      />
      
      {/* キャッシュ無効化の必要性 */}
      {impactData.cache_invalidation_required.length > 0 && (
        <Alert severity="warning">
          <AlertTitle>キャッシュ無効化が必要</AlertTitle>
          <ul>
            {impactData.cache_invalidation_required.map(cache => (
              <li key={cache}>{cache}</li>
            ))}
          </ul>
        </Alert>
      )}
      
      {/* テーブル影響範囲 */}
      <TableImpactSummary data={impactData} />
    </div>
  );
};
```

### 6.3 N+1問題の可視化

```typescript
// NPlusOneDetector.tsx
export const NPlusOneDetector: React.FC = () => {
  const [issues, setIssues] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);
  
  useEffect(() => {
    fetch(`/api/v1/database/detect/n-plus-one?database=${selectedDatabase || 'all'}`)
      .then(res => res.json())
      .then(data => setIssues(data.n_plus_one_issues));
  }, [selectedDatabase]);
  
  return (
    <div className="n-plus-one-detector">
      <h2>N+1問題検出</h2>
      
      <DatabaseFilter onChange={setSelectedDatabase} />
      
      <DataGrid
        columns={[
          { field: 'file.path', headerName: 'ファイル', width: 300 },
          { field: 'method.name', headerName: 'メソッド', width: 200 },
          { field: 'executionCount', headerName: '実行回数', width: 100 },
          { field: 'severity', headerName: '重要度', width: 100,
            renderCell: (params) => (
              <Chip 
                label={params.value} 
                color={params.value === 'high' ? 'error' : 'warning'} 
              />
            )
          },
          { field: 'query.queryText', headerName: 'クエリ', width: 400 }
        ]}
        rows={issues}
        onRowClick={(params) => navigateToCode(params.row['file.path'])}
      />
      
      <RecommendationPanel
        title="推奨される修正方法"
        items={[
          "Eager LoadingまたはJOIN FETCHを使用",
          "バッチフェッチングの実装",
          "頻繁にアクセスされるデータのキャッシュ"
        ]}
      />
    </div>
  );
};
```

---

## 7. データベース特化型の自動化ワークフロー

### 7.1 CI/CD統合

```yaml
# .github/workflows/database-analysis.yml
name: Database Impact Analysis

on:
  pull_request:
    paths:
      - '**/*.java'
      - '**/*.ts'
      - '**/*.cs'
      - '**/*.go'
      - '**/mapper/**'  # MyBatis
      - '**/repositories/**'

jobs:
  analyze-database-changes:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Database Analysis
        run: |
          docker-compose up -d neo4j
          python scripts/analyze_db_changes.py \
            --changed-files="${{ github.event.pull_request.changed_files }}"
      
      - name: Detect N+1 Problems
        id: n_plus_one
        run: |
          curl -X GET "http://localhost:8000/api/v1/database/detect/n-plus-one?severity=high" \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            > n_plus_one_report.json
      
      - name: Check Transaction Boundaries
        id: transactions
        run: |
          curl -X GET "http://localhost:8000/api/v1/database/detect/missing-transactions" \
            > transaction_report.json
      
      - name: Comment on PR
        uses: actions/github-script@v5
        with:
          script: |
            const nPlusOne = require('./n_plus_one_report.json');
            const transactions = require('./transaction_report.json');
            
            let comment = '## データベース影響分析レポート\n\n';
            
            if (nPlusOne.total_count > 0) {
              comment += `⚠️ **N+1問題検出**: ${nPlusOne.total_count}件\n\n`;
              comment += '詳細:\n';
              nPlusOne.n_plus_one_issues.slice(0, 5).forEach(issue => {
                comment += `- \`${issue['file.path']}\`: ${issue['method.name']}\n`;
              });
            }
            
            if (transactions.total_count > 0) {
              comment += `\n🔴 **トランザクション未管理**: ${transactions.total_count}件\n`;
            }
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
      
      - name: Fail if Critical Issues
        run: |
          if [ $(jq '.total_count' transaction_report.json) -gt 0 ]; then
            echo "❌ Critical: トランザクション未管理のDB書き込みが検出されました"
            exit 1
          fi
```

### 7.2 定期レポート生成

```python
# scripts/generate_weekly_db_report.py
import asyncio
from datetime import datetime, timedelta
from jinja2 import Template

async def generate_weekly_report():
    """
    週次データベース品質レポートを生成
    """
    # 各種メトリクスを取得
    n_plus_one = await fetch_n_plus_one_issues()
    cache_issues = await fetch_cache_inconsistencies()
    transaction_issues = await fetch_missing_transactions()
    connection_usage = await fetch_connection_pool_usage()
    
    # トレンド分析
    last_week = await fetch_last_week_metrics()
    trend = calculate_trend(last_week, {
        'n_plus_one': len(n_plus_one),
        'cache': len(cache_issues),
        'transactions': len(transaction_issues)
    })
    
    # レポート生成
    template = Template('''
    # データベース品質週次レポート
    
    **期間**: {{ start_date }} - {{ end_date }}
    
    ## サマリー
    
    | メトリクス | 今週 | 先週 | 変化 |
    |----------|------|------|------|
    | N+1問題 | {{ metrics.n_plus_one }} | {{ last_week.n_plus_one }} | {{ trend.n_plus_one }} |
    | キャッシュ不整合 | {{ metrics.cache }} | {{ last_week.cache }} | {{ trend.cache }} |
    | トランザクション未管理 | {{ metrics.transactions }} | {{ last_week.transactions }} | {{ trend.transactions }} |
    
    ## 重要度の高い問題 Top 10
    
    {% for issue in top_issues %}
    ### {{ loop.index }}. {{ issue.file }}
    - **タイプ**: {{ issue.type }}
    - **影響範囲**: {{ issue.impact_score }}
    - **推奨対応**: {{ issue.recommendation }}
    {% endfor %}
    
    ## データベース別の統計
    
    ### MySQL
    - クエリ数: {{ db_stats.mysql.query_count }}
    - 平均複雑度: {{ db_stats.mysql.avg_complexity }}
    
    ### Cassandra
    - CQL実行数: {{ db_stats.cassandra.query_count }}
    - Consistency Level違反: {{ db_stats.cassandra.cl_violations }}
    
    ### Elasticsearch
    - 検索クエリ数: {{ db_stats.elasticsearch.query_count }}
    - 複雑なクエリ: {{ db_stats.elasticsearch.complex_queries }}
    
    ### Redis
    - キャッシュ操作数: {{ db_stats.redis.operation_count }}
    - TTL未設定: {{ db_stats.redis.no_ttl_count }}
    
    ## 推奨アクション
    
    {% for action in recommended_actions %}
    - [ ] {{ action.description }} (優先度: {{ action.priority }})
    {% endfor %}
    ''')
    
    report = template.render(
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d'),
        metrics={
            'n_plus_one': len(n_plus_one),
            'cache': len(cache_issues),
            'transactions': len(transaction_issues)
        },
        last_week=last_week,
        trend=trend,
        top_issues=get_top_issues(n_plus_one, cache_issues, transaction_issues),
        db_stats=await fetch_db_statistics(),
        recommended_actions=generate_recommended_actions()
    )
    
    # レポートを保存・送信
    save_report(report)
    send_to_slack(report)
    send_email(report)

if __name__ == '__main__':
    asyncio.run(generate_weekly_report())
```

---

## 8. 実装優先度とロードマップ

### フェーズ1: 基本的なDB解析 (Week 1-3)
**目標**: SQLクエリの基本的な検出と関係構築

- [ ] SQL/CQLパーサーの実装
- [ ] DatabaseQueryノードの作成
- [ ] EXECUTES_QUERY関係の構築
- [ ] 基本的なN+1問題の検出

**成果物**:
- SQL解析エンジン
- Neo4jへのDB関係データ投入
- N+1問題検出API

### フェーズ2: トランザクション解析 (Week 4-5)
**目標**: トランザクション境界の検出

- [ ] @Transactionalアノテーション解析
- [ ] プログラマティックトランザクション検出
- [ ] TransactionBoundaryノードの作成
- [ ] トランザクション未管理の検出

**成果物**:
- トランザクション解析モジュール
- トランザクション検出API

### フェーズ3: キャッシュ解析 (Week 6-7)
**目標**: Redisキャッシュの追跡

- [ ] Redis操作の検出
- [ ] CacheOperationノードの作成
- [ ] キャッシュ無効化追跡
- [ ] キャッシュ不整合検出

**成果物**:
- キャッシュ解析エンジン
- キャッシュ整合性チェックAPI

### フェーズ4: 複数DB対応 (Week 8-10)
**目標**: Cassandra、Elasticsearch特化機能

- [ ] Cassandra CQL解析
- [ ] Elasticsearch DSL解析
- [ ] 整合性レベル検証
- [ ] クロスDB操作の検出

**成果物**:
- マルチDB解析対応
- DB特化型問題検出

### フェーズ5: UI開発 (Week 11-13)
**目標**: データベース専用ダッシュボード

- [ ] データベースダッシュボード
- [ ] クエリ影響範囲ビジュアライザー
- [ ] N+1問題リスト表示
- [ ] レポート生成機能

**成果物**:
- Webダッシュボード
- インタラクティブなグラフ表示

### フェーズ6: CI/CD統合 (Week 14-15)
**目標**: 自動化とワークフロー統合

- [ ] GitHub Actions統合
- [ ] PR自動コメント機能
- [ ] 週次レポート自動生成
- [ ] Slack通知

**成果物**:
- CI/CDパイプライン
- 自動レポート生成

---

## 9. 成功指標 (データベース特化)

### 9.1 検出精度

| 問題タイプ | 目標検出率 | 誤検出率目標 |
|----------|-----------|------------|
| N+1問題 | > 90% | < 10% |
| トランザクション未管理 | > 95% | < 5% |
| キャッシュ不整合 | > 85% | < 15% |
| インデックス不足 | > 80% | < 20% |

### 9.2 ビジネスインパクト

| 指標 | 目標 | 測定方法 |
|-----|------|---------|
| データベースバグ検出時間 | 90%短縮 | 1時間 → 6分 |
| 本番障害の事前検出 | 80%以上 | リリース前の検出率 |
| クエリパフォーマンス改善 | 平均50%向上 | レスポンスタイム測定 |
| データ不整合の削減 | 70%削減 | インシデント数 |

---

## 10. 次のステップ

### 即座に確認が必要な事項

1. **既存のORMフレームワーク**
   - 使用しているORM/データアクセスフレームワークは何でしょうか?
     - Hibernate / JPA (Java)
     - MyBatis (Java)
     - Entity Framework (C#)
     - GORM (Go)
     - TypeORM (TypeScript)

2. **データベース接続管理**
   - コネクションプールの設定ファイルの場所は?
   - 各データベースの接続数制限は?

3. **既知の問題**
   - 現在最も頻繁に発生しているデータベース関連のバグは何でしょうか?
   - 直近で大きな影響を与えたデータベースインシデントは?

4. **優先度**
   - 5つのデータベースの中で、最も問題が多いのはどれでしょうか?
   - 最初に分析すべきデータベースの優先順位は?

### プロトタイプ開発の提案

まずは1つのデータベース(例: MySQL)に絞った小規模プロトタイプを2週間で開発し、効果を検証することをご提案します。

**プロトタイプスコープ**:
- MySQL関連のN+1問題検出
- トランザクション境界チェック
- 簡易ダッシュボード
- 100-200ファイル規模での動作確認

---

**本仕様書のバージョン**: v1.1 (Database Extension)  
**最終更新日**: 2025年10月26日
