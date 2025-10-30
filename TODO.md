# 4J_Claude マルチフェーズコード分析システム - TODO管理

*バージョン: v6.0.0*
*最終更新: 2025年01月29日 16:21 JST*

**プロジェクト期間**: Phase 1-5 完了
**開始日**: 2024年10月28日
**完了日**: 2025年01月29日

---

## 📊 プロジェクト進捗ダッシュボード

```
全体進捗: [████████████████████] 100% (全5フェーズ完了)

Phase 1 (Cassandra分析):     [████████████████████] 100% ✅ 完了
Phase 2 (LLM統合):          [████████████████████] 100% ✅ 完了
Phase 3 (Neo4j/グラフDB):    [████████████████████] 100% ✅ 完了
Phase 4 (可視化・影響分析):   [████████████████████] 100% ✅ 完了
Phase 5 (認証・監視):        [████████████████████] 100% ✅ 完了

完了日: 2025年01月29日 JST
最終実績:
  - Phase 1: 95.34%カバレッジ、284テストケース ✅
  - Phase 2: 90%カバレッジ、Claude API統合 ✅
  - Phase 3: 83%カバレッジ、43統合テスト ✅
  - Phase 4: 100%カバレッジ、7分析API実装 ✅
  - Phase 5: 100%カバレッジ（796/796行）、149テストケース ✅
  - 総エンドポイント: 16個（分析7 + 認証9）
  - 総テストケース: 149件（全パス）
```

---

## ✅ 完了済みフェーズ詳細

### Phase 1-5 実装内容（全完了）
すべてのフェーズの実装が完了しました。詳細は各フェーズのドキュメントを参照してください：
- Phase 1: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
- Phase 2: [`phase2_llm/README.md`](./phase2_llm/README.md)
- Phase 3: [`phase3_neo4j/README.md`](./phase3_neo4j/README.md)
- Phase 4/5: [`phase4_visualization/README.md`](./phase4_visualization/README.md)

---

## 🚀 Phase 6: 次期計画（2025 Q2）

### マルチデータベース対応
**開始予定**: 2025年04月01日
**目標期限**: 2025年06月30日

#### 実装予定機能
1. **PostgreSQL/MySQL統合**
   - SQLパーサー実装
   - クエリパフォーマンス分析
   - インデックス最適化提案

2. **NoSQL データベース統合**
   - MongoDB クエリ分析
   - Redis パターン検出
   - Cassandra分析の拡張

3. **検索エンジン統合**
   - Elasticsearch クエリ最適化
   - Solr インテグレーション

4. **統合ダッシュボード**
   - マルチDB横断分析
   - 統一レポート生成
   - パフォーマンス比較

---

## 🎯 Week 1: 基盤実装 (10月28日 - 11月1日) [完了]

### 目標
- プロジェクト構造の構築
- JavaパーサーとCQLパーサーの実装
- 基本的な検出器の実装
- ユニットテストの実装

---

## Day 1: プロジェクト初期化とセットアップ (10月28日 月曜日)

### 🌅 午前 (4時間): 環境構築

#### Task 1.1: プロジェクト構造の作成
**優先度**: 🔴 Critical  
**所要時間**: 30分  
**担当**: 開発者  
**依存**: なし

**タスク内容**:
```bash
# Claude Code CLIで実行
mkdir cassandra-analyzer
cd cassandra-analyzer

# ディレクトリ構造作成
mkdir -p src/cassandra_analyzer/{parsers,detectors,models,reporters,utils,templates}
mkdir -p tests/{fixtures,unit,integration}
mkdir -p docs
mkdir -p examples
mkdir -p reports

# 初期ファイル作成
touch src/cassandra_analyzer/__init__.py
touch tests/__init__.py
touch README.md
touch requirements.txt
touch setup.py
touch pyproject.toml
```

**完了条件**:
- [ ] ディレクトリ構造が作成されている
- [ ] 全ての`__init__.py`が存在する
- [ ] `README.md`が作成されている

**Claude Code CLIコマンド**:
```bash
claude-code create "Initialize cassandra-analyzer project with complete directory structure as specified in DETAILED_DESIGN.md"
```

---

#### Task 1.2: 依存パッケージのセットアップ
**優先度**: 🔴 Critical  
**所要時間**: 45分  
**依存**: Task 1.1

**タスク内容**:
1. `requirements.txt`の作成
```txt
# requirements.txt
javalang==0.13.0
jinja2==3.1.2
pyyaml==6.0.1
click==8.1.7
rich==13.7.0
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
mypy==1.7.1
ruff==0.1.7
black==23.12.0
```

2. 仮想環境の作成とインストール
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

3. `setup.py`の作成
```python
from setuptools import setup, find_packages

setup(
    name="cassandra-analyzer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "javalang>=0.13.0",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "cassandra-analyzer=cassandra_analyzer.main:cli",
        ],
    },
    python_requires=">=3.11",
)
```

**完了条件**:
- [ ] `requirements.txt`が作成されている
- [ ] 仮想環境が作成されている
- [ ] 全依存パッケージがインストールされている
- [ ] `pip install -e .`が成功する

**Claude Code CLIコマンド**:
```bash
claude-code create "Create requirements.txt and setup.py with all dependencies"
claude-code run "pip install -r requirements.txt && pip install -e ."
```

---

#### Task 1.3: 設定ファイルの作成
**優先度**: 🟡 Medium  
**所要時間**: 30分  
**依存**: Task 1.1

**タスク内容**:
1. `config.yaml`のテンプレート作成
2. `pyproject.toml`の設定 (ruff, mypy, pytest)

```yaml
# config.yaml
analysis:
  target_directories:
    - "src/main/java"
  
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
  format: "html"
  output_path: "reports/analysis_report.html"
  include_code_snippets: true
  include_recommendations: true

logging:
  level: "INFO"
  format: "structured"
  output: "logs/analyzer.log"
```

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=src/cassandra_analyzer --cov-report=html"
```

**完了条件**:
- [ ] `config.yaml`が作成されている
- [ ] `pyproject.toml`が設定されている
- [ ] ruffで`ruff check .`が実行できる

**Claude Code CLIコマンド**:
```bash
claude-code create "Create config.yaml and pyproject.toml with analyzer settings"
```

---

#### Task 1.4: テストフィクスチャの準備
**優先度**: 🟡 Medium  
**所要時間**: 1時間  
**依存**: Task 1.1

**タスク内容**:
`tests/fixtures/`にサンプルJavaファイルを作成

1. `sample_dao_good.java` - 問題のないコード
2. `sample_dao_bad1.java` - ALLOW FILTERING
3. `sample_dao_bad2.java` - Partition Key未使用
4. `sample_dao_bad3.java` - 大量BATCH
5. `sample_dao_bad4.java` - Prepared Statement未使用

**完了条件**:
- [ ] 5つのサンプルファイルが作成されている
- [ ] 各ファイルが正しいJava構文である
- [ ] 各ファイルが特定の問題パターンを含む

**Claude Code CLIコマンド**:
```bash
claude-code create "Create test fixtures: sample_dao_good.java and 4 bad examples in tests/fixtures/"
```

---

### 🌆 午後 (4時間): パーサー実装開始

#### Task 1.5: データモデルの実装
**優先度**: 🔴 Critical  
**所要時間**: 1時間  
**依存**: Task 1.1

**タスク内容**:
以下のモデルクラスを実装:

1. `src/cassandra_analyzer/models/code_element.py`
2. `src/cassandra_analyzer/models/issue.py`
3. `src/cassandra_analyzer/models/analysis_result.py`

詳細は`DETAILED_DESIGN.md`のセクション2.2.1参照

**完了条件**:
- [ ] `Issue`クラスが実装されている
- [ ] `AnalysisResult`クラスが実装されている
- [ ] `to_dict()`メソッドが実装されている
- [ ] 型ヒントが正しく設定されている
- [ ] docstringが記載されている

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create Issue and AnalysisResult models in src/cassandra_analyzer/models/ following DETAILED_DESIGN.md section 2.2.1"
```

**検証**:
```bash
# 型チェック
mypy src/cassandra_analyzer/models/

# Pythonインポートテスト
python -c "from cassandra_analyzer.models.issue import Issue; print('OK')"
```

---

#### Task 1.6: JavaParserの基本実装
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Task 1.2, Task 1.5

**タスク内容**:
`src/cassandra_analyzer/parsers/java_parser.py`を実装

実装範囲:
- [ ] `CassandraCall` dataclass
- [ ] `CallType` enum
- [ ] `JavaCassandraParser` クラス
- [ ] `parse_file()` メソッド
- [ ] `_is_cassandra_call()` メソッド
- [ ] `_extract_call_info()` メソッド
- [ ] `_extract_cql_string()` メソッド（基本実装のみ）

