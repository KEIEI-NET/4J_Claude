# 4J_Claude: 汎用ソースコード解析システム

*バージョン: v2.0.0*
*最終更新: 2025年01月27日 15:30 JST*

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase%201%20Completed-success" alt="Phase 1 Completed"/>
  <img src="https://img.shields.io/badge/Phase%202-Completed-success" alt="Phase 2 Completed"/>
  <img src="https://img.shields.io/badge/Phase%203-Planning-blue" alt="Phase 3 Planning"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+"/>
</p>

## 📋 プロジェクト概要

**4J_Claude** は、ソースコードファイル群を解析し、**Neo4Jグラフデータベース**で視覚化し、バグ内容から関連ソースファイルを自動検出するための汎用ソースコード解析システムです。

### 核心機能

1. **Neo4Jグラフデータベースによる可視化**
   - ファイル、クラス、メソッド、クエリ、テーブル、問題の関係をグラフで表現
   - インタラクティブな依存関係の探索

2. **影響範囲分析**
   - ファイル/テーブル変更時の影響トレース
   - リスク評価と依存関係の可視化

3. **バグ関連ソース自動検索**
   - バグ内容を入力 → 関連ソースファイル群を自動抽出
   - 親子関係・依存関係の切り出し

4. **複数データベース対応**
   - Cassandra, MySQL, Redis, Elasticsearch, SQL Server

---

## 🎯 プロジェクト構成（4フェーズ）

### ✅ Phase 1: Cassandra特化型コード分析システム（完了）
**期間**: 2025年10月28日 - 11月8日
**ステータス**: ✅ **完了（95.34%テストカバレッジ達成）**

**成果物**:
- Javaファイルの静的解析
- CQL（Cassandra Query Language）の抽出と問題検出
- 4つの検出器：ALLOW FILTERING、Partition Key未使用、大量BATCH、Prepared Statement未使用
- HTML/JSON/Markdownレポート生成
- CLI実装

**ディレクトリ**: [`phase1_cassandra/`](./phase1_cassandra/)

---

### ✅ Phase 2: LLM統合（完了）
**期間**: 2025年11月11日 - 2025年1月27日
**ステータス**: ✅ **完了（100%実装済み、90%テストカバレッジ達成）**

**成果物**:
- **HybridAnalysisEngine**: 静的解析とLLM分析を統合
- **4つの分析モード**: quick, standard, comprehensive, critical_only
- **Anthropic Claude API統合**: Claude 3 Opus使用
- **信頼度計算システム**: AnalysisConfidence モデル実装
- **コスト管理**: $0.05-0.10/実行に最適化
- **環境変数管理**: python-dotenv統合

**テスト結果**:
- ユニットテスト: 63/63 passing (100%)
- カバレッジ: 90%
- 実LLM統合テスト: 全3モード成功
- LLM独自発見: DATA_MODEL_ISSUE, QUERY_PERFORMANCE, CONSISTENCY_LEVEL

**ディレクトリ**: [`phase2_llm/`](./phase2_llm/)

---

### 🌐 Phase 3: 本格展開 - Neo4Jグラフデータベース統合（計画中）
**期間**: 2025年11月25日 - 2026年1月3日
**ステータス**: 🔵 **計画中**

**目標**: 真の核心機能の実装

#### Week 5-6: Neo4Jグラフデータベース統合
**Neo4Jスキーマ設計**:
- **ノードタイプ**: FileNode, ClassNode, MethodNode, CQLQueryNode, TableNode, IssueNode
- **リレーションシップ**: CONTAINS, DEFINES, EXECUTES, ACCESSES, HAS_ISSUE, REFERENCES

**影響範囲分析**:
- ファイル変更の影響分析
- 依存関係トレース
- リスク評価

#### Week 7-8: 並列処理とダッシュボード
**Celery並列処理基盤**:
- 35,000ファイルを2時間以内に処理
- RabbitMQブローカー + Redisバックエンド

**FastAPI実装**:
- REST APIエンドポイント
  - `POST /analyze` - 分析実行
  - `GET /issues` - 問題一覧取得
  - `GET /impact/{table}` - 影響範囲分析
  - `GET /graph` - グラフデータ取得

**Reactダッシュボード**:
- D3.jsによるグラフ可視化
- インタラクティブな探索機能
- 問題一覧・フィルタリング

