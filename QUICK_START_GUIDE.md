# 🚀 クイックスタートガイド - 5分で始める4J_Claude

*バージョン: v6.0.0*
*最終更新: 2025年01月29日 16:21 JST*

このガイドでは、4J_Claudeプロジェクトを**5分以内**に動作させる最短手順を説明します。

---

## 📋 前提条件

### 必須ソフトウェア
- **Python 3.11+**
- **Node.js 18+** & npm 9+
- **Docker Desktop**
- **Git**

### 推奨スペック
- CPU: 4コア以上
- RAM: 8GB以上
- ストレージ: 10GB以上の空き容量

---

## ⚡ 最速セットアップ（3ステップ）

### ステップ 1: クローンと環境変数設定（1分）

```bash
# リポジトリをクローン
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude

# 環境変数ファイルをコピー
cp .env.example .env

# .envファイルを編集（最低限必要な設定）
# JWT_SECRET_KEY=your-32-character-secret-key-here
# NEO4J_PASSWORD=your-secure-password-here
```

### ステップ 2: Dockerで全サービス起動（3分）

```bash
# Neo4jとアプリケーションを起動
docker-compose up -d

# 監視スタックも起動する場合（オプション）
docker-compose -f docker-compose.monitoring.yml up -d
```

### ステップ 3: ブラウザでアクセス（1分）

以下のURLにアクセス:

- **アプリケーション**: http://localhost:3000
- **API ドキュメント**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Grafana** (監視): http://localhost:3001

デフォルトログイン情報:
- **ユーザー**: admin@example.com
- **パスワード**: admin123

---

## 🎯 動作確認

### 1. API ヘルスチェック

```bash
curl http://localhost:8000/health
```

期待される応答:
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "timestamp": "2025-01-29T16:21:00Z"
}
```

### 2. 認証テスト

```bash
# ログイン
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# レスポンスからaccess_tokenをコピー
```

### 3. 影響範囲分析テスト

```bash
# トークンを使用してAPI呼び出し
curl -X POST http://localhost:8000/api/impact-analysis \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "src/main.py", "change_type": "modification"}'
```

---

## 🔧 ローカル開発環境（詳細版）

### バックエンド起動

```bash
cd phase4_visualization/backend

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn api.main:app --reload --port 8000
```

### フロントエンド起動

```bash
cd phase4_visualization/frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

### Neo4j起動（Dockerなし）

```bash
# Neo4j Desktopをダウンロード
# https://neo4j.com/download/

# 新しいプロジェクト作成
# Database作成（バージョン5.x）
# パスワード設定
# Start ボタンをクリック
```

---

## 📊 サンプルデータ投入

### 1. テストデータ生成

```bash
cd phase4_visualization/scripts
python generate_test_data.py
```

### 2. Neo4jへのインポート

```bash
# Cypherクエリ実行
cd phase4_visualization
cat QUICK_START_QUERIES.cypher | docker exec -i neo4j cypher-shell -u neo4j -p password
```

### 3. 確認

ブラウザで http://localhost:3000 にアクセスし、グラフ表示を確認。

---

## 🧪 テスト実行

### バックエンドテスト

```bash
cd phase4_visualization
pytest backend/tests/ -v

# カバレッジレポート付き
pytest backend/tests/ --cov=backend --cov-report=html
```

### フロントエンドテスト

```bash
cd phase4_visualization/frontend
npm test           # ユニットテスト
npm run test:e2e   # E2Eテスト
```

---

## 🐛 トラブルシューティング

### ポート競合エラー

```bash
# 使用中のポート確認
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# docker-compose.ymlでポート変更
# ports:
#   - "8001:8000"  # 8001に変更
```

### Neo4j接続エラー

```bash
# Neo4jステータス確認
docker ps | grep neo4j

# ログ確認
docker logs neo4j

# 再起動
docker restart neo4j
```

### 認証エラー

```bash
# JWT_SECRET_KEYが設定されているか確認
echo $JWT_SECRET_KEY

# 最低32文字以上の文字列に設定
export JWT_SECRET_KEY="your-very-long-secret-key-minimum-32-chars"
```

---

## 📚 次のステップ

### 基本的な使い方

1. **影響範囲分析を試す**
   - ファイルを選択
   - 「Analyze Impact」ボタンをクリック
   - 影響を受けるファイルが赤でハイライト

2. **依存関係を探索**
   - グラフ上のノードをクリック
   - 依存先/依存元が表示される
   - ダブルクリックで詳細表示

3. **カスタムクエリ実行**
   - Neo4j Browser (http://localhost:7474)
   - サンプルクエリ実行
   ```cypher
   MATCH (n:File)-[:DEPENDS_ON]->(m:File)
   WHERE n.path CONTAINS 'main'
   RETURN n, m LIMIT 50
   ```

### 詳細ドキュメント

- **[README.md](./README.md)** - プロジェクト概要
- **[MASTER_DOCUMENTATION_INDEX.md](./MASTER_DOCUMENTATION_INDEX.md)** - 全ドキュメント索引
- **[phase4_visualization/API_SPECIFICATION.md](./phase4_visualization/API_SPECIFICATION.md)** - API仕様
- **[phase4_visualization/AUTHENTICATION_GUIDE.md](./phase4_visualization/AUTHENTICATION_GUIDE.md)** - 認証ガイド

---

## 🆘 ヘルプ・サポート

### よくある質問

**Q: データが表示されない**
A: サンプルデータを投入したか確認してください。`scripts/generate_test_data.py`を実行。

**Q: ログインできない**
A: デフォルトユーザーが作成されているか確認。`docker exec -it backend python scripts/create_admin.py`

**Q: グラフが重い**
A: 表示ノード数を制限。設定で「Max Nodes」を50以下に設定。

### コミュニティ

- GitHub Issues: バグ報告・機能要望
- Discussions: 質問・議論
- Wiki: 追加ドキュメント

---

*最終更新: 2025年01月29日 16:21 JST*
*バージョン: v6.0.0*

**更新履歴:**
- v6.0.0 (2025年01月29日): 初版作成、5分セットアップガイド