# マスタードキュメントインデックス

*バージョン: v6.0.0*
*最終更新: 2025年01月29日 16:21 JST*

このドキュメントは、4J_Claudeプロジェクトの全ドキュメントへの統合インデックスです。プロジェクトの完全な理解とAIによる再現性のために必要なすべての情報へのガイドとなります。

---

## 📚 プロジェクト概要ドキュメント

### 必読ドキュメント（優先順）

1. **[README.md](./README.md)** (12KB)
   - プロジェクト全体概要
   - Phase 1-5の完了状態
   - クイックスタートガイド
   - 技術スタック一覧

2. **[CLAUDE.md](./CLAUDE.md)** (15KB)
   - Claude Code開発者向けガイド
   - プロジェクト構造の詳細
   - 開発ワークフロー
   - 環境セットアップ手順

3. **[TODO.md](./TODO.md)** (65KB)
   - 全タスク管理と進捗
   - Phase 1-5の完了マーク
   - Phase 6（次期）計画

---

## 🏗️ アーキテクチャ・設計ドキュメント

### システム設計

4. **[DETAILED_DESIGN.md](./DETAILED_DESIGN.md)** (87KB)
   - 詳細技術アーキテクチャ
   - 各フェーズの設計思想
   - データフロー図

5. **[integrated_architecture.md](./integrated_architecture.md)** (12KB)
   - 統合システムアーキテクチャ
   - フェーズ間の連携設計
   - スケーラビリティ考慮事項

6. **[IMPLEMENTATION_SPEC.md](./IMPLEMENTATION_SPEC.md)** (35KB)
   - 実装仕様書
   - コーディング規約
   - テスト戦略

---

## 📂 フェーズ別ドキュメント

### Phase 1: Cassandra特化分析（完了）

7. **[phase1_cassandra/README_CASSANDRA.md](./phase1_cassandra/README_CASSANDRA.md)** (20KB)
   - Cassandra分析機能詳細
   - JavaパーサーとCQLパーサー仕様
   - 問題検出アルゴリズム

8. **[phase1_cassandra/DEVELOPMENT.md](./phase1_cassandra/DEVELOPMENT.md)** (8KB)
   - 開発ガイドライン
   - ローカル環境セットアップ
   - デバッグ手順

### Phase 2: LLM統合（完了）

9. **[phase2_llm/README.md](./phase2_llm/README.md)** (15KB)
   - Claude API統合方法
   - 意味論的分析エンジン
   - 自動修正提案システム

10. **[phase2_llm/LLM_INTEGRATION.md](./phase2_llm/LLM_INTEGRATION.md)** (10KB)
    - APIキー管理
    - レート制限対応
    - コスト最適化戦略

### Phase 3: Neo4j/グラフDB（完了）

11. **[phase3_neo4j/README.md](./phase3_neo4j/README.md)** (18KB)
    - Neo4j統合アーキテクチャ
    - グラフデータモデル
    - Celery並列処理設計

12. **[phase3_neo4j/GRAPH_QUERIES.md](./phase3_neo4j/GRAPH_QUERIES.md)** (12KB)
    - Cypherクエリサンプル
    - パフォーマンス最適化
    - インデックス戦略

### Phase 4/5: 可視化・認証・監視（完了）

13. **[phase4_visualization/README.md](./phase4_visualization/README.md)** (25KB)
    - 統合システム概要
    - API仕様（16エンドポイント）
    - フロントエンドアーキテクチャ

14. **[phase4_visualization/API_SPECIFICATION.md](./phase4_visualization/API_SPECIFICATION.md)** (16KB)
    - OpenAPI/Swagger仕様
    - エンドポイント詳細
    - リクエスト/レスポンス例

15. **[phase4_visualization/AUTHENTICATION_GUIDE.md](./phase4_visualization/AUTHENTICATION_GUIDE.md)** (14KB)
    - JWT認証実装
    - RBAC設計
    - セキュリティベストプラクティス

16. **[phase4_visualization/MONITORING_GUIDE.md](./phase4_visualization/MONITORING_GUIDE.md)** (17KB)
    - Prometheus設定
    - Grafanaダッシュボード
    - AlertManager設定

---

## 🚀 デプロイメント・運用ドキュメント

### Docker・CI/CD

17. **[phase4_visualization/DOCKER_SETUP.md](./phase4_visualization/DOCKER_SETUP.md)** (12KB)
    - Docker構成詳細
    - docker-compose設定
    - 環境変数管理

18. **[phase4_visualization/DEPLOYMENT_GUIDE.md](./phase4_visualization/DEPLOYMENT_GUIDE.md)** (13KB)
    - 本番デプロイ手順
    - スケーリング設定
    - バックアップ戦略

19. **[phase4_visualization/DOCKER_CI_CD_SUMMARY.md](./phase4_visualization/DOCKER_CI_CD_SUMMARY.md)** (15KB)
    - GitHub Actions設定
    - 自動テスト実行
    - デプロイパイプライン