詳細は`DETAILED_DESIGN.md`のセクション2.2.1参照

**完了条件**:
- [ ] クラスが実装されている
- [ ] `parse_file()`でSimple SELECTを抽出できる
- [ ] CQL文字列リテラルを抽出できる
- [ ] 行番号が正しく取得できる

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create JavaCassandraParser class in src/cassandra_analyzer/parsers/java_parser.py following DETAILED_DESIGN.md section 2.2.1. Focus on basic CQL extraction from string literals first."
```

**検証**:
```python
# tests/test_basic_parser.py
from pathlib import Path
from cassandra_analyzer.parsers.java_parser import JavaCassandraParser

def test_parse_simple_file():
    parser = JavaCassandraParser()
    test_file = Path("tests/fixtures/sample_dao_good.java")
    calls = parser.parse_file(test_file)
    assert len(calls) > 0
    assert calls[0].cql_text is not None
    print("✓ Basic parser test passed")

if __name__ == "__main__":
    test_parse_simple_file()
```

```bash
python tests/test_basic_parser.py
```

---

#### Task 1.7: 簡易ユニットテストの作成
**優先度**: 🔴 Critical  
**所要時間**: 1時間  
**依存**: Task 1.6

**タスク内容**:
`tests/unit/test_java_parser.py`の作成

テストケース:
1. シンプルなSELECTのパース
2. ALLOW FILTERINGを含むクエリのパース
3. 複数のCQL呼び出しの検出
4. エラーハンドリング（構文エラーファイル）

**完了条件**:
- [ ] 4つのテストケースが実装されている
- [ ] `pytest tests/unit/test_java_parser.py`が成功する
- [ ] カバレッジ > 70%

**Claude Code CLIコマンド**:
```bash
claude-code test "Create unit tests for JavaCassandraParser in tests/unit/test_java_parser.py with 4 test cases covering basic parsing, ALLOW FILTERING, multiple calls, and error handling"
```

**検証**:
```bash
pytest tests/unit/test_java_parser.py -v
pytest tests/unit/test_java_parser.py --cov=src/cassandra_analyzer/parsers
```

---

### 📝 Day 1まとめ

**完了チェックリスト**:
- [ ] プロジェクト構造が完成
- [ ] 依存パッケージがインストール済み
- [ ] 設定ファイルが作成済み
- [ ] テストフィクスチャが準備完了
- [ ] データモデルが実装済み
- [ ] JavaParser基本実装が完了
- [ ] 基本的なユニットテストが通過

**Day 1 終了時の成果物**:
```
cassandra-analyzer/
├── src/cassandra_analyzer/
│   ├── models/
│   │   ├── issue.py ✅
│   │   └── analysis_result.py ✅
│   └── parsers/
│       └── java_parser.py ✅ (基本実装)
├── tests/
│   ├── fixtures/ ✅
│   └── unit/
│       └── test_java_parser.py ✅
├── requirements.txt ✅
├── setup.py ✅
└── config.yaml ✅
```

---

## Day 2: CQLパーサーと定数解決 (10月29日 火曜日)

### 🌅 午前 (4時間): CQLパーサー実装

#### Task 2.1: CQLParserの実装
**優先度**: 🔴 Critical  
**所要時間**: 2.5時間  
**依存**: Day 1完了

**タスク内容**:
`src/cassandra_analyzer/parsers/cql_parser.py`を実装

実装範囲:
- [ ] `QueryType` enum
- [ ] `WhereClause` dataclass
- [ ] `CQLAnalysis` dataclass
- [ ] `CQLParser` クラス
- [ ] `analyze()` メソッド
- [ ] `_normalize_cql()` メソッド
- [ ] `_determine_query_type()` メソッド
- [ ] `_extract_tables()` メソッド
- [ ] `_parse_where_clause()` メソッド
- [ ] `_detect_issues()` メソッド

詳細は`DETAILED_DESIGN.md`のセクション2.2.2参照

**完了条件**:
- [ ] ALLOW FILTERING検出ができる
- [ ] WHERE句の解析ができる
- [ ] テーブル名抽出ができる
- [ ] 問題パターン検出ができる

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create CQLParser class in src/cassandra_analyzer/parsers/cql_parser.py following DETAILED_DESIGN.md section 2.2.2. Implement all core methods for CQL analysis and issue detection."
```

**検証**:
```python
# tests/test_cql_basic.py
from cassandra_analyzer.parsers.cql_parser import CQLParser

def test_allow_filtering_detection():
    parser = CQLParser()
    cql = "SELECT * FROM users WHERE email = 'test@example.com' ALLOW FILTERING"
    analysis = parser.analyze(cql)
    assert analysis.has_allow_filtering == True
    assert len(analysis.issues) > 0
    print("✓ ALLOW FILTERING detection works")

if __name__ == "__main__":
    test_allow_filtering_detection()
```

---

#### Task 2.2: CQLParserのユニットテスト
**優先度**: 🔴 Critical  
**所要時間**: 1.5時間  
**依存**: Task 2.1

**タスク内容**:
`tests/unit/test_cql_parser.py`の作成

テストケース:
1. ALLOW FILTERING検出
2. Partition Key未使用検出
3. BATCH処理検出
4. SELECT * 検出
5. IN句の検出
6. WHERE句の詳細解析

**完了条件**:
- [ ] 6つのテストケースが実装されている
- [ ] 全テストが成功する
- [ ] カバレッジ > 80%

**Claude Code CLIコマンド**:
```bash
claude-code test "Create comprehensive unit tests for CQLParser in tests/unit/test_cql_parser.py covering all detection patterns: ALLOW FILTERING, partition key, batch, SELECT *, IN clause, WHERE clause parsing"
```

**検証**:
```bash
pytest tests/unit/test_cql_parser.py -v --cov=src/cassandra_analyzer/parsers/cql_parser.py
```

---

### 🌆 午後 (4時間): JavaParser拡張

#### Task 2.3: 定数解決の実装
**優先度**: 🟠 High  
**所要時間**: 2時間  
**依存**: Task 1.6

**タスク内容**:
JavaParserに定数解決機能を追加

実装内容:
- [ ] `_extract_constants()` メソッド
- [ ] `_resolve_constant_reference()` メソッド
- [ ] 定数キャッシュの実装
- [ ] 定数参照の解決ロジック

**完了条件**:
- [ ] `static final String CQL_XXX = "..."`を抽出できる
- [ ] 定数参照を解決できる
- [ ] キャッシュが機能する

**Claude Code CLIコマンド**:
```bash
claude-code implement "Add constant resolution to JavaCassandraParser. Implement _extract_constants() and constant caching to resolve CQL constants defined as 'static final String'"
```

**検証**:
```python
def test_constant_resolution():
    parser = JavaCassandraParser(config={'resolve_constants': True})
    test_file = Path("tests/fixtures/sample_dao_with_constants.java")
    calls = parser.parse_file(test_file)
    
    # 定数参照が解決されているか確認
    assert any('SELECT' in call.cql_text for call in calls)
    assert not any('[CONSTANT:' in call.cql_text for call in calls)
    print("✓ Constant resolution works")
```

---

#### Task 2.4: Prepared Statement判定の強化
**優先度**: 🟡 Medium  
**所要時間**: 1時間  
**依存**: Task 2.3

**タスク内容**:
Prepared Statement使用の判定ロジックを強化

実装内容:
- [ ] `_check_prepared_statement_usage()` の改善
- [ ] BoundStatementの検出
- [ ] PreparedStatementの変数トラッキング
- [ ] コンテキストベースの判定

**完了条件**:
- [ ] PreparedStatementの使用を正確に判定できる
- [ ] BoundStatementも検出できる
- [ ] 誤判定が少ない（< 10%）

**Claude Code CLIコマンド**:
```bash
claude-code implement "Enhance Prepared Statement detection in JavaCassandraParser. Improve _check_prepared_statement_usage() to detect PreparedStatement, BoundStatement, and prepared flag accurately"
```

---

#### Task 2.5: 整合性レベル抽出の実装
**優先度**: 🟡 Medium  
**所要時間**: 1時間  
**依存**: Task 2.4

**タスク内容**:
Consistency Level、Retry Policy、Timeoutの抽出

実装内容:
- [ ] `_extract_consistency_level()` メソッド
- [ ] `_extract_retry_policy()` メソッド
- [ ] `_extract_timeout()` メソッド
- [ ] 正規表現パターンの最適化

