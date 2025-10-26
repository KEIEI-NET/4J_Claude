# Cassandra特化型バグ分析システム 詳細仕様書

## 1. エグゼクティブサマリー

### 1.1 Cassandra特有の課題

Cassandraは分散NoSQLデータベースであり、RDBMS とは根本的に異なる設計思想を持ちます。そのため、以下のような特有の問題が発生しやすくなります:

| 問題カテゴリ | 発生頻度 | 影響度 | 検出難易度 | ビジネスインパクト |
|------------|---------|--------|-----------|------------------|
| 整合性レベル(CL)の誤設定 | 高 | 🔴 致命的 | 高 | データ不整合、読み取り失敗 |
| Partition Key設計ミス | 中 | 🔴 致命的 | 高 | ホットスポット、性能劣化 |
| ALLOW FILTERINGの使用 | 高 | 🟡 深刻 | 低 | クエリタイムアウト |
| Secondary Indexの誤用 | 中 | 🟡 深刻 | 中 | スキャン範囲拡大 |
| 大量バッチ処理 | 中 | 🟡 深刻 | 中 | コーディネーター負荷 |
| Tombstone蓄積 | 低 | 🟡 深刻 | 高 | 読み取り性能低下 |
| タイムアウト設定不足 | 高 | 🟠 中程度 | 中 | アプリケーションハング |
| Prepared Statementの未使用 | 高 | 🟠 中程度 | 低 | パース負荷増大 |

### 1.2 本システムの目的

Cassandra特有の問題を**コードレベル**で事前に検出し、本番障害を未然に防ぐことを目的とします。

**主要機能**:
1. **CQL静的解析**: コード内のCQLを抽出し、問題パターンを検出
2. **整合性レベル追跡**: 読み書きのCLを追跡し、不整合リスクを評価
3. **データモデル検証**: Partition Key使用の検証
4. **影響範囲分析**: テーブル変更時の影響を即座に特定
5. **パフォーマンスリスク評価**: クエリパターンからボトルネックを予測

---

## 2. Cassandra特化型データモデル

### 2.1 拡張ノードタイプ

#### 2.1.1 CassandraQueryノード
```cypher
(:CassandraQuery {
  id: "cql_uuid",
  cqlText: "SELECT * FROM users WHERE user_id = ? AND timestamp > ?",
  queryType: "SELECT|INSERT|UPDATE|DELETE|BATCH",
  
  // 整合性レベル
  consistencyLevel: "ONE|QUORUM|ALL|LOCAL_QUORUM|EACH_QUORUM",
  serialConsistency: "SERIAL|LOCAL_SERIAL",
  
  // クエリ特性
  usesPartitionKey: true,
  usesClusteringKey: true,
  hasAllowFiltering: false,
  usesSecondaryIndex: false,
  isPrepared: true,
  
  // バッチ関連
  isBatch: false,
  batchType: "LOGGED|UNLOGGED|COUNTER",
  batchSize: 0,  // バッチ内の操作数
  
  // パフォーマンス指標
  estimatedPartitions: 1,  // アクセスするパーティション数
  estimatedRows: 100,
  scanType: "single_partition|multi_partition|full_table",
  
  // TTL・Tombstone関連
  usesTTL: false,
  usesDelete: false,  // DELETE操作（Tombstone生成）
  
  lineNumber: 145,
  methodId: "com.example.CassandraDAO.findUser"
})
```

#### 2.1.2 CassandraTableノード
```cypher
(:CassandraTable {
  id: "table_uuid",
  keyspace: "user_data",
  tableName: "users",
  
  // データモデル定義
  partitionKeys: ["user_id"],
  clusteringKeys: ["timestamp"],
  clusteringOrder: "DESC",
  regularColumns: ["email", "name", "status"],
  
  // インデックス
  secondaryIndexes: ["email_idx"],
  materializedViews: ["users_by_email"],
  
  // 統計情報
  estimatedRowCount: 10000000,
  estimatedPartitionCount: 1000000,
  avgPartitionSize: 10,  // KB
  
  // 設定
  compactionStrategy: "SizeTieredCompactionStrategy|LeveledCompactionStrategy",
  gcGraceSeconds: 864000,
  
  // 使用頻度
  readFrequency: "high|medium|low",
  writeFrequency: "high|medium|low",
  
  // 問題の有無
  hasTombstoneWarning: false,
  hasHotPartitionWarning: false
})
```

#### 2.1.3 CassandraSessionノード
```cypher
(:CassandraSession {
  id: "session_uuid",
  clusterName: "production_cluster",
  contactPoints: ["10.0.1.1", "10.0.1.2", "10.0.1.3"],
  localDatacenter: "dc1",
  
  // 接続設定
  defaultConsistencyLevel: "LOCAL_QUORUM",
  defaultTimeout: 12000,  // ms
  maxConnections: 8,
  
  // 使用箇所
  usedByClasses: ["UserDAO", "OrderDAO"],
  configLocation: "/config/cassandra.yml"
})
```

#### 2.1.4 CassandraDataModelノード
```cypher
(:CassandraDataModel {
  id: "model_uuid",
  entityName: "User",
  mappingType: "manual|datastax_mapper|spring_data",
  
  // テーブルマッピング
  tableName: "users",
  keyspace: "user_data",
  
  // フィールドマッピング
  partitionKeyField: "userId",
  clusteringKeyFields: ["timestamp"],
  
  // アプリケーション層での使用
  usedInClasses: ["UserService", "UserRepository"]
})
```

