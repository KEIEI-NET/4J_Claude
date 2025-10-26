# ソースコード関係性分析・グラフDB格納システム 詳細仕様書

## 1. エグゼクティブサマリー

### 1.1 プロジェクト目的
本システムは、大規模マルチ言語ソフトウェアプロジェクト(35,000ファイル規模)におけるソースコード間の複雑な関係性を自動解析し、Neo4jグラフデータベースに格納することで、バグ発生時の影響範囲を即座に特定し、開発効率を劇的に向上させることを目的とします。

### 1.2 主要ユースケース
- **バグ影響範囲の即時特定**: 特定のソースファイルや関数の変更が及ぼす影響を数秒で可視化
- **リファクタリング影響分析**: 大規模リファクタリング前の影響範囲の事前評価
- **コードレビュー支援**: Pull Request時の影響範囲の自動提示
- **技術的負債の可視化**: 複雑な依存関係や循環参照の検出

### 1.3 対象言語
- Java
- TypeScript
- Angular
- Go
- C#
- 将来的な拡張性を考慮した設計

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    ソースコードリポジトリ                      │
│              (Java/TS/Angular/Go/C# - 35,000ファイル)        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              並列解析オーケストレーター (Celery)               │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐      │
│  │ Java    │   TS    │ Angular │   Go    │   C#    │      │
│  │ Worker  │ Worker  │ Worker  │ Worker  │ Worker  │      │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   関係抽出エンジン                            │
│  ┌───────────────────────────────────────────────────┐      │
│  │  レベル1: ファイル間依存関係 (import/include)       │      │
│  │  レベル2: 関数/メソッド呼び出しグラフ               │      │
│  │  レベル3: データフロー・制御フロー分析              │      │
│  │  レベル4: 実行時動的依存関係の推定                 │      │
│  └───────────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Neo4j グラフDB                          │
│  ┌───────────────────────────────────────────────────┐      │
│  │  ノード: File, Class, Method, Variable, Module    │      │
│  │  エッジ: DEPENDS_ON, CALLS, INHERITS, DATA_FLOW   │      │
│  └───────────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              影響範囲分析・可視化レイヤー                      │
│  ┌─────────────────┬─────────────────┬──────────────┐      │
│  │ Cypher API      │  Web UI         │  CLI Tool    │      │
│  │ (FastAPI)       │  (React/D3.js)  │              │      │
│  └─────────────────┴─────────────────┴──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技術スタック

| レイヤー | 技術 | 選定理由 |
|---------|------|---------|
| 解析オーケストレーション | Celery + RabbitMQ | 35,000ファイルの並列処理に最適 |
| 言語パーサー | Tree-sitter (統一IF) | マルチ言語対応、高速、増分解析可能 |
| Java解析 | Eclipse JDT, JavaParser | AST + データフロー解析 |
| TypeScript/Angular解析 | TypeScript Compiler API | 公式API、型情報へのアクセス |
| Go解析 | go/parser, go/types | 標準ライブラリ、型システム統合 |
| C#解析 | Roslyn (Microsoft.CodeAnalysis) | 公式、強力なセマンティック解析 |
| グラフDB | Neo4j 5.x | Cypherクエリ、優れた可視化、スケーラビリティ |
| API層 | FastAPI | 非同期処理、高速、型安全 |
| フロントエンド | React + Recharts/D3.js | インタラクティブなグラフ可視化 |
| キャッシュ | Redis | 頻繁に参照される関係性のキャッシュ |

---

## 3. データモデル設計 (Neo4j)

### 3.1 ノードタイプ

#### 3.1.1 Fileノード
```cypher
(:File {
  id: "unique_file_id",
  path: "/src/main/java/com/example/Service.java",
  name: "Service.java",
  language: "java",
  size: 1024,
  lastModified: datetime(),
  checksum: "md5_hash",
  complexity: 45.2,  // McCabe Complexity
  linesOfCode: 350,
  testCoverage: 0.85
})
```

#### 3.1.2 Packageノード (モジュール構造)
```cypher
(:Package {
  id: "com.example.service",
  name: "service",
  fullName: "com.example.service",
  language: "java"
})
```

#### 3.1.3 Classノード
```cypher
(:Class {
  id: "com.example.Service",
  name: "Service",
  fullyQualifiedName: "com.example.Service",
  isAbstract: false,
  isInterface: false,
  visibility: "public",
  startLine: 10,
  endLine: 120,
  complexity: 25.3
})
```

#### 3.1.4 Methodノード
```cypher
(:Method {
  id: "com.example.Service.processData",
  name: "processData",
  signature: "processData(String, int): Result",
  returnType: "Result",
  parameters: ["String data", "int flags"],
  visibility: "public",
  isStatic: false,
  isAsync: false,
  complexity: 8,
  startLine: 45,
  endLine: 78,
  callCount: 0  // 更新される統計情報
})
```

#### 3.1.5 Variableノード (重要な状態変数)
```cypher
(:Variable {
  id: "com.example.Service.cache",
  name: "cache",
  type: "Map<String, Object>",
  scope: "instance",
  isStatic: false,
  isFinal: false
})
```

#### 3.1.6 Interfaceノード
```cypher
(:Interface {
  id: "com.example.IService",
  name: "IService",
  fullyQualifiedName: "com.example.IService"
})
```

### 3.2 関係性タイプ (エッジ)

#### 3.2.1 DEPENDS_ON (ファイル間依存)
```cypher
(:File)-[:DEPENDS_ON {
  importType: "static|dynamic",
  isCircular: false,
  strength: 1.0  // 依存の強さ (0.0-1.0)
}]->(:File)
```

#### 3.2.2 CALLS (関数呼び出し)
```cypher
(:Method)-[:CALLS {
  callType: "direct|indirect|polymorphic",
  frequency: 5,  // 静的解析で検出された回数
  isConditional: false,  // 条件分岐内の呼び出しか
  lineNumber: 67
}]->(:Method)
```

#### 3.2.3 INHERITS (継承関係)
```cypher
(:Class)-[:INHERITS]->(:Class)
```

#### 3.2.4 IMPLEMENTS (インターフェース実装)
```cypher
(:Class)-[:IMPLEMENTS]->(:Interface)
```

#### 3.2.5 DATA_FLOW (データフロー)
```cypher
(:Variable)-[:DATA_FLOW {
  flowType: "read|write|readwrite",
  isShared: false,  // スレッド間共有か
  lineNumber: 89
}]->(:Variable)
```

#### 3.2.6 CONTAINS (包含関係)
```cypher
(:File)-[:CONTAINS]->(:Class)
(:Class)-[:CONTAINS]->(:Method)
(:Package)-[:CONTAINS]->(:File)
```

#### 3.2.7 THROWS (例外スロー)
```cypher
(:Method)-[:THROWS {
  exceptionType: "IOException",
  isChecked: true
}]->(:Class)
```

#### 3.2.8 ACCESSES (フィールドアクセス)
```cypher
(:Method)-[:ACCESSES {
  accessType: "read|write|readwrite",
  lineNumber: 45
}]->(:Variable)
```

### 3.3 インデックス設計

```cypher
// 高速検索のための複合インデックス
CREATE INDEX file_path_idx FOR (f:File) ON (f.path);
CREATE INDEX file_language_idx FOR (f:File) ON (f.language);
CREATE INDEX method_name_idx FOR (m:Method) ON (m.name);
CREATE INDEX class_fqn_idx FOR (c:Class) ON (c.fullyQualifiedName);

// 全文検索インデックス
CREATE FULLTEXT INDEX file_content_idx FOR (f:File) ON EACH [f.path, f.name];
CREATE FULLTEXT INDEX method_search_idx FOR (m:Method) ON EACH [m.name, m.signature];
```

---

## 4. 解析エンジン詳細設計

### 4.1 言語別パーサー戦略

#### 4.1.1 Java解析
```python
class JavaAnalyzer:
    def __init__(self):
        self.parser = JavaParser()
        self.type_solver = CombinedTypeSolver()
        
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        レベル1: import文の解析
        レベル2: メソッド呼び出しの解析
        レベル3: データフロー解析 (変数の使用追跡)
        レベル4: リフレクション、動的呼び出しの推定
        """
        cu = self.parser.parse(file_path)
        
        # import解析
        dependencies = self._extract_imports(cu)
        
        # メソッド呼び出しグラフ
        call_graph = self._build_call_graph(cu)
        
        # データフロー解析
        data_flows = self._analyze_data_flow(cu)
        
        # 動的呼び出し推定
        dynamic_calls = self._infer_dynamic_calls(cu)
        
        return AnalysisResult(dependencies, call_graph, data_flows, dynamic_calls)
    
    def _analyze_data_flow(self, cu):
        """
        変数の定義から使用までの流れを追跡
        - 変数のスコープ分析
        - 代入チェーン
        - メソッド引数としての伝播
        """
        pass
```

#### 4.1.2 TypeScript/Angular解析
```python
class TypeScriptAnalyzer:
    def __init__(self):
        self.ts_compiler = ts.createProgram()
        
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Angular特有の解析:
        - @Component デコレーターの依存関係
        - サービスのDI (Dependency Injection)
        - テンプレートとの関連
        """
        source_file = self.ts_compiler.getSourceFile(file_path)
        
        # モジュール解析
        imports = self._extract_es6_imports(source_file)
        
        # Angular DI解析
        di_dependencies = self._analyze_angular_di(source_file)
        
        # 型情報を使った呼び出し解析
        typed_calls = self._analyze_with_type_info(source_file)
        
        return AnalysisResult(imports, di_dependencies, typed_calls)
```

#### 4.1.3 Go解析
```python
class GoAnalyzer:
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Go特有の解析:
        - パッケージ構造
        - goroutine呼び出し
        - チャネルを通じたデータフロー
        """
        fset = token.NewFileSet()
        node = parser.ParseFile(fset, file_path)
        
        # パッケージ依存
        package_deps = self._extract_imports(node)
        
        # goroutine解析
        concurrent_calls = self._analyze_goroutines(node)
        
        return AnalysisResult(package_deps, concurrent_calls)
```

#### 4.1.4 C#解析
```python
class CSharpAnalyzer:
    def __init__(self):
        self.workspace = MSBuildWorkspace.Create()
        
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Roslyn使用:
        - セマンティックモデルによる正確な型解決
        - LINQ式の解析
        - async/awaitパターン
        """
        tree = CSharpSyntaxTree.ParseText(file_content)
        compilation = CSharpCompilation.Create("Analysis")
        semantic_model = compilation.GetSemanticModel(tree)
        
        # セマンティック解析
        symbols = self._extract_symbols(semantic_model)
        
        # async/await解析
        async_flows = self._analyze_async_patterns(tree)
        
        return AnalysisResult(symbols, async_flows)
```

### 4.2 増分解析戦略

35,000ファイルすべてを毎回解析するのは非効率的です。以下の増分解析を実装します:

```python
class IncrementalAnalyzer:
    def __init__(self, redis_client, neo4j_driver):
        self.cache = redis_client
        self.db = neo4j_driver
        
    def analyze_changes(self, changed_files: List[str]):
        """
        変更されたファイルのみを解析し、影響範囲を更新
        """
        for file_path in changed_files:
            # ファイルのチェックサムを確認
            current_checksum = self._compute_checksum(file_path)
            cached_checksum = self.cache.get(f"checksum:{file_path}")
            
            if current_checksum != cached_checksum:
                # 解析実行
                result = self._analyze_file(file_path)
                
                # グラフの差分更新
                self._update_graph_delta(file_path, result)
                
                # チェックサム更新
                self.cache.set(f"checksum:{file_path}", current_checksum)
                
    def _update_graph_delta(self, file_path: str, result: AnalysisResult):
        """
        既存のノード・エッジを削除し、新しい関係を追加
        """
        with self.db.session() as session:
            # 古い関係を削除
            session.run("""
                MATCH (f:File {path: $path})-[r]-()
                DELETE r
            """, path=file_path)
            
            # 新しい関係を追加
            for dep in result.dependencies:
                session.run("""
                    MATCH (f1:File {path: $from})
                    MATCH (f2:File {path: $to})
                    MERGE (f1)-[:DEPENDS_ON {strength: $strength}]->(f2)
                """, from=file_path, to=dep.target, strength=dep.strength)
```

### 4.3 並列処理設計

```python
# Celeryタスク定義
@celery.task
def analyze_file_task(file_path: str, language: str):
    """
    単一ファイルの解析タスク
    """
    analyzer = get_analyzer(language)
    result = analyzer.analyze_file(file_path)
    store_to_neo4j(result)
    return {"status": "success", "file": file_path}

@celery.task
def analyze_project_task(project_root: str):
    """
    プロジェクト全体の解析をオーケストレート
    """
    files = discover_files(project_root)
    
    # ファイルを言語ごとにグループ化
    files_by_language = group_by_language(files)
    
    # 並列処理のチャンクサイズを決定 (メモリ効率を考慮)
    chunk_size = 100
    
    for language, file_list in files_by_language.items():
        # チャンクに分割して並列実行
        chunks = [file_list[i:i+chunk_size] for i in range(0, len(file_list), chunk_size)]
        
        for chunk in chunks:
            group = celery.group(
                analyze_file_task.s(file, language) for file in chunk
            )
            group.apply_async()
```

---

## 5. 影響範囲分析アルゴリズム

### 5.1 バグ影響範囲の特定

#### 5.1.1 前方影響分析 (Forward Impact)
「このファイルを変更すると、どこに影響が及ぶか?」

```cypher
// 特定ファイルから影響を受けるすべてのファイルを取得
MATCH path = (start:File {path: $targetFile})-[:DEPENDS_ON|CALLS*1..5]->(affected:File)
WHERE start <> affected
RETURN DISTINCT affected.path as affectedFile, 
       length(path) as distance,
       [node in nodes(path) | node.name] as impactChain
ORDER BY distance
```

#### 5.1.2 後方影響分析 (Backward Impact)
「このファイルに影響を与えるファイルは何か?」

```cypher
MATCH path = (source:File)-[:DEPENDS_ON|CALLS*1..5]->(target:File {path: $targetFile})
WHERE source <> target
RETURN DISTINCT source.path as sourceFile,
       length(path) as distance,
       [node in nodes(path) | node.name] as dependencyChain
ORDER BY distance
```

#### 5.1.3 メソッドレベルの影響分析

```cypher
// 特定メソッドを変更した場合の影響範囲
MATCH (method:Method {id: $methodId})
MATCH path = (method)-[:CALLS*1..3]->(calledMethod:Method)
MATCH (calledMethod)<-[:CONTAINS]-(affectedClass:Class)<-[:CONTAINS]-(affectedFile:File)
RETURN DISTINCT affectedFile.path, 
       affectedClass.name, 
       calledMethod.name,
       length(path) as callDepth
ORDER BY callDepth, affectedFile.path
```

#### 5.1.4 データフロー影響分析

```cypher
// 変数への変更が及ぼす影響
MATCH (var:Variable {id: $variableId})
MATCH path = (var)-[:DATA_FLOW*1..4]->(affectedVar:Variable)
MATCH (method:Method)-[:ACCESSES]->(affectedVar)
MATCH (method)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
RETURN DISTINCT file.path, 
       class.name, 
       method.name,
       affectedVar.name,
       [rel in relationships(path) | rel.flowType] as flowTypes
```

### 5.2 循環依存の検出

```cypher
// 循環依存の検出
MATCH cycle = (f:File)-[:DEPENDS_ON*2..]->(f)
RETURN [node in nodes(cycle) | node.path] as circularDependency,
       length(cycle) as cycleLength
ORDER BY cycleLength
```

### 5.3 複雑度スコアリング

```python
def calculate_change_risk_score(file_path: str) -> float:
    """
    ファイル変更のリスクスコアを計算
    """
    query = """
    MATCH (f:File {path: $path})
    OPTIONAL MATCH (f)-[:DEPENDS_ON]->(dep)
    OPTIONAL MATCH (dependent)-[:DEPENDS_ON]->(f)
    OPTIONAL MATCH (f)-[:CONTAINS]->(class:Class)-[:CONTAINS]->(method:Method)
    RETURN f.complexity as fileComplexity,
           count(DISTINCT dep) as outgoingDeps,
           count(DISTINCT dependent) as incomingDeps,
           avg(method.complexity) as avgMethodComplexity,
           f.testCoverage as testCoverage
    """
    
    result = neo4j_session.run(query, path=file_path).single()
    
    # リスクスコア計算式
    risk_score = (
        result['fileComplexity'] * 0.3 +
        result['outgoingDeps'] * 0.2 +
        result['incomingDeps'] * 0.3 +
        result['avgMethodComplexity'] * 0.1 +
        (1 - result['testCoverage']) * 0.1
    )
    
    return risk_score
```

---

## 6. API設計

### 6.1 FastAPI エンドポイント

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Source Code Graph Analysis API")

class ImpactAnalysisRequest(BaseModel):
    file_path: str
    analysis_depth: int = 3
    include_tests: bool = False

class ImpactAnalysisResponse(BaseModel):
    target_file: str
    forward_impact: List[Dict[str, Any]]
    backward_impact: List[Dict[str, Any]]
    risk_score: float
    circular_dependencies: List[List[str]]
    
@app.post("/api/v1/analyze/impact", response_model=ImpactAnalysisResponse)
async def analyze_impact(request: ImpactAnalysisRequest):
    """
    指定されたファイルの影響範囲を分析
    """
    # 前方影響分析
    forward_query = """
    MATCH path = (start:File {path: $path})-[:DEPENDS_ON|CALLS*1..$depth]->(affected:File)
    WHERE start <> affected
    RETURN DISTINCT affected.path as file, 
           length(path) as distance,
           [node in nodes(path) | node.name] as chain
    ORDER BY distance
    """
    
    forward_results = neo4j_driver.execute_query(
        forward_query, 
        path=request.file_path, 
        depth=request.analysis_depth
    )
    
    # 後方影響分析
    backward_results = # 同様のクエリ
    
    # リスクスコア計算
    risk_score = calculate_change_risk_score(request.file_path)
    
    # 循環依存チェック
    circular_deps = detect_circular_dependencies(request.file_path)
    
    return ImpactAnalysisResponse(
        target_file=request.file_path,
        forward_impact=forward_results,
        backward_impact=backward_results,
        risk_score=risk_score,
        circular_dependencies=circular_deps
    )

@app.post("/api/v1/analyze/method/{method_id}")
async def analyze_method_impact(method_id: str, depth: int = 3):
    """
    特定メソッドの呼び出し影響を分析
    """
    query = """
    MATCH (method:Method {id: $methodId})
    MATCH path = (method)-[:CALLS*1..$depth]->(called:Method)
    MATCH (called)<-[:CONTAINS]-(class:Class)<-[:CONTAINS]-(file:File)
    RETURN DISTINCT file.path, class.name, called.name, length(path) as depth
    ORDER BY depth
    """
    
    results = neo4j_driver.execute_query(query, methodId=method_id, depth=depth)
    return {"method_id": method_id, "called_methods": results}

@app.get("/api/v1/search/code")
async def search_code(query: str, language: Optional[str] = None):
    """
    コード要素の全文検索
    """
    cypher_query = """
    CALL db.index.fulltext.queryNodes('method_search_idx', $searchQuery)
    YIELD node, score
    WHERE $language IS NULL OR node.language = $language
    RETURN node.name as name, 
           node.signature as signature, 
           score
    ORDER BY score DESC
    LIMIT 20
    """
    
    results = neo4j_driver.execute_query(
        cypher_query, 
        searchQuery=query, 
        language=language
    )
    return {"results": results}

@app.get("/api/v1/stats/project")
async def get_project_statistics():
    """
    プロジェクト全体の統計情報
    """
    stats_query = """
    MATCH (f:File)
    OPTIONAL MATCH (f)-[:CONTAINS]->(c:Class)
    OPTIONAL MATCH (c)-[:CONTAINS]->(m:Method)
    RETURN count(DISTINCT f) as totalFiles,
           count(DISTINCT c) as totalClasses,
           count(DISTINCT m) as totalMethods,
           avg(f.complexity) as avgFileComplexity,
           sum(f.linesOfCode) as totalLinesOfCode
    """
    
    stats = neo4j_driver.execute_query(stats_query).single()
    
    # 言語別の分布
    lang_query = """
    MATCH (f:File)
    RETURN f.language as language, count(f) as fileCount
    ORDER BY fileCount DESC
    """
    
    lang_distribution = neo4j_driver.execute_query(lang_query)
    
    return {
        "total_statistics": stats,
        "language_distribution": lang_distribution
    }
```

### 6.2 リアルタイム更新 (WebSocket)

```python
from fastapi import WebSocket

@app.websocket("/ws/analysis")
async def websocket_analysis_progress(websocket: WebSocket):
    """
    解析進捗のリアルタイム通知
    """
    await websocket.accept()
    
    async for message in redis_subscriber.listen():
        if message['type'] == 'message':
            progress_data = json.loads(message['data'])
            await websocket.send_json(progress_data)
```

---

## 7. 可視化UI設計

### 7.1 主要画面構成

#### 7.1.1 プロジェクトダッシュボード
```
┌────────────────────────────────────────────────────────┐
│  プロジェクト概要                                       │
│  ┌──────────┬──────────┬──────────┬──────────┐       │
│  │ ファイル数│ クラス数 │ メソッド数│ 言語数   │       │
│  │  35,000  │  12,450  │  89,320  │    5     │       │
│  └──────────┴──────────┴──────────┴──────────┘       │
│                                                         │
│  言語別分布 (円グラフ)                                  │
│  ┌────────────────────────────────────────┐           │
│  │  Java: 45%  TypeScript: 30%            │           │
│  │  C#: 15%    Go: 7%    Angular: 3%      │           │
│  └────────────────────────────────────────┘           │
│                                                         │
│  高リスクファイル Top 10                                │
│  1. UserService.java (リスクスコア: 8.5)               │
│  2. PaymentProcessor.cs (リスクスコア: 7.9)            │
│  ...                                                   │
└────────────────────────────────────────────────────────┘
```

#### 7.1.2 影響範囲分析画面
```
┌────────────────────────────────────────────────────────┐
│  ファイル: /src/main/service/UserService.java         │
│  リスクスコア: ████████░░ 8.5/10                      │
│                                                         │
│  ┌─────────────────┬─────────────────┐               │
│  │ 前方影響 (15)   │ 後方依存 (23)   │               │
│  ├─────────────────┼─────────────────┤               │
│  │ • AuthService   │ • UserController│               │
│  │ • EmailService  │ • LoginModule   │               │
│  │ • CacheManager  │ • APIGateway    │               │
│  │   ...           │   ...           │               │
│  └─────────────────┴─────────────────┘               │
│                                                         │
│  [インタラクティブグラフビュー]                         │
│  ┌────────────────────────────────────────┐           │
│  │          ●─────●─────●                 │           │
│  │         /│      \     │                 │           │
│  │        ● │       ●────●                 │           │
│  │         \│      /                       │           │
│  │          ●─────●                        │           │
│  └────────────────────────────────────────┘           │
│                                                         │
│  循環依存: 検出されました (3件)                        │
│  • UserService ↔ AuthService ↔ TokenManager           │
└────────────────────────────────────────────────────────┘
```

#### 7.1.3 メソッド呼び出しツリー
```
UserService.createUser()
├─ validateEmail()
│  └─ EmailValidator.isValid()
├─ hashPassword()
│  └─ BCryptService.hash()
├─ database.insert()
│  ├─ ConnectionPool.getConnection()
│  └─ QueryBuilder.build()
└─ notifyAdmins()
   └─ EmailService.send()
      ├─ TemplateEngine.render()
      └─ SMTPClient.sendMail()
```

### 7.2 React + D3.js 実装例

```typescript
// ImpactGraphVisualization.tsx
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ImpactGraphProps {
  targetFile: string;
  impactData: ImpactAnalysisResponse;
}

export const ImpactGraphVisualization: React.FC<ImpactGraphProps> = ({
  targetFile,
  impactData
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (!svgRef.current) return;
    
    // D3.jsでグラフを描画
    const width = 1200;
    const height = 800;
    
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);
    
    // ノードとエッジのデータ準備
    const nodes = [
      { id: targetFile, type: 'target', level: 0 },
      ...impactData.forward_impact.map((item, idx) => ({
        id: item.file,
        type: 'affected',
        level: item.distance
      }))
    ];
    
    const links = impactData.forward_impact.map(item => ({
      source: targetFile,
      target: item.file,
      distance: item.distance
    }));
    
    // Force-directed layout
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));
    
    // リンクを描画
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.max(1, 3 - d.distance));
    
    // ノードを描画
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', d => d.type === 'target' ? 12 : 8)
      .attr('fill', d => d.type === 'target' ? '#ff6b6b' : '#4dabf7')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
    
    // ラベルを追加
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text(d => d.id.split('/').pop())
      .attr('font-size', 10)
      .attr('dx', 12)
      .attr('dy', 4);
    
    // ツールチップ
    node.append('title')
      .text(d => `${d.id}\nレベル: ${d.level}`);
    
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
      
      label
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });
    
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
  }, [targetFile, impactData]);
  
  return <svg ref={svgRef}></svg>;
};
```

---

## 8. 実装ロードマップ

### フェーズ1: 基盤構築 (Week 1-2)
- Neo4j環境のセットアップ
- データモデルの実装
- Celery + RabbitMQの構成
- 基本的なファイルスキャナーの実装

**成果物**:
- Neo4jスキーマスクリプト
- Docker Compose設定
- ファイル発見・分類モジュール

### フェーズ2: 言語パーサーの実装 (Week 3-6)
- Java解析エンジン (JavaParser + Eclipse JDT)
- TypeScript/Angular解析 (TS Compiler API)
- Go解析 (標準ライブラリ)
- C#解析 (Roslyn)
- Tree-sitterによる統一インターフェース

**成果物**:
- 各言語のAnalyzerクラス
- 共通のAnalysisResultフォーマット
- ユニットテストスイート

### フェーズ3: グラフ構築 (Week 7-8)
- ノード・エッジの生成ロジック
- Neo4jへのバルクインポート
- 増分更新の実装
- チェックサム管理

**成果物**:
- GraphBuilderモジュール
- インポートスクリプト
- 増分更新パイプライン

### フェーズ4: 分析アルゴリズム (Week 9-10)
- 影響範囲分析Cypherクエリ
- リスクスコア計算
- 循環依存検出
- パフォーマンス最適化

**成果物**:
- Cypherクエリライブラリ
- 分析アルゴリズムの実装
- パフォーマンスベンチマーク

### フェーズ5: API開発 (Week 11-12)
- FastAPI エンドポイント
- WebSocket実装
- 認証・認可
- APIドキュメント

**成果物**:
- RESTful API
- OpenAPI仕様書
- Postmanコレクション

### フェーズ6: UI開発 (Week 13-16)
- Reactダッシュボード
- D3.jsグラフ可視化
- 検索機能
- レスポンシブデザイン

**成果物**:
- Webアプリケーション
- ユーザーマニュアル

### フェーズ7: 最適化・本番化 (Week 17-18)
- 35,000ファイルでの負荷テスト
- メモリ使用量の最適化
- Neo4jクエリのチューニング
- CI/CDパイプライン

**成果物**:
- 本番環境構成
- 運用マニュアル
- モニタリングダッシュボード

---

## 9. パフォーマンス要件

### 9.1 処理性能目標

| 処理 | 目標 | 測定方法 |
|-----|------|---------|
| 単一ファイル解析 | < 500ms | 平均処理時間 |
| プロジェクト全体の初回解析 | < 2時間 | 35,000ファイル |
| 増分解析 (100ファイル変更) | < 5分 | Gitコミット後 |
| 影響範囲クエリ | < 3秒 | 深さ5まで |
| グラフ可視化の描画 | < 1秒 | 500ノードまで |

### 9.2 スケーラビリティ戦略

```python
# 並列度の動的調整
def calculate_optimal_workers(total_files: int, available_memory_gb: int) -> int:
    """
    システムリソースに基づいて最適なワーカー数を計算
    """
    # メモリベースの計算 (1ワーカーあたり2GB想定)
    memory_based_workers = available_memory_gb // 2
    
    # ファイル数ベースの計算 (1ワーカーあたり500ファイル想定)
    file_based_workers = total_files // 500
    
    # CPU数の考慮
    cpu_count = os.cpu_count()
    
    # 最も制約の厳しい値を採用
    optimal_workers = min(memory_based_workers, file_based_workers, cpu_count - 2)
    
    return max(optimal_workers, 4)  # 最低4ワーカー