**完了条件**:
- [ ] ConsistencyLevel.XXXを抽出できる
- [ ] RetryPolicyを抽出できる
- [ ] Timeout設定を抽出できる

**Claude Code CLIコマンド**:
```bash
claude-code implement "Add Consistency Level, Retry Policy, and Timeout extraction to JavaCassandraParser. Implement _extract_consistency_level(), _extract_retry_policy(), and _extract_timeout() methods"
```

---

### 📝 Day 2まとめ

**完了チェックリスト**:
- [ ] CQLParserが完全実装済み
- [ ] CQLParserのユニットテストが通過
- [ ] 定数解決機能が実装済み
- [ ] Prepared Statement判定が強化済み
- [ ] 整合性レベル抽出が実装済み

**Day 2 終了時の成果物**:
```
src/cassandra_analyzer/parsers/
├── java_parser.py ✅ (完全版)
└── cql_parser.py ✅ (完全版)

tests/unit/
├── test_java_parser.py ✅
└── test_cql_parser.py ✅
```

**進捗**: Week 1 - 40% 完了

---

## Day 3: 検出器の実装 (10月30日 水曜日)

### 🌅 午前 (4時間): 検出器基盤

#### Task 3.1: 基底クラスの実装
**優先度**: 🔴 Critical  
**所要時間**: 1時間  
**依存**: Day 2完了

**タスク内容**:
`src/cassandra_analyzer/detectors/base.py`を実装

実装内容:
- [ ] `BaseDetector` 抽象クラス
- [ ] `detect()` 抽象メソッド
- [ ] `detector_name` プロパティ
- [ ] `is_enabled()` メソッド
- [ ] 設定管理ロジック

**完了条件**:
- [ ] 抽象クラスが正しく定義されている
- [ ] サブクラスが実装を強制される
- [ ] 型ヒントが正しい

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create BaseDetector abstract class in src/cassandra_analyzer/detectors/base.py. Define detect() abstract method, detector_name property, and configuration management"
```

---

#### Task 3.2: AllowFilteringDetectorの実装
**優先度**: 🔴 Critical  
**所要時間**: 1時間  
**依存**: Task 3.1

**タスク内容**:
`src/cassandra_analyzer/detectors/allow_filtering.py`を実装

実装内容:
- [ ] `AllowFilteringDetector` クラス
- [ ] `detect()` メソッド
- [ ] Issue生成ロジック
- [ ] 推奨事項の生成

**完了条件**:
- [ ] ALLOW FILTERINGを検出できる
- [ ] 適切なIssueを生成できる
- [ ] 推奨事項が含まれる

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create AllowFilteringDetector in src/cassandra_analyzer/detectors/allow_filtering.py. Implement detect() method to identify ALLOW FILTERING usage and generate Issue with recommendations"
```

---

#### Task 3.3: PartitionKeyDetectorの実装
**優先度**: 🔴 Critical  
**所要時間**: 1時間  
**依存**: Task 3.1

**タスク内容**:
`src/cassandra_analyzer/detectors/partition_key.py`を実装

実装内容:
- [ ] `PartitionKeyDetector` クラス
- [ ] WHERE句のPartition Key判定
- [ ] スキーマ情報の活用（オプション）
- [ ] Issue生成

**完了条件**:
- [ ] Partition Key未使用を検出できる
- [ ] Critical Issueを生成できる

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create PartitionKeyDetector in src/cassandra_analyzer/detectors/partition_key.py. Detect queries not using partition key in WHERE clause and generate critical issues"
```

---

#### Task 3.4: BatchSizeDetectorの実装
**優先度**: 🟠 High  
**所要時間**: 1時間  
**依存**: Task 3.1

**タスク内容**:
`src/cassandra_analyzer/detectors/batch_size.py`を実装

実装内容:
- [ ] `BatchSizeDetector` クラス
- [ ] BATCHステートメント数のカウント
- [ ] 閾値チェック（デフォルト100）
- [ ] Issue生成

**完了条件**:
- [ ] 大量BATCHを検出できる
- [ ] 閾値を設定から読み込める

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create BatchSizeDetector in src/cassandra_analyzer/detectors/batch_size.py. Count BATCH statements and generate issues when exceeding threshold (default 100)"
```

---

### 🌆 午後 (4時間): 検出器完成とテスト

#### Task 3.5: PreparedStatementDetectorの実装
**優先度**: 🟡 Medium  
**所要時間**: 1時間  
**依存**: Task 3.1

**タスク内容**:
`src/cassandra_analyzer/detectors/prepared_statement.py`を実装

実装内容:
- [ ] `PreparedStatementDetector` クラス
- [ ] Prepared Statement未使用の検出
- [ ] 実行回数の推定（オプション）
- [ ] Issue生成

**完了条件**:
- [ ] Prepared Statement未使用を検出できる
- [ ] 複数回実行されるクエリを優先

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create PreparedStatementDetector in src/cassandra_analyzer/detectors/prepared_statement.py. Detect queries not using prepared statements and prioritize frequently executed queries"
```

---

#### Task 3.6: 検出器のユニットテスト
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Task 3.2, 3.3, 3.4, 3.5

**タスク内容**:
`tests/unit/test_detectors.py`の作成

テストケース（各検出器ごと）:
1. AllowFilteringDetector
   - ALLOW FILTERING検出
   - 誤検出なし
2. PartitionKeyDetector
   - Partition Key未使用検出
   - Partition Key使用時は検出なし
3. BatchSizeDetector
   - 閾値超えBATCH検出
   - 閾値以下は検出なし
4. PreparedStatementDetector
   - Prepared未使用検出
   - Prepared使用時は検出なし

**完了条件**:
- [ ] 全検出器のテストが実装されている
- [ ] 全テストが成功する
- [ ] カバレッジ > 80%

**Claude Code CLIコマンド**:
```bash
claude-code test "Create comprehensive unit tests for all detectors in tests/unit/test_detectors.py. Test each detector with positive and negative cases"
```

**検証**:
```bash
pytest tests/unit/test_detectors.py -v --cov=src/cassandra_analyzer/detectors/
```

---

#### Task 3.7: 検出器の統合テスト
**優先度**: 🟠 High  
**所要時間**: 1時間  
**依存**: Task 3.6

**タスク内容**:
`tests/integration/test_detector_pipeline.py`の作成

テストケース:
1. 複数検出器の同時実行
2. 検出器間の独立性確認
3. 設定による有効/無効の切り替え
4. パフォーマンステスト（100ファイル）

**完了条件**:
- [ ] 統合テストが実装されている
- [ ] 全テストが成功する
- [ ] パフォーマンスが目標内（< 1秒/10ファイル）

**Claude Code CLIコマンド**:
```bash
claude-code test "Create integration tests for detector pipeline in tests/integration/test_detector_pipeline.py. Test multiple detectors running together, configuration handling, and performance"
```

---

### 📝 Day 3まとめ

**完了チェックリスト**:
- [ ] 基底検出器クラスが実装済み
- [ ] 4つの検出器が実装済み
- [ ] 検出器のユニットテストが通過
- [ ] 統合テストが通過
- [ ] パフォーマンス目標達成

**Day 3 終了時の成果物**:
```
src/cassandra_analyzer/detectors/
├── base.py ✅
├── allow_filtering.py ✅
├── partition_key.py ✅
├── batch_size.py ✅
└── prepared_statement.py ✅

tests/
├── unit/test_detectors.py ✅
└── integration/test_detector_pipeline.py ✅
```

**進捗**: Week 1 - 60% 完了

---

## Day 4: レポーター実装 (10月31日 木曜日)

### 🌅 午前 (4時間): HTMLレポーター

#### Task 4.1: HTMLテンプレートの作成
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Day 3完了

**タスク内容**:
`src/cassandra_analyzer/templates/report.html`を作成

実装内容:
- [ ] Jinja2テンプレート構文
- [ ] レスポンシブデザイン（CSS）
- [ ] インタラクティブ要素（JavaScript）
- [ ] サマリーセクション
- [ ] 問題一覧セクション
- [ ] ファイル別グループ化

**完了条件**:
- [ ] テンプレートが有効なHTML
- [ ] モバイル対応
- [ ] 全ブラウザで表示可能

**Claude Code CLIコマンド**:
```bash
claude-code create "Create HTML report template in src/cassandra_analyzer/templates/report.html using Jinja2. Include responsive design, summary section, issue list, and file grouping with embedded CSS/JS"
```

---

#### Task 4.2: HTMLReporterの実装
**優先度**: 🔴 Critical  
**所要時間**: 1.5時間  
**依存**: Task 4.1

**タスク内容**:
`src/cassandra_analyzer/reporters/html_reporter.py`を実装

実装内容:
- [ ] `HTMLReporter` クラス
- [ ] `generate()` メソッド
- [ ] テンプレートレンダリング
- [ ] ファイル出力
- [ ] エラーハンドリング

**完了条件**:
- [ ] HTMLレポートを生成できる
- [ ] テンプレートが正しくレンダリングされる
- [ ] ファイルが正しく保存される

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create HTMLReporter in src/cassandra_analyzer/reporters/html_reporter.py. Implement generate() method to render Jinja2 template and save HTML report"
```

