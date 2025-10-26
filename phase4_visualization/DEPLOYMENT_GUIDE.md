# デプロイメントガイド

**最終更新**: 2025-10-28 03:00:00 JST (日本標準時)
**対象**: Phase 4 本番環境デプロイメント
**バージョン**: 4.2.0

---

## 📋 概要

Phase 4 可視化システムの本番環境へのデプロイ手順とベストプラクティスを説明します。

---

## 🎯 デプロイメント戦略

### デプロイメント方式

| 方式 | 説明 | 適用シーン |
|-----|------|----------|
| **Blue-Green** | 2つの環境を切り替え | 最小ダウンタイム |
| **Canary** | 段階的にトラフィック移行 | リスク最小化 |
| **Rolling** | 順次更新 | 継続的デプロイ |

**推奨**: Blue-Green (Phase 4では最小ダウンタイムが重要)

---

## 🚀 本番環境要件

### システム要件

| コンポーネント | 最小 | 推奨 |
|--------------|------|------|
| **CPU** | 4コア | 8コア |
| **メモリ** | 8GB | 16GB |
| **ストレージ** | 50GB SSD | 100GB NVMe SSD |
| **ネットワーク** | 100Mbps | 1Gbps |

### ソフトウェア要件

- **OS**: Ubuntu 22.04 LTS / CentOS 8+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **SSL/TLS証明書**: Let's Encrypt / 商用証明書

---

## 📦 デプロイ前準備

### 1. サーバーセットアップ

```bash
# Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose インストール
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER
```

### 2. ファイアウォール設定

```bash
# UFW設定 (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld設定 (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. SSL証明書取得

```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot certonly --standalone -d phase4.example.com
```

---

## 🔧 本番環境設定

### 1. 環境変数ファイル作成

**`.env.production`**:
```bash
# === API設定 ===
API_TITLE=Phase 4 Visualization API
API_VERSION=4.2.0
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# === Neo4j設定 ===
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${NEO4J_PRODUCTION_PASSWORD}  # 環境変数から取得

# === CORS設定 ===
CORS_ORIGINS=https://phase4.example.com

# === ログ設定 ===
LOG_LEVEL=WARNING
LOG_FORMAT=json

# === セキュリティ ===
API_SECRET_KEY=${API_SECRET_KEY}  # 環境変数から取得
```

### 2. docker-compose.production.yml作成

```yaml
version: '3.9'

services:
  neo4j:
    image: neo4j:5.15-enterprise  # Enterpriseエディション
    restart: always
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PRODUCTION_PASSWORD}
      - NEO4J_dbms_memory_heap_max__size=8G
      - NEO4J_dbms_memory_pagecache_size=4G
      - NEO4J_dbms_connector_bolt_advertised__address=neo4j:7687
    volumes:
      - /data/neo4j/data:/data
      - /data/neo4j/logs:/logs
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 12G

  backend:
    image: ghcr.io/keiei-net/4j_claude/phase4-backend:v4.2.0
    restart: always
    env_file:
      - .env.production
    depends_on:
      - neo4j
    deploy:
      replicas: 2  # 2インスタンス
      resources:
        limits:
          cpus: '2'
          memory: 2G

  frontend:
    image: ghcr.io/keiei-net/4j_claude/phase4-frontend:v4.2.0
    restart: always
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

  # === Nginx Reverse Proxy ===
  nginx:
    image: nginx:1.25-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - frontend
      - backend
```

### 3. Nginx設定 (nginx.conf)

```nginx
events {
    worker_connections 2048;
}

http {
    upstream backend {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
    }

    upstream frontend {
        server frontend:80;
    }

    # HTTP → HTTPS リダイレクト
    server {
        listen 80;
        server_name phase4.example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name phase4.example.com;

        # SSL証明書
        ssl_certificate /etc/letsencrypt/live/phase4.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/phase4.example.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # セキュリティヘッダー
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # フロントエンド
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # バックエンドAPI
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Rate Limiting
            limit_req zone=api_limit burst=20 nodelay;
        }
    }

    # Rate Limiting設定
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
}
```

---

## 🚢 デプロイ手順

### 1. Blue-Green デプロイメント

```bash
# === Green環境準備 ===
# 1. 新バージョンのイメージをPull
docker pull ghcr.io/keiei-net/4j_claude/phase4-backend:v4.2.0
docker pull ghcr.io/keiei-net/4j_claude/phase4-frontend:v4.2.0

# 2. Green環境起動
docker-compose -f docker-compose.production.yml -p phase4_green up -d

# 3. ヘルスチェック
curl https://green.phase4.example.com/health
curl https://green.phase4.example.com/api/health

# === トラフィック切り替え ===
# 4. Nginxでトラフィックを Green に切り替え
sudo nginx -s reload

# 5. Blue環境の監視（5分間）
docker-compose -f docker-compose.production.yml -p phase4_blue logs -f

# === Blue環境停止 ===
# 6. 問題なければ Blue環境停止
docker-compose -f docker-compose.production.yml -p phase4_blue down

