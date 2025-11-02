# Phase 6-5: 統合ダッシュボード設計書

**Version**: 1.0.0
**Date**: 2025-01-31
**Status**: 🚧 Design Phase

---

## 概要

Phase 6-5では、Elasticsearch、MySQL、LLMの3つの分析エンジンを統合し、統一されたインターフェースとレポーティングシステムを提供します。

### 目標

1. **統合アナライザー**: 複数のDBタイプを一度に分析
2. **統一レポート**: 一貫したフォーマットでの問題報告
3. **CLIインターフェース**: 使いやすいコマンドラインツール
4. **拡張性**: 将来のDB（Redis、PostgreSQLなど）の追加が容易

---

## アーキテクチャ

### 既存コンポーネント（完成済み）

```
phase4_multidb/src/multidb_analyzer/
├── core/                           ✅ 基底クラス
│   ├── base_detector.py           (BaseDetector, Issue, Severity)
│   ├── base_parser.py             (BaseParser)
│   └── plugin_manager.py          (PluginManager)
│
├── elasticsearch/                  ✅ 99% coverage, 234 tests
│   ├── parsers/
│   │   └── java_client_parser.py
│   ├── detectors/
│   │   ├── mapping_detector.py
│   │   ├── script_query_detector.py
│   │   ├── shard_detector.py
│   │   └── wildcard_detector.py
│   └── models/
│       └── es_models.py
│
├── mysql/                          ✅ 93% coverage, 94 tests
│   ├── parsers/
│   │   └── mysql_parser.py
│   ├── detectors/
│   │   ├── nplus_one_detector.py
│   │   ├── full_table_scan_detector.py
│   │   ├── missing_index_detector.py
│   │   └── join_performance_detector.py
│   └── models/
│       └── mysql_models.py
│
└── llm/                            ✅ Claude API統合
    ├── claude_client.py
    ├── llm_optimizer.py
    └── prompt_templates.py
```

### 新規コンポーネント（Phase 6-5）

```
phase4_multidb/src/multidb_analyzer/
├── unified/                        🆕 統合レイヤー
│   ├── __init__.py
│   ├── unified_analyzer.py        # メイン統合クラス
│   ├── report_generator.py        # 統合レポート生成
│   └── config.py                  # 設定管理
│
├── reporters/                      🆕 レポート生成
│   ├── __init__.py
│   ├── base_reporter.py           # 基底レポータークラス
│   ├── html_reporter.py           # HTMLレポート
│   ├── json_reporter.py           # JSONレポート
│   ├── markdown_reporter.py       # Markdownレポート
│   └── console_reporter.py        # コンソール出力
│
└── cli/                            🆕 CLIインターフェース
    ├── __init__.py
    ├── main.py                    # エントリーポイント
    ├── commands.py                # Clickコマンド定義
    └── formatters.py              # 出力フォーマッター
```

---

## コンポーネント詳細設計

### 1. UnifiedAnalyzer

**責任**: 複数のDBタイプを統合分析

```python
from typing import List, Dict, Optional
from pathlib import Path
from multidb_analyzer.core.base_detector import Issue

class UnifiedAnalyzer:
    """
    統合アナライザー

    複数のDBタイプ（Elasticsearch、MySQL）を一度に分析し、
    統一されたIssueリストを返します。
    """

    def __init__(
        self,
        enable_elasticsearch: bool = True,
        enable_mysql: bool = True,
        enable_llm: bool = False,
        llm_api_key: Optional[str] = None
    ):
        """初期化"""

    def analyze(
        self,
        source_paths: List[Path],
        output_dir: Optional[Path] = None,
        config: Optional[Dict] = None
    ) -> AnalysisResult:
        """
        統合分析を実行

        Args:
            source_paths: 分析対象のソースコードパス
            output_dir: 出力ディレクトリ（Noneの場合は./reports/）
            config: カスタム設定

        Returns:
            AnalysisResult: 分析結果
        """

    def _analyze_elasticsearch(self, paths: List[Path]) -> List[Issue]:
        """Elasticsearch分析"""

    def _analyze_mysql(self, paths: List[Path]) -> List[Issue]:
        """MySQL分析"""

    def _apply_llm_optimization(self, issues: List[Issue]) -> List[Issue]:
        """LLM最適化を適用"""
```