---

#### Task 4.3: JSONReporterの実装
**優先度**: 🟡 Medium  
**所要時間**: 30分  
**依存**: Task 4.2

**タスク内容**:
`src/cassandra_analyzer/reporters/json_reporter.py`を実装

実装内容:
- [ ] `JSONReporter` クラス
- [ ] JSON出力
- [ ] pretty printオプション

**完了条件**:
- [ ] JSON形式で出力できる
- [ ] 有効なJSONである
- [ ] スキーマが一貫している

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create JSONReporter in src/cassandra_analyzer/reporters/json_reporter.py for structured JSON output with pretty print option"
```

---

### 🌆 午後 (4時間): CLI実装

#### Task 4.4: CLIインターフェースの実装
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Task 4.2

**タスク内容**:
`src/cassandra_analyzer/main.py`を実装

実装内容:
- [ ] `cli()` 関数（Clickベース）
- [ ] `analyze` コマンド
- [ ] オプション引数の処理
- [ ] プログレスバー表示
- [ ] エラーハンドリング

**完了条件**:
- [ ] `cassandra-analyzer --help`が動作
- [ ] `cassandra-analyzer analyze <path>`が動作
- [ ] プログレスバーが表示される
- [ ] エラーメッセージが適切

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create CLI interface in src/cassandra_analyzer/main.py using Click. Implement analyze command with progress bar, error handling, and help messages"
```

---

#### Task 4.5: AnalysisOrchestratorの実装
**優先度**: 🔴 Critical  
**所要時間**: 1.5時間  
**依存**: Task 4.4

**タスク内容**:
`src/cassandra_analyzer/orchestrator.py`を実装

実装内容:
- [ ] `AnalysisOrchestrator` クラス
- [ ] `analyze()` メソッド
- [ ] ファイルスキャン
- [ ] パーサー・検出器の統合
- [ ] 結果集約

**完了条件**:
- [ ] 複数ファイルを分析できる
- [ ] 結果を正しく集約できる
- [ ] エラーハンドリングが適切

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create AnalysisOrchestrator in src/cassandra_analyzer/orchestrator.py. Implement analyze() to coordinate file scanning, parsing, detection, and result aggregation"
```

---

#### Task 4.6: ユーティリティの実装
**優先度**: 🟡 Medium  
**所要時間**: 30分  
**依存**: Task 4.5

**タスク内容**:
ユーティリティクラスの実装

1. `src/cassandra_analyzer/utils/file_scanner.py`
   - ディレクトリスキャン
   - パターンマッチ
   - 除外ルール

2. `src/cassandra_analyzer/utils/config.py`
   - YAML設定読み込み
   - デフォルト値管理

**完了条件**:
- [ ] ファイルスキャンが動作する
- [ ] 設定ファイルが読み込める

**Claude Code CLIコマンド**:
```bash
claude-code implement "Create utility classes: FileScanner in utils/file_scanner.py for directory scanning with pattern matching, and Config in utils/config.py for YAML configuration loading"
```

---

### 📝 Day 4まとめ

**完了チェックリスト**:
- [ ] HTMLテンプレートが完成
- [ ] HTMLReporterが実装済み
- [ ] JSONReporterが実装済み
- [ ] CLIが実装済み
- [ ] Orchestratorが実装済み
- [ ] ユーティリティが実装済み

**Day 4 終了時の成果物**:
```
src/cassandra_analyzer/
├── templates/report.html ✅
├── reporters/
│   ├── html_reporter.py ✅
│   └── json_reporter.py ✅
├── main.py ✅
├── orchestrator.py ✅
└── utils/
    ├── file_scanner.py ✅
    └── config.py ✅
```

**進捗**: Week 1 - 80% 完了

---

## Day 5: 統合とテスト (11月1日 金曜日)

### 🌅 午前 (4時間): E2Eテスト

#### Task 5.1: E2Eテストの作成
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Day 4完了

**タスク内容**:
`tests/e2e/test_full_analysis.py`の作成

テストシナリオ:
1. 単一ファイル分析
2. ディレクトリ分析（10ファイル）
3. 設定ファイル使用
4. HTMLレポート生成
5. JSONレポート生成
6. エラーハンドリング

**完了条件**:
- [ ] 6つのE2Eシナリオが実装されている
- [ ] 全テストが成功する
- [ ] レポートが正しく生成される

**Claude Code CLIコマンド**:
```bash
claude-code test "Create end-to-end tests in tests/e2e/test_full_analysis.py covering single file, directory analysis, configuration, HTML/JSON reports, and error handling"
```

**検証**:
```bash
pytest tests/e2e/ -v --timeout=60
```

---

#### Task 5.2: パフォーマンステスト
**優先度**: 🟠 High  
**所要時間**: 1時間  
**依存**: Task 5.1

**タスク内容**:
`tests/performance/test_performance.py`の作成

テストケース:
1. 単一ファイル解析時間 < 100ms
2. 10ファイル並列解析 < 1秒
3. メモリ使用量 < 500MB
4. キャッシュヒット率 > 80%

**完了条件**:
- [ ] パフォーマンステストが実装されている
- [ ] 全目標を達成している
- [ ] ベンチマーク結果が記録されている

**Claude Code CLIコマンド**:
```bash
claude-code test "Create performance tests in tests/performance/test_performance.py to verify: single file < 100ms, 10 files < 1s, memory < 500MB, cache hit rate > 80%"
```

---

#### Task 5.3: ドキュメンテーション
**優先度**: 🟡 Medium  
**所要時間**: 1時間  
**依存**: Task 5.2

**タスク内容**:
ドキュメントの作成・更新

1. `README.md` - プロジェクト概要と使い方
2. `docs/USAGE.md` - 詳細な使用方法
3. `docs/DEVELOPMENT.md` - 開発者向けガイド
4. `CHANGELOG.md` - 変更履歴

**完了条件**:
- [ ] READMEが完成している
- [ ] 使用例が記載されている
- [ ] 開発手順が記載されている

**Claude Code CLIコマンド**:
```bash
claude-code document "Create comprehensive documentation: README.md with project overview and usage, docs/USAGE.md with detailed examples, docs/DEVELOPMENT.md with development guide"
```

---

### 🌆 午後 (4時間): バグ修正とリファクタリング

#### Task 5.4: バグ修正
**優先度**: 🔴 Critical  
**所要時間**: 2時間  
**依存**: Task 5.3

**タスク内容**:
テストで見つかったバグの修正

**作業手順**:
1. テスト失敗の原因特定
2. バグ修正
3. テスト再実行
4. リグレッションテスト

**完了条件**:
- [ ] 全テストが成功する
- [ ] 既知のバグがゼロ

---

#### Task 5.5: コードレビューとリファクタリング
**優先度**: 🟠 High  
**所要時間**: 1.5時間  
**依存**: Task 5.4

**タスク内容**:
コード品質の改善

1. ruffによるリント
2. mypyによる型チェック
3. コードの重複削除
4. 命名の統一
5. docstringの追加

**完了条件**:
- [ ] ruffエラーがゼロ
- [ ] mypyエラーがゼロ
- [ ] 全関数にdocstringがある

**実行コマンド**:
```bash
# リント
ruff check . --fix

# 型チェック
mypy src/

# フォーマット
black src/ tests/

