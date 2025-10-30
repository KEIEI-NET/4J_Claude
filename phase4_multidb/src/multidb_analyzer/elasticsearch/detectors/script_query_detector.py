"""
Script Query Detector for Elasticsearch

Script Queryの不適切な使用を検出
Script Queryは非常に強力だが、CPU使用率が高くパフォーマンスに
深刻な影響を与える可能性がある
"""

from typing import List
import re

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.core.base_parser import ParsedQuery
from multidb_analyzer.elasticsearch.models.es_models import ScriptQuery


class ScriptQueryDetector(BaseDetector):
    """
    Script Query検出器

    検出パターン:
    1. Script Queryの使用 (CRITICAL)
    2. 複雑なスクリプト (CRITICAL)
    3. Inlineスクリプト (HIGH)

    例:
    ```java
    // ❌ CRITICAL - パフォーマンスへの深刻な影響
    QueryBuilders.scriptQuery(
        new Script("doc['price'].value * doc['quantity'].value > 1000")
    );

    // ❌ CRITICAL - 複雑なスクリプト
    QueryBuilders.scriptQuery(
        new Script(
            "for (item in doc['items']) { " +
            "  if (item.price > 100) return true; " +
            "} return false;"
        )
    );

    // ⚠️ HIGH - Inlineスクリプトは保存済みスクリプトより遅い
    ScriptQueryBuilder scriptQuery = QueryBuilders.scriptQuery(
        new Script(ScriptType.INLINE, "painless", "doc['field'].value > params.threshold", params)
    );

    // ✅ Better - 可能な限り通常のクエリを使用
    QueryBuilders.rangeQuery("price").gte(1000);
    ```
    """

    # 複雑なスクリプトを示すキーワード
    COMPLEX_SCRIPT_KEYWORDS = [
        'for', 'while', 'if', 'else', 'def',
        'function', 'return', 'loop'
    ]

    # パフォーマンスに影響する操作
    EXPENSIVE_OPERATIONS = [
        'doc[', '.value', 'params.', 'ctx.',
        '*', '/', 'Math.', 'String.'
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self._script_complexity_threshold = self.get_threshold('script_length', 100)

    def get_name(self) -> str:
        return "ScriptQueryDetector"

    def get_severity(self) -> Severity:
        return Severity.CRITICAL

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(self, queries: List[ParsedQuery]) -> List[Issue]:
        """
        Script Queryを検出

        Args:
            queries: 解析されたクエリのリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            if self._is_script_query(query):
                script_info = self._extract_script_info(query)
                if script_info:
                    issue = self._create_script_issue(query, script_info)
                    if issue:
                        issues.append(issue)

        self._issues.extend(issues)
        return issues

    def _is_script_query(self, query: ParsedQuery) -> bool:
        """
        Script Queryか判定

        Args:
            query: 解析されたクエリ

        Returns:
            Script Queryの場合True
        """
        # メタデータからチェック
        if query.metadata and query.metadata.get('is_script'):
            return True

        # クエリテキストからチェック
        if 'scriptQuery' in query.query_text or 'Script(' in query.query_text:
            return True

        return False

    def _extract_script_info(self, query: ParsedQuery) -> ScriptQuery | None:
        """
        スクリプト情報を抽出

        Args:
            query: 解析されたクエリ

        Returns:
            ScriptQuery（見つからない場合None）
        """
        script_source = None
        script_lang = "painless"
        is_inline = True

        # パラメータから抽出
        if query.parameters:
            # Script(...) の引数を探す
            for key, value in query.parameters.items():
                if isinstance(value, str):
                    # スクリプトソースの候補
                    if any(op in value for op in self.EXPENSIVE_OPERATIONS):
                        script_source = value
                        break

        # クエリテキストから抽出（フォールバック）
        if not script_source:
            # new Script("...") パターン
            match = re.search(r'new\s+Script\s*\(\s*["\']([^"\']+)["\']', query.query_text)
            if match:
                script_source = match.group(1)

            # ScriptType.INLINE パターン
            if 'ScriptType.INLINE' in query.query_text:
                is_inline = True
            elif 'ScriptType.STORED' in query.query_text:
                is_inline = False

        if script_source:
            return ScriptQuery(
                script_lang=script_lang,
                script_source=script_source,
                is_inline=is_inline
            )

        # スクリプトソースが見つからなくても、scriptQueryの使用自体は検出
        return ScriptQuery(
            script_lang=script_lang,
            script_source=None,
            is_inline=is_inline
        )

    def _create_script_issue(
        self,
        query: ParsedQuery,
        script_info: ScriptQuery
    ) -> Issue | None:
        """
        Script Query問題のIssueを作成

        Args:
            query: 解析されたクエリ
            script_info: スクリプト情報

        Returns:
            Issue
        """
        # 重要度の判定
        severity = self._determine_severity(script_info)

        # タイトルと説明の生成
        title = self._generate_title(script_info)
        description = self._generate_description(script_info)
        suggestion = self._generate_suggestion(script_info)

        # タグの生成
        tags = ['elasticsearch', 'script-query', 'performance']
        if script_info.is_complex():
            tags.append('complex-script')
        if script_info.is_inline:
            tags.append('inline-script')

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=severity,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,  # Script Queryの自動修正は困難
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-script-query.html",
            tags=tags,
            metadata={
                'script_source': script_info.script_source,
                'is_complex': script_info.is_complex(),
                'is_inline': script_info.is_inline,
                'script_length': len(script_info.script_source) if script_info.script_source else 0
            }
        )

    def _determine_severity(self, script_info: ScriptQuery) -> Severity:
        """重要度を判定"""
        # 複雑なスクリプトは最も深刻
        if script_info.is_complex():
            return Severity.CRITICAL

        # Inlineスクリプトは高
        if script_info.is_inline:
            return Severity.HIGH

        # その他のScript Query
        return Severity.HIGH

    def _generate_title(self, script_info: ScriptQuery) -> str:
        """タイトルを生成"""
        if script_info.is_complex():
            return "Complex script query detected - severe performance impact"

        if script_info.is_inline:
            return "Inline script query detected - performance concern"

        return "Script query usage detected"

    def _generate_description(self, script_info: ScriptQuery) -> str:
        """説明を生成"""
        desc_parts = []

        if script_info.is_complex():
            desc_parts.append(
                "A complex script query has been detected. "
                "Script queries execute custom code at query time, "
                "which can severely impact cluster performance. "
                "Complex scripts with loops, conditionals, or multiple operations "
                "are especially expensive."
            )
        else:
            desc_parts.append(
                "A script query has been detected. "
                "While script queries are powerful, they execute custom code "
                "at query time and can significantly impact performance."
            )

        if script_info.is_inline:
            desc_parts.append(
                " This is an inline script, which is compiled at runtime. "
                "Stored scripts are cached and perform better."
            )

        if script_info.script_source:
            desc_parts.append(f" Script: {script_info.script_source[:100]}...")

        return "".join(desc_parts)

    def _generate_suggestion(self, script_info: ScriptQuery) -> str:
        """修正提案を生成"""
        suggestions = []

        suggestions.append(
            "Consider whether this script query can be replaced with a standard query. "
            "For example, range queries, term queries, or bool queries are much faster."
        )

        if script_info.is_complex():
            suggestions.append(
                "If the script is complex, consider pre-computing the result at index time "
                "and storing it as a field. This moves the computational cost from query time to index time."
            )

        if script_info.is_inline:
            suggestions.append(
                "If script queries are necessary, use stored scripts instead of inline scripts. "
                "Stored scripts are compiled once and cached for better performance."
            )

        suggestions.append(
            "Profile your queries to understand the performance impact. "
            "Use the Profile API to measure query execution time."
        )

        suggestions.append(
            "Consider using function_score query with field_value_factor "
            "for simple calculations instead of scripts."
        )

        return " ".join(suggestions)