**主要メソッド**:
- `analyze()`: メイン分析メソッド
- `_analyze_elasticsearch()`: Elasticsearch特化分析
- `_analyze_mysql()`: MySQL特化分析
- `_apply_llm_optimization()`: LLMによる問題最適化

### 2. AnalysisResult

**責任**: 分析結果の一元管理

```python
@dataclass
class AnalysisResult:
    """分析結果"""

    # 基本情報
    timestamp: datetime
    total_files: int
    analyzed_files: int
    execution_time: float

    # 問題情報
    issues: List[Issue]
    issues_by_severity: Dict[Severity, List[Issue]]
    issues_by_category: Dict[IssueCategory, List[Issue]]
    issues_by_db_type: Dict[str, List[Issue]]  # 'elasticsearch', 'mysql'

    # 統計情報
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    # メタデータ
    config: Dict[str, Any]
    warnings: List[str]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""

    def get_summary(self) -> str:
        """サマリーテキストを取得"""

    def get_top_issues(self, limit: int = 10) -> List[Issue]:
        """重大度順にトップN問題を取得"""
```

### 3. ReportGenerator

**責任**: 統合レポートの生成

```python
class ReportGenerator:
    """統合レポート生成器"""

    def __init__(self, result: AnalysisResult):
        self.result = result

    def generate_all(
        self,
        output_dir: Path,
        formats: List[str] = ['html', 'json', 'markdown']
    ) -> Dict[str, Path]:
        """全形式のレポートを生成"""

    def generate_html(self, output_path: Path) -> Path:
        """HTMLレポート生成"""

    def generate_json(self, output_path: Path) -> Path:
        """JSONレポート生成"""

    def generate_markdown(self, output_path: Path) -> Path:
        """Markdownレポート生成"""

    def generate_console(self) -> str:
        """コンソール出力用テキスト生成"""
```

### 4. Reporters

#### BaseReporter

```python
class BaseReporter(ABC):
    """基底レポータークラス"""

    @abstractmethod
    def generate(
        self,
        result: AnalysisResult,
        output_path: Path
    ) -> Path:
        """レポート生成"""
        pass

    def _format_issue(self, issue: Issue) -> str:
        """Issue整形"""
        pass
```

#### HTMLReporter

- **機能**: インタラクティブなHTMLレポート
- **特徴**:
  - 問題の重大度別カラーコーディング
  - フィルタリング機能（重大度、カテゴリ、DBタイプ）
  - 折りたたみ可能な詳細表示
  - サマリーダッシュボード

#### JSONReporter

- **機能**: 機械可読なJSON形式
- **用途**: CI/CD統合、自動処理

#### MarkdownReporter

- **機能**: GitHub互換のMarkdown
- **用途**: PRコメント、ドキュメント

#### ConsoleReporter

- **機能**: Rich/Clickを使った美しいコンソール出力
- **特徴**:
  - カラーコーディング
  - プログレスバー
  - テーブル表示

---

## CLIインターフェース設計

### コマンド構造

```bash
# 基本的な分析
multidb-analyzer analyze <source_path>

# 特定のDB分析のみ
multidb-analyzer analyze <source_path> --db elasticsearch
multidb-analyzer analyze <source_path> --db mysql

# 複数パス分析
multidb-analyzer analyze <path1> <path2> <path3>

# LLM最適化有効化
multidb-analyzer analyze <source_path> --llm --api-key <key>

# レポート形式指定
multidb-analyzer analyze <source_path> --format html,json,markdown

# 出力ディレクトリ指定
multidb-analyzer analyze <source_path> --output ./reports

# 設定ファイル使用
multidb-analyzer analyze <source_path> --config config.yaml

# 詳細情報表示
multidb-analyzer analyze <source_path> --verbose

# ドライラン（レポート生成なし）
multidb-analyzer analyze <source_path> --dry-run

# バージョン情報
multidb-analyzer --version

# ヘルプ
multidb-analyzer --help
multidb-analyzer analyze --help
```

