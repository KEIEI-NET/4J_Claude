/**
 * API Type Definitions
 *
 * バックエンドAPIとの通信で使用する型定義
 */

export enum NodeType {
  FILE = 'file',
  CLASS = 'class',
  METHOD = 'method',
  PACKAGE = 'package',
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
}

// === Graph Types ===

export interface GraphNode {
  id: string
  label: string
  type: string
  properties: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  properties: Record<string, any>
}

export interface DependencyGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// === File Types ===

export interface FileInfo {
  type: string
  path: string
  name: string
  language?: string
  size?: number
  complexity?: number
}

export interface AffectedFile {
  path: string
  name: string
  distance: number
  dependency_type: string
  affected_methods: string[]
  risk_contribution: number
}

// === Impact Analysis ===

export interface ImpactSummary {
  total_affected_files: number
  total_affected_methods: number
  total_affected_classes: number
  risk_level: RiskLevel
  confidence: number
}

export interface ImpactAnalysisRequest {
  target_type: NodeType
  target_path: string
  depth: number
  include_indirect: boolean
}

export interface ImpactAnalysisResponse {
  target: FileInfo
  impact_summary: ImpactSummary
  affected_files: AffectedFile[]
  dependency_graph: DependencyGraph
}

// === Dependencies ===

export interface DependencyInfo {
  imports: string[]
  dependents: string[]
  dependency_count: number
  dependent_count: number
}

export interface MethodInfo {
  name: string
  calls: string[]
  called_by: string[]
}

export interface DependenciesResponse {
  file: FileInfo
  dependencies: DependencyInfo
  methods: MethodInfo[]
}

// === Path Finder ===

export interface PathInfo {
  length: number
  nodes: Array<{
    type: string
    name: string
    path: string
  }>
  relationships: Array<{
    type: string
    strength: number
  }>
}

export interface PathFinderRequest {
  source: string
  target: string
  max_depth: number
}

export interface PathFinderResponse {
  paths: PathInfo[]
  shortest_path_length: number
  total_paths_found: number
}

// === Circular Dependencies ===

export interface CircularDependency {
  cycle_id: string
  cycle_length: number
  nodes: string[]
  severity: string
}

export interface CircularDependenciesResponse {
  circular_dependencies: CircularDependency[]
  total_cycles: number
  recommendation: string
}

// === Health Check ===

export interface HealthCheckResponse {
  status: string
  neo4j_connected: boolean
  version: string
}
