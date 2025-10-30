# CLAUDE.md

*バージョン: v6.0.0*
*最終更新: 2025年01月29日 16:21 JST*

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

本プロジェクトは **マルチフェーズ静的コード分析システム** であり、データベース特化の問題検出から始まり、LLM統合、グラフDB、マルチDB対応へと進化する包括的な分析プラットフォームです。

**現在の状態**:
- Phase 1 (Cassandra分析): ✅ 完了
- Phase 2 (LLM統合): ✅ 完了
- Phase 3 (Neo4j統合): ✅ 完了
- Phase 4 (可視化・影響分析): ✅ 完了
- Phase 5 (認証・監視): ✅ 完了

**技術スタック**: Python 3.11+、Claude API、Neo4j、React/TypeScript
**主な対象**: Java/Python/TypeScript/Go/C#コードベース

## プロジェクト構造

### 最新のディレクトリ構造（2025年01月27日更新）

```
C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\
├── phase1_cassandra/          # Cassandra特化分析（完了）
│   ├── src/
│   │   └── cassandra_analyzer/
│   │       ├── parsers/       # Java/CQL解析
│   │       ├── detectors/     # 問題検出
│   │       ├── models/        # データモデル
│   │       ├── reporters/     # レポート生成
│   │       └── utils/         # ユーティリティ
│   ├── tests/
│   ├── docs/
│   └── README_CASSANDRA.md
├── phase2_llm/                # LLM統合分析（完了）
│   ├── src/
│   │   └── llm_analyzer/
│   │       ├── llm/           # Claude API統合
│   │       ├── semantic/      # 意味論的分析
│   │       └── augmentation/  # 分析強化
│   ├── tests/
│   └── README_LLM.md
├── phase3_neo4j/              # グラフDB分析（完了）
│   ├── src/
│   │   └── graph_analyzer/
│   │       ├── graph/         # Neo4j統合
│   │       ├── traversal/     # グラフ走査
│   │       └── visualization/ # 可視化
│   ├── tests/
│   └── README_NEO4J.md
├── phase4_visualization/      # 可視化・認証・監視（完了）
│   ├── backend/
│   │   ├── api/              # 16 APIエンドポイント
│   │   ├── auth/             # JWT認証・RBAC
│   │   ├── repositories/     # ユーザーデータ管理
│   │   ├── neo4j_client/     # グラフDB接続
│   │   └── tests/            # 149テスト（100%カバレッジ）
│   ├── frontend/
│   │   ├── src/components/   # React + D3.js
│   │   ├── src/api/          # Axios + 認証
│   │   └── src/stores/       # Zustand状態管理
│   ├── monitoring/           # Prometheus/Grafana
│   └── docker-compose.yml    # Docker構成
├── .env                       # 環境変数（Claude API等）
├── .gitignore                 # Git除外設定
├── README.md                  # 統合プロジェクト概要
├── TODO.md                    # 全体タスク管理
├── CHANGELOG.md               # 変更履歴
├── CLAUDE.md                  # このファイル
├── DETAILED_DESIGN.md         # 詳細設計（87KB）
├── IMPLEMENTATION_SPEC.md     # 実装仕様（35KB）
├── integrated_architecture.md  # 統合アーキテクチャ
└── その他仕様書...
```

### 重要な構造変更（2025年01月27日）

**cassandra-analyzerフォルダーは削除されました**。各フェーズは独立したプロジェクトとしてルート直下に配置されています。

## 各フェーズの概要

### Phase 1: Cassandra特化分析（完了）

**パス**: `./phase1_cassandra/`

**コアコンポーネント**:
- **JavaCassandraParser** (`phase1_cassandra/src/cassandra_analyzer/parsers/java_parser.py`)
- **CQLParser** (`phase1_cassandra/src/cassandra_analyzer/parsers/cql_parser.py`)
- **検出器** (`phase1_cassandra/src/cassandra_analyzer/detectors/`)
  - AllowFilteringDetector
  - PartitionKeyDetector
  - BatchSizeDetector
  - PreparedStatementDetector
- **レポーター** (`phase1_cassandra/src/cassandra_analyzer/reporters/`)

**成果**:
- ✅ 95%のテストカバレッジ達成
- ✅ 10個のサンプルDAOファイルで検証完了
- ✅ HTML/JSONレポート生成機能実装

### Phase 2: LLM統合分析（完了）

**パス**: `./phase2_llm/`

