/**
 * Dashboard Component Tests
 *
 * ダッシュボード統合コンポーネントのテスト
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@/test/utils'
import { Dashboard } from './Dashboard'
import { useGraphStore } from '@/stores/graphStore'
import { mockNodes, mockEdges, mockImpactAnalysisResponse } from '@/test/mockData'

vi.mock('@/stores/graphStore')
vi.mock('@/components/GraphView/GraphView', () => ({
  GraphView: () => <div data-testid="mock-graph-view">Mock GraphView</div>,
}))
vi.mock('@/components/ImpactAnalysis/ImpactPanel', () => ({
  ImpactPanel: () => <div data-testid="mock-impact-panel">Mock ImpactPanel</div>,
}))
vi.mock('@/components/FileExplorer/FileSearch', () => ({
  FileSearch: () => <div data-testid="mock-file-search">Mock FileSearch</div>,
}))

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useGraphStore).mockReturnValue({
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })
  })

  it('should render header with title', () => {
    render(<Dashboard />)

    expect(screen.getByText('Code Relationship Analyzer')).toBeInTheDocument()
  })

  it('should render node and edge counts in header', () => {
    render(<Dashboard />)

    expect(screen.getByText(/ノード数:/)).toBeInTheDocument()
    expect(screen.getByText(/エッジ数:/)).toBeInTheDocument()
  })

  it('should display correct node count', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByText(/ノード数: 3/)).toBeInTheDocument()
  })

  it('should display correct edge count', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByText(/エッジ数: 2/)).toBeInTheDocument()
  })

  it('should render sidebar with tabs', () => {
    render(<Dashboard />)

    expect(screen.getByText('影響範囲分析')).toBeInTheDocument()
    expect(screen.getByText('ファイル検索')).toBeInTheDocument()
    expect(screen.getByText('設定')).toBeInTheDocument()
  })

  it('should render ImpactPanel in default tab', () => {
    render(<Dashboard />)

    expect(screen.getByTestId('mock-impact-panel')).toBeInTheDocument()
  })

  it('should show empty state when no nodes', () => {
    render(<Dashboard />)

    expect(screen.getByText('影響範囲分析を実行してください')).toBeInTheDocument()
    expect(
      screen.getByText('左側のパネルからファイルを選択し、影響範囲分析を開始します。')
    ).toBeInTheDocument()
  })

  it('should render GraphView when nodes exist', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByTestId('mock-graph-view')).toBeInTheDocument()
    expect(screen.queryByText('影響範囲分析を実行してください')).not.toBeInTheDocument()
  })

  it('should display selected node info when a node is selected', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: mockNodes[0],
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByText('選択中:')).toBeInTheDocument()
    expect(screen.getByText('User.java')).toBeInTheDocument()
  })

  it('should display complexity for selected node', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: mockNodes[0],
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByText(/複雑度:/)).toBeInTheDocument()
  })

  it('should have correct layout structure', () => {
    const { container } = render(<Dashboard />)

    expect(container.querySelector('.dashboard')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-header')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-sider')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-content')).toBeInTheDocument()
  })

  it('should render graph header when nodes exist', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedNode: null,
      highlightedNodes: new Set(),
      impactAnalysis: null,
      dependencies: null,
      loading: false,
      error: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      analyzeImpact: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<Dashboard />)

    expect(screen.getByText('依存関係グラフ')).toBeInTheDocument()
  })
})
