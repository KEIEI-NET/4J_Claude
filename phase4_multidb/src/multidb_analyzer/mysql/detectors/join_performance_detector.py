"""
JOIN Performance Detector

JOINの非効率なパターンを検出
"""

import logging
from typing import List

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.mysql.models import MySQLQuery, SQLOperation, JoinType

logger = logging.getLogger(__name__)


class JoinPerformanceDetector(BaseDetector):
    """
    JOIN パフォーマンス検出器

    非効率なJOINパターンを検出します。

    検出パターン:
    - 過剰なJOIN数（4つ以上）
    - CROSS JOINの使用
    - SELECT *とJOINの組み合わせ
    - JOINのみでWHERE句がない

    重大度: MEDIUM/HIGH
    """

    def __init__(self):
        super().__init__()
        self.name = "JoinPerformanceDetector"

        # JOIN数の閾値
        self.join_count_threshold = 4


    def get_name(self) -> str:
        return "JoinPerformanceDetector"

    def get_severity(self) -> Severity:
        return Severity.HIGH

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(
        self,
        queries: List[MySQLQuery]
    ) -> List[Issue]:
        """
        JOIN関連の問題を検出

        Args:
            queries: 解析対象のクエリリスト
            context: 分析コンテキスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            if not query.has_joins():
                continue

            # 過剰なJOIN
            if len(query.joins) >= self.join_count_threshold:
                issue = self._create_excessive_joins_issue(query)
                issues.append(issue)

            # CROSS JOIN
            if self._has_cross_join(query):
                issue = self._create_cross_join_issue(query)
                issues.append(issue)

            # SELECT * with JOIN
            if query.uses_select_star:
                issue = self._create_select_star_join_issue(query)
                issues.append(issue)

            # JOIN without WHERE
            if not query.where_conditions:
                issue = self._create_join_without_where_issue(query)
                issues.append(issue)

        logger.info(
            f"JoinPerformanceDetector: Found {len(issues)} JOIN performance issues"
        )
        return issues

    def _create_excessive_joins_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """過剰なJOIN問題を作成"""

        join_count = len(query.joins)
        all_tables = query.get_all_tables()
        table_names = [t.name for t in all_tables]

        description = (
            f"Query joins {join_count} tables ({', '.join(table_names)}). "
            f"Excessive JOINs significantly degrade performance and make "
            f"queries difficult to maintain and optimize. "
            f"Consider denormalization or query refactoring."
        )

        suggestion = (
            f"**Optimization Strategies:**\n\n"
            f"1. **Split into Multiple Queries:**\n"
            f"   ```java\n"
            f"   // Instead of one complex query\n"
            f"   List<Parent> parents = findParents();\n"
            f"   Map<Long, Child> children = findChildrenByParentIds(parentIds);\n"
            f"   // Combine in application layer\n"
            f"   ```\n\n"
            f"2. **Use Subqueries Strategically:**\n"
            f"   ```sql\n"
            f"   SELECT * FROM main_table\n"
            f"   WHERE id IN (SELECT main_id FROM related_table WHERE ...)\n"
            f"   ```\n\n"
            f"3. **Denormalize Data:**\n"
            f"   - Add commonly joined columns to main table\n"
            f"   - Use materialized views (MySQL 8.0+)\n"
            f"   - Implement caching layer\n\n"
            f"4. **Use Covering Indexes:**\n"
            f"   ```sql\n"
            f"   CREATE INDEX idx_covering ON table_name \n"
            f"   (join_col, select_col1, select_col2);\n"
            f"   ```\n\n"
            f"5. **Consider NoSQL for Complex Relations:**\n"
            f"   - Document stores for hierarchical data\n"
            f"   - Graph databases for many-to-many relations\n\n"
            f"**Performance Impact:**\n"
            f"- Each additional JOIN multiplies execution time\n"
            f"- {join_count} JOINs may cause query timeout under load\n"
            f"- Increased lock contention and resource usage"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title=f"Excessive JOINs ({join_count} tables)",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'join_count': join_count,
                'tables': table_names,
                'join_types': [j.join_type.value for j in query.joins]
            }
        )

    def _create_cross_join_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """CROSS JOIN問題を作成"""

        cross_joins = [j for j in query.joins if j.join_type == JoinType.CROSS]

        description = (
            f"Query uses CROSS JOIN which produces Cartesian product. "
            f"This can generate enormous result sets and severely impact performance. "
            f"CROSS JOIN should be used very carefully and usually indicates a mistake."
        )

        suggestion = (
            f"**Solutions:**\n\n"
            f"1. **Add JOIN Condition:**\n"
            f"   ```sql\n"
            f"   -- ❌ Bad: CROSS JOIN (Cartesian product)\n"
            f"   SELECT * FROM table1 CROSS JOIN table2\n\n"
            f"   -- ✅ Good: Proper JOIN with condition\n"
            f"   SELECT * FROM table1\n"
            f"   INNER JOIN table2 ON table1.id = table2.table1_id\n"
            f"   ```\n\n"
            f"2. **Verify Intent:**\n"
            f"   - If Cartesian product is intended, add WHERE clause to limit results\n"
            f"   - Consider using WITH (CTE) for complex logic\n\n"
            f"3. **Calculate Impact:**\n"
            f"   ```\n"
            f"   Result rows = table1_rows × table2_rows\n"
            f"   Example: 1,000 × 1,000 = 1,000,000 rows\n"
            f"   ```\n\n"
            f"**Common Causes:**\n"
            f"- Missing ON clause (typo or mistake)\n"
            f"- Incorrect query generation\n"
            f"- Misunderstanding of CROSS JOIN semantics"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.CRITICAL,
            category=IssueCategory.PERFORMANCE,
            title="CROSS JOIN Detected - Cartesian Product",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'cross_join_count': len(cross_joins)
            }
        )

    def _create_select_star_join_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """SELECT * with JOIN問題を作成"""

        join_count = len(query.joins)
        table_count = len(query.get_all_tables())

        description = (
            f"Query uses SELECT * with {join_count} JOIN(s) across {table_count} tables. "
            f"This retrieves all columns from all tables, causing:\n"
            f"- Excessive data transfer\n"
            f"- Increased memory usage\n"
            f"- Ambiguous column names\n"
            f"- Difficult maintenance"
        )

        suggestion = (
            f"**Select Specific Columns:**\n"
            f"```sql\n"
            f"-- ❌ Bad: Retrieves all columns\n"
            f"SELECT * FROM orders o\n"
            f"INNER JOIN customers c ON o.customer_id = c.id\n\n"
            f"-- ✅ Good: Explicit column selection\n"
            f"SELECT \n"
            f"  o.id AS order_id,\n"
            f"  o.order_date,\n"
            f"  o.total_amount,\n"
            f"  c.name AS customer_name,\n"
            f"  c.email AS customer_email\n"
            f"FROM orders o\n"
            f"INNER JOIN customers c ON o.customer_id = c.id\n"
            f"```\n\n"
            f"**Benefits:**\n"
            f"- Reduced network traffic\n"
            f"- Better index usage (covering indexes)\n"
            f"- Clearer intent and easier maintenance\n"
            f"- Avoids column name conflicts\n\n"
            f"**Performance Impact:**\n"
            f"- Potential 50-80% reduction in data transfer\n"
            f"- Enables covering index optimization\n"
            f"- Faster application processing"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title=f"SELECT * with {join_count} JOIN(s)",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion
        )

    def _create_join_without_where_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """JOIN without WHERE問題を作成"""

        join_count = len(query.joins)

        description = (
            f"Query uses {join_count} JOIN(s) without WHERE clause. "
            f"This retrieves all combinations of joined records, which may be "
            f"unintentional and cause performance issues."
        )

        suggestion = (
            f"**Add WHERE Clause:**\n"
            f"```sql\n"
            f"-- ❌ Retrieves all records\n"
            f"SELECT * FROM orders o\n"
            f"INNER JOIN order_items oi ON o.id = oi.order_id\n\n"
            f"-- ✅ Filter appropriately\n"
            f"SELECT * FROM orders o\n"
            f"INNER JOIN order_items oi ON o.id = oi.order_id\n"
            f"WHERE o.status = 'completed'\n"
            f"  AND o.created_at >= '2024-01-01'\n"
            f"```\n\n"
            f"**If intentional:**\n"
            f"- Add LIMIT clause to prevent excessive results\n"
            f"- Consider pagination\n"
            f"- Add explicit comment in code explaining intent\n\n"
            f"**Performance Considerations:**\n"
            f"- Result set size = product of table sizes\n"
            f"- May cause memory issues\n"
            f"- Impacts network and application performance"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title=f"JOIN Without WHERE Clause ({join_count} joins)",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'join_count': join_count,
                'has_limit': query.has_limit
            }
        )

    def _has_cross_join(self, query: MySQLQuery) -> bool:
        """CROSS JOINがあるかチェック"""
        return any(j.join_type == JoinType.CROSS for j in query.joins)
