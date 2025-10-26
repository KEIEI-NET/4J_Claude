"""
Neo4j Database Client

Neo4jデータベースへの接続、トランザクション、クエリ実行を管理します。
"""

import logging
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..models.schema import GraphNode, GraphRelationship, SCHEMA_CONSTRAINTS

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4jデータベースクライアント"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Args:
            uri: Neo4j接続URI (例: bolt://localhost:7687)
            user: ユーザー名
            password: パスワード
            database: データベース名
        """
        self.uri = uri
        self.user = user
        self.database = database
        self._driver: Optional[Driver] = None

        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"Connected to Neo4j at {uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self) -> None:
        """データベース接続を閉じる"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self) -> "Neo4jClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.close()

    def verify_connectivity(self) -> bool:
        """接続確認"""
        try:
            if not self._driver:
                return False
            with self._driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as num")
                record = result.single()
                return record is not None and record["num"] == 1
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False

    def initialize_schema(self) -> None:
        """スキーマの初期化（制約とインデックス）"""
        logger.info("Initializing Neo4j schema...")

        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        with self._driver.session(database=self.database) as session:
            # 制約とインデックスを作成
            for statement in SCHEMA_CONSTRAINTS.strip().split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("//"):
                    try:
                        session.run(statement)
                        logger.debug(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        logger.warning(f"Schema statement failed: {e}")

        logger.info("Schema initialization complete")

    def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Cypherクエリを実行

        Args:
            query: Cypherクエリ
            parameters: クエリパラメータ

        Returns:
            クエリ結果のリスト
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        with self._driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def create_node(self, node: GraphNode) -> str:
        """
        ノードを作成

        Args:
            node: 作成するノード

        Returns:
            作成されたノードのID
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        query = f"""
        CREATE (n:{node.node_type.value} $properties)
        RETURN elementId(n) as node_id
        """

        with self._driver.session(database=self.database) as session:
            result = session.run(query, {"properties": node.properties})
            record = result.single()
            if not record:
                raise RuntimeError("Failed to create node")
            return str(record["node_id"])

    def create_relationship(self, rel: GraphRelationship) -> None:
        """
        リレーションシップを作成

        Args:
            rel: 作成するリレーションシップ
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        query = f"""
        MATCH (a), (b)
        WHERE elementId(a) = $from_id AND elementId(b) = $to_id
        CREATE (a)-[r:{rel.relation_type.value} $properties]->(b)
        """

        with self._driver.session(database=self.database) as session:
            session.run(
                query,
                {
                    "from_id": rel.from_node,
                    "to_id": rel.to_node,
                    "properties": rel.properties,
                },
            )

    def batch_create_nodes(
        self, nodes: List[GraphNode], batch_size: int = 1000
    ) -> List[str]:
        """
        複数のノードをバッチ作成

        Args:
            nodes: 作成するノードのリスト
            batch_size: バッチサイズ（デフォルト: 1000）

        Returns:
            作成されたノードのIDリスト
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        node_ids = []

        # ノードをバッチサイズごとに分割
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i : i + batch_size]

            with self._driver.session(database=self.database) as session:
                # バッチごとにトランザクションを実行
                with session.begin_transaction() as tx:
                    for node in batch:
                        query = f"""
                        CREATE (n:{node.node_type.value} $properties)
                        RETURN elementId(n) as node_id
                        """
                        result = tx.run(query, {"properties": node.properties})
                        record = result.single()
                        if record:
                            node_ids.append(str(record["node_id"]))

                    tx.commit()
                    logger.debug(f"Created batch of {len(batch)} nodes")

        logger.info(f"Batch created {len(node_ids)} nodes")
        return node_ids

    def batch_create_relationships(
        self, relationships: List[GraphRelationship], batch_size: int = 1000
    ) -> int:
        """
        複数のリレーションシップをバッチ作成

        Args:
            relationships: 作成するリレーションシップのリスト
            batch_size: バッチサイズ（デフォルト: 1000）

        Returns:
            作成されたリレーションシップの数
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        created_count = 0

        # リレーションシップをバッチサイズごとに分割
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i : i + batch_size]

            with self._driver.session(database=self.database) as session:
                with session.begin_transaction() as tx:
                    for rel in batch:
                        query = f"""
                        MATCH (a), (b)
                        WHERE elementId(a) = $from_id AND elementId(b) = $to_id
                        CREATE (a)-[r:{rel.relation_type.value} $properties]->(b)
                        """
                        tx.run(
                            query,
                            {
                                "from_id": rel.from_node,
                                "to_id": rel.to_node,
                                "properties": rel.properties,
                            },
                        )
                        created_count += 1

                    tx.commit()
                    logger.debug(f"Created batch of {len(batch)} relationships")

        logger.info(f"Batch created {created_count} relationships")
        return created_count

    def with_transaction(self, func, *args, **kwargs) -> Any:
        """
        トランザクション内で関数を実行

        Args:
            func: 実行する関数（第一引数はトランザクション）
            *args: 関数への引数
            **kwargs: 関数へのキーワード引数

        Returns:
            関数の戻り値

        Example:
            def create_graph(tx, nodes, rels):
                for node in nodes:
                    tx.run("CREATE (:Node $props)", props=node)

            client.with_transaction(create_graph, nodes, rels)
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        with self._driver.session(database=self.database) as session:
            with session.begin_transaction() as tx:
                try:
                    result = func(tx, *args, **kwargs)
                    tx.commit()
                    logger.debug("Transaction committed successfully")
                    return result
                except Exception as e:
                    tx.rollback()
                    logger.error(f"Transaction rolled back due to: {e}")
                    raise

    def clear_all(self) -> None:
        """全データを削除（テスト用）"""
        logger.warning("Deleting all nodes and relationships")
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        with self._driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
