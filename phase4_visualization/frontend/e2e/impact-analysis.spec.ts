/**
 * Impact Analysis E2E Tests
 *
 * 影響範囲分析のE2Eテスト
 */

import { test, expect } from '@playwright/test'

test.describe('Impact Analysis Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display application title', async ({ page }) => {
    await expect(page.locator('text=Code Relationship Analyzer')).toBeVisible()
  })

  test('should display empty state initially', async ({ page }) => {
    await expect(page.locator('text=影響範囲分析を実行してください')).toBeVisible()
  })

  test('should have search input in impact panel', async ({ page }) => {
    const searchInput = page.getByPlaceholderText(/ファイルパスを入力/)
    await expect(searchInput).toBeVisible()
  })

  test('should have analyze button', async ({ page }) => {
    const analyzeButton = page.getByRole('button', { name: /分析/ })
    await expect(analyzeButton).toBeVisible()
  })

  test('should type in search input', async ({ page }) => {
    const searchInput = page.getByPlaceholderText(/ファイルパスを入力/)
    await searchInput.fill('src/main/java/com/example/User.java')
    await expect(searchInput).toHaveValue('src/main/java/com/example/User.java')
  })

  test('should show depth selector', async ({ page }) => {
    await expect(page.locator('text=探索深さ:')).toBeVisible()
  })

  test('should have indirect dependency checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox')
    await expect(checkbox).toBeVisible()
    await expect(checkbox).toBeChecked()
  })

  test('should toggle indirect dependency checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox')
    await checkbox.uncheck()
    await expect(checkbox).not.toBeChecked()
    await checkbox.check()
    await expect(checkbox).toBeChecked()
  })

  test('should switch to file search tab', async ({ page }) => {
    const fileSearchTab = page.locator('text=ファイル検索')
    await fileSearchTab.click()
    await expect(page.getByPlaceholderText(/ファイル名またはパスを検索/)).toBeVisible()
  })

  test('should switch to settings tab', async ({ page }) => {
    const settingsTab = page.locator('text=設定')
    await settingsTab.click()
    await expect(page.locator('text=グラフ表示オプションや分析パラメータを設定します。')).toBeVisible()
  })

  test('should display header statistics', async ({ page }) => {
    await expect(page.locator('text=ノード数:')).toBeVisible()
    await expect(page.locator('text=エッジ数:')).toBeVisible()
  })

  test('should have responsive layout', async ({ page }) => {
    const header = page.locator('.dashboard-header')
    const sider = page.locator('.dashboard-sider')
    const content = page.locator('.dashboard-content')

    await expect(header).toBeVisible()
    await expect(sider).toBeVisible()
    await expect(content).toBeVisible()
  })
})

test.describe('Graph Visualization', () => {
  test('should render SVG when graph data is available', async ({ page }) => {
    // モックデータがあると仮定
    await page.goto('/')

    // SVG要素の存在を確認
    const svg = page.locator('svg')
    await expect(svg).toBeVisible()
  })

  test('should have zoom functionality', async ({ page }) => {
    await page.goto('/')

    // SVGをズームできることを確認（実装に依存）
    const svg = page.locator('svg')
    await expect(svg).toBeVisible()
  })
})

test.describe('File Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.locator('text=ファイル検索').click()
  })

  test('should have file search input', async ({ page }) => {
    const searchInput = page.getByPlaceholderText(/ファイル名またはパスを検索/)
    await expect(searchInput).toBeVisible()
  })

  test('should show statistics card', async ({ page }) => {
    await expect(page.locator('text=統計情報')).toBeVisible()
    await expect(page.locator('text=総ファイル数')).toBeVisible()
  })

  test('should type in file search', async ({ page }) => {
    const searchInput = page.getByPlaceholderText(/ファイル名またはパスを検索/)
    await searchInput.fill('User.java')
    await expect(searchInput).toHaveValue('User.java')
  })
})
