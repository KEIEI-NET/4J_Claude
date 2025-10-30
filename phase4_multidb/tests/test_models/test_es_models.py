"""
Tests for Elasticsearch Models

This module tests the Elasticsearch data models.
"""

import pytest
from multidb_analyzer.elasticsearch.models.es_models import (
    WildcardPattern,
    ScriptQuery,
    MappingIssue,
    ShardConfiguration
)


class TestWildcardPattern:
    """Test suite for WildcardPattern model"""

    def test_wildcard_pattern_basic(self):
        """Test basic WildcardPattern creation"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="*test*",
            starts_with_wildcard=True,
            ends_with_wildcard=True,
            contains_wildcard=True
        )

        assert pattern.field_name == "name"
        assert pattern.pattern == "*test*"
        assert pattern.starts_with_wildcard is True
        assert pattern.ends_with_wildcard is True
        assert pattern.contains_wildcard is True

    def test_wildcard_pattern_leading_only(self):
        """Test WildcardPattern with leading wildcard only"""
        pattern = WildcardPattern(
            field_name="email",
            pattern="*@example.com",
            starts_with_wildcard=True,
            ends_with_wildcard=False,
            contains_wildcard=True
        )

        assert pattern.starts_with_wildcard is True
        assert pattern.ends_with_wildcard is False
        assert pattern.contains_wildcard is True

    def test_wildcard_pattern_trailing_only(self):
        """Test WildcardPattern with trailing wildcard only"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="test*",
            starts_with_wildcard=False,
            ends_with_wildcard=True,
            contains_wildcard=True
        )

        assert pattern.starts_with_wildcard is False
        assert pattern.ends_with_wildcard is True
        assert pattern.contains_wildcard is True

    def test_wildcard_pattern_no_wildcard(self):
        """Test WildcardPattern without wildcards"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="test"
        )

        assert pattern.starts_with_wildcard is False
        assert pattern.ends_with_wildcard is False
        assert pattern.contains_wildcard is False

    def test_is_problematic_with_leading_wildcard(self):
        """Test is_problematic returns True for leading wildcard"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="*test",
            starts_with_wildcard=True
        )

        assert pattern.is_problematic() is True

    def test_is_problematic_without_leading_wildcard(self):
        """Test is_problematic returns False without leading wildcard"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="test*",
            starts_with_wildcard=False
        )

        assert pattern.is_problematic() is False

    def test_get_severity_high_with_leading_wildcard(self):
        """Test get_severity returns HIGH for leading wildcard"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="*test",
            starts_with_wildcard=True
        )

        assert pattern.get_severity() == "HIGH"

    def test_get_severity_medium_with_wildcard_no_leading(self):
        """Test get_severity returns MEDIUM for wildcard without leading"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="test*end",
            starts_with_wildcard=False,
            contains_wildcard=True
        )

        assert pattern.get_severity() == "MEDIUM"

    def test_get_severity_low_without_wildcard(self):
        """Test get_severity returns LOW without any wildcard"""
        pattern = WildcardPattern(
            field_name="name",
            pattern="test",
            starts_with_wildcard=False,
            contains_wildcard=False
        )

        assert pattern.get_severity() == "LOW"


class TestScriptQuery:
    """Test suite for ScriptQuery model"""

    def test_script_query_basic(self):
        """Test basic ScriptQuery creation"""
        query = ScriptQuery(
            script_lang="painless",
            script_source="doc['price'].value > 100"
        )

        assert query.script_lang == "painless"
        assert query.script_source == "doc['price'].value > 100"
        assert query.is_inline is True

    def test_script_query_complex_with_loop(self):
        """Test is_complex returns True for script with loop"""
        query = ScriptQuery(
            script_source="for (item in doc['items']) { if (item > 10) return true; }"
        )

        assert query.is_complex() is True

    def test_script_query_complex_with_if(self):
        """Test is_complex returns True for script with if"""
        query = ScriptQuery(
            script_source="if (value > threshold) return true; else return false;"
        )

        assert query.is_complex() is True

    def test_script_query_complex_with_long_source(self):
        """Test is_complex returns True for long script"""
        long_script = "doc['field'].value + " * 20  # > 100 chars
        query = ScriptQuery(
            script_source=long_script
        )

        assert query.is_complex() is True

    def test_script_query_not_complex(self):
        """Test is_complex returns False for simple script"""
        query = ScriptQuery(
            script_source="doc['price'].value > 100"
        )

        assert query.is_complex() is False

    def test_script_query_no_source(self):
        """Test is_complex returns False when no script source"""
        query = ScriptQuery(
            script_source=None
        )

        assert query.is_complex() is False


class TestMappingIssue:
    """Test suite for MappingIssue model"""

    def test_mapping_issue_basic(self):
        """Test basic MappingIssue creation"""
        issue = MappingIssue(
            index_name="products",
            field_name="price",
            issue_type="wrong_type",
            expected_type="float",
            actual_type="text",
            suggestion="Change mapping to float"
        )

        assert issue.index_name == "products"
        assert issue.field_name == "price"
        assert issue.issue_type == "wrong_type"
        assert issue.expected_type == "float"
        assert issue.actual_type == "text"


class TestShardConfiguration:
    """Test suite for ShardConfiguration model"""

    def test_shard_configuration_basic(self):
        """Test basic ShardConfiguration creation"""
        config = ShardConfiguration(
            index_name="logs",
            shard_count=5,
            replica_count=1,
            index_size_gb=100.0
        )

        assert config.index_name == "logs"
        assert config.shard_count == 5
        assert config.replica_count == 1
        assert config.index_size_gb == 100.0

    def test_is_over_sharded_by_size(self):
        """Test is_over_sharded returns True when shards are too small"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=20,
            replica_count=1,
            index_size_gb=50.0  # 50GB / 20 shards = 2.5GB per shard < 10GB
        )

        assert config.is_over_sharded() is True

    def test_is_over_sharded_by_document_count(self):
        """Test is_over_sharded returns True when documents per shard is too low"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=10,
            replica_count=1,
            document_count=5_000_000  # 5M / 10 shards = 500k per shard < 1M
        )

        assert config.is_over_sharded() is True

    def test_is_not_over_sharded(self):
        """Test is_over_sharded returns False for good configuration"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=5,
            replica_count=1,
            index_size_gb=100.0  # 100GB / 5 shards = 20GB per shard (good)
        )

        assert config.is_over_sharded() is False

    def test_is_under_sharded(self):
        """Test is_under_sharded returns True when shards are too large"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=2,
            replica_count=1,
            index_size_gb=200.0  # 200GB / 2 shards = 100GB per shard > 50GB
        )

        assert config.is_under_sharded() is True

    def test_is_not_under_sharded(self):
        """Test is_under_sharded returns False for good configuration"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=5,
            replica_count=1,
            index_size_gb=100.0  # 100GB / 5 shards = 20GB per shard (good)
        )

        assert config.is_under_sharded() is False

    def test_no_size_data(self):
        """Test shard checks return False when no size data"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=5,
            replica_count=1
        )

        assert config.is_over_sharded() is False
        assert config.is_under_sharded() is False

    def test_is_not_over_sharded_with_enough_docs_per_shard(self):
        """Test is_over_sharded returns False when documents per shard is sufficient"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=10,
            replica_count=1,
            document_count=15_000_000  # 15M / 10 shards = 1.5M per shard >= 1M
        )

        assert config.is_over_sharded() is False

    def test_get_recommended_shard_count_no_size(self):
        """Test get_recommended_shard_count returns None when no size data"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=5,
            replica_count=1
        )

        assert config.get_recommended_shard_count() is None

    def test_get_recommended_shard_count_small_index(self):
        """Test get_recommended_shard_count for small index"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=5,
            replica_count=1,
            index_size_gb=20.0  # 20GB -> recommends max(1, 20/30) = 1 shard
        )

        assert config.get_recommended_shard_count() == 1

    def test_get_recommended_shard_count_medium_index(self):
        """Test get_recommended_shard_count for medium index"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=10,
            replica_count=1,
            index_size_gb=150.0  # 150GB -> recommends 150/30 = 5 shards
        )

        assert config.get_recommended_shard_count() == 5

    def test_get_recommended_shard_count_large_index(self):
        """Test get_recommended_shard_count for large index"""
        config = ShardConfiguration(
            index_name="test",
            shard_count=3,
            replica_count=1,
            index_size_gb=300.0  # 300GB -> recommends 300/30 = 10 shards
        )

        assert config.get_recommended_shard_count() == 10
