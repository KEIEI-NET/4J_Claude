# API仕様書

**最終更新**: 2025-10-28 03:00:00 JST (日本標準時)
**API バージョン**: 4.0.0
**ベースURL**: `http://localhost:8000` (開発), `https://phase4.example.com` (本番)

---

## 📋 概要

Phase 4 コード関係可視化・影響範囲分析システムのREST API仕様書です。

### API設計原則

- **RESTful**: リソース指向設計
- **JSON**: リクエスト/レスポンス形式
- **CORS**: クロスオリジン対応
- **エラーハンドリング**: 標準HTTPステータスコード
- **バージョニング**: URLパス (将来的に /api/v2)

---

## 🔐 認証

**Phase 4 (現在)**: 認証なし（開発環境）
**Phase 5 (予定)**: JWT Bearer Token認証

```http
Authorization: Bearer <token>
```

---

## 📡 エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|-------------|---------|------|
| `/health` | GET | ヘルスチェック |
| `/api/impact-analysis` | POST | 影響範囲分析 |
| `/api/dependencies/{file_path}` | GET | ファイル依存関係取得 |
| `/api/graph/neighbors` | POST | グラフ隣接ノード取得 |
| `/api/path-finder` | POST | パス検索 |
| `/api/circular-dependencies` | GET | 循環依存検出 |
| `/api/refactoring-risk` | POST | リファクタリングリスク評価 |

---

## 🔍 エンドポイント詳細

### 1. ヘルスチェック

**概要**: APIとNeo4jの稼働状況を確認

#### リクエスト

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### レスポンス

