"""
API Models for Phase 4 Visualization

FastAPIエンドポイントで使用するPydanticモデル
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """ノードタイプ"""
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    PACKAGE = "package"


class DependencyDirection(str, Enum):
    """依存関係の方向"""
    IN = "in"  # 依存元
    OUT = "out"  # 依存先
    BOTH = "both"


class RiskLevel(str, Enum):
    """リスクレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# === リクエストモデル ===

class ImpactAnalysisRequest(BaseModel):
    """影響範囲分析リクエスト"""
    target_type: NodeType = Field(..., description="対象ノードタイプ")
    target_path: str = Field(..., description="対象パス")
    depth: int = Field(default=3, ge=1, le=10, description="探索深さ (1-10)")
    include_indirect: bool = Field(default=True, description="間接依存を含めるか")


class RefactoringRiskRequest(BaseModel):
    """リファクタリングリスク評価リクエスト"""
    target_files: List[str] = Field(..., description="対象ファイルリスト")
    refactoring_type: str = Field(
        default="rename",
        description="リファクタリングタイプ (rename|move|extract|inline)"
    )


class PathFinderRequest(BaseModel):
    """パスファインダーリクエスト"""
    source: str = Field(..., description="開始ノードパス")
    target: str = Field(..., description="終了ノードパス")
    max_depth: int = Field(default=5, ge=1, le=10, description="最大探索深さ")


class NeighborsRequest(BaseModel):
    """隣接ノード取得リクエスト"""
    node_id: str = Field(..., description="ノードID (ファイルパス)")
    depth: int = Field(default=1, ge=1, le=3, description="深さ")
    direction: DependencyDirection = Field(
        default=DependencyDirection.BOTH,
        description="方向 (in|out|both)"
    )
    node_type: NodeType = Field(default=NodeType.FILE, description="ノードタイプ")


# === レスポンスモデル ===

class FileInfo(BaseModel):
    """ファイル情報"""
    type: str = Field(..., description="ノードタイプ")
    path: str = Field(..., description="ファイルパス")
    name: str = Field(..., description="ファイル名")
    language: Optional[str] = Field(None, description="プログラミング言語")
    size: Optional[int] = Field(None, description="ファイルサイズ (bytes)")
    complexity: Optional[float] = Field(None, description="複雑度")


class AffectedFile(BaseModel):
    """影響を受けるファイル"""
    path: str = Field(..., description="ファイルパス")
    name: str = Field(..., description="ファイル名")
    distance: int = Field(..., description="依存の深さ")
    dependency_type: str = Field(default="direct", description="依存タイプ (direct|indirect)")
    affected_methods: List[str] = Field(default_factory=list, description="影響を受けるメソッド")
    risk_contribution: float = Field(..., description="リスク寄与度 (0.0-1.0)")


class ImpactSummary(BaseModel):
    """影響範囲サマリー"""
    total_affected_files: int = Field(..., description="影響を受けるファイル数")
    total_affected_methods: int = Field(..., description="影響を受けるメソッド数")
    total_affected_classes: int = Field(..., description="影響を受けるクラス数")
    risk_level: RiskLevel = Field(..., description="リスクレベル")
    confidence: float = Field(..., description="信頼度 (0.0-1.0)")


class GraphNode(BaseModel):
    """グラフノード"""
    id: str = Field(..., description="ノードID")
    label: str = Field(..., description="ラベル")
    type: str = Field(..., description="ノードタイプ")
    properties: Dict[str, Any] = Field(default_factory=dict, description="プロパティ")


class GraphEdge(BaseModel):
    """グラフエッジ"""
    source: str = Field(..., description="開始ノードID")
    target: str = Field(..., description="終了ノードID")
    type: str = Field(..., description="エッジタイプ")
    properties: Dict[str, Any] = Field(default_factory=dict, description="プロパティ")


class DependencyGraph(BaseModel):
    """依存関係グラフ"""
    nodes: List[GraphNode] = Field(..., description="ノードリスト")
    edges: List[GraphEdge] = Field(..., description="エッジリスト")


