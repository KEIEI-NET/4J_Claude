# 🤖 AI Reproducibility Guide - 4J_Claude プロジェクト

*バージョン: v1.0.0*
*最終更新: 2025年10月27日 08:35 JST*

## 📋 概要

本ガイドは、AIエージェント（Claude、GPT-4、その他のLLM）が4J_Claudeプロジェクトを理解し、開発を継続するための包括的な技術ドキュメントです。すべてのコマンド、ファイルパス、設定は明示的に記載され、曖昧さを排除しています。

---

## 🎯 プロジェクトコンテキスト

### プロジェクト目的
35,000ファイル規模のJavaコードベースを解析し、データベース操作（特にCassandra）のアンチパターンを検出、AIで深層分析し、Neo4jで関係性を可視化するシステムの構築。

### 現在の状態（2025年10月27日）
- **Phase 1-3**: 完了（静的解析、LLM統合、Neo4j統合）
- **Phase 4**: Week 7-8進行中（87.5%完了）
- **焦点**: バックエンド・フロントエンド統合、環境変数管理実装済み

### 作業ディレクトリ
```
C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude
```

---

## 🚀 環境セットアップ手順

### 1. 基本環境要件
```yaml
必須ソフトウェア:
  - Python: 3.11以上
  - Node.js: 18以上
  - Neo4j: 5.x
  - Git: 最新版

推奨IDE:
  - VSCode（拡張機能: Python, TypeScript, Prettier）
```

### 2. プロジェクトクローンと初期設定
```bash
# プロジェクトクローン
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude

# 絶対パスで作業（Windowsの例）
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude
```

### 3. Phase 4 開発環境構築（最新フォーカス）

#### バックエンド設定
```bash
# バックエンドディレクトリへ移動
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\backend

# Python仮想環境作成
python -m venv venv

# 仮想環境有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数ファイル作成
copy .env.example .env.development  # Windows
# cp .env.example .env.development  # Mac/Linux

# .env.developmentを編集
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your-password
# CORS_ALLOWED_ORIGINS=*
# DEBUG=true
```

#### フロントエンド設定
```bash
# フロントエンドディレクトリへ移動
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\frontend

# 依存パッケージインストール
npm install

# 環境変数ファイル作成
copy .env.example .env.development  # Windows
# cp .env.example .env.development  # Mac/Linux

# .env.developmentを編集
# VITE_API_BASE_URL=http://localhost:8000
# VITE_DEBUG_MODE=true
# VITE_API_TIMEOUT=30000
```

### 4. Neo4j データベースセットアップ
```bash
# Neo4j起動確認
neo4j status

# 起動していない場合
neo4j start

# ブラウザでアクセス
# http://localhost:7474
# デフォルト認証: neo4j/neo4j（初回アクセス時にパスワード変更）
```

---

## 🔧 開発サーバー起動手順

### Terminal 1: バックエンド起動
```bash
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\backend
venv\Scripts\activate  # 仮想環境有効化
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 確認URL:
# http://localhost:8000/health
# http://localhost:8000/docs (Swagger UI)
```

### Terminal 2: フロントエンド起動
```bash
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\frontend
npm run dev

# 確認URL:
# http://localhost:5173
```

---

## 📁 重要ファイルと役割

### プロジェクトルート
```
C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\
├── README.md                  # プロジェクト全体概要（v4.0.1）
├── DOCUMENTATION_INDEX.md     # ドキュメント索引（v4.0.0）
├── ARCHITECTURE_OVERVIEW.md   # システムアーキテクチャ（v1.0.0）
├── AI_REPRODUCIBILITY_GUIDE.md # このファイル
└── phase4_visualization/      # 現在の作業フォーカス
```

### Phase 4 重要ファイル
```
phase4_visualization/
├── backend/
│   ├── api/main.py           # FastAPIメインアプリケーション
│   ├── config/settings.py    # pydantic-settings環境変数管理
│   ├── services/             # ビジネスロジック実装
│   └── .env.development      # 開発環境変数（Git管理外）
├── frontend/
│   ├── src/api/client.ts     # APIクライアント実装
│   ├── src/env.d.ts          # TypeScript環境変数型定義
│   └── .env.development      # 開発環境変数（Git管理外）
└── scripts/
    └── test_api_integration.py # API統合テストスクリプト
```

---

## 🧪 テスト実行手順

### 1. API統合テスト
```bash
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization
python scripts\test_api_integration.py

# 期待される出力:
# ✓ Health Check: PASSED
# ✓ Impact Analysis: PASSED
# ✓ Dependencies: PASSED
# ✓ Circular Dependencies: PASSED
# ✓ CORS Configuration: PASSED
```

### 2. フロントエンドユニットテスト
```bash
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\frontend
npm run test

# 期待される結果: 67テスト全通過
```

### 3. E2Eテスト
```bash
cd C:\Users\kenji\Dropbox\AI開発\dev\Tools\4J\Claude\phase4_visualization\frontend
npm run test:e2e

# 期待される結果: 18テスト全通過
```

---

## 🔍 トラブルシューティング

### 問題1: Neo4j接続エラー
```bash
# エラー: Unable to connect to Neo4j
# 解決策:
neo4j status  # ステータス確認
neo4j start   # 起動
# .env.developmentのNEO4J_PASSWORDを確認
```

