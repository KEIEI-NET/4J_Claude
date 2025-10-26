"""
Elasticsearch Analyzer

Analyzes Elasticsearch Query DSL and detects performance issues
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from multidb_analyzer.models.database_models import (
    DatabaseQuery,
    QueryType,
    DatabaseType,
)


class ElasticsearchAnalyzer:
    """Analyzes Elasticsearch queries in source code"""

    def __init__(self):
        self._known_indices: set = set()
        self._all_queries: List[DatabaseQuery] = []

    def analyze_file(self, file_path: str) -> List[DatabaseQuery]:
        """
        Extract and analyze Elasticsearch queries from a file

        Args:
            file_path: Path to source code file

        Returns:
            List of DatabaseQuery objects
        """
        queries: List[DatabaseQuery] = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Pattern 1: Extract JSON strings with brace counting
        queries.extend(self._extract_json_strings(content, file_path))

        # Pattern 2: Elasticsearch client search calls
        search_patterns = [
            r"client\.search\(\s*(\{.*?\})\s*\)",
            r"esClient\.search\(\s*(\{.*?\})\s*\)",
            r"\.search\(\s*index\s*=\s*['\"]([^'\"]+)['\"]\s*,\s*body\s*=\s*(\{.*?\})\s*\)",
        ]

        for pattern in search_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                try:
                    # Extract query DSL
                    query_dsl_str = match.group(1)
                    query_dsl = self._extract_query_dsl(query_dsl_str)

                    line_number = content[: match.start()].count("\n") + 1

                    # Analyze the query
                    query_info = self._analyze_es_query(
                        query_dsl, file_path, line_number
                    )

                    if query_info:
                        queries.append(query_info)
                        self._all_queries.append(query_info)

                except Exception as e:
                    # Log but continue
                    print(f"Error parsing Elasticsearch query: {e}")

        return queries

    def _extract_json_strings(self, content: str, file_path: str) -> List[DatabaseQuery]:
        """Extract JSON strings from content using brace counting"""
        queries = []
        i = 0

        while i < len(content):
            # Look for opening brace that might start a JSON object
            if content[i] == '{':
                # Count braces to find matching closing brace
                brace_count = 0
                json_end = i

                while json_end < len(content):
                    if content[json_end] == '{':
                        brace_count += 1
                    elif content[json_end] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    json_end += 1

                if brace_count == 0 and json_end < len(content):
                    # Extract the JSON string
                    json_str = content[i:json_end+1]

                    try:
                        # Try to parse as JSON
                        query_dsl = json.loads(json_str)

                        # Check if it looks like an ES query
                        if isinstance(query_dsl, dict) and any(key in query_dsl for key in ["query", "aggs", "aggregations"]):
                            line_number = content[:i].count("\n") + 1

                            # Analyze the query
                            query_info = self._analyze_es_query(
                                query_dsl, file_path, line_number
                            )

                            if query_info:
                                queries.append(query_info)
                                self._all_queries.append(query_info)

                    except (json.JSONDecodeError, Exception):
                        pass

                    i = json_end + 1
                    continue

            i += 1

        return queries

    def _extract_query_dsl(self, query_str: str) -> Dict[str, Any]:
        """Extract query DSL from string"""
        try:
            # Try to parse as JSON
            return json.loads(query_str)
        except json.JSONDecodeError:
            # Return a minimal dict if parsing fails
            return {"query": {"match_all": {}}}

    def _analyze_es_query(
        self, query_dsl: Dict[str, Any], file_path: str, line_number: int
    ) -> Optional[DatabaseQuery]:
        """
        Analyze an Elasticsearch query DSL

        Args:
            query_dsl: Query DSL dictionary
            file_path: Source file path
            line_number: Line number

        Returns:
            DatabaseQuery object
        """
        # Determine query type
        query_type = self._detect_query_type(query_dsl)

        # Calculate complexity
        complexity = self._calculate_es_complexity(query_dsl)

        # Detect script usage (performance concern)
        uses_script = self._detect_script_usage(query_dsl)

        # Detect wildcard queries (anti-pattern)
        has_wildcard = self._detect_wildcard_query(query_dsl)

        # Check for filters
        uses_filter = "filter" in json.dumps(query_dsl)

        # Check for aggregations
        has_aggregation = "aggs" in query_dsl or "aggregations" in query_dsl

        return DatabaseQuery(
            query_text=json.dumps(query_dsl, indent=2),
            query_type=QueryType.DSL,
            database=DatabaseType.ELASTICSEARCH,
            file_path=file_path,
            line_number=line_number,
            complexity=complexity,
            uses_script=uses_script,
            has_wildcard=has_wildcard,
            is_prepared=False,  # Elasticsearch doesn't use prepared statements
        )

    def _detect_query_type(self, query_dsl: Dict[str, Any]) -> str:
        """Detect the type of Elasticsearch query"""
        if "query" in query_dsl:
            query_obj = query_dsl["query"]

            if "match" in query_obj or "match_phrase" in query_obj:
                return "match"
            elif "term" in query_obj or "terms" in query_obj:
                return "term"
            elif "bool" in query_obj:
                return "bool"
            elif "wildcard" in query_obj:
                return "wildcard"
            elif "fuzzy" in query_obj:
                return "fuzzy"

        return "unknown"

    def _calculate_es_complexity(self, query_dsl: Dict[str, Any]) -> float:
        """
        Calculate Elasticsearch query complexity (1-10)

        Factors:
        - Number of nested levels
        - Number of clauses
        - Use of aggregations
        - Use of scripts
        """
        complexity = 1.0

        # Count nesting depth
        depth = self._calculate_depth(query_dsl)
        complexity += depth * 1.0

        # Count bool clauses
        if "query" in query_dsl and "bool" in query_dsl["query"]:
            bool_obj = query_dsl["query"]["bool"]
            clause_count = 0
            for clause_type in ["must", "should", "must_not", "filter"]:
                if clause_type in bool_obj:
                    clause_count += len(bool_obj[clause_type]) if isinstance(bool_obj[clause_type], list) else 1

            complexity += clause_count * 0.5

        # Aggregations add complexity
        if "aggs" in query_dsl or "aggregations" in query_dsl:
            aggs = query_dsl.get("aggs") or query_dsl.get("aggregations", {})
            complexity += len(aggs) * 1.5

        # Script usage
        if self._detect_script_usage(query_dsl):
            complexity += 2.0

        return min(complexity, 10.0)

    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate nesting depth of a dict/list structure"""
        if not isinstance(obj, (dict, list)):
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._calculate_depth(v, current_depth + 1) for v in obj.values()
            )

        if isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._calculate_depth(item, current_depth + 1) for item in obj
            )

        return current_depth

    def _detect_script_usage(self, query_dsl: Dict[str, Any]) -> bool:
        """Detect if query uses scripting"""
        query_str = json.dumps(query_dsl)
        return "script" in query_str

    def _detect_wildcard_query(self, query_dsl: Dict[str, Any]) -> bool:
        """Detect wildcard queries (potential performance issue)"""
        query_str = json.dumps(query_dsl)
        return "wildcard" in query_str or "*" in query_str

    def assess_performance_risk(self, query_dsl: Dict[str, Any]) -> str:
        """
        Assess performance risk of the query

        Returns:
            Risk level: high|medium|low
        """
        complexity = self._calculate_es_complexity(query_dsl)
        uses_script = self._detect_script_usage(query_dsl)
        has_wildcard = self._detect_wildcard_query(query_dsl)

        if uses_script or has_wildcard:
            return "high"
        elif complexity > 7.0:
            return "high"
        elif complexity > 4.0:
            return "medium"
        else:
            return "low"

    def find_complex_queries(self, min_complexity: float = 5.0) -> List[DatabaseQuery]:
        """Find queries with complexity above threshold"""
        return [q for q in self._all_queries if q.complexity >= min_complexity]

    def add_known_index(self, index_name: str) -> None:
        """Add an index name to the known indices set"""
        self._known_indices.add(index_name)

    def get_known_indices(self) -> set:
        """Get all known index names"""
        return self._known_indices.copy()
