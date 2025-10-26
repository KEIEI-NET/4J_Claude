/**
 * App Component
 *
 * アプリケーションのルートコンポーネント
 * Code Splitting: React.lazy()によるコンポーネント遅延読み込み
 */

import React, { Suspense } from 'react'
import { ConfigProvider, Spin } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import './App.css'

// Lazy loading: Dashboardコンポーネントの動的インポート
const Dashboard = React.lazy(() =>
  import('@/components/Dashboard/Dashboard').then((module) => ({
    default: module.Dashboard,
  }))
)

// ローディングコンポーネント
const LoadingFallback: React.FC = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      flexDirection: 'column',
      gap: '16px',
    }}
  >
    <Spin size="large" />
    <p style={{ color: '#666', fontSize: '14px' }}>読み込み中...</p>
  </div>
)

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={jaJP}
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 4,
          fontSize: 14,
        },
      }}
    >
      <Suspense fallback={<LoadingFallback />}>
        <Dashboard />
      </Suspense>
    </ConfigProvider>
  )
}

export default App