```

### 9.3 Neo4jチューニング

```properties
# neo4j.conf の推奨設定 (35,000ファイル規模)

# メモリ設定
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=4G

# トランザクション設定
dbms.transaction.timeout=60s
dbms.transaction.bookmark_ready_timeout=30s

# クエリキャッシュ
dbms.query_cache_size=1000

# 並列処理
dbms.cypher.parallel.number_of_workers=8

# インデックス設定
dbms.index.fulltext.eventually_consistent=false
```

---

## 10. 運用・保守

### 10.1 モニタリング指標

```python
from prometheus_client import Counter, Histogram, Gauge

# メトリクス定義
files_analyzed = Counter('files_analyzed_total', 'Total files analyzed')
analysis_duration = Histogram('analysis_duration_seconds', 'Analysis duration')
neo4j_query_duration = Histogram('neo4j_query_seconds', 'Neo4j query duration')
graph_size = Gauge('graph_total_nodes', 'Total nodes in graph')
circular_dependencies = Gauge('circular_dependencies_count', 'Circular dependencies')

@app.on_event("startup")
async def setup_metrics():
    # 定期的にグラフサイズを更新
    async def update_graph_metrics():
        while True:
            result = neo4j_driver.execute_query("MATCH (n) RETURN count(n) as count")
            graph_size.set(result.single()['count'])
            await asyncio.sleep(300)  # 5分ごと
    
    asyncio.create_task(update_graph_metrics())
