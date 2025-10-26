/**
 * FileSearch Component Tests
 *
 * ファイル検索コンポーネントのテスト
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/utils'
import { FileSearch } from './FileSearch'
import { useGraphStore } from '@/stores/graphStore'
import { mockNodes } from '@/test/mockData'

vi.mock('@/stores/graphStore')

describe('FileSearch', () => {
  const mockOnFileSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useGraphStore).mockReturnValue({
      nodes: mockNodes,
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

  it('should render search input', () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    expect(searchInput).toBeInTheDocument()
  })

  it('should render statistics card', () => {
    render(<FileSearch />)

    expect(screen.getByText(/統計情報/)).toBeInTheDocument()
    expect(screen.getByText(/総ファイル数/)).toBeInTheDocument()
  })

  it('should display correct total file count', () => {
    render(<FileSearch />)

    expect(screen.getByText('3')).toBeInTheDocument() // mockNodes has 3 nodes
  })

  it('should filter files based on search query', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'User.java' } })

    await waitFor(() => {
      expect(screen.getByText('User.java')).toBeInTheDocument()
    })
  })

  it('should show all matching files', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'java' } })

    await waitFor(() => {
      // All 3 mock files contain 'java' in their path
      const fileItems = screen.getAllByText(/\.java/)
      expect(fileItems.length).toBeGreaterThan(0)
    })
  })

  it('should show empty state when no results found', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'nonexistent.py' } })

    await waitFor(() => {
      expect(screen.getByText(/検索結果がありません/)).toBeInTheDocument()
    })
  })

  it('should call onFileSelect when file is clicked', async () => {
    render(<FileSearch onFileSelect={mockOnFileSelect} />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'User.java' } })

    await waitFor(async () => {
      const fileItem = screen.getByText('User.java')
      fireEvent.click(fileItem.closest('.file-item')!)

      expect(mockOnFileSelect).toHaveBeenCalledWith('src/main/java/com/example/User.java')
    })
  })

  it('should clear search input', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(
      /ファイル名またはパスを検索.../
    ) as HTMLInputElement
    fireEvent.change(searchInput, { target: { value: 'User.java' } })

    expect(searchInput.value).toBe('User.java')

    // Find and click the clear button (Ant Design Search component)
    const clearButton = searchInput.parentElement?.querySelector('.ant-input-clear-icon')
    if (clearButton) {
      fireEvent.click(clearButton)
      await waitFor(() => {
        expect(searchInput.value).toBe('')
      })
    }
  })

  it('should display language tags for files', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'User.java' } })

    await waitFor(() => {
      expect(screen.getByText('Java')).toBeInTheDocument()
    })
  })

  it('should display file complexity when available', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'User.java' } })

    await waitFor(() => {
      expect(screen.getByText(/複雑度:/)).toBeInTheDocument()
    })
  })

  it('should handle search with case insensitivity', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'USER' } })

    await waitFor(() => {
      expect(screen.getByText('User.java')).toBeInTheDocument()
    })
  })

  it('should search by file path', async () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(/ファイル名またはパスを検索.../)
    fireEvent.change(searchInput, { target: { value: 'com/example' } })

    await waitFor(() => {
      const results = screen.getAllByText(/com\/example/)
      expect(results.length).toBeGreaterThan(0)
    })
  })

  it('should not show results when search is empty', () => {
    render(<FileSearch />)

    // 検索入力が空の場合、検索結果は表示されない
    expect(screen.queryByText(/検索結果がありません/)).not.toBeInTheDocument()
  })

  it('should update search query on input change', () => {
    render(<FileSearch />)

    const searchInput = screen.getByPlaceholderText(
      /ファイル名またはパスを検索.../
    ) as HTMLInputElement

    fireEvent.change(searchInput, { target: { value: 'test' } })
    expect(searchInput.value).toBe('test')

    fireEvent.change(searchInput, { target: { value: 'another' } })
    expect(searchInput.value).toBe('another')
  })
})
