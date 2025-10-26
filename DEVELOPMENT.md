# DEVELOPMENT.md - 開発者ガイド

Cassandra Code Analyzerの開発に参加するための包括的なガイドです。

## 目次

- [開発環境のセットアップ](#開発環境のセットアップ)
- [プロジェクト構成](#プロジェクト構成)
- [アーキテクチャ](#アーキテクチャ)
- [開発ワークフロー](#開発ワークフロー)
- [テスト](#テスト)
- [新機能の追加方法](#新機能の追加方法)
- [コーディング規約](#コーディング規約)
- [リリースプロセス](#リリースプロセス)

## 開発環境のセットアップ

### 前提条件

- Python 3.8以上
- pip（パッケージ管理）
- git

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/cassandra-analyzer.git
cd cassandra-analyzer

# 2. 仮想環境の作成
python -m venv venv

# 3. 仮想環境の有効化
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 開発用依存パッケージのインストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. 開発モードでインストール
pip install -e .

# 6. テストの実行（環境確認）
pytest tests/ -v
```

### 開発ツール

推奨される開発ツール：

- **エディタ**: VSCode, PyCharm
- **リンター**: Ruff
- **フォーマッター**: Black
- **型チェッカー**: mypy
- **テストフレームワーク**: pytest

### VSCode設定例

`.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "editor.rulers": [88]
}
```

## プロジェクト構成

```
cassandra-analyzer/
├── src/
│   └── cassandra_analyzer/
│       ├── __init__.py
│       ├── analyzer.py          # メインアナライザークラス
│       ├── models/               # データモデル
│       │   ├── __init__.py
│       │   ├── cassandra_call.py  # Cassandra呼び出し情報
│       │   ├── issue.py           # 検出された問題
│       │   └── analysis_result.py # 分析結果全体
│       ├── parsers/              # コードパーサー
│       │   ├── __init__.py
│       │   ├── base.py           # パーサーの基底クラス
│       │   └── java_parser.py    # Javaパーサー実装
│       ├── detectors/            # 問題検出器
│       │   ├── __init__.py
│       │   ├── base.py           # 検出器の基底クラス
│       │   ├── allow_filtering_detector.py
│       │   ├── partition_key_detector.py
│       │   ├── batch_size_detector.py
│       │   └── prepared_statement_detector.py
│       └── reporters/            # レポート生成
│           ├── __init__.py
│           ├── base.py           # レポーターの基底クラス
│           ├── json_reporter.py
│           ├── markdown_reporter.py
│           └── html_reporter.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/                 # テスト用フィクスチャ
│   │   ├── sample_dao_good.java
│   │   ├── sample_dao_bad1.java
│   │   ├── sample_dao_bad2.java
│   │   └── sample_dao_bad3.java
│   ├── unit/                     # ユニットテスト
│   │   ├── test_parsers.py
│   │   ├── test_detectors.py
│   │   └── test_reporters.py
│   ├── integration/              # 統合テスト
│   │   └── test_pipeline.py
│   └── e2e/                      # E2Eテスト
│       └── test_full_analysis.py
├── reports/                      # 生成されたレポート（gitignore）
├── docs/                         # 追加ドキュメント
├── .github/                      # GitHub Actions
│   └── workflows/
│       └── ci.yml
├── requirements.txt              # 本番依存パッケージ
├── requirements-dev.txt          # 開発依存パッケージ
├── setup.py                      # パッケージ設定
├── pyproject.toml                # プロジェクト設定
├── README.md
├── USAGE.md
├── DEVELOPMENT.md
└── LICENSE
```

## アーキテクチャ

### 設計原則

1. **単一責任の原則**: 各クラスは1つの責任のみを持つ
2. **開放閉鎖の原則**: 拡張に開き、修正に閉じる
3. **依存性逆転の原則**: 抽象に依存し、具象に依存しない
4. **型安全性**: すべての関数・メソッドに型ヒントを付与

### コンポーネント概要

#### 1. Parser（パーサー）

**役割**: Javaソースコードを解析してCassandra関連の呼び出しを抽出

```python
class BaseParser(ABC):
    """パーサーの基底クラス"""

    @abstractmethod
    def parse_file(self, file_path: str) -> List[CassandraCall]:
        """ファイルを解析してCassandra呼び出しを抽出"""
        pass
```

**実装**:
- `JavaCassandraParser`: 正規表現ベースのJavaパーサー（Phase 1）

**将来の拡張**:
- ASTベースのパーサー（Phase 2）
- Kotlinサポート
- Scalaサポート

#### 2. Detector（検出器）

**役割**: Cassandra呼び出しから問題パターンを検出

```python
class BaseDetector(ABC):
    """検出器の基底クラス"""

    @abstractmethod
    def detect(self, call: CassandraCall) -> List[Issue]:
        """Cassandra呼び出しから問題を検出"""
        pass

    def is_enabled(self) -> bool:
        """検出器が有効かどうか"""
        return self.enabled
```

**実装済み検出器**:
- `AllowFilteringDetector`: ALLOW FILTERINGの検出
- `PartitionKeyDetector`: Partition Key未使用の検出
- `BatchSizeDetector`: 過大なバッチサイズの検出
- `PreparedStatementDetector`: Prepared Statement未使用の検出

**検出器追加の指針**:
- 各検出器は独立して動作可能
- 設定可能なパラメータを持つ
- 検出の根拠（evidence）を提供
- 信頼度（confidence）を数値化

#### 3. Reporter（レポーター）

**役割**: 分析結果を各種フォーマットで出力

```python
class BaseReporter(ABC):
    """レポーターの基底クラス"""

    @abstractmethod
    def generate(self, result: AnalysisResult) -> str:
        """分析結果からレポートを生成"""
        pass

    def save(self, content: str, file_path: str) -> None:
        """レポートをファイルに保存"""
        pass
```

**実装済みレポーター**:
- `JSONReporter`: JSON形式
- `MarkdownReporter`: Markdown形式
- `HTMLReporter`: HTML形式

#### 4. Analyzer（アナライザー）

**役割**: パーサー、検出器、レポーターを統合

```python
class CassandraAnalyzer:
    """メインアナライザークラス"""

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """単一ファイルを分析"""

    def analyze_directory(self, directory: str) -> AnalysisResult:
        """ディレクトリを分析"""

    def analyze_files(self, file_paths: List[str]) -> AnalysisResult:
        """複数ファイルを分析"""
```

### データフロー

```
Javaファイル
    ↓
[Parser] - CassandraCall抽出
    ↓
CassandraCall[]
    ↓
[Detector] - 問題検出
    ↓
Issue[]
    ↓
[Analyzer] - 結果集約
    ↓
AnalysisResult
    ↓
[Reporter] - レポート生成
    ↓
JSON/Markdown/HTML
```

## 開発ワークフロー

### ブランチ戦略

- `main`: 本番リリース用
- `develop`: 開発用メインブランチ
- `feature/*`: 機能追加用
- `bugfix/*`: バグ修正用
- `hotfix/*`: 緊急修正用

### 開発フロー

```bash
# 1. 最新のdevelopを取得
git checkout develop
git pull origin develop

# 2. 機能ブランチを作成
git checkout -b feature/new-detector

# 3. 開発・テスト
# コードを書く
pytest tests/ -v

# 4. コミット
git add .
git commit -m "feat: Add new detector for X"

# 5. プッシュ
git push origin feature/new-detector

# 6. Pull Requestを作成
# GitHubでPRを作成し、レビューを依頼
```

### コミットメッセージ規約

Conventional Commitsに従う：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

**例**:

```
feat(detector): Add timeout detection

Add detector for query timeout issues based on complexity analysis.

Closes #123
```

## テスト

### テスト戦略

**3層のテスト構造**:

1. **Unit Tests**: 個別コンポーネントのテスト
2. **Integration Tests**: コンポーネント間の連携テスト
3. **E2E Tests**: 完全なワークフローのテスト

### テストの実行

```bash
# 全テスト実行
pytest tests/ -v

# 特定のテストファイルのみ
pytest tests/unit/test_detectors.py -v

# 特定のテストケースのみ
pytest tests/unit/test_detectors.py::TestAllowFilteringDetector::test_detect_allow_filtering -v

# カバレッジレポート
pytest tests/ --cov=src/cassandra_analyzer --cov-report=html
# 生成されたhtmlcov/index.htmlをブラウザで開く

# 並列実行（高速化）
pytest tests/ -n auto
```

### テスト作成ガイドライン

#### ユニットテストの例

```python
"""新しい検出器のテスト"""
import pytest
from cassandra_analyzer.detectors import NewDetector
from cassandra_analyzer.models import CassandraCall


class TestNewDetector:
    """NewDetectorのテストクラス"""

    @pytest.fixture
    def detector(self):
        """検出器のフィクスチャ"""
        return NewDetector()

    def test_detect_issue(self, detector):
        """問題が検出されることを確認"""
        call = CassandraCall(
            file_path="test.java",
            line_number=10,
            method_name="execute",
            cql_text="SELECT * FROM table WHERE x = ?",
            query_type="SELECT",
        )

        issues = detector.detect(call)

        assert len(issues) > 0
        assert issues[0].severity == "high"
        assert issues[0].issue_type == "NEW_ISSUE_TYPE"

    def test_no_issue(self, detector):
        """問題がない場合"""
        call = CassandraCall(
            file_path="test.java",
            line_number=10,
            method_name="execute",
            cql_text="SELECT * FROM table WHERE partition_key = ?",
            query_type="SELECT",
        )

        issues = detector.detect(call)

        assert len(issues) == 0
```

### カバレッジ目標

- 全体カバレッジ: **> 80%**
- 新規コード: **> 90%**
- Critical部分: **100%**

## 新機能の追加方法

### 新しい検出器の追加

1. **検出器クラスの作成**

```python
# src/cassandra_analyzer/detectors/my_detector.py
from typing import List, Dict, Any
from .base import BaseDetector
from cassandra_analyzer.models import CassandraCall, Issue


class MyDetector(BaseDetector):
    """新しい検出器の説明"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # カスタム設定の読み込み
        self.threshold = self.config.get("threshold", 100)

    def detect(self, call: CassandraCall) -> List[Issue]:
        """検出ロジック"""
        issues = []

        # 検出ロジックの実装
        if self._should_report(call):
            issue = Issue(
                detector_name=self.__class__.__name__,
                issue_type="MY_ISSUE_TYPE",
                severity="medium",
                file_path=call.file_path,
                line_number=call.line_number,
                message="Issue detected",
                cql_text=call.cql_text,
                recommendation="Fix it by doing X",
                evidence=["Evidence 1", "Evidence 2"],
                confidence=0.85,
            )
            issues.append(issue)

        return issues

    def _should_report(self, call: CassandraCall) -> bool:
        """問題を報告すべきかどうかの判定"""
        # 判定ロジック
        return True
```

2. **検出器の登録**

```python
# src/cassandra_analyzer/detectors/__init__.py
from .my_detector import MyDetector

__all__ = [
    "BaseDetector",
    "AllowFilteringDetector",
    "PartitionKeyDetector",
    "BatchSizeDetector",
    "PreparedStatementDetector",
    "MyDetector",  # 追加
]
```

3. **アナライザーへの統合**

```python
# src/cassandra_analyzer/analyzer.py
from cassandra_analyzer.detectors import (
    AllowFilteringDetector,
    PartitionKeyDetector,
    BatchSizeDetector,
    PreparedStatementDetector,
    MyDetector,  # 追加
)

def _initialize_detectors(self) -> List:
    # ...
    if "my_detector" in enabled_detectors:
        config = detector_configs.get("my_detector", {})
        detectors.append(MyDetector(config=config))
```

4. **テストの作成**

```python
# tests/unit/test_detectors.py
class TestMyDetector:
    """MyDetectorのテスト"""

    @pytest.fixture
    def detector(self):
        return MyDetector()

    def test_detect(self, detector):
        # テストケース
        pass
```

### 新しいレポーターの追加

1. **レポータークラスの作成**

```python
# src/cassandra_analyzer/reporters/my_reporter.py
from .base import BaseReporter
from cassandra_analyzer.models import AnalysisResult


class MyReporter(BaseReporter):
    """新しいレポーター"""

    @property
    def format_name(self) -> str:
        return "MyFormat"

    @property
    def file_extension(self) -> str:
        return ".myext"

    def generate(self, result: AnalysisResult) -> str:
        """レポート生成"""
        # 生成ロジック
        return "Generated report content"
```

2. **レポーターの登録とテスト**（検出器と同様）

## コーディング規約

### Python Style Guide

- **PEP 8**に準拠
- **行の長さ**: 88文字（Black準拠）
- **インデント**: 4スペース
- **クォート**: ダブルクォート `"` を推奨

### 型ヒント

すべての関数・メソッドに型ヒントを付与：

```python
def analyze_file(self, file_path: str) -> AnalysisResult:
    """ファイルを分析"""
    pass

def process_data(
    items: List[str],
    config: Dict[str, Any],
    threshold: Optional[int] = None
) -> Tuple[int, List[Issue]]:
    """データを処理"""
    pass
```

### Docstring

Google Styleを使用：

```python
def detect(self, call: CassandraCall) -> List[Issue]:
    """Cassandra呼び出しから問題を検出

    Args:
        call: Cassandra呼び出し情報

    Returns:
        検出された問題のリスト

    Raises:
        ValueError: 無効な呼び出し情報の場合
    """
    pass
```

### 命名規則

- **クラス**: PascalCase (`MyDetector`)
- **関数/メソッド**: snake_case (`detect_issues()`)
- **定数**: UPPER_SNAKE_CASE (`MAX_BATCH_SIZE`)
- **プライベート**: アンダースコアプレフィックス (`_internal_method()`)

### インポート順序

```python
# 1. 標準ライブラリ
import os
import sys
from typing import List, Dict

# 2. サードパーティ
import pytest

# 3. ローカル
from cassandra_analyzer.models import Issue
from .base import BaseDetector
```

## コード品質チェック

### 自動チェックの実行

```bash
# フォーマット
black src/ tests/

# リント
ruff check .

# 型チェック
mypy src/

# テスト
pytest tests/ --cov=src/cassandra_analyzer

# 全チェック一括実行
make check  # または手動で上記を順次実行
```

### pre-commitフックの設定

```bash
# pre-commitのインストール
pip install pre-commit

# フックの設定
pre-commit install

# 手動実行
pre-commit run --all-files
```

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

## リリースプロセス

### バージョニング

Semantic Versioningを使用：

- `MAJOR.MINOR.PATCH`
- 例: `1.0.0`, `1.1.0`, `1.1.1`

### リリース手順

```bash
# 1. developブランチで最終確認
git checkout develop
pytest tests/ -v
make check

# 2. バージョン更新
# setup.py, pyproject.toml, __init__.pyのバージョンを更新

# 3. CHANGELOGの更新
# CHANGELOG.mdに変更内容を記載

# 4. mainにマージ
git checkout main
git merge develop

# 5. タグ作成
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags

# 6. GitHubでリリースを作成
# GitHub Releasesでタグからリリースを作成
```

## トラブルシューティング

### よくある問題

**問題**: テストが失敗する

```bash
# キャッシュをクリア
pytest --cache-clear tests/

# 依存関係を再インストール
pip install -r requirements.txt --force-reinstall
```

**問題**: 型チェックエラー

```bash
# mypyキャッシュをクリア
mypy --clear-cache src/
```

**問題**: import エラー

```bash
# 開発モードで再インストール
pip install -e .
```

## コントリビューション

コントリビューションは大歓迎です！

1. Issueで議論
2. Forkしてfeatureブランチを作成
3. 変更をコミット
4. テストを追加・実行
5. Pull Requestを作成

## リソース

- [Python公式ドキュメント](https://docs.python.org/3/)
- [pytest公式ドキュメント](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)

---

質問があれば、お気軽にIssueやDiscussionsで聞いてください！
