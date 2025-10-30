"""
Base Parser for Multi-Database Analyzer

すべてのDBパーサーの基底クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """サポートするデータベースタイプ"""
    ELASTICSEARCH = "elasticsearch"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"
    CASSANDRA = "cassandra"  # Phase 1で実装済み
    NEO4J = "neo4j"  # Phase 3で実装済み


class QueryType(Enum):
    """クエリタイプ"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"  # Elasticsearch
    AGGREGATE = "aggregate"  # MongoDB, Elasticsearch
    CACHE_GET = "cache_get"  # Redis
    CACHE_SET = "cache_set"  # Redis
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    """解析されたクエリ情報"""
    query_type: QueryType
    query_text: str
    file_path: str
    line_number: int
    method_name: Optional[str] = None
    class_name: Optional[str] = None
    parameters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """
    すべてのDBパーサーの基底クラス

    各DBパーサーはこのクラスを継承して実装する
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        パーサーの初期化

        Args:
            config: パーサー設定
        """
        self.config = config or {}
        self._queries: List[ParsedQuery] = []

    @abstractmethod
    def get_db_type(self) -> DatabaseType:
        """
        データベースタイプを返す

        Returns:
            データベースタイプ
        """
        pass

    @abstractmethod
    def parse_file(self, file_path: Path) -> List[ParsedQuery]:
        """
        ファイルを解析してクエリ情報を抽出

        Args:
            file_path: 解析するファイルのパス

        Returns:
            解析されたクエリのリスト
        """
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        このパーサーが指定されたファイルを解析できるか判定

        Args:
            file_path: ファイルパス

        Returns:
            解析可能な場合True
        """
        pass

    def parse_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[ParsedQuery]:
        """
        ディレクトリ内のファイルを解析

        Args:
            directory: 解析するディレクトリ
            recursive: 再帰的に解析するか
            file_extensions: 対象とするファイル拡張子のリスト

        Returns:
            解析されたクエリのリスト
        """
        all_queries = []

        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            # 拡張子フィルタリング
            if file_extensions and file_path.suffix not in file_extensions:
                continue

            # パース可能か確認
            if not self.can_parse(file_path):
                continue

            try:
                queries = self.parse_file(file_path)
                all_queries.extend(queries)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue

        return all_queries

    def get_statistics(self) -> Dict[str, Any]:
        """
        解析統計を取得

        Returns:
            統計情報
        """
        query_types = {}
        for query in self._queries:
            query_type = query.query_type.value
            query_types[query_type] = query_types.get(query_type, 0) + 1

        return {
            "total_queries": len(self._queries),
            "query_types": query_types,
            "db_type": self.get_db_type().value
        }

    def clear_cache(self):
        """キャッシュをクリア"""
        self._queries.clear()


class JavaParserMixin:
    """
    Javaコード解析用のミックスイン

    javalangを使用したJava AST解析の共通機能を提供
    """

    def _is_java_file(self, file_path: Path) -> bool:
        """Javaファイルか判定"""
        return file_path.suffix == '.java'

    def _read_java_file(self, file_path: Path) -> str:
        """Javaファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # UTF-8で読めない場合、別のエンコーディングを試す
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def _extract_string_literal(self, node) -> Optional[str]:
        """
        ASTノードから文字列リテラルを抽出

        Args:
            node: ASTノード

        Returns:
            文字列リテラル（見つからない場合None）
        """
        if hasattr(node, 'value'):
            return node.value
        return None

    def _get_method_name(self, node, path: Optional[List] = None) -> Optional[str]:
        """
        ASTノードからメソッド名を抽出

        Args:
            node: ASTノード
            path: ASTパス（javalangの場合）

        Returns:
            メソッド名（見つからない場合None）
        """
        # javalangの場合、pathを使用
        if path is not None:
            import javalang
            # パスを逆順で探索してMethodDeclarationを見つける
            for parent_node in reversed(path):
                if isinstance(parent_node, javalang.tree.MethodDeclaration):
                    return parent_node.name

        # フォールバック: 古いロジック（parent属性がある場合）
        current = node
        while current is not None:
            if hasattr(current, 'name') and hasattr(current, 'parameters'):
                return current.name
            current = getattr(current, 'parent', None)
        return None

    def _get_class_name(self, node, path: Optional[List] = None) -> Optional[str]:
        """
        ASTノードからクラス名を抽出

        Args:
            node: ASTノード
            path: ASTパス（javalangの場合）

        Returns:
            クラス名（見つからない場合None）
        """
        # javalangの場合、pathを使用
        if path is not None:
            import javalang
            # パスを逆順で探索してClassDeclarationを見つける
            for parent_node in reversed(path):
                if isinstance(parent_node, javalang.tree.ClassDeclaration):
                    return parent_node.name

        # フォールバック: 古いロジック（parent属性がある場合）
        current = node
        while current is not None:
            if hasattr(current, 'name') and hasattr(current, 'body'):
                return current.name
            current = getattr(current, 'parent', None)
        return None


class PythonParserMixin:
    """
    Pythonコード解析用のミックスイン

    ast モジュールを使用したPython AST解析の共通機能を提供
    """

    def _is_python_file(self, file_path: Path) -> bool:
        """Pythonファイルか判定"""
        return file_path.suffix == '.py'

    def _read_python_file(self, file_path: Path) -> str:
        """Pythonファイルを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
