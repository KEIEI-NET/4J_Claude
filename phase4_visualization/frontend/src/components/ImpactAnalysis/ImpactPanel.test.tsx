/**
 * ImpactPanel Component Tests
 *
 * 影響範囲分析パネルのテスト
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/utils'
import { ImpactPanel } from './ImpactPanel'
import { useGraphStore } from '@/stores/graphStore'
import { mockImpactAnalysisResponse } from '@/test/mockData'

vi.mock('@/stores/graphStore')

describe('ImpactPanel', () => {
  const mockAnalyzeImpact = vi.fn()
  const mockOnFileSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: null,
      loading: false,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })
  })

  it('should render search input', () => {
    render(<ImpactPanel />)

    const searchInput = screen.getByPlaceholderText(/ファイルパスを入力/)
    expect(searchInput).toBeInTheDocument()
  })

  it('should render analyze button', () => {
    render(<ImpactPanel />)

    const button = screen.getByRole('button', { name: /分析/ })
    expect(button).toBeInTheDocument()
  })

  it('should update input value on change', () => {
    render(<ImpactPanel />)

    const input = screen.getByPlaceholderText(/ファイルパスを入力/) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'src/main/java/com/example/User.java' } })

    expect(input.value).toBe('src/main/java/com/example/User.java')
  })

  it('should call analyzeImpact when search button is clicked', async () => {
    render(<ImpactPanel />)

    const input = screen.getByPlaceholderText(/ファイルパスを入力/)
    fireEvent.change(input, { target: { value: 'src/main/java/com/example/User.java' } })

    const button = screen.getByRole('button', { name: /分析/ })
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockAnalyzeImpact).toHaveBeenCalledWith(
        'src/main/java/com/example/User.java',
        3,
        true
      )
    })
  })

  it('should not call analyzeImpact when input is empty', async () => {
    render(<ImpactPanel />)

    const button = screen.getByRole('button', { name: /分析/ })
    fireEvent.click(button)

    expect(mockAnalyzeImpact).not.toHaveBeenCalled()
  })

  it('should render depth selector', () => {
    render(<ImpactPanel />)

    const depthLabel = screen.getByText(/探索深さ:/)
    expect(depthLabel).toBeInTheDocument()
  })

  it('should render indirect dependency checkbox', () => {
    render(<ImpactPanel />)

    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeInTheDocument()
    expect(checkbox).toBeChecked()
  })

  it('should toggle indirect dependency checkbox', () => {
    render(<ImpactPanel />)

    const checkbox = screen.getByRole('checkbox') as HTMLInputElement
    expect(checkbox.checked).toBe(true)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(false)

    fireEvent.click(checkbox)
    expect(checkbox.checked).toBe(true)
  })

  it('should show loading state', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: null,
      loading: true,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel />)

    expect(screen.getByText(/影響範囲を分析中.../)).toBeInTheDocument()
  })

  it('should show error message', () => {
    const errorMessage = 'Network error'

    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: null,
      loading: false,
      error: errorMessage,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel />)

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('should display analysis results', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: mockImpactAnalysisResponse,
      loading: false,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel />)

    expect(screen.getByText(/分析サマリー/)).toBeInTheDocument()
    expect(screen.getByText(/影響を受けるファイル一覧/)).toBeInTheDocument()
  })

  it('should display correct statistics in summary', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: mockImpactAnalysisResponse,
      loading: false,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel />)

    expect(screen.getByText(/影響を受けるファイル/)).toBeInTheDocument()
    expect(screen.getByText(/影響を受けるメソッド/)).toBeInTheDocument()
    expect(screen.getByText(/影響を受けるクラス/)).toBeInTheDocument()
  })

  it('should call onFileSelect when file is clicked', async () => {
    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: mockImpactAnalysisResponse,
      loading: false,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel onFileSelect={mockOnFileSelect} />)

    const fileButton = screen.getByText('UserService.java')
    fireEvent.click(fileButton)

    expect(mockOnFileSelect).toHaveBeenCalledWith('src/main/java/com/example/UserService.java')
  })

  it('should display risk level badge', () => {
    vi.mocked(useGraphStore).mockReturnValue({
      impactAnalysis: mockImpactAnalysisResponse,
      loading: false,
      error: null,
      analyzeImpact: mockAnalyzeImpact,
      nodes: [],
      edges: [],
      selectedNode: null,
      highlightedNodes: new Set(),
      dependencies: null,
      setNodes: vi.fn(),
      setEdges: vi.fn(),
      selectNode: vi.fn(),
      highlightNodes: vi.fn(),
      clearHighlight: vi.fn(),
      loadDependencies: vi.fn(),
      reset: vi.fn(),
    })

    render(<ImpactPanel />)

    expect(screen.getByText(/MEDIUM/)).toBeInTheDocument()
  })
})