### 2.2 Cassandra特化型関係性

#### 2.2.1 EXECUTES_CQL
```cypher
(:Method)-[:EXECUTES_CQL {
  frequency: 5,
  isConditional: false,
  isInLoop: false,  // ループ内での実行（危険）
  isAsync: true,
  lineNumber: 145,
  
  // 整合性レベルの動的設定
  clIsDynamic: false,  // 実行時に変更されるか
  clVariableName: "consistencyLevel"
}]->(:CassandraQuery)
```

#### 2.2.2 ACCESSES_CASSANDRA_TABLE
```cypher
(:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE {
  operation: "read|write|readwrite",
  usesPartitionKey: true,
  partitionKeyCount: 1,  // アクセスするパーティション数
  isFullScan: false,
  estimatedCost: 1.5
}]->(:CassandraTable)
```

#### 2.2.3 CONSISTENCY_MISMATCH
```cypher
(:CassandraQuery)-[:CONSISTENCY_MISMATCH {
  readCL: "ONE",
  writeCL: "QUORUM",
  riskLevel: "high|medium|low",
  dataLossRisk: true
}]->(:CassandraQuery)
```

#### 2.2.4 USES_CASSANDRA_SESSION
```cypher
(:Method)-[:USES_CASSANDRA_SESSION {
  isDirect: true,  // 直接使用 vs DAOレイヤー経由
  sessionVariable: "session"
}]->(:CassandraSession)
```

#### 2.2.5 HOT_PARTITION_RISK
```cypher
(:CassandraQuery)-[:HOT_PARTITION_RISK {
  accessPattern: "sequential|random|time_series",
  riskScore: 8.5,
  recommendation: "Add bucketing to partition key"
}]->(:CassandraTable)
```

---

## 3. Cassandra CQL解析エンジン

### 3.1 CQLパーサーの実装

