/**
 * Mock Data
 *
 * テスト用モックデータ
 */

import type {
  GraphNode,
  GraphEdge,
  ImpactAnalysisResponse,
  DependenciesResponse,
  AffectedFile,
  FileInfo,
  ImpactSummary,
} from '@/types/api'

// モックノード
export const mockNodes: GraphNode[] = [
  {
    id: 'src/main/java/com/example/User.java',
    label: 'User.java',
    type: 'File',
    properties: {
      language: 'Java',
      complexity: 5.2,
      is_target: true,
    },
  },
  {
    id: 'src/main/java/com/example/UserService.java',
    label: 'UserService.java',
    type: 'File',
    properties: {
      language: 'Java',
      complexity: 8.5,
    },
  },
  {
    id: 'src/main/java/com/example/UserRepository.java',
    label: 'UserRepository.java',
    type: 'File',
    properties: {
      language: 'Java',
      complexity: 3.1,
    },
  },
]

// モックエッジ
export const mockEdges: GraphEdge[] = [
  {
    source: 'src/main/java/com/example/UserService.java',
    target: 'src/main/java/com/example/User.java',
    type: 'DEPENDS_ON',
    properties: {
      weight: 0.8,
    },
  },
  {
    source: 'src/main/java/com/example/UserRepository.java',
    target: 'src/main/java/com/example/User.java',
    type: 'DEPENDS_ON',
    properties: {
      weight: 0.6,
    },
  },
]

// モック影響ファイル
export const mockAffectedFiles: AffectedFile[] = [
  {
    path: 'src/main/java/com/example/UserService.java',
    name: 'UserService.java',
    distance: 1,
    dependency_type: 'DEPENDS_ON',
    affected_methods: ['getUser', 'createUser', 'updateUser'],
    risk_contribution: 0.75,
  },
  {
    path: 'src/main/java/com/example/UserRepository.java',
    name: 'UserRepository.java',
    distance: 1,
    dependency_type: 'DEPENDS_ON',
    affected_methods: ['findById', 'save'],
    risk_contribution: 0.45,
  },
  {
    path: 'src/main/java/com/example/UserController.java',
    name: 'UserController.java',
    distance: 2,
    dependency_type: 'CALLS',
    affected_methods: ['getUserById', 'createUser'],
    risk_contribution: 0.60,
  },
]

// モックファイル情報
export const mockFileInfo: FileInfo = {
  type: 'file',
  path: 'src/main/java/com/example/User.java',
  name: 'User.java',
  language: 'Java',
  size: 1024,
  complexity: 5.2,
}

// モック影響サマリー
export const mockImpactSummary: ImpactSummary = {
  total_affected_files: 3,
  total_affected_methods: 7,
  total_affected_classes: 3,
  risk_level: 'medium',
  confidence: 0.85,
}

// モック影響範囲分析レスポンス
export const mockImpactAnalysisResponse: ImpactAnalysisResponse = {
  target: mockFileInfo,
  impact_summary: mockImpactSummary,
  affected_files: mockAffectedFiles,
  dependency_graph: {
    nodes: mockNodes,
    edges: mockEdges,
  },
}

// モック依存関係レスポンス
export const mockDependenciesResponse: DependenciesResponse = {
  file: mockFileInfo,
  dependencies: {
    imports: [
      'src/main/java/com/example/common/BaseEntity.java',
      'src/main/java/com/example/util/DateUtil.java',
    ],
    dependents: [
      'src/main/java/com/example/UserService.java',
      'src/main/java/com/example/UserRepository.java',
    ],
    dependency_count: 2,
    dependent_count: 2,
  },
  methods: [
    {
      name: 'getUser',
      calls: ['DateUtil.format'],
      called_by: ['UserController.getUserById'],
    },
    {
      name: 'setName',
      calls: [],
      called_by: ['UserService.createUser', 'UserService.updateUser'],
    },
  ],
}
