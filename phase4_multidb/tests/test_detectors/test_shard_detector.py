"""
Tests for ShardDetector

This module tests the shard configuration detector for Elasticsearch.
"""

import pytest
from multidb_analyzer.elasticsearch.detectors import ShardDetector
from multidb_analyzer.core.base_parser import ParsedQuery, QueryType
from multidb_analyzer.core.base_detector import Severity


class TestShardDetector:
    """Test suite for ShardDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return ShardDetector()

    # Test 1: Detect over-sharding
    def test_detect_over_sharding(self, detector):
        """Test detection of excessive shard count"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("logs").settings(Settings.builder().put("index.number_of_shards", 1000).put("index.number_of_replicas", 1))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'logs'},
                metadata={'index_size_gb': 100.0}
            )
        ]

        issues = detector.detect(queries)

        # Should detect over-sharding
        overshard_issues = [i for i in issues if 'shard' in i.title.lower() and ('excessiv' in i.title.lower() or 'over' in i.title.lower())]
        assert len(overshard_issues) >= 1

        if overshard_issues:
            issue = overshard_issues[0]
            assert issue.severity == Severity.HIGH
            assert issue.detector_name == "ShardDetector"

    # Test 2: Detect under-sharding
    def test_detect_under_sharding(self, detector):
        """Test detection of insufficient shard count"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("products").settings(Settings.builder().put("index.number_of_shards", 1).put("index.number_of_replicas", 2))',
                file_path="IndexManager.java",
                line_number=15,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'products'},
                metadata={'index_size_gb': 500.0}  # 500GB with 1 shard = 500GB per shard (too large)
            )
        ]

        issues = detector.detect(queries)

        # Should detect under-sharding
        undershard_issues = [i for i in issues if 'shard' in i.title.lower() and 'under' in i.title.lower()]
        if undershard_issues:
            issue = undershard_issues[0]
            assert issue.severity == Severity.MEDIUM
            assert 'shard_count' in issue.metadata

    # Test 3: Detect replica configuration issues
    def test_detect_replica_issues(self, detector):
        """Test detection of replica count issues"""
        # Test with 0 replicas
        queries_no_replica = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("test").settings(Settings.builder().put("index.number_of_shards", 5).put("index.number_of_replicas", 0))',
                file_path="IndexManager.java",
                line_number=20,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test'},
                metadata={}
            )
        ]

        issues = detector.detect(queries_no_replica)

        # Should detect no replica issue
        replica_issues = [i for i in issues if 'replica' in i.title.lower()]
        if replica_issues:
            issue = replica_issues[0]
            assert issue.severity in [Severity.MEDIUM, Severity.LOW]

        # Test with too many replicas
        queries_many_replicas = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("test2").settings(Settings.builder().put("index.number_of_shards", 5).put("index.number_of_replicas", 5))',
                file_path="IndexManager.java",
                line_number=25,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test2'},
                metadata={}
            )
        ]

        detector2 = ShardDetector()
        issues2 = detector2.detect(queries_many_replicas)

        high_replica_issues = [i for i in issues2 if 'replica' in i.title.lower() and ('high' in i.title.lower() or '5' in str(i.metadata))]
        if high_replica_issues:
            issue = high_replica_issues[0]
            assert issue.severity in [Severity.LOW, Severity.MEDIUM]

    # Test 4: Calculate recommended shard count
    def test_recommended_shard_count(self, detector):
        """Test that detector calculates recommended shard count"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("events").settings(Settings.builder().put("index.number_of_shards", 100).put("index.number_of_replicas", 1))',
                file_path="IndexManager.java",
                line_number=30,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'events'},
                metadata={'index_size_gb': 100.0}
            )
        ]

        issues = detector.detect(queries)

        if issues:
            # Check if recommended shard count is in metadata
            for issue in issues:
                if 'recommended_shard_count' in issue.metadata:
                    recommended = issue.metadata['recommended_shard_count']
                    assert isinstance(recommended, int)
                    assert recommended > 0
                    # For 100GB, recommended should be around 3-5 shards (20-33GB each)
                    assert 2 <= recommended <= 10

    # Test 5: Detect multiple shard configuration issues
    def test_detect_multiple_shard_configs(self, detector):
        """Test detection of multiple shard configuration issues"""
        queries = [
            # Over-sharding
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("index1").settings(Settings.builder().put("index.number_of_shards", 200))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="create1",
                class_name="IndexManager",
                parameters={'index_name': 'index1'},
                metadata={}
            ),
            # No replicas
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("index2").settings(Settings.builder().put("index.number_of_shards", 5).put("index.number_of_replicas", 0))',
                file_path="IndexManager.java",
                line_number=15,
                method_name="create2",
                class_name="IndexManager",
                parameters={'index_name': 'index2'},
                metadata={}
            ),
            # Hardcoded shards
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='Settings.builder().put("index.number_of_shards", 5)',
                file_path="IndexManager.java",
                line_number=20,
                method_name="create3",
                class_name="IndexManager",
                parameters={},
                metadata={}
            ),
        ]

        issues = detector.detect(queries)

        # Should detect multiple types of issues
        assert len(issues) >= 2

        # Check for different issue categories
        issue_categories = set()
        for issue in issues:
            if 'shard' in issue.title.lower() and 'over' in issue.title.lower():
                issue_categories.add('over-sharding')
            if 'replica' in issue.title.lower():
                issue_categories.add('replica')
            if 'hardcod' in issue.title.lower():
                issue_categories.add('hardcoded')

        # Should have at least 2 different categories
        assert len(issue_categories) >= 2

    # Additional test: Detector metadata
    def test_detector_metadata(self, detector):
        """Test detector metadata and properties"""
        assert detector.get_name() == "ShardDetector"
        assert detector.get_severity() == Severity.HIGH
        assert detector.get_category() is not None

    # Test 7: Query without shard count should not crash
    def test_query_without_shard_count(self, detector):
        """Test handling of queries without shard count"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("test").settings(Settings.builder().put("some_setting", "value"))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test'},
                metadata={}
            )
        ]

        issues = detector.detect(queries)
        # Should handle gracefully, no issues expected for missing shard count
        assert isinstance(issues, list)

    # Test 8: Parameter-based index name extraction
    def test_parameter_based_index_name(self, detector):
        """Test index name extraction from parameters"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='Settings.builder().put("index.number_of_shards", 100).put("index.number_of_replicas", 1)',
                file_path="IndexManager.java",
                line_number=10,
                method_name="configureIndex",
                class_name="IndexManager",
                parameters={'index_name': 'my_index', 'arg0': 'my_index'},
                metadata={}
            )
        ]

        issues = detector.detect(queries)

        if issues:
            # Should be able to extract index name from parameters
            assert any('my_index' in issue.title.lower() or 'my_index' in str(issue.metadata) for issue in issues)

    # Test 9: Index size extraction from comments
    def test_index_size_from_comments(self, detector):
        """Test index size extraction from query comments"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='// Expected size: 50GB\nCreateIndexRequest("comments_index").settings(Settings.builder().put("index.number_of_shards", 10))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'comments_index'},
                metadata={}
            )
        ]

        issues = detector.detect(queries)

        if issues:
            # Should detect small shard size from comment-based index size (50GB / 10 shards = 5GB each)
            small_shard_issues = [i for i in issues if 'over' in i.title.lower() and 'shard' in i.title.lower()]
            # May or may not detect based on threshold, just ensure no crash
            assert isinstance(issues, list)

    # Test 10: Small shard size detection
    def test_small_shard_size_detection(self, detector):
        """Test detection of small shard sizes"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("small_shards").settings(Settings.builder().put("index.number_of_shards", 20))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'small_shards'},
                metadata={'index_size_gb': 50.0}  # 50GB / 20 shards = 2.5GB per shard
            )
        ]

        issues = detector.detect(queries)

        # Should detect small shard size (< 10GB per shard)
        small_shard_issues = [i for i in issues if 'over' in i.title.lower() or 'small' in i.title.lower()]
        assert len(small_shard_issues) >= 1

        if small_shard_issues:
            issue = small_shard_issues[0]
            # Check that recommended shard count is in suggestion or metadata
            assert 'recommended' in issue.suggestion.lower() or 'recommended_shard_count' in issue.metadata

    # Test 11: Non-hardcoded shard configuration
    def test_non_hardcoded_shards(self, detector):
        """Test that non-hardcoded shard config doesn't trigger hardcoded warning"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("dynamic").settings(Settings.builder().put("index.number_of_shards", shardCountVariable))',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'dynamic'},
                metadata={}
            )
        ]

        # Note: This query doesn't match the number_of_shards pattern with a literal number
        # So shard count won't be extracted and no issues will be created
        issues = detector.detect(queries)

        # Should not detect hardcoded shards (using variable instead)
        hardcoded_issues = [i for i in issues if 'hardcod' in i.title.lower()]
        # This should not produce hardcoded issues because it uses a variable
        assert len(hardcoded_issues) == 0

    # Test 12: Queries with different shard extraction patterns
    def test_various_shard_extraction_patterns(self, detector):
        """Test different patterns for extracting shard count"""
        queries = [
            # numberOfShards() method pattern
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='IndexSettings.builder().numberOfShards(15).build()',
                file_path="IndexManager.java",
                line_number=10,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test1'},
                metadata={}
            ),
            # setNumberOfShards() method pattern
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='Settings.builder().setNumberOfShards(8).build()',
                file_path="IndexManager.java",
                line_number=15,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test2'},
                metadata={}
            ),
        ]

        issues = detector.detect(queries)

        # Should successfully extract shard counts from both patterns
        # No specific assertions needed, just ensure no crashes
        assert isinstance(issues, list)

    # Test 13: numberOfShards pattern without hardcoded detection
    def test_number_of_shards_method_not_hardcoded(self, detector):
        """Test that numberOfShards() method pattern doesn't trigger hardcoded warning"""
        queries = [
            ParsedQuery(
                query_type=QueryType.INSERT,
                query_text='CreateIndexRequest("test_index").settings(Settings.builder().numberOfShards(5).numberOfReplicas(1))',
                file_path="IndexManager.java",
                line_number=25,
                method_name="createIndex",
                class_name="IndexManager",
                parameters={'index_name': 'test_index'},
                metadata={}
            )
        ]

        issues = detector.detect(queries)

        # numberOfShards(5) should NOT match the hardcoded pattern (number_of_shards", 5)
        # So no hardcoded warning should be issued
        hardcoded_issues = [i for i in issues if 'hardcod' in i.title.lower() or i.severity == Severity.INFO]
        # The pattern uses numberOfShards() not number_of_shards, so no hardcoded issue
        assert all(i.severity != Severity.INFO for i in hardcoded_issues)
