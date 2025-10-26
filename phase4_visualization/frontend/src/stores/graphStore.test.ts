/**
 * Graph Store Tests
 *
 * Zustand状態管理のテスト
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useGraphStore } from './graphStore'
import { apiClient } from '@/api/client'
import { mockNodes, mockEdges, mockImpactAnalysisResponse } from '@/test/mockData'

vi.mock('@/api/client')

describe('GraphStore', () => {
  beforeEach(() => {
    // ストアをリセット
    const { reset } = useGraphStore.getState()
    reset()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useGraphStore())

      expect(result.current.nodes).toEqual([])
      expect(result.current.edges).toEqual([])
      expect(result.current.selectedNode).toBeNull()
      expect(result.current.highlightedNodes).toEqual(new Set())
      expect(result.current.impactAnalysis).toBeNull()
      expect(result.current.dependencies).toBeNull()
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBeNull()
    })
  })

  describe('setNodes', () => {
    it('should set nodes', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.setNodes(mockNodes)
      })

      expect(result.current.nodes).toEqual(mockNodes)
      expect(result.current.nodes).toHaveLength(3)
    })
  })

  describe('setEdges', () => {
    it('should set edges', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.setEdges(mockEdges)
      })

      expect(result.current.edges).toEqual(mockEdges)
      expect(result.current.edges).toHaveLength(2)
    })
  })

  describe('selectNode', () => {
    it('should select a node', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.selectNode(mockNodes[0])
      })

      expect(result.current.selectedNode).toEqual(mockNodes[0])
    })

    it('should deselect node when null is passed', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.selectNode(mockNodes[0])
        result.current.selectNode(null)
      })

      expect(result.current.selectedNode).toBeNull()
    })
  })

  describe('highlightNodes', () => {
    it('should highlight nodes', () => {
      const { result } = renderHook(() => useGraphStore())
      const nodeIds = ['node1', 'node2', 'node3']

      act(() => {
        result.current.highlightNodes(nodeIds)
      })

      expect(result.current.highlightedNodes).toEqual(new Set(nodeIds))
      expect(result.current.highlightedNodes.size).toBe(3)
    })

    it('should replace previous highlights', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.highlightNodes(['node1', 'node2'])
        result.current.highlightNodes(['node3', 'node4'])
      })

      expect(result.current.highlightedNodes).toEqual(new Set(['node3', 'node4']))
      expect(result.current.highlightedNodes.size).toBe(2)
    })
  })

  describe('clearHighlight', () => {
    it('should clear all highlights', () => {
      const { result } = renderHook(() => useGraphStore())

      act(() => {
        result.current.highlightNodes(['node1', 'node2'])
        result.current.clearHighlight()
      })

      expect(result.current.highlightedNodes).toEqual(new Set())
      expect(result.current.highlightedNodes.size).toBe(0)
    })
  })

  describe('analyzeImpact', () => {
    it('should successfully analyze impact', async () => {
      vi.mocked(apiClient.analyzeImpact).mockResolvedValue(mockImpactAnalysisResponse)

      const { result } = renderHook(() => useGraphStore())

      expect(result.current.loading).toBe(false)

      await act(async () => {
        await result.current.analyzeImpact('src/main/java/com/example/User.java', 3, true)
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.impactAnalysis).toEqual(mockImpactAnalysisResponse)
      expect(result.current.nodes).toEqual(mockImpactAnalysisResponse.dependency_graph.nodes)
      expect(result.current.edges).toEqual(mockImpactAnalysisResponse.dependency_graph.edges)
      expect(result.current.highlightedNodes.size).toBe(3)
      expect(result.current.error).toBeNull()
    })

    it('should set loading state during analysis', async () => {
      vi.mocked(apiClient.analyzeImpact).mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve(mockImpactAnalysisResponse), 100)
          })
      )

      const { result } = renderHook(() => useGraphStore())

      const promise = act(async () => {
        await result.current.analyzeImpact('src/main/java/com/example/User.java')
      })

      // 実行中はloadingがtrue
      await waitFor(() => {
        expect(result.current.loading).toBe(true)
      })

      await promise

      // 完了後はloadingがfalse
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle errors', async () => {
      const errorMessage = 'Network error'
      vi.mocked(apiClient.analyzeImpact).mockRejectedValue(new Error(errorMessage))

      const { result } = renderHook(() => useGraphStore())

      await act(async () => {
        await result.current.analyzeImpact('invalid/path.java')
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.impactAnalysis).toBeNull()
    })

    it('should use default parameters', async () => {
      vi.mocked(apiClient.analyzeImpact).mockResolvedValue(mockImpactAnalysisResponse)

      const { result } = renderHook(() => useGraphStore())

      await act(async () => {
        await result.current.analyzeImpact('src/main/java/com/example/User.java')
      })

      expect(apiClient.analyzeImpact).toHaveBeenCalledWith({
        target_type: 'file',
        target_path: 'src/main/java/com/example/User.java',
        depth: 3,
        include_indirect: true,
      })
    })
  })

  describe('loadDependencies', () => {
    it('should successfully load dependencies', async () => {
      const mockDepsResponse = {
        file: {
          type: 'file',
          path: 'src/main/java/com/example/User.java',
          name: 'User.java',
          language: 'Java',
        },
        dependencies: {
          imports: ['java.util.List'],
          dependents: ['UserService.java'],
          dependency_count: 1,
          dependent_count: 1,
        },
        methods: [],
      }

      vi.mocked(apiClient.getDependencies).mockResolvedValue(mockDepsResponse)

      const { result } = renderHook(() => useGraphStore())

      await act(async () => {
        await result.current.loadDependencies('src/main/java/com/example/User.java')
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.dependencies).toEqual(mockDepsResponse)
      expect(result.current.error).toBeNull()
    })

    it('should handle errors when loading dependencies', async () => {
      const errorMessage = 'File not found'
      vi.mocked(apiClient.getDependencies).mockRejectedValue(new Error(errorMessage))

      const { result } = renderHook(() => useGraphStore())

      await act(async () => {
        await result.current.loadDependencies('invalid/path.java')
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.dependencies).toBeNull()
    })
  })

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      const { result } = renderHook(() => useGraphStore())

      // 状態を変更
      act(() => {
        result.current.setNodes(mockNodes)
        result.current.setEdges(mockEdges)
        result.current.selectNode(mockNodes[0])
        result.current.highlightNodes(['node1', 'node2'])
      })

      // リセット
      act(() => {
        result.current.reset()
      })

      // 初期状態に戻ることを確認
      expect(result.current.nodes).toEqual([])
      expect(result.current.edges).toEqual([])
      expect(result.current.selectedNode).toBeNull()
      expect(result.current.highlightedNodes).toEqual(new Set())
      expect(result.current.impactAnalysis).toBeNull()
      expect(result.current.dependencies).toBeNull()
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBeNull()
    })
  })
})