```

### 10.2 エラーハンドリング

```python
class AnalysisError(Exception):
    """解析エラーの基底クラス"""
    pass

class ParsingError(AnalysisError):
    """パース失敗"""
    pass

class GraphUpdateError(AnalysisError):
    """グラフ更新失敗"""
    pass

@celery.task(bind=True, max_retries=3)
def resilient_analyze_file(self, file_path: str):
    """
    リトライ機能付きファイル解析
    """
    try:
        result = analyze_file(file_path)
        return result
    except ParsingError as e:
        # パースエラーは致命的ではない場合がある
        logger.warning(f"Parsing failed for {file_path}: {e}")
        # 部分的な結果を保存
        save_partial_result(file_path, error=str(e))
    except GraphUpdateError as e:
        # グラフ更新エラーはリトライ
        logger.error(f"Graph update failed: {e}")
        raise self.retry(exc=e, countdown=60)  # 60秒後にリトライ
    except Exception as e:
        # その他のエラー
        logger.exception(f"Unexpected error analyzing {file_path}")
        raise
```

### 10.3 バックアップ戦略

```bash
# Neo4jデータベースの定期バックアップ
#!/bin/bash

BACKUP_DIR="/backup/neo4j"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# オンラインバックアップ
neo4j-admin database backup \
    --database=neo4j \
    --to-path=$BACKUP_DIR/backup_$TIMESTAMP \
    --type=full