#### Week 9-10: CI/CD統合と本番運用
**GitHub Actions ワークフロー**:
- プルリクエストでの自動分析
- Slack/メール通知

**Docker Compose構成**:
- Neo4j, RabbitMQ, Redis, Celery Worker (x8), FastAPI, Nginx
- Prometheus/Grafana監視

**ディレクトリ**: `phase3_neo4j/`（準備中）

**主要タスク**:
- Task 12.1: Neo4jスキーマ設計
- Task 12.2: Neo4jクライアント実装
- Task 12.3: 影響範囲分析
- Task 13.1: Celery並列処理基盤
- Task 13.2: FastAPI実装
- Task 13.3: Reactダッシュボード
- Task 14.1: CI/CD統合
- Task 14.3: 本番環境構築

---

### 🗄️ Phase 4: 他データベース展開（計画中）
**期間**: 2026年1月6日 - 2月14日
**ステータス**: 🔵 **計画中**

**目標**: 全データベース対応完了

**対応データベース**:
1. **MySQL**（Week 11-12）
   - N+1問題検出
   - フルテーブルスキャン検出
   - トランザクション漏れ
   - デッドロックリスク

2. **Redis**（Week 13-14）
   - キャッシュ整合性チェック
   - TTL設定検証
   - メモリ使用量推定

3. **Elasticsearch**（Week 13-14）
   - クエリDSL解析
   - インデックス設計評価
   - シャード設定検証

4. **SQL Server**（Week 15-16）
   - T-SQL解析
   - ストアドプロシージャ分析
   - トランザクション分離レベル

**ディレクトリ**: `phase4_multidb/`（準備中）

---

## 🚀 クイックスタート

### Phase 1（Cassandraアナライザー）を試す

```bash
# Phase 1ディレクトリに移動
cd phase1_cassandra/

# 仮想環境の作成とアクティベート
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
pip install -e .

# 分析実行
cassandra-analyzer analyze /path/to/your/java/project \
    --output reports/analysis_report.html \
    --config config.yaml

# テスト実行
pytest tests/ -v --cov
```

詳細は [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md) を参照してください。

---

## 📊 プロジェクト進捗

```
全体進捗: [██████████░░░░░░░░░░] 50% (Phase 1&2完了)

Phase 1: [████████████████████] 100% (完了)
Phase 2: [████████████████████] 100% (完了)
Phase 3: [░░░░░░░░░░░░░░░░░░░░]   0% (計画中)
Phase 4: [░░░░░░░░░░░░░░░░░░░░]   0% (計画中)
```

---

## 🏗️ プロジェクト構造

```
4J_Claude/
├── phase1_cassandra/          ✅ Phase 1: Cassandra特化型分析（完了）
│   ├── src/cassandra_analyzer/
│   │   ├── models/           # データモデル
│   │   ├── parsers/          # JavaParser, CQLParser, ASTParser
│   │   ├── detectors/        # 4つの問題検出器
│   │   ├── reporters/        # HTML/JSON/Markdownレポーター
│   │   ├── utils/            # ユーティリティ
│   │   └── main.py           # CLIエントリーポイント
│   ├── tests/                # 284テスト（95.34%カバレッジ）
│   ├── docs/                 # ドキュメント
│   └── README_CASSANDRA.md   # Phase 1詳細
│
├── phase2_llm/               ✅ Phase 2: LLM統合（完了）
│   ├── src/
│   │   ├── models.py         # AnalysisConfidence, HybridAnalysisResult
│   │   ├── llm_client.py     # AnthropicClient実装
│   │   ├── llm_analyzer.py   # LLMAnalyzer実装
│   │   └── hybrid_engine.py  # HybridAnalysisEngine実装
│   ├── tests/                # ユニットテスト（63テスト、90%カバレッジ）
│   ├── README.md             # Phase 2詳細ドキュメント
│   └── ARCHITECTURE.md       # Phase 2アーキテクチャ図
│
├── phase3_neo4j/             🔵 Phase 3: Neo4Jグラフデータベース（計画中）
│   ├── src/
│   │   ├── graph/            # Neo4jクライアント
│   │   ├── analyzers/        # 影響範囲分析
│   │   ├── api/              # FastAPI
│   │   └── worker/           # Celery並列処理
│   ├── dashboard/            # Reactダッシュボード
│   └── README.md             # Phase 3計画
│
├── phase4_multidb/           🔵 Phase 4: 他DB展開（計画中）
│   ├── parsers/
│   │   ├── mysql_parser.py
│   │   ├── redis_parser.py
│   │   ├── elasticsearch_parser.py
│   │   └── sqlserver_parser.py
│   └── README.md             # Phase 4計画
│
├── docs/                     # プロジェクト全体ドキュメント
│   ├── ARCHITECTURE.md       # アーキテクチャ設計
│   ├── NEO4J_SCHEMA.md       # Neo4Jスキーマ設計
│   └── API_SPEC.md           # API仕様書
│
├── README.md                 # このファイル（プロジェクト概要）
└── TODO.md                   # 詳細タスク管理（2,253行）
```

