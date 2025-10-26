"""
CQL文字列を解析して問題パターンを検出
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class QueryType(Enum):
    """CQLクエリのタイプ"""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BATCH = "BATCH"
    UNKNOWN = "UNKNOWN"


@dataclass
class WhereClause:
    """
    WHERE句の情報

    Attributes:
        columns: WHERE句で使用されているカラム名のリスト
        has_equality: 等価条件（=）を含むか
        has_in: IN句を含むか
        has_range: 範囲条件（>、<、>=、<=）を含むか
        raw_clause: 元のWHERE句文字列
    """

    columns: List[str] = field(default_factory=list)
    has_equality: bool = False
    has_in: bool = False
    has_range: bool = False
    raw_clause: str = ""


@dataclass
class CQLAnalysis:
    """
    CQL分析結果

    Attributes:
        query_type: クエリタイプ
        has_allow_filtering: ALLOW FILTERINGを含むか
        uses_partition_key: パーティションキーを使用しているか（推定）
        is_batch: BATCHクエリか
        batch_size: BATCH内のステートメント数
        tables: 対象テーブル名のリスト
        where_clause: WHERE句の情報
        issues: 検出された問題のリスト
        has_select_star: SELECT *を使用しているか
    """

    query_type: QueryType
    has_allow_filtering: bool
    uses_partition_key: bool
    is_batch: bool
    batch_size: int
    tables: List[str]
    where_clause: Optional[WhereClause]
    issues: List[Dict[str, Any]] = field(default_factory=list)
    has_select_star: bool = False


class CQLParser:
    """
    CQL文を解析して問題を検出

    正規表現ベースの解析を使用（完全なCQL文法パーサーではない）
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: 設定辞書（オプション）
        """
        self.config = config or {}
        self.batch_threshold = self.config.get("batch_threshold", 100)

    def analyze(self, cql: str) -> CQLAnalysis:
        """
        CQL文を分析

        Args:
            cql: 分析対象のCQL文

        Returns:
            CQLAnalysisオブジェクト
        """
        # CQLの正規化
        normalized_cql = self._normalize_cql(cql)
        cql_upper = normalized_cql.upper()

        # クエリタイプの判定
        query_type = self._determine_query_type(cql_upper)

        # テーブル名の抽出
        tables = self._extract_tables(normalized_cql)

        # WHERE句の解析
        where_clause = self._parse_where_clause(normalized_cql)

        # BATCH処理の解析
        is_batch = "BEGIN BATCH" in cql_upper
        batch_size = self._count_batch_statements(normalized_cql) if is_batch else 0

        # パーティションキー使用の推定
        uses_partition_key = self._estimate_partition_key_usage(where_clause)

        # SELECT *の検出
        has_select_star = "SELECT *" in cql_upper or "SELECT  *" in cql_upper

        # 基本的な分析結果の構築
        analysis = CQLAnalysis(
            query_type=query_type,
            has_allow_filtering="ALLOW FILTERING" in cql_upper,
            uses_partition_key=uses_partition_key,
            is_batch=is_batch,
            batch_size=batch_size,
            tables=tables,
            where_clause=where_clause,
            has_select_star=has_select_star,
        )

        # 問題パターンの検出
        analysis.issues = self._detect_issues(analysis, normalized_cql)

        return analysis

    def _normalize_cql(self, cql: str) -> str:
        """
        CQLを正規化（余分な空白を削除）

        Args:
            cql: 元のCQL文

        Returns:
            正規化されたCQL文
        """
        # 改行をスペースに変換
        cql = cql.replace("\n", " ").replace("\r", " ")

        # 複数の空白を1つに
        cql = re.sub(r"\s+", " ", cql)

        # 前後の空白を削除
        return cql.strip()

    def _determine_query_type(self, cql_upper: str) -> QueryType:
        """
        クエリタイプを判定

        Args:
            cql_upper: 大文字に変換されたCQL文

        Returns:
            QueryType
        """
        if cql_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif cql_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif cql_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif cql_upper.startswith("DELETE"):
            return QueryType.DELETE
        elif "BEGIN BATCH" in cql_upper:
            return QueryType.BATCH
        return QueryType.UNKNOWN

    def _extract_tables(self, cql: str) -> List[str]:
        """
        CQL文からテーブル名を抽出

        Args:
            cql: CQL文

        Returns:
            テーブル名のリスト
        """
        tables = []

        # FROM句からテーブル抽出
        from_matches = re.findall(r"FROM\s+(\w+)", cql, re.IGNORECASE)
        tables.extend(from_matches)

        # INTO句からテーブル抽出
        into_matches = re.findall(r"INTO\s+(\w+)", cql, re.IGNORECASE)
        tables.extend(into_matches)

        # UPDATE句からテーブル抽出
        update_matches = re.findall(r"UPDATE\s+(\w+)", cql, re.IGNORECASE)
        tables.extend(update_matches)

        # 重複を除去
        return list(set(tables))

    def _parse_where_clause(self, cql: str) -> Optional[WhereClause]:
        """
        WHERE句を解析

        Args:
            cql: CQL文

        Returns:
            WhereClause または None
        """
        # WHERE句を抽出（キーワードまたは文字列末尾まで）
        where_match = re.search(
            r"WHERE\s+(.*?)(?:\s+(?:ALLOW|ORDER|LIMIT|GROUP)\s|$)", cql, re.IGNORECASE | re.DOTALL
        )

        if not where_match:
            return None

        raw_clause = where_match.group(1).strip()

        # カラム名を抽出（簡易版：= の左側、IN の左側など）
        columns = []

        # 等価条件のカラム
        eq_columns = re.findall(r"(\w+)\s*=", raw_clause, re.IGNORECASE)
        columns.extend(eq_columns)

        # IN句のカラム
        in_columns = re.findall(r"(\w+)\s+IN\s*\(", raw_clause, re.IGNORECASE)
        columns.extend(in_columns)

        # 範囲条件のカラム
        range_columns = re.findall(r"(\w+)\s*[<>]=?", raw_clause, re.IGNORECASE)
        columns.extend(range_columns)

        # 重複を除去
        columns = list(set(columns))

        return WhereClause(
            columns=columns,
            has_equality="=" in raw_clause and "IN" not in raw_clause.upper(),
            has_in=" IN " in raw_clause.upper() or " IN(" in raw_clause.upper(),
            has_range=any(op in raw_clause for op in [">", "<", ">=", "<="]),
            raw_clause=raw_clause,
        )

    def _estimate_partition_key_usage(self, where_clause: Optional[WhereClause]) -> bool:
        """
        WHERE句からパーティションキー使用を推定

        Phase 1では実際のスキーマ情報がないため、
        等価条件の存在で推定する

        Args:
            where_clause: WHERE句の情報

        Returns:
            パーティションキーを使用している可能性が高い場合True
        """
        if not where_clause:
            return False

        # 等価条件があればパーティションキー使用の可能性が高い
        # （ただし、これは推定であり、実際のスキーマとの照合が必要）
        return where_clause.has_equality

    def _count_batch_statements(self, cql: str) -> int:
        """
        BATCH内のステートメント数をカウント

        Args:
            cql: CQL文（BATCH）

        Returns:
            ステートメント数
        """
        # セミコロンで分割
        statements = cql.split(";")

        # BEGIN BATCHとAPPLY BATCHを除外
        count = sum(
            1
            for stmt in statements
            if stmt.strip()
            and "BEGIN BATCH" not in stmt.upper()
            and "APPLY BATCH" not in stmt.upper()
        )

        return count

    def _detect_issues(self, analysis: CQLAnalysis, cql: str) -> List[Dict[str, Any]]:
        """
        問題パターンを検出

        Args:
            analysis: CQL分析結果
            cql: 元のCQL文

        Returns:
            検出された問題のリスト
        """
        issues = []

        # ALLOW FILTERING
        if analysis.has_allow_filtering:
            issues.append(
                {
                    "type": "ALLOW_FILTERING",
                    "severity": "high",
                    "message": "ALLOW FILTERING detected - full table scan risk",
                    "recommendation": "Create Materialized View or redesign data model to avoid ALLOW FILTERING",
                }
            )

        # Partition Key未使用（SELECTクエリのみ）
        if analysis.query_type == QueryType.SELECT and not analysis.uses_partition_key:
            issues.append(
                {
                    "type": "NO_PARTITION_KEY",
                    "severity": "critical",
                    "message": "Partition Key not used - multi-node scan",
                    "recommendation": "Add partition key to WHERE clause to avoid full cluster scan",
                }
            )

        # 大量バッチ
        if analysis.is_batch and analysis.batch_size > self.batch_threshold:
            issues.append(
                {
                    "type": "LARGE_BATCH",
                    "severity": "medium",
                    "message": f"Large batch processing: {analysis.batch_size} statements (threshold: {self.batch_threshold})",
                    "recommendation": f"Split batch into chunks of {self.batch_threshold} or less",
                }
            )

        # SELECT *の使用
        if analysis.has_select_star and analysis.query_type == QueryType.SELECT:
            issues.append(
                {
                    "type": "SELECT_STAR",
                    "severity": "low",
                    "message": "SELECT * detected - may retrieve unnecessary data",
                    "recommendation": "Specify only the columns you need instead of using SELECT *",
                }
            )

        # IN句の使用（警告レベル）
        if analysis.where_clause and analysis.where_clause.has_in:
            issues.append(
                {
                    "type": "IN_CLAUSE",
                    "severity": "low",
                    "message": "IN clause detected - may cause performance issues with large lists",
                    "recommendation": "Consider limiting IN clause to small sets (< 10 items) or redesigning the query",
                }
            )

        return issues
