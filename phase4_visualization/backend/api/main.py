"""
FastAPI Main Application

Phase 4: Code Relationship Visualization and Impact Analysis API
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config.settings import settings
from ..neo4j_client.client import Neo4jClient
from ..models.api_models import (
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    RefactoringRiskRequest,
    RefactoringRiskResponse,
    DependenciesResponse,
    NeighborsRequest,
    NeighborsResponse,
    PathFinderRequest,
    PathFinderResponse,
    CircularDependenciesResponse,
    HealthCheckResponse,
    FileInfo,
    ImpactSummary,
    AffectedFile,
    DependencyGraph,
    GraphNode,
    GraphEdge,
    RiskLevel,
)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# グローバル変数
neo4j_client: Neo4jClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """アプリケーションライフサイクル管理"""
    global neo4j_client

    # 起動時
    logger.info(f"Starting Phase 4 Visualization API v{settings.api_version}...")
    logger.info(f"Neo4j URI: {settings.neo4j_uri}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")

    # Neo4jクライアント初期化
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )

    if neo4j_client.health_check():
        logger.info("✅ Neo4j connection established")
    else:
        logger.warning("⚠️ Neo4j connection failed")

    yield

    # 終了時
    if neo4j_client:
        neo4j_client.close()
    logger.info("Phase 4 Visualization API shutdown")


# FastAPIアプリケーション
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    debug=settings.api_debug
)

# CORSミドルウェア (環境変数から設定を読み込み)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === エンドポイント実装 ===

@app.post("/api/impact-analysis", response_model=ImpactAnalysisResponse)
async def analyze_impact(request: ImpactAnalysisRequest) -> ImpactAnalysisResponse:
    """
    影響範囲分析

    指定されたファイルの変更が及ぼす影響範囲を分析します。
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        # 影響範囲の取得
        affected_files = neo4j_client.get_impact_range(
            file_path=request.target_path,
            max_depth=request.depth,
            include_indirect=request.include_indirect
        )

        # 対象ファイルの情報取得
        file_deps = neo4j_client.get_file_dependencies(request.target_path)
        if not file_deps['file']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.target_path}"
            )

        target_file_props = file_deps['file']['properties']

        # リスクレベルの評価
        risk_level = _assess_risk_level(len(affected_files))

        # グラフデータの構築
        graph_nodes, graph_edges = _build_dependency_graph(
            request.target_path,
            affected_files
        )

        # レスポンス構築
        return ImpactAnalysisResponse(
            target=FileInfo(
                type="file",
                path=request.target_path,
                name=target_file_props.get('name', ''),
                language=target_file_props.get('language'),
                size=target_file_props.get('size'),
                complexity=target_file_props.get('complexity')
            ),
            impact_summary=ImpactSummary(
                total_affected_files=len(affected_files),
                total_affected_methods=sum(
                    len(f.get('affected_methods', [])) for f in affected_files
                ),
                total_affected_classes=0,  # TODO: クラス数の計算
                risk_level=risk_level,
                confidence=0.85  # TODO: 信頼度の計算
            ),
            affected_files=[
                AffectedFile(
                    path=f['path'],
                    name=f['name'],
                    distance=f['distance'],
                    dependency_type="indirect" if f['distance'] > 1 else "direct",
                    affected_methods=[],  # TODO: メソッド情報の追加
                    risk_contribution=f['risk_contribution']
                )
                for f in affected_files
            ],
            dependency_graph=DependencyGraph(
                nodes=graph_nodes,
                edges=graph_edges
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Impact analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/api/dependencies/{file_path:path}", response_model=DependenciesResponse)
async def get_dependencies(file_path: str) -> DependenciesResponse:
    """
    ファイルの依存関係を取得
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        deps = neo4j_client.get_file_dependencies(file_path)

        if not deps['file']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )

        file_props = deps['file']['properties']

        return DependenciesResponse(
            file=FileInfo(
                type="file",
                path=file_path,
                name=file_props.get('name', ''),
                language=file_props.get('language'),
                size=file_props.get('size'),
                complexity=file_props.get('complexity')
            ),
            dependencies={
                'imports': [d['properties']['path'] for d in deps['dependencies']],
                'dependents': [d['properties']['path'] for d in deps['dependents']],
                'dependency_count': len(deps['dependencies']),
                'dependent_count': len(deps['dependents'])
            },
            methods=[]  # TODO: メソッド情報の追加
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dependencies error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/graph/neighbors", response_model=NeighborsResponse)
async def get_neighbors(request: NeighborsRequest) -> NeighborsResponse:
    """
    ノードの隣接ノードを取得（グラフ表示用）
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        result = neo4j_client.get_neighbors(
            node_id=request.node_id,
            node_type=request.node_type.value.capitalize(),
            depth=request.depth,
            direction=request.direction.value
        )

        if not result['center_node']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node not found: {request.node_id}"
            )

        center_props = result['center_node']['properties']

        return NeighborsResponse(
            center_node=GraphNode(
                id=result['center_node']['id'],
                label=center_props.get('name', center_props.get('path', '')),
                type=result['center_node']['labels'][0] if result['center_node']['labels'] else 'Unknown',
                properties=center_props
            ),
            neighbors=[
                {
                    'node': GraphNode(
                        id=n['node']['id'],
                        label=n['node']['properties'].get('name', ''),
                        type=n['node']['labels'][0] if n['node']['labels'] else 'Unknown',
                        properties=n['node']['properties']
                    ),
                    'relationship': n['relationship']
                }
                for n in result['neighbors']
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get neighbors error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/path-finder", response_model=PathFinderResponse)
async def find_path(request: PathFinderRequest) -> PathFinderResponse:
    """
    2つのノード間のパスを検索
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        paths = neo4j_client.find_path(
            source_path=request.source,
            target_path=request.target,
            max_depth=request.max_depth
        )

        if not paths:
            return PathFinderResponse(
                paths=[],
                shortest_path_length=0,
                total_paths_found=0
            )

        return PathFinderResponse(
            paths=paths,
            shortest_path_length=min(p['length'] for p in paths) if paths else 0,
            total_paths_found=len(paths)
        )

    except Exception as e:
        logger.error(f"Path finder error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/circular-dependencies", response_model=CircularDependenciesResponse)
async def get_circular_dependencies() -> CircularDependenciesResponse:
    """
    循環依存を検出
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        cycles = neo4j_client.find_circular_dependencies()

        return CircularDependenciesResponse(
            circular_dependencies=cycles,
            total_cycles=len(cycles),
            recommendation="循環依存を解消してください" if cycles else "循環依存はありません"
        )

    except Exception as e:
        logger.error(f"Circular dependencies error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/refactoring-risk", response_model=RefactoringRiskResponse)
async def assess_refactoring_risk(request: RefactoringRiskRequest) -> RefactoringRiskResponse:
    """
    リファクタリングリスクを評価

    TODO: 完全な実装
    """
    if not neo4j_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not initialized"
        )

    try:
        # TODO: 実装 (簡易版)
        total_affected = 0
        for file_path in request.target_files:
            affected = neo4j_client.get_impact_range(file_path, max_depth=3)
            total_affected += len(affected)

        risk_level = _assess_risk_level(total_affected)

        return RefactoringRiskResponse(
            risk_assessment={
                'overall_risk': risk_level,
                'risk_score': min(total_affected / 5.0, 10.0),
                'factors': {
                    'affected_file_count': total_affected,
                    'circular_dependencies': False,  # TODO
                    'test_coverage': 0.75,  # TODO
                    'complexity_increase': 1.0  # TODO
                }
            },
            recommendations=[
                "テストカバレッジを80%以上に向上させてください",
                "段階的なリファクタリングを推奨します"
            ],
            testing_checklist=[]  # TODO
        )

    except Exception as e:
        logger.error(f"Refactoring risk error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    ヘルスチェック
    """
    neo4j_connected = False
    if neo4j_client:
        neo4j_connected = neo4j_client.health_check()

    return HealthCheckResponse(
        status="healthy" if neo4j_connected else "degraded",
        neo4j_connected=neo4j_connected,
        version="4.0.0"
    )


# === ヘルパー関数 ===

def _assess_risk_level(affected_count: int) -> RiskLevel:
    """影響ファイル数からリスクレベルを評価"""
    if affected_count > 30:
        return RiskLevel.HIGH
    elif affected_count > 10:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def _build_dependency_graph(
    target_path: str,
    affected_files: list
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    依存関係グラフを構築

    TODO: より詳細なグラフ構築
    """
    nodes = [
        GraphNode(
            id=target_path,
            label=target_path.split('/')[-1],
            type="File",
            properties={'path': target_path, 'is_target': True}
        )
    ]

    edges = []

    for affected in affected_files:
        nodes.append(GraphNode(
            id=affected['path'],
            label=affected['name'],
            type="File",
            properties={'path': affected['path'], 'distance': affected['distance']}
        ))

        edges.append(GraphEdge(
            source=target_path,
            target=affected['path'],
            type="DEPENDS_ON",
            properties={'weight': affected['weight']}
        ))

    return nodes, edges


if __name__ == "__main__":
    import uvicorn

    # ログレベル設定
    logging.basicConfig(level=settings.log_level)

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
