/**
 * GraphView Component
 *
 * D3.jsを使用したインタラクティブなグラフ可視化
 * パフォーマンス最適化: React.memo, useMemo適用
 */

import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'
import type { GraphNode, GraphEdge } from '@/types/api'
import './GraphView.css'

interface GraphViewProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  highlightedNodes?: Set<string>
  onNodeClick?: (node: GraphNode) => void
  width?: number
  height?: number
}

interface D3Node extends d3.SimulationNodeDatum, GraphNode {
  x?: number
  y?: number
}

interface D3Edge extends GraphEdge {
  source: D3Node
  target: D3Node
}

const GraphViewComponent: React.FC<GraphViewProps> = ({
  nodes,
  edges,
  highlightedNodes = new Set(),
  onNodeClick,
  width = 1200,
  height = 800,
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const simulationRef = useRef<d3.Simulation<D3Node, D3Edge> | null>(null)

  // ノードデータをメモ化
  const nodeData: D3Node[] = useMemo(() => nodes.map((n) => ({ ...n })), [nodes])

  // エッジデータをメモ化
  const edgeData: D3Edge[] = useMemo(
    () =>
      edges.map((e) => ({
        ...e,
        source: nodeData.find((n) => n.id === e.source)!,
        target: nodeData.find((n) => n.id === e.target)!,
      })),
    [edges, nodeData]
  )

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return

    // SVGクリア
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // グラフコンテナ
    const g = svg.append('g').attr('class', 'graph-container')

    // ズーム機能
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Force Simulation
    const simulation = d3
      .forceSimulation<D3Node, D3Edge>(nodeData)
      .force(
        'link',
        d3
          .forceLink<D3Node, D3Edge>(edgeData)
          .id((d) => d.id)
          .distance(150)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

    simulationRef.current = simulation

    // エッジ（リンク）の描画
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edgeData)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', (d) => {
        if (d.type === 'DEPENDS_ON') return '#1890ff'
        if (d.type === 'CALLS') return '#52c41a'
        return '#d9d9d9'
      })
      .attr('stroke-width', (d) => {
        const strength = d.properties?.weight || 1.0
        return Math.max(1, strength * 3)
      })
      .attr('stroke-opacity', 0.6)

    // ノードの描画
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(nodeData)
      .join('circle')
      .attr('class', 'node')
      .attr('r', (d) => {
        const complexity = d.properties?.complexity || 1
        return Math.sqrt(complexity) * 3 + 8
      })
      .attr('fill', (d) => {
        if (highlightedNodes.has(d.id)) return '#ff4d4f'
        if (d.properties?.is_target) return '#faad14'
        if (d.type === 'File') return '#1890ff'
        if (d.type === 'Class') return '#52c41a'
        return '#d9d9d9'
      })
      .attr('stroke', (d) => (d.properties?.is_target ? '#000' : '#fff'))
      .attr('stroke-width', (d) => (d.properties?.is_target ? 3 : 1.5))
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        if (onNodeClick) onNodeClick(d)
      })
      .call(
        d3
          .drag<SVGCircleElement, D3Node>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )

    // ノードラベル
    const label = g
      .append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(nodeData)
      .join('text')
      .attr('class', 'label')
      .attr('text-anchor', 'middle')
      .attr('dy', -15)
      .attr('font-size', 10)
      .attr('fill', '#333')
      .text((d) => d.label)
      .style('pointer-events', 'none')

    // ツールチップ
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'graph-tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000)

    node
      .on('mouseover', (event, d) => {
        tooltip.transition().duration(200).style('opacity', 0.9)
        tooltip
          .html(
            `
            <strong>${d.label}</strong><br/>
            Type: ${d.type}<br/>
            ${d.properties?.language ? `Language: ${d.properties.language}<br/>` : ''}
            ${d.properties?.complexity ? `Complexity: ${d.properties.complexity.toFixed(1)}<br/>` : ''}
          `
          )
          .style('left', event.pageX + 10 + 'px')
          .style('top', event.pageY - 28 + 'px')
      })
      .on('mouseout', () => {
        tooltip.transition().duration(500).style('opacity', 0)
      })

    // Force Simulationの更新
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x || 0)
        .attr('y1', (d) => (d.source as D3Node).y || 0)
        .attr('x2', (d) => (d.target as D3Node).x || 0)
        .attr('y2', (d) => (d.target as D3Node).y || 0)

      node.attr('cx', (d) => d.x || 0).attr('cy', (d) => d.y || 0)

      label.attr('x', (d) => d.x || 0).attr('y', (d) => d.y || 0)
    })

    // クリーンアップ
    return () => {
      simulation.stop()
      tooltip.remove()
    }
  }, [nodeData, edgeData, highlightedNodes, onNodeClick, width, height])

  return (
    <div className="graph-view-container">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{
          border: '1px solid #d9d9d9',
          borderRadius: '4px',
          background: '#fafafa',
        }}
      />
    </div>
  )
}

// React.memoでメモ化してパフォーマンス最適化
export const GraphView = React.memo(GraphViewComponent)
