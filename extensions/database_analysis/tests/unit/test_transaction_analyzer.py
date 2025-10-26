"""
Unit tests for Transaction Analyzer
"""

import pytest
from pathlib import Path

from multidb_analyzer.analyzers.transaction_analyzer import TransactionAnalyzer
from multidb_analyzer.models.database_models import (
    TransactionBoundary,
    DatabaseQuery,
    QueryType,
    DatabaseType,
)


class TestTransactionAnalyzer:
    """Test cases for TransactionAnalyzer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = TransactionAnalyzer()

    def test_detect_spring_transactional(self, tmp_path):
        """Test detecting Spring @Transactional annotation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Service
            public class UserService {
                @Transactional
                public void updateUser(User user) {
                    userRepository.save(user);
                }
            }
        ''')

        transactions = self.analyzer.analyze_file(str(test_file))

        assert len(transactions) == 1
        assert transactions[0].type == "begin"
        assert "updateUser" in transactions[0].method_id

    def test_detect_transactional_with_isolation(self, tmp_path):
        """Test detecting @Transactional with isolation level"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Transactional(isolation = Isolation.SERIALIZABLE, timeout = 30)
            public void criticalUpdate(User user) {
                userRepository.save(user);
            }
        ''')

        transactions = self.analyzer.analyze_file(str(test_file))

        assert len(transactions) == 1
        assert transactions[0].isolation_level == "SERIALIZABLE"
        assert transactions[0].timeout == 30

    def test_detect_programmatic_transaction(self, tmp_path):
        """Test detecting programmatic transaction management"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void updateWithTransaction(User user) {
                Transaction tx = session.beginTransaction();
                try {
                    userRepository.save(user);
                    tx.commit();
                } catch (Exception e) {
                    tx.rollback();
                }
            }
        ''')

        transactions = self.analyzer.analyze_file(str(test_file))

        # Should detect begin, commit, and rollback
        assert len(transactions) >= 2
        assert any(t.type == "begin" for t in transactions)
        assert any(t.type == "commit" for t in transactions)
        assert any(t.type == "rollback" for t in transactions)

    def test_detect_jpa_transaction(self, tmp_path):
        """Test detecting JPA EntityManager transaction"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void saveWithJPA(User user) {
                entityManager.getTransaction().begin();
                entityManager.persist(user);
                entityManager.getTransaction().commit();
            }
        ''')

        transactions = self.analyzer.analyze_file(str(test_file))

        assert len(transactions) > 0
        assert any(t.type == "begin" for t in transactions)

    def test_find_queries_in_transaction(self):
        """Test finding queries within a transaction"""
        transaction = TransactionBoundary(
            type="begin",
            file_path="test.java",
            line_number=10,
            method_id="test.java:updateUser",
        )

        queries = [
            DatabaseQuery(
                query_text="UPDATE users SET name = ?",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=15,
                method_name="updateUser",
            ),
            DatabaseQuery(
                query_text="SELECT * FROM users",
                query_type=QueryType.SELECT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=20,
                method_name="getUsers",
            ),
        ]

        queries_in_tx = self.analyzer.find_queries_in_transaction(transaction, queries)

        assert len(queries_in_tx) == 1
        assert queries_in_tx[0].method_name == "updateUser"

    def test_check_distributed_transaction(self):
        """Test detecting distributed transactions"""
        queries = [
            DatabaseQuery(
                query_text="INSERT INTO users",
                query_type=QueryType.INSERT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
            DatabaseQuery(
                query_text="INSERT INTO cache",
                query_type=QueryType.INSERT,
                database=DatabaseType.REDIS,
                file_path="test.java",
                line_number=20,
            ),
        ]

        is_distributed, db_count = self.analyzer.check_distributed_tx(queries)

        assert is_distributed is True
        assert db_count == 2

    def test_check_single_database_transaction(self):
        """Test detecting single-database transaction"""
        queries = [
            DatabaseQuery(
                query_text="INSERT INTO users",
                query_type=QueryType.INSERT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
            DatabaseQuery(
                query_text="UPDATE orders",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=20,
            ),
        ]

        is_distributed, db_count = self.analyzer.check_distributed_tx(queries)

        assert is_distributed is False
        assert db_count == 1

    def test_assess_deadlock_risk_high(self):
        """Test assessing high deadlock risk"""
        queries = [
            DatabaseQuery(
                query_text="UPDATE users SET status = 'active'",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
            DatabaseQuery(
                query_text="UPDATE orders SET status = 'processed'",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=20,
            ),
            DatabaseQuery(
                query_text="UPDATE payments SET status = 'completed'",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=30,
            ),
            DatabaseQuery(
                query_text="DELETE FROM notifications",
                query_type=QueryType.DELETE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=40,
            ),
        ]

        risk = self.analyzer.assess_deadlock_risk(queries)

        assert risk == "high"  # Multiple writes to different tables

    def test_assess_deadlock_risk_low(self):
        """Test assessing low deadlock risk"""
        queries = [
            DatabaseQuery(
                query_text="SELECT * FROM users",
                query_type=QueryType.SELECT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
        ]

        risk = self.analyzer.assess_deadlock_risk(queries)

        assert risk == "low"  # Read-only queries

    def test_get_transaction_methods(self, tmp_path):
        """Test tracking transaction methods"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Transactional
            public void method1() {}

            @Transactional
            public void method2() {}
        ''')

        self.analyzer.analyze_file(str(test_file))
        tx_methods = self.analyzer.get_transaction_methods()

        assert "method1" in tx_methods
        assert "method2" in tx_methods

    def test_assess_deadlock_risk_medium(self):
        """Test assessing medium deadlock risk"""
        queries = [
            DatabaseQuery(
                query_text="UPDATE users SET status = 'active'",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
            DatabaseQuery(
                query_text="UPDATE orders SET status = 'processed'",
                query_type=QueryType.UPDATE,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=20,
            ),
        ]

        risk = self.analyzer.assess_deadlock_risk(queries)

        assert risk == "medium"  # 2 different tables

    def test_extract_table_name_insert(self):
        """Test extracting table name from INSERT"""
        table = self.analyzer._extract_table_name(
            "INSERT INTO users (name) VALUES (?)",
            QueryType.INSERT
        )
        assert table == "users"

    def test_extract_table_name_no_match(self):
        """Test extracting table name with no match"""
        # Invalid query format
        table = self.analyzer._extract_table_name(
            "INVALID SQL",
            QueryType.UPDATE
        )
        assert table is None

        # CQL query (not SQL)
        table = self.analyzer._extract_table_name(
            "SELECT * FROM users",
            QueryType.CQL
        )
        assert table is None

    def test_extract_table_name_delete(self):
        """Test extracting table name from DELETE"""
        table = self.analyzer._extract_table_name(
            "DELETE FROM orders WHERE id = ?",
            QueryType.DELETE
        )
        assert table == "orders"

    def test_check_distributed_tx_empty(self):
        """Test distributed transaction check with empty list"""
        is_distributed, db_count = self.analyzer.check_distributed_tx([])
        assert is_distributed is False
        assert db_count == 0

    def test_assess_deadlock_risk_no_writes(self):
        """Test deadlock risk with no write queries"""
        queries = [
            DatabaseQuery(
                query_text="SELECT * FROM users",
                query_type=QueryType.SELECT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=10,
            ),
            DatabaseQuery(
                query_text="SELECT * FROM orders",
                query_type=QueryType.SELECT,
                database=DatabaseType.MYSQL,
                file_path="test.java",
                line_number=20,
            ),
        ]

        risk = self.analyzer.assess_deadlock_risk(queries)
        assert risk == "low"
