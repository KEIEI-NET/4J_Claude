# Docker セットアップガイド

**最終更新**: 2025-10-28 03:00:00 JST (日本標準時)
**対象**: Phase 4 フロントエンド・バックエンド
**バージョン**: 4.2.0

---

## 📋 概要

Phase 4 可視化システムのDocker化構成とセットアップ手順を説明します。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├──────────────┬──────────────────┬─────────────────────────┤
│  Frontend    │    Backend       │       Neo4j             │
│  (Nginx)     │   (FastAPI)      │   (Database)            │
│  Port: 80    │   Port: 8000     │   Port: 7474, 7687      │
└──────────────┴──────────────────┴─────────────────────────┘
```

---

## 🚀 クイックスタート

### 前提条件

- Docker 24.0+
- Docker Compose 2.20+
- Git

### 起動手順

```bash
# リポジトリクローン
git clone https://github.com/KEIEI-NET/4J_Claude.git
cd 4J_Claude/phase4_visualization

# Docker Composeで全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f

# ヘルスチェック
curl http://localhost/health       # Frontend
curl http://localhost:8000/health  # Backend
curl http://localhost:7474         # Neo4j
```

**アクセスURL**:
- フロントエンド: http://localhost
- バックエンドAPI: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (user: neo4j, pass: password123)

---

## 📦 コンテナ構成

### 1. Frontend (React + Vite + Nginx)

**イメージ**: `phase4-frontend:latest`

**マルチステージビルド**:
1. **Builder Stage**: Node.js 20でViteビルド実行
2. **Production Stage**: Nginx Alpineで静的ファイル配信

**最適化**:
- ✅ Code splitting (5チャンク: react, antd, d3, state, app)
- ✅ Gzip圧縮
- ✅ Minification (Terser)
- ✅ 静的ファイルキャッシュ (1年)
- ✅ SPAルーティング対応
- ✅ APIプロキシ (/api → backend:8000)

**Nginx設定**:
```nginx
# Gzip圧縮
gzip on;
gzip_min_length 10240;

# 静的ファイルキャッシュ
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# SPAルーティング
location / {
    try_files $uri $uri/ /index.html;
}

# APIプロキシ
location /api/ {
    proxy_pass http://backend:8000/api/;
}
```

**セキュリティ**:
- 非rootユーザー (appuser:1000)
- 読み取り専用ファイルシステム
- ヘルスチェック有効

---

### 2. Backend (Python + FastAPI)

**イメージ**: `phase4-backend:latest`

**マルチステージビルド**:
1. **Builder Stage**: Python 3.11で依存関係インストール
2. **Production Stage**: 最小限の実行環境

**依存関係** (pyproject.toml):
```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "neo4j>=5.15.0",
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
]
```

**環境変数**:
| 変数 | デフォルト | 説明 |
|------|-----------|------|
| API_HOST | 0.0.0.0 | APIサーバーホスト |
| API_PORT | 8000 | APIサーバーポート |
| NEO4J_URI | bolt://neo4j:7687 | Neo4j接続URI |
| NEO4J_USER | neo4j | Neo4jユーザー名 |
| NEO4J_PASSWORD | password123 | Neo4jパスワード |
| CORS_ORIGINS | http://localhost:5173,http://localhost:80 | CORS許可オリジン |
| LOG_LEVEL | INFO | ログレベル |

**ヘルスチェック**:
```bash
python -c "import httpx; httpx.get('http://localhost:8000/health')"
```

**セキュリティ**:
- 非rootユーザー (appuser:1000)
- 依存関係の最小化
- ヘルスチェック有効

---

### 3. Neo4j (Database)

**イメージ**: `neo4j:5.15-community`

**設定**:
```yaml
environment:
  - NEO4J_AUTH=neo4j/password123
  - NEO4J_PLUGINS=["apoc", "graph-data-science"]
  - NEO4J_dbms_memory_heap_max__size=2G
  - NEO4J_dbms_memory_pagecache_size=1G
```

**プラグイン**:
- APOC (Awesome Procedures On Cypher)
- Graph Data Science

**永続化ボリューム**:
- `neo4j_data`: データベースファイル
- `neo4j_logs`: ログファイル
- `neo4j_import`: インポート用ディレクトリ
- `neo4j_plugins`: プラグイン

---

## 🔧 開発環境での使用

### ホットリロード対応

**Frontend**:
```bash
# docker-compose.override.yml を作成
services:
  frontend:
    volumes:
      - ./frontend/src:/app/src:ro
    command: npm run dev
```

**Backend**:
```bash
# docker-compose.override.yml を作成
services:
  backend:
    volumes:
      - ./backend:/app/backend:ro
    command: uvicorn backend.api.main:app --reload --host 0.0.0.0
```

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f neo4j
```

### コンテナ内でコマンド実行

```bash
# Backendコンテナ
docker-compose exec backend bash
docker-compose exec backend python -m pytest

# Neo4jコンテナ
docker-compose exec neo4j cypher-shell -u neo4j -p password123
```

---

## 📊 ビルドとデプロイ

### ローカルビルド

```bash
# Backend
docker build -t phase4-backend:latest -f backend/Dockerfile .

# Frontend
docker build -t phase4-frontend:latest -f frontend/Dockerfile ./frontend

# 全サービスビルド
docker-compose build
```

