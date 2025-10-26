# Claude Code CLI 実装仕様書
## マルチフェーズ静的コード分析システム

*バージョン: v2.1.0*
*最終更新: 2025年01月27日 16:30 JST*

**対象**: 全フェーズ統合システム

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [技術スタック](#技術スタック)
3. [ディレクトリ構造](#ディレクトリ構造)
4. [セットアップ手順](#セットアップ手順)
5. [実装詳細](#実装詳細)
6. [テスト戦略](#テスト戦略)
7. [デプロイ手順](#デプロイ手順)

---

## プロジェクト概要

### 目的
Cassandra関連のJavaコードを静的解析し、以下の問題を検出する:
- ALLOW FILTERINGの使用
- Partition Key未使用のクエリ
- 大量バッチ処理
- Prepared Statement未使用

### スコープ (Phase 1)
- **対象ファイル数**: 10-20個のCassandra DAOクラス
- **検出機能**: 上記4つの問題パターン
- **出力形式**: HTMLレポート
- **LLM統合**: なし (Phase 2以降)

### 成功基準
- 3-5個の実際のバグを検出
- 誤検出率 < 20%
- 実行時間 < 30秒

---

## 技術スタック

### 言語・フレームワーク
```yaml
言語: Python 3.11+
パーサー: javalang (Javaコード解析)
データベース: SQLite (開発用) → Neo4j (本番)
レポート: Jinja2 (HTMLテンプレート)
テスト: pytest
型チェック: mypy
リンター: ruff
```

### 依存パッケージ
```txt
# requirements.txt
javalang==0.13.0
jinja2==3.1.2
pyyaml==6.0.1
click==8.1.7
rich==13.7.0
pytest==7.4.3
mypy==1.7.1
ruff==0.1.7
```

---

## ディレクトリ構造

```
C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\
├── phase1_cassandra/
│   ├── README_CASSANDRA.md
│   ├── requirements.txt
│   ├── setup.py
│   ├── pyproject.toml
│   │
│   ├── src/
│   │   └── cassandra_analyzer/
│       ├── __init__.py
│       ├── main.py                    # CLIエントリーポイント
│       │
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── java_parser.py         # Javaファイル解析
│       │   └── cql_parser.py          # CQL文字列解析
│       │
│       ├── detectors/
│       │   ├── __init__.py
│       │   ├── base.py                # 検出器の基底クラス
│       │   ├── allow_filtering.py     # ALLOW FILTERING検出
│       │   ├── partition_key.py       # Partition Key検証
│       │   ├── batch_size.py          # バッチサイズ検出
│       │   └── prepared_statement.py  # Prepared Statement検出
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── code_element.py        # コード要素の表現
│       │   ├── issue.py               # 検出された問題
│       │   └── analysis_result.py     # 分析結果
│       │
│       ├── reporters/
│       │   ├── __init__.py
│       │   ├── html_reporter.py       # HTMLレポート生成
│       │   ├── json_reporter.py       # JSON出力
│       │   └── console_reporter.py    # コンソール出力
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── file_scanner.py        # ファイル検索
│       │   └── config.py              # 設定管理
│       │
│       └── templates/
│           └── report.html            # HTMLテンプレート
│
├── tests/
│   ├── __init__.py
│   ├── test_parsers.py
│   ├── test_detectors.py
│   ├── test_reporters.py
│   │
│   └── fixtures/
│       ├── sample_dao_good.java       # 問題のないコード
│       ├── sample_dao_bad1.java       # ALLOW FILTERING
│       ├── sample_dao_bad2.java       # Partition Key未使用
│       └── sample_dao_bad3.java       # 大量バッチ
│
├── examples/
│   ├── analyze_single_file.py
│   └── analyze_directory.py
│
└── docs/
    ├── architecture.md
    ├── detector_guide.md
    └── extending.md
```

---

## セットアップ手順

### 1. プロジェクト初期化

```bash
# プロジェクトルートに移動
cd "C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude"

# Phase 1ディレクトリに移動
cd phase1_cassandra

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 開発用パッケージのインストール
pip install -e .
```

### 2. 設定ファイルの作成

```yaml
# config.yaml
analysis:
  target_directories:
    - "src/main/java/com/example/dao/cassandra"
  
  file_patterns:
    - "**/*DAO.java"
    - "**/*Repository.java"
  
  exclude_patterns:
    - "**/test/**"
    - "**/Test*.java"

detection:
  allow_filtering:
    enabled: true
    severity: "high"
  
  partition_key:
    enabled: true
    severity: "critical"
  
  batch_size:
    enabled: true
    threshold: 100
    severity: "medium"
  
  prepared_statement:
    enabled: true
    min_executions: 5
    severity: "low"

output:
  format: "html"  # html, json, console
  output_path: "reports/analysis_report.html"
  include_code_snippets: true
```

---

## 実装詳細

### Phase 1.1: Javaパーサーの実装

**ファイル**: `src/cassandra_analyzer/parsers/java_parser.py`

```python
"""
Javaファイルを解析し、Cassandra関連の呼び出しを抽出
"""
import javalang
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CassandraCall:
    """Cassandraの呼び出し情報"""
    method_name: str
    cql_text: str
    line_number: int
    is_prepared: bool
    consistency_level: Optional[str]
    file_path: str

class JavaCassandraParser:
    """
    JavaファイルからCassandra操作を抽出
    
    検出対象:
    - session.execute()
    - session.executeAsync()
    - session.prepare()
    """
    
    def parse_file(self, file_path: Path) -> List[CassandraCall]:
        """
        Javaファイルを解析してCassandra呼び出しを抽出
        
        Args:
            file_path: 解析対象のJavaファイルパス
            
        Returns:
            CassandraCallのリスト
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = javalang.parse.parse(content)
        except javalang.parser.JavaSyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return []
        
        calls = []
        
        # MethodInvocationノードを探索
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            if self._is_cassandra_call(node):
                call = self._extract_call_info(node, content, file_path)
                if call:
                    calls.append(call)
        
        return calls
    
    def _is_cassandra_call(self, node: javalang.tree.MethodInvocation) -> bool:
        """Cassandra関連の呼び出しか判定"""
        cassandra_methods = ['execute', 'executeAsync', 'prepare', 'batch']
        return node.member in cassandra_methods
    
    def _extract_call_info(
        self, 
        node: javalang.tree.MethodInvocation,
        content: str,
        file_path: Path
    ) -> Optional[CassandraCall]:
        """呼び出し情報を詳細に抽出"""
        # CQL文字列の抽出
        cql_text = self._extract_cql_from_node(node)
        if not cql_text:
            return None
        
        # 行番号の取得
        line_number = node.position.line if hasattr(node, 'position') else 0
        
        # Prepared Statement判定
        is_prepared = node.member == 'prepare' or self._check_prepared_usage(content, line_number)
        
        # Consistency Level抽出
        consistency_level = self._extract_consistency_level(content, line_number)
        
        return CassandraCall(
            method_name=node.member,
            cql_text=cql_text,
            line_number=line_number,
            is_prepared=is_prepared,
            consistency_level=consistency_level,
            file_path=str(file_path)
        )
    
    def _extract_cql_from_node(self, node: javalang.tree.MethodInvocation) -> Optional[str]:
        """メソッド引数からCQL文字列を抽出"""
        if not node.arguments:
            return None
        
        for arg in node.arguments:
            if isinstance(arg, javalang.tree.Literal):
                # 文字列リテラル
                return arg.value.strip('"\'')
            elif isinstance(arg, javalang.tree.MemberReference):
                # 定数参照 - 今は無視（後で解決機能を追加）
                return f"[CONSTANT: {arg.member}]"
        
        return None
    
    def _check_prepared_usage(self, content: str, line_number: int) -> bool:
        """Prepared Statementが使用されているか確認"""
        # 簡易実装: 前後5行以内にPreparedStatementの使用があるか
        lines = content.split('\n')
        start = max(0, line_number - 5)
        end = min(len(lines), line_number + 5)
        
        context = '\n'.join(lines[start:end])
        return 'PreparedStatement' in context or 'prepare(' in context
    
    def _extract_consistency_level(self, content: str, line_number: int) -> Optional[str]:
        """Consistency Levelの設定を抽出"""
        lines = content.split('\n')
        start = max(0, line_number - 3)
        end = min(len(lines), line_number + 3)
        
        context = '\n'.join(lines[start:end])
        
        # ConsistencyLevel.XXXのパターンを探す
        import re
        match = re.search(r'ConsistencyLevel\.(\w+)', context)
        if match:
            return match.group(1)
        
        return None
```

**実装タスク**:
```bash
# Claude Code CLIで実装
claude-code implement "Create JavaCassandraParser class in src/cassandra_analyzer/parsers/java_parser.py"

# 実装後のテスト
pytest tests/test_parsers.py::test_java_parser
```

---

### Phase 1.2: CQLパーサーの実装

**ファイル**: `src/cassandra_analyzer/parsers/cql_parser.py`

```python
"""
CQL文字列を解析して問題パターンを検出
"""
import re
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class CQLAnalysis:
    """CQL分析結果"""
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, BATCH
    has_allow_filtering: bool
    uses_partition_key: bool
    is_batch: bool
    batch_size: int
    tables: List[str]
    issues: List[Dict[str, Any]]

class CQLParser:
    """
    CQL文を解析して問題を検出
    """
    
    def analyze(self, cql: str) -> CQLAnalysis:
        """
        CQL文を分析
        
        Args:
            cql: 分析対象のCQL文
            
        Returns:
            CQLAnalysisオブジェクト
        """
        cql_upper = cql.upper()
        
        analysis = CQLAnalysis(
            query_type=self._get_query_type(cql_upper),
            has_allow_filtering='ALLOW FILTERING' in cql_upper,
            uses_partition_key=self._check_partition_key_usage(cql),
            is_batch='BEGIN BATCH' in cql_upper,
            batch_size=self._count_batch_statements(cql) if 'BEGIN BATCH' in cql_upper else 0,
            tables=self._extract_tables(cql),
            issues=[]
        )
        
        # 問題パターンの検出
        analysis.issues = self._detect_issues(analysis, cql)
        
        return analysis
    
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
    
    def _check_partition_key_usage(self, cql: str) -> bool:
        """
        WHERE句でPartition Keyを使用しているか推定
        
        注: 実際のテーブル定義との照合が必要だが、
        Phase 1では等価条件の存在で推定
        """
        where_match = re.search(r'WHERE\s+(.+?)(?:ALLOW|ORDER|LIMIT|$)', cql, re.IGNORECASE)
        if not where_match:
            return False
        
        where_clause = where_match.group(1)
        
        # 等価条件 (=) の存在をチェック
        has_equality = '=' in where_clause and 'IN' not in where_clause.upper()
        
        return has_equality
    
    def _extract_tables(self, cql: str) -> List[str]:
        """CQL文からテーブル名を抽出"""
        tables = []
        
        # FROM句
        from_match = re.findall(r'FROM\s+(\w+)', cql, re.IGNORECASE)
        tables.extend(from_match)
        
        # INTO句
        into_match = re.findall(r'INTO\s+(\w+)', cql, re.IGNORECASE)
        tables.extend(into_match)
        
        # UPDATE句
        update_match = re.findall(r'UPDATE\s+(\w+)', cql, re.IGNORECASE)
        tables.extend(update_match)
        
        return list(set(tables))
    
    def _count_batch_statements(self, cql: str) -> int:
        """BATCH内のステートメント数をカウント"""
        # セミコロンで分割
        statements = cql.split(';')
        # BEGIN BATCHとAPPLY BATCHを除外
        count = sum(1 for stmt in statements 
                   if stmt.strip() 
                   and 'BEGIN BATCH' not in stmt 
                   and 'APPLY BATCH' not in stmt)
        return count
    
    def _detect_issues(self, analysis: CQLAnalysis, cql: str) -> List[Dict[str, Any]]:
        """問題パターンを検出"""
        issues = []
        
        # ALLOW FILTERING
        if analysis.has_allow_filtering:
            issues.append({
                'type': 'ALLOW_FILTERING',
                'severity': 'high',
                'message': 'ALLOW FILTERING detected - full table scan risk',
                'recommendation': 'Create Materialized View or redesign data model'
            })
        
        # Partition Key未使用
        if analysis.query_type == 'SELECT' and not analysis.uses_partition_key:
            issues.append({
                'type': 'NO_PARTITION_KEY',
                'severity': 'critical',
                'message': 'Partition Key not used - multi-node scan',
                'recommendation': 'Add partition key to WHERE clause'
            })
        
        # 大量バッチ
        if analysis.is_batch and analysis.batch_size > 100:
            issues.append({
                'type': 'LARGE_BATCH',
                'severity': 'medium',
                'message': f'Large batch processing: {analysis.batch_size} statements',
                'recommendation': 'Split batch into chunks of 100 or less'
            })
        
        return issues
```

**実装タスク**:
```bash
# Claude Code CLIで実装
claude-code implement "Create CQLParser class in src/cassandra_analyzer/parsers/cql_parser.py"

# テスト
pytest tests/test_parsers.py::test_cql_parser
```

---

### Phase 1.3: 検出器の実装

**ファイル**: `src/cassandra_analyzer/detectors/base.py`

```python
"""
検出器の基底クラス
"""
from abc import ABC, abstractmethod
from typing import List
from ..models.issue import Issue
from ..parsers.java_parser import CassandraCall
from ..parsers.cql_parser import CQLAnalysis

class BaseDetector(ABC):
    """検出器の基底クラス"""
    
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.severity = config.get('severity', 'medium')
    
    @abstractmethod
    def detect(self, call: CassandraCall, cql_analysis: CQLAnalysis) -> List[Issue]:
        """
        問題を検出
        
        Args:
            call: Cassandra呼び出し情報
            cql_analysis: CQL分析結果
            
        Returns:
            検出された問題のリスト
        """
        pass
    
    @property
    @abstractmethod
    def detector_name(self) -> str:
        """検出器の名前"""
        pass
```

**ファイル**: `src/cassandra_analyzer/detectors/allow_filtering.py`

```python
"""
ALLOW FILTERING検出器
"""
from typing import List
from .base import BaseDetector
from ..models.issue import Issue
from ..parsers.java_parser import CassandraCall
from ..parsers.cql_parser import CQLAnalysis

class AllowFilteringDetector(BaseDetector):
    """ALLOW FILTERINGの使用を検出"""
    
    @property
    def detector_name(self) -> str:
        return "ALLOW_FILTERING_DETECTOR"
    
    def detect(self, call: CassandraCall, cql_analysis: CQLAnalysis) -> List[Issue]:
        """ALLOW FILTERINGを検出"""
        if not self.enabled:
            return []
        
        if not cql_analysis.has_allow_filtering:
            return []
        
        issue = Issue(
            detector_name=self.detector_name,
            issue_type='ALLOW_FILTERING',
            severity=self.severity,
            file_path=call.file_path,
            line_number=call.line_number,
            message='ALLOW FILTERING detected - full table scan risk',
            cql_text=call.cql_text,
            recommendation='Create Materialized View or redesign data model',
            evidence=[
                'ALLOW FILTERING causes Cassandra to scan all nodes',
                'Performance degrades with data growth',
                'Can cause cluster-wide performance issues'
            ]
        )
        
        return [issue]
```

**実装タスク**:
```bash
# 基底クラス
claude-code implement "Create BaseDetector in src/cassandra_analyzer/detectors/base.py"

# 各検出器
claude-code implement "Create AllowFilteringDetector in src/cassandra_analyzer/detectors/allow_filtering.py"
claude-code implement "Create PartitionKeyDetector in src/cassandra_analyzer/detectors/partition_key.py"
claude-code implement "Create BatchSizeDetector in src/cassandra_analyzer/detectors/batch_size.py"
claude-code implement "Create PreparedStatementDetector in src/cassandra_analyzer/detectors/prepared_statement.py"

# テスト
pytest tests/test_detectors.py
```

---

### Phase 1.4: データモデルの実装

**ファイル**: `src/cassandra_analyzer/models/issue.py`

```python
"""
検出された問題を表すモデル
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Issue:
    """検出された問題"""
    detector_name: str
    issue_type: str
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: int
    message: str
    cql_text: str
    recommendation: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0-1.0
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'detector': self.detector_name,
            'type': self.issue_type,
            'severity': self.severity,
            'file': self.file_path,
            'line': self.line_number,
            'message': self.message,
            'cql': self.cql_text,
            'recommendation': self.recommendation,
            'evidence': self.evidence,
            'confidence': self.confidence
        }
```

**ファイル**: `src/cassandra_analyzer/models/analysis_result.py`

```python
"""
分析結果全体を表すモデル
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from .issue import Issue

@dataclass
class AnalysisResult:
    """分析結果"""
    analyzed_files: List[str]
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[Issue] = field(default_factory=list)
    analysis_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'analyzed_files': self.analyzed_files,
            'total_issues': self.total_issues,
            'issues_by_severity': self.issues_by_severity,
            'issues': [issue.to_dict() for issue in self.issues],
            'analysis_time_seconds': self.analysis_time,
            'timestamp': self.timestamp
        }
```

**実装タスク**:
```bash
claude-code implement "Create Issue model in src/cassandra_analyzer/models/issue.py"
claude-code implement "Create AnalysisResult model in src/cassandra_analyzer/models/analysis_result.py"
```

---

### Phase 1.5: レポーター の実装

**ファイル**: `src/cassandra_analyzer/reporters/html_reporter.py`

```python
"""
HTML形式でレポートを生成
"""
from pathlib import Path
from typing import Any
from jinja2 import Template
from ..models.analysis_result import AnalysisResult

class HTMLReporter:
    """HTMLレポート生成"""
    
    def __init__(self, template_path: Path):
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = Template(f.read())
    
    def generate(self, result: AnalysisResult, output_path: Path) -> None:
        """
        HTMLレポートを生成
        
        Args:
            result: 分析結果
            output_path: 出力先パス
        """
        html_content = self.template.render(
            result=result,
            severity_colors={
                'critical': '#dc2626',
                'high': '#ea580c',
                'medium': '#f59e0b',
                'low': '#84cc16'
            }
        )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML report generated: {output_path}")
```

**ファイル**: `src/cassandra_analyzer/templates/report.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cassandra Analysis Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .issue {
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .issue.critical { border-left-color: #dc2626; }
        .issue.high { border-left-color: #ea580c; }
        .issue.medium { border-left-color: #f59e0b; }
        .issue.low { border-left-color: #84cc16; }
        .code {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }
        .recommendation {
            background: #e7f3ff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Cassandra Analysis Report</h1>
        <p>Generated: {{ result.timestamp }}</p>
        <p>Analysis Time: {{ "%.2f"|format(result.analysis_time) }}s</p>
    </div>

    <div class="summary">
        <div class="metric">
            <div>Analyzed Files</div>
            <div class="metric-value">{{ result.analyzed_files|length }}</div>
        </div>
        <div class="metric">
            <div>Total Issues</div>
            <div class="metric-value">{{ result.total_issues }}</div>
        </div>
        <div class="metric">
            <div>Critical</div>
            <div class="metric-value" style="color: #dc2626;">
                {{ result.issues_by_severity.get('critical', 0) }}
            </div>
        </div>
        <div class="metric">
            <div>High</div>
            <div class="metric-value" style="color: #ea580c;">
                {{ result.issues_by_severity.get('high', 0) }}
            </div>
        </div>
    </div>

    <h2>Detected Issues</h2>
    {% for issue in result.issues %}
    <div class="issue {{ issue.severity }}">
        <h3>{{ issue.issue_type }}</h3>
        <p><strong>Severity:</strong> {{ issue.severity.upper() }}</p>
        <p><strong>File:</strong> {{ issue.file_path }}:{{ issue.line_number }}</p>
        <p>{{ issue.message }}</p>
        
        <div class="code">
            <strong>CQL:</strong><br>
            {{ issue.cql_text }}
        </div>
        
        <div class="recommendation">
            <strong>💡 Recommendation:</strong><br>
            {{ issue.recommendation }}
        </div>
        
        {% if issue.evidence %}
        <details>
            <summary>Evidence</summary>
            <ul>
            {% for evidence in issue.evidence %}
                <li>{{ evidence }}</li>
            {% endfor %}
            </ul>
        </details>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
```

**実装タスク**:
```bash
claude-code implement "Create HTMLReporter in src/cassandra_analyzer/reporters/html_reporter.py"
claude-code create "Create HTML template in src/cassandra_analyzer/templates/report.html"
```

---

### Phase 1.6: CLIエントリーポイント

**ファイル**: `src/cassandra_analyzer/main.py`

```python
"""
CLIエントリーポイント
"""
import click
from pathlib import Path
from rich.console import Console
from rich.progress import track
import time

from .parsers.java_parser import JavaCassandraParser
from .parsers.cql_parser import CQLParser
from .detectors.allow_filtering import AllowFilteringDetector
from .detectors.partition_key import PartitionKeyDetector
from .detectors.batch_size import BatchSizeDetector
from .detectors.prepared_statement import PreparedStatementDetector
from .models.analysis_result import AnalysisResult
from .reporters.html_reporter import HTMLReporter
from .utils.file_scanner import FileScanner
from .utils.config import load_config

console = Console()

@click.group()
def cli():
    """Cassandra Code Analyzer - Phase 1 Prototype"""
    pass

@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
@click.option('--output', '-o', type=click.Path(), default='reports/report.html', help='Output path')
def analyze(target_path: str, config: str, output: str):
    """
    Analyze Cassandra code
    
    TARGET_PATH: Directory or file to analyze
    """
    console.print("[bold blue]🔍 Cassandra Code Analyzer[/bold blue]")
    console.print()
    
    start_time = time.time()
    
    # 設定の読み込み
    if config:
        cfg = load_config(Path(config))
    else:
        cfg = {
            'detection': {
                'allow_filtering': {'enabled': True, 'severity': 'high'},
                'partition_key': {'enabled': True, 'severity': 'critical'},
                'batch_size': {'enabled': True, 'threshold': 100, 'severity': 'medium'},
                'prepared_statement': {'enabled': True, 'min_executions': 5, 'severity': 'low'}
            }
        }
    
    # ファイルスキャン
    scanner = FileScanner()
    target = Path(target_path)
    
    if target.is_file():
        files = [target]
    else:
        files = scanner.scan_directory(target, patterns=['**/*DAO.java', '**/*Repository.java'])
    
    console.print(f"Found {len(files)} files to analyze")
    console.print()
    
    # パーサーと検出器の初期化
    java_parser = JavaCassandraParser()
    cql_parser = CQLParser()
    
    detectors = [
        AllowFilteringDetector(cfg['detection']['allow_filtering']),
        PartitionKeyDetector(cfg['detection']['partition_key']),
        BatchSizeDetector(cfg['detection']['batch_size']),
        PreparedStatementDetector(cfg['detection']['prepared_statement'])
    ]
    
    # 分析実行
    all_issues = []
    
    for file_path in track(files, description="Analyzing..."):
        # Javaファイル解析
        calls = java_parser.parse_file(file_path)
        
        for call in calls:
            # CQL解析
            cql_analysis = cql_parser.analyze(call.cql_text)
            
            # 各検出器で問題を検出
            for detector in detectors:
                issues = detector.detect(call, cql_analysis)
                all_issues.extend(issues)
    
    # 分析結果の集計
    issues_by_severity = {}
    for issue in all_issues:
        issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
    
    result = AnalysisResult(
        analyzed_files=[str(f) for f in files],
        total_issues=len(all_issues),
        issues_by_severity=issues_by_severity,
        issues=all_issues,
        analysis_time=time.time() - start_time
    )
    
    # レポート生成
    template_path = Path(__file__).parent / 'templates' / 'report.html'
    reporter = HTMLReporter(template_path)
    reporter.generate(result, Path(output))
    
    # サマリー表示
    console.print()
    console.print("[bold green]✓ Analysis Complete[/bold green]")
    console.print(f"Total Issues: {result.total_issues}")
    console.print(f"  Critical: {issues_by_severity.get('critical', 0)}")
    console.print(f"  High: {issues_by_severity.get('high', 0)}")
    console.print(f"  Medium: {issues_by_severity.get('medium', 0)}")
    console.print(f"  Low: {issues_by_severity.get('low', 0)}")
    console.print(f"Report: {output}")

if __name__ == '__main__':
    cli()
```

**実装タスク**:
```bash
claude-code implement "Create CLI in src/cassandra_analyzer/main.py"
```

---

## テスト戦略

### ユニットテスト

**ファイル**: `tests/test_parsers.py`

```python
"""
パーサーのテスト
"""
import pytest
from pathlib import Path
from cassandra_analyzer.parsers.java_parser import JavaCassandraParser
from cassandra_analyzer.parsers.cql_parser import CQLParser

def test_java_parser_allow_filtering():
    """ALLOW FILTERINGを含むコードのパース"""
    parser = JavaCassandraParser()
    
    # テストファイル
    test_file = Path('tests/fixtures/sample_dao_bad1.java')
    calls = parser.parse_file(test_file)
    
    assert len(calls) > 0
    assert any('ALLOW FILTERING' in call.cql_text for call in calls)

def test_cql_parser_allow_filtering():
    """CQLパーサーのALLOW FILTERING検出"""
    parser = CQLParser()
    
    cql = "SELECT * FROM users WHERE email = 'test@example.com' ALLOW FILTERING"
    analysis = parser.analyze(cql)
    
    assert analysis.has_allow_filtering == True
    assert len(analysis.issues) > 0
    assert analysis.issues[0]['type'] == 'ALLOW_FILTERING'
```

**実装タスク**:
```bash
# テストファイルの作成
claude-code create "Create test fixtures in tests/fixtures/"
claude-code implement "Write unit tests in tests/test_parsers.py"
claude-code implement "Write unit tests in tests/test_detectors.py"

# テスト実行
pytest tests/ -v
pytest tests/ --cov=src/cassandra_analyzer
```

---

## デプロイ手順

### ローカル実行

```bash
# インストール
pip install -e .

# 分析実行（Phase 1）
cd phase1_cassandra
python -m cassandra_analyzer analyze /path/to/dao/directory

# 設定ファイル指定
python -m cassandra_analyzer analyze /path/to/dao/directory --config config.yaml

# 出力先指定
python -m cassandra_analyzer analyze /path/to/dao/directory --output reports/my_report.html
```

### Docker化

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

ENTRYPOINT ["python", "-m", "cassandra_analyzer"]
CMD ["--help"]
```

```bash
# ビルド
docker build -t phase1-cassandra:latest phase1_cassandra/

# 実行
docker run -v /path/to/code:/code phase1-cassandra analyze /code
```

---

## Claude Code CLI 使用例

### 実装フロー

```bash
# 1. プロジェクト構造の作成
claude-code create "Initialize cassandra-analyzer project structure"

# 2. パーサーの実装
claude-code implement "Implement JavaCassandraParser with javalang"

# 3. 検出器の実装
claude-code implement "Implement AllowFilteringDetector"

# 4. テストの作成
claude-code test "Create unit tests for JavaCassandraParser"

# 5. 実行確認
claude-code run "Execute analyzer on test fixtures"

# 6. バグ修正
claude-code fix "Fix CQL extraction logic in java_parser.py"

# 7. ドキュメント生成
claude-code document "Generate API documentation"
```

---

## 次のステップ (Phase 2以降)

Phase 1完了後、以下を追加:

1. **LLM統合** (Week 3-4)
   - Claude Sonnet 4.5統合
   - データモデル評価
   - 修正提案生成

2. **Neo4j統合** (Week 5-6)
   - グラフDB接続
   - 依存関係の保存
   - 影響範囲分析

3. **ダッシュボード** (Week 7-8)
   - React + D3.js
   - リアルタイム分析
   - インタラクティブなグラフ

---

## トラブルシューティング

### よくある問題

**問題**: javalangでパースエラー
```python
# 解決: エラーハンドリング追加
try:
    tree = javalang.parse.parse(content)
except javalang.parser.JavaSyntaxError as e:
    logger.error(f"Parse error in {file_path}: {e}")
    return []
```

**問題**: CQL抽出失敗
```python
# 解決: 複数パターンに対応
cql_patterns = [
    r'"(SELECT.*?)"',
    r"'(SELECT.*?)'",
    r'"""(SELECT.*?)"""'
]
```

---

**このドキュメントの使い方**:
1. 上から順に実装
2. 各セクションでClaude Code CLIコマンドを実行
3. テストを通過させながら進める
4. Phase 1完了後にレビュー・改善

---

*最終更新: 2025年01月27日 16:30 JST*
*バージョン: v2.1.0*

**更新履歴:**
- v2.1.0 (2025年01月27日): プロジェクト構造の大幅変更（各フェーズをルート直下に配置）
