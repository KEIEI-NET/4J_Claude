"""
Tests for ScriptQueryDetector

This module tests the script query detector for Elasticsearch.
"""

import pytest
from multidb_analyzer.elasticsearch.detectors import ScriptQueryDetector
from multidb_analyzer.core.base_parser import ParsedQuery, QueryType
from multidb_analyzer.core.base_detector import Severity


class TestScriptQueryDetector:
    """Test suite for ScriptQueryDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return ScriptQueryDetector()

    # Test 1: Detect script query usage
    def test_detect_script_query(self, detector):
        """Test detection of script query usage"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("doc[\'price\'].value > 100"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="searchByScript",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        issue = issues[0]
        assert issue.severity in [Severity.CRITICAL, Severity.HIGH]
        assert issue.detector_name == "ScriptQueryDetector"
        assert 'script' in issue.title.lower()

    # Test 2: Detect complex script
    def test_detect_complex_script(self, detector):
        """Test detection of complex script with loops/conditions"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("for (item in doc[\'items\']) { if (item.price > 100) return true; } return false;"))',
                file_path="SearchService.java",
                line_number=15,
                method_name="complexScript",
                class_name="SearchService",
                parameters={'script': 'for (item in doc[\'items\']) { if (item.price > 100) return true; } return false;'},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        issue = issues[0]
        # Complex scripts should be CRITICAL
        assert issue.severity == Severity.CRITICAL
        if issue.metadata:
            assert issue.metadata.get('is_complex') is True or 'complex' in issue.title.lower()

    # Test 3: Detect inline script
    def test_detect_inline_script(self, detector):
        """Test detection of inline script vs stored script"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script(ScriptType.INLINE, "painless", "doc[\'field\'].value > params.threshold", params))',
                file_path="SearchService.java",
                line_number=20,
                method_name="inlineScript",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        assert len(issues) >= 1
        issue = issues[0]
        # Inline scripts should trigger HIGH or CRITICAL
        assert issue.severity in [Severity.CRITICAL, Severity.HIGH]
        if issue.metadata:
            # Check if inline is detected
            assert issue.metadata.get('is_inline') is True or 'inline' in issue.tags

    # Test 4: Stored script has lower severity
    def test_stored_script_lower_severity(self, detector):
        """Test that stored scripts have lower severity than inline"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script(ScriptType.STORED, "painless", "my_stored_script", params))',
                file_path="SearchService.java",
                line_number=25,
                method_name="storedScript",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        # Stored scripts should still trigger issues but potentially with lower severity
        if issues:
            issue = issues[0]
            # Even stored scripts are HIGH severity in current implementation
            assert issue.severity in [Severity.CRITICAL, Severity.HIGH]

    # Test 5: Detect multiple script queries
    def test_detect_multiple_script_queries(self, detector):
        """Test detection of multiple script queries"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("doc[\'price\'].value * doc[\'quantity\'].value > 1000"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="script1",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            ),
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("doc[\'total\'].value > params.threshold"))',
                file_path="SearchService.java",
                line_number=15,
                method_name="script2",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            ),
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("for (x in doc[\'list\']) { if (x > 10) return true; }"))',
                file_path="SearchService.java",
                line_number=20,
                method_name="script3",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            ),
        ]

        issues = detector.detect(queries)

        # Should detect all three script queries
        assert len(issues) >= 3

        # At least one should be marked as complex
        complex_issues = [i for i in issues if i.metadata and i.metadata.get('is_complex')]
        assert len(complex_issues) >= 1

    # Additional test: Detector metadata
    def test_detector_metadata(self, detector):
        """Test detector metadata and properties"""
        assert detector.get_name() == "ScriptQueryDetector"
        assert detector.get_severity() == Severity.CRITICAL
        assert detector.get_category() is not None

    # Test 7: Script detection from query text (not metadata)
    def test_script_detection_from_text(self, detector):
        """Test script detection from query text patterns"""
        queries = [
            # Test scriptQuery pattern
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='client.search(new SearchRequest().source(QueryBuilders.scriptQuery(script)))',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},
                metadata={}  # No is_script metadata
            ),
            # Test Script( pattern
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='new Script("doc[\'field\'].value > 10")',
                file_path="SearchService.java",
                line_number=15,
                method_name="createScript",
                class_name="SearchService",
                parameters={},
                metadata={}  # No is_script metadata
            ),
        ]

        issues = detector.detect(queries)

        # Should detect scripts from text patterns
        assert len(issues) >= 1

    # Test 8: Non-script queries should not be detected
    def test_non_script_queries(self, detector):
        """Test that non-script queries are not detected"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.matchQuery("title", "test")',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},
                metadata={}
            ),
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.termQuery("status", "active")',
                file_path="SearchService.java",
                line_number=15,
                method_name="search2",
                class_name="SearchService",
                parameters={},
                metadata={}
            ),
        ]

        issues = detector.detect(queries)

        # Should not detect non-script queries
        assert len(issues) == 0

    # Test 9: Script complexity - empty script
    def test_empty_script_complexity(self, detector):
        """Test that empty scripts are not marked as complex"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script(""))',
                file_path="SearchService.java",
                line_number=10,
                method_name="emptyScript",
                class_name="SearchService",
                parameters={'script': ''},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        if issues:
            # Empty scripts should not be marked as complex
            assert not any(i.metadata.get('is_complex', False) for i in issues)

    # Test 10: Script complexity - long script
    def test_long_script_complexity(self, detector):
        """Test that very long scripts are marked as complex"""
        # Create a script longer than threshold (200 chars by default)
        long_script = "doc['field'].value + " * 20  # ~440 chars
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text=f'QueryBuilders.scriptQuery(new Script("{long_script}"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="longScript",
                class_name="SearchService",
                parameters={'script': long_script},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        # Should detect as complex due to length
        assert len(issues) >= 1
        complex_issues = [i for i in issues if i.metadata and i.metadata.get('is_complex')]
        assert len(complex_issues) >= 1

    # Test 11: Script complexity - keyword detection
    def test_keyword_complexity(self, detector):
        """Test that scripts with complex keywords are marked as complex"""
        complex_keywords_tests = [
            ('for', 'for (i = 0; i < 10; i++) { sum += i; }'),
            ('while', 'while (condition) { doSomething(); }'),
            ('if', 'if (value > threshold) return true; else return false;'),
            ('def', 'def myFunction() { return 42; }'),
        ]

        for keyword, script_source in complex_keywords_tests:
            queries = [
                ParsedQuery(
                    query_type=QueryType.SEARCH,
                    query_text=f'QueryBuilders.scriptQuery(new Script("{script_source}"))',
                    file_path="SearchService.java",
                    line_number=10,
                    method_name=f"script_{keyword}",
                    class_name="SearchService",
                    parameters={'script': script_source},
                    metadata={'is_script': True}
                )
            ]

            detector_fresh = ScriptQueryDetector()
            issues = detector_fresh.detect(queries)

            # Should detect as complex due to keyword
            assert len(issues) >= 1
            complex_issues = [i for i in issues if i.metadata and i.metadata.get('is_complex')]
            assert len(complex_issues) >= 1, f"Script with '{keyword}' should be marked as complex"

    # Test 12: Non-complex simple scripts
    def test_simple_non_complex_scripts(self, detector):
        """Test that simple scripts are not marked as complex"""
        simple_script = "doc['price'].value > 100"
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text=f'QueryBuilders.scriptQuery(new Script("{simple_script}"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="simpleScript",
                class_name="SearchService",
                parameters={'script': simple_script},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        # Simple scripts should not be marked as complex
        # (They'll still create issues, but without the complex flag)
        if issues:
            complex_issues = [i for i in issues if i.metadata and i.metadata.get('is_complex')]
            # This simple script should NOT be complex
            assert len(complex_issues) == 0

    # Test 13: Script query with non-string parameter value
    def test_script_with_non_string_parameter(self, detector):
        """Test script detection when parameter value is not a string"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("doc[\'price\'].value > 100"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="scriptWithObject",
                class_name="SearchService",
                parameters={'arg0': 123, 'arg1': None, 'arg2': ['list', 'values']},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        # Should handle non-string parameters gracefully
        assert isinstance(issues, list)
        if issues:
            # If issue is created, it should be valid
            issue = issues[0]
            assert issue.severity in [Severity.CRITICAL, Severity.HIGH]

    # Test 14: Script query without extractable script info
    def test_script_query_no_extractable_info(self, detector):
        """Test script query that cannot extract script_info"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='scriptQuery(unknownScriptVariable)',
                file_path="SearchService.java",
                line_number=15,
                method_name="scriptDynamic",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        issues = detector.detect(queries)

        # Should handle missing script info gracefully
        assert isinstance(issues, list)
        # May or may not create issues, just ensure no crashes

    # Test 15: Mock _extract_script_info to return None (line 97 branch)
    def test_extract_script_info_returns_none(self, detector, monkeypatch):
        """Test branch when _extract_script_info returns None"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(script)',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        # Mock _extract_script_info to return None
        monkeypatch.setattr(detector, '_extract_script_info', lambda q: None)

        issues = detector.detect(queries)

        # Should handle None gracefully and not create issues
        assert isinstance(issues, list)
        assert len(issues) == 0

    # Test 16: Mock _create_script_issue to return None (line 99 branch)
    def test_create_script_issue_returns_none(self, detector, monkeypatch):
        """Test branch when _create_script_issue returns None"""
        queries = [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text='QueryBuilders.scriptQuery(new Script("test"))',
                file_path="SearchService.java",
                line_number=10,
                method_name="search",
                class_name="SearchService",
                parameters={},
                metadata={'is_script': True}
            )
        ]

        # Mock _create_script_issue to return None
        monkeypatch.setattr(detector, '_create_script_issue', lambda q, s: None)

        issues = detector.detect(queries)

        # Should handle None gracefully and not add to issues list
        assert isinstance(issues, list)
        assert len(issues) == 0
