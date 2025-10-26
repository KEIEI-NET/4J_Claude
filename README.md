# 4J_Claude: 汎用ソースコード解析システム

*バージョン: v4.0.1*
*最終更新: 2025年10月27日 08:07 JST*

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase%201%20Completed-success" alt="Phase 1 Completed"/>
  <img src="https://img.shields.io/badge/Phase%202-Completed-success" alt="Phase 2 Completed"/>
  <img src="https://img.shields.io/badge/Phase%203-Completed-success" alt="Phase 3 Completed"/>
  <img src="https://img.shields.io/badge/Phase%204-87.5%25-yellow" alt="Phase 4 In Progress"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/Coverage-83%25-brightgreen" alt="Test Coverage 83%"/>
</p>

## 📋 プロジェクト概要

**4J_Claude** は、ソースコードファイル群を解析し、**Neo4Jグラフデータベース**で視覚化し、バグ内容から関連ソースファイルを自動検出するための汎用ソースコード解析システムです。

### 核心機能

1. **静的コード解析** - データベース関連のアンチパターンと問題を検出
2. **LLM統合** - Claude APIを使用した高度な意味論的分析
3. **Neo4Jグラフ可視化** - コード構造と依存関係の視覚的表現（Phase 3）
4. **影響範囲分析** - 変更の影響をトレースして可視化（Phase 3）
5. **マルチDB対応** - Cassandra, MySQL, Redis, Elasticsearch, SQL Server（Phase 4）

---

## 🎯 プロジェクト構成（4フェーズ）

### ✅ Phase 1: Cassandra特化型コード分析システム（完了）
Javaコード内のCassandraクエリを静的解析し、パフォーマンス問題を早期検出するシステム。284のテストで95.34%のカバレッジを達成。

**詳細ドキュメント**: 📖 [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)

### ✅ Phase 2: LLM統合（完了）
Anthropic Claude APIを統合し、静的解析では検出困難な問題を発見。4つの分析モード（quick, standard, comprehensive, critical_only）を提供。

**詳細ドキュメント**: 📖 [`phase2_llm/README.md`](./phase2_llm/README.md)

### ✅ Phase 3: Neo4Jグラフデータベース統合（完了）
コード構造をグラフDBで可視化し、影響範囲分析を実現。GraphBuilder、Neo4jClient、Celery並列処理タスクを実装し、統合テスト43件全通過。

**詳細ドキュメント**: 📖 [`phase3_neo4j/README.md`](./phase3_neo4j/README.md)
**主要成果**:
- GraphBuilderによる分析結果のグラフ変換（100%カバレッジ）
- Neo4jClientによるデータベース操作（98%カバレッジ）
- Celery並列処理タスク実装（97%カバレッジ）
- 統合テスト43件全通過
- テストカバレッジ: 66% → 83% (+17%向上)

### 🚧 Phase 4: 可視化と影響分析（Week 7-8 進行中 - 87.5%）
Neo4jグラフデータを活用したインタラクティブな可視化システム。React + D3.jsによるWebダッシュボードと、FastAPIによる高速分析APIを実装。

**詳細ドキュメント**: 📖 [`phase4_visualization/README.md`](./phase4_visualization/README.md)
**Week 7-8成果（統合作業）**:
- ✅ 環境変数管理システム実装（Vite + pydantic-settings）
- ✅ セキュアなCORS設定（開発/本番環境分離）
- ✅ API統合テストスクリプト作成
- ✅ FastAPI影響範囲分析API（<2秒レスポンス）
- ✅ React + TypeScript + D3.js実装（67ユニットテスト、18 E2Eテスト）
- ⏳ Docker化とCI/CDパイプライン構築（残タスク）

---

## 🚀 クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude

# Phase 1 & 2の基本使用
cd phase1_cassandra/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Cassandra分析実行（静的解析のみ）
cassandra-analyzer analyze /path/to/java/project --output report.html

# LLM統合分析（Phase 2機能）
cassandra-analyzer analyze /path/to/java/project \
    --enable-llm \
    --api-key $ANTHROPIC_API_KEY \
    --mode comprehensive
```

**詳細な使用方法**:
- Phase 1機能: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
- Phase 2機能: [`phase2_llm/README.md`](./phase2_llm/README.md)

---

## 📊 プロジェクト進捗

```
全体進捗: [████████████████████] 97% (Phase 1-3完了, Phase 4 87.5%)

