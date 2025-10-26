"""
Multi-Database Analyzer - Phase 4

Comprehensive database analysis framework supporting:
- MySQL / SQL Server (N+1 detection, transaction analysis)
- Redis (cache consistency analysis)
- Elasticsearch (query DSL optimization)
- Cassandra (consistency level validation - extends Phase 1)

Detects:
- N+1 query problems
- Missing transaction boundaries
- Cache invalidation issues
- Connection leaks
- Cross-database consistency risks
"""

__version__ = "4.0.0"
__author__ = "4J_Claude Team"

from multidb_analyzer.models.database_models import (
    DatabaseQuery,
    DatabaseEntity,
    TransactionBoundary,
    CacheOperation,
    QueryType,
    DatabaseType,
)

__all__ = [
    "DatabaseQuery",
    "DatabaseEntity",
    "TransactionBoundary",
    "CacheOperation",
    "QueryType",
    "DatabaseType",
]