#### 3.1.1 Java (DataStax Driver) 解析
```python
import javalang
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CassandraDriverCall:
    """DataStax Driver の呼び出し情報"""
    method_name: str
    cql_text: str
    consistency_level: Optional[str]
    is_prepared: bool
    is_async: bool
    line_number: int

class CassandraJavaAnalyzer:
    """
    JavaコードからCassandra操作を抽出
    """
    
    def __init__(self):
        self.driver_classes = [
            'Session',
            'CqlSession', 
            'Cluster',
            'PreparedStatement',
            'BoundStatement',
            'ResultSet'
        ]
        
    def analyze_java_file(self, file_path: str) -> List[CassandraDriverCall]:
        """
        Javaファイルを解析してCassandra操作を抽出
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = javalang.parse.parse(content)
        calls = []
        
        # Session.execute() の検出
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            if self._is_cassandra_call(node):
                call_info = self._extract_call_info(node, content)
                calls.append(call_info)
        
        return calls
    
    def _is_cassandra_call(self, node: javalang.tree.MethodInvocation) -> bool:
        """
        Cassandra関連の呼び出しか判定
        """
        if node.member in ['execute', 'executeAsync', 'prepare']:
            # session.execute() のような呼び出し
            return True
        return False
    
    def _extract_call_info(self, node, content: str) -> CassandraDriverCall:
        """
        呼び出し情報を詳細に抽出
        """
        # CQL文字列の抽出
        cql_text = self._extract_cql_from_arguments(node)
        
        # Consistency Levelの抽出
        consistency_level = self._extract_consistency_level(node, content)
        
        # Prepared Statement判定
        is_prepared = self._is_prepared_statement(node, content)
        
        # 非同期実行判定
        is_async = node.member == 'executeAsync'
        
        return CassandraDriverCall(
            method_name=node.member,
            cql_text=cql_text,
            consistency_level=consistency_level,
            is_prepared=is_prepared,
            is_async=is_async,
            line_number=node.position.line if hasattr(node, 'position') else 0
        )
    
    def _extract_cql_from_arguments(self, node) -> str:
        """
        メソッド引数からCQL文字列を抽出
        """
        if node.arguments:
            for arg in node.arguments:
                if isinstance(arg, javalang.tree.Literal):
                    # 文字列リテラル
                    return arg.value.strip('"\'')
                elif isinstance(arg, javalang.tree.MemberReference):
                    # 定数参照の場合は定数定義を探す
                    return self._resolve_constant(arg.member)
        return ""
    
    def _extract_consistency_level(self, node, content: str) -> Optional[str]:
        """
        Consistency Levelの設定を抽出
        
        パターン:
        1. statement.setConsistencyLevel(ConsistencyLevel.QUORUM)
        2. executeStatement(stmt, ConsistencyLevel.ONE)
        3. session.execute(SimpleStatement.builder(cql).setConsistencyLevel(...))
        """
        # SimpleStatementビルダーパターン
        if 'SimpleStatement.builder' in content:
            cl_match = re.search(
                r'setConsistencyLevel\(ConsistencyLevel\.(\w+)\)',
                content
            )
            if cl_match:
                return cl_match.group(1)
        
        # 直接設定パターン
        cl_match = re.search(
            r'ConsistencyLevel\.(\w+)',
            content[max(0, node.position.line - 5):node.position.line + 5]
        )
        if cl_match:
            return cl_match.group(1)
        
        return None
    
    def _is_prepared_statement(self, node, content: str) -> bool:
        """
        Prepared Statementの使用を判定
        """
        # session.prepare() の検出
        if 'prepare' in content:
            return True
        
        # PreparedStatement型の変数使用
        if 'PreparedStatement' in content:
            return True
        
        return False

class CassandraQueryAnalyzer:
    """
    CQL文を詳細に解析
    """
    
    def analyze_cql(self, cql: str) -> dict:
        """
        CQL文を解析して問題パターンを検出
        """
        cql_upper = cql.upper()
        
        result = {
            'query_type': self._get_query_type(cql_upper),
            'uses_partition_key': self._uses_partition_key(cql),
            'has_allow_filtering': 'ALLOW FILTERING' in cql_upper,
            'uses_secondary_index': self._uses_secondary_index(cql),
            'is_batch': 'BEGIN BATCH' in cql_upper,
            'scan_type': self._determine_scan_type(cql),
            'issues': []
        }
        
        # 問題パターンの検出
        if result['has_allow_filtering']:
            result['issues'].append({
                'severity': 'high',
                'type': 'ALLOW_FILTERING_DETECTED',
                'message': 'ALLOW FILTERING使用: 全テーブルスキャンの可能性',
                'recommendation': 'Materialized Viewまたはセカンダリインデックスの使用を検討'
            })
        
        if not result['uses_partition_key'] and result['query_type'] == 'SELECT':
            result['issues'].append({
                'severity': 'critical',
                'type': 'NO_PARTITION_KEY',
                'message': 'Partition Key未使用: 全ノードスキャン',
                'recommendation': 'WHERE句にPartition Keyを含める'
            })
        
        if result['uses_secondary_index']:
            result['issues'].append({
                'severity': 'medium',
                'type': 'SECONDARY_INDEX_USAGE',
                'message': 'Secondary Index使用: 低効率の可能性',
                'recommendation': 'データモデル設計の見直しを推奨'
            })
        
        return result
    
    def _get_query_type(self, cql: str) -> str:
        """クエリタイプを判定"""
        if cql.startswith('SELECT'):
            return 'SELECT'
        elif cql.startswith('INSERT'):
            return 'INSERT'
        elif cql.startswith('UPDATE'):
            return 'UPDATE'
        elif cql.startswith('DELETE'):
            return 'DELETE'
        elif 'BEGIN BATCH' in cql:
            return 'BATCH'
        return 'UNKNOWN'
    
    def _uses_partition_key(self, cql: str) -> bool:
        """
        WHERE句でPartition Keyを使用しているか判定
        
        注: 実際のテーブル定義と照合が必要
        このメソッドはシンプルな推定
        """
        # WHERE句の抽出
        where_match = re.search(r'WHERE\s+(.+?)(?:ALLOW|ORDER|LIMIT|$)', cql, re.IGNORECASE)
        if not where_match:
            return False
        
        where_clause = where_match.group(1)
        
        # 等価条件の存在（Partition Keyは通常等価条件）
        has_equality = '=' in where_clause and 'IN' not in where_clause.upper()
        
        return has_equality
    
    def _uses_secondary_index(self, cql: str) -> bool:
        """
        Secondary Indexを使用する可能性を推定
        """
        # WHERE句に非等価条件がある場合、Secondary Indexの可能性
        where_match = re.search(r'WHERE\s+(.+?)(?:ALLOW|ORDER|LIMIT|$)', cql, re.IGNORECASE)
        if not where_match:
            return False
        
        where_clause = where_match.group(1)
        
        # >, <, >=, <= などの範囲条件
        has_range = any(op in where_clause for op in ['>', '<', '>=', '<='])
        
        return has_range
    
    def _determine_scan_type(self, cql: str) -> str:
        """
        スキャンタイプを判定
        """
        cql_upper = cql.upper()
        
        if 'ALLOW FILTERING' in cql_upper:
            return 'full_table'
        
        where_match = re.search(r'WHERE\s+(.+?)(?:ALLOW|ORDER|LIMIT|$)', cql_upper)
        if not where_match:
            return 'full_table'
        
        where_clause = where_match.group(1)
        
        # Partition Key + Clustering Key の両方を使用
        if '=' in where_clause and 'AND' in where_clause:
            return 'single_partition'
        
        # IN句を使用（複数パーティション）
        if 'IN' in where_clause:
            return 'multi_partition'
        
        return 'single_partition'

class CassandraBatchAnalyzer:
    """
    BATCH操作の解析
    """
    
    def analyze_batch(self, cql: str) -> dict:
        """
        BATCH処理を解析
        """
        batch_type = self._get_batch_type(cql)
        statements = self._extract_batch_statements(cql)
        
        result = {
            'batch_type': batch_type,
            'statement_count': len(statements),
            'affects_multiple_partitions': self._affects_multiple_partitions(statements),
            'issues': []
        }
        
        # 大量バッチの警告
        if len(statements) > 100:
            result['issues'].append({
                'severity': 'high',
                'type': 'LARGE_BATCH',
                'message': f'大量バッチ処理: {len(statements)}件',
                'recommendation': '100件以下に分割することを推奨'
            })
        
        # 複数パーティションへのLOGGED BATCH
        if batch_type == 'LOGGED' and result['affects_multiple_partitions']:
            result['issues'].append({
                'severity': 'medium',
                'type': 'LOGGED_BATCH_MULTI_PARTITION',
                'message': 'LOGGED BATCHで複数パーティションに書き込み',
                'recommendation': 'UNLOGGED BATCHの使用を検討（冪等性を確保できる場合）'
            })
        
        return result
    
    def _get_batch_type(self, cql: str) -> str:
        """バッチタイプを判定"""
        cql_upper = cql.upper()
        if 'BEGIN UNLOGGED BATCH' in cql_upper:
            return 'UNLOGGED'
        elif 'BEGIN COUNTER BATCH' in cql_upper:
            return 'COUNTER'
        else:
            return 'LOGGED'
    
    def _extract_batch_statements(self, cql: str) -> List[str]:
        """BATCH内の個別文を抽出"""
        # 簡易実装: セミコロンで分割
        statements = cql.split(';')
        # BEGIN BATCH と APPLY BATCH を除外
        return [s.strip() for s in statements 
                if s.strip() and 'BEGIN BATCH' not in s and 'APPLY BATCH' not in s]
    
    def _affects_multiple_partitions(self, statements: List[str]) -> bool:
        """複数パーティションに影響するか判定"""
        # 簡易実装: 異なるテーブルへのアクセスを検出
        tables = set()
        for stmt in statements:
            match = re.search(r'(?:FROM|INTO|UPDATE)\s+(\w+)', stmt, re.IGNORECASE)
            if match:
                tables.add(match.group(1))
        return len(tables) > 1
```

