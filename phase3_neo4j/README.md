# Phase 3: 本格展開 - Neo4Jグラフデータベース統合

**ステータス**: 🔵 計画中
**期間**: 2025年11月25日 - 2026年1月3日

## 目標

真の核心機能の実装：Neo4Jグラフデータベースによるコード構造の可視化と影響範囲分析

## 主要機能

### Week 5-6: Neo4Jグラフデータベース統合

#### Task 12.1: Neo4jスキーマ設計

**ノードタイプ**:
- `FileNode` (Java/CQLファイル)
- `ClassNode` (Javaクラス)
- `MethodNode` (メソッド)
- `CQLQueryNode` (CQLクエリ)
- `TableNode` (Cassandraテーブル)
- `IssueNode` (検出された問題)

**リレーションシップ**:
- `CONTAINS` (File → Class)
- `DEFINES` (Class → Method)
- `EXECUTES` (Method → CQLQuery)
- `ACCESSES` (Query → Table)
- `HAS_ISSUE` (Query → Issue)
- `REFERENCES` (File → File)

#### Task 12.2: Neo4jクライアント実装
- 接続管理
- トランザクション管理
- バッチインポート
- グラフ構築

#### Task 12.3: 影響範囲分析
- ファイル変更の影響分析
- 依存関係トレース
- リスク評価

### Week 7-8: 並列処理とダッシュボード

#### Task 13.1: Celery並列処理基盤
- RabbitMQブローカー設定
- Redisバックエンド設定
- ファイル解析タスク
- **目標**: 35,000ファイルを2時間以内に処理

#### Task 13.2: FastAPI実装

**APIエンドポイント**:
- `POST /analyze` - 分析実行
- `GET /issues` - 問題一覧取得
- `GET /impact/{table}` - 影響範囲分析
- `GET /graph` - グラフデータ取得
- `POST /fix` - 自動修正実行
- `GET /reports` - レポート一覧

#### Task 13.3: Reactダッシュボード
- D3.jsによるグラフ可視化
- インタラクティブな探索機能
- 問題一覧・フィルタリング
- ズーム/フィルタ機能

### Week 9-10: CI/CD統合と本番運用

#### Task 14.1: CI/CD統合
- GitHub Actions ワークフロー
- プルリクエストでの自動分析
- Slack/メール通知

#### Task 14.2: 週次レポート自動化
- 週次統計集計
- トレンド分析
- Celery Beat設定

#### Task 14.3: 本番環境構築

**Docker Compose構成**:
- Neo4j コンテナ
- RabbitMQ コンテナ
- Redis コンテナ
- Celery Worker コンテナ (x8)
- FastAPI コンテナ
- Nginx コンテナ

**監視設定**:
- Prometheus メトリクス
- Grafana ダッシュボード
- アラート設定

## 成功条件

- [ ] Neo4jグラフDB構築完了
- [ ] 並列処理で2時間以内に35,000ファイル分析
- [ ] Reactダッシュボードが稼働
- [ ] CI/CD統合完了

## 予算

- LLMコスト: $315/月
- インフラコスト: $670/月
  - Neo4j: $200/月
  - RabbitMQ: $100/月
  - Redis: $50/月
  - Celery Workers (8 instances): $320/月
- **月間合計**: $985

## ディレクトリ構造（予定）

```
phase3_neo4j/
├── src/
│   └── cassandra_analyzer/
│       ├── graph/
│       │   ├── neo4j_client.py   # Neo4jクライアント
│       │   └── graph_builder.py  # グラフ構築
│       ├── analyzers/
│       │   └── impact_analyzer.py # 影響範囲分析
│       ├── api/
│       │   ├── main.py           # FastAPIアプリ
│       │   └── endpoints/        # APIエンドポイント
│       └── worker/
│           ├── celery_app.py     # Celeryアプリ
│           └── tasks.py          # 並列タスク
├── dashboard/                    # Reactダッシュボード
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── GraphView.tsx
│   │   │   └── IssueList.tsx
│   │   └── App.tsx
│   └── package.json
├── docker-compose.yml            # Docker構成
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions
├── tests/
│   ├── unit/
│   └── integration/
└── README.md                     # このファイル
```

## Cypherクエリ例

### 影響範囲分析
```cypher
// テーブルを使用している全ファイルを取得
MATCH (t:TableNode {name: 'users'})<-[:ACCESSES]-(q:CQLQueryNode)<-[:EXECUTES]-(m:MethodNode)<-[:DEFINES]-(c:ClassNode)<-[:CONTAINS]-(f:FileNode)
RETURN DISTINCT f.path, COUNT(q) as query_count
ORDER BY query_count DESC
```

### 依存関係トレース
```cypher
// ファイルの依存関係を再帰的に取得
MATCH path = (f:FileNode {path: '/src/UserDAO.java'})-[:REFERENCES*1..5]->(dep:FileNode)
RETURN path
```

## 詳細計画

詳細なタスクとタイムラインは [`../TODO.md`](../TODO.md) のPhase 3セクションを参照してください。

---

**開始日**: 2025年11月25日（予定）
