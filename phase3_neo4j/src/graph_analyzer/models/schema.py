"""
Neo4j Graph Schema Definitions

このモジュールは、コード分析グラフの全ノードタイプとリレーションシップを定義します。
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """グラフノードのタイプ"""

    FILE = "FileNode"
    CLASS = "ClassNode"
    METHOD = "MethodNode"
    QUERY = "CQLQueryNode"
    TABLE = "TableNode"
    ISSUE = "IssueNode"


class RelationType(str, Enum):
    """グラフリレーションシップのタイプ"""

    CONTAINS = "CONTAINS"  # File → Class
    DEFINES = "DEFINES"  # Class → Method
    EXECUTES = "EXECUTES"  # Method → Query
    ACCESSES = "ACCESSES"  # Query → Table
    HAS_ISSUE = "HAS_ISSUE"  # Query/Method/Class → Issue
    REFERENCES = "REFERENCES"  # File → File
    CALLS = "CALLS"  # Method → Method
    DEPENDS_ON = "DEPENDS_ON"  # Class → Class


class GraphNode(BaseModel):
    """基本グラフノード"""

    node_id: str
    node_type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)


class FileNode(GraphNode):
    """ファイルノード"""

    node_type: NodeType = NodeType.FILE
    path: str
    language: str
    size_bytes: int
    last_modified: Optional[str] = None


class ClassNode(GraphNode):
    """クラスノード"""

    node_type: NodeType = NodeType.CLASS
    name: str
    package: Optional[str] = None
    file_path: str
    start_line: int
    end_line: int


class MethodNode(GraphNode):
    """メソッドノード"""

    node_type: NodeType = NodeType.METHOD
    name: str
    signature: str
    class_name: str
    start_line: int
    end_line: int
    complexity: Optional[int] = None


class CQLQueryNode(GraphNode):
    """CQLクエリノード"""

    node_type: NodeType = NodeType.QUERY
    cql: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, BATCH
    method_name: str
    line_number: int


class TableNode(GraphNode):
    """テーブルノード"""

    node_type: NodeType = NodeType.TABLE
    name: str
    keyspace: Optional[str] = None
    database_type: str = "cassandra"


class IssueNode(GraphNode):
    """問題ノード"""

    node_type: NodeType = NodeType.ISSUE
    issue_type: str
    severity: str  # critical, high, medium, low
    message: str
    recommendation: Optional[str] = None
    confidence: float = 1.0


class GraphRelationship(BaseModel):
    """グラフリレーションシップ"""

    from_node: str
    to_node: str
    relation_type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)


# Cypher Create Queries
SCHEMA_CONSTRAINTS = """
// Unique constraints
CREATE CONSTRAINT file_path_unique IF NOT EXISTS
FOR (f:FileNode) REQUIRE f.path IS UNIQUE;

CREATE CONSTRAINT table_name_unique IF NOT EXISTS
FOR (t:TableNode) REQUIRE (t.name, t.keyspace) IS UNIQUE;

CREATE CONSTRAINT class_unique IF NOT EXISTS
FOR (c:ClassNode) REQUIRE (c.name, c.package, c.file_path) IS UNIQUE;

// Indexes
CREATE INDEX file_language_idx IF NOT EXISTS
FOR (f:FileNode) ON (f.language);

CREATE INDEX issue_severity_idx IF NOT EXISTS
FOR (i:IssueNode) ON (i.severity);

CREATE INDEX query_type_idx IF NOT EXISTS
FOR (q:CQLQueryNode) ON (q.query_type);
"""
