@echo off
REM Integration Test Runner Script for Windows
REM このスクリプトはDockerサービスを起動して統合テストを実行します

echo =========================================
echo   Celery Integration Test Runner
echo =========================================
echo.

REM ステップ1: 既存のテストコンテナを停止
echo Step 1: Stopping existing test containers...
docker-compose -f docker-compose.test.yml down -v 2>nul
echo.

REM ステップ2: Dockerサービスを起動
echo Step 2: Starting Docker services (RabbitMQ, Redis, Neo4j)...
docker-compose -f docker-compose.test.yml up -d rabbitmq-test redis-test neo4j-test
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start Docker services
    exit /b 1
)
echo.

REM ステップ3: サービスの起動を待機
echo Step 3: Waiting for services to be ready...
echo   - Waiting for RabbitMQ (max 60 seconds)...
timeout /t 10 /nobreak >nul
echo   - Waiting for Redis (max 60 seconds)...
timeout /t 5 /nobreak >nul
echo   - Waiting for Neo4j (max 120 seconds)...
timeout /t 30 /nobreak >nul
echo All services should be ready!
echo.

REM ステップ4: Celeryワーカーをバックグラウンドで起動
echo Step 4: Starting Celery worker in background...
set CELERY_BROKER_URL=amqp://test:test@localhost:5673//
set CELERY_RESULT_BACKEND=redis://localhost:6380/0

REM Celeryワーカーをバックグラウンドで起動
start /B python scripts\start_worker.py > celery_worker.log 2>&1
echo Celery worker started in background
echo Waiting for worker to initialize...
timeout /t 10 /nobreak >nul
echo.

REM ステップ5: 統合テストを実行
echo Step 5: Running integration tests...
set NEO4J_URI=bolt://localhost:7688
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=testpassword

pytest tests\integration\test_celery_integration.py -v --tb=short --color=yes
set TEST_RESULT=%ERRORLEVEL%
echo.

REM ステップ6: クリーンアップ
echo Step 6: Cleanup...

REM Celeryワーカーを停止
echo Stopping Celery worker...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq start_worker*" 2>nul

REM Dockerサービスを停止
echo Stopping Docker services...
docker-compose -f docker-compose.test.yml down -v
echo.

REM 結果を表示
if %TEST_RESULT% EQU 0 (
    echo =========================================
    echo   Integration tests PASSED!
    echo =========================================
    exit /b 0
) else (
    echo =========================================
    echo   Integration tests FAILED!
    echo =========================================
    echo.
    echo Check the logs:
    echo   - Celery worker: celery_worker.log
    echo   - Docker services: docker-compose -f docker-compose.test.yml logs
    exit /b 1
)
