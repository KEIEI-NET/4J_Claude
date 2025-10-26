"""
Neo4j Client for Graph Queries

Phase 4 可視化レイヤーでNeo4jグラフDBと通信するクライアント
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4jデータベースクライアント"""

    def __init__(self, uri: str, user: str, password: str):
        """
        初期化

        Args:
            uri: Neo4j接続URI (例: bolt://localhost:7687)
            user: ユーザー名
            password: パスワード
        """
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Neo4j client initialized: {uri}")

    def close(self) -> None:
        """接続を閉じる"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self) -> Session:
        """セッションコンテキストマネージャー"""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()

    def get_file_dependencies(
        self, file_path: str, depth: int = 1
    ) -> Dict[str, Any]:
        """
        指定されたファイルの依存関係を取得

        Args:
            file_path: ファイルパス
            depth: 取得する深さ (デフォルト: 1)

        Returns:
            {
                'file': ファイル情報,
                'dependencies': 依存先リスト,
                'dependents': 依存元リスト
            }
        """
        with self.session() as session:
            query = """
            MATCH (f:File {path: $path})
            OPTIONAL MATCH (f)-[:DEPENDS_ON]->(dep:File)
            OPTIONAL MATCH (f)<-[:DEPENDS_ON]-(dependent:File)
            RETURN f,
                   collect(DISTINCT dep) AS dependencies,
                   collect(DISTINCT dependent) AS dependents
            """

            result = session.run(query, path=file_path)
            record = result.single()

            if not record:
                return {
                    'file': None,
                    'dependencies': [],
                    'dependents': []
                }

            file_node = record['f']
            dependencies = [self._node_to_dict(dep) for dep in record['dependencies'] if dep]
            dependents = [self._node_to_dict(dep) for dep in record['dependents'] if dep]

            return {
                'file': self._node_to_dict(file_node),
                'dependencies': dependencies,
                'dependents': dependents
            }

    def get_impact_range(
        self,
        file_path: str,
        max_depth: int = 3,
        include_indirect: bool = True
    ) -> List[Dict[str, Any]]:
        """
        影響範囲を取得 (BFS探索)

        Args:
            file_path: 対象ファイルパス
            max_depth: 最大深さ
            include_indirect: 間接的な依存も含めるか

        Returns:
            影響を受けるファイルのリスト
        """
        with self.session() as session:
            if include_indirect:
                # 間接的な依存も含める
                query = """
                MATCH path = (target:File {path: $path})<-[:DEPENDS_ON*1..$max_depth]-(affected:File)
                RETURN DISTINCT affected.path AS file_path,
                       affected.name AS file_name,
                       affected.language AS language,
                       length(path) AS distance,
                       1.0 / length(path) AS weight
                ORDER BY distance ASC, file_path ASC
                """
            else:
                # 直接依存のみ
                query = """
                MATCH (target:File {path: $path})<-[dep:DEPENDS_ON]-(affected:File)
                RETURN DISTINCT affected.path AS file_path,
                       affected.name AS file_name,
                       affected.language AS language,
                       1 AS distance,
                       COALESCE(dep.strength, 1.0) AS weight
                ORDER BY weight DESC, file_path ASC
                """

            result = session.run(query, path=file_path, max_depth=max_depth)

            affected_files = []
            for record in result:
                affected_files.append({
                    'path': record['file_path'],
                    'name': record['file_name'],
                    'language': record['language'],
                    'distance': record['distance'],
                    'weight': record['weight'],
                    'risk_contribution': record['weight']
                })

            return affected_files

    def get_neighbors(
        self,
        node_id: str,
        node_type: str = "File",
        depth: int = 1,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """
        ノードの隣接ノードを取得 (グラフ可視化用)

        Args:
            node_id: ノードID (例: file_path)
            node_type: ノードタイプ (File, Class, Method)
            depth: 深さ
            direction: 方向 (in, out, both)

        Returns:
            {
                'center_node': 中心ノード,
                'neighbors': 隣接ノード+エッジのリスト
            }
        """
        with self.session() as session:
            # 方向に応じてクエリを変更
            if direction == "in":
                rel_pattern = "<-[r:DEPENDS_ON|CALLS*1..$depth]-"
            elif direction == "out":
                rel_pattern = "-[r:DEPENDS_ON|CALLS*1..$depth]->"
            else:  # both
                rel_pattern = "-[r:DEPENDS_ON|CALLS*1..$depth]-"

            query = f"""
            MATCH (center:{node_type} {{path: $node_id}})
            OPTIONAL MATCH path = (center){rel_pattern}(neighbor)
            RETURN center,
                   collect(DISTINCT neighbor) AS neighbors,
                   collect(DISTINCT r) AS relationships
            """

            result = session.run(query, node_id=node_id, depth=depth)
            record = result.single()

            if not record:
                return {
                    'center_node': None,
                    'neighbors': []
                }

            center = self._node_to_dict(record['center'])
            neighbors = []

            for neighbor_node in record['neighbors']:
                if neighbor_node:
                    neighbors.append({
                        'node': self._node_to_dict(neighbor_node),
                        'relationship': {
                            'type': 'DEPENDS_ON',  # Simplified
                            'direction': 'outgoing'
                        }
                    })

            return {
                'center_node': center,
                'neighbors': neighbors
            }

    def find_path(
        self,
        source_path: str,
        target_path: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        2つのノード間のパスを検索

        Args:
            source_path: 開始ノードのパス
            target_path: 終了ノードのパス
            max_depth: 最大深さ

        Returns:
            パスのリスト
        """
        with self.session() as session:
            query = """
            MATCH path = shortestPath(
                (source:File {path: $source_path})-[:DEPENDS_ON|CALLS*1..$max_depth]-(target:File {path: $target_path})
            )
            RETURN [node in nodes(path) | {
                type: labels(node)[0],
                name: COALESCE(node.name, node.path),
                path: node.path
            }] AS nodes,
            [rel in relationships(path) | {
                type: type(rel),
                strength: COALESCE(rel.strength, 1.0)
            }] AS relationships,
            length(path) AS path_length
            """

            result = session.run(
                query,
                source_path=source_path,
                target_path=target_path,
                max_depth=max_depth
            )

            paths = []
            for record in result:
                paths.append({
                    'length': record['path_length'],
                    'nodes': record['nodes'],
                    'relationships': record['relationships']
                })

            return paths

    def find_circular_dependencies(
        self, min_cycle_length: int = 2, max_cycle_length: int = 10
    ) -> List[Dict[str, Any]]:
        """
        循環依存を検出

        Args:
            min_cycle_length: 最小サイクル長
            max_cycle_length: 最大サイクル長

        Returns:
            循環依存のリスト
        """
        with self.session() as session:
            query = f"""
            MATCH path = (n:File)-[:DEPENDS_ON*{min_cycle_length}..{max_cycle_length}]->(n)
            WHERE ALL(node in nodes(path) WHERE node:File)
            RETURN DISTINCT [node in nodes(path) | node.name] AS cycle,
                   length(path) AS cycle_length
            ORDER BY cycle_length ASC
            LIMIT 20
            """

            result = session.run(query)

            cycles = []
            for record in result:
                cycles.append({
                    'cycle_id': f"cycle-{len(cycles) + 1}",
                    'cycle_length': record['cycle_length'],
                    'nodes': record['cycle'],
                    'severity': self._assess_cycle_severity(record['cycle_length'])
                })

            return cycles

    def _node_to_dict(self, node: Any) -> Dict[str, Any]:
        """Neo4jノードを辞書に変換"""
        if node is None:
            return {}

        return {
            'id': node.element_id,
            'labels': list(node.labels),
            'properties': dict(node)
        }

    def _assess_cycle_severity(self, cycle_length: int) -> str:
        """サイクルの重要度を評価"""
        if cycle_length <= 3:
            return "high"
        elif cycle_length <= 6:
            return "medium"
        else:
            return "low"

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS num")
                record = result.single()
                return record['num'] == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