**成功 (200 OK)**:
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "version": "4.0.0"
}
```

**障害時 (200 OK - degraded)**:
```json
{
  "status": "degraded",
  "neo4j_connected": false,
  "version": "4.0.0"
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 正常 (healthyまたはdegraded) |

---

### 2. 影響範囲分析

**概要**: 指定ファイルの変更が及ぼす影響範囲を分析

#### リクエスト

```http
POST /api/impact-analysis HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "target_path": "src/main/java/com/example/UserService.java",
  "depth": 3,
  "include_indirect": true
}
```

**パラメータ**:

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|----|----|---------|------|
| `target_path` | string | ✅ | - | 分析対象ファイルパス |
| `depth` | integer | ❌ | 3 | 探索深度 (1-10) |
| `include_indirect` | boolean | ❌ | true | 間接依存を含むか |

#### レスポンス

**成功 (200 OK)**:
```json
{
  "target": {
    "type": "file",
    "path": "src/main/java/com/example/UserService.java",
    "name": "UserService.java",
    "language": "java",
    "size": 15234,
    "complexity": 12
  },
  "impact_summary": {
    "total_affected_files": 23,
    "total_affected_methods": 67,
    "total_affected_classes": 15,
    "risk_level": "medium",
    "confidence": 0.85
  },
  "affected_files": [
    {
      "path": "src/main/java/com/example/UserController.java",
      "name": "UserController.java",
      "distance": 1,
      "dependency_type": "direct",
      "affected_methods": ["createUser", "updateUser"],
      "risk_contribution": 0.65
    }
  ],
  "dependency_graph": {
    "nodes": [
      {
        "id": "src/main/java/com/example/UserService.java",
        "label": "UserService.java",
        "type": "File",
        "properties": {
          "path": "src/main/java/com/example/UserService.java",
          "is_target": true
        }
      }
    ],
    "edges": [
      {
        "source": "src/main/java/com/example/UserService.java",
        "target": "src/main/java/com/example/UserController.java",
        "type": "DEPENDS_ON",
        "properties": {
          "weight": 0.75
        }
      }
    ]
  }
}
```

**リスクレベル**:
- `low`: 影響ファイル数 ≤ 10
- `medium`: 影響ファイル数 11-30
- `high`: 影響ファイル数 > 30

#### エラーレスポンス

**ファイル未検出 (404 Not Found)**:
```json
{
  "detail": "File not found: src/main/java/com/example/UserService.java"
}
```

**サービス利用不可 (503 Service Unavailable)**:
```json
{
  "detail": "Neo4j client not initialized"
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 404 | ファイル未検出 |
| 422 | バリデーションエラー |
| 500 | 内部エラー |
| 503 | Neo4j接続エラー |

---

### 3. ファイル依存関係取得

**概要**: 指定ファイルのインポート/依存元を取得

#### リクエスト

```http
GET /api/dependencies/src/main/java/com/example/UserService.java HTTP/1.1
Host: localhost:8000
```

**パラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|----|----|------|
| `file_path` | string (path) | ✅ | ファイルパス |

#### レスポンス

**成功 (200 OK)**:
```json
{
  "file": {
    "type": "file",
    "path": "src/main/java/com/example/UserService.java",
    "name": "UserService.java",
    "language": "java",
    "size": 15234,
    "complexity": 12
  },
  "dependencies": {
    "imports": [
      "src/main/java/com/example/UserRepository.java",
      "src/main/java/com/example/User.java"
    ],
    "dependents": [
      "src/main/java/com/example/UserController.java"
    ],
    "dependency_count": 2,
    "dependent_count": 1
  },
  "methods": []
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 404 | ファイル未検出 |
| 503 | Neo4j接続エラー |

---

### 4. グラフ隣接ノード取得

**概要**: 指定ノードの隣接ノードを取得（D3.js可視化用）

#### リクエスト

```http
POST /api/graph/neighbors HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "node_id": "src/main/java/com/example/UserService.java",
  "node_type": "file",
  "depth": 2,
  "direction": "both"
}
```

**パラメータ**:

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|----|----|---------|------|
| `node_id` | string | ✅ | - | ノードID (ファイルパスまたはクラス名) |
| `node_type` | enum | ✅ | - | ノードタイプ (file, class, method) |
| `depth` | integer | ❌ | 1 | 探索深度 (1-5) |
| `direction` | enum | ❌ | both | 方向 (incoming, outgoing, both) |

**node_type**:
- `file`: ファイルノード
- `class`: クラスノード
- `method`: メソッドノード

**direction**:
- `incoming`: 依存元のみ
- `outgoing`: 依存先のみ
- `both`: 両方向

#### レスポンス

**成功 (200 OK)**:
```json
{
  "center_node": {
    "id": "src/main/java/com/example/UserService.java",
    "label": "UserService.java",
    "type": "File",
    "properties": {
      "path": "src/main/java/com/example/UserService.java",
      "language": "java"
    }
  },
  "neighbors": [
    {
      "node": {
        "id": "src/main/java/com/example/UserRepository.java",
        "label": "UserRepository.java",
        "type": "File",
        "properties": {
          "path": "src/main/java/com/example/UserRepository.java"
        }
      },
      "relationship": {
        "type": "IMPORTS",
        "properties": {
          "line_number": 5
        }
      }
    }
  ]
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 404 | ノード未検出 |
| 422 | バリデーションエラー |
| 503 | Neo4j接続エラー |

---

### 5. パス検索

**概要**: 2つのノード間の依存パスを検索

#### リクエスト

```http
POST /api/path-finder HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "source": "src/main/java/com/example/UserController.java",
  "target": "src/main/java/com/example/UserRepository.java",
  "max_depth": 5
}
```

**パラメータ**:

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|----|----|---------|------|
| `source` | string | ✅ | - | 起点ノードID |
| `target` | string | ✅ | - | 終点ノードID |
| `max_depth` | integer | ❌ | 5 | 最大探索深度 (1-10) |

#### レスポンス

**成功 (200 OK)**:
```json
{
  "paths": [
    {
      "nodes": [
        "src/main/java/com/example/UserController.java",
        "src/main/java/com/example/UserService.java",
        "src/main/java/com/example/UserRepository.java"
      ],
      "relationships": [
        {
          "type": "CALLS",
          "source": "src/main/java/com/example/UserController.java",
          "target": "src/main/java/com/example/UserService.java"
        },
        {
          "type": "IMPORTS",
          "source": "src/main/java/com/example/UserService.java",
          "target": "src/main/java/com/example/UserRepository.java"
        }
      ],
      "length": 2,
      "weight": 1.5
    }
  ],
  "shortest_path_length": 2,
  "total_paths_found": 1
}
```

**パスが見つからない場合 (200 OK)**:
```json
{
  "paths": [],
  "shortest_path_length": 0,
  "total_paths_found": 0
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 (パスありまたはなし) |
| 422 | バリデーションエラー |
| 500 | 内部エラー |

---

### 6. 循環依存検出

**概要**: プロジェクト内の循環依存を検出

#### リクエスト

```http
GET /api/circular-dependencies HTTP/1.1
Host: localhost:8000
```

#### レスポンス

**成功 (200 OK)**:
```json
{
  "circular_dependencies": [
    {
      "cycle": [
        "src/main/java/com/example/A.java",
        "src/main/java/com/example/B.java",
        "src/main/java/com/example/C.java",
        "src/main/java/com/example/A.java"
      ],
      "length": 3,
      "severity": "high"
    }
  ],
  "total_cycles": 1,
  "recommendation": "循環依存を解消してください"
}
```

**循環依存なし (200 OK)**:
```json
{
  "circular_dependencies": [],
  "total_cycles": 0,
  "recommendation": "循環依存はありません"
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 500 | 内部エラー |
| 503 | Neo4j接続エラー |

---

### 7. リファクタリングリスク評価

**概要**: 複数ファイルのリファクタリングに伴うリスクを評価

#### リクエスト

```http
POST /api/refactoring-risk HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "target_files": [
    "src/main/java/com/example/UserService.java",
    "src/main/java/com/example/UserController.java"
  ]
}
```

**パラメータ**:

| フィールド | 型 | 必須 | 説明 |
|-----------|----|----|------|
| `target_files` | array[string] | ✅ | リファクタリング対象ファイルリスト |

#### レスポンス

**成功 (200 OK)**:
```json
{
  "risk_assessment": {
    "overall_risk": "medium",
    "risk_score": 6.5,
    "factors": {
      "affected_file_count": 32,
      "circular_dependencies": false,
      "test_coverage": 0.75,
      "complexity_increase": 1.0
    }
  },
  "recommendations": [
    "テストカバレッジを80%以上に向上させてください",
    "段階的なリファクタリングを推奨します"
  ],
  "testing_checklist": []
}
```

#### ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 422 | バリデーションエラー |
| 500 | 内部エラー |
| 503 | Neo4j接続エラー |

---

## 📦 共通データモデル

### FileInfo

```typescript
{
  type: "file",
  path: string,
  name: string,
  language?: string,
  size?: integer,
  complexity?: integer
}
```

### GraphNode

```typescript
{
  id: string,
  label: string,
  type: string,
  properties: object
}
```

### GraphEdge

```typescript
{
  source: string,
  target: string,
  type: string,
  properties: object
}
```

### RiskLevel

```typescript
enum RiskLevel {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high"
}
```

---

## ❌ エラーレスポンス

### 標準エラーフォーマット

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

| コード | 名称 | 説明 |
|-------|------|------|
| 200 | OK | 成功 |
| 400 | Bad Request | リクエストが不正 |
| 404 | Not Found | リソース未検出 |
| 422 | Unprocessable Entity | バリデーションエラー |
| 500 | Internal Server Error | サーバー内部エラー |
| 503 | Service Unavailable | Neo4j接続エラー |

### バリデーションエラー例

```json
{
  "detail": [
    {
      "loc": ["body", "depth"],
      "msg": "value must be between 1 and 10",
      "type": "value_error"
    }
  ]
}
```

---

## 🔄 CORS設定

### 許可オリジン

**開発環境**:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (テスト用)

**本番環境**:
- `https://phase4.example.com`

### 許可メソッド

- GET
- POST
- PUT
- DELETE
- OPTIONS

### 許可ヘッダー

- Content-Type
- Authorization
- Accept

---

## 📊 レート制限

**Phase 4 (現在)**: なし
**Phase 5 (予定)**:

| エンドポイント | 制限 |
|-------------|------|
| `/api/impact-analysis` | 10 req/分 |
| その他 | 60 req/分 |

---

## 🧪 テスト例

### cURL

```bash
# ヘルスチェック
curl http://localhost:8000/health

# 影響範囲分析
curl -X POST http://localhost:8000/api/impact-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "target_path": "src/main/java/com/example/UserService.java",
    "depth": 3,
    "include_indirect": true
  }'

# 依存関係取得
curl http://localhost:8000/api/dependencies/src/main/java/com/example/UserService.java
```

### JavaScript (Axios)

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 影響範囲分析
const response = await api.post('/api/impact-analysis', {
  target_path: 'src/main/java/com/example/UserService.java',
  depth: 3,
  include_indirect: true
})

console.log(response.data)
```

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        'http://localhost:8000/api/impact-analysis',
        json={
            'target_path': 'src/main/java/com/example/UserService.java',
            'depth': 3,
            'include_indirect': True
        }
    )
    print(response.json())
```

---

## 📚 OpenAPI Specification

完全なOpenAPI 3.0仕様は以下で自動生成されます:

```bash
# FastAPI起動
cd phase4_visualization
python -m uvicorn backend.api.main:app --reload

# OpenAPI JSON取得
curl http://localhost:8000/openapi.json > openapi.json

# Swagger UI
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

---

## 🔧 開発者向け情報

### ローカル開発

```bash
# Backendサーバー起動
cd phase4_visualization
python -m uvicorn backend.api.main:app --reload

# Frontendサーバー起動
cd frontend
npm run dev

# Neo4j起動
docker-compose up neo4j -d
```

### デバッグログ

```bash
# 環境変数でログレベル設定
export LOG_LEVEL=DEBUG
python -m uvicorn backend.api.main:app --reload
```

---

## 📝 変更履歴

### v4.0.0 (2025-10-28)
- ✅ 全エンドポイント実装
- ✅ Neo4j統合
- ✅ CORS設定
- ✅ エラーハンドリング標準化
- ✅ OpenAPI/Swagger対応

---

**作成日**: 2025-10-28 03:00:00 JST (日本標準時)
**担当**: Claude Code
**ステータス**: Week 7-8 実装完了