class ImpactAnalysisResponse(BaseModel):
    """影響範囲分析レスポンス"""
    target: FileInfo = Field(..., description="対象ファイル情報")
    impact_summary: ImpactSummary = Field(..., description="影響サマリー")
    affected_files: List[AffectedFile] = Field(..., description="影響を受けるファイル")
    dependency_graph: DependencyGraph = Field(..., description="依存関係グラフ")


class RiskFactor(BaseModel):
    """リスク要因"""
    affected_file_count: int = Field(..., description="影響ファイル数")
    circular_dependencies: bool = Field(..., description="循環依存の有無")
    test_coverage: float = Field(..., description="テストカバレッジ")
    complexity_increase: float = Field(..., description="複雑度増加率")


class RiskAssessment(BaseModel):
    """リスク評価"""
    overall_risk: RiskLevel = Field(..., description="総合リスク")
    risk_score: float = Field(..., description="リスクスコア (0.0-10.0)")
    factors: RiskFactor = Field(..., description="リスク要因")


class TestingChecklistItem(BaseModel):
    """テストチェックリスト項目"""
    file: str = Field(..., description="ファイル")
    methods: List[str] = Field(..., description="メソッドリスト")
    priority: str = Field(..., description="優先度 (high|medium|low)")


class RefactoringRiskResponse(BaseModel):
    """リファクタリングリスク評価レスポンス"""
    risk_assessment: RiskAssessment = Field(..., description="リスク評価")
    recommendations: List[str] = Field(..., description="推奨事項")
    testing_checklist: List[TestingChecklistItem] = Field(..., description="テストチェックリスト")


class DependencyInfo(BaseModel):
    """依存関係情報"""
    imports: List[str] = Field(..., description="インポート先")
    dependents: List[str] = Field(..., description="依存元")
    dependency_count: int = Field(..., description="依存先数")
    dependent_count: int = Field(..., description="依存元数")


class MethodInfo(BaseModel):
    """メソッド情報"""
    name: str = Field(..., description="メソッド名")
    calls: List[str] = Field(..., description="呼び出しメソッド")
    called_by: List[str] = Field(..., description="呼び出し元メソッド")


class DependenciesResponse(BaseModel):
    """依存関係取得レスポンス"""
    file: FileInfo = Field(..., description="ファイル情報")
    dependencies: DependencyInfo = Field(..., description="依存関係情報")
    methods: List[MethodInfo] = Field(default_factory=list, description="メソッド情報")


class RelationshipInfo(BaseModel):
    """関係性情報"""
    type: str = Field(..., description="関係タイプ")
    direction: str = Field(..., description="方向")
    properties: Dict[str, Any] = Field(default_factory=dict, description="プロパティ")


class NeighborInfo(BaseModel):
    """隣接ノード情報"""
    node: GraphNode = Field(..., description="ノード")
    relationship: RelationshipInfo = Field(..., description="関係性")


class NeighborsResponse(BaseModel):
    """隣接ノード取得レスポンス"""
    center_node: GraphNode = Field(..., description="中心ノード")
    neighbors: List[NeighborInfo] = Field(..., description="隣接ノード")


class PathInfo(BaseModel):
    """パス情報"""
    length: int = Field(..., description="パス長")
    nodes: List[Dict[str, Any]] = Field(..., description="ノードリスト")
    relationships: List[Dict[str, Any]] = Field(..., description="関係性リスト")


class PathFinderResponse(BaseModel):
    """パスファインダーレスポンス"""
    paths: List[PathInfo] = Field(..., description="パスリスト")
    shortest_path_length: int = Field(..., description="最短パス長")
    total_paths_found: int = Field(..., description="見つかったパス総数")


class CircularDependency(BaseModel):
    """循環依存"""
    cycle_id: str = Field(..., description="サイクルID")
    cycle_length: int = Field(..., description="サイクル長")
    nodes: List[str] = Field(..., description="ノードリスト")
    severity: str = Field(..., description="重要度 (high|medium|low)")


class CircularDependenciesResponse(BaseModel):
    """循環依存検出レスポンス"""
    circular_dependencies: List[CircularDependency] = Field(..., description="循環依存リスト")
    total_cycles: int = Field(..., description="循環依存総数")
    recommendation: str = Field(..., description="推奨事項")


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="ステータス")
    neo4j_connected: bool = Field(..., description="Neo4j接続状態")
    version: str = Field(..., description="APIバージョン")
