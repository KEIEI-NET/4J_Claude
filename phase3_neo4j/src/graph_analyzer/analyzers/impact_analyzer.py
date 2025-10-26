"""
Impact Analyzer

コード変更の影響範囲を分析します。
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum

from ..graph.neo4j_client import Neo4jClient
from ..models.schema import NodeType, RelationType

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """リスクレベル"""

    CRITICAL = "critical"  # 50+ ファイル影響、または重要なテーブル
    HIGH = "high"  # 20-49 ファイル影響
    MEDIUM = "medium"  # 5-19 ファイル影響
    LOW = "low"  # 1-4 ファイル影響
    MINIMAL = "minimal"  # 影響なし


class ImpactResult:
    """影響分析結果"""

    def __init__(
        self,
        target: str,
        impact_type: str,
        affected_files: List[str],
        affected_classes: List[str],
        affected_methods: List[str],
        risk_level: RiskLevel,
        risk_score: float,
        details: Dict,
    ):
        self.target = target
        self.impact_type = impact_type
        self.affected_files = affected_files
        self.affected_classes = affected_classes
        self.affected_methods = affected_methods
        self.risk_level = risk_level
        self.risk_score = risk_score
        self.details = details

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "target": self.target,
            "impact_type": self.impact_type,
            "affected_files": self.affected_files,
            "affected_files_count": len(self.affected_files),
            "affected_classes": self.affected_classes,
            "affected_methods": self.affected_methods,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "details": self.details,
        }


class CypherQueries:
    """Cypherクエリライブラリ"""

    # テーブルを使用している全ファイルを取得
    GET_FILES_USING_TABLE = """
    MATCH (t:TableNode {name: $table_name})
          <-[:ACCESSES]-(q:CQLQueryNode)
          <-[:EXECUTES]-(m:MethodNode)
          <-[:DEFINES]-(c:ClassNode)
          <-[:CONTAINS]-(f:FileNode)
    RETURN DISTINCT f.path as file_path,
           c.name as class_name,
           m.name as method_name,
           COUNT(q) as query_count
    ORDER BY query_count DESC
    """

    # テーブルに関連する問題を取得
    GET_ISSUES_FOR_TABLE = """
    MATCH (t:TableNode {name: $table_name})
          <-[:ACCESSES]-(q:CQLQueryNode)
          -[:HAS_ISSUE]->(i:IssueNode)
    RETURN i.issue_type as issue_type,
           i.severity as severity,
           i.message as message,
           COUNT(i) as issue_count
    """

    # ファイルの依存関係を取得（直接参照）
    GET_FILE_DEPENDENCIES = """
    MATCH (f:FileNode {path: $file_path})
          -[:REFERENCES]->(dep:FileNode)
    RETURN dep.path as dependent_file
    """

    # ファイルの依存関係を取得（再帰的）
    GET_FILE_DEPENDENCIES_RECURSIVE = """
    MATCH path = (f:FileNode {path: $file_path})
                 -[:REFERENCES*1..5]->(dep:FileNode)
    RETURN DISTINCT dep.path as dependent_file,
           LENGTH(path) as depth
    ORDER BY depth
    """

    # クラスが使用しているテーブルを取得
    GET_TABLES_USED_BY_CLASS = """
    MATCH (c:ClassNode {name: $class_name})
          -[:DEFINES]->(m:MethodNode)
          -[:EXECUTES]->(q:CQLQueryNode)
          -[:ACCESSES]->(t:TableNode)
    RETURN DISTINCT t.name as table_name,
           COUNT(q) as query_count
    ORDER BY query_count DESC
    """

    # メソッドが使用しているテーブルを取得
    GET_TABLES_USED_BY_METHOD = """
    MATCH (m:MethodNode)
          -[:EXECUTES]->(q:CQLQueryNode)
          -[:ACCESSES]->(t:TableNode)
    WHERE m.name = $method_name AND m.class_name = $class_name
    RETURN DISTINCT t.name as table_name,
           q.cql as cql_query
    """

    # 問題が多いファイルを取得
    GET_FILES_WITH_MOST_ISSUES = """
    MATCH (f:FileNode)
          <-[:CONTAINS]-(c:ClassNode)
          <-[:DEFINES]-(m:MethodNode)
          <-[:EXECUTES]-(q:CQLQueryNode)
          -[:HAS_ISSUE]->(i:IssueNode)
    WHERE i.severity IN $severities
    RETURN f.path as file_path,
           COUNT(DISTINCT i) as issue_count,
           COLLECT(DISTINCT i.severity) as severities
    ORDER BY issue_count DESC
    LIMIT $limit
    """

    # テーブルアクセスパターンの分析
    GET_TABLE_ACCESS_PATTERN = """
    MATCH (t:TableNode {name: $table_name})
          <-[:ACCESSES]-(q:CQLQueryNode)
    RETURN q.query_type as query_type,
           COUNT(q) as count
    ORDER BY count DESC
    """


class ImpactAnalyzer:
    """
    影響範囲分析クラス

    グラフデータベースを使用して、コード変更の影響範囲を分析します。
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Args:
            neo4j_client: Neo4jクライアント
        """
        self.client = neo4j_client
        self.queries = CypherQueries()

    def analyze_table_change_impact(
        self, table_name: str, include_issues: bool = True
    ) -> ImpactResult:
        """
        テーブル変更の影響を分析

        Args:
            table_name: テーブル名
            include_issues: 問題情報を含めるか

        Returns:
            影響分析結果
        """
        logger.info(f"Analyzing impact for table: {table_name}")

        # テーブルを使用しているファイルを取得
        files_data = self.client.execute_query(
            self.queries.GET_FILES_USING_TABLE, {"table_name": table_name}
        )

        affected_files = [row["file_path"] for row in files_data]
        affected_classes = list(set([row["class_name"] for row in files_data]))
        affected_methods = list(set([row["method_name"] for row in files_data]))

        # テーブルアクセスパターンを取得
        access_patterns = self.client.execute_query(
            self.queries.GET_TABLE_ACCESS_PATTERN, {"table_name": table_name}
        )

        details = {
            "files_with_query_counts": [
                {"file": row["file_path"], "queries": row["query_count"]}
                for row in files_data
            ],
            "access_patterns": [
                {"type": row["query_type"], "count": row["count"]}
                for row in access_patterns
            ],
        }

        # 問題情報を含める
        if include_issues:
            issues_data = self.client.execute_query(
                self.queries.GET_ISSUES_FOR_TABLE, {"table_name": table_name}
            )
            details["issues"] = [
                {
                    "type": row["issue_type"],
                    "severity": row["severity"],
                    "count": row["issue_count"],
                }
                for row in issues_data
            ]

        # リスクレベルを計算
        risk_level, risk_score = self._calculate_risk(
            len(affected_files), len(affected_classes), len(affected_methods)
        )

        return ImpactResult(
            target=table_name,
            impact_type="table_change",
            affected_files=affected_files,
            affected_classes=affected_classes,
            affected_methods=affected_methods,
            risk_level=risk_level,
            risk_score=risk_score,
            details=details,
        )

    def analyze_file_change_impact(
        self, file_path: str, recursive: bool = True
    ) -> ImpactResult:
        """
        ファイル変更の影響を分析

        Args:
            file_path: ファイルパス
            recursive: 再帰的に依存関係を追跡するか

        Returns:
            影響分析結果
        """
        logger.info(f"Analyzing impact for file: {file_path}")

        # ファイルの依存関係を取得
        if recursive:
            dependencies = self.client.execute_query(
                self.queries.GET_FILE_DEPENDENCIES_RECURSIVE, {"file_path": file_path}
            )
        else:
            dependencies = self.client.execute_query(
                self.queries.GET_FILE_DEPENDENCIES, {"file_path": file_path}
            )

        affected_files = [row["dependent_file"] for row in dependencies]

        details = {
            "dependencies": [
                {
                    "file": row["dependent_file"],
                    "depth": row.get("depth", 1),
                }
                for row in dependencies
            ]
        }

        # リスクレベルを計算
        risk_level, risk_score = self._calculate_risk(len(affected_files), 0, 0)

        return ImpactResult(
            target=file_path,
            impact_type="file_change",
            affected_files=affected_files,
            affected_classes=[],
            affected_methods=[],
            risk_level=risk_level,
            risk_score=risk_score,
            details=details,
        )

    def analyze_class_dependencies(self, class_name: str) -> ImpactResult:
        """
        クラスの依存関係を分析

        Args:
            class_name: クラス名

        Returns:
            影響分析結果
        """
        logger.info(f"Analyzing dependencies for class: {class_name}")

        # クラスが使用しているテーブルを取得
        tables_data = self.client.execute_query(
            self.queries.GET_TABLES_USED_BY_CLASS, {"class_name": class_name}
        )

        details = {
            "tables_used": [
                {"table": row["table_name"], "query_count": row["query_count"]}
                for row in tables_data
            ]
        }

        # リスクレベルを計算（テーブル数に基づく）
        risk_level, risk_score = self._calculate_risk(0, len(tables_data), 0)

        return ImpactResult(
            target=class_name,
            impact_type="class_dependencies",
            affected_files=[],
            affected_classes=[],
            affected_methods=[],
            risk_level=risk_level,
            risk_score=risk_score,
            details=details,
        )

    def get_high_risk_files(
        self, severities: List[str] = None, limit: int = 10
    ) -> List[Dict]:
        """
        高リスクファイルを取得

        Args:
            severities: 対象とする重要度リスト（デフォルト: ['critical', 'high']）
            limit: 取得件数

        Returns:
            高リスクファイルのリスト
        """
        if severities is None:
            severities = ["critical", "high"]

        results = self.client.execute_query(
            self.queries.GET_FILES_WITH_MOST_ISSUES,
            {"severities": severities, "limit": limit},
        )

        return [
            {
                "file_path": row["file_path"],
                "issue_count": row["issue_count"],
                "severities": row["severities"],
            }
            for row in results
        ]

    def trace_dependency_chain(
        self, start_file: str, target_file: str, max_depth: int = 5
    ) -> Optional[List[str]]:
        """
        2つのファイル間の依存関係チェーンを追跡

        Args:
            start_file: 開始ファイル
            target_file: 目標ファイル
            max_depth: 最大深さ

        Returns:
            依存関係チェーン（パス）、見つからない場合はNone
        """
        query = f"""
        MATCH path = shortestPath(
            (start:FileNode {{path: $start_file}})
            -[:REFERENCES*1..{max_depth}]->
            (target:FileNode {{path: $target_file}})
        )
        RETURN [node IN nodes(path) | node.path] as dependency_chain
        """

        results = self.client.execute_query(
            query, {"start_file": start_file, "target_file": target_file}
        )

        if results:
            return results[0]["dependency_chain"]
        return None

    def _calculate_risk(
        self, affected_files: int, affected_classes: int, affected_methods: int
    ) -> Tuple[RiskLevel, float]:
        """
        リスクレベルとスコアを計算

        Args:
            affected_files: 影響を受けるファイル数
            affected_classes: 影響を受けるクラス数
            affected_methods: 影響を受けるメソッド数

        Returns:
            (リスクレベル, リスクスコア 0.0-1.0)
        """
        # 重み付けスコア計算
        score = (affected_files * 1.0) + (affected_classes * 0.5) + (affected_methods * 0.2)

        # 正規化（0-1の範囲に）
        normalized_score = min(score / 100.0, 1.0)

        # リスクレベル決定
        if affected_files >= 50:
            risk_level = RiskLevel.CRITICAL
        elif affected_files >= 20:
            risk_level = RiskLevel.HIGH
        elif affected_files >= 5:
            risk_level = RiskLevel.MEDIUM
        elif affected_files >= 1:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL

        logger.debug(
            f"Risk calculation: files={affected_files}, "
            f"classes={affected_classes}, methods={affected_methods} "
            f"-> {risk_level.value} ({normalized_score:.2f})"
        )

        return risk_level, normalized_score
