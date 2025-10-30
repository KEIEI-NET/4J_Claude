"""
Pytest configuration and shared fixtures for multidb_analyzer tests

This module provides common fixtures and utilities for testing the
multi-database analyzer framework.
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from multidb_analyzer.core.base_parser import ParsedQuery, QueryType, DatabaseType
from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory


# Sample Java code snippets for testing
SAMPLE_JAVA_WILDCARD_LEADING = '''
package com.example.search;

import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.index.query.QueryBuilders;

public class SearchService {
    public void searchByName(String name) {
        QueryBuilders.wildcardQuery("name", "*smith");
    }
}
'''

SAMPLE_JAVA_WILDCARD_TRAILING = '''
package com.example.search;

import org.elasticsearch.index.query.QueryBuilders;

public class SearchService {
    public void searchByPrefix(String prefix) {
        QueryBuilders.wildcardQuery("name", "smith*");
    }
}
'''

SAMPLE_JAVA_SCRIPT_QUERY = '''
package com.example.search;

import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.script.Script;

public class SearchService {
    public void searchByScript() {
        QueryBuilders.scriptQuery(
            new Script("doc['price'].value * doc['quantity'].value > 1000")
        );
    }
}
'''

SAMPLE_JAVA_COMPLEX_SCRIPT = '''
package com.example.search;

import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.script.Script;

public class SearchService {
    public void complexScript() {
        QueryBuilders.scriptQuery(
            new Script("for (item in doc['items']) { if (item.price > 100) return true; } return false;")
        );
    }
}
'''

SAMPLE_JAVA_CREATE_INDEX = '''
package com.example.admin;

import org.elasticsearch.client.indices.CreateIndexRequest;
import org.elasticsearch.common.settings.Settings;

public class IndexManager {
    public void createIndex() {
        CreateIndexRequest request = new CreateIndexRequest("products")
            .settings(Settings.builder()
                .put("index.number_of_shards", 100)
                .put("index.number_of_replicas", 1)
            );
    }
}
'''

SAMPLE_JAVA_DYNAMIC_MAPPING = '''
package com.example.indexing;

import org.elasticsearch.action.index.IndexRequest;
import java.util.Map;

public class DocumentIndexer {
    public void indexDocument(Map<String, Object> jsonMap) {
        IndexRequest request = new IndexRequest("products")
            .source(jsonMap);
    }
}
'''


@pytest.fixture
def sample_java_wildcard_leading() -> str:
    """Sample Java code with leading wildcard"""
    return SAMPLE_JAVA_WILDCARD_LEADING


@pytest.fixture
def sample_java_wildcard_trailing() -> str:
    """Sample Java code with trailing wildcard"""
    return SAMPLE_JAVA_WILDCARD_TRAILING


@pytest.fixture
def sample_java_script_query() -> str:
    """Sample Java code with script query"""
    return SAMPLE_JAVA_SCRIPT_QUERY


@pytest.fixture
def sample_java_complex_script() -> str:
    """Sample Java code with complex script"""
    return SAMPLE_JAVA_COMPLEX_SCRIPT


@pytest.fixture
def sample_java_create_index() -> str:
    """Sample Java code with create index"""
    return SAMPLE_JAVA_CREATE_INDEX


@pytest.fixture
def sample_java_dynamic_mapping() -> str:
    """Sample Java code with dynamic mapping"""
    return SAMPLE_JAVA_DYNAMIC_MAPPING


@pytest.fixture
def temp_java_file(tmp_path: Path) -> Path:
    """Create a temporary Java file for testing"""
    def _create_file(content: str, filename: str = "TestClass.java") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    return _create_file


@pytest.fixture
def sample_parsed_query() -> ParsedQuery:
    """Create a sample ParsedQuery for testing"""
    return ParsedQuery(
        query_type=QueryType.SEARCH,
        query_text='QueryBuilders.wildcardQuery("name", "*smith")',
        file_path="SearchService.java",
        line_number=10,
        method_name="searchByName",
        class_name="SearchService",
        parameters={'arg0': 'name', 'arg1': '*smith'},
        metadata={'is_wildcard': True}
    )


@pytest.fixture
def sample_parsed_queries() -> List[ParsedQuery]:
    """Create multiple sample ParsedQuery objects for testing"""
    return [
        ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text='QueryBuilders.wildcardQuery("name", "*smith")',
            file_path="SearchService.java",
            line_number=10,
            method_name="searchByName",
            class_name="SearchService",
            parameters={'arg0': 'name', 'arg1': '*smith'},
            metadata={'is_wildcard': True}
        ),
        ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text='QueryBuilders.scriptQuery(new Script("doc[\'price\'].value > 100"))',
            file_path="SearchService.java",
            line_number=15,
            method_name="searchByPrice",
            class_name="SearchService",
            parameters={},
            metadata={'is_script': True}
        ),
    ]


@pytest.fixture
def sample_issue() -> Issue:
    """Create a sample Issue for testing"""
    return Issue(
        detector_name="TestDetector",
        severity=Severity.HIGH,
        category=IssueCategory.PERFORMANCE,
        title="Test issue",
        description="Test description",
        file_path="TestFile.java",
        line_number=10,
        query_text="test query",
        method_name="testMethod",
        class_name="TestClass",
        suggestion="Test suggestion",
        auto_fix_available=False,
        documentation_url="https://example.com",
        tags=['test'],
        metadata={}
    )


# Helper functions for testing
def assert_issue_has_required_fields(issue: Issue) -> None:
    """Assert that an Issue has all required fields"""
    assert issue.detector_name is not None
    assert issue.severity is not None
    assert issue.category is not None
    assert issue.title is not None
    assert issue.description is not None
    assert issue.file_path is not None
    assert issue.line_number is not None


def assert_parsed_query_has_required_fields(query: ParsedQuery) -> None:
    """Assert that a ParsedQuery has all required fields"""
    assert query.query_type is not None
    assert query.query_text is not None
    assert query.file_path is not None
    assert query.line_number is not None
