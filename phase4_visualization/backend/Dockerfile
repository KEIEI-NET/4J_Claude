# Phase 4 Backend Dockerfile
# Python 3.11 + FastAPI + Neo4j Client

FROM python:3.11-slim as base

# 作業ディレクトリ設定
WORKDIR /app

# 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システム依存関係のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ========== Builder Stage ==========
FROM base as builder

# pyproject.tomlとパッケージファイルをコピー
COPY ../pyproject.toml .
COPY backend/ ./backend/

# 依存関係のインストール
RUN pip install --user --no-warn-script-location \
    -e .[dev]

# ========== Production Stage ==========
FROM base as production

# ユーザー作成（セキュリティ）
RUN useradd -m -u 1000 appuser

# Python依存関係を builder からコピー
COPY --from=builder /root/.local /home/appuser/.local

# アプリケーションコードをコピー
COPY backend/ /app/backend/
COPY pyproject.toml /app/

# 所有権変更
RUN chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser

# PATHに .local/bin を追加
ENV PATH=/home/appuser/.local/bin:$PATH

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
