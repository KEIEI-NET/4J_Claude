/**
 * API Client
 *
 * バックエンドAPIとの通信を担当
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  ImpactAnalysisRequest,
  ImpactAnalysisResponse,
  DependenciesResponse,
  PathFinderRequest,
  PathFinderResponse,
  CircularDependenciesResponse,
  HealthCheckResponse,
} from '@/types/api'

class APIClient {
  private client: AxiosInstance
  private debugMode: boolean

  constructor(baseURL?: string) {
    // 環境変数から設定を読み込み
    const apiBaseURL = baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const apiTimeout = Number(import.meta.env.VITE_API_TIMEOUT) || 30000
    this.debugMode = import.meta.env.VITE_DEBUG_MODE === 'true'

    this.client = axios.create({
      baseURL: apiBaseURL,
      timeout: apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // リクエストインターセプター
    this.client.interceptors.request.use(
      (config) => {
        if (this.debugMode) {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // レスポンスインターセプター
    this.client.interceptors.response.use(
      (response) => {
        if (this.debugMode) {
          console.log(`[API] Response:`, response.status)
        }
        return response
      },
      (error: AxiosError) => {
        console.error(`[API] Error:`, error.message)
        if (error.response) {
          console.error(`[API] Status:`, error.response.status)
          console.error(`[API] Data:`, error.response.data)
        }
        return Promise.reject(error)
      }
    )
  }

  /**
   * 影響範囲分析
   */
  async analyzeImpact(request: ImpactAnalysisRequest): Promise<ImpactAnalysisResponse> {
    const response = await this.client.post<ImpactAnalysisResponse>(
      '/api/impact-analysis',
      request
    )
    return response.data
  }

  /**
   * 依存関係取得
   */
  async getDependencies(filePath: string): Promise<DependenciesResponse> {
    const response = await this.client.get<DependenciesResponse>(
      `/api/dependencies/${encodeURIComponent(filePath)}`
    )
    return response.data
  }

  /**
   * パス検索
   */
  async findPath(request: PathFinderRequest): Promise<PathFinderResponse> {
    const response = await this.client.post<PathFinderResponse>('/api/path-finder', request)
    return response.data
  }

  /**
   * 循環依存検出
   */
  async getCircularDependencies(): Promise<CircularDependenciesResponse> {
    const response = await this.client.get<CircularDependenciesResponse>(
      '/api/circular-dependencies'
    )
    return response.data
  }

  /**
   * ヘルスチェック
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/health')
    return response.data
  }
}

// シングルトンインスタンス
export const apiClient = new APIClient()

export default apiClient
