"""
Integration tests for Elasticsearch analyzer

This module tests end-to-end functionality with parser and detectors.
"""

import pytest
from pathlib import Path
from multidb_analyzer.core import (
    get_plugin_manager,
    DatabaseType,
    Severity
)
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector,
    MappingDetector,
    ShardDetector
)


class TestElasticsearchIntegration:
    """Integration test suite for Elasticsearch analyzer"""

    @pytest.fixture
    def plugin_manager(self):
        """Create and configure plugin manager"""
        from multidb_analyzer.core.plugin_manager import PluginManager
        manager = PluginManager()

        # Register Elasticsearch plugin
        manager.register_plugin(
            db_type=DatabaseType.ELASTICSEARCH,
            parser=ElasticsearchJavaParser(),
            detectors=[
                WildcardDetector(),
                ScriptQueryDetector(),
                MappingDetector(),
                ShardDetector()
            ]
        )

        return manager

    # Test 1: End-to-end analysis (parser + detectors)
    def test_end_to_end_analysis(self, plugin_manager, tmp_path):
        """Test complete analysis flow from file to issues"""
        java_file = tmp_path / "SearchService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class SearchService {
                public void searchWithWildcard() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Should detect the leading wildcard issue
        assert len(issues) >= 1
        wildcard_issues = [i for i in issues if 'wildcard' in i.title.lower()]
        assert len(wildcard_issues) >= 1

        issue = wildcard_issues[0]
        assert issue.severity == Severity.CRITICAL
        assert issue.file_path == str(java_file)

    # Test 2: Plugin manager registration
    def test_plugin_manager_registration(self):
        """Test plugin manager registration and retrieval"""
        from multidb_analyzer.core.plugin_manager import PluginManager

        manager = PluginManager()
        parser = ElasticsearchJavaParser()
        detectors = [WildcardDetector(), ScriptQueryDetector()]

        manager.register_plugin(
            db_type=DatabaseType.ELASTICSEARCH,
            parser=parser,
            detectors=detectors
        )

        # Verify plugin is registered
        assert DatabaseType.ELASTICSEARCH in manager._plugins
        plugin = manager._plugins[DatabaseType.ELASTICSEARCH]
        assert plugin.db_type == DatabaseType.ELASTICSEARCH
        assert plugin.parser is not None
        assert len(plugin.detector_registry._detectors) >= 2

    # Test 3: Multiple file analysis
    def test_multiple_file_analysis(self, plugin_manager, tmp_path):
        """Test analysis of multiple files"""
        # Create multiple Java files
        file1 = tmp_path / "Search1.java"
        file1.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;
            public class Search1 {
                public void search() {
                    QueryBuilders.wildcardQuery("field1", "*pattern");
                }
            }
        """, encoding='utf-8')

        file2 = tmp_path / "Search2.java"
        file2.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.script.Script;
            public class Search2 {
                public void search() {
                    QueryBuilders.scriptQuery(new Script("doc['field'].value > 100"));
                }
            }
        """, encoding='utf-8')

        # Analyze both files
        issues1 = plugin_manager.analyze_file(file1, DatabaseType.ELASTICSEARCH)
        issues2 = plugin_manager.analyze_file(file2, DatabaseType.ELASTICSEARCH)

        # Both should have issues
        assert len(issues1) >= 1
        assert len(issues2) >= 1

        # Different detector types
        wildcard_in_1 = any('wildcard' in i.title.lower() for i in issues1)
        script_in_2 = any('script' in i.title.lower() for i in issues2)

        assert wildcard_in_1 or script_in_2

    # Test 4: All detectors integration
    def test_all_detectors_integration(self, tmp_path):
        """Test that all four detectors work together"""
        java_file = tmp_path / "CompleteService.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.indices.CreateIndexRequest;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.script.Script;
            import org.elasticsearch.action.index.IndexRequest;
            import org.elasticsearch.common.settings.Settings;
            import java.util.Map;

            public class CompleteService {
                public void searchWildcard() {
                    QueryBuilders.wildcardQuery("name", "*pattern");
                }

                public void searchScript() {
                    QueryBuilders.scriptQuery(new Script("doc['price'].value > 100"));
                }

                public void indexDynamic(Map<String, Object> data) {
                    new IndexRequest("index").source(data);
                }

                public void createIndex() {
                    new CreateIndexRequest("logs")
                        .settings(Settings.builder()
                            .put("index.number_of_shards", 100)
                            .put("index.number_of_replicas", 0)
                        );
                }
            }
        """, encoding='utf-8')

        # Create fresh plugin manager for this test
        from multidb_analyzer.core.plugin_manager import PluginManager
        manager = PluginManager()
        manager.register_plugin(
            db_type=DatabaseType.ELASTICSEARCH,
            parser=ElasticsearchJavaParser(),
            detectors=[
                WildcardDetector(),
                ScriptQueryDetector(),
                MappingDetector(),
                ShardDetector()
            ]
        )

        issues = manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Should detect issues from multiple detectors
        assert len(issues) >= 2

        detector_names = set(i.detector_name for i in issues)
        # Should have at least 2 different detector types
        assert len(detector_names) >= 2

    # Test 5: Large file handling
    def test_large_file_handling(self, plugin_manager, tmp_path):
        """Test handling of large Java files"""
        java_file = tmp_path / "LargeService.java"

        # Create a file with many methods
        methods = []
        for i in range(50):
            methods.append(f"""
                public void search{i}() {{
                    QueryBuilders.matchQuery("field{i}", "value{i}");
                }}
            """)

        content = f"""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class LargeService {{
                {''.join(methods)}
            }}
        """

        java_file.write_text(content, encoding='utf-8')

        # Should handle large file without errors
        issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Should successfully parse (even if no critical issues found)
        assert issues is not None
        assert isinstance(issues, list)

    # Test 6: Error recovery
    def test_error_recovery(self, plugin_manager, tmp_path):
        """Test that system recovers from parsing errors"""
        # Create file with invalid syntax
        java_file = tmp_path / "Invalid.java"
        java_file.write_text("""
            This is not valid Java {{ syntax
        """, encoding='utf-8')

        # Should not crash
        try:
            issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)
            # Should return empty list or handle gracefully
            assert issues is not None
            assert isinstance(issues, list)
        except Exception as e:
            # If exception is raised, it should be handled gracefully
            pytest.fail(f"Should not raise exception on invalid code: {e}")

    # Test 7: Statistics collection
    def test_statistics_collection(self, plugin_manager, tmp_path):
        """Test that statistics are collected correctly"""
        java_file = tmp_path / "StatsTest.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class StatsTest {
                public void search1() {
                    QueryBuilders.matchQuery("field1", "value1");
                }
                public void search2() {
                    QueryBuilders.termQuery("field2", "value2");
                }
            }
        """, encoding='utf-8')

        issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Get statistics
        stats = plugin_manager.get_statistics()

        assert stats is not None
        assert isinstance(stats, dict)
        # Should have some statistics
        assert len(stats) > 0

    # Test 8: Issue filtering by severity
    def test_issue_filtering_by_severity(self, tmp_path):
        """Test filtering issues by severity level"""
        java_file = tmp_path / "FilterTest.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.script.Script;

            public class FilterTest {
                public void criticalIssue() {
                    QueryBuilders.wildcardQuery("name", "*pattern");
                }
                public void highIssue() {
                    QueryBuilders.scriptQuery(new Script("doc['x'].value > 10"));
                }
            }
        """, encoding='utf-8')

        from multidb_analyzer.core.plugin_manager import PluginManager
        manager = PluginManager()
        manager.register_plugin(
            db_type=DatabaseType.ELASTICSEARCH,
            parser=ElasticsearchJavaParser(),
            detectors=[WildcardDetector(), ScriptQueryDetector()]
        )

        issues = manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Filter by severity
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        high_issues = [i for i in issues if i.severity == Severity.HIGH]

        # Should have at least some critical or high severity issues
        assert len(critical_issues) + len(high_issues) >= 1

    # Test 9: Metadata extraction integration
    def test_metadata_extraction_integration(self, plugin_manager, tmp_path):
        """Test that metadata is properly extracted and passed through"""
        java_file = tmp_path / "MetadataTest.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.index.query.QueryBuilders;

            public class MetadataTest {
                public void searchInClass() {
                    QueryBuilders.wildcardQuery("email", "*@example.com");
                }
            }
        """, encoding='utf-8')

        issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        if issues:
            issue = issues[0]
            # Check that metadata is present
            assert issue.metadata is not None
            assert isinstance(issue.metadata, dict)

            # Check that file path and line number are correct
            assert issue.file_path == str(java_file)
            assert issue.line_number > 0

            # Check that class/method info is extracted
            assert issue.class_name is not None or issue.method_name is not None

    # Test 10: Real-world code analysis
    def test_real_world_code_analysis(self, plugin_manager, tmp_path):
        """Test analysis of realistic Elasticsearch Java code"""
        java_file = tmp_path / "ProductSearchService.java"
        java_file.write_text("""
            package com.example.search;

            import org.elasticsearch.action.search.SearchRequest;
            import org.elasticsearch.action.search.SearchResponse;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.index.query.QueryBuilders;
            import org.elasticsearch.index.query.BoolQueryBuilder;
            import org.elasticsearch.search.builder.SearchSourceBuilder;

            public class ProductSearchService {
                private final RestHighLevelClient client;

                public ProductSearchService(RestHighLevelClient client) {
                    this.client = client;
                }

                public SearchResponse searchProducts(String keyword, double minPrice, double maxPrice) {
                    BoolQueryBuilder boolQuery = QueryBuilders.boolQuery();

                    // Problematic: leading wildcard
                    if (keyword != null) {
                        boolQuery.must(QueryBuilders.wildcardQuery("name", "*" + keyword));
                    }

                    // Good: range query
                    if (minPrice > 0 || maxPrice > 0) {
                        boolQuery.filter(QueryBuilders.rangeQuery("price")
                            .gte(minPrice)
                            .lte(maxPrice));
                    }

                    SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();
                    sourceBuilder.query(boolQuery);

                    SearchRequest searchRequest = new SearchRequest("products");
                    searchRequest.source(sourceBuilder);

                    try {
                        return client.search(searchRequest);
                    } catch (Exception e) {
                        throw new RuntimeException("Search failed", e);
                    }
                }
            }
        """, encoding='utf-8')

        issues = plugin_manager.analyze_file(java_file, DatabaseType.ELASTICSEARCH)

        # Should detect the wildcard issue
        assert len(issues) >= 1

        wildcard_issues = [i for i in issues if 'wildcard' in i.title.lower()]
        assert len(wildcard_issues) >= 1

        issue = wildcard_issues[0]
        # Verify issue details
        assert issue.severity == Severity.CRITICAL
        assert 'name' in str(issue.metadata.get('field_name', ''))
        assert issue.suggestion is not None
        assert len(issue.suggestion) > 0