### Click実装例

```python
import click
from rich.console import Console
from pathlib import Path

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """MultiDB Analyzer - 複数DB静的コード分析ツール"""
    pass

@cli.command()
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True))
@click.option('--db', multiple=True, type=click.Choice(['elasticsearch', 'mysql', 'all']),
              default=['all'], help='分析するDBタイプ')
@click.option('--llm', is_flag=True, help='LLM最適化を有効化')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Claude APIキー')
@click.option('--format', multiple=True,
              type=click.Choice(['html', 'json', 'markdown', 'console']),
              default=['html', 'console'], help='レポート形式')
@click.option('--output', '-o', type=click.Path(), default='./reports',
              help='出力ディレクトリ')
@click.option('--config', '-c', type=click.Path(exists=True),
              help='設定ファイル')
@click.option('--verbose', '-v', is_flag=True, help='詳細情報表示')
@click.option('--dry-run', is_flag=True, help='ドライラン（レポート生成なし）')
def analyze(source_paths, db, llm, api_key, format, output, config, verbose, dry_run):
    """ソースコードを分析"""
    console = Console()

    # 分析実行
    analyzer = UnifiedAnalyzer(
        enable_elasticsearch='elasticsearch' in db or 'all' in db,
        enable_mysql='mysql' in db or 'all' in db,
        enable_llm=llm,
        llm_api_key=api_key
    )

    result = analyzer.analyze(
        source_paths=[Path(p) for p in source_paths],
        output_dir=Path(output) if not dry_run else None,
        config=load_config(config) if config else None
    )

    # レポート生成
    if not dry_run:
        generator = ReportGenerator(result)
        reports = generator.generate_all(Path(output), formats=list(format))

    # コンソール出力
    if 'console' in format or verbose:
        console.print(result.get_summary())
```

---

## 設定ファイル形式

### config.yaml

```yaml
# MultiDB Analyzer Configuration

# 分析対象
analysis:
  enabled_databases:
    - elasticsearch
    - mysql

  # パス除外パターン
  exclude_patterns:
    - "**/node_modules/**"
    - "**/target/**"
    - "**/.git/**"
    - "**/test/**"  # テストファイルを除外する場合

  # ファイル拡張子
  include_extensions:
    - .java
    - .py
    - .ts
    - .go

# 検出器設定
detectors:
  # Elasticsearch
  elasticsearch:
    mapping_detector:
      enabled: true
      severity: HIGH
    wildcard_detector:
      enabled: true
      severity: CRITICAL
    shard_detector:
      enabled: true
      max_shards: 5
    script_query_detector:
      enabled: true

  # MySQL
  mysql:
    nplus_one_detector:
      enabled: true
      severity: HIGH
    full_table_scan_detector:
      enabled: true
      severity: CRITICAL
    missing_index_detector:
      enabled: true
      severity: MEDIUM
    join_performance_detector:
      enabled: true
      max_joins: 4

# LLM設定
llm:
  enabled: false
  provider: claude
  model: claude-sonnet-3.5
  max_tokens: 4000
  temperature: 0.3
  # API キーは環境変数 ANTHROPIC_API_KEY から読み込み

# レポート設定
reports:
  formats:
    - html
    - json
    - markdown

  html:
    template: default
    include_code_snippets: true
    max_snippet_lines: 10

  json:
    pretty: true
    include_metadata: true

  markdown:
    include_toc: true
    include_summary: true

# 出力設定
output:
  directory: ./reports
  timestamp_format: "%Y%m%d_%H%M%S"
  create_subdirs: true  # DB別サブディレクトリ作成

# ログ設定
logging:
  level: INFO
  file: ./logs/multidb_analyzer.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## データフロー

```
┌─────────────────┐
│  Source Code    │
│  (Java/Python)  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│    UnifiedAnalyzer              │
│  ┌───────────────────────────┐  │
│  │ ElasticsearchAnalyzer     │  │
│  │  - JavaClientParser       │  │
│  │  - 4 Detectors            │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ MySQLAnalyzer             │  │
│  │  - MySQLParser            │  │
│  │  - 4 Detectors            │  │
│  └───────────────────────────┘  │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  Issues Collection              │
│  - Severity sorting             │
│  - Category grouping            │
│  - Deduplication                │
└────────┬────────────────────────┘
         │
         v (optional)