#### 3.1.2 TypeScript (cassandra-driver) 解析
```python
class CassandraTypeScriptAnalyzer:
    """
    TypeScriptコードからCassandra操作を抽出
    """
    
    def analyze_typescript_file(self, file_path: str) -> List[dict]:
        """
        TypeScriptファイルからCassandra操作を抽出
        
        対象パターン:
        - client.execute(query, params, options)
        - client.batch(queries, options)
        - await client.execute()
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        operations = []
        
        # client.execute() の検出
        execute_pattern = r'(?:await\s+)?client\.execute\((.*?)\)'
        for match in re.finditer(execute_pattern, content, re.DOTALL):
            args = match.group(1)
            operation = self._parse_execute_call(args, content)
            operations.append(operation)
        
        # client.batch() の検出
        batch_pattern = r'(?:await\s+)?client\.batch\((.*?)\)'
        for match in re.finditer(batch_pattern, content, re.DOTALL):
            args = match.group(1)
            operation = self._parse_batch_call(args, content)
            operations.append(operation)
        
        return operations
    
    def _parse_execute_call(self, args: str, content: str) -> dict:
        """
        execute呼び出しをパース
        """
        # 第一引数がCQL文
        cql_match = re.search(r'[\'"`](.+?)[\'"`]', args)
        cql = cql_match.group(1) if cql_match else ""
        
        # Consistency Level (optionsオブジェクト内)
        cl_match = re.search(r'consistency:\s*types\.consistencies\.(\w+)', args)
        consistency_level = cl_match.group(1) if cl_match else None
        
        # Prepared Statement判定
        is_prepared = 'prepare' in content and cql in content
        
        return {
            'type': 'execute',
            'cql': cql,
            'consistency_level': consistency_level,
            'is_prepared': is_prepared,
            'is_async': 'await' in args
        }
```

### 3.2 整合性レベルの追跡

```python
class ConsistencyLevelTracker:
    """
    Consistency Level設定を追跡し、不整合を検出
    """
    
    def __init__(self, neo4j_driver):
        self.db = neo4j_driver
        self.cl_hierarchy = {
            'ANY': 0,
            'ONE': 1,
            'TWO': 2,
            'THREE': 3,
            'QUORUM': 4,
            'LOCAL_QUORUM': 4,
            'EACH_QUORUM': 5,
            'ALL': 6,
            'LOCAL_ONE': 1,
            'LOCAL_SERIAL': 7,
            'SERIAL': 7
        }
    
    def track_consistency_levels(self, table_name: str, keyspace: str):
        """
        特定テーブルへのアクセスの整合性レベルを追跡
        """
        query = """
        MATCH (table:CassandraTable {tableName: $tableName, keyspace: $keyspace})
        MATCH (query:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE]->(table)
        MATCH (method:Method)-[:EXECUTES_CQL]->(query)
        RETURN query.queryType as queryType,
               query.consistencyLevel as consistencyLevel,
               method.name as methodName,
               query.cqlText as cql
        """
        
        results = self.db.execute_query(
            query, 
            tableName=table_name, 
            keyspace=keyspace
        )
        
        # 読み書きのCLを分類
        read_cls = []
        write_cls = []
        
        for r in results:
            if r['queryType'] == 'SELECT':
                read_cls.append({
                    'cl': r['consistencyLevel'],
                    'method': r['methodName']
                })
            else:
                write_cls.append({
                    'cl': r['consistencyLevel'],
                    'method': r['methodName']
                })
        
        # 不整合の検出
        inconsistencies = self._detect_inconsistencies(read_cls, write_cls)
        
        return {
            'table': table_name,
            'read_consistency_levels': read_cls,
            'write_consistency_levels': write_cls,
            'inconsistencies': inconsistencies
        }
    
    def _detect_inconsistencies(self, read_cls: List[dict], write_cls: List[dict]) -> List[dict]:
        """
        読み書きのCLの不整合を検出
        
        ルール:
        R + W > RF (Replication Factor)
        
        例: RF=3の場合
        - R=QUORUM(2) + W=QUORUM(2) = 4 > 3 ✓ 整合性保証
        - R=ONE(1) + W=ONE(1) = 2 < 3 ✗ 不整合の可能性
        """
        issues = []
        
        for read in read_cls:
            for write in write_cls:
                read_level = self.cl_hierarchy.get(read['cl'], 0)
                write_level = self.cl_hierarchy.get(write['cl'], 0)
                
                # RF=3を仮定（本来は実際のRFを取得）
                rf = 3
                
                if read_level + write_level <= rf:
                    issues.append({
                        'severity': 'high',
                        'type': 'CONSISTENCY_VIOLATION',
                        'read_method': read['method'],
                        'read_cl': read['cl'],
                        'write_method': write['method'],
                        'write_cl': write['cl'],
                        'message': f"R({read['cl']}) + W({write['cl']}) <= RF({rf}): データ不整合の可能性",
                        'recommendation': 'QuorumまたはALLの使用を検討'
                    })
        
        return issues