**主要機能**:
- Claude Sonnet 3.5による深い意味論的分析
- コンテキスト理解に基づく問題検出
- 自動修正提案生成
- バッチ処理とレート制限対応

**統合状況**:
- ✅ Claude API統合完了
- ✅ 意味論的分析エンジン実装
- ✅ 自動修正提案システム構築

### Phase 3: Neo4j グラフ分析（完了）

**パス**: `./phase3_neo4j/`

**実装機能**:
- ✅ コード依存関係のグラフ化（GraphBuilder）
- ✅ 影響範囲分析エンジン
- ✅ 循環依存検出アルゴリズム
- ✅ Celery並列処理タスク
- ✅ 43統合テスト全通過

### Phase 4: 可視化・影響分析（完了）

**パス**: `./phase4_visualization/`

**実装機能**:
- ✅ FastAPI バックエンド（7エンドポイント）
- ✅ React + TypeScript + D3.js フロントエンド
- ✅ グラフ可視化（ノード、エッジ、影響範囲）
- ✅ ファイル検索とフィルタリング
- ✅ Docker化とCI/CDパイプライン

### Phase 5: 認証・監視システム（完了）

**パス**: `./phase4_visualization/` （Phase 4と統合）

**実装機能**:
- ✅ JWT Bearer Token認証（HS256）
- ✅ RBAC（Admin/Developer/Viewer）
- ✅ ユーザー管理API（9エンドポイント）
- ✅ Prometheus + Grafana監視
- ✅ Loki + AlertManager通知

## 主要技術スタック

### 共通基盤
- **言語**: Python 3.11+
- **テスト**: pytest、pytest-cov
- **型チェック**: mypy
- **リント**: ruff
- **フォーマット**: black

### Phase別技術
- **Phase 1**: javalang（Java AST解析）、Jinja2、Click、Rich
- **Phase 2**: Anthropic Claude API、LangChain
- **Phase 3**: Neo4j、py2neo、NetworkX、Celery、Redis
- **Phase 4**: FastAPI、React、TypeScript、D3.js、Vite、Zustand
- **Phase 5**: JWT (python-jose)、bcrypt、Prometheus、Grafana、Loki

## 開発ワークフロー

### 環境セットアップ

```bash
# プロジェクトルートで実行
cd "C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude"

# 仮想環境の作成
python -m venv venv
venv\Scripts\activate  # Windows

# Phase 1の依存関係インストール
cd phase1_cassandra
pip install -r requirements.txt
pip install -e .

# Phase 2の依存関係（LLM統合）
cd ../phase2_llm
pip install -r requirements.txt

# 環境変数の設定（.envファイルはルートに配置）
# ANTHROPIC_API_KEY=your-api-key
```

### テストの実行

```bash
# Phase 1のテスト
cd phase1_cassandra
pytest tests/ -v --cov=src/cassandra_analyzer

# Phase 2のテスト
cd ../phase2_llm
pytest tests/ -v

# 統合テスト（ルートから）
python -m pytest phase1_cassandra/tests/integration/
```

### アナライザーの実行

```bash
# Phase 1: Cassandra分析
cd phase1_cassandra
python -m cassandra_analyzer analyze /path/to/java/code

# Phase 2: LLM拡張分析
cd ../phase2_llm
python -m llm_analyzer analyze /path/to/code --llm-enabled

# 設定ファイル使用
cassandra-analyzer analyze /path/to/code --config ../config.yaml
```

## 重要な実装詳細

### AST解析戦略（Phase 1）

JavaCassandraParserは**javalang**を使用：
- `MethodInvocation`ノードを検索
- Cassandraセッションメソッドを識別
- CQL文字列を抽出（リテラルと定数対応）

### LLM統合アプローチ（Phase 2）

- **コンテキスト構築**: 周辺コードを含めた分析
- **プロンプトエンジニアリング**: 構造化された問題検出
- **レート制限対応**: 指数バックオフとリトライ
- **コスト最適化**: バッチ処理とキャッシング

### グラフDB設計（Phase 3）

```cypher
// ノード例
(:Class {name, package, file_path})
(:Method {name, signature, class_id})
(:Database {type, name})
(:Query {cql, type})

// リレーション例
(:Method)-[:CALLS]->(:Method)
(:Method)-[:EXECUTES]->(:Query)
(:Query)-[:ACCESSES]->(:Database)
```

## パフォーマンス目標

