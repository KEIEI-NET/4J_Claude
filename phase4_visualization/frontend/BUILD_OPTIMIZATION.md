# Viteビルド最適化ガイド

**最終更新**: 2025-10-28 02:00:00 JST (日本標準時)
**対象**: Phase 4 フロントエンド
**バージョン**: 4.1.0

---

## 📋 概要

このドキュメントでは、Phase 4フロントエンド（React + Vite）のビルド最適化とCode splitting戦略について説明します。

### 最適化目標

| 項目 | 目標値 | 現状 |
|------|--------|------|
| 初回ロード時間 | < 2秒 | TBD |
| バンドルサイズ | < 500KB (gzip) | TBD |
| Lighthouse スコア | > 90 | TBD |
| Code Splitting | 5+チャンク | ✅ 実装済み |
| Tree Shaking | 100% | ✅ 有効 |

---

## 🎯 実装済み最適化

### 1. Code Splitting（コード分割）

**実装方法**: `vite.config.ts` の `manualChunks` 設定

```typescript
manualChunks: {
  // React関連を1つのチャンクに
  'react-vendor': ['react', 'react-dom', 'react-router-dom'],
  // Ant Design関連
  'antd-vendor': ['antd', '@ant-design/icons'],
  // D3.js関連
  'd3-vendor': ['d3', 'd3-force', 'd3-selection', 'd3-zoom', 'd3-drag'],
  // 状態管理・HTTP通信
  'state-vendor': ['zustand', 'axios'],
}
```

**効果**:
- ✅ 初回ロード時のJavaScriptサイズを削減
- ✅ キャッシュヒット率向上（ベンダーコードは変更頻度が低い）
- ✅ 並列ダウンロードによるロード時間短縮

**生成されるチャンク**:
1. `react-vendor-[hash].js` - React core (~150KB)
2. `antd-vendor-[hash].js` - Ant Design (~300KB)
3. `d3-vendor-[hash].js` - D3.js (~200KB)
4. `state-vendor-[hash].js` - Zustand + Axios (~50KB)
5. `index-[hash].js` - アプリケーションコード (~100KB)

---

### 2. Lazy Loading（遅延読み込み）

**実装場所**: `src/App.tsx`

```typescript
// Dashboardコンポーネントの動的インポート
const Dashboard = React.lazy(() =>
  import('@/components/Dashboard/Dashboard').then((module) => ({
    default: module.Dashboard,
  }))
)

// Suspenseでローディング状態を管理
<Suspense fallback={<LoadingFallback />}>
  <Dashboard />
</Suspense>
```

**効果**:
- ✅ 初回ロードに不要なコードを遅延ロード
- ✅ ユーザーがアクセスした時点でロード
- ✅ 初期バンドルサイズの削減

**適用対象**:
- ✅ Dashboard（メインコンポーネント）
- 将来的に追加するルートコンポーネント

---

### 3. Bundle分析

**使用ツール**: rollup-plugin-visualizer

**実行方法**:
```bash
npm run build:analyze
```

**出力**:
- `dist/stats.html` - 視覚的なバンドル分析レポート
- ファイルサイズ（オリジナル、gzip、brotli）を表示
- 依存関係ツリーを可視化

**分析ポイント**:
1. 最大のチャンクを特定
2. 不要な依存関係の検出
3. 重複コードの確認
4. Tree Shakingの効果確認

---

### 4. Minification（最小化）

**設定**: `vite.config.ts`

```typescript
minify: 'terser',
terserOptions: {
  compress: {
    drop_console: true,  // console.log削除
    drop_debugger: true, // debugger削除
  },
},
```

**効果**:
- ✅ JavaScriptファイルサイズの削減（平均30-50%）
- ✅ 本番環境でのデバッグコード除去
- ✅ セキュリティ向上（ソースコードの難読化）

---

### 5. Gzip圧縮

**使用プラグイン**: vite-plugin-compression

**設定**:
```typescript
viteCompression({
  verbose: true,
  disable: false,
  threshold: 10240, // 10KB以上のファイルを圧縮
  algorithm: 'gzip',
  ext: '.gz',
})
```

**効果**:
- ✅ ファイルサイズを平均70%削減
- ✅ 転送時間の短縮
- ✅ 帯域幅の節約

**サーバー側設定**:
Nginxやその他のWebサーバーでgzipファイルを優先的に配信する設定が必要です。

---

### 6. Tree Shaking

**自動有効化**: Vite（Rollup）のデフォルト機能

**効果**:
- ✅ 未使用コードの自動削除
- ✅ ES Modules形式のライブラリで特に効果的
- ✅ バンドルサイズの削減

**確認方法**:
```bash
npm run build
# 警告: "未使用のエクスポート" が表示されないことを確認
```

---

### 7. 依存関係の最適化

**設定**: `vite.config.ts`

```typescript
optimizeDeps: {
  include: ['react', 'react-dom', 'antd', 'd3', 'zustand', 'axios'],
}
```

