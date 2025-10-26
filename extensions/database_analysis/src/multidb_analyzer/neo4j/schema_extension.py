"""
Neo4j Schema Extension for Multi-Database Analysis

Phase 4で追加されるデータベース関連ノード・関係を定義
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DatabaseNodeType(str, Enum):
    """データベース関連ノードタイプ"""
    DATABASE_QUERY = "DatabaseQuery"
    DATABASE_ENTITY = "DatabaseEntity"
    TRANSACTION_BOUNDARY = "TransactionBoundary"
    CACHE_OPERATION = "CacheOperation"
    CONNECTION_POOL = "ConnectionPool"
    DATA_ACCESS_LAYER = "DataAccessLayer"


class DatabaseRelationType(str, Enum):
    """データベース関連関係タイプ"""
    EXECUTES_QUERY = "EXECUTES_QUERY"
    ACCESSES_ENTITY = "ACCESSES_ENTITY"
    IN_TRANSACTION = "IN_TRANSACTION"
    INVALIDATES_CACHE = "INVALIDATES_CACHE"
    USES_POOL = "USES_POOL"
    IMPLEMENTS_DAO = "IMPLEMENTS_DAO"


class DatabaseQueryNode(BaseModel):
    """データベースクエリノード"""
    node_id: str
    query_text: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, CQL, DSL
    database: str  # mysql, sqlserver, cassandra, elasticsearch, redis
    file_path: str
    line_number: int
    is_prepared: bool = False
    has_parameters: bool = False
    complexity: float = 1.0
    has_index: Optional[bool] = None
    is_in_loop: bool = False
    n_plus_one_risk: bool = False

    properties: Dict[str, Any] = Field(default_factory=dict)


class DatabaseEntityNode(BaseModel):
    """データベースエンティティノード (テーブル/コレクション/インデックス)"""
    node_id: str
    name: str
    entity_type: str  # table, collection, index, cache_key
    database: str
    schema: Optional[str] = None
    estimated_size: Optional[int] = None
    has_index: bool = False
    primary_key: List[str] = Field(default_factory=list)
    foreign_keys: List[str] = Field(default_factory=list)
    access_frequency: Optional[str] = None  # high, medium, low

    properties: Dict[str, Any] = Field(default_factory=dict)


class TransactionBoundaryNode(BaseModel):
    """トランザクション境界ノード"""
    node_id: str
    boundary_type: str  # begin, commit, rollback
    file_path: str
    line_number: int
    method_id: Optional[str] = None
    isolation_level: Optional[str] = None
    is_distributed: bool = False
    timeout: Optional[int] = None

    properties: Dict[str, Any] = Field(default_factory=dict)


class CacheOperationNode(BaseModel):
    """キャッシュ操作ノード (Redis特化)"""
    node_id: str
    operation: str  # get, set, delete, expire
    key_pattern: str
    file_path: str
    line_number: int
    ttl: Optional[int] = None
    missing_ttl: bool = False
    method_name: Optional[str] = None
    cache_pattern: Optional[str] = None  # CACHE_ASIDE, WRITE_THROUGH

    properties: Dict[str, Any] = Field(default_factory=dict)


class ExecutesQueryRelationship(BaseModel):
    """メソッド-クエリ実行関係"""
    from_node_id: str  # Method node
    to_node_id: str  # DatabaseQuery node
    frequency: int = 1
    is_conditional: bool = False
    is_in_loop: bool = False
    is_async: bool = False
    line_number: int

    properties: Dict[str, Any] = Field(default_factory=dict)


class AccessesEntityRelationship(BaseModel):
    """クエリ-エンティティアクセス関係"""
    from_node_id: str  # DatabaseQuery node
    to_node_id: str  # DatabaseEntity node
    operation: str  # read, write, readwrite
    is_indexed: bool = False

    properties: Dict[str, Any] = Field(default_factory=dict)


class InTransactionRelationship(BaseModel):
    """クエリ-トランザクション関係"""
    from_node_id: str  # DatabaseQuery node
    to_node_id: str  # TransactionBoundary node
    position: int = 0  # トランザクション内の実行順序

    properties: Dict[str, Any] = Field(default_factory=dict)


def to_neo4j_properties(node: BaseModel) -> Dict[str, Any]:
    """
    Pydanticモデルをnx4jプロパティ辞書に変換

    Args:
        node: ノードモデル

    Returns:
        Neo4jプロパティ辞書
    """
    props = node.model_dump(exclude={'node_id', 'properties'})

    # カスタムプロパティをマージ
    if hasattr(node, 'properties'):
        props.update(node.properties)

    # Noneは除外
    props = {k: v for k, v in props.items() if v is not None}

    # リストは文字列に変換
    for key, value in props.items():
        if isinstance(value, list):
            props[key] = ','.join(str(v) for v in value)

    return props
