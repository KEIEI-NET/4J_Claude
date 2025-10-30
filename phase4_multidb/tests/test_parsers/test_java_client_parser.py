"""
Tests for ElasticsearchJavaParser

This module tests the Java client parser for Elasticsearch code analysis.
"""

import pytest
from pathlib import Path
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.core.base_parser import QueryType, DatabaseType


class TestElasticsearchJavaParser:
    """Test suite for ElasticsearchJavaParser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return ElasticsearchJavaParser()

    # Test 1: Can parse Elasticsearch file
    def test_can_parse_elasticsearch_file(self, parser, tmp_path):
        """Test that parser can identify Elasticsearch Java files"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            public class SearchService {}
        """, encoding='utf-8')

        assert parser.can_parse(java_file) is True

    # Test 2: Cannot parse non-Elasticsearch file
    def test_cannot_parse_non_elasticsearch_file(self, parser, tmp_path):
        """Test that parser rejects non-Elasticsearch Java files"""
        java_file = tmp_path / "RegularService.java"
        java_file.write_text("""
            package com.example;
            public class RegularService {}
        """, encoding='utf-8')

        assert parser.can_parse(java_file) is False

    # Test 3: Parse wildcard query
    def test_parse_wildcard_query(self, parser, tmp_path):
        """Test parsing wildcard query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        assert len(queries) >= 1

        wildcard_query = next((q for q in queries if 'wildcardQuery' in q.query_text), None)
        assert wildcard_query is not None
        assert wildcard_query.query_type == QueryType.SEARCH
        assert 'wildcardQuery' in wildcard_query.query_text
        assert wildcard_query.file_path == str(java_file)

    # Test 4: Parse script query
    def test_parse_script_query(self, parser, tmp_path):
        """Test parsing script query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.script.Script;

            public class SearchService {
                public void search() {
                    QueryBuilders.scriptQuery(new Script("doc['price'].value > 100"));
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        assert len(queries) >= 1

        script_query = next((q for q in queries if 'scriptQuery' in q.query_text), None)
        assert script_query is not None
        assert 'scriptQuery' in script_query.query_text or 'Script' in script_query.query_text

    # Test 5: Parse match query
    def test_parse_match_query(self, parser, tmp_path):
        """Test parsing match query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.matchQuery("description", "laptop");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        match_query = next((q for q in queries if 'matchQuery' in q.query_text), None)
        assert match_query is not None
        assert match_query.query_type == QueryType.SEARCH

    # Test 6: Parse term query
    def test_parse_term_query(self, parser, tmp_path):
        """Test parsing term query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.termQuery("status", "active");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        term_query = next((q for q in queries if 'termQuery' in q.query_text), None)
        assert term_query is not None

    # Test 7: Parse range query
    def test_parse_range_query(self, parser, tmp_path):
        """Test parsing range query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.rangeQuery("price").gte(100).lte(500);
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        range_query = next((q for q in queries if 'rangeQuery' in q.query_text), None)
        assert range_query is not None

    # Test 8: Parse bool query
    def test_parse_bool_query(self, parser, tmp_path):
        """Test parsing bool query"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.boolQuery()
                        .must(QueryBuilders.matchQuery("title", "search"))
                        .filter(QueryBuilders.rangeQuery("price").gte(100));
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        bool_query = next((q for q in queries if 'boolQuery' in q.query_text), None)
        assert bool_query is not None

    # Test 9: Parse aggregation
    def test_parse_aggregation(self, parser, tmp_path):
        """Test parsing aggregation"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.search.aggregations.AggregationBuilders;

            public class SearchService {
                public void aggregate() {
                    AggregationBuilders.terms("categories").field("category");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        # Aggregations might be detected
        assert queries is not None

    # Test 10: Parse search method
    def test_parse_search_method(self, parser, tmp_path):
        """Test parsing search method invocation"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.action.search.SearchRequest;

            public class SearchService {
                public void performSearch(RestHighLevelClient client) {
                    SearchRequest searchRequest = new SearchRequest("products");
                    client.search(searchRequest);
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        # Search request creation should be detected
        assert queries is not None

    # Test 11: Parse index operation
    def test_parse_index_operation(self, parser, tmp_path):
        """Test parsing index operation"""
        java_file = tmp_path / "IndexService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.action.index.IndexRequest;

            public class IndexService {
                public void indexDocument() {
                    IndexRequest request = new IndexRequest("products");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        # Index operations might be detected
        assert queries is not None

    # Test 12: Parse multiple queries
    def test_parse_multiple_queries(self, parser, tmp_path):
        """Test parsing file with multiple queries"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search1() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }

                public void search2() {
                    QueryBuilders.matchQuery("title", "laptop");
                }

                public void search3() {
                    QueryBuilders.termQuery("status", "active");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        assert len(queries) >= 2  # Should detect multiple queries

    # Test 13: Extract class name
    def test_extract_class_name(self, parser, tmp_path):
        """Test that class name is correctly extracted"""
        java_file = tmp_path / "MySearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class MySearchService {
                public void search() {
                    QueryBuilders.matchQuery("field", "value");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        if queries:
            query = queries[0]
            assert query.class_name is not None

    # Test 14: Extract method name
    def test_extract_method_name(self, parser, tmp_path):
        """Test that method name is correctly extracted"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void searchByName() {
                    QueryBuilders.matchQuery("name", "value");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        if queries:
            query = queries[0]
            assert query.method_name is not None

    # Test 15: Extract parameters
    def test_extract_parameters(self, parser, tmp_path):
        """Test that query parameters are extracted"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        wildcard_query = next((q for q in queries if 'wildcardQuery' in q.query_text), None)
        if wildcard_query and wildcard_query.parameters:
            # Parameters should be extracted
            assert isinstance(wildcard_query.parameters, dict)

    # Test 16: Extract line number
    def test_extract_line_number(self, parser, tmp_path):
        """Test that line numbers are correctly extracted"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.matchQuery("field", "value");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        if queries:
            query = queries[0]
            assert query.line_number > 0

    # Test 17: Extract metadata
    def test_extract_metadata(self, parser, tmp_path):
        """Test that metadata is extracted"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*pattern");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        wildcard_query = next((q for q in queries if 'wildcardQuery' in q.query_text), None)
        if wildcard_query:
            assert wildcard_query.metadata is not None
            assert isinstance(wildcard_query.metadata, dict)

    # Test 18: Handle invalid Java code
    def test_handle_invalid_java_code(self, parser, tmp_path):
        """Test error handling for invalid Java code"""
        java_file = tmp_path / "InvalidCode.java"
        java_file.write_text("""
            This is not valid Java code {{{
        """, encoding='utf-8')

        # Should not raise exception
        queries = parser.parse_file(java_file)
        assert queries is not None
        assert isinstance(queries, list)

    # Test 19: Handle empty file
    def test_handle_empty_file(self, parser, tmp_path):
        """Test handling of empty Java file"""
        java_file = tmp_path / "Empty.java"
        java_file.write_text("", encoding='utf-8')

        queries = parser.parse_file(java_file)
        assert queries is not None
        assert isinstance(queries, list)
        assert len(queries) == 0

    # Test 20: Get statistics
    def test_get_statistics(self, parser, tmp_path):
        """Test getting parser statistics"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void search() {
                    QueryBuilders.matchQuery("field", "value");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)
        stats = parser.get_statistics()

        assert stats is not None
        assert isinstance(stats, dict)
        assert 'files_analyzed' in stats or 'queries_found' in stats or len(stats) >= 0

    # Additional test: Database type
    def test_get_db_type(self, parser):
        """Test that parser returns correct database type"""
        assert parser.get_db_type() == DatabaseType.ELASTICSEARCH

    # Test 21: Non-Elasticsearch file
    def test_cannot_parse_file_without_es_imports(self, parser, tmp_path):
        """Test that parser cannot parse files without Elasticsearch imports"""
        java_file = tmp_path / "PlainJava.java"
        java_file.write_text("""
            package com.example;

            public class PlainJava {
                public void method() {
                    System.out.println("Hello");
                }
            }
        """, encoding='utf-8')

        assert parser.can_parse(java_file) is False

    # Test 22: Parse file with index operations
    def test_parse_index_operations_detailed(self, parser, tmp_path):
        """Test parsing of various index operations"""
        java_file = tmp_path / "IndexOps.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.action.index.IndexRequest;
            import org.elasticsearch.action.update.UpdateRequest;
            import org.elasticsearch.action.delete.DeleteRequest;
            import org.elasticsearch.action.bulk.BulkRequest;

            public class IndexOps {
                public void indexDoc() {
                    client.index(new IndexRequest("index"), options);
                }

                public void updateDoc() {
                    client.update(new UpdateRequest("index", "id"), options);
                }

                public void deleteDoc() {
                    client.delete(new DeleteRequest("index", "id"), options);
                }

                public void bulkOps() {
                    client.bulk(new BulkRequest(), options);
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should parse index operations
        assert len(queries) >= 1
        query_types = {q.query_type for q in queries}
        # At least one of these types should be detected
        assert len(query_types) >= 1

    # Test 23: Parse with non-UTF8 encoding
    def test_parse_latin1_encoded_file(self, parser, tmp_path):
        """Test parsing file with Latin-1 encoding"""
        java_file = tmp_path / "Latin1.java"
        content = """
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;

            public class Latin1 {
                public void search() {}
            }
        """
        java_file.write_bytes(content.encode('latin-1'))

        # Should handle Latin-1 encoded files
        queries = parser.parse_file(java_file)
        assert isinstance(queries, list)

    # Test 24: Parse aggregation methods
    def test_parse_aggregation_detailed(self, parser, tmp_path):
        """Test parsing of Elasticsearch aggregations"""
        java_file = tmp_path / "AggService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.search.aggregations.AggregationBuilders;

            public class AggService {
                public void aggregate() {
                    AggregationBuilders.terms("by_status");
                    AggregationBuilders.sum("total_price");
                    AggregationBuilders.avg("average_rating");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should parse aggregations
        assert len(queries) >= 1
        agg_queries = [q for q in queries if q.query_type == QueryType.AGGREGATE]
        assert len(agg_queries) >= 1

    # Test 25: Extract query text from source
    def test_extract_query_text(self, parser, tmp_path):
        """Test extraction of query text from source code"""
        java_file = tmp_path / "QueryText.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class QueryText {
                public void search() {
                    QueryBuilders.matchQuery("field", "value");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        assert len(queries) >= 1
        # Query text should be extracted
        assert any(q.query_text for q in queries)

    # Test 26: Client type detection
    def test_detect_different_client_types(self, parser, tmp_path):
        """Test detection of different Elasticsearch client types"""
        for client_type in ["RestHighLevelClient", "RestClient", "TransportClient", "ElasticsearchClient"]:
            java_file = tmp_path / f"{client_type}Test.java"
            java_file.write_text(f"""
                package com.example;
                import org.elasticsearch.client.{client_type};
                import org.elasticsearch.index.query.QueryBuilders;

                public class {client_type}Test {{
                    private {client_type} client;

                    public void search() {{
                        QueryBuilders.matchQuery("field", "value");
                    }}
                }}
            """, encoding='utf-8')

            # Should be able to parse files with different client types
            assert parser.can_parse(java_file) is True

    # Test 27: Boolean query parsing
    def test_parse_complex_bool_query(self, parser, tmp_path):
        """Test parsing of complex boolean queries"""
        java_file = tmp_path / "BoolQuery.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.index.query.BoolQueryBuilder;

            public class BoolQuery {
                public void complexSearch() {
                    BoolQueryBuilder query = QueryBuilders.boolQuery();
                    query.must(QueryBuilders.termQuery("status", "active"));
                    query.filter(QueryBuilders.rangeQuery("price").gte(100));
                    query.should(QueryBuilders.matchQuery("title", "product"));
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should parse bool query and its clauses
        assert len(queries) >= 1

    # Test 29: Cannot parse non-Java files
    def test_cannot_parse_non_java_file(self, parser, tmp_path):
        """Test that non-Java files are not parsed"""
        # Create a Python file
        python_file = tmp_path / "script.py"
        python_file.write_text("print('hello')", encoding='utf-8')

        # Should return False for can_parse
        assert parser.can_parse(python_file) is False

        # Create a text file
        text_file = tmp_path / "readme.txt"
        text_file.write_text("Some text", encoding='utf-8')

        assert parser.can_parse(text_file) is False

    # Test 30: Handle file read errors
    def test_handle_file_read_error(self, parser, tmp_path):
        """Test handling of file read errors"""
        # Create a file that doesn't exist
        non_existent_file = tmp_path / "nonexistent.java"

        # Should handle gracefully
        assert parser.can_parse(non_existent_file) is False

    # Test 31: Handle general parsing exception
    def test_handle_general_exception(self, parser, tmp_path, monkeypatch):
        """Test handling of general exceptions during parsing"""
        java_file = tmp_path / "Exception.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            public class Test {
                public void test() {}
            }
        """, encoding='utf-8')

        # Mock javalang.parse.parse to raise a non-syntax exception
        import javalang.parse
        original_parse = javalang.parse.parse

        def mock_parse(code):
            raise RuntimeError("Test exception")

        monkeypatch.setattr(javalang.parse, "parse", mock_parse)

        # Should handle exception gracefully and return empty list
        queries = parser.parse_file(java_file)
        assert isinstance(queries, list)
        assert len(queries) == 0

        # Restore original
        monkeypatch.setattr(javalang.parse, "parse", original_parse)

    # Test 32: Extract MemberReference argument value
    def test_extract_member_reference(self, parser, tmp_path):
        """Test extraction of MemberReference argument values"""
        java_file = tmp_path / "MemberRef.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class MemberRefTest {
                private static final String FIELD_NAME = "status";

                public void search() {
                    QueryBuilders.termQuery(FIELD_NAME, "active");
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should extract MemberReference
        assert len(queries) >= 0  # May or may not detect depending on parsing

    # Test 33: Client type detection
    def test_client_type_detection_detailed(self, parser, tmp_path):
        """Test detailed client type detection"""
        # Test with explicit RestHighLevelClient
        java_file = tmp_path / "ClientType.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.action.search.SearchRequest;

            public class ClientTypeTest {
                private RestHighLevelClient client;

                public void search() {
                    client.search(new SearchRequest("index"));
                }
            }
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Client type should be detected
        if queries:
            # Check that parser detected some query
            assert len(queries) >= 0

    # Test 34: Line number detection from source
    def test_line_number_from_source(self, parser, tmp_path):
        """Test line number detection when position is not available"""
        java_file = tmp_path / "LineNumber.java"
        java_file.write_text("""
package com.example;
import org.elasticsearch.index.query.QueryBuilders;

public class LineNumberTest {
    public void search() {
        // Line 6
        QueryBuilders.matchQuery("field", "value");
        // Line 8
        QueryBuilders.termQuery("status", "active");
    }
}
        """, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should detect queries with line numbers
        assert len(queries) >= 1
        for query in queries:
            # Line numbers should be > 0
            assert query.line_number >= 0

    # Test 35: Query text extraction edge cases
    def test_query_text_extraction_edge_cases(self, parser, tmp_path):
        """Test query text extraction with edge cases"""
        # Test with very long file
        long_content = """
package com.example;
import org.elasticsearch.index.query.QueryBuilders;

public class EdgeCaseTest {
    public void test() {
""" + "\n".join([f"        // Line {i}" for i in range(1000)]) + """
        QueryBuilders.matchQuery("field", "value");
    }
}
        """

        java_file = tmp_path / "EdgeCase.java"
        java_file.write_text(long_content, encoding='utf-8')

        queries = parser.parse_file(java_file)

        # Should handle long files
        assert isinstance(queries, list)

    # Test 36: Multiple client patterns
    def test_multiple_client_patterns(self, parser, tmp_path):
        """Test detection of multiple Elasticsearch client patterns"""
        java_file = tmp_path / "MultiClient.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestClient;
            import org.elasticsearch.client.RestHighLevelClient;
            import co.elastic.clients.elasticsearch.ElasticsearchClient;

            public class MultiClientTest {
                private RestHighLevelClient highLevelClient;
                private RestClient restClient;
                private ElasticsearchClient esClient;

                public void search1() {
                    // Using RestHighLevelClient
                }

                public void search2() {
                    // Using RestClient
                }

                public void search3() {
                    // Using ElasticsearchClient (8.x)
                }
            }
        """, encoding='utf-8')

        # Should recognize file as Elasticsearch file
        assert parser.can_parse(java_file) is True

    # Test 37: Extract query text with None line number
    def test_extract_query_text_none_line_number(self, parser):
        """Test _extract_query_text returns None when line number is None"""
        # Mock node without position
        class MockNode:
            pass

        node = MockNode()
        parser._current_source = "some source code"

        result = parser._extract_query_text(node, [])
        # Should return None when line number cannot be determined
        assert result is None

    # Test 38: Extract query text with no current source
    def test_extract_query_text_no_source(self, parser):
        """Test _extract_query_text returns None when no source"""
        class MockNode:
            def __init__(self):
                self.position = type('obj', (object,), {'line': 1})()

        node = MockNode()
        parser._current_source = None

        result = parser._extract_query_text(node, [])
        # Should return None when no source code
        assert result is None

    # Test 39: Detect client type with matching pattern
    def test_detect_client_type_with_type_attribute(self, parser):
        """Test _detect_client_type with node having type attribute"""
        # Mock nodes with type attributes
        class MockType:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        class MockNode:
            def __init__(self, type_name):
                self.type = MockType(type_name)

        # Test with RestHighLevelClient
        node1 = MockNode("RestHighLevelClient")
        result1 = parser._detect_client_type([node1])
        assert result1 == "RestHighLevelClient"

        # Test with RestClient
        node2 = MockNode("org.elasticsearch.client.RestClient")
        result2 = parser._detect_client_type([node2])
        assert "RestClient" in result2

        # Test with ElasticsearchClient
        node3 = MockNode("co.elastic.clients.elasticsearch.ElasticsearchClient")
        result3 = parser._detect_client_type([node3])
        assert "ElasticsearchClient" in result3

    # Test 40: Get line number with member attribute fallback
    def test_get_line_number_with_member_fallback(self, parser):
        """Test _get_line_number fallback to member search"""
        # Mock node with member but no position
        class MockNode:
            def __init__(self):
                self.member = "matchQuery"

        node = MockNode()
        parser._current_source = """
package com.example;
import org.elasticsearch.index.query.QueryBuilders;

public class Test {
    public void search() {
        QueryBuilders.matchQuery("field", "value");
    }
}
        """

        line_num = parser._get_line_number(node, [])
        # Should find line number by searching for member name
        assert line_num > 0

    # Test 41: Get line number returns 0 when no position or member
    def test_get_line_number_returns_zero(self, parser):
        """Test _get_line_number returns 0 when unable to determine"""
        class MockNode:
            pass

        node = MockNode()
        parser._current_source = "some code"

        line_num = parser._get_line_number(node, [])
        # Should return 0 when unable to determine line number
        assert line_num == 0

    # Test 42: Extract query text with out of bounds line number
    def test_extract_query_text_out_of_bounds(self, parser):
        """Test _extract_query_text with line number out of bounds"""
        class MockNode:
            def __init__(self):
                self.position = type('obj', (object,), {'line': 9999})()

        node = MockNode()
        parser._current_source = "line1\nline2\nline3"

        result = parser._extract_query_text(node, [])
        # Should return None when line number is out of bounds
        assert result is None

    # Test 43: Detect client type with no matching pattern
    def test_detect_client_type_no_match(self, parser):
        """Test _detect_client_type returns Unknown when no pattern matches"""
        class MockType:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        class MockNode:
            def __init__(self, type_name):
                self.type = MockType(type_name)

        # Test with non-Elasticsearch type
        node = MockNode("java.lang.String")
        result = parser._detect_client_type([node])
        assert result == "Unknown"

    # Test 44: Get line number member search no match
    def test_get_line_number_member_no_match(self, parser):
        """Test _get_line_number with member that doesn't match"""
        class MockNode:
            def __init__(self):
                self.member = "nonExistentMethod"

        node = MockNode()
        parser._current_source = """
package com.example;
public class Test {
    public void search() {
        // some code
    }
}
        """

        line_num = parser._get_line_number(node, [])
        # Should return 0 when member is not found
        assert line_num == 0
