"""
Full Table Scan Detector

WHERE句がないクエリやインデックスを使用しないクエリを検出
"""

import logging
import re
from typing import List

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.mysql.models import MySQLQuery, SQLOperation

logger = logging.getLogger(__name__)


class FullTableScanDetector(BaseDetector):
    """
    フルテーブルスキャン検出器

    インデックスを使用しないクエリを検出します。

    検出パターン:
    - WHERE句がないSELECT/UPDATE/DELETE
    - WHERE句に関数適用（インデックス使用不可）
    - OR条件の不適切な使用
    - LIKE '%pattern'（先頭ワイルドカード）

    重大度: CRITICAL/HIGH
    """

    def __init__(self):
        super().__init__()
        self.name = "FullTableScanDetector"

        # インデックスを使用できない関数
        self.non_sargable_functions = {
            'LOWER', 'UPPER', 'SUBSTRING', 'LEFT', 'RIGHT',
            'CONCAT', 'TRIM', 'LTRIM', 'RTRIM', 'YEAR', 'MONTH', 'DAY'
        }


    def get_name(self) -> str:
        return "FullTableScanDetector"

    def get_severity(self) -> Severity:
        return Severity.HIGH

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(
        self,
        queries: List[MySQLQuery]
    ) -> List[Issue]:
        """
        フルテーブルスキャンパターンを検出

        Args:
            queries: 解析対象のクエリリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            # SELECT/UPDATE/DELETEのみチェック
            if query.operation not in (
                SQLOperation.SELECT,
                SQLOperation.UPDATE,
                SQLOperation.DELETE
            ):
                continue

            # WHERE句がない
            if not query.where_conditions:
                issue = self._create_missing_where_issue(query)
                issues.append(issue)
                continue

            # WHERE句に関数適用
            if self._has_non_sargable_condition(query):
                issue = self._create_function_in_where_issue(query)
                issues.append(issue)

            # 先頭ワイルドカードLIKE
            if self._has_leading_wildcard(query):
                issue = self._create_leading_wildcard_issue(query)
                issues.append(issue)

        logger.info(
            f"FullTableScanDetector: Found {len(issues)} full table scan issues"
        )
        return issues

    def _create_missing_where_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """WHERE句がない問題を作成"""

        main_table = query.get_main_table()
        table_name = main_table.name if main_table else "unknown"

        description = (
            f"{query.operation.value} query without WHERE clause causes full table scan. "
            f"This results in poor performance on large tables and may have "
            f"unintended consequences (e.g., deleting all records)."
        )

        # 操作に応じて重大度を決定
        severity = Severity.CRITICAL if query.operation in (
            SQLOperation.UPDATE, SQLOperation.DELETE
        ) else Severity.HIGH

        suggestion = (
            f"**Add WHERE clause** to limit affected records:\n\n"
            f"```sql\n"
            f"{query.operation.value} FROM {table_name}\n"
            f"WHERE <condition>  -- Add appropriate filter\n"
            f"```\n\n"
            f"**If you intentionally want to {query.operation.value.lower()} all records:**\n"
            f"- Use TRUNCATE for DELETE (faster, but no rollback)\n"
            f"- Add explicit WHERE 1=1 to indicate intentional full scan\n"
            f"- Consider batching for large tables"
        )

        return Issue(
            detector_name=self.name,
            severity=severity,
            category=IssueCategory.PERFORMANCE,
            title=f"Missing WHERE Clause - Full Table Scan",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'table': table_name,
                'operation': query.operation.value,
                'has_limit': query.has_limit
            }
        )

    def _create_function_in_where_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """WHERE句での関数適用問題を作成"""

        description = (
            "Query uses function in WHERE clause which prevents index usage. "
            "Functions applied to indexed columns make the index unusable, "
            "forcing full table scan."
        )

        suggestion = (
            "**Solutions:**\n\n"
            "1. **Avoid functions on indexed columns**:\n"
            "   ```sql\n"
            "   -- ❌ Bad: Function prevents index usage\n"
            "   WHERE YEAR(created_date) = 2024\n\n"
            "   -- ✅ Good: Index can be used\n"
            "   WHERE created_date >= '2024-01-01' \n"
            "     AND created_date < '2025-01-01'\n"
            "   ```\n\n"
            "2. **Use computed columns** (MySQL 5.7+):\n"
            "   ```sql\n"
            "   ALTER TABLE table_name \n"
            "   ADD COLUMN year_created INT AS (YEAR(created_date)) STORED,\n"
            "   ADD INDEX idx_year_created (year_created);\n"
            "   ```\n\n"
            "3. **Use function-based index** (MySQL 8.0+):\n"
            "   ```sql\n"
            "   CREATE INDEX idx_func ON table_name ((YEAR(created_date)));\n"
            "   ```"
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Non-Sargable Query - Function in WHERE Clause",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion
        )

    def _create_leading_wildcard_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """先頭ワイルドカードLIKE問題を作成"""

        description = (
            "LIKE pattern with leading wildcard (e.g., '%value') "
            "cannot use index and forces full table scan. "
            "This severely impacts performance on large tables."
        )

        suggestion = (
            "**Solutions:**\n\n"
            "1. **Remove leading wildcard** if possible:\n"
            "   ```sql\n"
            "   -- ❌ Bad: Full table scan\n"
            "   WHERE name LIKE '%smith'\n\n"
            "   -- ✅ Good: Can use index\n"
            "   WHERE name LIKE 'smith%'\n"
            "   ```\n\n"
            "2. **Use Full-Text Search** for text search:\n"
            "   ```sql\n"
            "   ALTER TABLE table_name ADD FULLTEXT INDEX ft_name (name);\n"
            "   WHERE MATCH(name) AGAINST('smith' IN BOOLEAN MODE);\n"
            "   ```\n\n"
            "3. **Use reverse index** for suffix search:\n"
            "   - Add reversed column: `name_reversed`\n"
            "   - Search: `WHERE name_reversed LIKE REVERSE('smith%')`\n\n"
            "4. **External search engine** for complex text search:\n"
            "   - Elasticsearch, Solr, etc."
        )

        return Issue(
            detector_name=self.name,
            severity=Severity.CRITICAL,
            category=IssueCategory.PERFORMANCE,
            title="Leading Wildcard in LIKE - Full Table Scan",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion
        )

    def _has_non_sargable_condition(self, query: MySQLQuery) -> bool:
        """WHERE句に非SARGABLE条件があるかチェック"""
        for condition in query.where_conditions:
            condition_upper = condition.upper()

            # 関数適用をチェック
            for func in self.non_sargable_functions:
                if re.search(rf'\b{func}\s*\(', condition_upper):
                    return True

        return False

    def _has_leading_wildcard(self, query: MySQLQuery) -> bool:
        """先頭ワイルドカードLIKEがあるかチェック"""
        for condition in query.where_conditions:
            # LIKE '%...' パターン
            if re.search(r"LIKE\s+['\"]%", condition, re.IGNORECASE):
                return True

        return False
