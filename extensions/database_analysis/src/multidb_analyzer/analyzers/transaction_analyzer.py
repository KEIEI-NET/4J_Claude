"""
Transaction Analyzer

Analyzes transaction boundaries in source code
"""

import re
import javalang
from typing import List, Optional, Set, Tuple
from pathlib import Path

from multidb_analyzer.models.database_models import (
    TransactionBoundary,
    DatabaseQuery,
    QueryType,
)


class TransactionAnalyzer:
    """Analyzes transaction boundaries in source code"""

    def __init__(self):
        self._transaction_methods: Set[str] = set()

    def analyze_file(self, file_path: str) -> List[TransactionBoundary]:
        """
        Extract transaction boundaries from a file

        Args:
            file_path: Path to source code file

        Returns:
            List of TransactionBoundary objects
        """
        transactions: List[TransactionBoundary] = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Pattern 1: Spring @Transactional annotation
        spring_tx = self._detect_spring_transactional(content, file_path)
        transactions.extend(spring_tx)

        # Pattern 2: Programmatic transactions
        programmatic_tx = self._detect_programmatic_tx(content, file_path)
        transactions.extend(programmatic_tx)

        # Pattern 3: JPA EntityManager transaction
        jpa_tx = self._detect_jpa_transactions(content, file_path)
        transactions.extend(jpa_tx)

        return transactions

    def _detect_spring_transactional(
        self, content: str, file_path: str
    ) -> List[TransactionBoundary]:
        """Detect Spring @Transactional annotations"""
        transactions = []

        # Pattern: @Transactional(isolation = ..., propagation = ...)
        transactional_pattern = r'@Transactional\s*(?:\([^)]*\))?\s*\n\s*(?:public|private|protected)?\s+\w+\s+(\w+)\s*\('

        for match in re.finditer(transactional_pattern, content):
            method_name = match.group(1)
            line_number = content[: match.start()].count("\n") + 1

            # Extract transaction properties
            annotation_text = content[match.start() : match.end()]
            isolation_level = self._extract_isolation_level(annotation_text)
            timeout = self._extract_timeout(annotation_text)

            transaction = TransactionBoundary(
                type="begin",
                file_path=file_path,
                line_number=line_number,
                method_id=f"{file_path}:{method_name}",
                isolation_level=isolation_level,
                timeout=timeout,
            )

            transactions.append(transaction)
            self._transaction_methods.add(method_name)

        return transactions

    def _detect_programmatic_tx(
        self, content: str, file_path: str
    ) -> List[TransactionBoundary]:
        """Detect programmatic transaction management"""
        transactions = []

        # Pattern: transaction.begin(), session.beginTransaction(), etc.
        begin_patterns = [
            r"(\w+)\.begin(?:Transaction)?\s*\(\s*\)",
            r"getTransaction\s*\(\s*\)\.begin\s*\(\s*\)",
        ]

        for pattern in begin_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[: match.start()].count("\n") + 1
                method_name = self._find_containing_method(content, match.start())

                transaction = TransactionBoundary(
                    type="begin",
                    file_path=file_path,
                    line_number=line_number,
                    method_id=f"{file_path}:{method_name}",
                    is_distributed=False,
                )

                transactions.append(transaction)

        # Pattern: transaction.commit()
        commit_pattern = r"(\w+)\.commit\s*\(\s*\)"
        for match in re.finditer(commit_pattern, content):
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_containing_method(content, match.start())

            transaction = TransactionBoundary(
                type="commit",
                file_path=file_path,
                line_number=line_number,
                method_id=f"{file_path}:{method_name}",
            )

            transactions.append(transaction)

        # Pattern: transaction.rollback()
        rollback_pattern = r"(\w+)\.rollback\s*\(\s*\)"
        for match in re.finditer(rollback_pattern, content):
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_containing_method(content, match.start())

            transaction = TransactionBoundary(
                type="rollback",
                file_path=file_path,
                line_number=line_number,
                method_id=f"{file_path}:{method_name}",
            )

            transactions.append(transaction)

        return transactions

    def _detect_jpa_transactions(
        self, content: str, file_path: str
    ) -> List[TransactionBoundary]:
        """Detect JPA EntityManager transactions"""
        transactions = []

        # Pattern: entityManager.getTransaction().begin()
        jpa_begin_pattern = r"entityManager\.getTransaction\s*\(\s*\)\.begin\s*\(\s*\)"

        for match in re.finditer(jpa_begin_pattern, content):
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_containing_method(content, match.start())

            transaction = TransactionBoundary(
                type="begin",
                file_path=file_path,
                line_number=line_number,
                method_id=f"{file_path}:{method_name}",
            )

            transactions.append(transaction)

        return transactions

    def _extract_isolation_level(self, annotation_text: str) -> Optional[str]:
        """Extract isolation level from @Transactional annotation"""
        isolation_pattern = r"isolation\s*=\s*Isolation\.(\w+)"
        match = re.search(isolation_pattern, annotation_text)

        if match:
            return match.group(1)

        return None

    def _extract_timeout(self, annotation_text: str) -> Optional[int]:
        """Extract timeout from @Transactional annotation"""
        timeout_pattern = r"timeout\s*=\s*(\d+)"
        match = re.search(timeout_pattern, annotation_text)

        if match:
            return int(match.group(1))

        return None

    def _find_containing_method(self, content: str, position: int) -> str:
        """Find the method name containing a position"""
        before_position = content[:position]

        method_patterns = [
            r"(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)\s*{[^}]*$",
            r"def\s+(\w+)\s*\([^)]*\):",  # Python
            r"func\s+(\w+)\s*\([^)]*\)",  # Go
        ]

        for pattern in method_patterns:
            match = re.search(pattern, before_position[-1500:])
            if match:
                return match.group(1)

        return "unknown_method"

    def find_queries_in_transaction(
        self,
        transaction: TransactionBoundary,
        all_queries: List[DatabaseQuery],
    ) -> List[DatabaseQuery]:
        """
        Find all queries within a transaction boundary

        Args:
            transaction: Transaction boundary
            all_queries: List of all database queries

        Returns:
            List of queries within the transaction
        """
        queries_in_tx = []

        for query in all_queries:
            # Check if query is in the same file and method
            if (
                query.file_path == transaction.file_path
                and query.method_name in transaction.method_id
            ):
                queries_in_tx.append(query)

        return queries_in_tx

    def check_distributed_tx(
        self, queries: List[DatabaseQuery]
    ) -> Tuple[bool, int]:
        """
        Check if queries span multiple databases (distributed transaction)

        Args:
            queries: List of database queries

        Returns:
            Tuple of (is_distributed, database_count)
        """
        databases = set(q.database for q in queries)
        database_count = len(databases)

        is_distributed = database_count > 1

        return is_distributed, database_count

    def assess_deadlock_risk(self, queries: List[DatabaseQuery]) -> str:
        """
        Assess deadlock risk based on queries in transaction

        Args:
            queries: List of queries in transaction

        Returns:
            Risk level: high|medium|low
        """
        # Count write operations
        write_queries = [
            q
            for q in queries
            if q.query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]
        ]

        if len(write_queries) == 0:
            return "low"

        # Multiple writes to different tables = higher risk
        write_tables = set()
        for query in write_queries:
            # Extract table names from query text
            table_name = self._extract_table_name(query.query_text, query.query_type)
            if table_name:
                write_tables.add(table_name)

        if len(write_tables) > 3:
            return "high"
        elif len(write_tables) > 1:
            return "medium"
        else:
            return "low"

    def _extract_table_name(self, query_text: str, query_type: QueryType) -> Optional[str]:
        """Extract table name from SQL query"""
        import re

        query_upper = query_text.upper()

        if query_type == QueryType.INSERT:
            # INSERT INTO table_name
            match = re.search(r'INSERT\s+INTO\s+(\w+)', query_upper)
            if match:
                return match.group(1).lower()

        elif query_type == QueryType.UPDATE:
            # UPDATE table_name SET
            match = re.search(r'UPDATE\s+(\w+)\s+SET', query_upper)
            if match:
                return match.group(1).lower()

        elif query_type == QueryType.DELETE:
            # DELETE FROM table_name
            match = re.search(r'DELETE\s+FROM\s+(\w+)', query_upper)
            if match:
                return match.group(1).lower()

        return None

    def get_transaction_methods(self) -> Set[str]:
        """Get all methods that have transaction boundaries"""
        return self._transaction_methods.copy()
