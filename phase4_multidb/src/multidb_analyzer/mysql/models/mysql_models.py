"""
MySQL Query Models

MySQLクエリとSQL操作のデータモデル
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class SQLOperation(Enum):
    """SQL操作タイプ"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"


class JoinType(Enum):
    """JOINタイプ"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL JOIN"
    CROSS = "CROSS JOIN"


@dataclass
class TableReference:
    """
    テーブル参照情報

    Attributes:
        name: テーブル名
        alias: エイリアス（オプション）
        schema: スキーマ名（オプション）
    """
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None

    def __str__(self) -> str:
        """文字列表現"""
        full_name = f"{self.schema}.{self.name}" if self.schema else self.name
        return f"{full_name} AS {self.alias}" if self.alias else full_name


@dataclass
class JoinInfo:
    """
    JOIN情報

    Attributes:
        join_type: JOINタイプ
        table: 結合先テーブル
        condition: 結合条件
        line_number: 行番号
    """
    join_type: JoinType
    table: TableReference
    condition: str
    line_number: int


@dataclass
class IndexHint:
    """
    インデックスヒント

    Attributes:
        hint_type: ヒントタイプ（USE, FORCE, IGNORE）
        index_names: インデックス名のリスト
    """
    hint_type: str  # USE, FORCE, IGNORE
    index_names: List[str]


@dataclass
class MySQLQuery:
    """
    MySQLクエリ情報

    Attributes:
        operation: SQL操作タイプ
        tables: 参照テーブル
        query_text: クエリテキスト
        file_path: ファイルパス
        line_number: 行番号
        method_name: メソッド名（オプション）
        class_name: クラス名（オプション）
        joins: JOIN情報のリスト
        where_conditions: WHERE条件のリスト
        has_index_hint: インデックスヒントの有無
        index_hints: インデックスヒント情報
        has_limit: LIMIT句の有無
        limit_value: LIMIT値
        has_order_by: ORDER BY句の有無
        order_by_columns: ORDER BY対象カラム
        is_in_loop: ループ内での実行かどうか
        loop_type: ループタイプ（for, while, etc）
        uses_select_star: SELECT *の使用有無
        column_count: 選択カラム数
        has_subquery: サブクエリの有無
        metadata: 追加メタデータ
    """
    operation: SQLOperation
    tables: List[TableReference]
    query_text: str
    file_path: str
    line_number: int

    # オプショナルフィールド
    method_name: Optional[str] = None
    class_name: Optional[str] = None

    # JOIN情報
    joins: List[JoinInfo] = field(default_factory=list)

    # WHERE条件
    where_conditions: List[str] = field(default_factory=list)

    # インデックスヒント
    has_index_hint: bool = False
    index_hints: List[IndexHint] = field(default_factory=list)

    # LIMIT/ORDER BY
    has_limit: bool = False
    limit_value: Optional[int] = None
    has_order_by: bool = False
    order_by_columns: List[str] = field(default_factory=list)

    # ループ検出
    is_in_loop: bool = False
    loop_type: Optional[str] = None  # for, while, do-while

    # SELECT分析
    uses_select_star: bool = False
    column_count: Optional[int] = None

    # サブクエリ
    has_subquery: bool = False

    # その他メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """クエリの文字列表現"""
        tables_str = ", ".join(str(t) for t in self.tables)
        location = f"{self.file_path}:{self.line_number}"
        return f"{self.operation.value} on {tables_str} ({location})"

    def get_main_table(self) -> Optional[TableReference]:
        """メインテーブルを取得"""
        return self.tables[0] if self.tables else None

    def has_joins(self) -> bool:
        """JOIN句の有無を確認"""
        return len(self.joins) > 0

    def get_all_tables(self) -> List[TableReference]:
        """全テーブル（JOIN含む）を取得"""
        all_tables = self.tables.copy()
        for join in self.joins:
            all_tables.append(join.table)
        return all_tables

    def is_simple_query(self) -> bool:
        """シンプルなクエリかどうか判定"""
        return (
            not self.has_joins()
            and not self.has_subquery
            and len(self.tables) == 1
            and not self.uses_select_star
            and not self.is_in_loop
        )

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'operation': self.operation.value,
            'tables': [str(t) for t in self.tables],
            'query_text': self.query_text,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'method_name': self.method_name,
            'class_name': self.class_name,
            'has_joins': self.has_joins(),
            'join_count': len(self.joins),
            'has_index_hint': self.has_index_hint,
            'has_limit': self.has_limit,
            'limit_value': self.limit_value,
            'is_in_loop': self.is_in_loop,
            'uses_select_star': self.uses_select_star,
            'has_subquery': self.has_subquery
        }
