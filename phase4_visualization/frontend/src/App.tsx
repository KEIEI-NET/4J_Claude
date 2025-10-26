/**
 * App Component
 *
 * アプリケーションのルートコンポーネント
 */

import React from 'react'
import { ConfigProvider } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import { Dashboard } from '@/components/Dashboard/Dashboard'
import './App.css'

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
      <Dashboard />
    </ConfigProvider>
  )
}

export default App
