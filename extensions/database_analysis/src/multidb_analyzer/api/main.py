"""
FastAPI Main Application for Multi-Database Analysis

Phase 4のマルチDB解析APIエンドポイント
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from ..analyzers.sql_analyzer import SQLAnalyzer
from ..analyzers.redis_analyzer import RedisAnalyzer
from ..analyzers.elasticsearch_analyzer import ElasticsearchAnalyzer
from ..analyzers.transaction_analyzer import TransactionAnalyzer
from ..models.database_models import (
    DatabaseQuery,
    DatabaseEntity,
    TransactionBoundary,
    CacheOperation,
    DatabaseType,
)
from ..neo4j.graph_exporter import MultiDBGraphExporter

logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="Multi-Database Analyzer API",
    description="Phase 4: マルチデータベース解析API",
    version="4.0.0",
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["analysis"])


# リクエスト/レスポンスモデル
class AnalyzeFileRequest(BaseModel):
    """ファイル解析リクエスト"""
    file_path: str = Field(..., description="解析対象ファイルパス")
    database_type: DatabaseType = Field(
        default=DatabaseType.MYSQL,
        description="データベースタイプ"
    )


class AnalyzeDirectoryRequest(BaseModel):
    """ディレクトリ解析リクエスト"""
    directory_path: str = Field(..., description="解析対象ディレクトリパス")
    file_pattern: str = Field(default="**/*.java", description="ファイルパターン")
    include_tests: bool = Field(default=False, description="テストファイルを含める")


class AnalysisResponse(BaseModel):
    """解析レスポンス"""
    status: str = Field(..., description="解析ステータス")
    queries: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    transactions: List[Dict[str, Any]] = Field(default_factory=list)
    cache_operations: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class DatabaseImpactRequest(BaseModel):
    """DB影響分析リクエスト"""
    entity_name: str = Field(..., description="エンティティ名（テーブル名など）")
    database_type: DatabaseType = Field(..., description="データベースタイプ")


class DatabaseImpactResponse(BaseModel):
    """DB影響分析レスポンス"""
    entity_name: str
    database_type: str
    affected_queries: List[Dict[str, Any]]
    affected_methods: List[str]
    risk_assessment: str
    recommendations: List[str]


# エンドポイント実装

@router.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(request: AnalyzeFileRequest):
    """
    単一ファイルのデータベース操作を解析

    Args:
        request: 解析リクエスト

    Returns:
        解析結果
    """
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        queries = []
        transactions = []
        cache_ops = []

        # SQLアナライザー
        if request.database_type in [DatabaseType.MYSQL, DatabaseType.SQL_SERVER]:
            sql_analyzer = SQLAnalyzer(database=request.database_type)
            queries = sql_analyzer.analyze_file(str(file_path))

        # Redisアナライザー
        elif request.database_type == DatabaseType.REDIS:
            redis_analyzer = RedisAnalyzer()
            cache_ops = redis_analyzer.analyze_file(str(file_path))

        # Elasticsearchアナライザー
        elif request.database_type == DatabaseType.ELASTICSEARCH:
            es_analyzer = ElasticsearchAnalyzer()
            queries = es_analyzer.analyze_file(str(file_path))

        # トランザクション解析
        tx_analyzer = TransactionAnalyzer()
        transactions = tx_analyzer.analyze_file(str(file_path))

        # サマリー作成
        summary = {
            "total_queries": len(queries),
            "total_transactions": len(transactions),
            "total_cache_operations": len(cache_ops),
            "n_plus_one_risks": sum(1 for q in queries if q.n_plus_one_risk),
            "missing_transactions": sum(1 for q in queries if q.missing_transaction),
            "missing_ttl": sum(1 for op in cache_ops if op.missing_ttl),
        }

        return AnalysisResponse(
            status="success",
            queries=[q.model_dump() for q in queries],
            transactions=[t.model_dump() for t in transactions],
            cache_operations=[op.model_dump() for op in cache_ops],
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/directory", response_model=AnalysisResponse)
async def analyze_directory(request: AnalyzeDirectoryRequest, background_tasks: BackgroundTasks):
    """
    ディレクトリ内のすべてのファイルを解析

    Args:
        request: 解析リクエスト
        background_tasks: バックグラウンドタスク

    Returns:
        解析結果
    """
    try:
        directory = Path(request.directory_path)
        if not directory.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory_path}")

        # ファイル検索
        files = list(directory.glob(request.file_pattern))
        if not request.include_tests:
            files = [f for f in files if "test" not in f.name.lower()]

        all_queries = []
        all_transactions = []
        all_cache_ops = []

        # 各アナライザー初期化
        sql_analyzer = SQLAnalyzer()
        redis_analyzer = RedisAnalyzer()
        es_analyzer = ElasticsearchAnalyzer()
        tx_analyzer = TransactionAnalyzer()

        # ファイルごとに解析
        for file_path in files:
            try:
                # SQL解析
                queries = sql_analyzer.analyze_file(str(file_path))
                all_queries.extend(queries)

                # Redis解析
                cache_ops = redis_analyzer.analyze_file(str(file_path))
                all_cache_ops.extend(cache_ops)

                # Elasticsearch解析
                es_queries = es_analyzer.analyze_file(str(file_path))
                all_queries.extend(es_queries)

                # トランザクション解析
                transactions = tx_analyzer.analyze_file(str(file_path))
                all_transactions.extend(transactions)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        # サマリー作成
        summary = {
            "total_files": len(files),
            "total_queries": len(all_queries),
            "total_transactions": len(all_transactions),
            "total_cache_operations": len(all_cache_ops),
            "n_plus_one_risks": sum(1 for q in all_queries if q.n_plus_one_risk),
            "complex_queries": sum(1 for q in all_queries if q.complexity > 5.0),
            "high_deadlock_risk": sum(
                1 for t in all_transactions
                if tx_analyzer.assess_deadlock_risk(all_queries) == "high"
            ),
        }

        return AnalysisResponse(
            status="success",
            queries=[q.model_dump() for q in all_queries],
            transactions=[t.model_dump() for t in all_transactions],
            cache_operations=[op.model_dump() for op in all_cache_ops],
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Directory analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact/database", response_model=DatabaseImpactResponse)
async def analyze_database_impact(request: DatabaseImpactRequest):
    """
    特定のデータベースエンティティへの影響を分析

    Args:
        request: 影響分析リクエスト

    Returns:
        影響分析結果
    """
    try:
        # 実装例：エンティティ名からクエリを検索
        affected_queries = []
        affected_methods = set()

        # リスク評価ロジック（簡易版）
        risk_level = "low"
        if len(affected_queries) > 10:
            risk_level = "high"
        elif len(affected_queries) > 5:
            risk_level = "medium"

        recommendations = [
            "Ensure proper indexing on the entity",
            "Review query complexity and optimize if needed",
            "Consider caching frequently accessed data",
            "Monitor query performance in production",
        ]

        return DatabaseImpactResponse(
            entity_name=request.entity_name,
            database_type=request.database_type.value,
            affected_queries=affected_queries,
            affected_methods=list(affected_methods),
            risk_assessment=risk_level,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Impact analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント

    Returns:
        ステータス情報
    """
    return {
        "status": "healthy",
        "version": "4.0.0",
        "analyzers": {
            "sql": "available",
            "redis": "available",
            "elasticsearch": "available",
            "transaction": "available",
        }
    }


# アプリにルーターを登録
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
