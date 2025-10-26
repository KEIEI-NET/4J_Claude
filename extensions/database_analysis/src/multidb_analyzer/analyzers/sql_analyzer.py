"""
SQL Analyzer for MySQL and SQL Server

Extracts and analyzes SQL queries from Java/C#/Go/TypeScript source code
"""

import re
import sqlparse
from typing import List, Dict, Optional, Set
from pathlib import Path

from multidb_analyzer.models.database_models import (
    DatabaseQuery,
    QueryType,
    DatabaseType,
)


class CodeContext:
    """Context information about where code is located"""

    def __init__(
        self,
        file_path: str,
        line_number: int,
        is_in_loop: bool = False,
        method_name: Optional[str] = None,
        class_name: Optional[str] = None,
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.is_in_loop = is_in_loop
        self.method_name = method_name
        self.class_name = class_name


class SQLAnalyzer:
    """Analyzes SQL queries in source code"""

    def __init__(self, database: DatabaseType = DatabaseType.MYSQL):
        self.database = database
        self._known_tables: Set[str] = set()

    def analyze_file(self, file_path: str) -> List[DatabaseQuery]:
        """
        Extract and analyze all SQL queries in a file

        Args:
            file_path: Path to source code file

        Returns:
            List of DatabaseQuery objects
        """
        queries: List[DatabaseQuery] = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # First, extract concatenated SQL strings (Java/C#/etc)
        concatenated_queries = self._extract_concatenated_sql(content, file_path)
        queries.extend(concatenated_queries)

        # Pattern 1: String literals containing SQL
        sql_patterns = [
            r'"(SELECT|INSERT|UPDATE|DELETE)\s+.*?"',
            r"'(SELECT|INSERT|UPDATE|DELETE)\s+.*?'",
            r'"""(SELECT|INSERT|UPDATE|DELETE)\s+.*?"""',  # Python docstrings
        ]

        for pattern in sql_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                sql_text = match.group(0).strip('"').strip("'")
                line_number = content[: match.start()].count("\n") + 1

                # Skip if already captured
                if self._is_already_captured(sql_text, queries):
                    continue

                # Determine context
                context = self._determine_context(content, match.start(), file_path)

                # Analyze the query
                query_info = self._analyze_single_query(
                    sql_text, context, line_number
                )
                if query_info:
                    queries.append(query_info)

        # Pattern 2: MyBatis/Hibernate annotations
        annotation_queries = self._extract_annotation_queries(content, file_path)
        for ann_query in annotation_queries:
            # Skip if already captured
            if not self._is_already_captured(ann_query.query_text, queries):
                queries.append(ann_query)

        return queries

    def _extract_concatenated_sql(
        self, content: str, file_path: str
    ) -> List[DatabaseQuery]:
        """
        Extract SQL from concatenated strings (Java/C#/JavaScript style)

        Examples:
            String sql = "SELECT * FROM users " +
                       "WHERE id = ?";
        """
        queries = []

        # Pattern for string concatenation with +
        # Matches: "text" + "text" + ... across multiple lines
        concat_pattern = r'["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^"\']*)["\'](?:\s*\+\s*["\'][^"\']*["\'])*'

        for match in re.finditer(concat_pattern, content, re.IGNORECASE):
            full_match = match.group(0)
            line_number = content[: match.start()].count("\n") + 1

            # Extract all string parts
            string_parts = re.findall(r'["\']([^"\']+)["\']', full_match)

            # Concatenate them
            sql_text = " ".join(string_parts)

            # Only process if it looks like SQL
            sql_upper = sql_text.upper().strip()
            if not any(sql_upper.startswith(kw) for kw in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                continue

            # Determine context
            context = self._determine_context(content, match.start(), file_path)

            # Analyze the query
            query_info = self._analyze_single_query(sql_text, context, line_number)
            if query_info:
                queries.append(query_info)

        return queries

    def _is_already_captured(
        self, sql_text: str, existing_queries: List[DatabaseQuery]
    ) -> bool:
        """Check if this SQL fragment is already captured in existing queries"""
        sql_normalized = " ".join(sql_text.split()).upper()

        for query in existing_queries:
            query_normalized = " ".join(query.query_text.split()).upper()
            # If this SQL is a substring of an existing query, skip it
            if sql_normalized in query_normalized:
                return True

        return False

    def _determine_context(
        self, content: str, position: int, file_path: str
    ) -> CodeContext:
        """Determine the context of a code position"""
        # Find the line number
        line_number = content[:position].count("\n") + 1

        # Check if in a loop
        before_position = content[:position]
        is_in_loop = bool(
            re.search(r"\b(for|while|forEach|map|stream)\b", before_position[-500:])
        )

        # Try to find method and class names (simplified)
        method_match = re.search(
            r"(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)\s*{[^}]*$",
            before_position[-1000:],
        )
        method_name = method_match.group(1) if method_match else None

        class_match = re.search(
            r"(?:public|private)?\s+class\s+(\w+)", before_position[-2000:]
        )
        class_name = class_match.group(1) if class_match else None

        return CodeContext(
            file_path=file_path,
            line_number=line_number,
            is_in_loop=is_in_loop,
            method_name=method_name,
            class_name=class_name,
        )

    def _analyze_single_query(
        self, sql: str, context: CodeContext, line_number: int
    ) -> Optional[DatabaseQuery]:
        """
        Analyze a single SQL query in detail

        Args:
            sql: The SQL query text
            context: Code context information
            line_number: Line number in source file

        Returns:
            DatabaseQuery object or None if not a valid query
        """
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return None

            statement = parsed[0]

            # Determine query type
            query_type = self._get_query_type(statement)
            if not query_type:
                return None

            # Extract tables
            tables = self._extract_tables(statement)
            self._known_tables.update(tables)

            # Analyze WHERE clause
            where_clauses = self._analyze_where_clause(statement)

            # Detect JOINs
            joins = self._extract_joins(statement)

            # Estimate index usage
            has_index = self._estimate_index_usage(tables, where_clauses)

            # Calculate complexity
            complexity = self._calculate_complexity(statement, joins, where_clauses)

            # Detect N+1 pattern
            n_plus_one_risk = self._detect_n_plus_one_pattern(sql, context)

            # Check if prepared statement
            is_prepared = "?" in sql or ":param" in sql or "$1" in sql

            return DatabaseQuery(
                query_text=sql,
                query_type=query_type,
                database=self.database,
                file_path=context.file_path,
                line_number=line_number,
                method_name=context.method_name,
                class_name=context.class_name,
                is_prepared=is_prepared,
                has_parameters=is_prepared,
                is_in_loop=context.is_in_loop,
                complexity=complexity,
                has_index=has_index,
                n_plus_one_risk=n_plus_one_risk,
                missing_transaction=(
                    query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]
                ),
            )

        except Exception as e:
            # Log error but don't fail
            print(f"Error analyzing query: {e}")
            return None

    def _get_query_type(self, statement: sqlparse.sql.Statement) -> Optional[QueryType]:
        """Determine the type of SQL query"""
        first_token = statement.token_first(skip_ws=True, skip_cm=True)
        if not first_token:
            return None

        query_type_str = first_token.value.upper()

        type_mapping = {
            "SELECT": QueryType.SELECT,
            "INSERT": QueryType.INSERT,
            "UPDATE": QueryType.UPDATE,
            "DELETE": QueryType.DELETE,
        }

        return type_mapping.get(query_type_str)

    def _extract_tables(self, statement: sqlparse.sql.Statement) -> List[str]:
        """Extract table names from SQL statement"""
        tables = []

        # Find FROM clause
        from_seen = False
        for token in statement.tokens:
            if from_seen:
                if isinstance(token, sqlparse.sql.IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.append(identifier.get_name())
                elif isinstance(token, sqlparse.sql.Identifier):
                    tables.append(token.get_name())
                elif token.ttype is None:
                    # Could be a table name
                    table_name = str(token).strip()
                    if table_name and not table_name.upper() in [
                        "WHERE",
                        "JOIN",
                        "LEFT",
                        "RIGHT",
                        "INNER",
                        "OUTER",
                    ]:
                        tables.append(table_name)

            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "FROM":
                from_seen = True
            elif from_seen and token.ttype is sqlparse.tokens.Keyword:
                # Stop at next keyword
                if token.value.upper() in ["WHERE", "GROUP", "ORDER", "LIMIT"]:
                    break

        return [t.strip("`").strip('"').strip("'") for t in tables if t]

    def _analyze_where_clause(self, statement: sqlparse.sql.Statement) -> List[str]:
        """Extract WHERE clause conditions"""
        conditions = []

        where_seen = False
        for token in statement.tokens:
            if where_seen:
                if isinstance(token, sqlparse.sql.Where):
                    conditions.append(str(token).strip())
                elif token.ttype is sqlparse.tokens.Keyword:
                    break

            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "WHERE":
                where_seen = True

        return conditions

    def _extract_joins(self, statement: sqlparse.sql.Statement) -> List[str]:
        """Extract JOIN clauses"""
        joins = []

        for token in statement.tokens:
            if token.ttype is sqlparse.tokens.Keyword:
                if "JOIN" in token.value.upper():
                    joins.append(token.value)

        return joins

    def _estimate_index_usage(self, tables: List[str], where_clauses: List[str]) -> bool:
        """Estimate if query uses indexes (simplified)"""
        # If there are WHERE clauses on known tables, assume index usage
        # This is a simplification; real implementation would need schema info
        if tables and where_clauses:
            return True

        # SELECT without WHERE might do full table scan
        if tables and not where_clauses:
            return False

        return True

    def _calculate_complexity(
        self,
        statement: sqlparse.sql.Statement,
        joins: List[str],
        where_clauses: List[str],
    ) -> float:
        """Calculate query complexity score (1-10)"""
        complexity = 1.0

        # Add for JOINs
        complexity += len(joins) * 1.5

        # Add for WHERE conditions
        complexity += len(where_clauses) * 0.5

        # Add for subqueries
        subqueries = self._detect_subqueries(statement)
        complexity += len(subqueries) * 2.0

        return min(complexity, 10.0)

    def _detect_subqueries(self, statement: sqlparse.sql.Statement) -> List[str]:
        """Detect subqueries in SQL"""
        subqueries = []
        sql_str = str(statement)

        # Simple pattern matching for subqueries
        subquery_pattern = r"\(\s*SELECT\s+.*?\)"
        for match in re.finditer(subquery_pattern, sql_str, re.IGNORECASE | re.DOTALL):
            subqueries.append(match.group(0))

        return subqueries

    def _detect_n_plus_one_pattern(self, sql: str, context: CodeContext) -> bool:
        """
        Detect potential N+1 query problems

        N+1 happens when:
        1. Query is in a loop
        2. Query is a SELECT
        3. Query has parameters (likely filtering by ID from outer loop)
        """
        if not context.is_in_loop:
            return False

        if not sql.strip().upper().startswith("SELECT"):
            return False

        # Check for foreign key condition
        if self._has_foreign_key_condition(sql):
            return True

        return False

    def _has_foreign_key_condition(self, sql: str) -> bool:
        """Check if WHERE clause likely contains foreign key"""
        # Common foreign key patterns
        fk_patterns = [
            r"WHERE\s+\w+_id\s*=",
            r"WHERE\s+\w+Id\s*=",
            r"WHERE\s+id\s*=",
        ]

        for pattern in fk_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True

        return False

    def _extract_annotation_queries(
        self, content: str, file_path: str
    ) -> List[DatabaseQuery]:
        """Extract queries from Spring Data @Query annotations"""
        queries = []

        # Spring Data @Query pattern
        query_pattern = r'@Query\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'

        for match in re.finditer(query_pattern, content):
            sql_text = match.group(1)
            line_number = content[: match.start()].count("\n") + 1

            context = self._determine_context(content, match.start(), file_path)
            query_info = self._analyze_single_query(sql_text, context, line_number)

            if query_info:
                queries.append(query_info)

        return queries

    def add_known_table(self, table_name: str) -> None:
        """Add a table name to the known tables set"""
        self._known_tables.add(table_name)

    def get_known_tables(self) -> Set[str]:
        """Get all known table names"""
        return self._known_tables.copy()
