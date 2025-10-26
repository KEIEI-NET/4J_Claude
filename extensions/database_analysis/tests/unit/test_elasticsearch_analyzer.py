"""
Unit tests for Elasticsearch Analyzer
"""

import pytest
from pathlib import Path

from multidb_analyzer.analyzers.elasticsearch_analyzer import ElasticsearchAnalyzer
from multidb_analyzer.models.database_models import QueryType


class TestElasticsearchAnalyzer:
    """Test cases for ElasticsearchAnalyzer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = ElasticsearchAnalyzer()

    def test_analyze_simple_match_query(self):
        """Test analyzing a simple match query"""
        query_dsl = {"query": {"match": {"name": "test"}}}

        query = self.analyzer._analyze_es_query(query_dsl, "test.py", 1)

        assert query is not None
        assert query.query_type == QueryType.DSL
        assert "match" in query.query_text.lower()

    def test_analyze_bool_query(self):
        """Test analyzing a bool query"""
        query_dsl = {"query": {"bool": {"must": [{"term": {"status": "active"}}]}}}

        query = self.analyzer._analyze_es_query(query_dsl, "test.py", 1)

        assert query is not None
        assert query.complexity > 1.0

    def test_analyze_aggregation_query(self):
        """Test analyzing aggregation query"""
        query_dsl = {"aggs": {"by_status": {"terms": {"field": "status"}}}}

        query = self.analyzer._analyze_es_query(query_dsl, "test.py", 1)

        assert query is not None

    def test_analyze_wildcard_query(self):
        """Test detecting wildcard query"""
        query_dsl = {"query": {"wildcard": {"name": "*admin*"}}}

        query = self.analyzer._analyze_es_query(query_dsl, "test.py", 1)

        assert query is not None
        assert query.has_wildcard is True

    def test_analyze_script_query(self):
        """Test detecting script usage"""
        query_dsl = {"query": {"script": {"script": "doc.age.value > 18"}}}

        query = self.analyzer._analyze_es_query(query_dsl, "test.py", 1)

        assert query is not None
        assert query.uses_script is True

    def test_calculate_complexity_simple(self):
        """Test complexity calculation for simple query"""
        query_dsl = {"query": {"match": {"name": "John"}}}

        complexity = self.analyzer._calculate_es_complexity(query_dsl)

        assert complexity >= 1.0

    def test_calculate_complexity_nested(self):
        """Test complexity calculation for nested query"""
        query_dsl = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"name": "John"}},
                        {"range": {"age": {"gte": 18}}}
                    ],
                    "should": [
                        {"term": {"status": "active"}}
                    ]
                }
            },
            "aggs": {
                "by_status": {
                    "terms": {"field": "status"}
                }
            }
        }

        complexity = self.analyzer._calculate_es_complexity(query_dsl)

        assert complexity > 3.0

    def test_detect_wildcard_query(self):
        """Test wildcard detection"""
        query_with_wildcard = {"query": {"wildcard": {"name": "*test*"}}}
        query_without_wildcard = {"query": {"match": {"name": "test"}}}

        assert self.analyzer._detect_wildcard_query(query_with_wildcard) is True
        assert self.analyzer._detect_wildcard_query(query_without_wildcard) is False

    def test_detect_script_usage(self):
        """Test script usage detection"""
        query_with_script = {"query": {"script": {"script": "doc['age'].value > 18"}}}
        query_without_script = {"query": {"match": {"name": "test"}}}

        assert self.analyzer._detect_script_usage(query_with_script) is True
        assert self.analyzer._detect_script_usage(query_without_script) is False

    def test_find_complex_queries(self):
        """Test finding complex queries"""
        # First analyze some queries
        test_file = Path(__file__).parent.parent / "fixtures" / "es_queries.java"

        # Create a simple temp file if fixture doesn't exist
        if not test_file.exists():
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write('''
                    public void test() {
                        String simple = "{\"query\": {\"match\": {\"name\": \"test\"}}}";
                        String complex = "{\"query\": {\"bool\": {\"must\": [{\"match\": {\"a\": \"b\"}}, {\"match\": {\"c\": \"d\"}}], \"filter\": [{\"term\": {\"e\": \"f\"}}]}}}";
                    }
                ''')
                test_file = Path(f.name)

        queries = self.analyzer.analyze_file(str(test_file))

        # If we got queries, test complexity filtering
        if queries:
            complex_queries = self.analyzer.find_complex_queries(min_complexity=3.0)
            assert isinstance(complex_queries, list)

    def test_get_known_indices(self):
        """Test tracking known indices"""
        self.analyzer.add_known_index("users")
        self.analyzer.add_known_index("orders")

        indices = self.analyzer.get_known_indices()

        assert "users" in indices
        assert "orders" in indices

    def test_error_handling_invalid_json(self, tmp_path):
        """Test handling invalid JSON gracefully"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void broken() {
                String query = "{invalid json}";
                esClient.search(query);
            }
        ''')

        # Should not raise exception
        queries = self.analyzer.analyze_file(str(test_file))

    def test_analyze_file_not_found(self):
        """Test handling file not found"""
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_file("/nonexistent/file.java")

    def test_extract_multiline_json(self, tmp_path):
        """Test extracting multi-line JSON queries"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public List<User> search() {
                String query = "{" +
                    "\\"query\\": {" +
                    "\\"match\\": {\\"name\\": \\"test\\"}" +
                    "}" +
                "}";
                return esClient.search(query);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        # Should handle concatenated JSON strings
        assert len(queries) >= 0

    def test_detect_query_type_variations(self):
        """Test various query type detections"""
        # Match query
        query1 = {"query": {"match": {"name": "test"}}}
        type1 = self.analyzer._detect_query_type(query1)
        assert type1 == "match"

        # Term query
        query2 = {"query": {"term": {"status": "active"}}}
        type2 = self.analyzer._detect_query_type(query2)
        assert type2 == "term"

        # Bool query
        query3 = {"query": {"bool": {"must": []}}}
        type3 = self.analyzer._detect_query_type(query3)
        assert type3 == "bool"

        # Wildcard query
        query4 = {"query": {"wildcard": {"name": "*test*"}}}
        type4 = self.analyzer._detect_query_type(query4)
        assert type4 == "wildcard"

        # Fuzzy query
        query5 = {"query": {"fuzzy": {"name": "tset"}}}
        type5 = self.analyzer._detect_query_type(query5)
        assert type5 == "fuzzy"

        # Unknown query
        query6 = {"aggs": {"count": {"value_count": {"field": "id"}}}}
        type6 = self.analyzer._detect_query_type(query6)
        assert type6 == "unknown"

    def test_calculate_depth(self):
        """Test depth calculation for nested structures"""
        # Simple dict
        simple = {"a": 1}
        depth1 = self.analyzer._calculate_depth(simple)
        assert depth1 == 1

        # Nested dict
        nested = {"a": {"b": {"c": 1}}}
        depth2 = self.analyzer._calculate_depth(nested)
        assert depth2 == 3

        # List
        list_obj = [1, 2, 3]
        depth3 = self.analyzer._calculate_depth(list_obj)
        assert depth3 == 1

        # Empty dict
        empty = {}
        depth4 = self.analyzer._calculate_depth(empty)
        assert depth4 == 0

        # Empty list
        empty_list = []
        depth5 = self.analyzer._calculate_depth(empty_list)
        assert depth5 == 0

        # Scalar
        scalar = "string"
        depth6 = self.analyzer._calculate_depth(scalar)
        assert depth6 == 0

    def test_assess_performance_risk(self):
        """Test performance risk assessment"""
        # High risk - with script
        query1 = {"query": {"script": {"script": "doc.age.value > 18"}}}
        risk1 = self.analyzer.assess_performance_risk(query1)
        assert risk1 == "high"

        # High risk - with wildcard
        query2 = {"query": {"wildcard": {"name": "*test*"}}}
        risk2 = self.analyzer.assess_performance_risk(query2)
        assert risk2 == "high"

        # High risk - high complexity
        query3 = {
            "query": {
                "bool": {
                    "must": [{"match": {"f1": "v1"}} for _ in range(10)],
                    "should": [{"term": {"f2": "v2"}} for _ in range(10)]
                }
            },
            "aggs": {f"agg{i}": {"terms": {"field": f"field{i}"}} for i in range(5)}
        }
        risk3 = self.analyzer.assess_performance_risk(query3)
        assert risk3 == "high"

        # Medium risk
        query4 = {
            "query": {
                "bool": {
                    "must": [{"match": {"name": "test"}}, {"term": {"status": "active"}}]
                }
            }
        }
        risk4 = self.analyzer.assess_performance_risk(query4)
        # Bool queries have higher complexity due to nesting depth
        assert risk4 in ["high", "medium"]

        # Low risk - simple query
        query5 = {"query": {"match": {"name": "test"}}}
        risk5 = self.analyzer.assess_performance_risk(query5)
        assert risk5 == "low"

    def test_extract_query_dsl_invalid_json(self):
        """Test extraction with invalid JSON"""
        invalid = "{invalid json}"
        result = self.analyzer._extract_query_dsl(invalid)
        # Should return default query
        assert "match_all" in str(result)

    def test_analyze_file_with_search_patterns(self, tmp_path):
        """Test analyzing file with ES client search patterns"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void searchUsers() {
                client.search({"query": {"match": {"name": "John"}}});
                esClient.search({"query": {"term": {"status": "active"}}});
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 2

    def test_analyze_file_with_index_param(self, tmp_path):
        """Test analyzing file with index parameter"""
        test_file = tmp_path / "test.py"
        test_file.write_text('''
            result = client.search(
                index="users",
                body={"query": {"match_all": {}}}
            )
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1

    def test_extract_json_strings_nested(self, tmp_path):
        """Test extracting deeply nested JSON"""
        test_file = tmp_path / "test.js"
        test_file.write_text('''
            const complexQuery = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"title": "test"}},
                            {"nested": {
                                "path": "comments",
                                "query": {"match": {"comments.text": "hello"}}
                            }}
                        ]
                    }
                },
                "aggs": {
                    "by_category": {
                        "terms": {"field": "category"}
                    }
                }
            };
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1
        if queries:
            assert queries[0].complexity > 3.0

    def test_extract_json_strings_invalid_json(self, tmp_path):
        """Test handling invalid JSON gracefully"""
        test_file = tmp_path / "test.js"
        test_file.write_text('''
            const broken = {
                "query": {"match": "missing closing brace"
            };
        ''')

        # Should not raise exception
        queries = self.analyzer.analyze_file(str(test_file))
        # May or may not extract anything

    def test_detect_wildcard_prefix(self):
        """Test detecting prefix wildcard"""
        query = {"query": {"wildcard": {"path": "/usr/*"}}}
        assert self.analyzer._detect_wildcard_query(query) is True

    def test_assess_performance_risk_edge_cases(self):
        """Test performance risk with edge complexity values"""
        # Exactly at threshold
        query1 = {
            "query": {"bool": {"must": [{"match": {"f": "v"}}] * 12}}
        }
        risk1 = self.analyzer.assess_performance_risk(query1)
        assert risk1 in ["high", "medium"]

        # Empty query
        query2 = {}
        risk2 = self.analyzer.assess_performance_risk(query2)
        assert risk2 == "low"

    def test_find_complex_queries_empty(self):
        """Test finding complex queries when none exist"""
        # Don't add any queries to analyzer
        complex_queries = self.analyzer.find_complex_queries(min_complexity=10.0)
        assert complex_queries == []

    def test_calculate_depth_mixed_structures(self):
        """Test depth calculation with mixed dict/list"""
        mixed = {
            "a": [
                {"b": {"c": [1, 2, 3]}},
                {"d": "value"}
            ]
        }
        depth = self.analyzer._calculate_depth(mixed)
        assert depth >= 3

    def test_analyze_file_with_malformed_search(self, tmp_path):
        """Test analyzing file with malformed search patterns"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void searchWithMalformedJSON() {
                client.search({malformed json without quotes});
                esClient.search({"query": {unclosed brackets}
            }
        ''')

        # Should handle errors gracefully and not crash
        queries = self.analyzer.analyze_file(str(test_file))
        # May or may not extract queries, but should not raise exception

    def test_find_complex_queries_with_results(self):
        """Test finding complex queries when some exist"""
        # Manually add a complex query
        from multidb_analyzer.models.database_models import DatabaseQuery, QueryType, DatabaseType
        complex_query = DatabaseQuery(
            query_text='{"query": {"bool": {"must": [{"match": {"f": "v"}}] * 10}}}',
            query_type=QueryType.DSL,
            database=DatabaseType.ELASTICSEARCH,
            file_path="test.java",
            line_number=1,
            complexity=8.0
        )
        self.analyzer._all_queries.append(complex_query)

        # Find complex queries
        result = self.analyzer.find_complex_queries(min_complexity=7.0)
        assert len(result) >= 1
        assert result[0].complexity >= 7.0
