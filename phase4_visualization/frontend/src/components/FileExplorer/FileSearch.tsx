/**
 * File Search Component
 *
 * ファイル検索とナビゲーション
 * パフォーマンス最適化: React.memo, useMemo, useCallback適用
 */

import React, { useState, useMemo, useCallback } from 'react'
import { Card, Input, List, Tag, Empty } from 'antd'
import { FileOutlined, FolderOutlined, SearchOutlined } from '@ant-design/icons'
import { useGraphStore } from '@/stores/graphStore'
import './FileSearch.css'

const { Search } = Input

interface FileSearchProps {
  onFileSelect?: (filePath: string) => void
}

const FileSearchComponent: React.FC<FileSearchProps> = ({ onFileSelect }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [recentSearches, setRecentSearches] = useState<string[]>([])

  const { nodes } = useGraphStore()

  // ファイルノードのフィルタリング（メモ化）
  const fileNodes = useMemo(() => nodes.filter((node) => node.type === 'File'), [nodes])

  // 検索フィルター（メモ化）
  const filteredFiles = useMemo(
    () =>
      searchQuery
        ? fileNodes.filter(
            (node) =>
              node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
              node.id.toLowerCase().includes(searchQuery.toLowerCase())
          )
        : [],
    [searchQuery, fileNodes]
  )

  const handleSearch = useCallback(
    (value: string) => {
      setSearchQuery(value)
      if (value && !recentSearches.includes(value)) {
        setRecentSearches([value, ...recentSearches.slice(0, 4)])
      }
    },
    [recentSearches]
  )

  const handleFileClick = useCallback(
    (filePath: string) => {
      onFileSelect?.(filePath)
    },
    [onFileSelect]
  )

  const getFileExtension = useCallback((filename: string): string => {
    const ext = filename.split('.').pop()
    return ext || ''
  }, [])

  const getLanguageTag = useCallback((extension: string): { color: string; text: string } => {
    const languageMap: Record<string, { color: string; text: string }> = {
      java: { color: 'red', text: 'Java' },
      py: { color: 'blue', text: 'Python' },
      ts: { color: 'cyan', text: 'TypeScript' },
      tsx: { color: 'cyan', text: 'TSX' },
      js: { color: 'gold', text: 'JavaScript' },
      jsx: { color: 'gold', text: 'JSX' },
      css: { color: 'purple', text: 'CSS' },
      html: { color: 'orange', text: 'HTML' },
    }
    return languageMap[extension] || { color: 'default', text: extension.toUpperCase() }
  }, [])

  return (
    <div className="file-search">
      <Card title="ファイル検索" className="search-card">
        <Search
          placeholder="ファイル名またはパスを検索..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          prefix={<SearchOutlined />}
          allowClear
          size="large"
        />

        {recentSearches.length > 0 && !searchQuery && (
          <div className="recent-searches">
            <div className="recent-title">最近の検索</div>
            <div className="recent-list">
              {recentSearches.map((search, index) => (
                <Tag
                  key={index}
                  onClick={() => setSearchQuery(search)}
                  style={{ cursor: 'pointer', marginBottom: 8 }}
                >
                  {search}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {searchQuery && (
          <div className="search-results">
            {filteredFiles.length > 0 ? (
              <List
                dataSource={filteredFiles}
                renderItem={(node) => {
                  const extension = getFileExtension(node.label)
                  const langTag = getLanguageTag(extension)

                  return (
                    <List.Item
                      key={node.id}
                      onClick={() => handleFileClick(node.id)}
                      className="file-item"
                    >
                      <List.Item.Meta
                        avatar={<FileOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                        title={
                          <div className="file-title">
                            <span>{node.label}</span>
                            <Tag color={langTag.color}>{langTag.text}</Tag>
                          </div>
                        }
                        description={
                          <div className="file-description">
                            <FolderOutlined style={{ marginRight: 4 }} />
                            <span className="file-path">{node.id}</span>
                          </div>
                        }
                      />
                      {node.properties?.complexity && (
                        <div className="file-stats">
                          <Tag color="purple">
                            複雑度: {node.properties.complexity.toFixed(1)}
                          </Tag>
                        </div>
                      )}
                    </List.Item>
                  )
                }}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: false,
                  showTotal: (total) => `${total} 件`,
                }}
              />
            ) : (
              <Empty
                description="検索結果がありません"
                style={{ marginTop: 32 }}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </div>
        )}
      </Card>

      <Card title="統計情報" style={{ marginTop: 16 }}>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">{fileNodes.length}</div>
            <div className="stat-label">総ファイル数</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {fileNodes.filter((n) => n.properties?.language === 'Java').length}
            </div>
            <div className="stat-label">Javaファイル</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {fileNodes.filter((n) => n.properties?.language === 'Python').length}
            </div>
            <div className="stat-label">Pythonファイル</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">
              {fileNodes.filter((n) => n.type === 'Class').length}
            </div>
            <div className="stat-label">クラス数</div>
          </div>
        </div>
      </Card>
    </div>
  )
}

// React.memoでメモ化してパフォーマンス最適化
export const FileSearch = React.memo(FileSearchComponent)