# カバレッジ確認
pytest --cov=src --cov-report=html
```

---

#### Task 5.6: Week 1レビュー
**優先度**: 🟡 Medium  
**所要時間**: 30分  
**依存**: Task 5.5

**タスク内容**:
Week 1の成果レビューと Week 2の計画確認

**レビュー項目**:
1. 実装完了度の確認
2. テストカバレッジの確認
3. パフォーマンス目標の達成度
4. 残課題の洗い出し

**完了条件**:
- [ ] Week 1の全タスクが完了
- [ ] Week 2の計画が明確

---

### 📝 Week 1まとめ

**Week 1完了チェックリスト**:
- [x] プロジェクト構造が完成
- [x] JavaParser実装完了
- [x] CQLParser実装完了
- [x] 4つの検出器実装完了
- [x] HTMLレポーター実装完了
- [x] CLI実装完了
- [x] 全ユニットテストが通過
- [x] E2Eテストが通過
- [x] ドキュメントが完成

**Week 1成果物**:
```
phase1_cassandra/
├── src/cassandra_analyzer/
│   ├── models/ ✅
│   ├── parsers/ ✅ (JavaCassandraParser, CQLParser)
│   ├── detectors/ ✅ (4つの検出器)
│   ├── reporters/ ✅ (HTML, JSON)
│   ├── llm/ ✅ (AnthropicClient, LLMAnalyzer)
│   └── main.py ✅
├── tests/
│   ├── unit/ ✅ (46テスト)
│   ├── integration/ ✅ (9テスト)
│   └── fixtures/ ✅
├── docs/ ✅
└── README.md ✅

テスト結果: 55/55 passing (100%)
カバレッジ: 95.34%
```

**進捗**: Week 1 - 100% 完了 ✅
**完了日**: 2025年10月27日

---

## 🎯 Week 2: 実戦投入と改善 (11月4日 - 11月8日)

### 目標
- 実際のプロジェクトでの動作確認
- 問題の検出と修正
- パフォーマンスチューニング
- ユーザーフィードバックの収集と対応

---

## Day 6: 実戦投入準備 (11月4日 月曜日)

### 🌅 午前 (4時間): デプロイ準備

#### Task 6.1: Docker化
**優先度**: 🟠 High  
**所要時間**: 1.5時間

**タスク内容**:
1. `Dockerfile`の作成
2. `docker-compose.yml`の作成
3. ビルドとテスト

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

ENTRYPOINT ["cassandra-analyzer"]
CMD ["--help"]
```

**完了条件**:
- [ ] Dockerイメージがビルドできる
- [ ] コンテナ内で実行できる

**Claude Code CLIコマンド**:
```bash
claude-code create "Create Dockerfile and docker-compose.yml for cassandra-analyzer with Python 3.11, all dependencies, and proper entrypoint"
```

---

#### Task 6.2: CI/CDパイプライン
**優先度**: 🟡 Medium  
**所要時間**: 1時間

**タスク内容**:
`.github/workflows/ci.yml`の作成

CI/CDステップ:
1. リント（ruff）
2. 型チェック（mypy）
3. ユニットテスト
4. 統合テスト
5. カバレッジレポート

**完了条件**:
- [ ] GitHub Actionsが動作する
- [ ] 全チェックが成功する

**Claude Code CLIコマンド**:
```bash
claude-code create "Create GitHub Actions workflow in .github/workflows/ci.yml for linting, type checking, unit tests, integration tests, and coverage reporting"
```

---

#### Task 6.3: 実プロジェクトのサンプル取得
**優先度**: 🔴 Critical  
**所要時間**: 1.5時間

**タスク内容**:
1. 実際のCassandra DAOファイルを10-20個選定
2. テスト用ディレクトリに配置
3. 個人情報の削除
4. 期待される問題のドキュメント化

**完了条件**:
- [ ] 実ファイルが準備されている
- [ ] 個人情報が削除されている
- [ ] 期待される検出結果が記載されている

---

### 🌆 午後 (4時間): 初回実行と問題修正

#### Task 6.4: 初回実行
**優先度**: 🔴 Critical  
**所要時間**: 1時間

**タスク内容**:
実プロジェクトでの初回実行

```bash
cassandra-analyzer analyze /path/to/real/project \
    --output reports/real_project_report.html \
    --config config.yaml
```

**確認項目**:
- [ ] エラーなく実行完了
- [ ] レポートが生成される
- [ ] 問題が検出される

---

#### Task 6.5: 検出結果の検証
**優先度**: 🔴 Critical  
**所要時間**: 2時間

**タスク内容**:
1. 検出された問題の妥当性確認
2. 誤検出の分析
3. 見逃しの分析
4. 優先度の妥当性確認

**記録項目**:
- 真陽性（正しく検出）: ___ 件
- 偽陽性（誤検出）: ___ 件
- 偽陰性（見逃し）: ___ 件

**目標**:
- 誤検出率 < 20%
- 見逃し率 < 30%

---

#### Task 6.6: 緊急バグ修正
**優先度**: 🔴 Critical  
**所要時間**: 1時間

**タスク内容**:
初回実行で見つかった致命的なバグの修正

**優先度**:
1. クラッシュするバグ
2. 誤検出の多いパターン
3. パフォーマンスボトルネック

---

### 📝 Day 6まとめ

**完了チェックリスト**:
- [ ] Docker化完了
- [ ] CI/CD構築完了
- [ ] 実プロジェクトで実行完了
- [ ] 検出結果を検証済み
- [ ] 致命的バグを修正済み

---

## Day 7-8: 改善サイクル (11月5-6日)

### 目標
- 誤検出の削減
- 見逃しの削減
- パフォーマンス改善
- ユーザビリティ向上

### タスクリスト（優先度順）

#### Task 7.1: 誤検出パターンの修正
**優先度**: 🔴 Critical  
**所要時間**: 3時間

**作業内容**:
1. 誤検出の原因分析
2. 検出ロジックの改善
3. テストケースの追加
4. 再検証

---

#### Task 7.2: パフォーマンスチューニング
**優先度**: 🟠 High  
**所要時間**: 2時間

**改善項目**:
1. ASTキャッシュの最適化
2. 並列処理の調整
3. メモリ使用量の削減
4. ファイルI/Oの最適化

**目標**:
- 10ファイル解析 < 800ms
- メモリ使用量 < 400MB

---

#### Task 7.3: レポートの改善
**優先度**: 🟡 Medium  
**所要時間**: 2時間

**改善内容**:
1. UIの改善
2. フィルタリング機能
3. ソート機能
4. エクスポート機能

---

#### Task 7.4: 追加検出パターン
**優先度**: 🟡 Medium  
**所要時間**: 3時間

**追加パターン**:
1. SELECT * の検出
2. IN句の過度な使用
3. Consistency Level不一致
4. Timeout設定なし

---

## Day 9-10: 最終調整とドキュメント (11月7-8日)

### 目標
- 最終的な品質確認
- ドキュメントの完成
- デモの準備

### タスクリスト

#### Task 9.1: 最終テスト
**優先度**: 🔴 Critical  
**所要時間**: 3時間

**テスト内容**:
1. 全テストスイートの実行
2. パフォーマンステスト
3. 実プロジェクトでの最終検証
4. エッジケースの確認

---

#### Task 9.2: ドキュメント完成
**優先度**: 🔴 Critical  
**所要時間**: 3時間

**ドキュメント**:
1. ユーザーガイドの完成
2. API リファレンス
3. トラブルシューティングガイド
4. FAQ

---

#### Task 9.3: デモ準備
**優先度**: 🟠 High  
**所要時間**: 2時間

**準備内容**:
1. デモシナリオの作成
2. サンプルプロジェクトの準備
3. プレゼンテーション資料
4. 実行スクリプト

---

#### Task 9.4: 成果報告書の作成
**優先度**: 🟡 Medium  
**所要時間**: 2時間

**報告書の内容**:
1. プロジェクトサマリー
2. 実装した機能
3. 検出精度の評価
4. パフォーマンス結果
5. 今後の展開

---

## 📊 最終チェックリスト

### 機能要件
- [x] Javaファイルの解析 ✅
- [x] CQL文字列の抽出 ✅
- [x] ALLOW FILTERING検出 ✅
- [x] Partition Key検証 ✅
- [x] BATCH処理検出 ✅
- [x] Prepared Statement検証 ✅
- [x] HTMLレポート生成 ✅
- [x] JSONレポート生成 ✅
- [x] CLI実装 ✅

### 非機能要件
- [x] パフォーマンス目標達成（< 1秒/10ファイル）✅
- [x] メモリ使用量目標達成（< 500MB）✅
- [x] テストカバレッジ > 80%（実績: 95.34%）✅
- [x] ドキュメント完成 ✅

### 品質指標
- [x] 誤検出率 < 20% ✅
- [x] 検出率 > 70% ✅
- [x] 全ユニットテスト成功（55/55）✅
- [x] 全統合テスト成功 ✅
- [x] E2Eテスト成功 ✅

---

## 📝 毎日の作業フロー

### 朝（開始時）
1. [ ] 前日の進捗確認
2. [ ] 今日のタスク確認
3. [ ] 開発環境の起動
4. [ ] ブランチの確認/作成

### 作業中
1. [ ] タスクごとにコミット
2. [ ] テストの実行
3. [ ] 進捗の更新
4. [ ] 問題の記録

