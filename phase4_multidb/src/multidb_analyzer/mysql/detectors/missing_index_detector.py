"""
Missing Index Detector

インデックスヒントがないクエリや最適化の機会を検出
"""

import logging
import re
from typing import List, Set

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.mysql.models import MySQLQuery, SQLOperation

logger = logging.getLogger(__name__)


class MissingIndexDetector(BaseDetector):
    """
    欠落インデックス検出器

    インデックスが必要と思われる箇所を検出します。

    検出パターン:
    - WHERE句のカラムにインデックスヒントがない
    - ORDER BYカラムにインデックスがない可能性
    - JOINカラムにインデックスが必要
    - 複合インデックスが有効な場合

    重大度: MEDIUM/HIGH
    """

    def __init__(self):
        super().__init__()
        self.name = "MissingIndexDetector"

        # インデックスが推奨されるキーワード
        self.index_recommended_patterns = {
            'foreign_key': r'\b(customer_id|user_id|order_id|product_id|account_id)\b',
            'status': r'\bstatus\b',
            'type': r'\btype\b',
            'date': r'\b(created_at|updated_at|deleted_at|date|timestamp)\b'
        }


    def get_name(self) -> str:
        return "MissingIndexDetector"

    def get_severity(self) -> Severity:
        return Severity.MEDIUM

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(
        self,
        queries: List[MySQLQuery]
    ) -> List[Issue]:
        """
        インデックス最適化の機会を検出

        Args:
            queries: 解析対象のクエリリスト
            context: 分析コンテキスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            # SELECTクエリのみチェック
            if query.operation != SQLOperation.SELECT:
                continue

            # WHERE句があるのにインデックスヒントがない
            if query.where_conditions and not query.has_index_hint:
                # WHERE句のカラムを抽出
                where_columns = self._extract_columns_from_where(query)

                if where_columns:
                    issue = self._create_missing_index_hint_issue(
                        query, where_columns
                    )
                    issues.append(issue)

            # ORDER BYがあるが対応するインデックスがない可能性
            if query.has_order_by and not query.has_index_hint:
                issue = self._create_order_by_index_issue(query)
                issues.append(issue)

            # JOINがあるがインデックスヒントがない
            if query.has_joins() and not query.has_index_hint:
                issue = self._create_join_index_issue(query)
                issues.append(issue)

        logger.info(
            f"MissingIndexDetector: Found {len(issues)} missing index issues"
        )
        return issues

    def _create_missing_index_hint_issue(
        self,
        query: MySQLQuery,
        where_columns: Set[str]
    ) -> Issue:
        """インデックスヒント欠落問題を作成"""

        main_table = query.get_main_table()
        table_name = main_table.name if main_table else "unknown"

        columns_str = ", ".join(sorted(where_columns))

        description = (
            f"Query filters on columns ({columns_str}) without index hint. "
            f"Consider adding appropriate indexes to improve query performance. "
            f"This is especially important for high-frequency queries."
        )

        # 推奨されるインデックス名を生成
        recommended_index_name = self._generate_index_name(
            table_name, where_columns
        )

        suggestion = (
            f"**1. Create Index:**\n"
            f"```sql\n"
            f"CREATE INDEX {recommended_index_name}\n"
            f"ON {table_name} ({columns_str});\n"
            f"```\n\n"
            f"**2. Use Index Hint (optional):**\n"
            f"```sql\n"
            f"SELECT * FROM {table_name}\n"
            f"USE INDEX ({recommended_index_name})\n"
            f"WHERE {' AND '.join(f'{col} = ?' for col in where_columns)}\n"
            f"```\n\n"
            f"**3. Verify with EXPLAIN:**\n"
            f"```sql\n"
            f"EXPLAIN {query.query_text}\n"
            f"```\n"
            f"- Check 'type': should be 'ref' or 'range' (not 'ALL')\n"
            f"- Check 'key': should show your index name\n"
            f"- Check 'rows': should be small relative to table size\n\n"
            f"**4. Composite Index Considerations:**\n"
            f"- Order matters: most selective column first\n"
            f"- Equality conditions before range conditions\n"
            f"- Cover ORDER BY columns when possible"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title=f"Potential Missing Index on WHERE Columns",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'table': table_name,
                'columns': list(where_columns),
                'recommended_index': recommended_index_name
            }
        )

    def _create_order_by_index_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """ORDER BYインデックス問題を作成"""

        main_table = query.get_main_table()
        table_name = main_table.name if main_table else "unknown"

        order_columns = [
            col.split()[0]  # "column DESC" -> "column"
            for col in query.order_by_columns
        ]

        description = (
            "Query uses ORDER BY without index hint. "
            "ORDER BY operations can be expensive without proper indexes, "
            "requiring filesort which impacts performance."
        )

        columns_str = ", ".join(order_columns)
        index_name = f"idx_{table_name}_{'_'.join(order_columns[:3])}"

        suggestion = (
            f"**Create Index for ORDER BY:**\n"
            f"```sql\n"
            f"CREATE INDEX {index_name}\n"
            f"ON {table_name} ({columns_str});\n"
            f"```\n\n"
            f"**Optimization Tips:**\n"
            f"- Include WHERE columns first, then ORDER BY columns\n"
            f"- Match ORDER BY direction (ASC/DESC) in index definition\n"
            f"- Consider covering index (include SELECT columns)\n\n"
            f"**Verify Performance:**\n"
            f"```sql\n"
            f"EXPLAIN {query.query_text}\n"
            f"```\n"
            f"- Look for 'Using filesort' in Extra column (bad)\n"
            f"- Ideal: 'Using index' without 'Using filesort'"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title="ORDER BY Without Proper Index",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'table': table_name,
                'order_by_columns': order_columns
            }
        )

    def _create_join_index_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """JOINインデックス問題を作成"""

        description = (
            f"Query uses {len(query.joins)} JOIN(s) without index hints. "
            f"JOIN operations require indexes on join columns for optimal performance. "
            f"Without proper indexes, MySQL may perform full table scans on joined tables."
        )

        # JOINカラムを抽出
        join_suggestions = []
        for i, join in enumerate(query.joins, 1):
            join_table = join.table.name

            # JOIN条件からカラムを抽出（簡易的）
            condition = join.condition
            columns = re.findall(r'(\w+)\.(\w+)', condition)

            if columns:
                join_suggestions.append(
                    f"{i}. **{join_table}** table:\n"
                    f"   ```sql\n"
                    f"   CREATE INDEX idx_{join_table}_join ON {join_table} "
                    f"({columns[0][1] if columns else 'join_column'});\n"
                    f"   ```"
                )

        suggestions_str = "\n\n".join(join_suggestions)

        suggestion = (
            f"**Create Indexes on JOIN Columns:**\n\n"
            f"{suggestions_str}\n\n"
            f"**Best Practices:**\n"
            f"- Always index foreign key columns\n"
            f"- Consider composite indexes for multiple JOIN conditions\n"
            f"- Index both sides of the JOIN\n\n"
            f"**Verify with EXPLAIN:**\n"
            f"```sql\n"
            f"EXPLAIN {query.query_text}\n"
            f"```\n"
            f"Check each joined table:\n"
            f"- 'type' should be 'ref' or 'eq_ref' (not 'ALL')\n"
            f"- 'key' should show index usage\n"
            f"- 'rows' should be small"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title=f"JOIN Without Index Hints ({len(query.joins)} joins)",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'join_count': len(query.joins),
                'join_types': [j.join_type.value for j in query.joins]
            }
        )

    def _extract_columns_from_where(self, query: MySQLQuery) -> Set[str]:
        """WHERE句からカラム名を抽出"""
        columns = set()

        for condition in query.where_conditions:
            # カラム名を抽出（簡易的）
            # "column = value" or "table.column = value"
            matches = re.findall(r'\b(\w+)\.(\w+)\s*[=<>]', condition)
            if matches:
                columns.update(col for _, col in matches)
            else:
                matches = re.findall(r'\b(\w+)\s*[=<>]', condition)
                columns.update(matches)

        return columns

    def _generate_index_name(
        self,
        table_name: str,
        columns: Set[str]
    ) -> str:
        """インデックス名を生成"""
        column_list = sorted(columns)[:3]  # 最大3カラム
        columns_part = '_'.join(column_list)
        return f"idx_{table_name}_{columns_part}"
