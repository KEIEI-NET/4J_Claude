"""
Graph Builder

Phase 1の分析結果をNeo4jグラフ構造に変換します。
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from ..models.schema import (
    GraphNode,
    GraphRelationship,
    NodeType,
    RelationType,
    FileNode,
    ClassNode,
    MethodNode,
    CQLQueryNode,
    TableNode,
    IssueNode,
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    分析結果からグラフを構築するクラス

    Phase 1の分析結果（AnalysisResult、Issue、CassandraCall）を
    Neo4jグラフのノードとリレーションシップに変換します。
    """

    def __init__(self):
        """初期化"""
        self._node_id_map: Dict[str, str] = {}  # キー -> Neo4j node_id
        self._created_nodes: List[GraphNode] = []
        self._created_relationships: List[GraphRelationship] = []

    def build_from_analysis_result(
        self, analysis_result: dict
    ) -> Tuple[List[GraphNode], List[GraphRelationship]]:
        """
        分析結果からグラフを構築

        Args:
            analysis_result: Phase 1の分析結果（辞書形式）

        Returns:
            (ノードリスト, リレーションシップリスト)
        """
        self._created_nodes.clear()
        self._created_relationships.clear()
        self._node_id_map.clear()

        # 1. ファイルノードを作成
        # バッチ分析結果の場合: analyzed_files フィールド
        for file_path in analysis_result.get("analyzed_files", []):
            self._create_file_node(file_path)

        # 単一ファイル分析結果の場合: file フィールド
        if "file" in analysis_result and "analyzed_files" not in analysis_result:
            self._create_file_node(analysis_result["file"])

        # 2. 問題からクラス、メソッド、クエリ、テーブル、問題ノードを作成
        for issue in analysis_result.get("issues", []):
            self._process_issue(issue)

        logger.info(
            f"Built graph: {len(self._created_nodes)} nodes, "
            f"{len(self._created_relationships)} relationships"
        )

        return self._created_nodes, self._created_relationships

    def _create_file_node(self, file_path: str) -> str:
        """
        ファイルノードを作成

        Args:
            file_path: ファイルパス

        Returns:
            ノードの一意キー
        """
        node_key = f"file:{file_path}"
        if node_key in self._node_id_map:
            return node_key

        path_obj = Path(file_path)
        file_node = FileNode(
            node_id=node_key,
            path=file_path,
            language="java",
            size_bytes=path_obj.stat().st_size if path_obj.exists() else 0,
            properties={
                "path": file_path,
                "language": "java",
                "size_bytes": path_obj.stat().st_size if path_obj.exists() else 0,
            },
        )

        self._created_nodes.append(file_node)
        self._node_id_map[node_key] = node_key
        logger.debug(f"Created FileNode: {file_path}")
        return node_key

    def _process_issue(self, issue: dict) -> None:
        """
        問題からノードとリレーションシップを作成

        Args:
            issue: 問題情報（辞書形式）
        """
        file_path = issue.get("file", "")
        line_number = issue.get("line", 0)
        cql_text = issue.get("cql", "")

        # ファイルノードを取得/作成
        file_key = self._create_file_node(file_path)

        # クラス情報を抽出（ファイル名から推測）
        class_name = self._extract_class_name(file_path)
        class_key = self._create_class_node(class_name, file_path, file_key)

        # メソッド情報を抽出（issue typeから推測）
        method_name = self._extract_method_name(issue)
        method_key = self._create_method_node(
            method_name, class_name, class_key, line_number
        )

        # CQLクエリノードを作成
        query_key = self._create_cql_query_node(
            cql_text, method_name, method_key, line_number
        )

        # テーブルノードを作成（CQLから抽出）
        table_names = self._extract_table_names(cql_text)
        for table_name in table_names:
            table_key = self._create_table_node(table_name)
            # Query -> Table リレーションシップ
            self._create_relationship(query_key, table_key, RelationType.ACCESSES)

        # 問題ノードを作成
        issue_key = self._create_issue_node(issue)

        # Method/Query -> Issue リレーションシップ
        self._create_relationship(query_key, issue_key, RelationType.HAS_ISSUE)

    def _create_class_node(
        self, class_name: str, file_path: str, file_key: str
    ) -> str:
        """クラスノードを作成"""
        node_key = f"class:{file_path}:{class_name}"
        if node_key in self._node_id_map:
            return node_key

        package_name = self._extract_package_name(file_path)
        class_node = ClassNode(
            node_id=node_key,
            name=class_name,
            package=package_name,
            file_path=file_path,
            start_line=1,
            end_line=1000,
            properties={
                "name": class_name,
                "package": package_name,
                "file_path": file_path,
            },
        )

        self._created_nodes.append(class_node)
        self._node_id_map[node_key] = node_key

        # File -> Class リレーションシップ
        self._create_relationship(file_key, node_key, RelationType.CONTAINS)

        logger.debug(f"Created ClassNode: {class_name}")
        return node_key

    def _create_method_node(
        self, method_name: str, class_name: str, class_key: str, line_number: int
    ) -> str:
        """メソッドノードを作成"""
        node_key = f"method:{class_name}:{method_name}:{line_number}"
        if node_key in self._node_id_map:
            return node_key

        method_node = MethodNode(
            node_id=node_key,
            name=method_name,
            signature=f"{method_name}()",
            class_name=class_name,
            start_line=line_number,
            end_line=line_number + 10,
            properties={
                "name": method_name,
                "signature": f"{method_name}()",
                "class_name": class_name,
            },
        )

        self._created_nodes.append(method_node)
        self._node_id_map[node_key] = node_key

        # Class -> Method リレーションシップ
        self._create_relationship(class_key, node_key, RelationType.DEFINES)

        logger.debug(f"Created MethodNode: {method_name}")
        return node_key

    def _create_cql_query_node(
        self, cql_text: str, method_name: str, method_key: str, line_number: int
    ) -> str:
        """CQLクエリノードを作成"""
        node_key = f"query:{method_name}:{line_number}"
        if node_key in self._node_id_map:
            return node_key

        query_type = self._extract_query_type(cql_text)
        query_node = CQLQueryNode(
            node_id=node_key,
            cql=cql_text,
            query_type=query_type,
            method_name=method_name,
            line_number=line_number,
            properties={
                "cql": cql_text,
                "query_type": query_type,
                "method_name": method_name,
                "line_number": line_number,
            },
        )

        self._created_nodes.append(query_node)
        self._node_id_map[node_key] = node_key

        # Method -> Query リレーションシップ
        self._create_relationship(method_key, node_key, RelationType.EXECUTES)

        logger.debug(f"Created CQLQueryNode: {query_type}")
        return node_key

    def _create_table_node(self, table_name: str) -> str:
        """テーブルノードを作成"""
        node_key = f"table:{table_name}"
        if node_key in self._node_id_map:
            return node_key

        table_node = TableNode(
            node_id=node_key,
            name=table_name,
            keyspace=None,
            database_type="cassandra",
            properties={"name": table_name, "database_type": "cassandra"},
        )

        self._created_nodes.append(table_node)
        self._node_id_map[node_key] = node_key
        logger.debug(f"Created TableNode: {table_name}")
        return node_key

    def _create_issue_node(self, issue: dict) -> str:
        """問題ノードを作成"""
        issue_type = issue.get("type", "")
        severity = issue.get("severity", "medium")
        line = issue.get("line", 0)

        node_key = f"issue:{issue_type}:{line}"
        if node_key in self._node_id_map:
            return node_key

        issue_node = IssueNode(
            node_id=node_key,
            issue_type=issue_type,
            severity=severity,
            message=issue.get("message", ""),
            recommendation=issue.get("recommendation", ""),
            confidence=issue.get("confidence", 1.0),
            properties={
                "issue_type": issue_type,
                "severity": severity,
                "message": issue.get("message", ""),
                "recommendation": issue.get("recommendation", ""),
                "confidence": issue.get("confidence", 1.0),
                "detector": issue.get("detector", ""),
            },
        )

        self._created_nodes.append(issue_node)
        self._node_id_map[node_key] = node_key
        logger.debug(f"Created IssueNode: {issue_type} ({severity})")
        return node_key

    def _create_relationship(
        self,
        from_key: str,
        to_key: str,
        relation_type: RelationType,
        properties: Optional[Dict] = None,
    ) -> None:
        """リレーションシップを作成"""
        rel = GraphRelationship(
            from_node=from_key,
            to_node=to_key,
            relation_type=relation_type,
            properties=properties or {},
        )
        self._created_relationships.append(rel)
        logger.debug(f"Created relationship: {from_key} -{relation_type.value}-> {to_key}")

    # ===== ユーティリティメソッド =====

    def _extract_class_name(self, file_path: str) -> str:
        """ファイルパスからクラス名を抽出"""
        path_obj = Path(file_path)
        return path_obj.stem  # 拡張子を除いたファイル名

    def _extract_package_name(self, file_path: str) -> Optional[str]:
        """ファイルパスからパッケージ名を推測"""
        # 例: src/main/java/com/example/dao/UserDAO.java -> com.example.dao
        parts = Path(file_path).parts
        try:
            java_idx = parts.index("java")
            package_parts = parts[java_idx + 1 : -1]
            return ".".join(package_parts) if package_parts else None
        except (ValueError, IndexError):
            return None

    def _extract_method_name(self, issue: dict) -> str:
        """問題情報からメソッド名を推測"""
        # とりあえずissue typeから推測
        issue_type = issue.get("type", "unknownMethod")
        return f"method_{issue_type.lower()}"

    def _extract_query_type(self, cql_text: str) -> str:
        """CQLからクエリタイプを抽出"""
        cql_upper = cql_text.strip().upper()
        if cql_upper.startswith("SELECT"):
            return "SELECT"
        elif cql_upper.startswith("INSERT"):
            return "INSERT"
        elif cql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif cql_upper.startswith("DELETE"):
            return "DELETE"
        elif cql_upper.startswith("BATCH") or cql_upper.startswith("BEGIN BATCH"):
            return "BATCH"
        return "UNKNOWN"

    def _extract_table_names(self, cql_text: str) -> List[str]:
        """CQLからテーブル名を抽出"""
        tables = []

        # FROM句からテーブル名を抽出
        from_pattern = r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        from_matches = re.findall(from_pattern, cql_text, re.IGNORECASE)
        tables.extend(from_matches)

        # INSERT INTO句からテーブル名を抽出
        insert_pattern = r"\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        insert_matches = re.findall(insert_pattern, cql_text, re.IGNORECASE)
        tables.extend(insert_matches)

        # UPDATE句からテーブル名を抽出
        update_pattern = r"\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        update_matches = re.findall(update_pattern, cql_text, re.IGNORECASE)
        tables.extend(update_matches)

        return list(set(tables))  # 重複除去
