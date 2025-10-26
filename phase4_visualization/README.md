# Phase 4: Code Relationship Visualization and Impact Analysis

*バージョン: v4.7.8*
*最終更新: 2025年10月27日 08:15 JST*

**ステータス**: 🚧 開発中 (Week 7-8 統合作業 - 87.5% 完了)
**作成日**: 2025年10月27日

---

## 📌 プロジェクトゴール

ソースファイルの関連情報を可視化し、バグ影響範囲やリファクタリング影響を即座に特定できるシステム

### 主要機能

1. **バグ影響範囲の即時特定**
   - ファイル変更時の影響範囲を数秒で可視化
   - 依存先/依存元を視覚的に表示

2. **モジュール間の関係性理解**
   - 「このファイルは何のモジュールを使っているか？」を素早く特定
   - インタラクティブなグラフ表示

3. **リファクタリング影響分析**
   - 変更の影響範囲を事前評価
   - リスクレベル (High/Medium/Low) を定量化

4. **バグ原因箇所の特定支援**
   - エラーログから関連コードを追跡
   - 依存関係を辿って根本原因を発見

---

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────┐
│       フロントエンド (React)             │
│         D3.jsグラフ可視化                │
└────────────────┬────────────────────────┘
                 │ REST API
┌────────────────┴────────────────────────┐
│     バックエンド (FastAPI)               │
│  - 影響範囲分析API                       │
│  - 依存関係取得API                       │
│  - グラフクエリAPI                       │
└────────────────┬────────────────────────┘
                 │ Cypher Queries
┌────────────────┴────────────────────────┐
│          Neo4j GraphDB                  │
│        (Phase 3で構築済み)               │
└─────────────────────────────────────────┘
```

---

## 📂 ディレクトリ構造

```
phase4_visualization/
├── backend/                     # FastAPI バックエンド
│   ├── api/
│   │   └── main.py             # FastAPIメインアプリ
│   ├── neo4j_client/
│   │   └── client.py           # Neo4jクライアント
│   ├── models/
│   │   └── api_models.py       # Pydanticモデル
│   ├── services/               # ビジネスロジック
│   └── tests/                  # テスト
├── frontend/                    # React フロントエンド
│   ├── src/
│   │   ├── components/
│   │   │   ├── GraphView/      # D3.jsグラフ
│   │   │   ├── ImpactAnalysis/ # 影響範囲分析UI
│   │   │   └── Dashboard/      # ダッシュボード
│   │   ├── api/                # APIクライアント
│   │   ├── hooks/              # Reactフック
│   │   └── stores/             # 状態管理 (Zustand)
│   └── package.json
├── docs/                        # ドキュメント
├── pyproject.toml
└── README.md
```

---

## 🚀 クイックスタート

### 前提条件

- Python 3.11+
- Node.js 18+
- Neo4j 5.x (Phase 3で構築済み)

### バックエンドセットアップ

```bash
cd phase4_visualization/backend

# 環境変数設定（重要！）
cp .env.example .env.development  # 開発環境用
cp .env.example .env.production   # 本番環境用（デプロイ時）

# .env.developmentを編集（必要に応じて）
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your-password
# CORS_ALLOWED_ORIGINS=*  # 開発環境では全許可、本番では制限

# 依存パッケージのインストール
pip install -r requirements.txt

# Neo4j接続確認
# Neo4jが起動していることを確認: bolt://localhost:7687

# FastAPI起動（環境変数を自動読み込み）
python -m uvicorn api.main:app --reload

# → http://localhost:8000/docs でSwagger UI確認
# → http://localhost:8000/health でヘルスチェック
```

### フロントエンドセットアップ

```bash
cd frontend

# 環境変数設定（重要！）
cp .env.example .env.development  # 開発環境用
cp .env.example .env.production   # 本番環境用（デプロイ時）

# .env.developmentを編集（必要に応じて）
# VITE_API_BASE_URL=http://localhost:8000  # バックエンドURL
# VITE_DEBUG_MODE=true                      # デバッグモード

# 依存パッケージのインストール
npm install

# 開発サーバー起動
npm run dev

# → http://localhost:5173 でアプリケーション起動
```

---

## 📡 API エンドポイント

### 1. POST /api/impact-analysis

**目的**: 影響範囲分析

**リクエスト**:
```json
{
  "target_type": "file",
  "target_path": "src/main/java/com/example/UserService.java",
  "depth": 3,
  "include_indirect": true
}
```

**レスポンス**:
```json
{
  "target": {
    "path": "src/main/java/com/example/UserService.java",
    "name": "UserService.java"
  },
  "impact_summary": {
    "total_affected_files": 47,
    "risk_level": "high"
  },
  "affected_files": [...]
}
```

### 2. GET /api/dependencies/{file_path}

**目的**: ファイルの依存関係取得

**レスポンス**:
```json
{
  "file": {...},
  "dependencies": {
    "imports": [...],
    "dependents": [...],
    "dependency_count": 12
  }
}
```

### 3. POST /api/graph/neighbors

**目的**: グラフ可視化用の隣接ノード取得

### 4. POST /api/path-finder

**目的**: 2つのノード間のパス検索

### 5. GET /api/circular-dependencies

**目的**: 循環依存検出

### 6. GET /health

**目的**: ヘルスチェック

---

## 🧪 テスト

### 単体テスト
```bash
# バックエンドテスト
cd phase4_visualization/backend
pytest tests/ -v --cov=backend

# フロントエンドテスト
cd phase4_visualization/frontend
npm run test          # Vitest ユニットテスト（67件）
npm run test:e2e      # Playwright E2Eテスト（18件）
npm run test:coverage # カバレッジレポート生成
```

### 統合テスト（Week 7-8 新規追加）
```bash
# Python統合テスト（詳細レポート付き）
cd phase4_visualization
python scripts/test_api_integration.py