# === ロールバック（問題発生時） ===
# Nginxでトラフィックを Blue に戻す
sudo nginx -s reload
docker-compose -f docker-compose.production.yml -p phase4_green down
```

### 2. デプロイスクリプト (deploy.sh)

```bash
#!/bin/bash
set -euo pipefail

VERSION=${1:-latest}
COMPOSE_FILE="docker-compose.production.yml"

echo "=== Phase 4 Deployment v${VERSION} ==="

# 1. イメージPull
echo "Pulling Docker images..."
docker pull ghcr.io/keiei-net/4j_claude/phase4-backend:${VERSION}
docker pull ghcr.io/keiei-net/4j_claude/phase4-frontend:${VERSION}

# 2. 設定検証
echo "Validating configuration..."
docker-compose -f ${COMPOSE_FILE} config > /dev/null

# 3. データベースバックアップ
echo "Backing up Neo4j database..."
docker-compose -f ${COMPOSE_FILE} exec neo4j neo4j-admin backup --backup-dir=/backups

# 4. デプロイ実行
echo "Deploying..."
docker-compose -f ${COMPOSE_FILE} up -d --force-recreate

# 5. ヘルスチェック
echo "Health check..."
sleep 30
curl -f http://localhost:8000/health || { echo "Backend health check failed"; exit 1; }
curl -f http://localhost/health || { echo "Frontend health check failed"; exit 1; }

# 6. 古いイメージ削除
echo "Cleaning up old images..."
docker image prune -f

echo "✅ Deployment successful!"
```

---

## 📊 監視とロギング

### 1. ログ集約 (Loki + Promtail)

**docker-compose.monitoring.yml**:
```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
```

### 2. メトリクス監視 (Prometheus)

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']
```

### 3. アラート設定

```yaml
groups:
  - name: phase4_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: Neo4jDown
        expr: up{job="neo4j"} == 0
        for: 1m
        annotations:
          summary: "Neo4j is down"
```

---

## 🔒 セキュリティ強化

### 1. シークレット管理

```bash
# Docker Secrets使用
echo "production_password" | docker secret create neo4j_password -
echo "api_secret_key_xyz" | docker secret create api_secret_key -

# docker-compose.ymlで参照
secrets:
  neo4j_password:
    external: true
  api_secret_key:
    external: true
```

### 2. ネットワーク分離

```yaml
networks:
  frontend_network:
    driver: bridge
  backend_network:
    driver: bridge
    internal: true  # 外部アクセス不可
```

### 3. 定期的なセキュリティスキャン

```bash
# Trivyでイメージスキャン
trivy image ghcr.io/keiei-net/4j_claude/phase4-backend:latest

# 脆弱性修正
docker pull ghcr.io/keiei-net/4j_claude/phase4-backend:latest
docker-compose up -d --force-recreate
```

---

## 🧪 デプロイ後検証

### 1. スモークテスト

```bash
#!/bin/bash
set -e

BASE_URL="https://phase4.example.com"

# ヘルスチェック
curl -f ${BASE_URL}/health
curl -f ${BASE_URL}/api/health

# 基本機能テスト
curl -f ${BASE_URL}/api/dependencies/src/main/java/Example.java

echo "✅ Smoke tests passed"
```

### 2. パフォーマンステスト

```bash
# Apache Bench
ab -n 1000 -c 10 https://phase4.example.com/api/health

# K6負荷テスト
k6 run load-test.js
```

### 3. E2Eテスト

```bash
# Playwright本番環境テスト
PLAYWRIGHT_BASE_URL=https://phase4.example.com npm run test:e2e
```

---

## 🔄 バックアップとリカバリ

### 1. Neo4jバックアップ

```bash
# 定期バックアップ (cron)
0 2 * * * docker-compose exec neo4j neo4j-admin backup --backup-dir=/backups/$(date +\%Y\%m\%d)

# バックアップ保持期間: 30日
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

### 2. リストア手順

```bash
# Neo4jコンテナ停止
docker-compose stop neo4j

# データリストア
docker-compose exec neo4j neo4j-admin restore --from=/backups/20251028

# Neo4j再起動
docker-compose start neo4j
```

---

## 📚 参考リソース

- [Docker Production Best Practices](https://docs.docker.com/config/containers/resource_constraints/)
- [Neo4j Operations Manual](https://neo4j.com/docs/operations-manual/current/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Best Practices](https://www.nginx.com/blog/tuning-nginx/)

---

## ✅ デプロイチェックリスト

- [x] Docker環境構築
- [x] SSL証明書取得
- [x] 本番環境設定ファイル作成
- [x] Nginx Reverse Proxy設定
- [x] デプロイスクリプト作成
- [ ] 監視・ロギング設定
- [ ] バックアップ設定
- [ ] スモークテスト実行
- [ ] パフォーマンステスト実行
- [ ] セキュリティスキャン実行
- [ ] ドキュメント更新

---

**作成日**: 2025-10-28 03:00:00 JST (日本標準時)
**担当**: Claude Code
**ステータス**: Week 7-8 実装完了
