#!/bin/bash

# Integration Test Runner Script
# このスクリプトはDockerサービスを起動して統合テストを実行します

set -e

echo "========================================="
echo "  Celery Integration Test Runner"
echo "========================================="
echo ""

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ステップ1: 既存のテストコンテナを停止
echo -e "${YELLOW}Step 1: Stopping existing test containers...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
echo ""

# ステップ2: Dockerサービスを起動
echo -e "${YELLOW}Step 2: Starting Docker services (RabbitMQ, Redis, Neo4j)...${NC}"
docker-compose -f docker-compose.test.yml up -d rabbitmq-test redis-test neo4j-test

# ステップ3: サービスの起動を待機
echo -e "${YELLOW}Step 3: Waiting for services to be ready...${NC}"
echo "  - Waiting for RabbitMQ..."
timeout 60 bash -c 'until docker-compose -f docker-compose.test.yml exec -T rabbitmq-test rabbitmq-diagnostics ping >/dev/null 2>&1; do sleep 1; done' || {
    echo -e "${RED}RabbitMQ failed to start${NC}"
    docker-compose -f docker-compose.test.yml logs rabbitmq-test
    exit 1
}

echo "  - Waiting for Redis..."
timeout 60 bash -c 'until docker-compose -f docker-compose.test.yml exec -T redis-test redis-cli ping >/dev/null 2>&1; do sleep 1; done' || {
    echo -e "${RED}Redis failed to start${NC}"
    docker-compose -f docker-compose.test.yml logs redis-test
    exit 1
}

echo "  - Waiting for Neo4j..."
timeout 120 bash -c 'until docker-compose -f docker-compose.test.yml exec -T neo4j-test wget --spider -q http://localhost:7474 >/dev/null 2>&1; do sleep 2; done' || {
    echo -e "${RED}Neo4j failed to start${NC}"
    docker-compose -f docker-compose.test.yml logs neo4j-test
    exit 1
}

echo -e "${GREEN}All services are ready!${NC}"
echo ""

# ステップ4: Celeryワーカーをバックグラウンドで起動
echo -e "${YELLOW}Step 4: Starting Celery worker in background...${NC}"
export CELERY_BROKER_URL="amqp://test:test@localhost:5673//"
export CELERY_RESULT_BACKEND="redis://localhost:6380/0"

# Celeryワーカーをバックグラウンドで起動
python scripts/start_worker.py > /tmp/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "Celery worker started with PID: $WORKER_PID"

# ワーカーの起動を待機（5秒）
echo "Waiting for worker to initialize..."
sleep 5
echo ""

# ステップ5: 統合テストを実行
echo -e "${YELLOW}Step 5: Running integration tests...${NC}"
export NEO4J_URI="bolt://localhost:7688"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="testpassword"

pytest tests/integration/test_celery_integration.py -v --tb=short --color=yes || TEST_FAILED=1

echo ""

# ステップ6: クリーンアップ
echo -e "${YELLOW}Step 6: Cleanup...${NC}"

# Celeryワーカーを停止
if [ ! -z "$WORKER_PID" ]; then
    echo "Stopping Celery worker (PID: $WORKER_PID)..."
    kill $WORKER_PID 2>/dev/null || true
    sleep 2
fi

# Dockerサービスを停止
echo "Stopping Docker services..."
docker-compose -f docker-compose.test.yml down -v

echo ""

# 結果を表示
if [ -z "$TEST_FAILED" ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  Integration tests PASSED!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}  Integration tests FAILED!${NC}"
    echo -e "${RED}=========================================${NC}"
    echo ""
    echo "Check the logs:"
    echo "  - Celery worker: /tmp/celery_worker.log"
    echo "  - Docker services: docker-compose -f docker-compose.test.yml logs"
    exit 1
fi