---

## 📊 完了レポート・サマリー

### 週次完了レポート

20. **[phase4_visualization/WEEK1_2_COMPLETION_REPORT.md](./phase4_visualization/WEEK1_2_COMPLETION_REPORT.md)**
    - バックエンドAPI実装

21. **[phase4_visualization/WEEK3_4_COMPLETION_REPORT.md](./phase4_visualization/WEEK3_4_COMPLETION_REPORT.md)**
    - フロントエンド実装

22. **[phase4_visualization/WEEK5_6_COMPLETION_REPORT.md](./phase4_visualization/WEEK5_6_COMPLETION_REPORT.md)**
    - テスト実装

23. **[phase4_visualization/WEEK7_8_COMPLETION_REPORT.md](./phase4_visualization/WEEK7_8_COMPLETION_REPORT.md)**
    - 統合・最適化

24. **[phase4_visualization/WEEK7_8_INTEGRATION_REPORT.md](./phase4_visualization/WEEK7_8_INTEGRATION_REPORT.md)**
    - システム統合詳細

### Phase完了レポート

25. **[phase4_visualization/PHASE5_COMPLETION_REPORT.md](./phase4_visualization/PHASE5_COMPLETION_REPORT.md)** (25KB)
    - Phase 5完全実装レポート
    - 認証・監視システム詳細
    - 100%カバレッジ達成記録

---

## 🔧 実装ガイド・チュートリアル

### 実装ガイド

26. **[phase4_visualization/NEO4J_VISUALIZATION_GUIDE.md](./phase4_visualization/NEO4J_VISUALIZATION_GUIDE.md)** (11KB)
    - グラフ可視化実装
    - D3.js統合方法

27. **[phase4_visualization/STEP_BY_STEP_TUTORIAL.md](./phase4_visualization/STEP_BY_STEP_TUTORIAL.md)** (7KB)
    - 初心者向けチュートリアル
    - 5分でのセットアップ

28. **[phase4_visualization/QUICK_START_QUERIES.cypher](./phase4_visualization/QUICK_START_QUERIES.cypher)** (11KB)
    - Cypherクエリサンプル
    - データ初期化スクリプト

### 分類・カテゴリ化ガイド

29. **[phase4_visualization/CONTENT_CATEGORIZATION_GUIDE.md](./phase4_visualization/CONTENT_CATEGORIZATION_GUIDE.md)** (28KB)
    - コンテンツ分類手法
    - カテゴリ定義

30. **[phase4_visualization/CALLS_DETAILED_CLASSIFICATION_GUIDE.md](./phase4_visualization/CALLS_DETAILED_CLASSIFICATION_GUIDE.md)** (20KB)
    - 関数呼び出し分類
    - 依存関係分析

---

## 📈 変更履歴・メタドキュメント

31. **[CHANGELOG.md](./CHANGELOG.md)** (10KB)
    - 全バージョン変更履歴
    - リリースノート

32. **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** (5KB)
    - 旧ドキュメントインデックス

33. **[DOCUMENTATION_UPDATE_REPORT.md](./DOCUMENTATION_UPDATE_REPORT.md)** (8KB)
    - ドキュメント更新履歴

34. **[DOCUMENTATION_UPDATE_REPORT_PHASE3.md](./DOCUMENTATION_UPDATE_REPORT_PHASE3.md)** (10KB)
    - Phase 3ドキュメント更新

---

## 🎯 AI再現性のための重要情報

### 環境設定ファイル

- `.env.example` - 環境変数テンプレート
- `pyproject.toml` - Python依存関係
- `package.json` - Node.js依存関係
- `docker-compose.yml` - Docker構成
- `docker-compose.monitoring.yml` - 監視スタック構成

### 必須環境変数

```bash
# 認証
JWT_SECRET_KEY=min-32-chars-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# データベース
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# API
ANTHROPIC_API_KEY=sk-xxx

# 監視
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### テスト実行コマンド

```bash
# バックエンドテスト（100%カバレッジ）
cd phase4_visualization
python -m pytest backend/tests/ --cov=backend --cov-report=html

# フロントエンドテスト
cd phase4_visualization/frontend
npm test
npm run test:e2e

# 統合テスト
python test_detailed_api.py
```

### Docker起動コマンド

```bash
# アプリケーション起動
docker-compose up -d

# 監視スタック起動
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 📞 サポート・問い合わせ

- **GitHubリポジトリ**: [プロジェクトURL]
- **Issues**: バグ報告・機能要望
- **Wiki**: 追加ドキュメント
- **Discussions**: コミュニティサポート

---

*最終更新: 2025年01月29日 16:21 JST*
*バージョン: v6.0.0*

**更新履歴:**
- v6.0.0 (2025年01月29日): 初版作成、Phase 1-5完全実装に伴う全ドキュメントインデックス化