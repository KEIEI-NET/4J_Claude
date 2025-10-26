/**
 * API Client Tests
 *
 * APIクライアントの単体テスト
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { apiClient } from './client'
import {
  mockImpactAnalysisResponse,
  mockDependenciesResponse,
} from '@/test/mockData'
import type { ImpactAnalysisRequest, PathFinderRequest } from '@/types/api'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('APIClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('analyzeImpact', () => {
    it('should successfully analyze impact', async () => {
      const mockRequest: ImpactAnalysisRequest = {
        target_type: 'file',
        target_path: 'src/main/java/com/example/User.java',
        depth: 3,
        include_indirect: true,
      }

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockImpactAnalysisResponse }),
        get: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      // 新しいインスタンスを作成してテスト
      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      const response = await client.analyzeImpact(mockRequest)

      expect(response).toEqual(mockImpactAnalysisResponse)
      expect(response.impact_summary.total_affected_files).toBe(3)
      expect(response.affected_files).toHaveLength(3)
    })

    it('should handle API errors', async () => {
      const mockRequest: ImpactAnalysisRequest = {
        target_type: 'file',
        target_path: 'invalid/path.java',
        depth: 3,
        include_indirect: true,
      }

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn().mockRejectedValue(new Error('File not found')),
        get: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      await expect(client.analyzeImpact(mockRequest)).rejects.toThrow('File not found')
    })
  })

  describe('getDependencies', () => {
    it('should successfully get dependencies', async () => {
      const filePath = 'src/main/java/com/example/User.java'

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn(),
        get: vi.fn().mockResolvedValue({ data: mockDependenciesResponse }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      const response = await client.getDependencies(filePath)

      expect(response).toEqual(mockDependenciesResponse)
      expect(response.dependencies.dependency_count).toBe(2)
      expect(response.dependencies.dependent_count).toBe(2)
    })

    it('should encode file path in URL', async () => {
      const filePath = 'src/main/java/com/example/User Service.java' // スペース含む
      const getMock = vi.fn().mockResolvedValue({ data: mockDependenciesResponse })

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn(),
        get: getMock,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      await client.getDependencies(filePath)

      expect(getMock).toHaveBeenCalledWith(
        expect.stringContaining(encodeURIComponent(filePath))
      )
    })
  })

  describe('findPath', () => {
    it('should successfully find path', async () => {
      const mockRequest: PathFinderRequest = {
        source: 'src/main/java/com/example/User.java',
        target: 'src/main/java/com/example/UserController.java',
        max_depth: 5,
      }

      const mockResponse = {
        paths: [
          {
            length: 2,
            nodes: [
              { type: 'File', name: 'User.java', path: 'src/main/java/com/example/User.java' },
              {
                type: 'File',
                name: 'UserService.java',
                path: 'src/main/java/com/example/UserService.java',
              },
              {
                type: 'File',
                name: 'UserController.java',
                path: 'src/main/java/com/example/UserController.java',
              },
            ],
            relationships: [
              { type: 'DEPENDS_ON', strength: 0.8 },
              { type: 'CALLS', strength: 0.9 },
            ],
          },
        ],
        shortest_path_length: 2,
        total_paths_found: 1,
      }

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockResponse }),
        get: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      const response = await client.findPath(mockRequest)

      expect(response).toEqual(mockResponse)
      expect(response.shortest_path_length).toBe(2)
      expect(response.paths).toHaveLength(1)
    })
  })

  describe('getCircularDependencies', () => {
    it('should successfully get circular dependencies', async () => {
      const mockResponse = {
        circular_dependencies: [
          {
            cycle_id: 'cycle_1',
            cycle_length: 3,
            nodes: [
              'src/main/java/com/example/A.java',
              'src/main/java/com/example/B.java',
              'src/main/java/com/example/C.java',
            ],
            severity: 'high',
          },
        ],
        total_cycles: 1,
        recommendation: 'Refactor to remove circular dependencies',
      }

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn(),
        get: vi.fn().mockResolvedValue({ data: mockResponse }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      const response = await client.getCircularDependencies()

      expect(response).toEqual(mockResponse)
      expect(response.total_cycles).toBe(1)
      expect(response.circular_dependencies).toHaveLength(1)
    })
  })

  describe('healthCheck', () => {
    it('should successfully check health', async () => {
      const mockResponse = {
        status: 'healthy',
        neo4j_connected: true,
        version: '1.0.0',
      }

      mockedAxios.create = vi.fn().mockReturnValue({
        post: vi.fn(),
        get: vi.fn().mockResolvedValue({ data: mockResponse }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any)

      const { APIClient } = await import('./client')
      const client = new (APIClient as any)()

      const response = await client.healthCheck()

      expect(response).toEqual(mockResponse)
      expect(response.status).toBe('healthy')
      expect(response.neo4j_connected).toBe(true)
    })
  })
})
