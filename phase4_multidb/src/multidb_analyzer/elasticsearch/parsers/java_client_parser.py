"""
Elasticsearch Java Client Parser

Elasticsearch Java クライアントを使用したコードを解析し、
検索クエリ、Aggregation、インデックス操作を抽出
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import javalang

from multidb_analyzer.core.base_parser import (
    BaseParser,
    DatabaseType,
    QueryType,
    ParsedQuery,
    JavaParserMixin
)


class ElasticsearchJavaParser(BaseParser, JavaParserMixin):
    """
    Elasticsearch Javaクライアントのパーサー

    対応クライアント:
    - RestHighLevelClient (Elasticsearch 7.x)
    - RestClient (低レベルAPI)
    - TransportClient (非推奨だが legacy対応)
    """

    # Elasticsearchクライアントのパターン
    ES_CLIENT_PATTERNS = [
        'RestHighLevelClient',
        'RestClient',
        'TransportClient',
        'ElasticsearchClient'
    ]

    # 検索関連のメソッド
    SEARCH_METHODS = [
        'search',
        'searchScroll',
        'multiSearch',
        'count'
    ]

    # インデックス操作のメソッド
    INDEX_METHODS = [
        'index',
        'bulk',
        'update',
        'delete',
        'updateByQuery',
        'deleteByQuery'
    ]

    # QueryBuildersのパターン（要注意）
    QUERY_BUILDER_PATTERNS = {
        'wildcardQuery': QueryType.SEARCH,
        'scriptQuery': QueryType.SEARCH,
        'matchQuery': QueryType.SEARCH,
        'termQuery': QueryType.SEARCH,
        'rangeQuery': QueryType.SEARCH,
        'boolQuery': QueryType.SEARCH,
        'multiMatchQuery': QueryType.SEARCH,
    }

    # Aggregationのパターン
    AGGREGATION_PATTERNS = [
        'AggregationBuilders',
        'terms',
        'sum',
        'avg',
        'max',
        'min',
        'cardinality',
        'dateHistogram'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._current_file: Optional[Path] = None
        self._current_source: Optional[str] = None

    def get_db_type(self) -> DatabaseType:
        """Elasticsearchを返す"""
        return DatabaseType.ELASTICSEARCH

    def can_parse(self, file_path: Path) -> bool:
        """
        Javaファイルで、Elasticsearchクライアントのimportがあるか確認

        Args:
            file_path: ファイルパス

        Returns:
            解析可能な場合True
        """
        if not self._is_java_file(file_path):
            return False

        try:
            content = self._read_java_file(file_path)

            # Elasticsearchのimportチェック
            es_imports = [
                'org.elasticsearch.client',
                'org.elasticsearch.action',
                'org.elasticsearch.index.query',
                'co.elastic.clients'  # Elasticsearch Java API Client 8.x
            ]

            return any(imp in content for imp in es_imports)
        except Exception:
            return False

    def parse_file(self, file_path: Path) -> List[ParsedQuery]:
        """
        Javaファイルを解析してElasticsearchクエリを抽出

        Args:
            file_path: 解析するファイル

        Returns:
            解析されたクエリのリスト
        """
        self._current_file = file_path
        self._current_source = self._read_java_file(file_path)

        queries = []

        try:
            # Java ASTを生成
            tree = javalang.parse.parse(self._current_source)

            # メソッド呼び出しを解析
            for path, node in tree.filter(javalang.tree.MethodInvocation):
                query = self._parse_method_invocation(node, path)
                if query:
                    queries.append(query)

        except javalang.parser.JavaSyntaxError as e:
            print(f"Java syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        self._queries.extend(queries)
        return queries

    def _parse_method_invocation(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[ParsedQuery]:
        """
        メソッド呼び出しを解析してElasticsearchクエリを抽出

        Args:
            node: MethodInvocationノード
            path: ASTパス

        Returns:
            ParsedQuery（Elasticsearchクエリでない場合None）
        """
        method_name = node.member

        # 検索メソッドのチェック
        if method_name in self.SEARCH_METHODS:
            return self._parse_search_method(node, path)

        # インデックス操作のチェック
        if method_name in self.INDEX_METHODS:
            return self._parse_index_method(node, path)

        # QueryBuildersのチェック
        if method_name in self.QUERY_BUILDER_PATTERNS:
            return self._parse_query_builder(node, path)

        # Aggregationのチェック
        if self._is_aggregation(node):
            return self._parse_aggregation(node, path)

        return None

    def _parse_search_method(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[ParsedQuery]:
        """
        検索メソッドを解析

        例:
        client.search(searchRequest, RequestOptions.DEFAULT);
        """
        method_name = node.member
        line_number = self._get_line_number(node, path)

        # クエリテキストの抽出を試みる
        query_text = self._extract_query_text(node, path)

        # メタデータの収集
        metadata = {
            'method': method_name,
            'client_type': self._detect_client_type(path)
        }

        return ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text=query_text or f"{method_name}(...)",
            file_path=str(self._current_file),
            line_number=line_number,
            method_name=self._get_method_name(node, path),
            class_name=self._get_class_name(node, path),
            metadata=metadata
        )

    def _parse_index_method(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[ParsedQuery]:
        """
        インデックス操作メソッドを解析

        例:
        client.index(indexRequest, RequestOptions.DEFAULT);
        client.bulk(bulkRequest, RequestOptions.DEFAULT);
        """
        method_name = node.member
        line_number = self._get_line_number(node, path)

        # クエリタイプの判定
        query_type_map = {
            'index': QueryType.INSERT,
            'update': QueryType.UPDATE,
            'delete': QueryType.DELETE,
            'bulk': QueryType.INSERT,
            'updateByQuery': QueryType.UPDATE,
            'deleteByQuery': QueryType.DELETE
        }
        query_type = query_type_map.get(method_name, QueryType.UNKNOWN)

        query_text = f"{method_name}(...)"

        return ParsedQuery(
            query_type=query_type,
            query_text=query_text,
            file_path=str(self._current_file),
            line_number=line_number,
            method_name=self._get_method_name(node, path),
            class_name=self._get_class_name(node, path),
            metadata={'method': method_name}
        )

    def _parse_query_builder(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[ParsedQuery]:
        """
        QueryBuildersメソッドを解析

        例:
        QueryBuilders.wildcardQuery("name", "*smith");
        QueryBuilders.scriptQuery(new Script("doc['price'].value > 100"));
        """
        method_name = node.member
        line_number = self._get_line_number(node, path)

        # クエリパラメータの抽出
        params = {}
        if node.arguments:
            for i, arg in enumerate(node.arguments):
                param_value = self._extract_argument_value(arg)
                params[f'arg{i}'] = param_value

        # 特別な検出: wildcardQuery
        is_wildcard = method_name == 'wildcardQuery'
        is_script = method_name == 'scriptQuery'

        metadata = {
            'query_builder_method': method_name,
            'is_wildcard': is_wildcard,
            'is_script': is_script,
            'parameters': params
        }

        query_text = f"QueryBuilders.{method_name}({', '.join(str(v) for v in params.values())})"

        return ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text=query_text,
            file_path=str(self._current_file),
            line_number=line_number,
            method_name=self._get_method_name(node, path),
            class_name=self._get_class_name(node, path),
            parameters=params,
            metadata=metadata
        )

    def _parse_aggregation(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[ParsedQuery]:
        """
        Aggregationを解析

        例:
        AggregationBuilders.terms("by_category").field("category.keyword");
        """
        method_name = node.member
        line_number = self._get_line_number(node, path)

        query_text = f"AggregationBuilders.{method_name}(...)"

        return ParsedQuery(
            query_type=QueryType.AGGREGATE,
            query_text=query_text,
            file_path=str(self._current_file),
            line_number=line_number,
            method_name=self._get_method_name(node, path),
            class_name=self._get_class_name(node, path),
            metadata={'aggregation_type': method_name}
        )

    def _is_aggregation(self, node: javalang.tree.MethodInvocation) -> bool:
        """Aggregationメソッドか判定"""
        if node.qualifier and 'AggregationBuilders' in str(node.qualifier):
            return True

        return node.member in self.AGGREGATION_PATTERNS

    def _extract_query_text(
        self,
        node: javalang.tree.MethodInvocation,
        path: List
    ) -> Optional[str]:
        """
        クエリテキストを抽出（可能な場合）

        完全なクエリの抽出は困難なため、メソッド名と周辺コードを返す
        """
        # 簡易実装: 周辺のソースコードを抽出
        line_number = self._get_line_number(node, path)
        if line_number and self._current_source:
            lines = self._current_source.split('\n')
            if 0 <= line_number - 1 < len(lines):
                return lines[line_number - 1].strip()

        return None

    def _extract_argument_value(self, arg) -> Any:
        """引数の値を抽出"""
        if isinstance(arg, javalang.tree.Literal):
            return arg.value

        if isinstance(arg, javalang.tree.MemberReference):
            return arg.member

        # その他の場合は文字列表現
        return str(arg)

    def _detect_client_type(self, path: List) -> str:
        """クライアントタイプを検出"""
        # パスを辿ってクライアントタイプを推測
        for node in path:
            if hasattr(node, 'type') and node.type:
                type_name = str(node.type)
                for client_pattern in self.ES_CLIENT_PATTERNS:
                    if client_pattern in type_name:
                        return client_pattern

        return 'Unknown'

    def _get_line_number(
        self,
        node,
        path: List
    ) -> int:
        """行番号を取得"""
        # javalangのノードにはposition属性がある場合がある
        if hasattr(node, 'position') and node.position:
            return node.position.line

        # 代替: ソースコードから検索
        if self._current_source and hasattr(node, 'member'):
            pattern = re.escape(node.member)
            for i, line in enumerate(self._current_source.split('\n'), 1):
                if re.search(pattern, line):
                    return i

        return 0
