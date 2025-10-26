/// <reference types="vite/client" />

/**
 * 環境変数の型定義
 * Vite環境変数はimport.meta.envを通してアクセス可能
 */
interface ImportMetaEnv {
  /** Backend API Base URL (例: http://localhost:8000) */
  readonly VITE_API_BASE_URL: string

  /** API Request Timeout (milliseconds) */
  readonly VITE_API_TIMEOUT: string

  /** Debug Mode Flag */
  readonly VITE_DEBUG_MODE: string

  /** 循環依存チェック機能の有効化 */
  readonly VITE_ENABLE_CIRCULAR_DEPENDENCY_CHECK: string

  /** リファクタリングリスク評価機能の有効化 */
  readonly VITE_ENABLE_REFACTORING_RISK_ASSESSMENT: string

  /** デフォルトのグラフ探索深さ */
  readonly VITE_DEFAULT_GRAPH_DEPTH: string

  /** 最大グラフ探索深さ */
  readonly VITE_MAX_GRAPH_DEPTH: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