# 7日以上古いバックアップを削除
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;

# S3へのアップロード (オプション)
aws s3 sync $BACKUP_DIR s3://your-bucket/neo4j-backups/
```

---

## 11. セキュリティ考慮事項

### 11.1 アクセス制御

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    JWTトークンからユーザーを取得
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except JWTError:
        raise HTTPException(status_code=401)

@app.post("/api/v1/analyze/impact")
async def analyze_impact(
    request: ImpactAnalysisRequest,
    current_user: str = Depends(get_current_user)
):
    """
    認証が必要なエンドポイント
    """
    # 実装
    pass
```

### 11.2 機密情報の除外

```python
def sanitize_code_content(content: str) -> str:
    """
    コード内容から機密情報を除去
    """
    # APIキー、パスワードなどのパターンマッチング
    patterns = [
        r'password\s*=\s*["\'].*?["\']',
        r'api[_-]?key\s*=\s*["\'].*?["\']',
        r'secret\s*=\s*["\'].*?["\']',
    ]
    
    sanitized = content
    for pattern in patterns:
        sanitized = re.sub(pattern, 'password="***"', sanitized, flags=re.IGNORECASE)
    
    return sanitized
```

---

## 12. 拡張性への配慮

### 12.1 新言語追加のインターフェース

```python
from abc import ABC, abstractmethod

class LanguageAnalyzer(ABC):
    """
    すべての言語アナライザーの基底クラス
    """
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """ファイルを解析"""
        pass
    
    @abstractmethod
    def extract_dependencies(self, ast) -> List[Dependency]:
        """依存関係を抽出"""
        pass
    
    @abstractmethod
    def extract_calls(self, ast) -> List[CallRelation]:
        """関数呼び出しを抽出"""
        pass
    
    @abstractmethod
    def analyze_data_flow(self, ast) -> List[DataFlow]:
        """データフローを解析"""
        pass

# 新言語を追加する場合
class RustAnalyzer(LanguageAnalyzer):
    def analyze_file(self, file_path: str) -> AnalysisResult:
        # Rustの解析実装
        pass
    
    # 他のメソッドも実装

# 登録
LANGUAGE_ANALYZERS = {
    'java': JavaAnalyzer(),
    'typescript': TypeScriptAnalyzer(),
    'go': GoAnalyzer(),
    'csharp': CSharpAnalyzer(),
    'rust': RustAnalyzer(),  # 新言語を追加
}
```

