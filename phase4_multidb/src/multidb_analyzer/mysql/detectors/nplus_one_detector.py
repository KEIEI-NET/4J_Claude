"""
N+1 Query Detector

ループ内でのクエリ実行（N+1問題）を検出
"""

import logging
from typing import List

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.mysql.models import MySQLQuery, SQLOperation

logger = logging.getLogger(__name__)


class NPlusOneDetector(BaseDetector):
    """
    N+1クエリ検出器

    ループ内でのクエリ実行を検出します。
    これは典型的なパフォーマンスアンチパターンです。

    検出パターン:
    - for/while/do-whileループ内でのSELECT実行
    - 反復処理内での個別レコード取得

    重大度: HIGH
    """

    def __init__(self):
        super().__init__()
        self.name = "NPlusOneDetector"


    def get_name(self) -> str:
        return "NPlusOneDetector"

    def get_severity(self) -> Severity:
        return Severity.HIGH

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(
        self,
        queries: List[MySQLQuery]
    ) -> List[Issue]:
        """
        N+1クエリパターンを検出

        Args:
            queries: 解析対象のクエリリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            # ループ内かつSELECTクエリをチェック
            if query.is_in_loop and query.operation == SQLOperation.SELECT:
                issues.append(self._create_nplus_one_issue(query))

        logger.info(f"NPlusOneDetector: Found {len(issues)} N+1 query issues")
        return issues

    def _create_nplus_one_issue(
        self,
        query: MySQLQuery
    ) -> Issue:
        """N+1クエリの問題を作成"""

        # ループタイプを表示
        loop_info = f" ({query.loop_type} loop)" if query.loop_type else ""

        # テーブル情報
        main_table = query.get_main_table()
        table_name = main_table.name if main_table else "unknown"

        description = (
            f"Query executed inside a {query.loop_type or 'loop'}, "
            f"which may cause N+1 query problem. "
            f"This pattern executes 1 query to fetch parent records, "
            f"then N queries (one per parent record) to fetch related data, "
            f"resulting in poor performance."
        )

        suggestion = self._generate_suggestion(query, table_name)

        return Issue(
            detector_name=self.name,
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title=f"N+1 Query Pattern Detected{loop_info}",
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            query_text=query.query_text,
            suggestion=suggestion,
            metadata={
                'loop_type': query.loop_type,
                'table': table_name,
                'operation': query.operation.value,
                'method_name': query.method_name,
                'class_name': query.class_name
            }
        )

    def _generate_suggestion(self, query: MySQLQuery, table_name: str) -> str:
        """最適化提案を生成"""

        suggestions = [
            "**Recommended Solutions:**",
            "",
            "1. **Batch Query**: Collect IDs from the loop and use IN clause:",
            f"   ```sql",
            f"   SELECT * FROM {table_name} WHERE id IN (?, ?, ...)",
            f"   ```",
            "",
            "2. **JOIN Query**: Use JOIN to fetch related data in single query:",
            "   ```sql",
            "   SELECT parent.*, child.* FROM parent_table parent",
            f"   LEFT JOIN {table_name} child ON parent.id = child.parent_id",
            "   ```",
            "",
            "3. **ORM Eager Loading**: If using JPA/Hibernate:",
            "   ```java",
            "   @EntityGraph(attributePaths = {\"relatedEntity\"})",
            "   List<ParentEntity> findAll();",
            "   ```",
            "",
            "4. **Caching**: Consider caching frequently accessed data",
            "",
            "**Performance Impact**: Can reduce query count from O(N) to O(1)",
            "and significantly improve response time for large datasets."
        ]

        return "\n".join(suggestions)