Phase 1: [████████████████████] 100% ✅ 静的解析
Phase 2: [████████████████████] 100% ✅ LLM統合
Phase 3: [████████████████████] 100% ✅ Neo4j/Celery
Phase 4: [████████████████▓░░░]  87.5% 🚧 Week 7-8 統合中
```

### Phase 4 進捗詳細（Week 7-8）
- **Week 1-2**: ✅ バックエンドAPI実装（100%完了）
- **Week 3-4**: ✅ フロントエンド基盤構築（100%完了）
- **Week 5-6**: ✅ コア機能実装（100%完了）
- **Week 7-8**: 🚧 統合作業（50%完了 - 5/10タスク）

---

## 🏗️ プロジェクト構造

```
4j-claude/
├── phase1_cassandra/         ✅ Cassandra特化型分析（完了）
├── phase2_llm/               ✅ LLM統合（完了）
├── phase3_neo4j/             ✅ グラフDB統合（完了）
│   ├── src/graph_analyzer/
│   │   ├── graph/           # Neo4j接続とグラフ構築
│   │   ├── impact/          # 影響範囲分析
│   │   └── tasks/           # Celery並列処理
│   └── tests/               # 43統合テスト
├── phase4_visualization/    🚧 可視化システム（Week 7-8）
│   ├── backend/             # FastAPI バックエンド
│   │   ├── api/            # REST APIエンドポイント
│   │   ├── config/         # 環境変数設定（pydantic-settings）
│   │   └── services/       # ビジネスロジック
│   ├── frontend/           # React フロントエンド
│   │   ├── src/
│   │   │   ├── components/ # React + D3.jsコンポーネント
│   │   │   ├── api/        # Axios APIクライアント
│   │   │   └── stores/     # Zustand状態管理
│   │   └── .env.*         # Vite環境変数
│   └── scripts/           # 統合テストスクリプト
├── README.md               # プロジェクト概要（このファイル）
└── TODO.md                 # タスク管理
```

**詳細な構造は各フェーズのREADMEを参照**:
- [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md#ディレクトリ構造)
- [`phase2_llm/README.md`](./phase2_llm/README.md#ディレクトリ構造)
- [`phase3_neo4j/README.md`](./phase3_neo4j/README.md#ディレクトリ構造予定)
- [`phase4_multidb/README.md`](./phase4_multidb/README.md#ディレクトリ構造予定)

---

## 📈 成功指標

| Phase | ステータス | 主要指標 |
|-------|-----------|----------|
| **Phase 1** | ✅ 完了 | テストカバレッジ 95.34%、284テスト成功 |
| **Phase 2** | ✅ 完了 | LLM精度 92-97%、コスト $0.05-0.10/実行 |
| **Phase 3** | ✅ 完了 | カバレッジ 83%、統合テスト43件、GraphBuilder 100%、Neo4jClient 98%、Celeryタスク 97% |
| **Phase 4** | 🚧 87.5% | Vitestテスト67件、Playwrightテスト18件、API応答<2秒、環境変数管理実装 |

---

## 📚 ドキュメント構造

### プロジェクト全体
- **このREADME** - プロジェクト概要とナビゲーション
- [`TODO.md`](./TODO.md) - 全フェーズの詳細タスク管理
- [`DETAILED_DESIGN.md`](./DETAILED_DESIGN.md) - 技術アーキテクチャ詳細
- [`IMPLEMENTATION_SPEC.md`](./IMPLEMENTATION_SPEC.md) - 実装仕様

### 各フェーズ詳細
- **Phase 1**: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
  - Cassandra分析の詳細仕様、使用方法、テスト結果
- **Phase 2**: [`phase2_llm/README.md`](./phase2_llm/README.md)
  - LLM統合の実装詳細、4つの分析モード、コスト管理
- **Phase 3**: [`phase3_neo4j/README.md`](./phase3_neo4j/README.md)
  - Neo4J統合計画、スキーマ設計、並列処理アーキテクチャ
- **Phase 4**: [`phase4_multidb/README.md`](./phase4_multidb/README.md)
  - マルチDB対応計画、各DB固有の検出パターン

---

## 🎯 次のステップ（Phase 4 Week 8 残タスク）

**Week 8 完了予定**: 2025年11月3日 JST

### 即座に実施予定
1. 🔜 E2Eテスト実行（Neo4j実データ使用）
2. 🔜 Viteビルド最適化とCode splitting
3. 🔜 Docker化（Dockerfile + docker-compose.yml）
4. 🔜 GitHub Actions CI/CD設定
5. 🔜 運用ガイドとAPI仕様書作成

### 環境変数設定（新規実装済み）

**開発環境セットアップ**:
```bash
# フロントエンド
cd phase4_visualization/frontend
cp .env.example .env.development
npm install
npm run dev  # http://localhost:5173

# バックエンド
cd phase4_visualization/backend
cp .env.example .env.development
pip install -r requirements.txt
python -m uvicorn api.main:app --reload  # http://localhost:8000
```

詳細は[`phase4_visualization/WEEK7_8_INTEGRATION_REPORT.md`](./phase4_visualization/WEEK7_8_INTEGRATION_REPORT.md)を参照

---

## 🤝 開発ガイド

### 🔧 環境セットアップ
```bash
# 基本セットアップ
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude
```

### 🌐 Phase 4 統合環境（Week 7-8実装済み）

#### セキュリティ設定
- **開発環境**: `.env.development` - ローカル開発用設定
- **本番環境**: `.env.production` - 本番デプロイ用設定
- **重要**: `.env`ファイルは`.gitignore`に登録済み（機密情報保護）

#### 環境変数管理
- **フロントエンド**: Vite環境変数（`import.meta.env`）
- **バックエンド**: pydantic-settings（型安全な設定管理）
- **CORS設定**: 環境に応じた自動切り替え

### 📋 テスト実行
```bash
# Phase 4 フロントエンドテスト
cd phase4_visualization/frontend
npm run test          # Vitest ユニットテスト（67件）
npm run test:e2e      # Playwright E2Eテスト（18件）

# Phase 4 API統合テスト
cd phase4_visualization
python scripts/test_api_integration.py  # Python統合テスト
bash scripts/test_api_quick.sh         # Bash簡易テスト
```

---

## 📄 ライセンス

MIT License

---

## 📧 お問い合わせ

プロジェクトに関する質問や提案は、GitHubのIssuesでお願いします。

---

*最終更新: 2025年10月27日 08:07 JST*
*バージョン: v4.0.1*

**更新履歴:**
- v4.0.1 (2025年10月27日): Phase 4 Week 7-8 統合作業のドキュメント更新
- v4.0.0 (2025年10月27日): Phase 4 可視化システム開始、環境変数管理実装
- v3.0.0 (2025年01月27日): Phase 3 Neo4j統合完了、テストカバレッジ83%達成
- v2.0.0 (2025年01月27日): ドキュメント構造の整理と重複削除