┌─────────────────────────────────┐
│  LLM Optimizer                  │
│  - Context analysis             │
│  - Priority adjustment          │
│  - Fix suggestions              │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  AnalysisResult                 │
│  - Aggregated statistics        │
│  - Metadata                     │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  ReportGenerator                │
│  ┌──────────────────────────┐   │
│  │ HTMLReporter             │   │
│  ├──────────────────────────┤   │
│  │ JSONReporter             │   │
│  ├──────────────────────────┤   │
│  │ MarkdownReporter         │   │
│  ├──────────────────────────┤   │
│  │ ConsoleReporter          │   │
│  └──────────────────────────┘   │
└────────┬────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  Reports                        │
│  - analysis_report.html         │
│  - analysis_report.json         │
│  - analysis_report.md           │
│  - Console output               │
└─────────────────────────────────┘
```

---

## テスト戦略

### テストカバレッジ目標

| コンポーネント | カバレッジ目標 |
|---------------|---------------|
| UnifiedAnalyzer | 90%+ |
| ReportGenerator | 90%+ |
| Reporters | 85%+ |
| CLI | 80%+ |

### テストスイート構成

```
tests/
├── test_unified/
│   ├── test_unified_analyzer.py        # 統合テスト
│   ├── test_report_generator.py        # レポート生成テスト
│   └── test_config.py                  # 設定テスト
│
├── test_reporters/
│   ├── test_html_reporter.py
│   ├── test_json_reporter.py
│   ├── test_markdown_reporter.py
│   └── test_console_reporter.py
│
├── test_cli/
│   ├── test_commands.py                # CLIコマンドテスト
│   └── test_formatters.py              # フォーマッターテスト
│
└── test_integration/
    ├── test_elasticsearch_mysql_integration.py
    ├── test_llm_integration.py
    └── test_end_to_end.py              # E2Eテスト
```

---

## 実装順序

### Step 1: Core Infrastructure (Day 1)
1. ✅ AnalysisResult dataclass
2. ✅ UnifiedAnalyzer基本構造
3. ✅ Config loader

### Step 2: Reporters (Day 2-3)
1. ✅ BaseReporter
2. ✅ JSONReporter (最もシンプル)
3. ✅ ConsoleReporter
4. ✅ MarkdownReporter
5. ✅ HTMLReporter (最も複雑)

### Step 3: CLI Interface (Day 4)
1. ✅ Click setup
2. ✅ Main commands
3. ✅ Rich formatting

### Step 4: Integration & Testing (Day 5-6)
1. ✅ Unit tests
2. ✅ Integration tests
3. ✅ E2E tests
4. ✅ Documentation

---

## 成功基準

### 機能要件
- ✅ Elasticsearch + MySQL統合分析
- ✅ 4種類のレポート形式
- ✅ CLI実装
- ✅ 設定ファイルサポート
- ✅ LLM統合（オプション）

### 品質要件
- ✅ テストカバレッジ > 85%
- ✅ 全テスト合格
- ✅ 型ヒント100%
- ✅ Docstring完備

### パフォーマンス要件
- ✅ 100ファイル分析 < 30秒
- ✅ レポート生成 < 5秒
- ✅ メモリ使用量 < 500MB

---

## 次のアクション

1. **AnalysisResult実装** → 分析結果データ構造
2. **UnifiedAnalyzer実装** → 統合分析エンジン
3. **BaseReporter実装** → レポーター基底クラス
4. **JSONReporter実装** → 最もシンプルなレポーター
5. **テスト作成** → 各コンポーネントのテスト

---

**設計完了**: 2025-01-31
**次フェーズ**: 実装開始
**予定期間**: 5-6日
