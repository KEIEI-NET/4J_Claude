# Code Relationship Analyzer - Frontend

Phase 4の可視化レイヤーフロントエンド実装です。

## 🚀 クイックスタート

### 前提条件

- Node.js 18以上
- npm 9以上

### インストール

```bash
npm install
```

### 環境変数設定

`.env.example` をコピーして `.env.development` を作成:

```bash
cp .env.example .env.development
```

`.env.development` を編集してバックエンドAPIのURLを設定:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_DEBUG_MODE=true
```

**重要**: 本番環境では `.env.production` を作成し、適切なURLを設定してください。

### 開発サーバー起動

```bash
npm run dev
```

開発サーバーが http://localhost:5173 で起動します。

### ビルド

```bash
npm run build
```

### プレビュー

```bash
npm run preview
```

## 📁 プロジェクト構造

```
frontend/
├── src/
│   ├── components/      # Reactコンポーネント
│   │   ├── Dashboard/   # メインダッシュボード
│   │   ├── GraphView/   # D3.jsグラフ可視化
│   │   ├── ImpactAnalysis/  # 影響範囲分析パネル
│   │   └── FileExplorer/    # ファイル検索
│   ├── stores/          # Zustand状態管理
│   ├── api/            # APIクライアント
│   └── types/          # TypeScript型定義
├── index.html          # HTMLテンプレート
├── package.json        # 依存関係
└── vite.config.ts      # Vite設定
```

## 🎨 主要機能

### 1. グラフ可視化 (GraphView)

- D3.js Force-directed レイアウト
- ズーム・パン機能
- ノードドラッグ操作
- ツールチップ表示
- ノードハイライト

### 2. 影響範囲分析 (ImpactPanel)

- ファイルパス検索
- 探索深さ設定
- 影響ファイル一覧表示
- リスクレベル評価
- 詳細テーブル表示

### 3. ファイル検索 (FileSearch)

- インクリメンタル検索
- 最近の検索履歴
- ファイル一覧表示
- 統計情報表示

### 4. ダッシュボード統合 (Dashboard)

- レスポンシブレイアウト
- タブ切り替え
- コンポーネント連携
- リアルタイム更新

## 🔧 技術スタック

### コア技術

- **React 18.2** - UIライブラリ
- **TypeScript 5.3** - 型安全な開発
- **Vite 5.0** - 高速ビルドツール

### UI/可視化

- **Ant Design 5.12** - UIコンポーネント
- **D3.js 7.8** - グラフ可視化
- **@ant-design/icons** - アイコンライブラリ

### 状態管理/通信

- **Zustand 4.5** - 軽量な状態管理
- **Axios 1.6** - HTTP通信

### 開発ツール

- **Vitest** - テストフレームワーク
- **ESLint** - コードリンター
- **TypeScript** - 型チェック

## 🎯 API統合

### バックエンドAPI

APIのベースURLは環境変数で設定します。`.env.development` または `.env.production` で設定:

```env
VITE_API_BASE_URL=http://localhost:8000  # バックエンドAPIのURL
VITE_API_TIMEOUT=30000                   # タイムアウト (ms)
VITE_DEBUG_MODE=true                     # デバッグログ有効化
```

**環境変数設定方法**:

1. `.env.example` をコピーして `.env.development` を作成
2. 必要に応じて値を変更
3. 本番環境では `.env.production` を別途作成

プログラムから直接URLを指定する場合（非推奨）:

```typescript
const apiClient = new APIClient('http://your-backend-url')
```

### 利用可能なAPI

1. `/api/impact-analysis` - 影響範囲分析
2. `/api/dependencies/:path` - 依存関係取得
3. `/api/path-finder` - パス検索
4. `/api/circular-dependencies` - 循環依存検出
5. `/health` - ヘルスチェック

## 📊 コンポーネントAPI

### GraphView

```tsx
<GraphView
  nodes={nodes}
  edges={edges}
  highlightedNodes={highlightedNodes}
  onNodeClick={(node) => console.log(node)}
  width={1200}
  height={800}
/>
```

### ImpactPanel

```tsx
<ImpactPanel
  onFileSelect={(filePath) => console.log(filePath)}
/>
```

### FileSearch

```tsx
<FileSearch
  onFileSelect={(filePath) => console.log(filePath)}
/>
```

## 🔄 状態管理

Zustandストアを使用:

```typescript
import { useGraphStore } from '@/stores/graphStore'

const Component = () => {
  const { nodes, edges, analyzeImpact } = useGraphStore()

  const handleAnalyze = async () => {
    await analyzeImpact('path/to/file.java', 3, true)
  }

  return <div>{nodes.length} nodes</div>
}
```

## 🧪 テスト (Week 5-6で実装予定)

```bash
npm run test        # テスト実行
npm run test:ui     # テストUIで実行
npm run coverage    # カバレッジレポート
```

## 📦 ビルド成果物

```bash
npm run build
```

`dist/` ディレクトリに以下が生成されます:

- `index.html` - エントリーポイント
- `assets/` - JavaScript/CSSバンドル
- `vite.svg` - アイコン

## 🎨 カスタマイズ

### テーマ変更

`src/App.tsx` のConfigProviderを編集:

```typescript
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',  // プライマリカラー
      borderRadius: 4,          // 角丸半径
      fontSize: 14,             // フォントサイズ
    },
  }}
>
```

### グラフレイアウト調整

`src/components/GraphView/GraphView.tsx` のforce設定を編集:

```typescript
.force('link', d3.forceLink().distance(150))    // リンク距離
.force('charge', d3.forceManyBody().strength(-400))  // 反発力
.force('collision', d3.forceCollide().radius(40))    // 衝突半径
```

## 📚 追加リソース

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [D3.js Documentation](https://d3js.org/)
- [Ant Design Documentation](https://ant.design/)
- [Zustand Documentation](https://github.com/pmndrs/zustand)

## 🐛 トラブルシューティング

### ポート競合

開発サーバーのポートを変更:

```bash
npm run dev -- --port 3000
```

### ビルドエラー

キャッシュをクリア:

```bash
rm -rf node_modules dist
npm install
npm run build
```

### 型エラー

TypeScript設定を確認:

```bash
npx tsc --noEmit
```

## 📄 ライセンス

このプロジェクトは4Jツールの一部です。

---

**作成日**: 2025-10-27 23:45:00 JST (日本標準時)
**バージョン**: 1.0.0
**ステータス**: Week 3-4 完了 ✅
