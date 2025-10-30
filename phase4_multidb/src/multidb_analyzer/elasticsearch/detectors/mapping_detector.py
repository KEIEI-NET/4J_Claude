"""
Mapping Detector for Elasticsearch

Dynamic Mappingへの依存や型の不一致を検出
Dynamic Mappingは便利だが、プロダクション環境では
予期しない型の問題やパフォーマンス低下を引き起こす可能性がある
"""

from typing import List, Dict, Set, Optional
import re

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.core.base_parser import ParsedQuery
from multidb_analyzer.elasticsearch.models.es_models import MappingIssue


class MappingDetector(BaseDetector):
    """
    Mapping検出器

    検出パターン:
    1. Dynamic Mappingへの依存 (MEDIUM)
    2. 同じフィールドへの異なる型のアクセス (HIGH)
    3. Text型フィールドでのAnalyzer未指定 (MEDIUM)
    4. Nested/Object型の不適切な使用 (MEDIUM)

    例:
    ```java
    // ❌ MEDIUM - Dynamic Mappingに依存
    // 明示的なマッピング定義なしでインデックス
    IndexRequest request = new IndexRequest("products")
        .source(jsonMap);  // 型が不明確

    // ❌ HIGH - 同じフィールドに異なる型
    // ある場所では String として扱い
    request.source("timestamp", "2024-01-01");
    // 別の場所では Long として扱う
    request.source("timestamp", System.currentTimeMillis());

    // ⚠️ MEDIUM - Analyzer未指定のText検索
    QueryBuilders.matchQuery("description", "search term");
    // descriptionフィールドのAnalyzer設定が不明

    // ✅ Good - 明示的なマッピング定義
    PutMappingRequest mappingRequest = new PutMappingRequest("products")
        .source(
            "properties", Map.of(
                "description", Map.of(
                    "type", "text",
                    "analyzer", "standard"
                ),
                "timestamp", Map.of(
                    "type", "date",
                    "format", "epoch_millis"
                )
            )
        );
    ```
    """

    # Dynamic Mappingを示唆するパターン
    DYNAMIC_MAPPING_INDICATORS = [
        'source(jsonMap',
        'source(objectMapper',
        'source(json',
        'setSource',
        'source(Map<',
    ]

    # 型指定のキーワード
    TYPE_KEYWORDS = {
        'text': ['matchQuery', 'matchPhraseQuery', 'multiMatchQuery'],
        'keyword': ['termQuery', 'termsQuery', 'prefixQuery'],
        'long': ['rangeQuery'],
        'date': ['rangeQuery'],
        'boolean': ['termQuery'],
        'geo_point': ['geoDistanceQuery', 'geoBoundingBoxQuery'],
    }

    # Analyzerが重要なクエリタイプ
    ANALYZER_REQUIRED_QUERIES = [
        'matchQuery',
        'matchPhraseQuery',
        'multiMatchQuery',
        'queryStringQuery',
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self._field_type_map: Dict[str, Set[str]] = {}
        self._text_fields: Set[str] = set()
        self._enable_type_checking = self.get_config_value('enable_type_checking', True)

    def get_name(self) -> str:
        return "MappingDetector"

    def get_severity(self) -> Severity:
        return Severity.MEDIUM

    def get_category(self) -> IssueCategory:
        return IssueCategory.BEST_PRACTICE

    def detect(self, queries: List[ParsedQuery]) -> List[Issue]:
        """
        Mapping問題を検出

        Args:
            queries: 解析されたクエリのリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        # フィールド使用状況を収集
        self._collect_field_usage(queries)

        for query in queries:
            # Dynamic Mappingチェック
            if self._is_dynamic_mapping(query):
                issue = self._create_dynamic_mapping_issue(query)
                if issue:
                    issues.append(issue)

            # 型の不一致チェック
            type_issues = self._check_type_consistency(query)
            issues.extend(type_issues)

            # Analyzerチェック
            analyzer_issue = self._check_analyzer_usage(query)
            if analyzer_issue:
                issues.append(analyzer_issue)

        self._issues.extend(issues)
        return issues

    def _collect_field_usage(self, queries: List[ParsedQuery]) -> None:
        """
        クエリからフィールド使用状況を収集

        Args:
            queries: 解析されたクエリのリスト
        """
        for query in queries:
            if not query.parameters:
                continue

            # フィールド名を取得（通常はarg0）
            field_name = query.parameters.get('arg0', '')
            if not isinstance(field_name, str) or not field_name:
                continue

            # クエリタイプから推測される型を記録
            query_method = query.method_name or ''
            inferred_type = self._infer_field_type(query_method)

            if inferred_type:
                if field_name not in self._field_type_map:
                    self._field_type_map[field_name] = set()
                self._field_type_map[field_name].add(inferred_type)

            # Textクエリのフィールドを記録
            if any(method in query_method for method in self.ANALYZER_REQUIRED_QUERIES):
                self._text_fields.add(field_name)

    def _infer_field_type(self, query_method: str) -> Optional[str]:
        """
        クエリメソッドから推測されるフィールド型を取得

        Args:
            query_method: クエリメソッド名

        Returns:
            推測される型（不明な場合None）
        """
        for field_type, methods in self.TYPE_KEYWORDS.items():
            if any(method in query_method for method in methods):
                return field_type
        return None

    def _is_dynamic_mapping(self, query: ParsedQuery) -> bool:
        """
        Dynamic Mappingへの依存を判定

        Args:
            query: 解析されたクエリ

        Returns:
            Dynamic Mappingに依存している場合True
        """
        # IndexRequestでsource()を使っている
        if 'IndexRequest' in query.query_text or 'index(' in query.query_text:
            # Dynamic Mapping indicators をチェック
            return any(indicator in query.query_text for indicator in self.DYNAMIC_MAPPING_INDICATORS)

        return False

    def _check_type_consistency(self, query: ParsedQuery) -> List[Issue]:
        """
        フィールド型の一貫性をチェック

        Args:
            query: 解析されたクエリ

        Returns:
            型の不一致に関する問題のリスト
        """
        if not self._enable_type_checking:
            return []

        issues = []

        if not query.parameters:
            return issues

        field_name = query.parameters.get('arg0', '')
        if not isinstance(field_name, str) or not field_name:
            return issues

        # このフィールドに複数の型が推測される場合
        if field_name in self._field_type_map:
            inferred_types = self._field_type_map[field_name]
            if len(inferred_types) > 1:
                # インデックス名を取得（メタデータから、または不明）
                index_name = query.metadata.get('index_name', 'unknown')

                mapping_issue = MappingIssue(
                    index_name=index_name,
                    field_name=field_name,
                    issue_type="type_inconsistency",
                    expected_type=None,
                    actual_type=", ".join(inferred_types),  # リストを文字列に変換
                    suggestion="Field type should be consistent across queries"
                )

                issue = self._create_type_inconsistency_issue(query, mapping_issue)
                if issue:
                    issues.append(issue)

        return issues

    def _check_analyzer_usage(self, query: ParsedQuery) -> Optional[Issue]:
        """
        Analyzerの使用状況をチェック

        Args:
            query: 解析されたクエリ

        Returns:
            Analyzer関連の問題（なければNone）
        """
        query_method = query.method_name or ''

        # Analyzerが重要なクエリか
        if not any(method in query_method for method in self.ANALYZER_REQUIRED_QUERIES):
            return None

        if not query.parameters:
            return None

        field_name = query.parameters.get('arg0', '')
        if not isinstance(field_name, str) or not field_name:
            return None

        # Analyzerの指定があるかチェック
        has_analyzer = False
        if query.parameters:
            # analyzer パラメータの存在チェック
            has_analyzer = 'analyzer' in query.parameters or 'search_analyzer' in query.parameters

        # Analyzerが未指定の場合、警告
        if not has_analyzer and field_name in self._text_fields:
            # インデックス名を取得（メタデータから、または不明）
            index_name = query.metadata.get('index_name', 'unknown')

            mapping_issue = MappingIssue(
                index_name=index_name,
                field_name=field_name,
                issue_type="missing_analyzer",
                expected_type="text",
                actual_type=None,
                suggestion="Specify an analyzer for text field analysis"
            )

            return self._create_analyzer_issue(query, mapping_issue)

        return None

    def _create_dynamic_mapping_issue(self, query: ParsedQuery) -> Optional[Issue]:
        """
        Dynamic Mapping問題のIssueを作成

        Args:
            query: 解析されたクエリ

        Returns:
            Issue
        """
        title = "Dynamic mapping dependency detected"

        description = (
            "This code appears to rely on dynamic mapping by indexing documents "
            "without explicit type definitions. While dynamic mapping is convenient "
            "during development, it can lead to unexpected type conflicts and "
            "performance issues in production. Elasticsearch will automatically infer "
            "types, which may not match your intentions."
        )

        suggestion = (
            "Define explicit mappings for your indices before indexing documents. "
            "Use the Put Mapping API to specify field types, analyzers, and other properties. "
            "This ensures consistent behavior and optimal performance. "
            "Example: Create a mapping template with specific field types like 'text', 'keyword', 'date', etc."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.MEDIUM,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/explicit-mapping.html",
            tags=['elasticsearch', 'mapping', 'dynamic-mapping', 'best-practice'],
            metadata={
                'issue_type': 'dynamic_mapping',
                'recommendation': 'Use explicit mappings'
            }
        )

    def _create_type_inconsistency_issue(
        self,
        query: ParsedQuery,
        mapping_issue: MappingIssue
    ) -> Optional[Issue]:
        """
        型の不一致問題のIssueを作成

        Args:
            query: 解析されたクエリ
            mapping_issue: マッピング問題情報

        Returns:
            Issue
        """
        inferred_types = mapping_issue.actual_type or []
        types_str = ", ".join(inferred_types)

        title = f"Inconsistent field type usage for '{mapping_issue.field_name}'"

        description = (
            f"The field '{mapping_issue.field_name}' is used with multiple inferred types: {types_str}. "
            f"This suggests the field might be accessed inconsistently across different queries, "
            f"which can lead to mapping conflicts or unexpected query behavior. "
            f"Elasticsearch requires consistent field types across the index."
        )

        suggestion = (
            f"Review all usages of '{mapping_issue.field_name}' and ensure they are consistent. "
            f"Define an explicit mapping for this field with a single, appropriate type. "
            f"If you need to store different types of data, consider using different field names "
            f"or multi-fields with different mappings."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.HIGH,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html",
            tags=['elasticsearch', 'mapping', 'type-inconsistency', 'reliability'],
            metadata={
                'field_name': mapping_issue.field_name,
                'inferred_types': inferred_types,
                'issue_type': 'type_inconsistency'
            }
        )

    def _create_analyzer_issue(
        self,
        query: ParsedQuery,
        mapping_issue: MappingIssue
    ) -> Optional[Issue]:
        """
        Analyzer未指定問題のIssueを作成

        Args:
            query: 解析されたクエリ
            mapping_issue: マッピング問題情報

        Returns:
            Issue
        """
        title = f"Text field '{mapping_issue.field_name}' used without explicit analyzer"

        description = (
            f"The text field '{mapping_issue.field_name}' is used in a full-text search query "
            f"without an explicitly defined analyzer. While Elasticsearch uses the 'standard' "
            f"analyzer by default, explicitly defining analyzers ensures consistent search behavior "
            f"and allows for language-specific or custom text processing."
        )

        suggestion = (
            f"Define an explicit analyzer for the '{mapping_issue.field_name}' field in your index mapping. "
            f"Choose an appropriate analyzer based on your use case: "
            f"'standard' for general text, 'english' for English text with stemming, "
            f"'keyword' for exact matching, or create a custom analyzer for specific requirements. "
            f"You can also specify a different 'search_analyzer' for query-time analysis."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.MEDIUM,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-analyzers.html",
            tags=['elasticsearch', 'mapping', 'analyzer', 'text-search'],
            metadata={
                'field_name': mapping_issue.field_name,
                'issue_type': 'missing_analyzer',
                'recommendation': 'Define explicit analyzer'
            }
        )
