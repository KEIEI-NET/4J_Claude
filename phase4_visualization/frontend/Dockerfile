# Phase 4 Frontend Dockerfile
# Multi-stage build: Node.js 20 + Vite + React

# ========== Builder Stage ==========
FROM node:20-alpine as builder

# 作業ディレクトリ設定
WORKDIR /app

# package.json と package-lock.json をコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci --only=production=false

# ソースコードをコピー
COPY . .

# Viteビルド実行（Code splitting、minification、gzip圧縮を含む）
RUN npm run build

# ========== Production Stage ==========
FROM nginx:1.25-alpine as production

# Nginxユーザー設定
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Nginx設定ファイルをコピー
COPY --chown=appuser:appuser <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip圧縮設定
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied any;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/x-javascript
        application/xml
        application/xml+rss;

    # 静的ファイルのキャッシュ設定
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # SPAルーティング対応
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # APIプロキシ（バックエンドへ転送）
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ヘルスチェック
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

# ビルド成果物をコピー
COPY --from=builder --chown=appuser:appuser /app/dist /usr/share/nginx/html

# 所有権変更
RUN chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

# 非rootユーザーに切り替え
USER appuser

# ポート公開
EXPOSE 80

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

# Nginx起動
CMD ["nginx", "-g", "daemon off;"]