class PartitionKeyAnalyzer:
    """
    Partition Key使用の検証
    """
    
    def __init__(self, neo4j_driver):
        self.db = neo4j_driver
    
    def analyze_partition_key_usage(self, table_name: str):
        """
        テーブルへのクエリがPartition Keyを適切に使用しているか検証
        """
        # テーブル定義を取得
        table_query = """
        MATCH (table:CassandraTable {tableName: $tableName})
        RETURN table.partitionKeys as partitionKeys
        """
        
        table_info = self.db.execute_query(table_query, tableName=table_name).single()
        partition_keys = table_info['partitionKeys']
        
        # このテーブルへのクエリを取得
        query = """
        MATCH (table:CassandraTable {tableName: $tableName})
        MATCH (cql:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE]->(table)
        MATCH (method:Method)-[:EXECUTES_CQL]->(cql)
        RETURN cql.cqlText as cql,
               cql.usesPartitionKey as usesPartitionKey,
               cql.scanType as scanType,
               method.name as methodName
        """
        
        results = self.db.execute_query(query, tableName=table_name)
        
        issues = []
        for r in results:
            if not r['usesPartitionKey']:
                issues.append({
                    'severity': 'critical',
                    'method': r['methodName'],
                    'cql': r['cql'],
                    'type': 'MISSING_PARTITION_KEY',
                    'message': f"Partition Key未使用: {partition_keys}",
                    'scan_type': r['scanType'],
                    'recommendation': f"WHERE句に{', '.join(partition_keys)}を含める"
                })
        
        return {
            'table': table_name,
            'partition_keys': partition_keys,
            'issues': issues,
            'queries_without_pk': len(issues),
            'total_queries': len(results)
        }
```

---

## 4. Cassandra特化型分析クエリ

### 4.1 整合性レベル不整合の検出

```cypher
// 同一テーブルへの読み書きでCLが不整合
MATCH (table:CassandraTable)
MATCH (readQuery:CassandraQuery {queryType: 'SELECT'})-[:ACCESSES_CASSANDRA_TABLE]->(table)
MATCH (writeQuery:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE]->(table)
WHERE writeQuery.queryType IN ['INSERT', 'UPDATE', 'DELETE']
  AND readQuery.consistencyLevel IS NOT NULL
  AND writeQuery.consistencyLevel IS NOT NULL

WITH table, readQuery, writeQuery,
     CASE readQuery.consistencyLevel
       WHEN 'ONE' THEN 1
       WHEN 'QUORUM' THEN 2
       WHEN 'ALL' THEN 3
       ELSE 0
     END as readLevel,
     CASE writeQuery.consistencyLevel
       WHEN 'ONE' THEN 1
       WHEN 'QUORUM' THEN 2
       WHEN 'ALL' THEN 3
       ELSE 0
     END as writeLevel

// RF=3を仮定: R + W <= 3 の場合は不整合リスク
WHERE readLevel + writeLevel <= 3

MATCH (readMethod:Method)-[:EXECUTES_CQL]->(readQuery)
MATCH (writeMethod:Method)-[:EXECUTES_CQL]->(writeQuery)
MATCH (readMethod)<-[:CONTAINS]-(readClass:Class)<-[:CONTAINS]-(readFile:File)
MATCH (writeMethod)<-[:CONTAINS]-(writeClass:Class)<-[:CONTAINS]-(writeFile:File)

RETURN table.keyspace + '.' + table.tableName as table,
       readFile.path as readLocation,
       readMethod.name as readMethod,
       readQuery.consistencyLevel as readCL,
       writeFile.path as writeLocation,
       writeMethod.name as writeMethod,
       writeQuery.consistencyLevel as writeCL,
       'Data Inconsistency Risk' as issue,
       'Increase Consistency Level to QUORUM or higher' as recommendation
```

### 4.2 ALLOW FILTERINGの検出

```cypher
// ALLOW FILTERING使用の検出
MATCH (query:CassandraQuery)
WHERE query.hasAllowFiltering = true
MATCH (method:Method)-[:EXECUTES_CQL]->(query)
MATCH (query)-[:ACCESSES_CASSANDRA_TABLE]->(table:CassandraTable)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