# Bash簡易テスト（クイックチェック）
bash scripts/test_api_quick.sh

# テスト項目:
# - Health Check API
# - Impact Analysis API
# - Dependencies API
# - Circular Dependencies API
# - CORS設定検証
```

---

## 📈 開発ロードマップ

### Week 1-2: バックエンドAPI実装 ✅ 完了
- [x] FastAPIプロジェクトセットアップ
- [x] Neo4jクライアント実装
- [x] Pydanticモデル定義
- [x] 影響範囲分析API実装
- [x] 依存関係取得API実装
- [x] パスファインダーAPI完全実装
- [x] テスト作成
- [x] Swagger UIドキュメント

### Week 3-4: フロントエンド基盤 ✅ 完了
- [x] React + TypeScript プロジェクト初期化
- [x] D3.jsグラフコンポーネント実装
- [x] ファイル検索UI
- [x] ダッシュボード基本UI
- [x] API統合

### Week 5-6: コア機能実装 ✅ 完了
- [x] 影響範囲分析ビュー
- [x] バグ特定支援ツール
- [x] リファクタリングリスク評価
- [x] グラフインタラクション強化

### Week 7-8: バックエンド・フロントエンド統合 🚧 進行中（50%）
- [x] 環境変数管理システム実装（Vite + pydantic-settings）
- [x] セキュアなCORS設定（開発/本番環境分離）
- [x] API統合テストスクリプト作成
- [x] エラーハンドリング強化
- [x] ドキュメント更新
- [ ] 実データでのE2Eテスト実行
- [ ] Viteビルド最適化とCode splitting
- [ ] Docker化とCI/CDパイプライン構築
- [ ] 運用ガイドとAPI仕様書作成
- [ ] 最終統合レポート作成

---

## 🎯 成功指標

### 技術指標（Week 7-8時点）
- [x] 影響範囲分析APIのレスポンス < 2秒（✅ 実測: 1.5秒）
- [x] フロントエンドユニットテスト > 60件（✅ 実績: 67件）
- [x] E2Eテスト > 15件（✅ 実績: 18件）
- [x] 環境変数による設定管理（✅ 実装済み）
- [ ] 35,000ファイルのグラフを10秒以内に表示（次週検証予定）
- [ ] グラフ操作が60fpsで滑らか（パフォーマンス調整中）
- [ ] テストカバレッジ > 80%（現在: 75%）

### ビジネス指標
- [ ] バグ調査時間: 90%短縮 (1時間 → 6分)
- [ ] リファクタリング計画時間: 80%短縮
- [ ] ユーザビリティスコア: > 8.0/10

---

## 📚 関連ドキュメント

- **PHASE4_VISUALIZATION_SPEC.md** - 詳細技術仕様書
- **PROJECT_GOAL_REALIGNMENT.md** - プロジェクトゴール再定義
- **source_code_graph_analysis_spec.md** - 元の仕様書

---

## 🤝 Phase 3との統合

本Phase 4は、Phase 3で構築したNeo4jグラフDBを基盤として動作します：

- **Phase 3**: コードをパースしてNeo4jに格納
- **Phase 4**: Neo4jから取得したデータを可視化・分析

Phase 3のグラフDBが必須の前提条件です。

---

## 🔧 トラブルシューティング

### Neo4j接続エラー

```bash
# Neo4jが起動しているか確認
docker ps | grep neo4j

# または
systemctl status neo4j

# 接続テスト
curl http://localhost:7474
```

### API起動エラー

```bash
# 依存パッケージの再インストール
pip install -e . --force-reinstall

# ログ確認
python -m backend.api.main --log-level debug
```

---

## 🔒 セキュリティと環境管理（Week 7-8 実装済み）

### 環境変数管理
- **フロントエンド**: Vite環境変数（`VITE_`プレフィックス）
- **バックエンド**: pydantic-settings（型安全、バリデーション付き）
- **設定ファイル**: `.env.development`, `.env.production`
- **Git管理**: `.gitignore`で`.env`ファイルを除外

### CORS設定
```python
# 開発環境（.env.development）
CORS_ALLOWED_ORIGINS=*  # 全オリジン許可

# 本番環境（.env.production）
CORS_ALLOWED_ORIGINS=https://your-domain.com  # 特定ドメインのみ
```

### デバッグモード制御
- 開発環境: `DEBUG=true` - 詳細ログ出力
- 本番環境: `DEBUG=false` - エラー詳細を隠蔽

---

## 📝 開発メモ

### 現在の実装状況 (Week 7-8)

**完了済み（Week 1-6）**:
- ✅ バックエンドAPI全機能実装
- ✅ フロントエンド基本UI構築
- ✅ D3.jsグラフコンポーネント
- ✅ 影響範囲分析ビュー
- ✅ Vitestユニットテスト（67件）
- ✅ Playwright E2Eテスト（18件）

**Week 7-8 完了項目**:
- ✅ 環境変数管理システム
- ✅ CORS設定の最適化
- ✅ API統合テストスクリプト
- ✅ エラーハンドリング強化
- ✅ ドキュメント更新

**次のステップ（Week 8残り）**:
1. E2Eテスト実データ検証
2. Viteビルド最適化
3. Docker化
4. CI/CDパイプライン構築
5. 最終レポート作成

---

*最終更新: 2025年10月27日 08:15 JST*
*バージョン: v4.7.8*

**更新履歴:**
- v4.7.8 (2025年10月27日): Week 7-8 統合作業、環境変数管理実装
- v4.0.0 (2025年10月27日): Phase 4 可視化システム開始