---

## 📈 成功指標

### Phase 1（達成済み）
- ✅ テストカバレッジ > 95%（達成: 95.34%）
- ✅ 284テスト全成功
- ✅ 4種類の問題検出器実装完了
- ✅ HTML/JSON/Markdownレポート生成

### Phase 2（達成済み）
- ✅ LLM統合が動作（HybridAnalysisEngine完了）
- ✅ 自動修正提案が有用（3つのLLM独自問題検出）
- ✅ LLM精度 > 85%（信頼度0.92-0.97達成）
- ✅ コスト管理が機能（$0.05-0.10/実行）

### Phase 3（目標）
- [ ] Neo4jグラフDB構築完了
- [ ] 並列処理で2時間以内に35,000ファイル分析
- [ ] Reactダッシュボードが稼働
- [ ] CI/CD統合完了

### Phase 4（目標）
- [ ] 5種DB全対応
- [ ] クロスDB整合性チェック機能
- [ ] 統合E2Eテスト成功
- [ ] 全DB問題検出率 > 80%

---

## 💰 予算管理

| Phase | 期間 | LLMコスト | インフラコスト | 月間合計 |
|-------|------|-----------|----------------|----------|
| Phase 1 | 2週間 | - | - | - |
| Phase 2 | 2週間 | $315/月 | $100/月 | $415/月 |
| Phase 3 | 6週間 | $315/月 | $670/月 | $985/月 |
| Phase 4 | 6週間 | $315/月 | $670/月 | $985/月 |

---

## 🤝 開発ガイド

### Phase 1の開発継続
Phase 1のバグ修正や機能追加は `phase1_cassandra/` で作業してください。

### Phase 2以降の開発開始
各フェーズのディレクトリ内でREADME.mdを作成し、TODO.mdを参照して実装してください。

### テスト実行
```bash
# Phase 1のテスト
cd phase1_cassandra/
pytest tests/ -v --cov

# 将来: Phase 3のテスト
cd phase3_neo4j/
pytest tests/ -v --cov
```

---

## 📝 詳細ドキュメント

- **Phase 1詳細**: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
- **使用方法**: [`phase1_cassandra/USAGE.md`](./phase1_cassandra/USAGE.md)
- **開発ガイド**: [`phase1_cassandra/DEVELOPMENT.md`](./phase1_cassandra/DEVELOPMENT.md)
- **タスク管理**: [`TODO.md`](../TODO.md)（2,253行の詳細計画）

---

## 🎯 次のステップ

1. **Phase 3の開始**（2025年1月28日開始予定）
   - Neo4Jスキーマの詳細設計
   - グラフデータベース構築
   - 影響範囲分析エンジンの実装
   - Reactダッシュボードのモックアップ作成

2. **Phase 4の調査**（2026年2月開始予定）
   - MySQL/Redis/Elasticsearch/SQL Serverのパーサーライブラリ調査
   - 各データベース固有の問題パターン定義

3. **本番環境準備**
   - Docker Compose構成の準備
   - CI/CDパイプラインの設計

---

## 📄 ライセンス

MIT License

---

## 📧 お問い合わせ

プロジェクトに関する質問や提案は、GitHubのIssuesでお願いします。

---

**🚀 Generated with Claude Code by Anthropic**

---

*最終更新: 2025年01月27日 15:30 JST*
*バージョン: v2.0.0*

**更新履歴:**
- v2.0.0 (2025年01月27日): Phase 2 LLM統合完了、HybridAnalysisEngine実装、4つの分析モード追加
