/**
 * Graph Store (Zustand)
 *
 * グラフデータと影響範囲分析の状態管理
 */

import { create } from 'zustand'
import type {
  GraphNode,
  GraphEdge,
  ImpactAnalysisResponse,
  DependenciesResponse,
  NodeType,
  RiskLevel,
} from '@/types/api'
import { apiClient } from '@/api/client'

interface GraphState {
  // データ
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNode: GraphNode | null
  highlightedNodes: Set<string>
  impactAnalysis: ImpactAnalysisResponse | null
  dependencies: DependenciesResponse | null

  // UI状態
  loading: boolean
  error: string | null

  // アクション
  setNodes: (nodes: GraphNode[]) => void
  setEdges: (edges: GraphEdge[]) => void
  selectNode: (node: GraphNode | null) => void
  highlightNodes: (nodeIds: string[]) => void
  clearHighlight: () => void

  // API呼び出し
  analyzeImpact: (
    targetPath: string,
    depth?: number,
    includeIndirect?: boolean
  ) => Promise<void>
  loadDependencies: (filePath: string) => Promise<void>
  reset: () => void
}

export const useGraphStore = create<GraphState>((set, get) => ({
  // 初期状態
  nodes: [],
  edges: [],
  selectedNode: null,
  highlightedNodes: new Set(),
  impactAnalysis: null,
  dependencies: null,
  loading: false,
  error: null,

  // アクション
  setNodes: (nodes) => set({ nodes }),

  setEdges: (edges) => set({ edges }),

  selectNode: (node) => set({ selectedNode: node }),

  highlightNodes: (nodeIds) => set({ highlightedNodes: new Set(nodeIds) }),

  clearHighlight: () => set({ highlightedNodes: new Set() }),

  // 影響範囲分析
  analyzeImpact: async (targetPath, depth = 3, includeIndirect = true) => {
    set({ loading: true, error: null })

    try {
      const response = await apiClient.analyzeImpact({
        target_type: 'file' as NodeType,
        target_path: targetPath,
        depth,
        include_indirect: includeIndirect,
      })

      // グラフデータを設定
      set({
        impactAnalysis: response,
        nodes: response.dependency_graph.nodes,
        edges: response.dependency_graph.edges,
        loading: false,
      })

      // 影響を受けるファイルをハイライト
      const affectedIds = response.affected_files.map((f) => f.path)
      get().highlightNodes(affectedIds)
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      })
    }
  },

  // 依存関係の読み込み
  loadDependencies: async (filePath) => {
    set({ loading: true, error: null })

    try {
      const response = await apiClient.getDependencies(filePath)

      set({
        dependencies: response,
        loading: false,
      })
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      })
    }
  },

  // リセット
  reset: () =>
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
    }),
}))
