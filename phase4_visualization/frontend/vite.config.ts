import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import viteCompression from 'vite-plugin-compression'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Bundle分析（npm run build時のみ有効化）
    visualizer({
      filename: './dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }) as any,
    // Gzip圧縮
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240, // 10KB以上のファイルを圧縮
      algorithm: 'gzip',
      ext: '.gz',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // ビルド最適化設定
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // 本番環境ではfalse
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // console.log削除
        drop_debugger: true,
      },
    },
    // Code Splitting設定
    rollupOptions: {
      output: {
        manualChunks: {
          // React関連を1つのチャンクに
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Ant Design関連
          'antd-vendor': ['antd', '@ant-design/icons'],
          // D3.js関連
          'd3-vendor': ['d3', 'd3-force', 'd3-selection', 'd3-zoom', 'd3-drag'],
          // 状態管理・HTTP通信
          'state-vendor': ['zustand', 'axios'],
        },
        // ファイル名の最適化
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // チャンクサイズ警告の閾値
    chunkSizeWarningLimit: 1000, // 1MB
  },
  // 最適化設定
  optimizeDeps: {
    include: ['react', 'react-dom', 'antd', 'd3', 'zustand', 'axios'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
