/**
 * Impact Analysis Panel Component
 *
 * 影響範囲分析の結果を表示
 * パフォーマンス最適化: React.memo, useCallback適用
 */

import React, { useState, useCallback } from 'react'
import { Card, Input, Button, Select, Table, Tag, Statistic, Row, Col, Spin, Alert } from 'antd'
import { SearchOutlined, FileOutlined, WarningOutlined } from '@ant-design/icons'
import type { AffectedFile } from '@/types/api'
import { useGraphStore } from '@/stores/graphStore'
import './ImpactPanel.css'

const { Search } = Input

interface ImpactPanelProps {
  onFileSelect?: (filePath: string) => void
}

const ImpactPanelComponent: React.FC<ImpactPanelProps> = ({ onFileSelect }) => {
  const [targetPath, setTargetPath] = useState('')
  const [depth, setDepth] = useState(3)
  const [includeIndirect, setIncludeIndirect] = useState(true)

  const { impactAnalysis, loading, error, analyzeImpact } = useGraphStore()

  const handleAnalyze = useCallback(async () => {
    if (!targetPath.trim()) return
    await analyzeImpact(targetPath, depth, includeIndirect)
  }, [targetPath, depth, includeIndirect, analyzeImpact])

  const getRiskColor = useCallback((riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return 'red'
      case 'medium':
        return 'orange'
      case 'low':
        return 'green'
      default:
        return 'default'
    }
  }, [])

  const columns = [
    {
      title: 'ファイル名',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: AffectedFile) => (
        <Button
          type="link"
          icon={<FileOutlined />}
          onClick={() => onFileSelect?.(record.path)}
        >
          {name}
        </Button>
      ),
    },
    {
      title: 'パス',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
    },
    {
      title: '距離',
      dataIndex: 'distance',
      key: 'distance',
      width: 100,
      sorter: (a: AffectedFile, b: AffectedFile) => a.distance - b.distance,
      render: (distance: number) => <Tag color="blue">{distance}</Tag>,
    },
    {
      title: '依存タイプ',
      dataIndex: 'dependency_type',
      key: 'dependency_type',
      width: 150,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: '影響メソッド',
      dataIndex: 'affected_methods',
      key: 'affected_methods',
      width: 120,
      render: (methods: string[]) => <Tag color="purple">{methods.length}</Tag>,
    },
    {
      title: 'リスク寄与度',
      dataIndex: 'risk_contribution',
      key: 'risk_contribution',
      width: 150,
      sorter: (a: AffectedFile, b: AffectedFile) => a.risk_contribution - b.risk_contribution,
      render: (risk: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: '100px',
              height: '8px',
              background: '#f0f0f0',
              borderRadius: '4px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${risk * 100}%`,
                height: '100%',
                background: risk > 0.7 ? '#ff4d4f' : risk > 0.4 ? '#faad14' : '#52c41a',
              }}
            />
          </div>
          <span>{(risk * 100).toFixed(1)}%</span>
        </div>
      ),
    },
  ]

  return (
    <div className="impact-panel">
      <Card title="影響範囲分析" className="search-card">
        <div className="search-controls">
          <Search
            placeholder="ファイルパスを入力 (例: src/main/java/com/example/User.java)"
            value={targetPath}
            onChange={(e) => setTargetPath(e.target.value)}
            onSearch={handleAnalyze}
            enterButton={
              <Button type="primary" icon={<SearchOutlined />} loading={loading}>
                分析
              </Button>
            }
            size="large"
          />

          <div className="analysis-options">
            <div className="option-group">
              <label>探索深さ:</label>
              <Select
                value={depth}
                onChange={setDepth}
                style={{ width: 120 }}
                options={[
                  { value: 1, label: '1 (直接のみ)' },
                  { value: 2, label: '2' },
                  { value: 3, label: '3 (推奨)' },
                  { value: 4, label: '4' },
                  { value: 5, label: '5' },
                ]}
              />
            </div>

            <div className="option-group">
              <label>
                <input
                  type="checkbox"
                  checked={includeIndirect}
                  onChange={(e) => setIncludeIndirect(e.target.checked)}
                />
                間接依存を含める
              </label>
            </div>
          </div>
        </div>

        {error && (
          <Alert
            message="エラー"
            description={error}
            type="error"
            closable
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      {loading && (
        <Card style={{ marginTop: 16, textAlign: 'center' }}>
          <Spin size="large" tip="影響範囲を分析中..." />
        </Card>
      )}

      {impactAnalysis && !loading && (
        <>
          <Card title="分析サマリー" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="影響を受けるファイル"
                  value={impactAnalysis.impact_summary.total_affected_files}
                  prefix={<FileOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="影響を受けるメソッド"
                  value={impactAnalysis.impact_summary.total_affected_methods}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="影響を受けるクラス"
                  value={impactAnalysis.impact_summary.total_affected_classes}
                />
              </Col>
              <Col span={6}>
                <Card className="risk-card">
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 14, color: '#666', marginBottom: 8 }}>
                      リスクレベル
                    </div>
                    <Tag
                      icon={<WarningOutlined />}
                      color={getRiskColor(impactAnalysis.impact_summary.risk_level)}
                      style={{ fontSize: 16, padding: '4px 12px' }}
                    >
                      {impactAnalysis.impact_summary.risk_level.toUpperCase()}
                    </Tag>
                    <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                      信頼度: {(impactAnalysis.impact_summary.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>

          <Card title="影響を受けるファイル一覧" style={{ marginTop: 16 }}>
            <Table
              columns={columns}
              dataSource={impactAnalysis.affected_files}
              rowKey="path"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `全 ${total} ファイル`,
              }}
              size="small"
            />
          </Card>
        </>
      )}
    </div>
  )
}

// React.memoでメモ化してパフォーマンス最適化
export const ImpactPanel = React.memo(ImpactPanelComponent)