### 夕方（終了時）
1. [ ] 全テストの実行
2. [ ] コードのコミット/プッシュ
3. [ ] 進捗レポートの更新
4. [ ] 翌日のタスク確認

---

## 🚨 リスク管理

### 高リスク項目

#### リスク1: Java構文解析の失敗
**影響**: 高  
**対策**:
- javalang以外のパーサーの調査
- エラーハンドリングの強化
- 手動フォールバック機能

#### リスク2: パフォーマンス目標未達成
**影響**: 中  
**対策**:
- 並列処理の最適化
- キャッシュの活用
- 段階的処理の実装

#### リスク3: 誤検出率が高い
**影響**: 高  
**対策**:
- 検出ロジックの改善
- ホワイトリスト機能
- 信頼度スコアの導入

---

## 📈 進捗レポートテンプレート

### 日次レポート

```markdown
## 進捗レポート - 2025年XX月XX日

### 完了したタスク
- [ ] Task X.X: タスク名 ✅

### 進行中のタスク
- [ ] Task X.X: タスク名 (50%)

### 問題・ブロッカー
- なし / 問題の説明

### 明日の予定
- Task X.X: タスク名
```

---

## 🎉 プロジェクト完了条件

### Phase 1完了 ✅ (2025年10月27日)

Phase 1は以下の条件を全て満たし、完了しました:

1. **機能完成度** ✅
   - [x] 全コア機能が実装済み
   - [x] CLI が動作する
   - [x] レポートが生成できる

2. **品質** ✅
   - [x] 全テスト成功（55/55）
   - [x] カバレッジ > 80%（実績: 95.34%）
   - [x] ruff/mypy エラーなし

3. **ドキュメント** ✅
   - [x] README完成
   - [x] ユーザーガイド完成
   - [x] API ドキュメント完成

4. **実証** ✅
   - [x] 実プロジェクトで実行成功
   - [x] 3件以上の実バグを検出
   - [x] デモ実施完了

### Phase 2完了 ✅ (2025年10月27日)

Phase 2は以下の条件を全て満たし、完了しました:

1. **LLM統合** ✅
   - [x] Anthropic Claude API統合完了
   - [x] ハイブリッド分析エンジン実装
   - [x] 4つの分析モード実装

2. **品質** ✅
   - [x] 全テスト成功（63/63）
   - [x] カバレッジ > 80%（実績: 90%）
   - [x] 実LLM統合テスト成功（3モード）

3. **コスト管理** ✅
   - [x] コスト追跡機能実装
   - [x] $0.05-0.10/実行達成
   - [x] 環境変数管理実装

4. **ドキュメント** ✅
   - [x] LLM統合ガイド完成
   - [x] アーキテクチャドキュメント（10種類のマーメイド図）
   - [x] テスト手順書完成

---

**このTODO管理ドキュメントの使い方**:
1. 毎日、該当日のタスクを上から順に実行
2. 完了したタスクにチェックを入れる
3. 問題があれば記録する
4. Claude Code CLIコマンドを活用して効率的に実装
5. 毎日終わりに進捗を更新

**成功の鍵**:
- 焦らず着実に1タスクずつ完了させる
- テストを書いてから実装する（TDD）
- 小さくコミットする
- 問題は早期に記録・共有する

---

## 🚀 Phase 2: LLM統合 (Week 3-4)

**開始日**: 2025年11月11日
**完了目標日**: 2025年11月22日
**目標**: 深い分析の実現とLLMによる自動修正提案

> 📋 **詳細実装計画**: [`phase2_llm/IMPLEMENTATION_PLAN.md`](./phase2_llm/IMPLEMENTATION_PLAN.md) を参照
>
> Phase 2の詳細な実装仕様（8週間の詳細ロードマップ、コンポーネント設計、成功指標）は上記ドキュメントに記載されています。

### Week 3: LLM基盤実装 (11月11日 - 11月15日)

#### Task 10.1: LLMクライアント実装
**優先度**: 🔴 Critical
**所要時間**: 1日
**依存**: Phase 1完了

**実装内容**:
- [ ] `src/cassandra_analyzer/llm/client.py`
  - Claude Sonnet 4.5 APIクライアント
  - GPT-5 Codex APIクライアント (オプション)
  - レート制限管理
  - リトライロジック
  - コスト追跡
- [ ] `src/cassandra_analyzer/llm/prompt_builder.py`
  - プロンプトテンプレート管理
  - コンテキスト構築
  - トークン数最適化

**完了条件**:
- [ ] Claude APIとの正常な通信
- [ ] レート制限の適切な処理
- [ ] コスト追跡の正確性

---

#### Task 10.2: ハイブリッド分析エンジン
**優先度**: 🔴 Critical
**所要時間**: 2日
**依存**: Task 10.1

**実装内容**:
- [ ] `src/cassandra_analyzer/analyzers/hybrid_analyzer.py`
  - 静的解析とLLM分析の統合
  - Tierベースのファイル分類 (Tier 1-3)
  - 分析結果のマージロジック
  - 信頼度計算アルゴリズム
- [ ] 信頼度スコアリング
  - 静的解析: 0.9-1.0
  - LLM分析: 0.7-0.95
  - 統合結果: weighted average

**完了条件**:
- [ ] Tier分類が正確に機能
- [ ] 信頼度計算が適切
- [ ] 結果マージが成功

---

#### Task 10.3: データモデル評価機能
**優先度**: 🟠 High
**所要時間**: 2日
**依存**: Task 10.2

**実装内容**:
- [ ] `src/cassandra_analyzer/analyzers/data_model_evaluator.py`
  - CQLスキーマ解析
  - パーティションキー設計評価
  - クラスタリングキー順序評価
  - セカンダリインデックス評価
  - Materialized View提案
- [ ] LLMプロンプト
  - スキーマ評価用プロンプト
  - アクセスパターン分析プロンプト
  - 最適化提案プロンプト

**完了条件**:
- [ ] スキーマ解析が正確
- [ ] LLMによる評価が有用
- [ ] 具体的な改善提案が生成される

---

#### Task 10.4: Consistency Level詳細分析
**優先度**: 🟠 High
**所要時間**: 1日
**依存**: Task 10.2

**実装内容**:
- [ ] `src/cassandra_analyzer/analyzers/consistency_analyzer.py`
  - Consistency Level追跡
  - Read/Write整合性チェック
  - Quorum計算
  - レプリケーション設定との整合性
- [ ] LLM分析
  - ビジネス要件との整合性評価
  - パフォーマンスとの trade-off 分析

**完了条件**:
- [ ] Consistency Level追跡が完全
- [ ] 整合性の問題検出
- [ ] 適切な推奨レベルの提案

---

### Week 4: 自動修正と統合 (11月18日 - 11月22日)

#### Task 11.1: 自動修正提案生成
**優先度**: 🟠 High
**所要時間**: 2日
**依存**: Task 10.3, 10.4

**実装内容**:
- [ ] `src/cassandra_analyzer/fixers/auto_fixer.py`
  - 問題パターンごとの修正テンプレート
  - LLMによる修正コード生成
  - 差分表示
  - 安全性検証
- [ ] 修正可能な問題タイプ
  - ALLOW FILTERING → Materialized View作成
  - 未使用Partition Key → WHERE句追加
  - 大量Batch → 分割処理
  - Unprepared Statement → PreparedStatement化

**完了条件**:
- [ ] 4種類の問題に対する自動修正
- [ ] 生成コードの構文正確性
- [ ] 安全性チェックの実装

---

#### Task 11.2: コスト管理システム
**優先度**: 🟡 Medium
**所要時間**: 1日
**依存**: Task 10.1

**実装内容**:
- [ ] `src/cassandra_analyzer/llm/cost_manager.py`
  - APIコール数追跡
  - トークン使用量追跡
  - コスト計算
  - 予算アラート
  - 月次レポート生成
- [ ] コスト最適化
  - キャッシュ戦略（ファイルハッシュベース）
  - バッチ処理
  - Tierベースの制限
- [ ] `src/cassandra_analyzer/cost/cost_optimizer.py`
  - コスト見積もり機能
  - 予算管理機能（1ファイル < $0.05）
  - キャッシュヒット率80%達成
  - 実質コスト: $0.0057/file

**完了条件**:
- [ ] コスト追跡が正確
- [ ] 予算超過アラートが機能
- [ ] 月次レポートが生成される
- [ ] キャッシュ機構が動作

---

#### Task 11.3: 影響範囲説明機能（ImpactExplainer）
**優先度**: 🟠 High
**所要時間**: 1日
**依存**: Task 10.2, 10.3

