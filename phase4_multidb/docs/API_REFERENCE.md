# API リファレンス

**バージョン**: v1.0.0
**最終更新**: 2025年01月27日

## 目次

1. [パーサー API](#パーサー-api)
2. [検出器 API](#検出器-api)
3. [LLM統合 API](#llm統合-api)
4. [レポーター API](#レポーター-api)
5. [コアモデル](#コアモデル)
6. [ユーティリティ](#ユーティリティ)

---

## パーサー API

### JavaElasticsearchParser

Javaコード内のElasticsearchクエリを抽出するパーサー。

#### クラス定義

```python
class JavaElasticsearchParser:
    """
    JavaコードからElasticsearchクエリを抽出

    Attributes:
        query_patterns (List[Dict[str, str]]): クエリパターン定義
        import_patterns (List[str]): インポートパターン
    """
```

#### メソッド

##### `parse_file(file_path: str, code: str) -> List[ElasticsearchQuery]`

Javaファイルを解析してクエリを抽出します。

**パラメータ**:
- `file_path` (str): ファイルパス
- `code` (str): Javaコード

**戻り値**:
- `List[ElasticsearchQuery]`: 抽出されたクエリのリスト

**例外**:
- `ParsingError`: 構文エラーが発生した場合

**使用例**:

```python
parser = JavaElasticsearchParser()
queries = parser.parse_file('SearchService.java', code_content)

for query in queries:
    print(f"Query: {query.query_type}")
    print(f"Line: {query.line_number}")
```

##### `extract_query_builders(tree: javalang.tree.CompilationUnit) -> List[Dict[str, Any]]`

ASTからQueryBuilderの呼び出しを抽出します。

**パラメータ**:
- `tree` (CompilationUnit): Java AST

**戻り値**:
- `List[Dict[str, Any]]`: クエリビルダー情報

**内部メソッド** (通常は直接呼び出さない):

```python
def _extract_method_invocation(
    node: javalang.tree.MethodInvocation,
    context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """メソッド呼び出しから情報抽出"""
```

---

## 検出器 API

すべての検出器は`BaseDetector`を継承します。

### BaseDetector

#### クラス定義

```python
class BaseDetector(ABC):
    """
    基底検出器クラス

    Attributes:
        name (str): 検出器名
        config (DetectorConfig): 設定
    """

    def __init__(self, config: Optional[DetectorConfig] = None):
        self.config = config or DetectorConfig()
```

#### 抽象メソッド

##### `detect(queries: List[Query], context: AnalysisContext) -> List[Issue]`

クエリを分析して問題を検出します。

**パラメータ**:
- `queries` (List[Query]): 分析対象のクエリ
- `context` (AnalysisContext): 分析コンテキスト

**戻り値**:
- `List[Issue]`: 検出された問題のリスト

---

### WildcardDetector

先頭ワイルドカードを検出します。

#### 使用例

```python
from multidb_analyzer.elasticsearch.detectors import WildcardDetector
from multidb_analyzer.core.base_detector import AnalysisContext

detector = WildcardDetector()
context = AnalysisContext(
    file_path='SearchService.java',
    code_content=code
)

issues = detector.detect(queries, context)
```

#### 検出ロジック

```python
def detect(self, queries: List[ElasticsearchQuery], context: AnalysisContext) -> List[Issue]:
    """
    先頭ワイルドカードパターンを検出

    検出パターン:
    - wildcardQuery("field", "*value")
    - wildcardQuery("field", "?value")
    """
```

---

### NPlusOneDetector

ループ内のクエリ実行を検出します。

#### 設定

```python
config = DetectorConfig(
    custom_params={
        'loop_threshold': 5  # ループ回数の閾値
    }
)

detector = NPlusOneDetector(config=config)
```

#### 検出ロジック

```python
def detect(self, queries: List[ElasticsearchQuery], context: AnalysisContext) -> List[Issue]:
    """
    ループ内のクエリ実行を検出

    検出条件:
    1. for/while/do-whileループ内
    2. ループ回数 > threshold
    3. バッチクエリが使用されていない
    """
```

---

### LargeSizeDetector

過大なサイズ指定を検出します。

#### 設定

```python
config = DetectorConfig(
    custom_params={
        'size_threshold': 1000  # サイズ閾値
    }
)

detector = LargeSizeDetector(config=config)
```

#### 検出ロジック

```python
def detect(self, queries: List[ElasticsearchQuery], context: AnalysisContext) -> List[Issue]:
    """
    大きすぎるsizeパラメータを検出

    検出条件:
    - searchSourceBuilder.size(n) where n > threshold
    """
```

---

## LLM統合 API

### ClaudeClient

Claude APIクライアント。

#### クラス定義

```python
class ClaudeClient:
    """
    Claude API統合クライアント

    Attributes:
        api_key (str): Anthropic APIキー
        model (ClaudeModel): 使用するモデル
        max_retries (int): 最大リトライ回数
        timeout (int): タイムアウト（秒）
        usage (APIUsage): 使用統計
    """
```

#### 初期化

```python
from multidb_analyzer.llm import ClaudeClient, ClaudeModel

# APIキー指定
client = ClaudeClient(
    api_key="sk-ant-xxxxx",
    model=ClaudeModel.SONNET,
    max_retries=3,
    timeout=60
)

# 環境変数から取得
# ANTHROPIC_API_KEY環境変数を設定
client = ClaudeClient()
```

#### メソッド

##### `generate(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str`

テキストを生成します。

**パラメータ**:
- `prompt` (str): ユーザープロンプト
- `system_prompt` (Optional[str]): システムプロンプト
- `max_tokens` (int): 最大トークン数（デフォルト: 4096）
- `temperature` (float): 生成温度（デフォルト: 0.7）
- `model` (Optional[ClaudeModel]): モデル上書き

**戻り値**:
- `str`: 生成されたテキスト

**例外**:
- `APIError`: API呼び出しが失敗した場合

**使用例**:

```python
response = client.generate(
    prompt="Optimize this query: ...",
    system_prompt="You are a database expert.",
    max_tokens=2048,
    temperature=0.3
)
```

##### `generate_batch(prompts: List[str], delay_between_requests: float = 1.0, **kwargs) -> List[str]`

複数のプロンプトをバッチ処理します。

**パラメータ**:
- `prompts` (List[str]): プロンプトのリスト
- `delay_between_requests` (float): リクエスト間の遅延（秒）
- `**kwargs`: generate()に渡される追加パラメータ

**戻り値**:
- `List[str]`: 生成されたテキストのリスト

**使用例**:

```python
prompts = [
    "Analyze query 1: ...",
    "Analyze query 2: ...",
    "Analyze query 3: ..."
]

responses = client.generate_batch(
    prompts,
    delay_between_requests=1.5,
    temperature=0.3
)
```

##### `get_usage_stats() -> Dict[str, Any]`

API使用統計を取得します。

**戻り値**:
```python
{
    'total_requests': int,
    'total_tokens': int,
    'input_tokens': int,
    'output_tokens': int,
    'total_cost_usd': float,
    'average_cost_per_request': float,
    'request_history': List[Dict[str, Any]]
}
```

**使用例**:

```python
stats = client.get_usage_stats()
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
print(f"Requests: {stats['total_requests']}")
```

##### `reset_usage_stats() -> None`

使用統計をリセットします。

```python
client.reset_usage_stats()
```

---

### LLMOptimizer

LLMを使用したコード最適化エンジン。

#### クラス定義

```python
class LLMOptimizer:
    """
    LLM最適化エンジン

    Attributes:
        client (ClaudeClient): Claude APIクライアント
        temperature (float): 生成温度
        max_tokens (int): 最大トークン数
    """
```

#### 初期化

```python
from multidb_analyzer.llm import LLMOptimizer, ClaudeModel

optimizer = LLMOptimizer(
    api_key="sk-ant-xxxxx",
    model=ClaudeModel.SONNET,
    temperature=0.3,
    max_tokens=4096
)
```

#### メソッド

##### `optimize_issue(issue: Issue, code: str, language: str = "java", db_type: str = "elasticsearch") -> OptimizationResult`

単一の問題を最適化します。

**パラメータ**:
- `issue` (Issue): 検出された問題
- `code` (str): 元のコード
- `language` (str): プログラミング言語
- `db_type` (str): データベースタイプ

**戻り値**:
- `OptimizationResult`: 最適化結果

**使用例**:

```python
result = optimizer.optimize_issue(
    issue=detected_issue,
    code='wildcardQuery("name", "*smith")',
    language="java",
    db_type="elasticsearch"
)

print(f"Root cause: {result.root_cause}")
print(f"Performance impact: {result.performance_impact}")
print(f"Optimized code:\n{result.optimized_code}")
print(f"Confidence: {result.confidence_score}")
```

##### `optimize_batch(issues: List[Issue], code_snippets: Dict[str, str], **kwargs) -> List[OptimizationResult]`

複数の問題をバッチ最適化します。

**パラメータ**:
- `issues` (List[Issue]): 問題のリスト
- `code_snippets` (Dict[str, str]): ファイル:行番号 → コードのマッピング
- `language` (str): プログラミング言語
- `db_type` (str): データベースタイプ

**戻り値**:
- `List[OptimizationResult]`: 最適化結果のリスト

**使用例**:

```python
code_snippets = {
    "SearchService.java:10": 'wildcardQuery("name", "*smith")',
    "SearchService.java:25": 'searchSourceBuilder.size(10000)'
}

results = optimizer.optimize_batch(
    issues=detected_issues,
    code_snippets=code_snippets,
    language="java"
)
```

##### `prioritize_issues(issues: List[Issue]) -> Dict[str, Any]`

問題の優先順位を決定します。

**パラメータ**:
- `issues` (List[Issue]): 問題のリスト

**戻り値**:
```python
{
    'prioritized_issues': [
        {
            'issue_id': int,
            'priority_score': float,
            'recommended_order': int
        }
    ],
    'quick_wins': List[str],
    'high_risk_high_reward': List[str],
    'technical_debt': List[str]
}
```

**使用例**:

```python
prioritization = optimizer.prioritize_issues(all_issues)

for item in prioritization['prioritized_issues']:
    issue = all_issues[item['issue_id']]
    print(f"{item['recommended_order']}. {issue.title}")
    print(f"   Priority score: {item['priority_score']}")
```

##### `generate_auto_fix(issue: Issue, code: str, **kwargs) -> Dict[str, Any]`

自動修正コードを生成します。

**パラメータ**:
- `issue` (Issue): 問題
- `code` (str): 元のコード
- `db_type` (str): データベースタイプ
- `framework` (str): フレームワーク
- `language` (str): プログラミング言語

**戻り値**:
```python
{
    'fixed_code': str,
    'confidence': float,
    'breaking_changes': bool,
    'migration_notes': str
}
```

**使用例**:

```python
fix = optimizer.generate_auto_fix(
    issue=wildcard_issue,
    code='wildcardQuery("name", "*smith")',
    db_type="elasticsearch",
    framework="Spring Data"
)

if fix['confidence'] > 0.8:
    print(f"Fixed code:\n{fix['fixed_code']}")
    if fix['breaking_changes']:
        print(f"Warning: {fix['migration_notes']}")
```

---

### PromptTemplates

プロンプトテンプレート集。

#### 定数

```python
SYSTEM_PROMPT: str  # システムプロンプト
ELASTICSEARCH_OPTIMIZATION: str  # Elasticsearch最適化テンプレート
PRIORITIZE_ISSUES: str  # 問題優先順位付けテンプレート
CODE_REVIEW: str  # コードレビューテンプレート
AUTO_FIX_GENERATION: str  # 自動修正生成テンプレート
```

#### クラスメソッド

##### `format_elasticsearch_optimization(issue: Issue, code: str, language: str) -> str`

Elasticsearch最適化プロンプトをフォーマットします。

```python
from multidb_analyzer.llm import PromptTemplates

prompt = PromptTemplates.format_elasticsearch_optimization(
    issue=detected_issue,
    code=original_code,
    language="java"
)
```

##### `format_prioritize_issues(issues: List[Issue]) -> str`

優先順位付けプロンプトをフォーマットします。

```python
prompt = PromptTemplates.format_prioritize_issues(all_issues)
```

---

## レポーター API

### HTMLReporter

HTML形式のレポートを生成します。

#### クラス定義

```python
class HTMLReporter:
    """
    HTMLレポート生成器

    Attributes:
        config (ReportConfig): レポート設定
    """
```

#### 使用例

```python
from multidb_analyzer.reporters import HTMLReporter, ReportConfig

config = ReportConfig(
    title="Elasticsearch Analysis Report",
    include_statistics=True,
    include_code_snippets=True,
    max_snippet_lines=15
)

reporter = HTMLReporter(config=config)
reporter.generate(issues, output_path='report.html')
```

---

## コアモデル

### Issue

検出された問題を表すモデル。

#### 定義

```python
@dataclass
class Issue:
    detector_name: str
    severity: Severity
    category: IssueCategory
    title: str
    description: str
    file_path: str
    line_number: int
    query_text: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### 使用例

```python
issue = Issue(
    detector_name="WildcardDetector",
    severity=Severity.CRITICAL,
    category=IssueCategory.PERFORMANCE,
    title="Leading Wildcard Query",
    description="Query uses leading wildcard which causes full index scan",
    file_path="SearchService.java",
    line_number=42,
    query_text='wildcardQuery("name", "*smith")',
    suggestion="Use prefixQuery() or matchQuery() instead"
)
```

### Severity

重大度の列挙型。

```python
class Severity(Enum):
    CRITICAL = "CRITICAL"  # 即座に対応が必要
    HIGH = "HIGH"          # 優先度高
    MEDIUM = "MEDIUM"      # 中程度
    LOW = "LOW"            # 低優先度
    INFO = "INFO"          # 情報提供
```

### IssueCategory

問題カテゴリの列挙型。

```python
class IssueCategory(Enum):
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    RELIABILITY = "RELIABILITY"
    BEST_PRACTICE = "BEST_PRACTICE"
```

### AnalysisContext

分析コンテキスト。

```python
@dataclass
class AnalysisContext:
    file_path: str
    code_content: str
    language: str = "java"
    db_type: str = "elasticsearch"
    metadata: Optional[Dict[str, Any]] = None
```

---

## ユーティリティ

### FileUtils

ファイル操作ユーティリティ。

#### メソッド

```python
from multidb_analyzer.utils import FileUtils

# Javaファイルを検索
java_files = FileUtils.find_files(
    directory='/path/to/project',
    extension='.java',
    exclude_patterns=['**/test/**', '**/generated/**']
)

# コード行数をカウント
loc = FileUtils.count_lines_of_code(file_path)

# ファイルエンコーディング検出
encoding = FileUtils.detect_encoding(file_path)
```

### CodeSnippetExtractor

コードスニペット抽出ユーティリティ。

```python
from multidb_analyzer.utils import CodeSnippetExtractor

extractor = CodeSnippetExtractor()

# 行番号周辺のコードを抽出
snippet = extractor.extract(
    file_path='SearchService.java',
    line_number=42,
    context_lines=5  # 前後5行
)
```

---

## エラーハンドリング

### 例外クラス

```python
from multidb_analyzer.exceptions import (
    ParsingError,
    DetectionError,
    LLMError,
    ConfigurationError
)

try:
    queries = parser.parse_file(file_path, code)
except ParsingError as e:
    logger.error(f"Failed to parse {file_path}: {e}")
    # エラー処理

try:
    response = client.generate(prompt)
except LLMError as e:
    logger.error(f"LLM API failed: {e}")
    # フォールバック処理
```

---

## ベストプラクティス

### 1. リソース管理

```python
# コンテキストマネージャーを使用
with ClaudeClient(api_key=api_key) as client:
    response = client.generate(prompt)
# 自動的にクリーンアップ
```

### 2. エラーハンドリング

```python
try:
    result = optimizer.optimize_issue(issue, code)
except LLMError:
    # フォールバック
    result = create_fallback_result(issue, code)
```

### 3. バッチ処理

```python
# 大量の問題を処理する場合
BATCH_SIZE = 10
for i in range(0, len(issues), BATCH_SIZE):
    batch = issues[i:i+BATCH_SIZE]
    results = optimizer.optimize_batch(batch, code_snippets)
    process_results(results)
```

---

## バージョン互換性

| API | v1.0.0 | 備考 |
|-----|--------|------|
| ClaudeClient | ✅ | 安定版 |
| LLMOptimizer | ✅ | 安定版 |
| BaseDetector | ✅ | 安定版 |
| HTMLReporter | ✅ | 安定版 |

---

**次のステップ**: [EXAMPLES.md](./EXAMPLES.md)で実用的なサンプルコードを確認してください。
