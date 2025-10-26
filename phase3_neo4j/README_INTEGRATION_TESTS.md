# Integration Tests Guide

このガイドでは、Celery並列処理基盤の統合テストの実行方法を説明します。

## 概要

統合テストでは、実際のDockerサービス（RabbitMQ、Redis、Neo4j）を使用してCeleryタスクをテストします。

### テスト対象
- RabbitMQへの接続
- Redisへの接続
- Neo4jへの接続
- 各Celeryタスクの実行
- エンドツーエンドのワークフロー
- エラーハンドリング
- パフォーマンスベンチマーク

## 前提条件

### 必須ツール
- Docker Desktop (Windows) または Docker + Docker Compose (Linux/Mac)
- Python 3.11+
- pip

### 必須パッケージ
```bash
pip install -r requirements.txt
```

## 実行方法

### 方法1: Pythonスクリプトで実行（推奨）

最も簡単な方法です。すべてのステップを自動化します。

```bash
python scripts/run_integration_tests.py
```

このスクリプトは以下を実行します：
1. 既存のテストコンテナを停止
2. Dockerサービスを起動（RabbitMQ、Redis、Neo4j）
3. サービスの準備を待機
4. Celeryワーカーをバックグラウンド起動
5. 統合テストを実行
6. クリーンアップ（コンテナ停止、ワーカー終了）

### 方法2: バッチスクリプトで実行（Windows）

```cmd
scripts\run_integration_tests.bat
```

### 方法3: シェルスクリプトで実行（Linux/Mac）

```bash
chmod +x scripts/run_integration_tests.sh
./scripts/run_integration_tests.sh
```

### 方法4: 手動実行

より細かい制御が必要な場合は、手動で各ステップを実行できます。

#### ステップ1: Dockerサービスを起動

```bash
docker-compose -f docker-compose.test.yml up -d
```

起動されるサービス:
- `rabbitmq-test`: RabbitMQ (port 5673, 15673)
- `redis-test`: Redis (port 6380)
- `neo4j-test`: Neo4j (port 7475, 7688)

#### ステップ2: サービスの準備を確認

```bash
# RabbitMQ
docker-compose -f docker-compose.test.yml exec rabbitmq-test rabbitmq-diagnostics ping

# Redis
docker-compose -f docker-compose.test.yml exec redis-test redis-cli ping

# Neo4j
curl http://localhost:7475
```

#### ステップ3: Celeryワーカーを起動

別のターミナルで:

```bash
# 環境変数を設定
export CELERY_BROKER_URL=amqp://test:test@localhost:5673//
export CELERY_RESULT_BACKEND=redis://localhost:6380/0

# ワーカーを起動
python scripts/start_worker.py
```

#### ステップ4: 統合テストを実行

別のターミナルで:

```bash
# 環境変数を設定
export NEO4J_URI=bolt://localhost:7688
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=testpassword

# テストを実行
pytest tests/integration/test_celery_integration.py -v
```

#### ステップ5: クリーンアップ

```bash
# Celeryワーカーを停止（Ctrl+C）

# Dockerサービスを停止
docker-compose -f docker-compose.test.yml down -v
```

## テストケース詳細

### TestCeleryConnection
- RabbitMQ接続確認
- Redis接続確認
- Neo4j接続確認

### TestAnalyzeFileTask
- 単一ファイル分析タスクの実行
- 存在しないファイルのエラーハンドリング

### TestBatchAnalyzeFilesTask
- バッチ分析タスクの実行（並列処理）
- 空のファイルリストのハンドリング

### TestUpdateGraphTask
- グラフ更新タスクの実行
- Neo4jへのノード作成確認

### TestBatchUpdateGraphTask
- バッチグラフ更新タスクの実行
- 複数の分析結果の処理

### TestAnalyzeAndUpdateGraphTask
- Chordパターンの実行
- 分析→グラフ更新の統合フロー

### TestEndToEndIntegration
- 完全なワークフローのテスト
- パフォーマンスベンチマーク

### TestErrorHandling
- 無効な認証情報のエラーハンドリング
- タスクのリトライメカニズム

## トラブルシューティング

### Dockerサービスが起動しない

```bash
# ログを確認
docker-compose -f docker-compose.test.yml logs

# 特定のサービスのログ
docker-compose -f docker-compose.test.yml logs rabbitmq-test
docker-compose -f docker-compose.test.yml logs redis-test
docker-compose -f docker-compose.test.yml logs neo4j-test
```

### Celeryワーカーが接続できない

```bash
# 環境変数を確認
echo $CELERY_BROKER_URL
echo $CELERY_RESULT_BACKEND

# RabbitMQが起動しているか確認
docker-compose -f docker-compose.test.yml ps rabbitmq-test

# RabbitMQ Management UIで確認
# http://localhost:15673
# User: test, Password: test
```

### Neo4jに接続できない

```bash
# Neo4jが起動しているか確認
docker-compose -f docker-compose.test.yml ps neo4j-test

# Neo4j Browserで確認
# http://localhost:7475
# User: neo4j, Password: testpassword

# Boltポートの確認
nc -zv localhost 7688
```

### テストが失敗する

```bash
# より詳細な出力でテストを実行
pytest tests/integration/test_celery_integration.py -v -s --tb=long

# 特定のテストのみ実行
pytest tests/integration/test_celery_integration.py::TestAnalyzeFileTask::test_analyze_file_task_execution -v

# Celeryワーカーのログを確認
cat celery_worker.log
```

### ポート競合

テスト環境は本番環境と異なるポートを使用します：

| サービス | 本番ポート | テストポート |
|---------|-----------|-------------|
| RabbitMQ AMQP | 5672 | 5673 |
| RabbitMQ Management | 15672 | 15673 |
| Redis | 6379 | 6380 |
| Neo4j HTTP | 7474 | 7475 |
| Neo4j Bolt | 7687 | 7688 |

ポート競合がある場合は、`docker-compose.test.yml`でポートを変更してください。

## CI/CD統合

### GitHub Actions例

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run integration tests
      run: |
        python scripts/run_integration_tests.py
```

## パフォーマンス目標

| テストケース | 目標時間 |
|-------------|---------|
| test_analyze_file_task_execution | < 5秒 |
| test_batch_analyze_files_execution | < 10秒 |
| test_update_graph_execution | < 10秒 |
| test_analyze_and_update_graph_execution | < 30秒 |
| test_full_workflow | < 30秒 |
| 全テストスイート | < 2分 |

## 継続的改善

統合テストは定期的に実行し、以下の点を監視してください：

1. **実行時間**: テストが遅くなっていないか
2. **成功率**: 全テストがパスしているか
3. **カバレッジ**: 新機能がテストされているか
4. **リソース使用量**: Dockerコンテナのメモリ・CPU使用率

## 次のステップ

1. 統合テストをCI/CDパイプラインに統合
2. パフォーマンステストを追加（大量ファイル処理）
3. 負荷テストを追加（並列度のテスト）
4. E2Eテストを追加（実際のJavaプロジェクトを使用）

## 参考資料

- [Celery Testing](https://docs.celeryq.dev/en/stable/userguide/testing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Neo4j Testing](https://neo4j.com/docs/operations-manual/current/docker/)