**効果**:
- ✅ 開発サーバーの起動時間短縮
- ✅ 依存関係の事前バンドル
- ✅ ホットリロードの高速化

---

## 📊 ベンチマーク結果

### ビルドサイズ（予測）

| チャンク | 元サイズ | Gzip | Brotli |
|---------|---------|------|--------|
| react-vendor | 150KB | 50KB | 45KB |
| antd-vendor | 300KB | 100KB | 90KB |
| d3-vendor | 200KB | 70KB | 60KB |
| state-vendor | 50KB | 20KB | 18KB |
| index | 100KB | 35KB | 30KB |
| **合計** | **800KB** | **275KB** | **243KB** |

### ロード時間（予測）

| 接続速度 | 初回ロード | キャッシュ利用時 |
|---------|----------|--------------|
| 4G (10Mbps) | 2.2秒 | 0.5秒 |
| 光回線 (100Mbps) | 0.3秒 | 0.1秒 |
| 5G (100Mbps+) | 0.2秒 | 0.05秒 |

---

## 🚀 ビルドコマンド

### 通常ビルド

```bash
npm run build
```

**出力**:
- `dist/` ディレクトリに最適化済みファイル
- `dist/assets/` にチャンク分割されたJavaScript/CSS
- `dist/*.gz` にGzip圧縮ファイル

### 分析付きビルド

```bash
npm run build:analyze
```

**追加出力**:
- `dist/stats.html` - バンドル分析レポート

### プレビュー

```bash
npm run build
npm run preview
```

**確認事項**:
- ✅ 本番環境と同じビルド成果物をテスト
- ✅ Gzip圧縮の効果確認
- ✅ Code splittingの動作確認

---

## 🔍 パフォーマンス測定

### Lighthouse監査

```bash
# 本番ビルドでサーバー起動
npm run build
npm run preview

# 別ターミナルでLighthouse実行
npx lighthouse http://localhost:4173 --view
```

**目標スコア**:
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 90

### Bundle Analyzer

```bash
npm run build:analyze
```

**確認ポイント**:
1. 最大チャンクサイズ < 300KB
2. 重複ライブラリの有無
3. 未使用コードの検出

---

## 🛠️ トラブルシューティング

### ビルドエラー: "Cannot find module 'rollup-plugin-visualizer'"

**原因**: パッケージ未インストール

**解決方法**:
```bash
npm install --save-dev rollup-plugin-visualizer vite-plugin-compression
```

### ビルドサイズが大きい

**確認事項**:
1. ✅ Tree Shakingが有効か確認
2. ✅ 未使用の依存関係を削除
3. ✅ 画像を最適化（WebP形式など）
4. ✅ アイコンライブラリの使用を最小限に

**コマンド**:
```bash
npm run build:analyze
# stats.htmlで大きなファイルを特定
```

### Lazy Loadingが動作しない

**確認事項**:
1. ✅ `React.lazy()` と `Suspense` の正しい使用
2. ✅ Dynamic importの構文確認
3. ✅ ネットワークタブで分割チャンクの読み込み確認

---

## 📈 今後の最適化

### Phase 1: Route-based Code Splitting（次回実装）

React Routerを使用したルートベースのコード分割:

```typescript
const Home = React.lazy(() => import('./pages/Home'))
const Dashboard = React.lazy(() => import('./pages/Dashboard'))
const Settings = React.lazy(() => import('./pages/Settings'))

<Routes>
  <Route path="/" element={<Suspense fallback={<Loading />}><Home /></Suspense>} />
  <Route path="/dashboard" element={<Suspense fallback={<Loading />}><Dashboard /></Suspense>} />
  <Route path="/settings" element={<Suspense fallback={<Loading />}><Settings /></Suspense>} />
</Routes>
```

### Phase 2: Image Optimization

- WebP形式への変換
- Lazy loading for images
- Responsive images

### Phase 3: PWA対応

- Service Worker追加
- オフライン対応
- アプリキャッシュ

---

## 📚 参考リソース

### 公式ドキュメント

- [Vite Build Optimizations](https://vitejs.dev/guide/build.html)
- [React Code Splitting](https://react.dev/reference/react/lazy)
- [Rollup Manual Chunks](https://rollupjs.org/configuration-options/#output-manualchunks)

### ツール

- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Webpack Bundle Analyzer](https://github.com/webpack-contrib/webpack-bundle-analyzer)
- [Source Map Explorer](https://github.com/danvk/source-map-explorer)

---

## ✅ チェックリスト

ビルド最適化の確認項目:

- [x] Code splitting実装
- [x] Lazy loading実装
- [x] Bundle分析ツール追加
- [x] Minification設定
- [x] Gzip圧縮有効化
- [x] Tree Shaking確認
- [x] 依存関係最適化
- [ ] Lighthouseスコア測定
- [ ] 実環境での負荷テスト
- [ ] CDN配信設定

---

**作成日**: 2025-10-28 02:00:00 JST (日本標準時)
**担当**: Claude Code
**ステータス**: Week 7-8 実装完了