### 12.2 プラグインアーキテクチャ

```python
class AnalysisPlugin:
    """
    カスタム分析ロジックを追加するためのプラグイン
    """
    def pre_analysis(self, file_path: str):
        """解析前フック"""
        pass
    
    def post_analysis(self, result: AnalysisResult):
        """解析後フック"""
        pass
    
    def custom_analysis(self, ast) -> Dict[str, Any]:
        """カスタム解析"""
        pass

# プラグインの使用例
class SecurityVulnerabilityPlugin(AnalysisPlugin):
    """
    セキュリティ脆弱性を検出するプラグイン
    """
    def custom_analysis(self, ast) -> Dict[str, Any]:
        vulnerabilities = []
        # SQL injection検出
        # XSS検出
        return {"vulnerabilities": vulnerabilities}
```

---

## 13. 成功指標 (KPI)

### 13.1 技術指標

| 指標 | 目標値 | 測定方法 |
|-----|--------|---------|
| 解析精度 | > 95% | 手動検証との比較 |
| カバレッジ | > 99% | 解析成功ファイル数 / 全ファイル数 |
| 誤検出率 | < 5% | 誤った依存関係の割合 |
| クエリ応答時間 | < 3秒 | P95レスポンスタイム |
| システム稼働率 | > 99.5% | アップタイム |