### イメージサイズ最適化

**Backend**:
- Base image: python:3.11-slim (~120MB)
- Final image: ~350MB (依存関係含む)

**Frontend**:
- Base image: nginx:1.25-alpine (~40MB)
- Final image: ~50MB (静的ファイル含む)

**最適化手法**:
- ✅ マルチステージビルド
- ✅ .dockerignoreの活用
- ✅ レイヤーキャッシュ最適化
- ✅ 不要ファイルの除外

---

## 🔒 セキュリティベストプラクティス

### 1. 非rootユーザー実行

```dockerfile
# ユーザー作成
RUN useradd -m -u 1000 appuser

# 所有権変更
RUN chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser
```

### 2. シークレット管理

**開発環境**:
```bash
# .env ファイル作成
NEO4J_PASSWORD=your_secure_password
API_SECRET_KEY=your_secret_key
```

**本番環境**:
- Docker Secrets
- Kubernetes Secrets
- HashiCorp Vault

### 3. ネットワーク分離

```yaml
networks:
  phase4_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### 4. ボリューム権限

```bash
# ボリューム所有権確認
docker-compose exec neo4j ls -la /data
```

---

## 🧪 テスト

### Docker Composeテスト

```bash
# 設定検証
docker-compose config

# サービス起動テスト
docker-compose up -d
docker-compose ps

# ヘルスチェック
curl http://localhost/health
curl http://localhost:8000/health

# 停止・削除
docker-compose down -v
```

### イメージ脆弱性スキャン

```bash
# Trivyでスキャン
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image phase4-backend:latest

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image phase4-frontend:latest
```

---

## 🚨 トラブルシューティング

### コンテナが起動しない

```bash
# ログ確認
docker-compose logs backend
docker-compose logs frontend
docker-compose logs neo4j

# ヘルスチェック確認
docker-compose ps
```

### Neo4j接続エラー

**症状**: Backend起動時に "Neo4j connection failed"

**解決方法**:
1. Neo4jヘルスチェック確認
```bash
docker-compose logs neo4j | grep "Started"
```

2. 接続確認
```bash
docker-compose exec backend python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
driver.verify_connectivity()
print('✅ Connected')
driver.close()
"
```

### ポート競合

**症状**: "Bind for 0.0.0.0:8000 failed: port is already allocated"

**解決方法**:
```bash
# ポート使用状況確認
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# docker-compose.ymlでポート変更
ports:
  - "8001:8000"  # ホスト:8001 → コンテナ:8000
```

### ビルドキャッシュクリア

```bash
# イメージ削除
docker-compose down --rmi all

# ビルドキャッシュクリア
docker builder prune

# 完全クリーンビルド
docker-compose build --no-cache
```

---

## 📈 パフォーマンスチューニング

### Neo4jメモリ設定

```yaml
environment:
  # ヒープメモリ (推奨: システムメモリの50%)
  - NEO4J_dbms_memory_heap_max__size=4G

  # ページキャッシュ (推奨: システムメモリの25%)
  - NEO4J_dbms_memory_pagecache_size=2G
```

### Nginxワーカープロセス

```nginx
worker_processes auto;  # CPUコア数に自動調整
worker_connections 1024;
```

### Uvicornワーカー数

```bash
# docker-compose.yml
command: uvicorn backend.api.main:app --workers 4 --host 0.0.0.0
```

---

## 🔄 CI/CD統合

### GitHub Actions

`.github/workflows/ci.yml`:
- Backend/Frontendテスト
- Dockerイメージビルド
- セキュリティスキャン

`.github/workflows/deploy.yml`:
- イメージプッシュ (GitHub Container Registry)
- ステージング/本番デプロイ
- リリース作成

### イメージタグ戦略

```bash
# 開発: ブランチ名
phase4-backend:develop

# ステージング: コミットハッシュ
phase4-backend:abc1234

# 本番: セマンティックバージョン
phase4-backend:v4.2.0
phase4-backend:latest
```

---

## 📚 参考リソース

### 公式ドキュメント

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Neo4j Docker](https://neo4j.com/docs/operations-manual/current/docker/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Docker](https://hub.docker.com/_/nginx)

### ツール

- [Trivy](https://github.com/aquasecurity/trivy) - コンテナ脆弱性スキャン
- [Dive](https://github.com/wagoodman/dive) - イメージレイヤー分析
- [Hadolint](https://github.com/hadolint/hadolint) - Dockerfileリント

---

## ✅ チェックリスト

Docker化完了確認項目:

- [x] Backend Dockerfile作成
- [x] Frontend Dockerfile作成
- [x] docker-compose.yml作成
- [x] .dockerignore作成
- [x] GitHub Actions CI/CD設定
- [x] セキュリティ設定（非rootユーザー）
- [x] ヘルスチェック設定
- [x] マルチステージビルド実装
- [ ] ローカルでdocker-compose起動テスト
- [ ] E2Eテスト実行
- [ ] セキュリティスキャン実行

---

**作成日**: 2025-10-28 03:00:00 JST (日本標準時)
**担当**: Claude Code
**ステータス**: Week 7-8 実装完了