| フェーズ | 指標 | 目標値 |
|---------|------|--------|
| Phase 1 | 単一ファイル分析 | < 100ms | ✅ 達成 |
| Phase 1 | 10ファイル並列 | < 1秒 | ✅ 達成 |
| Phase 2 | LLM分析/ファイル | < 2秒 | ✅ 達成 |
| Phase 3 | グラフ構築（1000ノード） | < 5秒 | ✅ 達成 |
| Phase 4 | API レスポンスタイム | < 2秒 | ✅ 達成 |
| Phase 5 | 認証処理時間 | < 100ms | ✅ 達成 |

## コード品質基準

- すべての関数に型ヒント必須 ✅
- 公開APIにdocstring必須 ✅
- テストカバレッジ > 80% ✅ (Phase 4/5: 100%達成)
- mypyエラー 0 ✅
- ruffエラー 0 ✅
- PEP 8準拠（black使用） ✅

## エラーハンドリング哲学

- **グレースフルデグラデーション**: 部分的な失敗を許容
- **詳細なログ**: コンテキスト付きエラー情報
- **ユーザーフレンドリー**: 実行可能な解決策を提示
- **リカバリー戦略**: 自動リトライとフォールバック

## ドキュメント構成

| ドキュメント | 内容 | サイズ |
|------------|------|-------|
| README.md | プロジェクト概要 | 8KB |
| DETAILED_DESIGN.md | 技術アーキテクチャ | 87KB |
| IMPLEMENTATION_SPEC.md | 実装ガイド | 35KB |
| TODO.md | タスク管理 | 65KB |
| integrated_architecture.md | 統合設計 | 12KB |

## 今後の展開

### 完了済み（2025 Q1）
- ✅ Phase 1-5 全フェーズ完了
- ✅ 100%テストカバレッジ達成
- ✅ 認証・監視システム実装
- ✅ Docker化・CI/CD完備

### 短期目標（2025 Q2）
- Phase 6: マルチデータベース対応
  - MySQL/PostgreSQL統合
  - MongoDB/Redis統合
  - Elasticsearch統合
- パフォーマンス最適化（サブ秒レスポンス）

### 中期目標（2025 Q3-Q4）
- エンタープライズ機能強化
  - SAML/OAuth2.0統合
  - マルチテナント対応
  - 監査ログ強化
- AI機能拡張
  - GPT-4統合オプション
  - 自動修正提案の実装

### 長期ビジョン（2025 Q4以降）
- エンタープライズ版の開発
- SaaS展開の検討
- コミュニティ版の公開

## 開発上の注意事項

### パス参照の統一

- **絶対パス例**: `C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase1_cassandra\`
- **相対パス例**: `./phase1_cassandra/src/`
- **インポート例**: `from cassandra_analyzer.parsers import JavaParser`

### 環境変数管理

`.env`ファイルはプロジェクトルートに配置：
```
ANTHROPIC_API_KEY=sk-xxx
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Git管理

```bash
# .gitignoreで除外
.env
*.pyc
__pycache__/
venv/
.pytest_cache/
htmlcov/
*.egg-info/
```

## トラブルシューティング

### よくある問題と解決策

1. **インポートエラー**
   - 各フェーズディレクトリで `pip install -e .` を実行
   - PYTHONPATHに各フェーズのsrcを追加

2. **LLM API エラー**
   - .envファイルのAPI キーを確認
   - レート制限を確認（待機後リトライ）

3. **Neo4j接続エラー**
   - Neo4jサービスが起動しているか確認
   - 認証情報を.envで設定

## 貢献ガイドライン

1. フィーチャーブランチで開発
2. テストカバレッジ80%以上を維持
3. PRテンプレートに従って記述
4. コードレビューを経てマージ

---

*最終更新: 2025年01月29日 16:21 JST*
*バージョン: v6.0.0*

**更新履歴:**
- v6.0.0 (2025年01月29日): Phase 4/5完全実装完了、認証・監視システム統合、100%テストカバレッジ達成
- v5.0.0 (2025年01月28日): Phase 5認証・監視システム実装
- v4.0.0 (2025年01月27日): Phase 4可視化システム完了
- v3.0.0 (2025年01月27日): Phase 3 Neo4j統合完了
- v2.1.0 (2025年01月27日): プロジェクト構造の大幅変更（cassandra-analyzerフォルダー削除、各フェーズをルート直下に配置）
- v2.0.0 (2025年01月26日): Phase 2完了、統合アーキテクチャ確定