"""
Database analysis data models
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class QueryType(str, Enum):
    """Type of database query"""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CQL = "CQL"  # Cassandra Query Language
    DSL = "DSL"  # Elasticsearch Domain Specific Language
    CACHE_GET = "CACHE_GET"
    CACHE_SET = "CACHE_SET"
    CACHE_DELETE = "CACHE_DELETE"


class DatabaseType(str, Enum):
    """Supported database types"""

    MYSQL = "mysql"
    SQL_SERVER = "sqlserver"
    CASSANDRA = "cassandra"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"


class ConsistencyLevel(str, Enum):
    """Cassandra consistency levels"""

    ONE = "ONE"
    TWO = "TWO"
    THREE = "THREE"
    QUORUM = "QUORUM"
    ALL = "ALL"
    LOCAL_QUORUM = "LOCAL_QUORUM"
    EACH_QUORUM = "EACH_QUORUM"
    LOCAL_ONE = "LOCAL_ONE"
    ANY = "ANY"


class CachePattern(str, Enum):
    """Redis cache patterns"""

    CACHE_ASIDE = "cache_aside"
    READ_THROUGH = "read_through"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


class DatabaseQuery(BaseModel):
    """Represents a database query found in code"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    query_text: str = Field(..., description="The SQL/CQL/DSL query text")
    query_type: QueryType
    database: DatabaseType
    file_path: str = Field(..., description="Source file containing the query")
    line_number: int = Field(..., description="Line number in source file")
    method_name: Optional[str] = Field(None, description="Method containing the query")
    class_name: Optional[str] = Field(None, description="Class containing the query")

    # Query characteristics
    is_prepared: bool = Field(
        default=False, description="Whether query uses prepared statements"
    )
    has_parameters: bool = Field(default=False, description="Whether query has parameters")
    is_in_loop: bool = Field(
        default=False, description="Whether query is executed in a loop (N+1 risk)"
    )
    is_async: bool = Field(default=False, description="Whether query is async")

    # Performance metrics
    complexity: float = Field(default=1.0, description="Query complexity score (1-10)")
    estimated_rows: Optional[int] = Field(None, description="Estimated rows returned")
    has_index: bool = Field(default=True, description="Whether query uses indexes")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")

    # Cassandra specific
    consistency_level: Optional[ConsistencyLevel] = None
    uses_partition_key: bool = Field(
        default=False, description="Whether query uses partition key"
    )
    has_allow_filtering: bool = Field(default=False, description="Uses ALLOW FILTERING")

    # Elasticsearch specific
    uses_script: bool = Field(default=False, description="Uses scripting")
    has_wildcard: bool = Field(default=False, description="Uses wildcard queries")

    # Issues detected
    n_plus_one_risk: bool = Field(default=False, description="Potential N+1 problem")
    missing_transaction: bool = Field(
        default=False, description="Write query without transaction"
    )

    class Config:
        use_enum_values = True


class DatabaseEntity(BaseModel):
    """Represents a database entity (table, collection, index)"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Entity name (table/collection/index)")
    type: str = Field(..., description="table|collection|index|cache_key")
    database: DatabaseType
    schema: Optional[str] = Field(None, description="Schema/namespace name")

    # Metadata
    estimated_size: Optional[int] = Field(None, description="Estimated row/document count")
    has_index: bool = Field(default=True, description="Whether entity has indexes")
    primary_key: List[str] = Field(default_factory=list)
    foreign_keys: List[str] = Field(default_factory=list)

    # Access patterns
    access_frequency: str = Field(default="medium", description="high|medium|low")
    read_write_ratio: Optional[float] = Field(None, description="Read/write ratio")

    class Config:
        use_enum_values = True


class TransactionBoundary(BaseModel):
    """Represents a transaction boundary in code"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str = Field(..., description="begin|commit|rollback")
    file_path: str
    line_number: int
    method_id: str = Field(..., description="Method containing transaction")

    # Transaction properties
    isolation_level: Optional[str] = Field(
        None, description="READ_COMMITTED|SERIALIZABLE|etc"
    )
    is_distributed: bool = Field(
        default=False, description="Spans multiple databases"
    )
    timeout: Optional[int] = Field(None, description="Transaction timeout in milliseconds")

    # Queries in transaction
    query_ids: List[str] = Field(default_factory=list, description="IDs of queries in transaction")
    database_count: int = Field(default=1, description="Number of databases involved")

    # Risk assessment
    deadlock_risk: str = Field(default="low", description="high|medium|low")
    consistency_risk: str = Field(default="low", description="high|medium|low")


class CacheOperation(BaseModel):
    """Represents a Redis cache operation"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    operation: str = Field(..., description="get|set|delete|expire")
    key_pattern: str = Field(..., description="Cache key pattern (e.g., user:*:profile)")
    file_path: str
    line_number: int
    method_name: Optional[str] = None

    # Cache properties
    ttl: Optional[int] = Field(None, description="Time-to-live in seconds")
    is_distributed: bool = Field(default=True, description="Distributed cache")
    cache_pattern: Optional[CachePattern] = None

    # Related entities
    entity_name: Optional[str] = Field(
        None, description="Database entity being cached"
    )
    invalidation_points: List[str] = Field(
        default_factory=list, description="Methods that invalidate this cache"
    )

    # Issues
    missing_ttl: bool = Field(default=False, description="No TTL set")
    missing_invalidation: bool = Field(
        default=False, description="Data update without cache invalidation"
    )

    class Config:
        use_enum_values = True


class ConnectionPool(BaseModel):
    """Represents a database connection pool configuration"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    database: DatabaseType
    max_connections: int = Field(..., description="Maximum connections in pool")
    min_connections: int = Field(default=0, description="Minimum connections")
    timeout: int = Field(default=30000, description="Connection timeout in milliseconds")
    config_file: Optional[str] = Field(None, description="Configuration file path")

    # Usage tracking
    usage_locations: List[str] = Field(
        default_factory=list, description="Files using this pool"
    )
    estimated_usage: int = Field(default=0, description="Estimated concurrent usage")
    utilization_level: str = Field(default="medium", description="high|medium|low")

    # Issues
    potential_exhaustion: bool = Field(
        default=False, description="Risk of pool exhaustion"
    )

    class Config:
        use_enum_values = True


class DataAccessLayer(BaseModel):
    """Represents a DAO/Repository layer"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="DAO/Repository name")
    type: str = Field(..., description="DAO|Repository|Mapper")
    framework: str = Field(
        ..., description="MyBatis|Hibernate|Spring Data|Custom"
    )
    database: DatabaseType
    entity_name: str = Field(..., description="Entity being accessed")

    # Methods
    methods: List[str] = Field(default_factory=list, description="Method names")
    file_path: str

    # Configuration
    connection_pool_id: Optional[str] = None
    transaction_manager: Optional[str] = None

    class Config:
        use_enum_values = True