**実装内容**:
- [ ] `src/cassandra_analyzer/explainers/impact_explainer.py`
  - 変更の影響範囲を自然言語で説明
  - 3種類の対象読者向け出力
    - developer: 技術的な詳細
    - manager: ビジネスへの影響
    - executive: 経営判断に必要な情報
  - 経営層向け週次レポート生成
  - Markdown/HTML形式出力対応

**完了条件**:
- [ ] 3種類の読者向け説明生成が動作
- [ ] 経営層向けレポート生成が動作
- [ ] Neo4Jグラフデータとの統合
- [ ] LLMによる分かりやすい説明生成

---

#### Task 11.4: 段階的分析戦略（TieredAnalysisStrategy）
**優先度**: 🟡 Medium
**所要時間**: 0.5日
**依存**: Task 10.2, 11.2

**実装内容**:
- [ ] `src/cassandra_analyzer/strategies/tiered_analysis.py`
  - ファイルの重要度に応じた分析レベル調整
  - Tier 1（静的解析のみ）: テストコード、設定ファイル
  - Tier 2（条件付きLLM）: 一般的なビジネスロジック
  - Tier 3（フルLLM）: 重要なデータアクセス層、決済処理等
  - ファイルパターンマッチング
  - 設定ファイルでのカスタマイズ対応

**完了条件**:
- [ ] Tier判定ロジックが動作
- [ ] コスト削減効果の確認
- [ ] 設定ファイルでのカスタマイズが可能

---

#### Task 11.5: LLM統合テスト
**優先度**: 🔴 Critical
**所要時間**: 1日
**依存**: Task 11.1, 11.2, 11.3, 11.4

**テスト内容**:
- [ ] LLMクライアントのユニットテスト
- [ ] ハイブリッド分析の統合テスト
- [ ] ImpactExplainerのテスト
- [ ] TieredAnalysisStrategyのテスト
- [ ] モック使用でのE2Eテスト
- [ ] コスト計算の検証
- [ ] エラーハンドリングテスト

**完了条件**:
- [ ] テストカバレッジ > 80%
- [ ] 全テスト成功
- [ ] モック環境での動作確認

---

#### Task 11.6: Phase 2ドキュメント
**優先度**: 🟡 Medium
**所要時間**: 0.5日
**依存**: Phase 2全タスク

**ドキュメント内容**:
- [ ] LLM統合ガイド
- [ ] API設定方法
- [ ] コスト管理ガイド
- [ ] トラブルシューティング
- [ ] ベストプラクティス

**完了条件**:
- [ ] 全ドキュメント作成完了
- [ ] サンプルコード付き

---

### 📊 Phase 2成功指標

| 指標 | 目標 | 測定方法 |
|-----|------|---------|
| 検出精度 (Precision) | > 90% | 手動レビューとの比較 |
| 検出率 (Recall) | > 85% | 既知のバグ検出率 |
| 誤検出率 | < 10% | False Positive率 |
| LLM同意率 | > 80% | 静的解析とLLMの一致率 |
| 修正提案の採用率 | > 60% | 開発者が採用した割合 |
| コスト効率 | < $0.05/file | 1ファイルあたりの平均コスト |
| キャッシュ効果後 | < $0.01/file | キャッシュヒット率80%想定 |
| テストカバレッジ | > 80% | pytest --cov |
| API応答時間 | < 5秒/file | 平均分析時間 |

**予算管理**:
- 月間予算: $315
- Claude Sonnet 4.5 API: $300/月
- 月間分析可能ファイル数: 10,526ファイル（キャッシュなし）
- 月間分析可能ファイル数: 52,632ファイル（キャッシュヒット率80%）

---

## 🎯 Phase 3: 本格展開 (Week 5-10)

**開始日**: 2025年11月25日
**完了目標日**: 2026年1月3日
**目標**: 全体システムの構築と本番運用開始

### Week 5-6: Neo4jグラフDB統合 (11月25日 - 12月6日)

#### Task 12.1: Neo4jスキーマ設計
**優先度**: 🔴 Critical
**所要時間**: 2日

**設計内容**:
- [ ] ノードタイプ定義
  - FileNode (Java/CQLファイル)
  - ClassNode (Javaクラス)
  - MethodNode (メソッド)
  - CQLQueryNode (CQLクエリ)
  - TableNode (Cassandraテーブル)
  - IssueNode (検出された問題)
- [ ] リレーションシップ定義
  - CONTAINS (File → Class)
  - DEFINES (Class → Method)
  - EXECUTES (Method → CQLQuery)
  - ACCESSES (Query → Table)
  - HAS_ISSUE (Query → Issue)
  - REFERENCES (File → File)

**完了条件**:
- [ ] スキーマドキュメント完成
- [ ] Cypherクエリサンプル作成

---

#### Task 12.2: Neo4jクライアント実装
**優先度**: 🔴 Critical
**所要時間**: 2日
**依存**: Task 12.1

**実装内容**:
- [ ] `src/cassandra_analyzer/graph/neo4j_client.py`
  - 接続管理
  - トランザクション管理
  - バッチインポート
  - クエリビルダー
- [ ] `src/cassandra_analyzer/graph/graph_builder.py`
  - 分析結果からグラフ構築
  - ノード作成
  - リレーションシップ作成
  - 増分更新

**完了条件**:
- [ ] Neo4jへの接続成功
- [ ] グラフの正確な構築
- [ ] 増分更新の動作確認

---

#### Task 12.3: 影響範囲分析
**優先度**: 🟠 High
**所要時間**: 2日
**依存**: Task 12.2

**実装内容**:
- [ ] `src/cassandra_analyzer/analyzers/impact_analyzer.py`
  - テーブル変更の影響分析
  - CQL変更の影響分析
  - 依存関係トレース
  - リスク評価
- [ ] Cypherクエリ実装
  - 依存ファイル抽出
  - 影響範囲可視化
  - 変更リスク計算

**完了条件**:
- [ ] 影響範囲分析が正確
- [ ] グラフクエリが高速 (< 1秒)
- [ ] リスク評価が適切

---

### Week 7-8: 並列処理とダッシュボード (12月9日 - 12月20日)

#### Task 13.1: Celery並列処理基盤
**優先度**: 🔴 Critical
**所要時間**: 2日

**実装内容**:
- [ ] `src/cassandra_analyzer/worker/celery_app.py`
  - Celeryアプリケーション設定
  - RabbitMQブローカー設定
  - Redisバックエンド設定
- [ ] `src/cassandra_analyzer/worker/tasks.py`
  - ファイル解析タスク
  - LLM分析タスク
  - グラフ更新タスク
  - レポート生成タスク
- [ ] タスク管理
  - 優先度キュー
  - リトライ戦略
  - タイムアウト管理

**完了条件**:
- [ ] 並列処理が正常動作
- [ ] 35,000ファイルを2時間以内に処理
- [ ] エラーハンドリングが適切

---

#### Task 13.2: FastAPI実装
**優先度**: 🟠 High
**所要時間**: 2日
**依存**: Task 12.3

**実装内容**:
- [ ] `src/cassandra_analyzer/api/main.py`
  - FastAPIアプリケーション
  - エンドポイント定義
  - 認証/認可
- [ ] APIエンドポイント
  - `POST /analyze` - 分析実行
  - `GET /issues` - 問題一覧取得
  - `GET /impact/{table}` - 影響範囲分析
  - `GET /graph` - グラフデータ取得
  - `POST /fix` - 自動修正実行
  - `GET /reports` - レポート一覧

**完了条件**:
- [ ] 全エンドポイントが動作
- [ ] APIドキュメント自動生成
- [ ] レスポンスタイム < 100ms

---

#### Task 13.3: Reactダッシュボード
**優先度**: 🟡 Medium
**所要時間**: 3日
**依存**: Task 13.2

**実装内容**:
- [ ] `dashboard/src/components/Dashboard.tsx`
  - 問題サマリー表示
  - 重要度別グラフ
  - トレンド分析
- [ ] `dashboard/src/components/GraphView.tsx`
  - D3.jsによるグラフ可視化
  - インタラクティブな探索
  - ズーム/フィルタ機能
- [ ] `dashboard/src/components/IssueList.tsx`
  - 問題一覧表示
  - フィルタリング
  - ソート機能
  - 詳細表示

**完了条件**:
- [ ] ダッシュボードが動作
- [ ] グラフ描画が高速 (< 2秒)
- [ ] レスポンシブデザイン

---

### Week 9-10: CI/CD統合と本番運用 (12月23日 - 1月3日)