### 13.2 ビジネス指標

| 指標 | 目標値 | 期待効果 |
|-----|--------|---------|
| バグ調査時間短縮 | 70%減 | 平均30分 → 9分 |
| リファクタリング計画時間 | 80%減 | 影響範囲の事前把握 |
| コードレビュー効率化 | 50%向上 | 自動影響範囲提示 |
| 技術的負債の可視化 | 100% | 循環依存・複雑度の定量化 |

---

## 14. リスクと対策

### 14.1 技術的リスク

| リスク | 影響度 | 対策 |
|-------|--------|------|
| パース失敗による不完全なグラフ | 高 | エラーハンドリング、部分的結果の保存 |
| Neo4jのスケーラビリティ限界 | 中 | シャーディング、キャッシュ戦略 |
| 解析時間の長期化 | 中 | 並列化、増分更新 |
| 動的コード解析の限界 | 低 | 静的解析 + 推定アルゴリズム |

### 14.2 運用リスク

| リスク | 影響度 | 対策 |
|-------|--------|------|
| メモリ不足 | 高 | チャンク処理、ガベージコレクション最適化 |
| ディスク容量不足 | 中 | 定期的なバックアップと古いデータの削除 |
| 解析中のリポジトリ変更 | 低 | ロックメカニズム、バージョン管理 |

