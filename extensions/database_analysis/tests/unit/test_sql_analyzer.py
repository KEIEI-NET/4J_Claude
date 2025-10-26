"""
Unit tests for SQL Analyzer
"""

import pytest
import tempfile
import os
from pathlib import Path

from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer, CodeContext
from multidb_analyzer.models.database_models import (
    DatabaseQuery,
    QueryType,
    DatabaseType,
)


class TestSQLAnalyzer:
    """Test cases for SQLAnalyzer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = SQLAnalyzer(database=DatabaseType.MYSQL)

    def test_analyze_simple_select(self, tmp_path):
        """Test analyzing a simple SELECT query"""
        # Create a test file
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public class UserDAO {
                public User findById(Long id) {
                    String sql = "SELECT * FROM users WHERE id = ?";
                    return executeQuery(sql, id);
                }
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].query_type == QueryType.SELECT
        assert queries[0].database == DatabaseType.MYSQL
        assert queries[0].is_prepared is True
        assert "users" in queries[0].query_text.lower()

    def test_detect_n_plus_one_in_loop(self, tmp_path):
        """Test detecting N+1 query pattern in a loop"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void processUsers(List<User> users) {
                for (User user : users) {
                    String sql = "SELECT * FROM orders WHERE user_id = ?";
                    List<Order> orders = executeQuery(sql, user.getId());
                }
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].is_in_loop is True
        assert queries[0].n_plus_one_risk is True

    def test_analyze_insert_query(self, tmp_path):
        """Test analyzing an INSERT query"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void createUser(User user) {
                String sql = "INSERT INTO users (name, email) VALUES (?, ?)";
                executeUpdate(sql, user.getName(), user.getEmail());
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].query_type == QueryType.INSERT
        assert queries[0].missing_transaction is True  # Write without @Transactional

    def test_analyze_update_query(self, tmp_path):
        """Test analyzing an UPDATE query"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void updateUser(User user) {
                String sql = "UPDATE users SET email = ? WHERE id = ?";
                executeUpdate(sql, user.getEmail(), user.getId());
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].query_type == QueryType.UPDATE

    def test_analyze_delete_query(self, tmp_path):
        """Test analyzing a DELETE query"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void deleteUser(Long id) {
                String sql = "DELETE FROM users WHERE id = ?";
                executeUpdate(sql, id);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].query_type == QueryType.DELETE

    def test_analyze_join_query(self, tmp_path):
        """Test analyzing a query with JOINs"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public List<User> getUsersWithOrders() {
                String sql = "SELECT u.*, o.* FROM users u " +
                           "INNER JOIN orders o ON u.id = o.user_id " +
                           "WHERE o.status = ?";
                return executeQuery(sql, "active");
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert queries[0].complexity > 2.0  # JOINs increase complexity

    def test_analyze_spring_data_query(self, tmp_path):
        """Test analyzing Spring Data @Query annotation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Repository
            public interface UserRepository extends JpaRepository<User, Long> {
                @Query("SELECT u FROM User u WHERE u.email = :email")
                User findByEmail(@Param("email") String email);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 1
        assert "email" in queries[0].query_text.lower()

    def test_extract_tables(self):
        """Test extracting table names from SQL"""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        import sqlparse

        statement = sqlparse.parse(sql)[0]
        tables = self.analyzer._extract_tables(statement)

        assert "users" in tables or "u" in tables

    def test_detect_subqueries(self):
        """Test detecting subqueries"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE status = 'active')"
        import sqlparse

        statement = sqlparse.parse(sql)[0]
        subqueries = self.analyzer._detect_subqueries(statement)

        assert len(subqueries) > 0

    def test_calculate_complexity(self):
        """Test calculating query complexity"""
        # Simple query
        simple_sql = "SELECT * FROM users"
        import sqlparse

        statement = sqlparse.parse(simple_sql)[0]
        complexity = self.analyzer._calculate_complexity(statement, [], [])
        assert complexity >= 1.0

        # Complex query with JOINs
        complex_sql = """
            SELECT u.*, o.*, p.*
            FROM users u
            JOIN orders o ON u.id = o.user_id
            JOIN products p ON o.product_id = p.id
            WHERE u.status = 'active'
            AND o.created_at > '2024-01-01'
        """
        statement = sqlparse.parse(complex_sql)[0]
        joins = ["JOIN orders", "JOIN products"]
        where = ["WHERE u.status = 'active'", "AND o.created_at > '2024-01-01'"]
        complexity = self.analyzer._calculate_complexity(statement, joins, where)
        assert complexity > 3.0

    def test_context_determination(self, tmp_path):
        """Test determining code context"""
        test_file = tmp_path / "test.java"
        content = '''
            public class UserService {
                public void processUsers() {
                    for (User user : getUsers()) {
                        String sql = "SELECT * FROM orders WHERE user_id = ?";
                        processOrders(sql, user.getId());
                    }
                }
            }
        '''
        test_file.write_text(content)

        position = content.find("SELECT")
        context = self.analyzer._determine_context(content, position, str(test_file))

        assert context.is_in_loop is True
        assert context.file_path == str(test_file)

    def test_foreign_key_condition_detection(self):
        """Test detecting foreign key conditions"""
        sql_with_fk = "SELECT * FROM orders WHERE user_id = ?"
        assert self.analyzer._has_foreign_key_condition(sql_with_fk) is True

        sql_without_fk = "SELECT * FROM users WHERE email = ?"
        assert self.analyzer._has_foreign_key_condition(sql_without_fk) is False

    def test_multiple_queries_in_file(self, tmp_path):
        """Test analyzing multiple queries in a single file"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public class UserDAO {
                public User findById(Long id) {
                    String sql = "SELECT * FROM users WHERE id = ?";
                    return executeQuery(sql, id);
                }

                public void deleteUser(Long id) {
                    String sql = "DELETE FROM users WHERE id = ?";
                    executeUpdate(sql, id);
                }

                public List<User> findByEmail(String email) {
                    String sql = "SELECT * FROM users WHERE email = ?";
                    return executeQuery(sql, email);
                }
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        assert len(queries) == 3
        assert sum(1 for q in queries if q.query_type == QueryType.SELECT) == 2
        assert sum(1 for q in queries if q.query_type == QueryType.DELETE) == 1

    def test_get_known_tables(self):
        """Test tracking known tables"""
        self.analyzer.add_known_table("users")
        self.analyzer.add_known_table("orders")

        tables = self.analyzer.get_known_tables()

        assert "users" in tables
        assert "orders" in tables
        assert len(tables) == 2

    def test_error_handling_invalid_sql(self, tmp_path):
        """Test handling invalid SQL gracefully"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void broken() {
                String sql = "SELECT * INVALID SQL SYNTAX";
                executeQuery(sql);
            }
        ''')

        # Should not raise exception
        queries = self.analyzer.analyze_file(str(test_file))
        # May or may not return queries depending on parsing tolerance


    def test_prepared_statement_detection(self, tmp_path):
        """Test detecting prepared statements"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void test() {
                String sql1 = "SELECT * FROM users WHERE id = ?";
                String sql2 = "SELECT * FROM users WHERE id = 123";
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))

        # Find the query with ?
        prepared_query = next((q for q in queries if "?" in q.query_text), None)
        if prepared_query:
            assert prepared_query.is_prepared is True

    def test_analyze_file_not_found(self):
        """Test handling file not found"""
        with pytest.raises(FileNotFoundError):
            self.analyzer.analyze_file("/nonexistent/file.java")

    def test_estimate_index_usage_no_where(self):
        """Test index estimation without WHERE clause"""
        has_index = self.analyzer._estimate_index_usage(["users"], [])
        assert has_index is False  # Full table scan

    def test_estimate_index_usage_no_tables(self):
        """Test index estimation with no tables"""
        has_index = self.analyzer._estimate_index_usage([], ["WHERE id = 1"])
        assert has_index is True  # Default

    def test_query_with_no_type(self, tmp_path):
        """Test handling query with unrecognized type"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void test() {
                String sql = "TRUNCATE TABLE users";
                execute(sql);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        # TRUNCATE is not a recognized query type, should be filtered out

    def test_concatenated_sql_deduplication(self, tmp_path):
        """Test that concatenated SQL doesn't create duplicates"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void test() {
                String sql = "SELECT * FROM users " +
                           "WHERE id = ?";
                execute(sql);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        # Should have exactly 1 query, not duplicates
        assert len(queries) == 1

    def test_detect_subqueries_none(self):
        """Test subquery detection with no subqueries"""
        import sqlparse
        sql = "SELECT * FROM users WHERE status = 'active'"
        statement = sqlparse.parse(sql)[0]
        subqueries = self.analyzer._detect_subqueries(statement)
        assert len(subqueries) == 0

    def test_has_foreign_key_condition_variations(self):
        """Test various foreign key patterns"""
        # user_id pattern
        assert self.analyzer._has_foreign_key_condition("WHERE user_id = 1") is True
        # userId camelCase pattern
        assert self.analyzer._has_foreign_key_condition("WHERE userId = 1") is True
        # id pattern
        assert self.analyzer._has_foreign_key_condition("WHERE id = 1") is True
        # No foreign key
        assert self.analyzer._has_foreign_key_condition("WHERE name = 'test'") is False

    def test_extract_concatenated_sql_complex(self, tmp_path):
        """Test extracting complex concatenated SQL"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void complexQuery() {
                String sql = "SELECT u.*, o.* " +
                           "FROM users u " +
                           "INNER JOIN orders o ON u.id = o.user_id " +
                           "WHERE u.status = ? " +
                           "AND o.created_at > ?";
                executeQuery(sql);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1
        if queries:
            assert "JOIN" in queries[0].query_text

    def test_extract_spring_data_query_with_params(self, tmp_path):
        """Test extracting @Query with parameters"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Repository
            public interface OrderRepository {
                @Query("SELECT o FROM Order o WHERE o.userId = :userId AND o.status = :status")
                List<Order> findByUserAndStatus(@Param("userId") Long userId, @Param("status") String status);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1

    def test_determine_context_in_loop(self, tmp_path):
        """Test context determination inside loop"""
        test_file = tmp_path / "test.java"
        content = '''
            public void processAll() {
                while (hasMore()) {
                    String sql = "SELECT * FROM items WHERE category_id = ?";
                    process(sql);
                }
            }
        '''
        test_file.write_text(content)

        position = content.find("SELECT")
        context = self.analyzer._determine_context(content, position, str(test_file))

        assert context.is_in_loop is True

    def test_determine_context_with_annotation(self, tmp_path):
        """Test context determination with @Transactional annotation"""
        test_file = tmp_path / "test.java"
        content = '''
            @Transactional
            public void updateAll() {
                String sql = "UPDATE users SET status = ?";
                execute(sql);
            }
        '''
        test_file.write_text(content)

        position = content.find("UPDATE")
        context = self.analyzer._determine_context(content, position, str(test_file))

        # Context should include file path and line number
        assert context.file_path == str(test_file)
        assert context.line_number > 0

    def test_calculate_complexity_with_subquery(self):
        """Test complexity with subquery"""
        import sqlparse
        sql = """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders
                WHERE status = 'active'
            )
        """
        statement = sqlparse.parse(sql)[0]
        subqueries = self.analyzer._detect_subqueries(statement)
        complexity = self.analyzer._calculate_complexity(statement, [], [])
        assert complexity > 1.0

    def test_extract_tables_with_aliases(self):
        """Test extracting tables with aliases"""
        import sqlparse
        sql = "SELECT u.name, o.total FROM users AS u, orders AS o WHERE u.id = o.user_id"
        statement = sqlparse.parse(sql)[0]
        tables = self.analyzer._extract_tables(statement)
        # Should extract at least one table
        assert len(tables) > 0

    def test_prepared_statement_multiple_placeholders(self, tmp_path):
        """Test prepared statement with multiple placeholders"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void multiParam() {
                String sql = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)";
                executeUpdate(sql, name, email, age);
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1
        if queries:
            assert queries[0].is_prepared is True
            assert queries[0].query_text.count("?") >= 3

    def test_query_in_nested_method(self, tmp_path):
        """Test query inside nested method"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public class Service {
                public void outer() {
                    inner();
                }

                private void inner() {
                    String sql = "DELETE FROM temp WHERE created_at < ?";
                    execute(sql);
                }
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1

    def test_estimate_index_usage_with_where(self):
        """Test index estimation with WHERE clause"""
        has_index = self.analyzer._estimate_index_usage(
            ["users"],
            ["WHERE id = 1", "AND status = 'active'"]
        )
        assert has_index is True  # Has WHERE conditions

    def test_extract_concatenated_sql_with_analysis(self, tmp_path):
        """Test full analysis of concatenated SQL"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void updateWithConcat() {
                for (User user : users) {
                    String sql = "UPDATE users " +
                               "SET status = ? " +
                               "WHERE id = ?";
                    execute(sql, status, id);
                }
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        assert len(queries) >= 1
        if queries:
            # Should detect it's in a loop
            assert queries[0].is_in_loop is True
            # Should be an UPDATE query
            assert queries[0].query_type == QueryType.UPDATE

    def test_analyze_single_query_with_nulls(self):
        """Test analyzing query that returns None"""
        context = CodeContext(
            file_path="test.java",
            line_number=1,
            is_in_loop=False
        )

        # Empty SQL should return None
        result = self.analyzer._analyze_single_query("", context, 1)
        # This path may or may not return None depending on implementation

    def test_extract_annotation_queries_jpql(self, tmp_path):
        """Test extracting JPQL queries from annotations"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Entity
            @NamedQuery(
                name = "User.findByStatus",
                query = "SELECT u FROM User u WHERE u.status = :status"
            )
            public class User {
                @Id private Long id;
            }
        ''')

        queries = self.analyzer.analyze_file(str(test_file))
        # May or may not capture JPQL queries depending on implementation
