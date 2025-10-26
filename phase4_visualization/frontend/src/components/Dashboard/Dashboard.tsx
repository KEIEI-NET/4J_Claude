/**
 * Dashboard Component
 *
 * メインダッシュボード - 影響範囲分析とグラフ可視化を統合
 * パフォーマンス最適化: React.memo, useCallback適用
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Layout, Tabs, message } from 'antd'
import {
  ApartmentOutlined,
  SearchOutlined,
  FileSearchOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { GraphView } from '@/components/GraphView/GraphView'
import { ImpactPanel } from '@/components/ImpactAnalysis/ImpactPanel'
import { FileSearch } from '@/components/FileExplorer/FileSearch'
import { useGraphStore } from '@/stores/graphStore'
import type { GraphNode } from '@/types/api'
import './Dashboard.css'

const { Header, Content, Sider } = Layout
const { TabPane } = Tabs

const DashboardComponent: React.FC = () => {
  const [activeTab, setActiveTab] = useState('impact')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const { nodes, edges, highlightedNodes, impactAnalysis, selectNode } = useGraphStore()

  useEffect(() => {
    if (impactAnalysis) {
      message.success(`影響範囲分析完了: ${impactAnalysis.affected_files.length} ファイルが影響を受けます`)
    }
  }, [impactAnalysis])

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      setSelectedNode(node)
      selectNode(node)
      message.info(`選択: ${node.label}`)
    },
    [selectNode]
  )

  const handleFileSelect = useCallback(
    (filePath: string) => {
      const node = nodes.find((n) => n.id === filePath)
      if (node) {
        handleNodeClick(node)
        setActiveTab('graph')
      }
    },
    [nodes, handleNodeClick]
  )

  return (
    <Layout className="dashboard">
      <Header className="dashboard-header">
        <div className="header-content">
          <div className="logo">
            <ApartmentOutlined style={{ fontSize: 24, marginRight: 12 }} />
            <span className="title">Code Relationship Analyzer</span>
          </div>
          <div className="header-info">
            <span className="node-count">ノード数: {nodes.length}</span>
            <span className="edge-count">エッジ数: {edges.length}</span>
          </div>
        </div>
      </Header>

      <Layout>
        <Sider width={400} theme="light" className="dashboard-sider">
          <Tabs activeKey={activeTab} onChange={setActiveTab} className="sider-tabs">
            <TabPane
              tab={
                <span>
                  <SearchOutlined />
                  影響範囲分析
                </span>
              }
              key="impact"
            >
              <ImpactPanel onFileSelect={handleFileSelect} />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <FileSearchOutlined />
                  ファイル検索
                </span>
              }
              key="search"
            >
              <FileSearch onFileSelect={handleFileSelect} />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <SettingOutlined />
                  設定
                </span>
              }
              key="settings"
            >
              <div style={{ padding: 16 }}>
                <h3>設定</h3>
                <p>グラフ表示オプションや分析パラメータを設定します。</p>
                {/* 将来的に設定項目を追加 */}
              </div>
            </TabPane>
          </Tabs>
        </Sider>

        <Content className="dashboard-content">
          <div className="graph-container">
            {nodes.length > 0 ? (
              <>
                <div className="graph-header">
                  <h2>依存関係グラフ</h2>
                  {selectedNode && (
                    <div className="selected-node-info">
                      <span className="label">選択中:</span>
                      <span className="value">{selectedNode.label}</span>
                      {selectedNode.properties?.complexity && (
                        <span className="complexity">
                          複雑度: {selectedNode.properties.complexity.toFixed(1)}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <GraphView
                  nodes={nodes}
                  edges={edges}
                  highlightedNodes={highlightedNodes}
                  onNodeClick={handleNodeClick}
                  width={1400}
                  height={800}
                />
              </>
            ) : (
              <div className="empty-state">
                <ApartmentOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />
                <h2>影響範囲分析を実行してください</h2>
                <p>左側のパネルからファイルを選択し、影響範囲分析を開始します。</p>
              </div>
            )}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

// React.memoでメモ化してパフォーマンス最適化
export const Dashboard = React.memo(DashboardComponent)
