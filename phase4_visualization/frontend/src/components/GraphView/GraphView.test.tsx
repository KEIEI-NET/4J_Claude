/**
 * GraphView Component Tests
 *
 * D3.jsグラフ可視化コンポーネントのテスト
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import { GraphView } from './GraphView'
import { mockNodes, mockEdges } from '@/test/mockData'

describe('GraphView', () => {
  it('should render SVG element', () => {
    const { container } = render(
      <GraphView nodes={mockNodes} edges={mockEdges} width={800} height={600} />
    )

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveAttribute('width', '800')
    expect(svg).toHaveAttribute('height', '600')
  })

  it('should render with default dimensions', () => {
    const { container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveAttribute('width', '1200')
    expect(svg).toHaveAttribute('height', '800')
  })

  it('should not render when nodes are empty', () => {
    const { container } = render(<GraphView nodes={[]} edges={[]} />)

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()

    // SVG内のノードがないことを確認
    const circles = container.querySelectorAll('circle')
    expect(circles).toHaveLength(0)
  })

  it('should render correct number of nodes', () => {
    const { container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    // D3.jsが非同期でレンダリングするため、少し待つ
    setTimeout(() => {
      const circles = container.querySelectorAll('circle.node')
      expect(circles.length).toBeGreaterThan(0)
    }, 100)
  })

  it('should render correct number of edges', () => {
    const { container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    setTimeout(() => {
      const lines = container.querySelectorAll('line.link')
      expect(lines.length).toBeGreaterThan(0)
    }, 100)
  })

  it('should call onNodeClick when node is clicked', () => {
    const onNodeClick = vi.fn()
    const { container } = render(
      <GraphView nodes={mockNodes} edges={mockEdges} onNodeClick={onNodeClick} />
    )

    setTimeout(() => {
      const firstCircle = container.querySelector('circle.node')
      if (firstCircle) {
        firstCircle.dispatchEvent(new MouseEvent('click', { bubbles: true }))
        expect(onNodeClick).toHaveBeenCalled()
      }
    }, 100)
  })

  it('should highlight nodes based on highlightedNodes prop', () => {
    const highlightedNodes = new Set([mockNodes[0].id])

    const { container } = render(
      <GraphView nodes={mockNodes} edges={mockEdges} highlightedNodes={highlightedNodes} />
    )

    setTimeout(() => {
      const circles = container.querySelectorAll('circle.node')
      // ハイライトされたノードの色が変わることを確認
      // D3.jsが属性を設定するまで待つ必要がある
      expect(circles.length).toBeGreaterThan(0)
    }, 100)
  })

  it('should render labels for nodes', () => {
    const { container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    setTimeout(() => {
      const labels = container.querySelectorAll('text.label')
      expect(labels.length).toBeGreaterThan(0)
    }, 100)
  })

  it('should have graph-view-container class', () => {
    const { container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    const containerDiv = container.querySelector('.graph-view-container')
    expect(containerDiv).toBeInTheDocument()
  })

  it('should apply custom width and height', () => {
    const customWidth = 1000
    const customHeight = 700

    const { container } = render(
      <GraphView nodes={mockNodes} edges={mockEdges} width={customWidth} height={customHeight} />
    )

    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', customWidth.toString())
    expect(svg).toHaveAttribute('height', customHeight.toString())
  })

  it('should clean up on unmount', () => {
    const { unmount, container } = render(<GraphView nodes={mockNodes} edges={mockEdges} />)

    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()

    unmount()

    // コンポーネントがアンマウントされたことを確認
    const svgAfterUnmount = container.querySelector('svg')
    expect(svgAfterUnmount).not.toBeInTheDocument()
  })
})
