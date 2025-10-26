# Test Scripts

Phase 4 バックエンドAPIの統合テストスクリプト集

## 📁 スクリプト一覧

### 1. `test_api_integration.py`

Pythonによる包括的なAPI統合テストスクリプト

**機能**:
- 全APIエンドポイントの動作確認
- CORS設定の検証
- 詳細なテスト結果レポート
- Rich UIによる見やすい出力

**使用方法**:

```bash
# デフォルト (http://localhost:8000)
python scripts/test_api_integration.py

# カスタムURL指定
python scripts/test_api_integration.py --url http://your-server:8000
```

**必要なパッケージ**:
```bash
pip install requests rich
```

**テスト項目**:
1. ✓ Health Check (`GET /health`)
2. ✓ Impact Analysis (`POST /api/impact-analysis`)
3. ✓ Get Dependencies (`GET /api/dependencies/:path`)
4. ✓ Circular Dependencies (`GET /api/circular-dependencies`)
5. ✓ CORS Configuration

### 2. `test_api_quick.sh`

Bashによる簡易APIテストスクリプト

**機能**:
- curlを使用した基本的な接続テスト
- CORSヘッダー確認
- シンプルで高速な動作確認

**使用方法**:

```bash
# デフォルト (http://localhost:8000)
./scripts/test_api_quick.sh

# カスタムURL指定
./scripts/test_api_quick.sh http://your-server:8000
```

**必要な環境**:
- bash
- curl
- python3 (JSON整形用、オプション)

**実行権限の付与**:
```bash
chmod +x scripts/test_api_quick.sh
```

## 🚀 使用例

### シナリオ1: ローカル開発環境でのテスト

1. バックエンドAPIを起動:
```bash
cd backend
python -m uvicorn api.main:app --reload
```

2. 別のターミナルで統合テストを実行:
```bash
python scripts/test_api_integration.py
```

### シナリオ2: CI/CDパイプラインでの使用

```yaml
# .github/workflows/test.yml の例
- name: Run API Integration Tests
  run: |
    python scripts/test_api_integration.py --url http://test-server:8000
```

### シナリオ3: 本番環境ヘルスチェック

```bash
# 簡易テストで本番APIの状態確認
./scripts/test_api_quick.sh https://production-api.example.com
```

## 📊 出力例

### test_api_integration.py

```
╭──────────────────────────────────────────╮
│ API Integration Test Suite              │
│ Testing: http://localhost:8000           │
╰──────────────────────────────────────────╯

1. Testing Health Check Endpoint
✓ Health check passed
  Status: healthy
  Neo4j Connected: True
  Version: 4.0.0

2. Testing Impact Analysis Endpoint
✓ Impact analysis succeeded
  Affected files: 15
  Risk level: medium

...

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ Endpoint                    ┃ Status  ┃ HTTP Code ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ GET /health                 │ ✓ Pass  │ 200       │
│ POST /api/impact-analysis   │ ✓ Pass  │ 200       │
│ ...                         │ ...     │ ...       │
└─────────────────────────────┴─────────┴───────────┘

Overall Result: 5/5 tests passed (100.0%)
✓ All tests passed!
```

### test_api_quick.sh

```
=========================================
Quick API Test
API URL: http://localhost:8000
=========================================

1. Testing Health Check...
✓ Health check passed (HTTP 200)
{
    "status": "healthy",
    "neo4j_connected": true,
    "version": "4.0.0"
}

2. Testing Impact Analysis Endpoint...
⚠ File not found - expected if no data loaded (HTTP 404)

...
```

## 🔧 トラブルシューティング

### エラー: Connection refused

**原因**: バックエンドAPIが起動していない

**解決方法**:
```bash
# バックエンドを起動
cd backend
python -m uvicorn api.main:app --reload
```

### エラー: Module 'requests' not found

**原因**: 必要なPythonパッケージがインストールされていない

**解決方法**:
```bash
pip install requests rich
```

### CORS テスト失敗

**原因**: バックエンドのCORS設定が正しくない

**解決方法**:
1. `backend/.env.development` を確認
2. `CORS_ALLOWED_ORIGINS` が正しく設定されているか確認
3. バックエンドを再起動

## 📝 注意事項

- **データがない場合**: Neo4jにデータが登録されていない場合、一部のテストは404エラーになりますが、これは正常な動作です
- **タイムアウト設定**: ネットワークが遅い環境では、スクリプト内のタイムアウト値を調整してください
- **セキュリティ**: 本番環境でテストする場合は、認証情報やAPIキーが必要な場合があります

## 🔗 関連ドキュメント

- [Backend API Documentation](../backend/README.md)
- [Frontend Integration Guide](../frontend/README.md)
- [Phase 4 Overview](../README.md)

---

**作成日**: 2025-10-28 JST
**対象**: Phase 4 可視化レイヤー
**ステータス**: Week 7-8 実装中