RETURN file.path,
       class.name,
       method.name,
       table.tableName,
       query.cqlText,
       query.estimatedRows,
       'ALLOW FILTERING - Full Table Scan Risk' as issue,
       CASE 
         WHEN query.estimatedRows > 100000 THEN 'critical'
         WHEN query.estimatedRows > 10000 THEN 'high'
         ELSE 'medium'
       END as severity,
       'Create Materialized View or redesign data model' as recommendation
ORDER BY query.estimatedRows DESC
```

### 4.3 Partition Key未使用の検出

```cypher
// Partition Keyを使わないSELECTクエリ
MATCH (query:CassandraQuery {queryType: 'SELECT'})
WHERE query.usesPartitionKey = false
  AND query.hasAllowFiltering = false  // ALLOW FILTERINGなしでPK不使用
MATCH (method:Method)-[:EXECUTES_CQL]->(query)
MATCH (query)-[:ACCESSES_CASSANDRA_TABLE]->(table:CassandraTable)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

RETURN file.path,
       method.name,
       table.tableName,
       table.partitionKeys,
       query.cqlText,
       query.scanType,
       'Missing Partition Key - Multi-node Scan' as issue,
       'critical' as severity,
       'Add partition key to WHERE clause: ' + table.partitionKeys[0] as recommendation
```

### 4.4 大量バッチ処理の検出

```cypher
// 大量バッチ処理
MATCH (query:CassandraQuery {isBatch: true})
WHERE query.batchSize > 100
MATCH (method:Method)-[:EXECUTES_CQL]->(query)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

RETURN file.path,
       method.name,
       query.batchType,
       query.batchSize,
       'Large Batch Processing' as issue,
       CASE 
         WHEN query.batchSize > 500 THEN 'critical'
         WHEN query.batchSize > 200 THEN 'high'
         ELSE 'medium'
       END as severity,
       'Split batch into chunks of 100 or less' as recommendation
ORDER BY query.batchSize DESC
```

### 4.5 ホットパーティションリスク

```cypher
// 時系列データでのホットパーティションリスク
MATCH (query:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE]->(table:CassandraTable)
WHERE table.hasHotPartitionWarning = true
  OR (table.partitionKeys = ['date'] OR table.partitionKeys = ['timestamp'])
MATCH (method:Method)-[:EXECUTES_CQL]->(query)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

WITH table, query, method, file, class,
     query.estimatedPartitions as partitionCount

WHERE partitionCount = 1  // 単一パーティションへの書き込み

RETURN file.path,
       method.name,
       table.tableName,
       table.partitionKeys,
       'Hot Partition Risk - Time-based Partition Key' as issue,
       'high' as severity,
       'Add bucketing: partition_key = (date, bucket)' as recommendation
```

### 4.6 Prepared Statement未使用

```cypher
// Prepared Statementを使っていない頻繁なクエリ
MATCH (method:Method)-[exec:EXECUTES_CQL]->(query:CassandraQuery)
WHERE query.isPrepared = false
  AND exec.frequency > 10
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

RETURN file.path,
       method.name,
       query.cqlText,
       exec.frequency,
       'Unprepared Statement - Parse Overhead' as issue,
       CASE 
         WHEN exec.frequency > 100 THEN 'high'
         WHEN exec.frequency > 50 THEN 'medium'
         ELSE 'low'
       END as severity,
       'Use prepared statement to reduce parse overhead' as recommendation
ORDER BY exec.frequency DESC
```

### 4.7 Secondary Index使用の検出

```cypher
// Secondary Indexを使用するクエリ
MATCH (query:CassandraQuery)
WHERE query.usesSecondaryIndex = true
MATCH (method:Method)-[:EXECUTES_CQL]->(query)
MATCH (query)-[:ACCESSES_CASSANDRA_TABLE]->(table:CassandraTable)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)

RETURN file.path,
       method.name,
       table.tableName,
       table.secondaryIndexes,
       query.cqlText,
       'Secondary Index Usage - Performance Concern' as issue,
       'medium' as severity,
       'Consider data model redesign or Materialized View' as recommendation
```

---

## 5. Cassandra特化型API

```python
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional

app = FastAPI(title="Cassandra Analysis API")

@app.get("/api/v1/cassandra/health")
async def cassandra_health_check():
    """
    Cassandra関連コードの健全性チェック
    """
    # 各種問題の集計
    allow_filtering_count = await count_allow_filtering_issues()
    pk_missing_count = await count_missing_partition_key()
    cl_mismatch_count = await count_consistency_mismatches()
    large_batch_count = await count_large_batches()
    unprepared_count = await count_unprepared_statements()
    
    total_issues = (
        allow_filtering_count + 
        pk_missing_count + 
        cl_mismatch_count + 
        large_batch_count + 
        unprepared_count
    )
    
    health_score = max(0, 100 - (total_issues * 2))
    
    return {
        "health_score": health_score,
        "health_status": "good" if health_score > 80 else "warning" if health_score > 60 else "critical",
        "issues_summary": {
            "allow_filtering": allow_filtering_count,
            "missing_partition_key": pk_missing_count,
            "consistency_mismatch": cl_mismatch_count,
            "large_batch": large_batch_count,
            "unprepared_statement": unprepared_count
        },
        "total_issues": total_issues
    }