### 問題2: CORS エラー
```bash
# エラー: CORS policy blocked
# 解決策:
# backend/.env.developmentを確認
# CORS_ALLOWED_ORIGINS=* （開発環境）
# FastAPIを再起動
```

### 問題3: ポート競合
```bash
# エラー: Port already in use
# 解決策:
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>
```

---

## 📝 コード変更時の手順

### 1. バックエンドAPI追加
```python
# backend/api/main.pyに新エンドポイント追加
@app.post("/api/new-endpoint")
async def new_endpoint(request: RequestModel) -> ResponseModel:
    """
    新しいエンドポイントの説明
    """
    # 実装
    return response
```

### 2. フロントエンドコンポーネント追加
```typescript
// frontend/src/components/NewComponent.tsx
import React from 'react';

export const NewComponent: React.FC = () => {
    // 実装
    return <div>New Component</div>;
};
```

### 3. 環境変数追加
```bash
# 1. .env.exampleに追加
NEW_VARIABLE=default_value

# 2. .env.developmentに追加
NEW_VARIABLE=development_value

# 3. コードで使用
# Backend: settings.NEW_VARIABLE
# Frontend: import.meta.env.VITE_NEW_VARIABLE
```

---

## 🚀 デプロイメント手順（Week 8予定）

### 1. ビルド
```bash
# フロントエンドビルド
cd frontend
npm run build  # dist/フォルダに出力

# バックエンドは直接実行
```

### 2. Docker化（計画中）
```dockerfile
# Dockerfile例
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

### 3. 本番環境変数
```bash
# .env.productionを使用
cp .env.example .env.production
# 本番用の値を設定
# DEBUG=false
# CORS_ALLOWED_ORIGINS=https://your-domain.com
```

---

## 📊 プロジェクト状態の確認方法

### 1. 進捗確認
```bash
# README.mdの進捗セクション参照
grep "Phase 4" README.md

# TODOリスト確認
grep "Week 7-8" phase4_visualization/WEEK7_8_INTEGRATION_REPORT.md
```

### 2. テストカバレッジ確認
```bash
# Backend
cd backend
pytest --cov=. --cov-report=html

# Frontend
cd frontend
npm run test:coverage
```

### 3. ログ確認
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend console
# ブラウザのDevTools → Console
```

---

## 🎯 Week 8 残タスク（AIが継続すべき作業）

### 優先度高
1. **E2Eテスト実データ検証**
   - Neo4jにサンプルデータ投入
   - 実際の影響分析シナリオテスト

2. **Viteビルド最適化**
   ```javascript
   // vite.config.ts
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           'react-vendor': ['react', 'react-dom'],
           'd3-vendor': ['d3']
         }
       }
     }
   }
   ```

3. **Docker化**
   - Dockerfile作成（frontend/backend）
   - docker-compose.yml作成
   - マルチステージビルド実装

### 優先度中
4. **CI/CD設定**
   - .github/workflows/ci.yml作成
   - 自動テスト設定
   - デプロイメント自動化

5. **ドキュメント完成**
   - API仕様書（OpenAPI）
   - 運用ガイド作成

---

## 🔄 継続的な更新が必要な項目

### 毎日更新
- phase4_visualization/README.mdの進捗状況
- テスト結果とカバレッジ

### 週次更新
- WEEK*_COMPLETION_REPORT.md作成
- DOCUMENTATION_INDEX.md更新
- メインREADME.mdの進捗率

### リリース時更新
- CHANGELOG.md
- バージョン番号（全ドキュメント）
- 本番環境設定

---

## 🤝 AI間の引き継ぎプロトコル

### セッション開始時
1. このガイドを最初に読む
2. `git status`で現在の変更を確認
3. 最新のWEEKレポートを読む
4. テストを実行して現状確認

### セッション終了時
1. 変更内容をコミット
2. ドキュメント更新（バージョン、日時）
3. 残タスクを明確に記載
4. 次のAIへの引き継ぎメモ作成

### エラー発生時
1. エラーメッセージを完全に記録
2. 試した解決策を文書化
3. 回避策があれば実装
4. 根本解決は次のセッションへ

---

## 📌 重要な規約とルール

### コーディング規約
- Python: PEP 8準拠、型ヒント必須
- TypeScript: ESLint/Prettier設定に従う
- コミットメッセージ: Conventional Commits形式

### ドキュメント規約
- 日時: 日本標準時（JST）で記載
- バージョン: セマンティックバージョニング
- 更新履歴: 必ず記載

### セキュリティ規約
- 機密情報はenvファイルのみ
- .gitignoreで確実に除外
- APIキーはハードコード禁止

---

## 🎓 学習リソース

### プロジェクト理解
1. DETAILED_DESIGN.md - アーキテクチャ全体像
2. phase*/README.md - 各フェーズ詳細
3. WEEK*_REPORT.md - 実装履歴

### 技術スタック学習
- FastAPI: https://fastapi.tiangolo.com/
- Neo4j: https://neo4j.com/docs/
- React: https://react.dev/
- D3.js: https://d3js.org/

---

*最終更新: 2025年10月27日 08:35 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年10月27日): 初版作成、Phase 4 Week 7-8の状況を反映、完全なAI再現性ガイド