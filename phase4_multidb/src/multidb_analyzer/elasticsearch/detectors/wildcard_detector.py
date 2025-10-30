"""
Wildcard Detector for Elasticsearch

ワイルドカードクエリの不適切な使用を検出
特に先頭にワイルドカード(*で始まる)を使用するケースは
インデックスを使用できずパフォーマンスに深刻な影響を与える
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
from multidb_analyzer.elasticsearch.models.es_models import WildcardPattern


class WildcardDetector(BaseDetector):
    """
    ワイルドカードクエリ検出器

    検出パターン:
    1. 先頭ワイルドカード: *smith (CRITICAL)
    2. 両端ワイルドカード: *smith* (HIGH)
    3. 末尾ワイルドカード: smith* (INFO - 通常は問題なし)

    例:
    ```java
    // ❌ 非常に悪い - インデックスが使えない
    QueryBuilders.wildcardQuery("name", "*smith");
    QueryBuilders.wildcardQuery("email", "*@example.com");

    // ❌ 悪い - パフォーマンスへの影響大
    QueryBuilders.wildcardQuery("description", "*keyword*");

    // ✅ OK - インデックスを使用可能
    QueryBuilders.wildcardQuery("name", "smith*");
    ```
    """

    def __init__(self, config=None):
        super().__init__(config)
        self._wildcard_pattern = re.compile(r'[\*\?]')

    def get_name(self) -> str:
        return "WildcardDetector"

    def get_severity(self) -> Severity:
        return Severity.HIGH

    def get_category(self) -> IssueCategory:
        return IssueCategory.PERFORMANCE

    def detect(self, queries: List[ParsedQuery]) -> List[Issue]:
        """
        ワイルドカードクエリを検出

        Args:
            queries: 解析されたクエリのリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            # wildcardQueryメソッドのチェック
            if self._is_wildcard_query(query):
                wildcard_pattern = self._extract_wildcard_pattern(query)
                if wildcard_pattern:
                    issue = self._create_wildcard_issue(query, wildcard_pattern)
                    if issue:
                        issues.append(issue)

        self._issues.extend(issues)
        return issues

    def _is_wildcard_query(self, query: ParsedQuery) -> bool:
        """
        ワイルドカードクエリか判定

        Args:
            query: 解析されたクエリ

        Returns:
            ワイルドカードクエリの場合True
        """
        # メタデータからチェック
        if query.metadata and query.metadata.get('is_wildcard'):
            return True

        # クエリテキストからチェック
        if 'wildcardQuery' in query.query_text:
            return True

        return False

    def _strip_quotes(self, text: str) -> str:
        """
        文字列から引用符を除去

        Args:
            text: 入力文字列

        Returns:
            引用符を除去した文字列
        """
        if isinstance(text, str):
            text = text.strip()
            if (text.startswith('"') and text.endswith('"')) or \
               (text.startswith("'") and text.endswith("'")):
                return text[1:-1]
        return text

    def _extract_wildcard_pattern(self, query: ParsedQuery) -> WildcardPattern | None:
        """
        ワイルドカードパターンを抽出

        Args:
            query: 解析されたクエリ

        Returns:
            WildcardPattern（見つからない場合None）
        """
        # パラメータから抽出
        if query.parameters:
            field_name = self._strip_quotes(str(query.parameters.get('arg0', '')))
            pattern = self._strip_quotes(str(query.parameters.get('arg1', '')))

            if isinstance(pattern, str):
                # BinaryOperationの場合の特別処理
                # e.g., 'BinaryOperation(...value="*", ...operator=+)' のようなパターンを検出
                is_binary_leading_wildcard = (
                    'BinaryOperation' in pattern and
                    'value="*"' in pattern and
                    'operator=+' in pattern
                )

                # 通常のワイルドカードパターンまたはBinaryOperationでの動的ワイルドカード
                if self._wildcard_pattern.search(pattern) or is_binary_leading_wildcard:
                    return WildcardPattern(
                        pattern=pattern,
                        field_name=field_name,
                        starts_with_wildcard=(
                            pattern.startswith('*') or
                            pattern.startswith('?') or
                            is_binary_leading_wildcard
                        ),
                        ends_with_wildcard=pattern.endswith('*') or pattern.endswith('?'),
                        contains_wildcard='*' in pattern or '?' in pattern
                    )

        # クエリテキストから抽出（フォールバック）
        match = re.search(r'wildcardQuery\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\)', query.query_text)
        if match:
            field_name = match.group(1)
            pattern = match.group(2)

            return WildcardPattern(
                pattern=pattern,
                field_name=field_name,
                starts_with_wildcard=pattern.startswith('*') or pattern.startswith('?'),
                ends_with_wildcard=pattern.endswith('*') or pattern.endswith('?'),
                contains_wildcard='*' in pattern or '?' in pattern
            )

        return None

    def _create_wildcard_issue(
        self,
        query: ParsedQuery,
        wildcard_pattern: WildcardPattern
    ) -> Issue | None:
        """
        ワイルドカード問題のIssueを作成

        Args:
            query: 解析されたクエリ
            wildcard_pattern: ワイルドカードパターン

        Returns:
            Issue（問題がない場合None）
        """
        # 問題がないパターンはスキップ
        if not wildcard_pattern.is_problematic():
            # 末尾ワイルドカードのみの場合はINFO程度
            if wildcard_pattern.ends_with_wildcard and not wildcard_pattern.starts_with_wildcard:
                # 情報提供のみ
                return None

        # 重要度の判定
        severity = self._determine_severity(wildcard_pattern)

        # タイトルと説明の生成
        title = self._generate_title(wildcard_pattern)
        description = self._generate_description(wildcard_pattern)
        suggestion = self._generate_suggestion(wildcard_pattern)

        # Auto-fix の生成（可能な場合）
        auto_fix_code = self._generate_auto_fix(query, wildcard_pattern)

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
            auto_fix_available=auto_fix_code is not None,
            auto_fix_code=auto_fix_code,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html",
            tags=['elasticsearch', 'wildcard', 'performance'],
            metadata={
                'pattern': wildcard_pattern.pattern,
                'field_name': wildcard_pattern.field_name,
                'starts_with_wildcard': wildcard_pattern.starts_with_wildcard
            }
        )

    def _determine_severity(self, pattern: WildcardPattern) -> Severity:
        """重要度を判定"""
        if pattern.starts_with_wildcard:
            return Severity.CRITICAL  # 先頭ワイルドカードは最悪
        if pattern.contains_wildcard and not pattern.ends_with_wildcard:
            return Severity.HIGH  # 中間ワイルドカード
        return Severity.MEDIUM

    def _generate_title(self, pattern: WildcardPattern) -> str:
        """タイトルを生成"""
        if pattern.starts_with_wildcard:
            return f"Leading wildcard in field '{pattern.field_name}' causes full index scan"
        return f"Wildcard pattern in field '{pattern.field_name}' may impact performance"

    def _generate_description(self, pattern: WildcardPattern) -> str:
        """説明を生成"""
        if pattern.starts_with_wildcard:
            return (
                f"The wildcard pattern '{pattern.pattern}' starts with a wildcard character. "
                f"This prevents Elasticsearch from using the index efficiently and forces a full scan "
                f"of all documents. This can severely impact query performance, especially on large indices."
            )

        return (
            f"The wildcard pattern '{pattern.pattern}' may impact query performance. "
            f"Wildcard queries are generally slower than term or prefix queries."
        )

    def _generate_suggestion(self, pattern: WildcardPattern) -> str:
        """修正提案を生成"""
        suggestions = []

        if pattern.starts_with_wildcard:
            suggestions.append(
                "Consider using an n-gram tokenizer or edge n-gram tokenizer in your index mapping "
                "to enable efficient prefix/suffix searches."
            )
            suggestions.append(
                "If you need full-text search, consider using a match query instead."
            )
            suggestions.append(
                "For exact substring matching, consider using a regexp query with anchors, "
                "though this is still slower than term queries."
            )

        if pattern.ends_with_wildcard and not pattern.starts_with_wildcard:
            suggestions.append(
                "For prefix matching, consider using a prefix query instead of wildcard query "
                "for better performance."
            )

        return " ".join(suggestions) if suggestions else "Review the wildcard pattern for optimization opportunities."

    def _generate_auto_fix(
        self,
        query: ParsedQuery,
        pattern: WildcardPattern
    ) -> str | None:
        """
        自動修正コードを生成（可能な場合）

        Args:
            query: 解析されたクエリ
            pattern: ワイルドカードパターン

        Returns:
            修正コード（自動修正できない場合None）
        """
        # 末尾ワイルドカードのみの場合 → prefixQueryに変換可能
        if (pattern.ends_with_wildcard and
            not pattern.starts_with_wildcard and
            '*' not in pattern.pattern[:-1]):  # 末尾以外にワイルドカードがない

            prefix = pattern.pattern.rstrip('*')
            return f'QueryBuilders.prefixQuery("{pattern.field_name}", "{prefix}")'

        # それ以外は自動修正困難
        return None
