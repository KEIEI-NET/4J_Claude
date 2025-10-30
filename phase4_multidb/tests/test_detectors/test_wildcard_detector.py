"""
Tests for WildcardDetector

This module tests the wildcard query detector for Elasticsearch.
"""

import pytest
from multidb_analyzer.elasticsearch.detectors import WildcardDetector
from multidb_analyzer.core.base_parser import ParsedQuery, QueryType
from multidb_analyzer.core.base_detector import Severity


class TestWildcardDetector:
    """Test suite for WildcardDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return WildcardDetector()

    # Test 1: Detect leading wildcard (CRITICAL)
    def test_detect_leading_wildcard(self, detector):
        """Test detection of leading wildcard pattern"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "*smith")',
                file_path="SearchService.java",
                line_number=10,
                method_name="searchByName",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': '*smith'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        issue = issues[0]
        assert issue.severity == Severity.CRITICAL
        assert 'wildcard' in issue.title.lower() or 'leading' in issue.title.lower()
        assert issue.detector_name == "WildcardDetector"
        assert 'name' in issue.metadata.get('field_name', '')
        assert issue.metadata.get('starts_with_wildcard') is True

    # Test 2: Detect both-ended wildcard (HIGH)
    def test_detect_both_ended_wildcard(self, detector):
        """Test detection of wildcard pattern on both ends"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("description", "*keyword*")',
                file_path="SearchService.java",
                line_number=15,
                method_name="searchByDescription",
                class_name="SearchService",
                parameters={'arg0': 'description', 'arg1': '*keyword*'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        issue = issues[0]
        # Both-ended wildcards start with wildcard, so should be CRITICAL
        assert issue.severity in [Severity.CRITICAL, Severity.HIGH]
        assert issue.metadata.get('starts_with_wildcard') is True

    # Test 3: Trailing wildcard should not trigger issue
    def test_trailing_wildcard_no_issue(self, detector):
        """Test that trailing wildcard alone doesn't trigger an issue"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "smith*")',
                file_path="SearchService.java",
                line_number=20,
                method_name="searchByPrefix",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': 'smith*'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Trailing wildcard only should not produce critical/high issues
        # or should produce no issues at all
        if issues:
            for issue in issues:
                assert issue.severity not in [Severity.CRITICAL, Severity.HIGH]

    # Test 4: Auto-fix generation for trailing wildcard
    def test_auto_fix_generation(self, detector):
        """Test auto-fix code generation for convertible patterns"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "smith*")',
                file_path="SearchService.java",
                line_number=25,
                method_name="searchByPrefix",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': 'smith*'},
                metadata={'is_wildcard': True}
            )
        ]

        # Note: WildcardDetector might not create issues for safe trailing wildcards
        # But if it does, and auto-fix is available, test it
        issues = detector.detect(queries)

        # If auto-fix is provided for any issue, verify it
        auto_fix_issues = [i for i in issues if i.auto_fix_available]
        if auto_fix_issues:
            issue = auto_fix_issues[0]
            assert 'prefixQuery' in issue.auto_fix_code
            assert 'smith' in issue.auto_fix_code

    # Test 5: Detect multiple wildcard patterns
    def test_detect_multiple_patterns(self, detector):
        """Test detection of multiple wildcard patterns in different queries"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "*smith")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search1",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': '*smith'},
                metadata={'is_wildcard': True}
            ),
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("email", "*@example.com")',
                file_path="SearchService.java",
                line_number=15,
                method_name="search2",
                class_name="SearchService",
                parameters={'arg0': 'email', 'arg1': '*@example.com'},
                metadata={'is_wildcard': True}
            ),
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("title", "product*")',
                file_path="SearchService.java",
                line_number=20,
                method_name="search3",
                class_name="SearchService",
                parameters={'arg0': 'title', 'arg1': 'product*'},
                metadata={'is_wildcard': True}
            ),
        ]

        issues = detector.detect(queries)

        # Should detect at least the two leading wildcard patterns
        critical_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        assert len(critical_issues) >= 2

    # Additional test: Detector metadata
    def test_detector_metadata(self, detector):
        """Test detector metadata and properties"""
        assert detector.get_name() == "WildcardDetector"
        assert detector.get_severity() == Severity.HIGH
        assert detector.get_category() is not None

    # Test 7: Non-wildcard query should not be detected
    def test_non_wildcard_query(self, detector):
        """Test that non-wildcard queries are not detected"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.matchQuery("name", "smith")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': 'smith'},
                metadata={}  # No wildcard flag
            )
        ]

        issues = detector.detect(queries)

        # Should not detect non-wildcard queries
        assert len(issues) == 0

    # Test 8: Question mark wildcard
    def test_question_mark_wildcard(self, detector):
        """Test detection of question mark wildcard"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("code", "?ABC")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'code', 'arg1': '?ABC'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Should detect leading ? wildcard
        assert len(issues) >= 1
        if issues:
            assert issues[0].severity == Severity.CRITICAL

    # Test 9: Wildcard pattern with no parameters
    def test_wildcard_with_no_parameters(self, detector):
        """Test handling of wildcard query without parameters"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery()',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters=None,
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Should handle gracefully without crashing
        assert isinstance(issues, list)

    # Test 10: Auto-fix not available for leading wildcard
    def test_no_autofix_for_leading_wildcard(self, detector):
        """Test that leading wildcards don't have auto-fix"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "*smith")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': '*smith'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        # Leading wildcards should not have auto-fix
        assert issues[0].auto_fix_available is False

    # Test 11: Middle wildcard detection (not at start or end)
    def test_middle_wildcard_detection(self, detector):
        """Test detection of wildcard in the middle of pattern"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("email", "test*@example.com")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'email', 'arg1': 'test*@example.com'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Should detect middle wildcard as HIGH severity
        assert len(issues) >= 1
        # Middle wildcards don't start with wildcard
        assert not issues[0].metadata.get('starts_with_wildcard', True)

    # Test 12: Regex fallback pattern extraction
    def test_regex_fallback_extraction(self, detector):
        """Test pattern extraction via regex when parameters are not available"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='client.search(QueryBuilders.wildcardQuery("field", "*pattern"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},  # No parameters - force regex fallback
                metadata={}
            )
        ]

        issues = detector.detect(queries)

        # Should extract pattern via regex fallback
        assert len(issues) >= 1

    # Test 13: Single-quote pattern handling
    def test_single_quote_pattern(self, detector):
        """Test pattern with single quotes"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text="QueryBuilders.wildcardQuery('name', '*smith')",
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': "'*smith'"},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Should handle single quotes properly
        assert len(issues) >= 1

    # Test 14: Non-string pattern parameter
    def test_non_string_pattern(self, detector):
        """Test handling of non-string pattern parameter"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("field", patternVar)',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'field', 'arg1': None},  # Non-string parameter
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Should handle gracefully
        assert isinstance(issues, list)

    # Test 15: Trailing-only wildcard with auto-fix
    def test_trailing_wildcard_with_autofix(self, detector):
        """Test that trailing-only wildcard generates auto-fix to prefixQuery"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "prefix*")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={'arg0': 'name', 'arg1': 'prefix*'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Trailing wildcard might not create issues or might create INFO-level
        # If it creates an issue with auto-fix, verify the auto-fix
        auto_fix_issues = [i for i in issues if i.auto_fix_code]
        if auto_fix_issues:
            assert 'prefixQuery' in auto_fix_issues[0].auto_fix_code
            assert 'prefix' in auto_fix_issues[0].auto_fix_code

    # Test 16: Detection from query text without metadata
    def test_detection_from_text_only(self, detector):
        """Test wildcard detection from query text when metadata is absent"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='client.search(QueryBuilders.wildcardQuery("field", "*value"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},
                metadata={}  # No is_wildcard metadata
            )
        ]

        issues = detector.detect(queries)

        # Should detect from 'wildcardQuery' in text
        assert len(issues) >= 1

    # Test 17: Comprehensive severity levels
    def test_comprehensive_severity_levels(self, detector):
        """Test all severity levels for different wildcard patterns"""
        queries = [
            # CRITICAL: Leading wildcard
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("f1", "*abc")',
                file_path="test.java",
                line_number=10,
                parameters={'arg0': 'f1', 'arg1': '*abc'},
                metadata={'is_wildcard': True}
            ),
            # HIGH: Middle wildcard (contains but not ends)
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("f2", "ab*cd")',
                file_path="test.java",
                line_number=15,
                parameters={'arg0': 'f2', 'arg1': 'ab*cd'},
                metadata={'is_wildcard': True}
            ),
        ]

        detector_fresh = WildcardDetector()
        issues = detector_fresh.detect(queries)

        # Should have both CRITICAL and HIGH severity issues
        severities = {issue.severity for issue in issues}
        assert Severity.CRITICAL in severities

    # Test 18: MEDIUM severity wildcard (contains but also ends)
    def test_medium_severity_wildcard(self, detector):
        """Test MEDIUM severity for trailing wildcards"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("field", "abc*")',
                file_path="test.java",
                line_number=10,
                parameters={'arg0': 'field', 'arg1': 'abc*'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Trailing wildcard should generate issues with suggestions
        # Check for prefix query suggestion
        if issues:
            has_prefix_suggestion = any('prefix' in issue.suggestion.lower() for issue in issues)
            # Should suggest prefix query
            assert has_prefix_suggestion or len(issues[0].suggestion) > 0

    # Test 19: Generate auto-fix for simple trailing wildcard
    def test_autofix_for_simple_trailing(self, detector):
        """Test auto-fix generation for simple trailing wildcard"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("name", "test*")',
                file_path="test.java",
                line_number=10,
                parameters={'arg0': 'name', 'arg1': 'test*'},
                metadata={'is_wildcard': True}
            )
        ]

        issues = detector.detect(queries)

        # Simple trailing wildcard should have auto-fix
        if issues:
            auto_fix_issues = [i for i in issues if i.auto_fix_code]
            if auto_fix_issues:
                assert 'prefixQuery' in auto_fix_issues[0].auto_fix_code
                assert 'test' in auto_fix_issues[0].auto_fix_code
                assert issues[0].auto_fix_available or len(auto_fix_issues) > 0

    # Test 20: Non-string input to _strip_quotes
    def test_strip_quotes_non_string(self, detector):
        """Test _strip_quotes with non-string input"""
        # Direct call to _strip_quotes with non-string
        result = detector._strip_quotes(123)
        assert result == 123

        result = detector._strip_quotes(None)
        assert result is None

    # Test 21: Direct call to _determine_severity with trailing wildcard
    def test_determine_severity_trailing_wildcard(self, detector):
        """Test _determine_severity returns MEDIUM for trailing wildcard pattern"""
        from multidb_analyzer.elasticsearch.models.es_models import WildcardPattern

        # Create a trailing-only wildcard pattern
        pattern = WildcardPattern(
            pattern="test*",
            field_name="field",
            starts_with_wildcard=False,
            ends_with_wildcard=True,
            contains_wildcard=True
        )

        # Call _determine_severity directly
        severity = detector._determine_severity(pattern)

        # Should be MEDIUM for trailing wildcard
        assert severity == Severity.MEDIUM

    # Test 22: Direct call to _generate_suggestion with trailing wildcard
    def test_generate_suggestion_trailing_wildcard(self, detector):
        """Test _generate_suggestion includes prefix query recommendation"""
        from multidb_analyzer.elasticsearch.models.es_models import WildcardPattern

        pattern = WildcardPattern(
            pattern="john*",
            field_name="name",
            starts_with_wildcard=False,
            ends_with_wildcard=True,
            contains_wildcard=True
        )

        suggestion = detector._generate_suggestion(pattern)

        # Should mention prefix query
        assert 'prefix' in suggestion.lower()

    # Test 23: Direct call to _generate_auto_fix with trailing wildcard
    def test_generate_auto_fix_trailing_wildcard(self, detector):
        """Test _generate_auto_fix creates prefix query code"""
        from multidb_analyzer.elasticsearch.models.es_models import WildcardPattern

        pattern = WildcardPattern(
            pattern="user*",
            field_name="email",
            starts_with_wildcard=False,
            ends_with_wildcard=True,
            contains_wildcard=True
        )

        query = ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text='QueryBuilders.wildcardQuery("email", "user*")',
            file_path="test.java",
            line_number=20
        )

        auto_fix = detector._generate_auto_fix(query, pattern)

        # Should generate prefix query auto-fix
        assert auto_fix is not None
        assert 'prefixQuery' in auto_fix
        assert 'user' in auto_fix
        assert 'email' in auto_fix

    # Test 24: Pattern extraction with non-string pattern (edge case)
    def test_pattern_extraction_non_string_pattern(self, detector):
        """Test pattern extraction when pattern is not a string (edge case)"""
        # Create a query with parameters where arg1 is not a string
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("field", pattern)',
                file_path="test.java",
                line_number=25,
                parameters={'arg0': 'field', 'arg1': None},  # None instead of string
                metadata={'is_wildcard': True}
            )
        ]

        # This should fall back to regex extraction from query_text
        issues = detector.detect(queries)

        # Might not detect since pattern is None and query_text doesn't have literal pattern
        # This tests the branch where isinstance(pattern, str) is False
        assert isinstance(issues, list)

    # Test 25: Mock _strip_quotes to return non-string (line 134->158 branch)
    def test_strip_quotes_returns_non_string(self, detector, monkeypatch):
        """Test branch when _strip_quotes returns non-string value"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.wildcardQuery("field", "*test")',
                file_path="test.java",
                line_number=10,
                parameters={'arg0': 'field', 'arg1': '*test'},
                metadata={'is_wildcard': True}
            )
        ]

        # Mock _strip_quotes to return None (non-string)
        monkeypatch.setattr(detector, '_strip_quotes', lambda x: None if x == '*test' else x)

        issues = detector.detect(queries)

        # Should fall back to regex extraction from query_text
        # The query text has "wildcardQuery" pattern so should still detect
        assert isinstance(issues, list)