@app.get("/api/v1/cassandra/tables/{keyspace}/{table}/analysis")
async def analyze_table(keyspace: str, table: str):
    """
    特定テーブルの詳細分析
    """
    # テーブルへのアクセスパターン分析
    access_patterns = await analyze_table_access_patterns(keyspace, table)
    
    # 整合性レベルの追跡
    cl_tracker = ConsistencyLevelTracker(neo4j_driver)
    cl_analysis = cl_tracker.track_consistency_levels(table, keyspace)
    
    # Partition Key使用分析
    pk_analyzer = PartitionKeyAnalyzer(neo4j_driver)
    pk_analysis = pk_analyzer.analyze_partition_key_usage(table)
    
    # パフォーマンスリスク評価
    perf_risks = await assess_performance_risks(keyspace, table)
    
    return {
        "keyspace": keyspace,
        "table": table,
        "access_patterns": access_patterns,
        "consistency_analysis": cl_analysis,
        "partition_key_analysis": pk_analysis,
        "performance_risks": perf_risks,
        "overall_risk_score": calculate_risk_score(cl_analysis, pk_analysis, perf_risks)
    }

@app.get("/api/v1/cassandra/detect/consistency-mismatches")
async def detect_consistency_mismatches():
    """
    整合性レベルの不整合を検出
    """
    cypher_query = """
    MATCH (table:CassandraTable)
    MATCH (readQuery:CassandraQuery {queryType: 'SELECT'})-[:ACCESSES_CASSANDRA_TABLE]->(table)
    MATCH (writeQuery:CassandraQuery)-[:ACCESSES_CASSANDRA_TABLE]->(table)
    WHERE writeQuery.queryType IN ['INSERT', 'UPDATE', 'DELETE']
      AND readQuery.consistencyLevel IS NOT NULL
      AND writeQuery.consistencyLevel IS NOT NULL
    
    WITH table, readQuery, writeQuery,
         CASE readQuery.consistencyLevel
           WHEN 'ONE' THEN 1
           WHEN 'QUORUM' THEN 2
           WHEN 'ALL' THEN 3
           ELSE 0
         END as readLevel,
         CASE writeQuery.consistencyLevel
           WHEN 'ONE' THEN 1
           WHEN 'QUORUM' THEN 2
           WHEN 'ALL' THEN 3
           ELSE 0
         END as writeLevel
    
    WHERE readLevel + writeLevel <= 3
    
    MATCH (readMethod:Method)-[:EXECUTES_CQL]->(readQuery)
    MATCH (writeMethod:Method)-[:EXECUTES_CQL]->(writeQuery)
    
    RETURN table.tableName as table,
           readMethod.name as readMethod,
           readQuery.consistencyLevel as readCL,
           writeMethod.name as writeMethod,
           writeQuery.consistencyLevel as writeCL
    """
    
    results = neo4j_driver.execute_query(cypher_query)
    
    return {
        "consistency_mismatches": results,
        "total_count": len(results),
        "severity": "critical" if len(results) > 0 else "low",
        "recommendations": [
            "両方のConsistency LevelをQUORUMに設定",
            "Read: QUORUM, Write: ALLの組み合わせを検討",
            "データ整合性要件を再確認"
        ]
    }

@app.post("/api/v1/cassandra/simulate/table-change")
async def simulate_table_change(
    keyspace: str,
    table: str,
    change_type: str = Query(..., regex="^(add_column|remove_column|change_partition_key|add_index)$")
):
    """
    Cassandraテーブル変更の影響をシミュレーション
    """
    # このテーブルにアクセスするクエリを取得
    affected_queries = await get_affected_queries(keyspace, table)
    
    # 変更タイプごとの影響評価
    impact_assessment = assess_change_impact(change_type, affected_queries)
    
    # ダウンタイムの推定
    estimated_downtime = estimate_downtime(change_type, affected_queries)
    
    # ロールバック戦略
    rollback_strategy = generate_rollback_strategy(change_type)
    
    return {
        "keyspace": keyspace,
        "table": table,
        "change_type": change_type,
        "affected_queries": len(affected_queries),
        "affected_methods": [q['method'] for q in affected_queries],
        "impact_level": impact_assessment['level'],
        "impact_details": impact_assessment['details'],
        "estimated_downtime_minutes": estimated_downtime,
        "rollback_strategy": rollback_strategy,
        "migration_steps": generate_migration_steps(change_type, keyspace, table)
    }

def assess_change_impact(change_type: str, affected_queries: List[dict]) -> dict:
    """
    変更タイプに応じた影響評価
    """
    if change_type == "change_partition_key":
        return {
            "level": "critical",
            "details": [
                "全てのクエリがWHERE句の変更必要",
                "データ再配置による大規模マイグレーション",
                "アプリケーション側の大幅な修正"
            ]
        }
    elif change_type == "remove_column":
        affected_count = sum(1 for q in affected_queries if 'column_name' in q['cql'])
        return {
            "level": "high" if affected_count > 0 else "medium",
            "details": [
                f"{affected_count}個のクエリが影響を受ける",
                "SELECT *を使用している箇所は影響を受けない可能性",
                "アプリケーション層のマッピング更新必要"
            ]
        }
    else:
        return {
            "level": "low",
            "details": ["影響は軽微"]
        }