---

## 15. 次のステップ

### 15.1 即座に開始できる作業

1. **環境構築**
   ```bash
   # Docker Composeでローカル環境構築
   docker-compose up -d neo4j rabbitmq redis
   ```

2. **プロトタイプ開発**
   - 単一言語(Java)の簡易パーサー
   - Neo4jへの基本的なデータ投入
   - シンプルなCypherクエリの実行

3. **サンプルプロジェクトでの検証**
   - 小規模プロジェクト(100-200ファイル)で動作確認
   - パフォーマンス測定
   - 改善点の洗い出し

### 15.2 追加検討事項

**ご確認いただきたい点**:
1. **CI/CD統合**: GitHubアクション等との連携は必要でしょうか?
2. **通知機能**: 高リスク変更の検出時にSlack/メール通知は必要でしょうか?
3. **レポート出力**: PDF/Excelでのレポート生成機能は必要でしょうか?
4. **AIアシスタント**: 影響範囲分析結果に対するAIによる推奨アクションは必要でしょうか?
5. **マルチリポジトリ対応**: 複数のリポジトリをまたいだ依存関係の追跡は必要でしょうか?

---

## 付録A: サンプルCypherクエリ集

### A.1 最も依存されているファイル Top 10
```cypher
MATCH (f:File)<-[:DEPENDS_ON]-(dependent)
RETURN f.path as file, 
       count(dependent) as dependentCount,
       f.complexity as complexity
ORDER BY dependentCount DESC
LIMIT 10
```

### A.2 最も複雑なメソッド
```cypher
MATCH (m:Method)
WHERE m.complexity > 15
MATCH (m)<-[:CONTAINS]-(c:Class)<-[:CONTAINS]-(f:File)
RETURN f.path, c.name, m.name, m.complexity
ORDER BY m.complexity DESC
LIMIT 20
```

### A.3 孤立したファイルの検出
```cypher
MATCH (f:File)
WHERE NOT (f)-[:DEPENDS_ON]-() AND NOT ()-[:DEPENDS_ON]->(f)
RETURN f.path as isolatedFile
```

### A.4 最長の依存チェーン
```cypher
MATCH path = (start:File)-[:DEPENDS_ON*]->(end:File)
WHERE NOT (end)-[:DEPENDS_ON]->()
RETURN [node in nodes(path) | node.path] as dependencyChain,
       length(path) as chainLength
ORDER BY chainLength DESC
LIMIT 5
```

---

**本仕様書のバージョン**: v1.0  
**最終更新日**: 2025年10月26日  
**次回レビュー予定**: プロトタイプ完成後
