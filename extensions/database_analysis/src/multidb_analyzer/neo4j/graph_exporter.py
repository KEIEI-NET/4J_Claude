"""
Multi-Database Analysis Graph Exporter

Phase 4のマルチDB分析結果をNeo4jグラフに変換・エクスポート
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from ..models.database_models import (
    DatabaseQuery,
    DatabaseEntity,
    TransactionBoundary,
    CacheOperation,
    DatabaseType,
    QueryType,
)

from .schema_extension import (
    DatabaseQueryNode,
    DatabaseEntityNode,
    TransactionBoundaryNode,
    CacheOperationNode,
    ExecutesQueryRelationship,
    AccessesEntityRelationship,
    InTransactionRelationship,
    to_neo4j_properties,
)

logger = logging.getLogger(__name__)


class MultiDBGraphExporter:
    """マルチDB分析結果をNeo4jグラフに変換するクラス"""

    def __init__(self):
        """初期化"""
        self.nodes: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self._node_id_map: Dict[str, str] = {}

    def export_database_queries(
        self,
        queries: List[DatabaseQuery],
        method_map: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        データベースクエリをグラフノードに変換

        Args:
            queries: データベースクエリリスト
            method_map: メソッド名 -> Neo4jノードIDのマッピング

        Returns:
            (ノードリスト, リレーションシップリスト)
        """
        self.nodes.clear()
        self.relationships.clear()
        self._node_id_map.clear()

        method_map = method_map or {}

        # クエリノードを作成
        for query in queries:
            node = self._create_query_node(query)
            self.nodes.append(node)

            # メソッドとの関係を作成
            if query.method_name and query.method_name in method_map:
                rel = self._create_executes_query_relationship(
                    method_map[query.method_name],
                    node['node_id'],
                    query
                )
                self.relationships.append(rel)

        return self.nodes.copy(), self.relationships.copy()

    def export_database_entities(
        self,
        entities: List[DatabaseEntity]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        データベースエンティティをグラフノードに変換

        Args:
            entities: データベースエンティティリスト

        Returns:
            (ノードリスト, リレーションシップリスト)
        """
        nodes = []
        relationships = []

        for entity in entities:
            node_id = f"entity:{entity.database}:{entity.name}"

            node = {
                'node_id': node_id,
                'label': 'DatabaseEntity',
                'properties': to_neo4j_properties(DatabaseEntityNode(
                    node_id=node_id,
                    name=entity.name,
                    entity_type=entity.type,
                    database=entity.database,
                    schema=entity.schema,
                    estimated_size=entity.estimated_size,
                    has_index=entity.has_index,
                ))
            }
            nodes.append(node)

        return nodes, relationships

    def export_transaction_boundaries(
        self,
        transactions: List[TransactionBoundary],
        query_map: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        トランザクション境界をグラフノードに変換

        Args:
            transactions: トランザクション境界リスト
            query_map: クエリID -> Neo4jノードIDのマッピング

        Returns:
            (ノードリスト, リレーションシップリスト)
        """
        nodes = []
        relationships = []
        query_map = query_map or {}

        for tx in transactions:
            node_id = f"tx:{tx.id}"

            node = {
                'node_id': node_id,
                'label': 'TransactionBoundary',
                'properties': to_neo4j_properties(TransactionBoundaryNode(
                    node_id=node_id,
                    boundary_type=tx.type,
                    file_path=tx.file_path,
                    line_number=tx.line_number,
                    method_id=tx.method_id,
                    isolation_level=tx.isolation_level,
                    is_distributed=tx.is_distributed,
                    timeout=tx.timeout,
                ))
            }
            nodes.append(node)

        return nodes, relationships

    def export_cache_operations(
        self,
        cache_ops: List[CacheOperation]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        キャッシュ操作をグラフノードに変換

        Args:
            cache_ops: キャッシュ操作リスト

        Returns:
            (ノードリスト, リレーションシップリスト)
        """
        nodes = []
        relationships = []

        for op in cache_ops:
            node_id = f"cache:{op.id}"

            node = {
                'node_id': node_id,
                'label': 'CacheOperation',
                'properties': to_neo4j_properties(CacheOperationNode(
                    node_id=node_id,
                    operation=op.operation,
                    key_pattern=op.key_pattern,
                    file_path=op.file_path,
                    line_number=op.line_number,
                    ttl=op.ttl,
                    missing_ttl=op.missing_ttl,
                    method_name=op.method_name,
                    cache_pattern=op.cache_pattern.value if op.cache_pattern else None,
                ))
            }
            nodes.append(node)

        return nodes, relationships

    def _create_query_node(self, query: DatabaseQuery) -> Dict[str, Any]:
        """
        DatabaseQueryからNeo4jノードを作成

        Args:
            query: データベースクエリ

        Returns:
            Neo4jノード辞書
        """
        node_id = f"query:{query.id}"
        self._node_id_map[query.id] = node_id

        query_node = DatabaseQueryNode(
            node_id=node_id,
            query_text=query.query_text,
            query_type=query.query_type.value,
            database=query.database.value,
            file_path=query.file_path,
            line_number=query.line_number,
            is_prepared=query.is_prepared,
            complexity=query.complexity,
            is_in_loop=query.is_in_loop,
            n_plus_one_risk=query.n_plus_one_risk,
        )

        return {
            'node_id': node_id,
            'label': 'DatabaseQuery',
            'properties': to_neo4j_properties(query_node)
        }

    def _create_executes_query_relationship(
        self,
        method_node_id: str,
        query_node_id: str,
        query: DatabaseQuery
    ) -> Dict[str, Any]:
        """
        EXECUTES_QUERY関係を作成

        Args:
            method_node_id: メソッドノードID
            query_node_id: クエリノードID
            query: データベースクエリ

        Returns:
            Neo4j関係辞書
        """
        rel = ExecutesQueryRelationship(
            from_node_id=method_node_id,
            to_node_id=query_node_id,
            frequency=1,
            is_in_loop=query.is_in_loop,
            line_number=query.line_number,
        )

        return {
            'from_node_id': method_node_id,
            'to_node_id': query_node_id,
            'type': 'EXECUTES_QUERY',
            'properties': to_neo4j_properties(rel)
        }

    def create_full_graph(
        self,
        queries: List[DatabaseQuery],
        entities: List[DatabaseEntity],
        transactions: List[TransactionBoundary],
        cache_ops: List[CacheOperation],
        method_map: Optional[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        完全なグラフを作成

        Args:
            queries: クエリリスト
            entities: エンティティリスト
            transactions: トランザクションリスト
            cache_ops: キャッシュ操作リスト
            method_map: メソッドマッピング

        Returns:
            (全ノード, 全リレーションシップ)
        """
        all_nodes = []
        all_relationships = []

        # クエリノードとその関係
        q_nodes, q_rels = self.export_database_queries(queries, method_map)
        all_nodes.extend(q_nodes)
        all_relationships.extend(q_rels)

        # エンティティノード
        e_nodes, e_rels = self.export_database_entities(entities)
        all_nodes.extend(e_nodes)
        all_relationships.extend(e_rels)

        # トランザクションノード
        t_nodes, t_rels = self.export_transaction_boundaries(transactions)
        all_nodes.extend(t_nodes)
        all_relationships.extend(t_rels)

        # キャッシュ操作ノード
        c_nodes, c_rels = self.export_cache_operations(cache_ops)
        all_nodes.extend(c_nodes)
        all_relationships.extend(c_rels)

        logger.info(
            f"Created graph: {len(all_nodes)} nodes, {len(all_relationships)} relationships"
        )

        return all_nodes, all_relationships