def generate_migration_steps(change_type: str, keyspace: str, table: str) -> List[dict]:
    """
    マイグレーション手順を生成
    """
    if change_type == "change_partition_key":
        return [
            {
                "step": 1,
                "action": "新しいテーブルスキーマを作成",
                "command": f"CREATE TABLE {keyspace}.{table}_new (...)",
                "rollback": f"DROP TABLE {keyspace}.{table}_new"
            },
            {
                "step": 2,
                "action": "データを新テーブルにコピー",
                "command": "spark-submit copy_data.py",
                "estimated_time": "数時間〜数日"
            },
            {
                "step": 3,
                "action": "アプリケーションコードを更新",
                "command": "Deploy new application version",
                "rollback": "Rollback to previous version"
            },
            {
                "step": 4,
                "action": "旧テーブルを削除",
                "command": f"DROP TABLE {keyspace}.{table}",
                "note": "十分な検証後に実行"
            }
        ]
    else:
        return [
            {
                "step": 1,
                "action": f"テーブル変更を実行",
                "command": f"ALTER TABLE {keyspace}.{table} ..."
            }
        ]

@app.get("/api/v1/cassandra/recommendations")
async def get_recommendations():
    """
    Cassandra使用のベストプラクティス推奨事項
    """
    # 実際の使用パターンから推奨事項を生成
    issues = await get_all_issues()
    
    recommendations = []
    
    # ALLOW FILTERINGが多い場合
    if issues['allow_filtering_count'] > 10:
        recommendations.append({
            "priority": "high",
            "category": "data_modeling",
            "title": "データモデルの再設計",
            "description": "ALLOW FILTERINGの使用が多く検出されました。クエリパターンに合わせたテーブル設計を推奨します。",
            "actions": [
                "頻繁なクエリパターンを特定",
                "Materialized Viewの作成を検討",
                "Query-drivenなテーブル設計への移行"
            ]
        })
    
    # 整合性レベル不整合
    if issues['cl_mismatch_count'] > 0:
        recommendations.append({
            "priority": "critical",
            "category": "consistency",
            "title": "整合性レベルの統一",
            "description": "読み書きのConsistency Levelが不整合です。データ不整合のリスクがあります。",
            "actions": [
                "読み書き共にQUORUMを設定",
                "CAP定理を理解し、要件に合わせた設定",
                "整合性テストの実施"
            ]
        })
    
    return {
        "recommendations": recommendations,
        "total_recommendations": len(recommendations)
    }
```

---

## 6. 実装ロードマップ (Cassandra特化)

### Week 1: 基本CQL解析
**目標**: JavaコードからCQLを抽出

- [ ] DataStax Driver呼び出しの検出
- [ ] CQL文字列の抽出
- [ ] 基本的なCQLパース
- [ ] Neo4jへのCassandraQueryノード作成

**成果物**: 
- `CassandraJavaAnalyzer`クラス
- 100件のテストケース

### Week 2: 整合性レベル追跡
**目標**: CL設定の追跡

- [ ] Consistency Level設定の検出
- [ ] 読み書きのCLマッピング
- [ ] 不整合検出ロジック
- [ ] ConsistencyLevelTrackerの実装

**成果物**:
- CL追跡機能
- 不整合検出API

### Week 3: 問題パターン検出
**目標**: Cassandra特有の問題を検出

- [ ] ALLOW FILTERING検出
- [ ] Partition Key未使用検出
- [ ] 大量バッチ検出
- [ ] Secondary Index使用検出

**成果物**:
- 問題検出Cypherクエリ集
- 検出API

### Week 4: 統合とダッシュボード
**目標**: UIとレポート

- [ ] Cassandraダッシュボード
- [ ] 問題リスト表示
- [ ] テーブル分析ビュー
- [ ] 週次レポート生成

**成果物**:
- Webダッシュボード
- 自動レポート

---

## 7. 成功指標 (Cassandra特化)

| 指標 | 現状 | 目標 | 測定方法 |
|-----|------|------|---------|
| ALLOW FILTERING検出 | - | 95%以上 | 手動レビューとの比較 |
| CL不整合検出 | - | 100% | 全パターン検出 |
| Cassandra起因の障害 | ? | 80%削減 | インシデント数 |
| スロークエリ削減 | - | 50%削減 | P95レスポンスタイム |

---

## 8. 次のステップ

### 即座に必要な情報

1. **使用しているCassandraドライバー**
   - DataStax Java Driver (バージョン)
   - cassandra-driver (Node.js)
   - gocql (Go)
   - その他

2. **現在のCassandra構成**
   - クラスターサイズ
   - Replication Factor
   - デフォルトのConsistency Level

3. **直近の障害事例**
   - 最近発生したCassandra関連の障害内容
   - 最も痛い問題は何か

4. **コードの配置**
   - CassandraアクセスコードはDAO層に集約されているか
   - 散在しているか

### プロトタイプ提案

まずは**1週間**で以下のプロトタイプを作成し、効果を検証することを提案します:

**スコープ**:
- Javaファイル 10-20個
- ALLOW FILTERING検出
- Partition Key未使用検出
- 簡易レポート出力

**デモ可能な成果物**:
- 実際のコードから問題を検出
- HTMLレポート生成
- 修正推奨事項の提示

この方向性でよろしいでしょうか? 詳細をお聞かせください。

---

**本仕様書のバージョン**: v1.2 (Cassandra Specialized)  
**最終更新日**: 2025年10月26日