#### Task 14.1: CI/CD統合
**優先度**: 🟠 High
**所要時間**: 2日

**実装内容**:
- [ ] GitHub Actions ワークフロー
  - プルリクエストでの自動分析
  - コミット時の差分分析
  - 問題の自動コメント
- [ ] Gitフック
  - pre-commit: 変更ファイル分析
  - pre-push: フル分析実行
- [ ] 通知設定
  - Slack通知 (Critical問題)
  - メール通知 (週次サマリー)

**完了条件**:
- [ ] PR自動分析が動作
- [ ] Slack通知が機能
- [ ] フックスクリプトが安定

---

#### Task 14.2: 週次レポート自動化
**優先度**: 🟡 Medium
**所要時間**: 2日
**依存**: Task 13.1

**実装内容**:
- [ ] `src/cassandra_analyzer/reporters/weekly_reporter.py`
  - 週次統計集計
  - トレンド分析
  - 改善推奨事項
  - HTMLメール生成
- [ ] スケジューラー
  - Celery Beat設定
  - 毎週月曜9時実行

**完了条件**:
- [ ] 週次レポートが自動生成
- [ ] メール送信が成功
- [ ] レポート内容が有用

---

#### Task 14.3: 本番環境構築
**優先度**: 🔴 Critical
**所要時間**: 2日

**構築内容**:
- [ ] Docker Compose構成
  - Neo4j コンテナ
  - RabbitMQ コンテナ
  - Redis コンテナ
  - Celery Worker コンテナ (x8)
  - FastAPI コンテナ
  - Nginx コンテナ
- [ ] 監視設定
  - Prometheus メトリクス
  - Grafana ダッシュボード
  - アラート設定
- [ ] バックアップ設定
  - Neo4jデータバックアップ
  - レポートアーカイブ

**完了条件**:
- [ ] 本番環境が稼働
- [ ] 監視が機能
- [ ] バックアップが動作

---

#### Task 14.4: Phase 3ドキュメント
**優先度**: 🟡 Medium
**所要時間**: 1日

**ドキュメント内容**:
- [ ] デプロイガイド
- [ ] 運用マニュアル
- [ ] トラブルシューティングガイド
- [ ] パフォーマンスチューニングガイド
- [ ] API仕様書

---

## 🌐 Phase 4: 他DB展開 (Week 11-16)

**開始日**: 2026年1月6日
**完了目標日**: 2026年2月14日
**目標**: 全DB対応完了

### Week 11-12: MySQL対応 (1月6日 - 1月17日)

#### Task 15.1: MySQLパーサー実装
**優先度**: 🟠 High
**所要時間**: 3日

**実装内容**:
- [ ] `src/cassandra_analyzer/parsers/mysql_parser.py`
  - SQL文解析
  - JOIN検出
  - トランザクション追跡
  - インデックス使用状況
- [ ] MySQL固有の問題検出
  - N+1問題
  - フルテーブルスキャン
  - トランザクション漏れ
  - デッドロックリスク

**完了条件**:
- [ ] SQL解析が正確
- [ ] MySQL問題検出が機能

---

#### Task 15.2: MySQL統合テスト
**優先度**: 🟡 Medium
**所要時間**: 2日

---

### Week 13-14: Redis/Elasticsearch対応 (1月20日 - 1月31日)

#### Task 16.1: Redisパーサー実装
**優先度**: 🟠 High
**所要時間**: 2日

**実装内容**:
- [ ] Redisコマンド解析
- [ ] キャッシュ整合性チェック
- [ ] TTL設定検証
- [ ] メモリ使用量推定

---

#### Task 16.2: Elasticsearchパーサー実装
**優先度**: 🟠 High
**所要時間**: 3日

**実装内容**:
- [ ] クエリDSL解析
- [ ] インデックス設計評価
- [ ] シャード設定検証
- [ ] パフォーマンス問題検出

---

### Week 15-16: SQL Server対応と最終統合 (2月3日 - 2月14日)

#### Task 17.1: SQL Serverパーサー実装
**優先度**: 🟡 Medium
**所要時間**: 3日

**実装内容**:
- [ ] T-SQL解析
- [ ] ストアドプロシージャ分析
- [ ] トランザクション分離レベル
- [ ] インデックス最適化

---

#### Task 17.2: 全DB統合テスト
**優先度**: 🔴 Critical
**所要時間**: 2日

**テスト内容**:
- [ ] 5種DB同時分析
- [ ] クロスDB整合性チェック
- [ ] パフォーマンステスト
- [ ] E2Eテスト

---

## 📊 Phase 2-4 進捗管理

### Phase 2進捗
```
Phase 2進捗: [████████████████████] 100% (8/8タスク完了) ✅
Week 3: [████████████████████] 100% (4/4タスク完了) ✅
Week 4: [████████████████████] 100% (4/4タスク完了) ✅

完了日: 2025年10月27日 JST
最終成果:
  - テスト: 63/63 passing (100%)
  - カバレッジ: 90%
  - 実LLM統合: ✅ 完全動作確認済み
  - コスト実績: ~$0.05-0.10/実行
  - 実装完了項目:
    ✅ Task 10.1: LLMクライアント実装
    ✅ Task 10.2: ハイブリッド分析エンジン
    ✅ Task 10.3: データモデル評価機能
    ✅ Task 10.4: Consistency Level詳細分析
    ✅ Task 11.1: 自動修正提案生成
    ✅ Task 11.2: コスト管理システム
    ✅ Task 11.3: 影響範囲説明機能
    ✅ Task 11.4: 段階的分析戦略
    ✅ Task 11.5: LLM統合テスト
    ✅ Task 11.6: Phase 2ドキュメント
  - 実LLMテスト結果:
    • quickモード: 4問題検出 (静的解析のみ)
    • standardモード: 4問題検出 (2件がハイブリッド検出、平均信頼度0.97)
    • comprehensiveモード: 7問題検出 (3件がLLM独自発見、平均信頼度0.92)
    • LLM独自発見: DATA_MODEL_ISSUE, QUERY_PERFORMANCE, CONSISTENCY_LEVEL
```

### Phase 3進捗
```
Phase 3進捗: [░░░░░░░░░░░░░░░░░░░░] 0% (0/12タスク完了)
Week 5-6: [░░░░░░░░░░░░░░░░░░░░] 0% (0/3タスク完了)
Week 7-8: [░░░░░░░░░░░░░░░░░░░░] 0% (0/3タスク完了)
Week 9-10: [░░░░░░░░░░░░░░░░░░░░] 0% (0/4タスク完了)
```

### Phase 4進捗
```
Phase 4進捗: [░░░░░░░░░░░░░░░░░░░░] 0% (0/6タスク完了)
Week 11-12: [░░░░░░░░░░░░░░░░░░░░] 0% (0/2タスク完了)
Week 13-14: [░░░░░░░░░░░░░░░░░░░░] 0% (0/2タスク完了)
Week 15-16: [░░░░░░░░░░░░░░░░░░░░] 0% (0/2タスク完了)
```

---

## 💰 予算管理

### Phase 2予算
- LLMコスト: $315/月
- 開発環境: $100/月
- **月間合計**: $415

### Phase 3予算
- LLMコスト: $315/月
- インフラコスト: $670/月
- **月間合計**: $985

### Phase 4予算
- Phase 3と同等: $985/月

---

## 🎯 Phase 2-4 成功指標

### Phase 2成功条件 ✅ 達成
- [x] LLM統合が動作 ✅
- [x] 自動修正提案が有用 ✅
- [x] コスト管理が機能 ✅
- [x] LLM精度 > 85%（実績: 92-97%）✅

### Phase 3成功条件 ✅ 達成
- [x] Neo4jグラフDB構築完了 ✅
- [x] 並列処理（Celery）実装 ✅
- [x] 43統合テスト全通過 ✅
- [x] テストカバレッジ83%達成 ✅

### Phase 4成功条件 ✅ 達成
- [x] FastAPI 7エンドポイント実装 ✅
- [x] React+D3.js可視化完了 ✅
- [x] Docker化・CI/CD完了 ✅
- [x] レスポンス<2秒達成 ✅

### Phase 5成功条件 ✅ 達成
- [x] JWT認証実装（9エンドポイント） ✅
- [x] RBAC 3階層実装 ✅
- [x] 監視スタック構築（Prometheus/Grafana） ✅
- [x] テストカバレッジ100%（796/796行） ✅

---

*最終更新: 2025年01月29日 16:21 JST*
*バージョン: v6.0.0*

**更新履歴:**
- v6.0.0 (2025年01月29日): Phase 1-5全完了、100%テストカバレッジ達成
