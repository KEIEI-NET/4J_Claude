# Cassandra特化型コード分析システム - 詳細設計書
## Phase 1 プロトタイプ

**バージョン**: v2.0 (Detailed Design)  
**作成日**: 2025年10月26日  
**対象読者**: 実装担当開発者

---

## 📋 目次

1. [アーキテクチャ詳細設計](#1-アーキテクチャ詳細設計)
2. [クラス設計](#2-クラス設計)
3. [データ構造設計](#3-データ構造設計)
4. [アルゴリズム詳細](#4-アルゴリズム詳細)
5. [エラーハンドリング設計](#5-エラーハンドリング設計)
6. [パフォーマンス設計](#6-パフォーマンス設計)
7. [テスト設計](#7-テスト設計)
8. [ログ・モニタリング設計](#8-ログモニタリング設計)

---

## 1. アーキテクチャ詳細設計

### 1.1 レイヤードアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CLI         │  │  HTML Report │  │  JSON Export │      │
│  │  Interface   │  │  Generator   │  │  API         │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         AnalysisOrchestrator                         │   │
│  │  - ファイルスキャン管理                                │   │
│  │  - パイプライン実行                                    │   │
│  │  - 結果集約                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Parsers     │  │  Detectors   │  │  Analyzers   │      │
│  │              │  │              │  │              │      │
│  │ - Java       │  │ - ALLOW      │  │ - Impact     │      │
│  │ - CQL        │  │   FILTERING  │  │   Analysis   │      │
│  │ - AST        │  │ - Partition  │  │ - Metrics    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  FileSystem  │  │  Config      │  │  Cache       │      │
│  │  Reader      │  │  Loader      │  │  Manager     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 処理フロー詳細

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: ファイルスキャン                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
  [ディレクトリ走査]              [ファイルフィルタリング]
        │                                 │
        │  - 再帰的探索                   │  - パターンマッチ
        │  - シンボリックリンク追跡       │  - 除外ルール適用
        │  - 権限チェック                 │  - ファイルサイズ制限
        │                                 │
        └────────────────┬────────────────┘
                         ↓
              [ファイルリスト生成]
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: 並列解析                                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
  [ワーカープール起動]            [タスクキュー生成]
        │                                 │
        │  - スレッド数決定               │  - ファイル分割
        │  - メモリ割り当て               │  - 優先度付け
        │                                 │
        └────────────────┬────────────────┘
                         ↓
              [並列解析実行]
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    [Worker 1]      [Worker 2]      [Worker N]
        │                │                │
        │  ┌─────────────┴────────────┐  │
        └─▶│  ファイル単位の解析       │◀─┘
           │  1. Java構文解析         │
           │  2. CQL抽出              │
           │  3. 問題検出             │
           │  4. 結果記録             │
           └─────────────┬────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: 結果集約                                            │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
  [Issue集約]                    [メトリクス計算]
        │                                 │
        │  - 重複除去                     │  - 重要度別カウント
        │  - 優先度ソート                 │  - ファイル別統計
        │  - ファイル別グループ化         │  - 問題タイプ別統計
        │                                 │
        └────────────────┬────────────────┘
                         ↓
              [AnalysisResult生成]
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: レポート生成                                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
  [HTMLレンダリング]            [JSON/CSV出力]
        │                                 │
        │  - Jinja2テンプレート           │  - 構造化データ
        │  - CSS/JS埋め込み               │  - エクスポート用
        │  - インタラクティブ要素         │
        │                                 │
        └────────────────┬────────────────┘
                         ↓
              [ファイル書き込み]
                         ↓
                    [完了通知]
```

### 1.3 コンポーネント間相互作用

```python
"""
シーケンス図: 単一ファイルの解析フロー
"""

# 1. CLI → AnalysisOrchestrator
CLI.execute(target_path)
    ↓
AnalysisOrchestrator.__init__()
    ↓
# 2. Orchestrator → FileScanner
AnalysisOrchestrator.scan_files()
    ↓
FileScanner.scan_directory(target_path)
    → [file1.java, file2.java, ...]
    ↓
# 3. Orchestrator → AnalysisPipeline
for file in files:
    AnalysisPipeline.analyze_file(file)
        ↓
    # 4. Pipeline → JavaParser
    JavaParser.parse_file(file)
        ↓
    # 4.1 構文解析
    javalang.parse.parse(content)
        → AST
        ↓
    # 4.2 Cassandra呼び出し抽出
    JavaParser._extract_cassandra_calls(AST)
        → [CassandraCall1, CassandraCall2, ...]
        ↓
    # 5. Pipeline → CQLParser
    for call in calls:
        CQLParser.analyze(call.cql_text)
            ↓
        # 5.1 CQL構文解析
        CQLParser._tokenize(cql)
            → tokens
            ↓
        # 5.2 問題パターン検出
        CQLParser._detect_patterns(tokens)
            → CQLAnalysis
            ↓
    # 6. Pipeline → Detectors
    for detector in detectors:
        detector.detect(call, cql_analysis)
            ↓
        # 6.1 ルールマッチング
        detector._match_rules(call, cql_analysis)
            ↓
        # 6.2 Issue生成
        if matched:
            Issue(...)
            ↓
    # 7. Pipeline → ResultCollector
    ResultCollector.add_issues(issues)
    ↓
# 8. Orchestrator → Reporter
AnalysisResult = ResultCollector.finalize()
Reporter.generate(AnalysisResult)
    ↓
# 9. Output
report.html
```

---

## 2. クラス設計

### 2.1 コアクラス図

```
┌─────────────────────────────────────────────────────────────┐
│                    <<interface>>                             │
│                    Parser                                    │
├─────────────────────────────────────────────────────────────┤
│ + parse_file(path: Path): List[ParsedElement]              │
│ + get_supported_extensions(): List[str]                     │
└────────────────────────┬────────────────────────────────────┘
                         △
                         │ implements
        ┌────────────────┼────────────────┐
        │                                 │
┌───────┴────────┐              ┌────────┴───────┐
│ JavaParser     │              │ CQLParser      │
├────────────────┤              ├────────────────┤
│ - tree_walker  │              │ - tokenizer    │
│ - ast_cache    │              │ - grammar      │
├────────────────┤              ├────────────────┤
│ + parse_file() │              │ + analyze()    │
│ - _extract()   │              │ - _tokenize()  │
└────────────────┘              └────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                    <<interface>>                             │
│                    Detector                                  │
├─────────────────────────────────────────────────────────────┤
│ + detect(call, analysis): List[Issue]                       │
│ + get_detector_name(): str                                  │
│ + is_enabled(): bool                                        │
└────────────────────────┬────────────────────────────────────┘
                         △
                         │ implements
        ┌────────────────┼────────────────┬──────────────┐
        │                │                │              │
┌───────┴────────┐ ┌────┴────────┐ ┌─────┴──────┐ ┌────┴─────┐
│AllowFiltering │ │PartitionKey │ │BatchSize   │ │Prepared  │
│Detector        │ │Detector     │ │Detector    │ │Statement │
├────────────────┤ ├─────────────┤ ├────────────┤ │Detector  │
│- severity      │ │- schema_info│ │- threshold │ ├──────────┤
│- patterns      │ │- key_extrac.│ │- counter   │ │- min_exec│
├────────────────┤ ├─────────────┤ ├────────────┤ ├──────────┤
│+ detect()      │ │+ detect()   │ │+ detect()  │ │+ detect()│
└────────────────┘ └─────────────┘ └────────────┘ └──────────┘


┌─────────────────────────────────────────────────────────────┐
│                 AnalysisOrchestrator                         │
├─────────────────────────────────────────────────────────────┤
│ - config: Config                                            │
│ - file_scanner: FileScanner                                 │
│ - pipeline: AnalysisPipeline                                │
│ - result_collector: ResultCollector                         │
│ - thread_pool: ThreadPoolExecutor                           │
├─────────────────────────────────────────────────────────────┤
│ + __init__(config: Config)                                  │
│ + analyze(target: Path): AnalysisResult                     │
│ - _scan_files(target: Path): List[Path]                    │
│ - _analyze_parallel(files: List[Path]): List[Issue]        │
│ - _analyze_single_file(file: Path): List[Issue]            │
│ - _aggregate_results(issues: List[Issue]): AnalysisResult  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 詳細クラス仕様

#### 2.2.1 JavaCassandraParser

```python
"""
JavaCassandraParser - Java AST解析とCassandra呼び出し抽出
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from pathlib import Path
import javalang
import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class CallType(Enum):
    """Cassandra呼び出しのタイプ"""
    EXECUTE = "execute"
    EXECUTE_ASYNC = "executeAsync"
    PREPARE = "prepare"
    BATCH = "batch"
    UNKNOWN = "unknown"

@dataclass
class CassandraCall:
    """
    Cassandra呼び出しの詳細情報
    
    Attributes:
        call_type: 呼び出しタイプ
        cql_text: CQL文字列（定数参照の場合は解決済み）
        cql_is_constant: CQLが定数かどうか
        constant_name: 定数名（定数の場合）
        line_number: 行番号
        column_number: 列番号
        file_path: ファイルパス
        class_name: クラス名
        method_name: メソッド名
        is_prepared: Prepared Statementを使用しているか
        consistency_level: 整合性レベル
        retry_policy: リトライポリシー
        timeout_ms: タイムアウト（ミリ秒）
        is_async: 非同期実行か
        context: 呼び出しコンテキスト（前後3行）
    """
    call_type: CallType
    cql_text: str
    cql_is_constant: bool = False
    constant_name: Optional[str] = None
    line_number: int = 0
    column_number: int = 0
    file_path: str = ""
    class_name: str = ""
    method_name: str = ""
    is_prepared: bool = False
    consistency_level: Optional[str] = None
    retry_policy: Optional[str] = None
    timeout_ms: Optional[int] = None
    is_async: bool = False
    context: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """データの妥当性チェック"""
        if not self.cql_text:
            raise ValueError("cql_text cannot be empty")
        
        if self.line_number < 0:
            raise ValueError("line_number must be non-negative")

class JavaCassandraParser:
    """
    JavaファイルからCassandra関連の操作を抽出
    
    機能:
    1. Java AST解析
    2. Cassandra Session呼び出しの検出
    3. CQL文字列の抽出（定数解決含む）
    4. 整合性レベルの抽出
    5. Prepared Statement判定
    """
    
    # Cassandraセッションメソッドのパターン
    CASSANDRA_METHODS = {
        'execute', 'executeAsync', 'prepare', 
        'batch', 'prepareAsync'
    }
    
    # 整合性レベルのパターン
    CONSISTENCY_LEVEL_PATTERN = re.compile(
        r'ConsistencyLevel\.(ONE|TWO|THREE|QUORUM|ALL|LOCAL_QUORUM|'
        r'EACH_QUORUM|LOCAL_ONE|ANY|SERIAL|LOCAL_SERIAL)'
    )
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初期化
        
        Args:
            config: 設定辞書
                - cache_enabled: ASTキャッシュを有効化 (default: True)
                - context_lines: コンテキスト行数 (default: 3)
                - resolve_constants: 定数を解決するか (default: True)
        """
        self.config = config or {}
        self._cache_enabled = self.config.get('cache_enabled', True)
        self._context_lines = self.config.get('context_lines', 3)
        self._resolve_constants = self.config.get('resolve_constants', True)
        
        # ASTキャッシュ（ファイルハッシュ → AST）
        self._ast_cache: Dict[str, javalang.tree.CompilationUnit] = {}
        
        # 定数キャッシュ（ファイル内の定数定義）
        self._constants_cache: Dict[str, Dict[str, str]] = {}
    
    def parse_file(self, file_path: Path) -> List[CassandraCall]:
        """
        Javaファイルを解析してCassandra呼び出しを抽出
        
        Args:
            file_path: 解析対象のJavaファイルパス
            
        Returns:
            CassandraCallのリスト
            
        Raises:
            FileNotFoundError: ファイルが存在しない
            JavaSyntaxError: Java構文エラー
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Parsing file: {file_path}")
        
        # ファイル読み込み
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode {file_path} as UTF-8, trying latin-1")
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # AST解析（キャッシュチェック）
        file_hash = self._compute_hash(content)
        
        if self._cache_enabled and file_hash in self._ast_cache:
            logger.debug(f"Using cached AST for {file_path}")
            tree = self._ast_cache[file_hash]
        else:
            try:
                tree = javalang.parse.parse(content)
                if self._cache_enabled:
                    self._ast_cache[file_hash] = tree
            except javalang.parser.JavaSyntaxError as e:
                logger.error(f"Syntax error in {file_path}: {e}")
                raise
        
        # 定数の抽出（CQL定数の解決に使用）
        if self._resolve_constants:
            constants = self._extract_constants(tree, content)
            self._constants_cache[str(file_path)] = constants
        else:
            constants = {}
        
        # Cassandra呼び出しの抽出
        calls = []
        lines = content.split('\n')
        
        # クラス名の取得
        class_name = self._get_class_name(tree)
        
        # MethodInvocationノードを走査
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            if self._is_cassandra_call(node):
                call = self._extract_call_info(
                    node, path, content, lines, 
                    file_path, class_name, constants
                )
                if call:
                    calls.append(call)
        
        logger.info(f"Found {len(calls)} Cassandra calls in {file_path}")
        return calls
    
    def _is_cassandra_call(self, node: javalang.tree.MethodInvocation) -> bool:
        """
        Cassandra関連の呼び出しか判定
        
        判定基準:
        1. メソッド名がCassandraセッションメソッドに一致
        2. qualifierがsessionまたはsession-like
        
        Args:
            node: MethodInvocationノード
            
        Returns:
            Cassandra呼び出しの場合True
        """
        # メソッド名チェック
        if node.member not in self.CASSANDRA_METHODS:
            return False
        
        # qualifierチェック（session, getSession(), etc.）
        if hasattr(node, 'qualifier'):
            qualifier_str = str(node.qualifier)
            if 'session' in qualifier_str.lower():
                return True
        
        # qualifierがない場合もある（this.session等）
        return True
    
    def _extract_call_info(
        self,
        node: javalang.tree.MethodInvocation,
        path: List,
        content: str,
        lines: List[str],
        file_path: Path,
        class_name: str,
        constants: Dict[str, str]
    ) -> Optional[CassandraCall]:
        """
        呼び出し情報の詳細抽出
        
        Args:
            node: MethodInvocationノード
            path: ASTパス
            content: ファイル全体の内容
            lines: ファイルの行リスト
            file_path: ファイルパス
            class_name: クラス名
            constants: 定数マップ
            
        Returns:
            CassandraCallオブジェクト、抽出失敗時はNone
        """
        # 行番号・列番号
        line_number = node.position.line if hasattr(node, 'position') else 0
        column_number = node.position.column if hasattr(node, 'position') else 0
        
        # CQL文字列の抽出
        cql_text, is_constant, constant_name = self._extract_cql_string(
            node, constants
        )
        
        if not cql_text:
            logger.debug(f"Could not extract CQL from {file_path}:{line_number}")
            return None
        
        # メソッド名の取得（どのメソッド内の呼び出しか）
        method_name = self._get_enclosing_method_name(path)
        
        # コンテキストの抽出（前後N行）
        context = self._extract_context(lines, line_number, self._context_lines)
        
        # Prepared Statement判定
        is_prepared = (
            node.member in {'prepare', 'prepareAsync'} or
            self._check_prepared_statement_usage(context)
        )
        
        # 整合性レベルの抽出
        consistency_level = self._extract_consistency_level(context)
        
        # リトライポリシーの抽出
        retry_policy = self._extract_retry_policy(context)
        
        # タイムアウトの抽出
        timeout_ms = self._extract_timeout(context)
        
        # 呼び出しタイプの判定
        call_type = self._determine_call_type(node.member)
        
        # 非同期判定
        is_async = 'async' in node.member.lower()
        
        return CassandraCall(
            call_type=call_type,
            cql_text=cql_text,
            cql_is_constant=is_constant,
            constant_name=constant_name,
            line_number=line_number,
            column_number=column_number,
            file_path=str(file_path),
            class_name=class_name,
            method_name=method_name,
            is_prepared=is_prepared,
            consistency_level=consistency_level,
            retry_policy=retry_policy,
            timeout_ms=timeout_ms,
            is_async=is_async,
            context=context
        )
    
    def _extract_cql_string(
        self, 
        node: javalang.tree.MethodInvocation,
        constants: Dict[str, str]
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        メソッド引数からCQL文字列を抽出
        
        抽出パターン:
        1. 文字列リテラル: "SELECT ..."
        2. 文字列連結: "SELECT " + "* FROM users"
        3. 定数参照: CQL_SELECT_USER
        4. StringBuilder: new StringBuilder().append("SELECT")...
        
        Args:
            node: MethodInvocationノード
            constants: 定数マップ
            
        Returns:
            (CQL文字列, 定数フラグ, 定数名)のタプル
        """
        if not node.arguments:
            return None, False, None
        
        first_arg = node.arguments[0]
        
        # パターン1: 文字列リテラル
        if isinstance(first_arg, javalang.tree.Literal):
            cql = first_arg.value.strip('"\'')
            return cql, False, None
        
        # パターン2: 定数参照
        if isinstance(first_arg, javalang.tree.MemberReference):
            constant_name = first_arg.member
            if constant_name in constants:
                cql = constants[constant_name]
                return cql, True, constant_name
            else:
                # 定数が解決できない場合はプレースホルダー
                return f"[CONSTANT: {constant_name}]", True, constant_name
        
        # パターン3: 文字列連結（BinaryOperation）
        if isinstance(first_arg, javalang.tree.BinaryOperation):
            cql = self._resolve_binary_operation(first_arg, constants)
            return cql, False, None
        
        # パターン4: StringBuilder（後で実装）
        # TODO: StringBuilder.append() チェーンの解析
        
        return None, False, None
    
    def _extract_constants(
        self, 
        tree: javalang.tree.CompilationUnit,
        content: str
    ) -> Dict[str, str]:
        """
        ファイル内の定数定義を抽出
        
        抽出対象:
        - public static final String CQL_XXX = "...";
        - private static final String QUERY_YYY = "...";
        
        Args:
            tree: AST
            content: ファイル内容
            
        Returns:
            定数名 → 定数値のマップ
        """
        constants = {}
        
        for _, node in tree.filter(javalang.tree.FieldDeclaration):
            # static final チェック
            if not ('static' in node.modifiers and 'final' in node.modifiers):
                continue
            
            # String型チェック
            if node.type.name != 'String':
                continue
            
            # 値の抽出
            for declarator in node.declarators:
                if declarator.initializer:
                    if isinstance(declarator.initializer, javalang.tree.Literal):
                        value = declarator.initializer.value.strip('"\'')
                        constants[declarator.name] = value
        
        return constants
    
    def _check_prepared_statement_usage(self, context: List[str]) -> bool:
        """
        コンテキストからPrepared Statementの使用を判定
        
        判定パターン:
        - PreparedStatement ps = ...
        - BoundStatement bound = ...
        - session.prepare()の呼び出し
        
        Args:
            context: コンテキスト行
            
        Returns:
            Prepared Statement使用の場合True
        """
        context_str = '\n'.join(context)
        
        patterns = [
            r'PreparedStatement\s+\w+',
            r'BoundStatement\s+\w+',
            r'\.prepare\s*\(',
            r'\.bind\s*\('
        ]
        
        for pattern in patterns:
            if re.search(pattern, context_str):
                return True
        
        return False
    
    def _extract_consistency_level(self, context: List[str]) -> Optional[str]:
        """
        コンテキストから整合性レベルを抽出
        
        抽出パターン:
        - .setConsistencyLevel(ConsistencyLevel.QUORUM)
        - ConsistencyLevel.ONE
        
        Args:
            context: コンテキスト行
            
        Returns:
            整合性レベル（例: "QUORUM"）、見つからない場合None
        """
        context_str = '\n'.join(context)
        
        match = self.CONSISTENCY_LEVEL_PATTERN.search(context_str)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_retry_policy(self, context: List[str]) -> Optional[str]:
        """リトライポリシーの抽出"""
        context_str = '\n'.join(context)
        
        patterns = [
            r'DefaultRetryPolicy',
            r'DowngradingConsistencyRetryPolicy',
            r'FallthroughRetryPolicy',
            r'LoggingRetryPolicy'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context_str)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_timeout(self, context: List[str]) -> Optional[int]:
        """タイムアウト設定の抽出"""
        context_str = '\n'.join(context)
        
        # setTimeout(5000) のようなパターン
        match = re.search(r'setTimeout\s*\(\s*(\d+)\s*\)', context_str)
        if match:
            return int(match.group(1))
        
        return None
    
    def _extract_context(
        self, 
        lines: List[str], 
        line_number: int, 
        context_lines: int
    ) -> List[str]:
        """
        指定行の前後コンテキストを抽出
        
        Args:
            lines: ファイルの全行
            line_number: 対象行番号（1-indexed）
            context_lines: 前後の行数
            
        Returns:
            コンテキスト行のリスト
        """
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        return lines[start:end]
    
    def _get_class_name(self, tree: javalang.tree.CompilationUnit) -> str:
        """ASTからクラス名を取得"""
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            return node.name
        return "Unknown"
    
    def _get_enclosing_method_name(self, path: List) -> str:
        """ASTパスから包含メソッド名を取得"""
        for node in reversed(path):
            if isinstance(node, javalang.tree.MethodDeclaration):
                return node.name
        return "unknown"
    
    def _determine_call_type(self, method_name: str) -> CallType:
        """メソッド名から呼び出しタイプを判定"""
        method_lower = method_name.lower()
        
        if 'prepare' in method_lower:
            return CallType.PREPARE
        elif 'batch' in method_lower:
            return CallType.BATCH
        elif 'async' in method_lower:
            return CallType.EXECUTE_ASYNC
        elif 'execute' in method_lower:
            return CallType.EXECUTE
        else:
            return CallType.UNKNOWN
    
    def _compute_hash(self, content: str) -> str:
        """ファイル内容のハッシュを計算"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _resolve_binary_operation(
        self,
        node: javalang.tree.BinaryOperation,
        constants: Dict[str, str]
    ) -> str:
        """
        文字列連結（BinaryOperation）を解決
        
        例: "SELECT " + "* FROM users" → "SELECT * FROM users"
        
        Args:
            node: BinaryOperationノード
            constants: 定数マップ
            
        Returns:
            連結後の文字列
        """
        # TODO: 再帰的に左右のオペランドを解決
        # 簡易実装: 左右がリテラルの場合のみ対応
        left = ""
        right = ""
        
        if isinstance(node.operandl, javalang.tree.Literal):
            left = node.operandl.value.strip('"\'')
        
        if isinstance(node.operandr, javalang.tree.Literal):
            right = node.operandr.value.strip('"\'')
        
        return left + right
```

#### 2.2.2 CQLParser

```python
"""
CQLParser - CQL文字列の解析と問題パターン検出
"""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class QueryType(Enum):
    """クエリタイプ"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BATCH = "BATCH"
    CREATE_TABLE = "CREATE TABLE"
    ALTER_TABLE = "ALTER TABLE"
    DROP_TABLE = "DROP TABLE"
    CREATE_INDEX = "CREATE INDEX"
    TRUNCATE = "TRUNCATE"
    UNKNOWN = "UNKNOWN"

@dataclass
class WhereClause:
    """WHERE句の詳細情報"""
    raw_text: str
    conditions: List[Dict[str, any]] = field(default_factory=list)
    has_partition_key_filter: bool = False
    has_clustering_key_filter: bool = False
    uses_in_clause: bool = False
    uses_range_query: bool = False
    filter_columns: Set[str] = field(default_factory=set)

@dataclass
class CQLAnalysis:
    """
    CQL分析結果
    
    Attributes:
        query_type: クエリタイプ
        tables: 対象テーブル名のリスト
        has_allow_filtering: ALLOW FILTERINGの使用有無
        where_clause: WHERE句の詳細
        is_batch: BATCH処理か
        batch_size: BATCH内のステートメント数
        uses_prepared_statement_marker: ?マーカー使用有無
        select_columns: SELECT対象カラム
        consistency_level_in_cql: CQL内の整合性レベル指定
        limit_clause: LIMIT値
        order_by_clause: ORDER BY句
        issues: 検出された問題
    """
    query_type: QueryType
    tables: List[str]
    has_allow_filtering: bool = False
    where_clause: Optional[WhereClause] = None
    is_batch: bool = False
    batch_size: int = 0
    uses_prepared_statement_marker: bool = False
    select_columns: List[str] = field(default_factory=list)
    consistency_level_in_cql: Optional[str] = None
    limit_clause: Optional[int] = None
    order_by_clause: Optional[str] = None
    issues: List[Dict] = field(default_factory=list)

class CQLParser:
    """
    CQL文を解析して構造と問題を検出
    
    機能:
    1. CQLトークン化
    2. クエリタイプの判定
    3. WHERE句の詳細解析
    4. 問題パターンの検出
    """
    
    # CQLキーワード
    KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'UPDATE', 'DELETE',
        'SET', 'VALUES', 'AND', 'OR', 'IN', 'ALLOW', 'FILTERING',
        'ORDER', 'BY', 'LIMIT', 'USING', 'TTL', 'TIMESTAMP',
        'BEGIN', 'BATCH', 'APPLY', 'UNLOGGED', 'COUNTER'
    }
    
    # 比較演算子
    OPERATORS = {'=', '>', '<', '>=', '<=', '!='}
    
    def __init__(self, schema_info: Optional[Dict] = None):
        """
        初期化
        
        Args:
            schema_info: スキーマ情報（テーブル定義、キー情報など）
                {
                    'table_name': {
                        'partition_keys': ['user_id'],
                        'clustering_keys': ['created_at'],
                        'columns': ['user_id', 'name', 'email', ...]
                    }
                }
        """
        self.schema_info = schema_info or {}
    
    def analyze(self, cql: str) -> CQLAnalysis:
        """
        CQL文を分析
        
        Args:
            cql: 分析対象のCQL文
            
        Returns:
            CQLAnalysisオブジェクト
        """
        if not cql or not cql.strip():
            raise ValueError("CQL cannot be empty")
        
        # 正規化（余分な空白削除、大文字化）
        cql_normalized = self._normalize_cql(cql)
        cql_upper = cql_normalized.upper()
        
        # クエリタイプの判定
        query_type = self._determine_query_type(cql_upper)
        
        # テーブル名の抽出
        tables = self._extract_tables(cql_normalized, query_type)
        
        # ALLOW FILTERINGチェック
        has_allow_filtering = 'ALLOW FILTERING' in cql_upper
        
        # WHERE句の解析
        where_clause = self._parse_where_clause(cql_normalized, tables)
        
        # BATCH処理チェック
        is_batch = 'BEGIN BATCH' in cql_upper or 'BEGIN UNLOGGED BATCH' in cql_upper
        batch_size = self._count_batch_statements(cql_normalized) if is_batch else 0
        
        # Prepared Statementマーカーチェック
        uses_prepared = '?' in cql
        
        # SELECT句の解析
        select_columns = []
        if query_type == QueryType.SELECT:
            select_columns = self._extract_select_columns(cql_normalized)
        
        # LIMIT句
        limit_clause = self._extract_limit(cql_normalized)
        
        # ORDER BY句
        order_by_clause = self._extract_order_by(cql_normalized)
        
        # 分析結果の構築
        analysis = CQLAnalysis(
            query_type=query_type,
            tables=tables,
            has_allow_filtering=has_allow_filtering,
            where_clause=where_clause,
            is_batch=is_batch,
            batch_size=batch_size,
            uses_prepared_statement_marker=uses_prepared,
            select_columns=select_columns,
            limit_clause=limit_clause,
            order_by_clause=order_by_clause
        )
        
        # 問題の検出
        analysis.issues = self._detect_issues(analysis, cql)
        
        return analysis
    
    def _normalize_cql(self, cql: str) -> str:
        """
        CQLを正規化
        
        - 余分な空白を削除
        - 改行を空白に変換
        - 連続した空白を1つに
        
        Args:
            cql: 元のCQL
            
        Returns:
            正規化されたCQL
        """
        # 改行を空白に
        cql = cql.replace('\n', ' ').replace('\r', ' ')
        
        # 連続空白を1つに
        cql = re.sub(r'\s+', ' ', cql)
        
        # 前後の空白を削除
        cql = cql.strip()
        
        return cql
    
    def _determine_query_type(self, cql_upper: str) -> QueryType:
        """クエリタイプの判定"""
        if cql_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif cql_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif cql_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif cql_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif 'BEGIN BATCH' in cql_upper or 'BEGIN UNLOGGED BATCH' in cql_upper:
            return QueryType.BATCH
        elif cql_upper.startswith('CREATE TABLE'):
            return QueryType.CREATE_TABLE
        elif cql_upper.startswith('ALTER TABLE'):
            return QueryType.ALTER_TABLE
        elif cql_upper.startswith('DROP TABLE'):
            return QueryType.DROP_TABLE
        elif cql_upper.startswith('CREATE INDEX'):
            return QueryType.CREATE_INDEX
        elif cql_upper.startswith('TRUNCATE'):
            return QueryType.TRUNCATE
        else:
            return QueryType.UNKNOWN
    
    def _extract_tables(self, cql: str, query_type: QueryType) -> List[str]:
        """
        CQLからテーブル名を抽出
        
        Args:
            cql: CQL文
            query_type: クエリタイプ
            
        Returns:
            テーブル名のリスト
        """
        tables = []
        
        # FROM句（SELECT, DELETE）
        from_match = re.findall(r'FROM\s+(\w+)', cql, re.IGNORECASE)
        tables.extend(from_match)
        
        # INTO句（INSERT）
        into_match = re.findall(r'INTO\s+(\w+)', cql, re.IGNORECASE)
        tables.extend(into_match)
        
        # UPDATE句
        if query_type == QueryType.UPDATE:
            update_match = re.findall(r'UPDATE\s+(\w+)', cql, re.IGNORECASE)
            tables.extend(update_match)
        
        # CREATE TABLE
        if query_type == QueryType.CREATE_TABLE:
            create_match = re.findall(r'CREATE\s+TABLE\s+(\w+)', cql, re.IGNORECASE)
            tables.extend(create_match)
        
        # 重複削除
        return list(set(tables))
    
    def _parse_where_clause(
        self, 
        cql: str, 
        tables: List[str]
    ) -> Optional[WhereClause]:
        """
        WHERE句の詳細解析
        
        Args:
            cql: CQL文
            tables: テーブル名リスト
            
        Returns:
            WhereClauseオブジェクト、WHERE句がない場合None
        """
        # WHERE句の抽出
        where_match = re.search(
            r'WHERE\s+(.+?)(?:ALLOW|ORDER|LIMIT|;|$)', 
            cql, 
            re.IGNORECASE
        )
        
        if not where_match:
            return None
        
        where_text = where_match.group(1).strip()
        
        # 条件の解析
        conditions = self._parse_conditions(where_text)
        
        # フィルタ対象カラムの抽出
        filter_columns = {cond['column'] for cond in conditions}
        
        # Partition Key判定（スキーマ情報があれば）
        has_partition_key = False
        has_clustering_key = False
        
        if tables and self.schema_info:
            table = tables[0]  # 最初のテーブルで判定
            if table in self.schema_info:
                schema = self.schema_info[table]
                partition_keys = set(schema.get('partition_keys', []))
                clustering_keys = set(schema.get('clustering_keys', []))
                
                has_partition_key = bool(filter_columns & partition_keys)
                has_clustering_key = bool(filter_columns & clustering_keys)
        
        # IN句の使用
        uses_in = 'IN' in where_text.upper()
        
        # 範囲クエリ（>, <, >=, <=）の使用
        uses_range = any(op in where_text for op in ['>', '<', '>=', '<='])
        
        return WhereClause(
            raw_text=where_text,
            conditions=conditions,
            has_partition_key_filter=has_partition_key,
            has_clustering_key_filter=has_clustering_key,
            uses_in_clause=uses_in,
            uses_range_query=uses_range,
            filter_columns=filter_columns
        )
    
    def _parse_conditions(self, where_text: str) -> List[Dict]:
        """
        WHERE句の条件を個別に解析
        
        Args:
            where_text: WHERE句のテキスト
            
        Returns:
            条件のリスト
                [
                    {'column': 'user_id', 'operator': '=', 'value': '?'},
                    {'column': 'status', 'operator': 'IN', 'value': ['active', 'pending']}
                ]
        """
        conditions = []
        
        # AND/ORで分割
        parts = re.split(r'\s+AND\s+|\s+OR\s+', where_text, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            
            # 等価条件: column = value
            match = re.match(r'(\w+)\s*=\s*(.+)', part)
            if match:
                conditions.append({
                    'column': match.group(1),
                    'operator': '=',
                    'value': match.group(2).strip()
                })
                continue
            
            # IN句: column IN (...)
            match = re.match(r'(\w+)\s+IN\s*\((.+?)\)', part, re.IGNORECASE)
            if match:
                conditions.append({
                    'column': match.group(1),
                    'operator': 'IN',
                    'value': match.group(2).strip()
                })
                continue
            
            # 範囲条件: column > value
            match = re.match(r'(\w+)\s*(>=?|<=?)\s*(.+)', part)
            if match:
                conditions.append({
                    'column': match.group(1),
                    'operator': match.group(2),
                    'value': match.group(3).strip()
                })
                continue
        
        return conditions
    
    def _count_batch_statements(self, cql: str) -> int:
        """BATCH内のステートメント数をカウント"""
        # セミコロンで分割してカウント
        statements = cql.split(';')
        
        # BEGIN BATCHとAPPLY BATCHを除外
        count = 0
        for stmt in statements:
            stmt_upper = stmt.strip().upper()
            if stmt_upper and \
               'BEGIN' not in stmt_upper and \
               'APPLY' not in stmt_upper:
                count += 1
        
        return count
    
    def _extract_select_columns(self, cql: str) -> List[str]:
        """SELECT対象カラムを抽出"""
        match = re.search(r'SELECT\s+(.+?)\s+FROM', cql, re.IGNORECASE)
        if not match:
            return []
        
        columns_text = match.group(1).strip()
        
        # SELECT * の場合
        if columns_text == '*':
            return ['*']
        
        # カンマ区切りでカラムを抽出
        columns = [col.strip() for col in columns_text.split(',')]
        return columns
    
    def _extract_limit(self, cql: str) -> Optional[int]:
        """LIMIT句を抽出"""
        match = re.search(r'LIMIT\s+(\d+)', cql, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_order_by(self, cql: str) -> Optional[str]:
        """ORDER BY句を抽出"""
        match = re.search(r'ORDER\s+BY\s+(.+?)(?:LIMIT|ALLOW|;|$)', cql, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _detect_issues(self, analysis: CQLAnalysis, cql: str) -> List[Dict]:
        """
        問題パターンを検出
        
        検出パターン:
        1. ALLOW FILTERING
        2. Partition Key未使用
        3. 大量BATCH
        4. SELECT *
        5. INクエリの過度な使用
        
        Args:
            analysis: CQL分析結果
            cql: 元のCQL文
            
        Returns:
            問題のリスト
        """
        issues = []
        
        # 1. ALLOW FILTERING
        if analysis.has_allow_filtering:
            issues.append({
                'type': 'ALLOW_FILTERING',
                'severity': 'high',
                'message': 'ALLOW FILTERING detected - causes full table scan across all nodes',
                'recommendation': 'Create a Materialized View or redesign the data model to avoid filtering',
                'performance_impact': 'severe'
            })
        
        # 2. Partition Key未使用（SELECTのみ）
        if analysis.query_type == QueryType.SELECT:
            if analysis.where_clause:
                if not analysis.where_clause.has_partition_key_filter:
                    issues.append({
                        'type': 'NO_PARTITION_KEY',
                        'severity': 'critical',
                        'message': 'WHERE clause does not use partition key - requires multi-node scan',
                        'recommendation': 'Add partition key to WHERE clause for single-partition query',
                        'performance_impact': 'severe'
                    })
            else:
                # WHERE句なし
                issues.append({
                    'type': 'NO_WHERE_CLAUSE',
                    'severity': 'critical',
                    'message': 'No WHERE clause - scans entire table',
                    'recommendation': 'Add WHERE clause with partition key',
                    'performance_impact': 'critical'
                })
        
        # 3. 大量BATCH
        if analysis.is_batch and analysis.batch_size > 100:
            issues.append({
                'type': 'LARGE_BATCH',
                'severity': 'medium',
                'message': f'Large batch with {analysis.batch_size} statements - may cause performance issues',
                'recommendation': 'Split batch into chunks of 100 statements or less',
                'performance_impact': 'moderate'
            })
        
        # 4. SELECT *
        if analysis.query_type == QueryType.SELECT:
            if '*' in analysis.select_columns:
                issues.append({
                    'type': 'SELECT_ALL',
                    'severity': 'low',
                    'message': 'SELECT * fetches all columns - may retrieve unnecessary data',
                    'recommendation': 'Specify only required columns explicitly',
                    'performance_impact': 'minor'
                })
        
        # 5. INクエリの過度な使用
        if analysis.where_clause and analysis.where_clause.uses_in_clause:
            # IN句の値の数をチェック（簡易実装）
            in_values_count = cql.count(',')  # 近似
            if in_values_count > 10:
                issues.append({
                    'type': 'LARGE_IN_CLAUSE',
                    'severity': 'medium',
                    'message': f'IN clause with many values (approximately {in_values_count}) - may cause performance issues',
                    'recommendation': 'Limit IN clause values to 10 or split into multiple queries',
                    'performance_impact': 'moderate'
                })
        
        return issues
```

---

## 3. データ構造設計

### 3.1 メモリ内データ構造

```python
"""
分析結果を保持するデータ構造
"""

from typing import Dict, List, Set
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class AnalysisState:
    """
    分析プロセス全体の状態を保持
    
    スレッドセーフな実装が必要
    """
    # ファイル → 問題のマップ
    issues_by_file: Dict[str, List['Issue']] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    # 問題タイプ → 問題のマップ
    issues_by_type: Dict[str, List['Issue']] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    # 重要度 → 問題のマップ
    issues_by_severity: Dict[str, List['Issue']] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    # 処理済みファイル数
    processed_files: int = 0
    
    # 総ファイル数
    total_files: int = 0
    
    # エラーが発生したファイル
    error_files: Set[str] = field(default_factory=set)
    
    # スキップされたファイル
    skipped_files: Set[str] = field(default_factory=set)
    
    def add_issue(self, issue: 'Issue'):
        """スレッドセーフに問題を追加"""
        self.issues_by_file[issue.file_path].append(issue)
        self.issues_by_type[issue.issue_type].append(issue)
        self.issues_by_severity[issue.severity].append(issue)
    
    def increment_processed(self):
        """処理済みファイル数をインクリメント（スレッドセーフ）"""
        # 実装時はthreading.Lockを使用
        self.processed_files += 1
    
    def get_progress(self) -> float:
        """進捗率を取得"""
        if self.total_files == 0:
            return 0.0
        return self.processed_files / self.total_files
```

### 3.2 キャッシュ構造

```python
"""
パフォーマンス向上のためのキャッシュ
"""

from functools import lru_cache
from typing import Optional
import hashlib

class AnalysisCache:
    """
    分析結果のキャッシュ
    
    キャッシュキー: ファイルハッシュ + 設定ハッシュ
    キャッシュ値: 分析結果
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Args:
            max_size: キャッシュの最大サイズ
        """
        self.max_size = max_size
        self._cache: Dict[str, List['Issue']] = {}
        self._access_count: Dict[str, int] = defaultdict(int)
    
    def get(self, file_hash: str, config_hash: str) -> Optional[List['Issue']]:
        """キャッシュから取得"""
        key = f"{file_hash}:{config_hash}"
        
        if key in self._cache:
            self._access_count[key] += 1
            return self._cache[key]
        
        return None
    
    def put(self, file_hash: str, config_hash: str, issues: List['Issue']):
        """キャッシュに保存"""
        key = f"{file_hash}:{config_hash}"
        
        # キャッシュサイズ制限
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        self._cache[key] = issues
        self._access_count[key] = 1
    
    def _evict_lru(self):
        """LRU方式でキャッシュを削除"""
        # アクセス回数が最も少ないエントリを削除
        lru_key = min(self._access_count, key=self._access_count.get)
        del self._cache[lru_key]
        del self._access_count[lru_key]
    
    def invalidate_file(self, file_path: str):
        """特定ファイルのキャッシュを無効化"""
        keys_to_delete = [k for k in self._cache.keys() if file_path in k]
        for key in keys_to_delete:
            del self._cache[key]
            del self._access_count[key]
    
    def clear(self):
        """全キャッシュをクリア"""
        self._cache.clear()
        self._access_count.clear()
```

---

## 4. アルゴリズム詳細

### 4.1 並列処理アルゴリズム

```python
"""
ファイル分析の並列処理アルゴリズム
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable
import multiprocessing

class ParallelAnalyzer:
    """
    並列分析の実行エンジン
    
    ワーカー数の決定:
    - CPU数の75%をデフォルトとする
    - I/O待ちが多い処理なのでCPU数以上も許可
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Args:
            max_workers: ワーカー数（Noneの場合は自動決定）
        """
        if max_workers is None:
            cpu_count = multiprocessing.cpu_count()
            # CPU数の75%、最小2、最大16
            max_workers = max(2, min(16, int(cpu_count * 0.75)))
        
        self.max_workers = max_workers
    
    def analyze_files(
        self,
        files: List[Path],
        analyze_func: Callable[[Path], List['Issue']]
    ) -> List['Issue']:
        """
        ファイルリストを並列分析
        
        Args:
            files: 分析対象ファイルリスト
            analyze_func: 単一ファイル分析関数
            
        Returns:
            全ファイルの問題リスト
            
        アルゴリズム:
        1. ファイルをワーカー数で分割
        2. 各ワーカーに分析タスクを投入
        3. 完了したタスクから結果を収集
        4. プログレスバーを更新
        """
        all_issues = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # タスクの投入
            future_to_file = {
                executor.submit(analyze_func, file): file
                for file in files
            }
            
            # 完了したタスクから結果を収集
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                
                try:
                    issues = future.result(timeout=30)  # 30秒タイムアウト
                    all_issues.extend(issues)
                except Exception as e:
                    logger.error(f"Error analyzing {file}: {e}")
        
        return all_issues
```

### 4.2 問題の優先度付けアルゴリズム

```python
"""
検出された問題に優先度を付与
"""

def calculate_priority_score(issue: 'Issue') -> float:
    """
    問題の優先度スコアを計算
    
    スコア計算式:
        score = severity_weight * confidence * impact_multiplier
    
    Args:
        issue: 問題
        
    Returns:
        優先度スコア（0-100）
    """
    # 重要度の重み
    severity_weights = {
        'critical': 10.0,
        'high': 7.5,
        'medium': 5.0,
        'low': 2.5
    }
    
    base_score = severity_weights.get(issue.severity, 5.0)
    
    # 信頼度で調整
    confidence_adjusted = base_score * issue.confidence
    
    # 影響範囲の係数
    impact_multiplier = 1.0
    
    # Cassandra関連は係数を上げる
    if 'cassandra' in issue.file_path.lower():
        impact_multiplier *= 1.5
    
    # DAOレイヤーは係数を上げる
    if 'dao' in issue.file_path.lower() or 'repository' in issue.file_path.lower():
        impact_multiplier *= 1.3
    
    final_score = confidence_adjusted * impact_multiplier
    
    # 0-100に正規化
    return min(100, final_score * 10)

def sort_issues_by_priority(issues: List['Issue']) -> List['Issue']:
    """問題を優先度順にソート"""
    return sorted(
        issues,
        key=lambda issue: (
            calculate_priority_score(issue),
            issue.severity,
            issue.file_path
        ),
        reverse=True
    )
```

### 4.3 重複検出アルゴリズム

```python
"""
同一問題の重複を検出
"""

def deduplicate_issues(issues: List['Issue']) -> List['Issue']:
    """
    重複する問題を除去
    
    重複判定基準:
    - 同じファイル
    - 同じ行番号
    - 同じ問題タイプ
    - CQL文字列が類似（編集距離で判定）
    
    Args:
        issues: 問題リスト
        
    Returns:
        重複除去後の問題リスト
    """
    unique_issues = []
    seen_signatures = set()
    
    for issue in issues:
        # 問題のシグネチャを生成
        signature = _generate_issue_signature(issue)
        
        if signature not in seen_signatures:
            unique_issues.append(issue)
            seen_signatures.add(signature)
        else:
            logger.debug(f"Duplicate issue filtered: {issue}")
    
    return unique_issues

def _generate_issue_signature(issue: 'Issue') -> str:
    """
    問題のユニークなシグネチャを生成
    
    Returns:
        ハッシュ文字列
    """
    import hashlib
    
    components = [
        issue.file_path,
        str(issue.line_number),
        issue.issue_type,
        issue.cql_text[:100]  # CQL最初の100文字
    ]
    
    signature_str = '|'.join(components)
    return hashlib.md5(signature_str.encode()).hexdigest()
```

---

## 5. エラーハンドリング設計

### 5.1 エラーハンドリング戦略

```python
"""
包括的なエラーハンドリング
"""

from typing import Optional, Any
from dataclasses import dataclass
import traceback

@dataclass
class AnalysisError:
    """分析エラーの詳細"""
    file_path: str
    error_type: str
    error_message: str
    stack_trace: str
    recoverable: bool
    
class ErrorHandler:
    """エラーハンドリングユーティリティ"""
    
    def __init__(self):
        self.errors: List[AnalysisError] = []
    
    def handle_parse_error(
        self,
        file_path: Path,
        exception: Exception
    ) -> Optional[List['Issue']]:
        """
        パースエラーのハンドリング
        
        戦略:
        1. javalang.JavaSyntaxError → ファイルスキップ
        2. UnicodeDecodeError → エンコーディング再試行
        3. その他 → ログして継続
        
        Returns:
            回復可能な場合は再試行結果、不可能な場合None
        """
        if isinstance(exception, javalang.parser.JavaSyntaxError):
            # 構文エラー - スキップ
            logger.warning(f"Syntax error in {file_path}, skipping: {exception}")
            self._record_error(file_path, exception, recoverable=False)
            return None
        
        elif isinstance(exception, UnicodeDecodeError):
            # エンコーディングエラー - 別のエンコーディングで再試行
            logger.info(f"Retrying {file_path} with different encoding")
            try:
                return self._retry_with_latin1(file_path)
            except Exception as e:
                self._record_error(file_path, e, recoverable=False)
                return None
        
        else:
            # 予期しないエラー
            logger.error(f"Unexpected error in {file_path}: {exception}")
            self._record_error(file_path, exception, recoverable=False)
            return None
    
    def handle_detection_error(
        self,
        issue_type: str,
        call: 'CassandraCall',
        exception: Exception
    ) -> None:
        """
        検出器のエラーハンドリング
        
        検出器のエラーは全体の処理を止めない
        """
        logger.error(
            f"Detector '{issue_type}' failed on {call.file_path}:{call.line_number}: "
            f"{exception}"
        )
        self._record_error(call.file_path, exception, recoverable=True)
    
    def _record_error(
        self,
        file_path: Path,
        exception: Exception,
        recoverable: bool
    ):
        """エラーを記録"""
        error = AnalysisError(
            file_path=str(file_path),
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            recoverable=recoverable
        )
        self.errors.append(error)
    
    def _retry_with_latin1(self, file_path: Path) -> List['Issue']:
        """Latin-1エンコーディングで再試行"""
        # 実装省略
        pass
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        return {
            'total_errors': len(self.errors),
            'recoverable': sum(1 for e in self.errors if e.recoverable),
            'unrecoverable': sum(1 for e in self.errors if not e.recoverable),
            'by_type': self._group_errors_by_type()
        }
    
    def _group_errors_by_type(self) -> Dict[str, int]:
        """エラーをタイプ別に集計"""
        from collections import Counter
        return dict(Counter(e.error_type for e in self.errors))
```

### 5.2 タイムアウト管理

```python
"""
処理のタイムアウト管理
"""

import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """
    処理にタイムアウトを設定
    
    使用例:
        with timeout(30):
            result = long_running_function()
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # タイムアウトハンドラーを設定
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # タイムアウトを解除
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# 使用例
def analyze_with_timeout(file_path: Path, timeout_seconds: int = 30) -> List['Issue']:
    """タイムアウト付きで分析"""
    try:
        with timeout(timeout_seconds):
            return analyze_file(file_path)
    except TimeoutError as e:
        logger.warning(f"Analysis of {file_path} timed out after {timeout_seconds}s")
        return []
```

---

## 6. パフォーマンス設計

### 6.1 パフォーマンス目標

| 指標 | 目標値 | 測定方法 |
|-----|--------|---------|
| 単一ファイル解析 | < 100ms | 平均実行時間 |
| 10ファイル並列解析 | < 1秒 | 総実行時間 |
| メモリ使用量 | < 500MB | 20ファイル解析時 |
| キャッシュヒット率 | > 80% | 再解析時 |

### 6.2 最適化手法

```python
"""
パフォーマンス最適化
"""

# 1. 遅延評価
class LazyParser:
    """必要になるまでパースを遅延"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._content: Optional[str] = None
        self._ast: Optional[Any] = None
    
    @property
    def content(self) -> str:
        """遅延読み込み"""
        if self._content is None:
            with open(self.file_path) as f:
                self._content = f.read()
        return self._content
    
    @property
    def ast(self) -> Any:
        """遅延パース"""
        if self._ast is None:
            self._ast = javalang.parse.parse(self.content)
        return self._ast

# 2. バッチ処理
def analyze_in_batches(
    files: List[Path],
    batch_size: int = 10
) -> List['Issue']:
    """ファイルをバッチ単位で処理してメモリ効率化"""
    all_issues = []
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        batch_issues = analyze_batch(batch)
        all_issues.extend(batch_issues)
        
        # バッチ間でメモリをクリア
        gc.collect()
    
    return all_issues

# 3. インクリメンタル解析
class IncrementalAnalyzer:
    """
    変更されたファイルのみを再解析
    
    前回の分析結果とファイルハッシュを保存し、
    変更がないファイルはスキップ
    """
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.previous_state = self._load_state()
    
    def analyze_incremental(self, files: List[Path]) -> List['Issue']:
        """増分解析"""
        files_to_analyze = []
        cached_issues = []
        
        for file in files:
            file_hash = compute_file_hash(file)
            
            if file_hash in self.previous_state:
                # キャッシュヒット
                cached_issues.extend(self.previous_state[file_hash]['issues'])
            else:
                # 新規または変更あり
                files_to_analyze.append(file)
        
        # 変更されたファイルのみ解析
        new_issues = analyze_files(files_to_analyze)
        
        return cached_issues + new_issues
    
    def _load_state(self) -> Dict:
        """前回の状態を読み込み"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {}
```

---

## 7. テスト設計

### 7.1 テストピラミッド

```
         ┌──────────┐
         │   E2E    │  10% - 実際のプロジェクトで動作確認
         │  Tests   │
         └──────────┘
       ┌──────────────┐
       │ Integration  │  30% - コンポーネント間の連携
       │    Tests     │
       └──────────────┘
     ┌──────────────────┐
     │   Unit Tests     │  60% - 個別クラス・メソッド
     │                  │
     └──────────────────┘
```

### 7.2 テストケース設計

```python
"""
包括的なテストスイート
"""

import pytest
from pathlib import Path

# === ユニットテスト ===

class TestJavaParser:
    """JavaParserのユニットテスト"""
    
    @pytest.fixture
    def parser(self):
        return JavaCassandraParser()
    
    @pytest.fixture
    def sample_code(self):
        return """
        public class UserDAO {
            private Session session;
            
            public User findById(String id) {
                String cql = "SELECT * FROM users WHERE user_id = ?";
                PreparedStatement ps = session.prepare(cql);
                BoundStatement bound = ps.bind(id);
                ResultSet rs = session.execute(bound);
                return mapToUser(rs.one());
            }
        }
        """
    
    def test_parse_simple_select(self, parser, sample_code, tmp_path):
        """シンプルなSELECTのパース"""
        # テストファイル作成
        test_file = tmp_path / "UserDAO.java"
        test_file.write_text(sample_code)
        
        # パース実行
        calls = parser.parse_file(test_file)
        
        # アサーション
        assert len(calls) == 1
        assert calls[0].call_type == CallType.PREPARE
        assert "SELECT * FROM users" in calls[0].cql_text
        assert calls[0].is_prepared == True
    
    def test_parse_allow_filtering(self, parser, tmp_path):
        """ALLOW FILTERINGを含むコードのパース"""
        code = """
        public List<User> findByEmail(String email) {
            String cql = "SELECT * FROM users WHERE email = ? ALLOW FILTERING";
            return session.execute(cql, email).all();
        }
        """
        
        test_file = tmp_path / "BadDAO.java"
        test_file.write_text(code)
        
        calls = parser.parse_file(test_file)
        
        assert len(calls) == 1
        assert "ALLOW FILTERING" in calls[0].cql_text
    
    def test_parse_batch(self, parser, tmp_path):
        """BATCH処理のパース"""
        code = """
        public void updateMultiple(List<User> users) {
            BatchStatement batch = new BatchStatement();
            for (User user : users) {
                batch.add(session.prepare("UPDATE users SET name = ? WHERE id = ?")
                    .bind(user.getName(), user.getId()));
            }
            session.execute(batch);
        }
        """
        
        test_file = tmp_path / "BatchDAO.java"
        test_file.write_text(code)
        
        calls = parser.parse_file(test_file)
        
        assert len(calls) > 0
        # BATCHの検出を確認

class TestCQLParser:
    """CQLParserのユニットテスト"""
    
    @pytest.fixture
    def parser(self):
        # スキーマ情報付きで初期化
        schema_info = {
            'users': {
                'partition_keys': ['user_id'],
                'clustering_keys': ['created_at'],
                'columns': ['user_id', 'name', 'email', 'created_at']
            }
        }
        return CQLParser(schema_info=schema_info)
    
    def test_detect_allow_filtering(self, parser):
        """ALLOW FILTERING検出"""
        cql = "SELECT * FROM users WHERE email = 'test@example.com' ALLOW FILTERING"
        analysis = parser.analyze(cql)
        
        assert analysis.has_allow_filtering == True
        assert len(analysis.issues) > 0
        assert analysis.issues[0]['type'] == 'ALLOW_FILTERING'
    
    def test_detect_no_partition_key(self, parser):
        """Partition Key未使用検出"""
        cql = "SELECT * FROM users WHERE email = ?"
        analysis = parser.analyze(cql)
        
        assert analysis.where_clause is not None
        assert analysis.where_clause.has_partition_key_filter == False
        assert any(i['type'] == 'NO_PARTITION_KEY' for i in analysis.issues)
    
    def test_batch_size_detection(self, parser):
        """大量BATCHの検出"""
        # 150個のINSERTを含むBATCH
        statements = [
            f"INSERT INTO users (user_id, name) VALUES ('{i}', 'User{i}');"
            for i in range(150)
        ]
        cql = "BEGIN BATCH\n" + "\n".join(statements) + "\nAPPLY BATCH;"
        
        analysis = parser.analyze(cql)
        
        assert analysis.is_batch == True
        assert analysis.batch_size == 150
        assert any(i['type'] == 'LARGE_BATCH' for i in analysis.issues)

# === 統合テスト ===

class TestAnalysisPipeline:
    """分析パイプライン全体のテスト"""
    
    @pytest.fixture
    def pipeline(self):
        config = {
            'detection': {
                'allow_filtering': {'enabled': True, 'severity': 'high'},
                'partition_key': {'enabled': True, 'severity': 'critical'},
                'batch_size': {'enabled': True, 'threshold': 100, 'severity': 'medium'},
                'prepared_statement': {'enabled': True, 'min_executions': 5, 'severity': 'low'}
            }
        }
        return AnalysisPipeline(config)
    
    def test_analyze_file_with_issues(self, pipeline, tmp_path):
        """問題を含むファイルの分析"""
        code = """
        public class ProblematicDAO {
            private Session session;
            
            public List<User> findAll() {
                // 問題1: WHERE句なし
                String cql = "SELECT * FROM users";
                return session.execute(cql).all();
            }
            
            public User findByEmail(String email) {
                // 問題2: ALLOW FILTERING
                String cql = "SELECT * FROM users WHERE email = ? ALLOW FILTERING";
                return session.execute(cql, email).one();
            }
        }
        """
        
        test_file = tmp_path / "ProblematicDAO.java"
        test_file.write_text(code)
        
        issues = pipeline.analyze_file(test_file)
        
        # 2つ以上の問題が検出されるべき
        assert len(issues) >= 2
        
        # ALLOW FILTERINGが検出されているべき
        assert any(i.issue_type == 'ALLOW_FILTERING' for i in issues)

# === E2Eテスト ===

class TestEndToEnd:
    """エンドツーエンドテスト"""
    
    def test_full_analysis_workflow(self, tmp_path):
        """完全な分析ワークフロー"""
        # テストプロジェクト構造を作成
        project_dir = tmp_path / "test_project"
        dao_dir = project_dir / "src" / "main" / "java" / "com" / "example" / "dao"
        dao_dir.mkdir(parents=True)
        
        # 複数のDAOファイルを作成
        (dao_dir / "UserDAO.java").write_text("""
        public class UserDAO {
            public User findById(String id) {
                String cql = "SELECT * FROM users WHERE user_id = ?";
                PreparedStatement ps = session.prepare(cql);
                return session.execute(ps.bind(id)).one();
            }
        }
        """)
        
        (dao_dir / "OrderDAO.java").write_text("""
        public class OrderDAO {
            public List<Order> findByStatus(String status) {
                // ALLOW FILTERING問題
                String cql = "SELECT * FROM orders WHERE status = ? ALLOW FILTERING";
                return session.execute(cql, status).all();
            }
        }
        """)
        
        # 分析実行
        orchestrator = AnalysisOrchestrator(config={})
        result = orchestrator.analyze(project_dir)
        
        # アサーション
        assert len(result.analyzed_files) == 2
        assert result.total_issues > 0
        assert 'high' in result.issues_by_severity
```

### 7.3 テストデータ

```python
"""
テスト用のフィクスチャデータ
"""

# tests/fixtures/sample_good.java
GOOD_DAO_CODE = """
public class GoodUserDAO {
    private Session session;
    
    public User findById(String userId) {
        // 良い例: Prepared Statement + Partition Key使用
        String cql = "SELECT user_id, name, email FROM users WHERE user_id = ?";
        PreparedStatement ps = session.prepare(cql);
        BoundStatement bound = ps.bind(userId);
        bound.setConsistencyLevel(ConsistencyLevel.LOCAL_QUORUM);
        ResultSet rs = session.execute(bound);
        return mapToUser(rs.one());
    }
    
    public List<Order> findUserOrders(String userId, Date from, Date to) {
        // 良い例: Partition Key + Clustering Key範囲クエリ
        String cql = "SELECT * FROM orders WHERE user_id = ? AND created_at >= ? AND created_at < ?";
        PreparedStatement ps = session.prepare(cql);
        return session.execute(ps.bind(userId, from, to)).all();
    }
}
"""

# tests/fixtures/sample_bad1.java - ALLOW FILTERING
BAD_DAO_ALLOW_FILTERING = """
public class BadUserDAO {
    public List<User> findByEmail(String email) {
        // 悪い例: ALLOW FILTERING使用
        String cql = "SELECT * FROM users WHERE email = ? ALLOW FILTERING";
        return session.execute(cql, email).all();
    }
}
"""

# tests/fixtures/sample_bad2.java - Partition Key未使用
BAD_DAO_NO_PARTITION_KEY = """
public class BadOrderDAO {
    public List<Order> findByStatus(String status) {
        // 悪い例: Partition Key未使用
        String cql = "SELECT * FROM orders WHERE status = ?";
        return session.execute(cql, status).all();
    }
}
"""

# tests/fixtures/sample_bad3.java - 大量BATCH
BAD_DAO_LARGE_BATCH = """
public class BadBatchDAO {
    public void insertMany(List<User> users) {
        // 悪い例: 大量のBATCH処理
        BatchStatement batch = new BatchStatement();
        for (User user : users) {  // usersが200件と仮定
            batch.add(session.prepare("INSERT INTO users (user_id, name) VALUES (?, ?)")
                .bind(user.getId(), user.getName()));
        }
        session.execute(batch);
    }
}
"""
```

---

## 8. ログ・モニタリング設計

### 8.1 ログ設計

```python
"""
構造化ログの実装
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

class StructuredLogger:
    """
    構造化ログ出力
    
    ログフォーマット: JSON Lines
    {
        "timestamp": "2025-10-26T10:30:00Z",
        "level": "INFO",
        "component": "JavaParser",
        "event": "file_parsed",
        "file_path": "/path/to/UserDAO.java",
        "duration_ms": 45,
        "calls_found": 3
    }
    """
    
    def __init__(self, component: str):
        self.component = component
        self.logger = logging.getLogger(component)
    
    def log(self, level: str, event: str, **kwargs):
        """構造化ログを出力"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'component': self.component,
            'event': event,
            **kwargs
        }
        
        log_line = json.dumps(log_entry)
        
        if level == 'ERROR':
            self.logger.error(log_line)
        elif level == 'WARNING':
            self.logger.warning(log_line)
        elif level == 'INFO':
            self.logger.info(log_line)
        else:
            self.logger.debug(log_line)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """パフォーマンスログ"""
        self.log(
            'INFO',
            'performance',
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_error(self, error: Exception, **kwargs):
        """エラーログ"""
        import traceback
        self.log(
            'ERROR',
            'error_occurred',
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            **kwargs
        )

# 使用例
logger = StructuredLogger('JavaParser')

# ファイル解析の開始
logger.log('INFO', 'parse_start', file_path='/path/to/UserDAO.java')

# パフォーマンス測定
start = time.time()
# ... 処理 ...
duration = (time.time() - start) * 1000
logger.log_performance('file_parse', duration, file_path='/path/to/UserDAO.java')

# エラー
try:
    # ... 処理 ...
    pass
except Exception as e:
    logger.log_error(e, file_path='/path/to/UserDAO.java')
```

### 8.2 メトリクス収集

```python
"""
メトリクスの収集と出力
"""

from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class AnalysisMetrics:
    """分析のメトリクス"""
    
    # ファイル数
    total_files: int = 0
    processed_files: int = 0
    error_files: int = 0
    skipped_files: int = 0
    
    # 問題数
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    # パフォーマンス
    total_duration_seconds: float = 0.0
    average_file_duration_ms: float = 0.0
    
    # キャッシュ
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'files': {
                'total': self.total_files,
                'processed': self.processed_files,
                'errors': self.error_files,
                'skipped': self.skipped_files
            },
            'issues': {
                'total': self.total_issues,
                'by_severity': {
                    'critical': self.critical_issues,
                    'high': self.high_issues,
                    'medium': self.medium_issues,
                    'low': self.low_issues
                }
            },
            'performance': {
                'total_duration_seconds': self.total_duration_seconds,
                'average_file_duration_ms': self.average_file_duration_ms
            },
            'cache': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0 else 0.0
            }
        }
    
    def print_summary(self):
        """サマリーを出力"""
        print("\n" + "="*60)
        print("Analysis Summary")
        print("="*60)
        print(f"Files Analyzed: {self.processed_files}/{self.total_files}")
        print(f"Total Issues: {self.total_issues}")
        print(f"  Critical: {self.critical_issues}")
        print(f"  High: {self.high_issues}")
        print(f"  Medium: {self.medium_issues}")
        print(f"  Low: {self.low_issues}")
        print(f"\nPerformance:")
        print(f"  Total Time: {self.total_duration_seconds:.2f}s")
        print(f"  Avg per File: {self.average_file_duration_ms:.1f}ms")
        print(f"\nCache:")
        hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100 \
            if (self.cache_hits + self.cache_misses) > 0 else 0.0
        print(f"  Hit Rate: {hit_rate:.1f}%")
        print("="*60)
```

---

## 次のステップ

この詳細設計書に基づいて、TODO管理ドキュメントで具体的な実装タスクを定義します。

**実装の開始準備**:
1. 開発環境のセットアップ
2. ディレクトリ構造の作成
3. 依存パッケージのインストール
4. テストフィクスチャの準備

各クラスの実装は、Claude Code CLIで段階的に進めることが可能です。
