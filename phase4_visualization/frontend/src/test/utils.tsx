/**
 * Test Utilities
 *
 * テスト用ヘルパー関数
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { ConfigProvider } from 'antd'
import jaJP from 'antd/locale/ja_JP'

// Ant Design ConfigProviderでラップ
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
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
      {children}
    </ConfigProvider>
  )
}

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
